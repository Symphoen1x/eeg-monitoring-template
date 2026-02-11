"""
config.py
=========
Configuration settings for EEG Systems.

Centralized configuration for all modules.
Modify these values to adjust system behavior.
"""

# ===========================
# EEG ACQUISITION
# ===========================
STREAM_TYPE = "EEG"
STREAM_TIMEOUT = 20          # seconds to wait for LSL stream
MAX_CHUNK_LENGTH = 12        # samples per chunk

# Muse 2 channel labels
CHANNEL_LABELS = ["TP9", "AF7", "AF8", "TP10", "AUX"]

# ===========================
# PREPROCESSING
# ===========================
SAMPLING_RATE = 256.0        # Muse 2 default sampling rate (Hz)

# Filter settings
LOWCUT_FREQ = 1.0            # High-pass cutoff (Hz) - removes DC drift
HIGHCUT_FREQ = 40.0          # Low-pass cutoff (Hz) - removes muscle artifacts
NOTCH_FREQ = 50.0            # Power line frequency (50 Hz Indonesia, 60 Hz USA)
FILTER_ORDER = 4             # Butterworth filter order

# ===========================
# FEATURE EXTRACTION
# ===========================
NPERSEG = 256                # Segment length for Welch PSD

# EEG Frequency bands (Hz)
FREQ_BANDS = {
    "delta": (1, 4),         # Deep sleep
    "theta": (4, 8),         # Drowsiness, light sleep
    "alpha": (8, 13),        # Relaxed, calm
    "beta": (13, 30),        # Active thinking, focus
    "gamma": (30, 45)        # High-level cognition
}

# ===========================
# COGNITIVE ANALYSIS
# ===========================
# Thresholds for cognitive state detection
# Adjust based on individual calibration
FATIGUE_THRESHOLD = 1.3      # Theta/Alpha ratio
STRESS_THRESHOLD = 1.2       # Beta/Alpha ratio
FOCUS_THRESHOLD = 0.8        # Alpha/Beta ratio

# ===========================
# REAL-TIME MONITORING
# ===========================
CHUNK_DURATION = 2.0         # Duration of each analysis window (seconds)
UPDATE_INTERVAL = 1.0        # Time between updates (seconds)

# ===========================
# DATA RECORDING
# ===========================
RECORDING_DIR = "recordings"
RECORDING_FORMAT = "csv"     # Options: csv, edf

# ===========================
# BACKEND SETTINGS (Fumorive Backend)
# ===========================
BACKEND_URL = "http://localhost:8000"       # Backend URL
EEG_ENDPOINT = "/api/v1/eeg/stream"         # EEG streaming endpoint (HTTP POST)
SAVE_TO_DB = False                          # Save to database by default

# WebSocket endpoint (untuk referensi - tidak digunakan oleh server.py)
# Frontend connects to: ws://localhost:8000/api/v1/ws/session/{session_id}

# Legacy (for standalone server)
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5000
DEBUG_MODE = True

# ===========================
# LOGGING
# ===========================
LOG_LEVEL = "INFO"           # DEBUG, INFO, WARNING, ERROR
LOG_FILE = "eeg_system.log"

# ===========================
# STATE THRESHOLDS (Cognitive Analysis)
# ===========================
# These align with eeg/analysis.py CognitiveAnalyzer
# Relative thresholds after baseline normalization
THRESHOLDS = {
    "fatigue": {
        "theta_alpha_min": 1.4,      # θ/α harus di atas ini
        "alpha_power_max": 0.8       # α power harus rendah
    },
    "stress": {
        "beta_alpha_min": 1.8,       # β/α harus tinggi
        "theta_alpha_max": 1.2,      # θ/α harus rendah
        "variability_min": 0.15      # high frequency variability
    },
    "focused": {
        "beta_alpha_min": 1.2,       # β/α moderate-high
        "beta_alpha_max": 1.8,       # tapi tidak setinggi stress
        "theta_alpha_max": 1.3,      # tidak ngantuk
        "stability_min": 0.7         # signal harus stabil
    },
    "relaxed": {
        "alpha_beta_min": 1.3,       # α/β tinggi
        "theta_alpha_max": 1.2       # tidak ngantuk
    }
}
