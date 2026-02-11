"""
server.py
=========
EEG Streaming Server - Bridge antara Muse 2 dan Backend Fumorive

Purpose:
- Akuisisi real-time EEG dari Muse 2 via LSL
- Proses dan ekstrak fitur kognitif
- Stream data ke Backend via HTTP POST

Data Flow:
    Muse 2 → LSL → server.py (HTTP POST) → Backend → WebSocket → Frontend

Usage:
    python server.py --session-id <SESSION_UUID>
    python server.py --session-id <SESSION_UUID> --backend-url http://localhost:8000
    python server.py --session-id <SESSION_UUID> --save-db --no-calibrate
"""

import time
import argparse
import logging
import requests
from datetime import datetime
from typing import Optional
import numpy as np

from eeg import EEGAcquisition, EEGPreprocessor, EEGFeatureExtractor, CognitiveAnalyzer
from config import (
    SAMPLING_RATE, CHUNK_DURATION, 
    LOWCUT_FREQ, HIGHCUT_FREQ, NOTCH_FREQ,
    BACKEND_URL, EEG_ENDPOINT
)


# ===========================
# LOGGING SETUP
# ===========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


# ===========================
# STATE MAPPING (EEG -> Backend)
# ===========================
# Backend schema expects: "alert", "drowsy", "fatigued"
# See: backend/app/schemas/eeg.py EEGDataPoint.cognitive_state

def get_backend_state(internal_state: str, fatigue_score: float) -> str:
    """
    Convert internal cognitive state ke format yang backend harapkan.
    
    Backend expects: "alert", "drowsy", "fatigued"
    Internal states: "fatigue", "stress", "focused", "relaxed", "normal", "unknown"
    """
    # Fatigue score based mapping (primary)
    if fatigue_score >= 70:
        return "fatigued"
    elif fatigue_score >= 40:
        return "drowsy"
    
    # State based mapping (secondary)
    if internal_state == "fatigue":
        return "drowsy"
    
    # All other states map to alert
    return "alert"


# ===========================
# EEG SERVER CLASS
# ===========================
class EEGStreamingServer:
    """
    Server untuk streaming EEG data ke Fumorive Backend via HTTP POST.
    
    Backend akan menerima data dan broadcast ke frontend via WebSocket.
    """
    
    def __init__(
        self,
        session_id: str,
        backend_url: str = None,
        save_to_db: bool = False
    ):
        """
        Initialize EEG Streaming Server.
        
        Parameters
        ----------
        session_id : str
            UUID session dari backend (wajib)
        backend_url : str
            URL backend Fumorive (default dari config.py)
        save_to_db : bool
            Apakah menyimpan ke database (untuk recording)
        """
        self.session_id = session_id
        self.backend_url = backend_url or BACKEND_URL
        self.save_to_db = save_to_db
        self.endpoint = f"{self.backend_url}{EEG_ENDPOINT}"
        
        # Statistics
        self.samples_sent = 0
        self.errors = 0
        self.consecutive_errors = 0
        self.start_time = None
        
        # EEG Components (will be initialized on start)
        self.eeg: Optional[EEGAcquisition] = None
        self.preprocessor: Optional[EEGPreprocessor] = None
        self.extractor: Optional[EEGFeatureExtractor] = None
        self.analyzer: Optional[CognitiveAnalyzer] = None
        
        logger.info("EEG Server initialized")
        logger.info(f"  Session ID: {session_id}")
        logger.info(f"  Backend: {self.backend_url}")
        logger.info(f"  Endpoint: {self.endpoint}")
    
    def _initialize_components(self):
        """Initialize EEG processing components."""
        logger.info("Initializing EEG components...")
        
        # Acquisition
        self.eeg = EEGAcquisition()
        self.eeg.connect()
        
        # Preprocessing
        self.preprocessor = EEGPreprocessor(
            sampling_rate=self.eeg.sampling_rate,
            lowcut=LOWCUT_FREQ,
            highcut=HIGHCUT_FREQ,
            notch_freq=NOTCH_FREQ,
            driving_mode=True
        )
        
        # Feature extraction
        self.extractor = EEGFeatureExtractor(
            sampling_rate=self.eeg.sampling_rate
        )
        
        # Cognitive analyzer
        self.analyzer = CognitiveAnalyzer()
        
        logger.info("EEG components initialized successfully")
    
    def _calibrate(self, duration: float = 10.0):
        """
        Run calibration phase.
        
        Parameters
        ----------
        duration : float
            Calibration duration in seconds
        """
        logger.info("")
        logger.info("=" * 50)
        logger.info(" CALIBRATION PHASE")
        logger.info("=" * 50)
        print("""
    ⚠️  INSTRUKSI KALIBRASI:
    ─────────────────────────
    1. Duduk TEGAK (posisi mengemudi)
    2. Mata TERBUKA, pandang lurus ke depan
    3. Rileks tapi TETAP ALERT
    4. JANGAN ngantuk, JANGAN tegang
        """)
        logger.info(f"Durasi: {duration} detik")
        logger.info("")
        
        self.analyzer.start_calibration()
        
        num_samples = int(duration / CHUNK_DURATION)
        for i in range(num_samples):
            elapsed = (i + 1) * CHUNK_DURATION
            print(f"\r  ⏱️  Calibrating... {elapsed:.0f}/{duration:.0f}s", end="", flush=True)
            
            raw_data, _ = self.eeg.pull_chunk(duration=CHUNK_DURATION)
            if raw_data.size > 0:
                clean_data, quality = self.preprocessor.process(raw_data)
                if clean_data.size > 0 and quality > 0.3:
                    features = self.extractor.extract(clean_data)
                    self.analyzer.add_calibration_sample(features)
        
        print("")  # New line after progress
        logger.info("")
        
        if self.analyzer.calibrated:
            logger.info("✅ Calibration complete!")
            logger.info(f"  Baseline θ/α: {self.analyzer.baseline['theta_alpha']:.3f}")
            logger.info(f"  Baseline β/α: {self.analyzer.baseline['beta_alpha']:.3f}")
            logger.info(f"  Baseline α/β: {self.analyzer.baseline['alpha_beta']:.3f}")
            
            # Baseline quality warnings
            if self.analyzer.baseline['theta_alpha'] > 1.3:
                logger.warning("⚠️ Baseline θ/α tinggi - mungkin kalibrasi saat ngantuk")
            if self.analyzer.baseline['beta_alpha'] > 1.8:
                logger.warning("⚠️ Baseline β/α tinggi - mungkin kalibrasi saat stress")
        else:
            logger.warning("⚠️ Calibration incomplete, using default thresholds")
    
    def _process_chunk(self) -> Optional[dict]:
        """
        Process one chunk of EEG data.
        
        Returns
        -------
        dict or None
            Processed data ready for backend, or None if invalid
        """
        # 1. Acquire
        raw_data, timestamps = self.eeg.pull_chunk(duration=CHUNK_DURATION)
        if raw_data.size == 0:
            return None
        
        # 2. Preprocess
        clean_data, quality = self.preprocessor.process(raw_data)
        if clean_data.size == 0 or quality < 0.2:
            return None
        
        # 3. Extract features
        features = self.extractor.extract(clean_data)
        if not features:
            return None
        
        # 4. Analyze cognitive state
        result = self.analyzer.analyze(features, signal_quality=quality)
        
        # 5. Calculate fatigue score (0-100 scale for backend)
        theta_alpha = result['metrics'].get('theta_alpha', 1.0)
        fatigue_score = min(100, max(0, (theta_alpha - 1.0) * 50 + 30))
        
        # Adjust based on detected state
        if result['state'] == 'fatigue':
            fatigue_score = max(fatigue_score, 50 + result['confidence'] * 45)
        
        # 6. Get backend-compatible state
        backend_state = get_backend_state(result['state'], fatigue_score)
        
        # 7. Get channel values (average of last chunk)
        channel_values = {
            "TP9": float(np.mean(raw_data[:, 0])) if raw_data.shape[1] > 0 else 0,
            "AF7": float(np.mean(raw_data[:, 1])) if raw_data.shape[1] > 1 else 0,
            "AF8": float(np.mean(raw_data[:, 2])) if raw_data.shape[1] > 2 else 0,
            "TP10": float(np.mean(raw_data[:, 3])) if raw_data.shape[1] > 3 else 0
        }
        
        # Determine cognitive state based on fatigue
        if fatigue_score < 30:
            cognitive_state = "alert"
        elif fatigue_score < 60:
            cognitive_state = "drowsy"
        else:
            cognitive_state = "fatigued"
        
        # 8. Build payload
        payload = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat() + "Z",
            "sample_rate": int(self.eeg.sampling_rate),
            "channels": channel_values,
            "processed": {
                "theta_power": float(np.mean(features.get('theta', [0]))),
                "alpha_power": float(np.mean(features.get('alpha', [0]))),
                "beta_power": float(np.mean(features.get('beta', [0]))),
                "gamma_power": float(np.mean(features.get('gamma', [0]))),
                "theta_alpha_ratio": float(result['metrics'].get('theta_alpha', 1.0)),
                "beta_alpha_ratio": float(result['metrics'].get('beta_alpha', 1.0)),
                "eeg_fatigue_score": round(fatigue_score, 2),  # Frontend expects this name
                "signal_quality": float(quality),
                "cognitive_state": cognitive_state  # Frontend expects this for State display
            },
            "save_to_db": self.save_to_db
        }
        
        return payload
    
    def _send_to_backend(self, payload: dict) -> bool:
        """
        Send data to backend via HTTP POST.
        
        Returns True if successful.
        """
        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                timeout=2.0,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                self.samples_sent += 1
                self.consecutive_errors = 0
                return True
            else:
                self.errors += 1
                self.consecutive_errors += 1
                if self.consecutive_errors <= 3:
                    logger.warning(f"Backend returned {response.status_code}: {response.text[:100]}")
                return False
                
        except requests.exceptions.ConnectionError:
            self.errors += 1
            self.consecutive_errors += 1
            if self.consecutive_errors == 1:
                logger.error(f"Cannot connect to backend at {self.endpoint}")
                logger.error("Is the backend running? Start with: uvicorn main:app --reload")
            elif self.consecutive_errors == 10:
                logger.warning("Still trying to connect... (errors suppressed)")
            return False
            
        except requests.exceptions.Timeout:
            self.errors += 1
            self.consecutive_errors += 1
            if self.consecutive_errors <= 3:
                logger.warning("Backend request timeout")
            return False
            
        except Exception as e:
            self.errors += 1
            self.consecutive_errors += 1
            logger.error(f"Send error: {e}")
            return False
    
    def start(self, calibrate: bool = True, calibration_duration: float = 10.0):
        """
        Start EEG streaming server.
        
        Parameters
        ----------
        calibrate : bool
            Run calibration phase before streaming
        calibration_duration : float
            Duration of calibration in seconds
        """
        logger.info("=" * 60)
        logger.info(" FUMORIVE EEG STREAMING SERVER")
        logger.info("=" * 60)
        
        try:
            # Initialize
            self._initialize_components()
            
            # Test backend connection first
            logger.info("")
            logger.info("Testing backend connection...")
            try:
                test_response = requests.get(
                    f"{self.backend_url}/health",
                    timeout=5.0
                )
                if test_response.status_code == 200:
                    logger.info("✅ Backend connection OK")
                else:
                    logger.warning(f"Backend returned {test_response.status_code}")
            except requests.exceptions.ConnectionError:
                logger.warning("⚠️ Cannot reach backend - will retry during streaming")
            except Exception as e:
                logger.warning(f"⚠️ Backend test failed: {e}")
            
            # Calibrate
            if calibrate:
                self._calibrate(duration=calibration_duration)
            else:
                logger.info("Skipping calibration (using default baseline)")
            
            # Start streaming
            logger.info("")
            logger.info("=" * 60)
            logger.info(" STREAMING TO BACKEND")
            logger.info("=" * 60)
            logger.info(f"Endpoint: {self.endpoint}")
            logger.info("Press Ctrl+C to stop")
            logger.info("")
            
            self.start_time = time.time()
            last_log = time.time()
            
            while True:
                # Process chunk
                payload = self._process_chunk()
                
                if payload:
                    # Send to backend
                    success = self._send_to_backend(payload)
                    
                    # Log progress every 5 seconds
                    now = time.time()
                    if now - last_log >= 5.0:
                        elapsed = now - self.start_time
                        fatigue = payload['processed']['eeg_fatigue_score']
                        signal_quality = payload['processed']['signal_quality']
                        
                        logger.info(
                            f"[{elapsed:.0f}s] Fatigue: {fatigue:.0f}% | "
                            f"Signal Quality: {signal_quality:.2f} | "
                            f"Sent: {self.samples_sent} | Errors: {self.errors}"
                        )
                        last_log = now
                
                # Control rate
                time.sleep(0.5)
        
        except KeyboardInterrupt:
            logger.info("")
            logger.info("Stopping EEG server...")
        
        finally:
            if self.eeg:
                self.eeg.close()
            
            # Print summary
            elapsed = time.time() - self.start_time if self.start_time else 0
            logger.info("")
            logger.info("=" * 60)
            logger.info(" SESSION SUMMARY")
            logger.info("=" * 60)
            logger.info(f"Duration: {elapsed:.1f} seconds")
            logger.info(f"Samples sent: {self.samples_sent}")
            logger.info(f"Errors: {self.errors}")
            logger.info("Server stopped cleanly")


# ===========================
# MAIN ENTRY POINT
# ===========================
def main():
    parser = argparse.ArgumentParser(
        description="Fumorive EEG Streaming Server - Bridge Muse 2 ke Backend",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python server.py --session-id 123e4567-e89b-12d3-a456-426614174000
  python server.py --session-id <UUID> --save-db
  python server.py --session-id <UUID> --no-calibrate

Note:
  - Session ID harus UUID yang valid dari backend
  - Pastikan 'muselsl stream' sudah berjalan sebelum menjalankan server
  - Pastikan backend Fumorive sudah berjalan (uvicorn main:app --reload)
        """
    )
    parser.add_argument(
        "--session-id",
        type=str,
        required=True,
        help="Session UUID dari backend (required)"
    )
    parser.add_argument(
        "--backend-url",
        type=str,
        default=None,
        help=f"Backend URL (default: {BACKEND_URL})"
    )
    parser.add_argument(
        "--save-db",
        action="store_true",
        help="Simpan data ke database TimescaleDB"
    )
    parser.add_argument(
        "--no-calibrate",
        action="store_true",
        help="Skip fase kalibrasi (gunakan default baseline)"
    )
    parser.add_argument(
        "--calibration-time",
        type=float,
        default=10.0,
        help="Durasi kalibrasi dalam detik (default: 10)"
    )
    
    args = parser.parse_args()
    
    # Validate session_id format (basic UUID check)
    if len(args.session_id) < 32:
        logger.error("Session ID harus berupa UUID yang valid")
        logger.error("Contoh: 123e4567-e89b-12d3-a456-426614174000")
        return
    
    # Print banner
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║     🚗 FUMORIVE EEG STREAMING SERVER 🧠                  ║
    ║         Muse 2 → Backend → Frontend                      ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    server = EEGStreamingServer(
        session_id=args.session_id,
        backend_url=args.backend_url,
        save_to_db=args.save_db
    )
    
    server.start(
        calibrate=not args.no_calibrate,
        calibration_duration=args.calibration_time
    )


if __name__ == "__main__":
    main()
