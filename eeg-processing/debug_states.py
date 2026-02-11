"""
debug_states.py
===============
Debug script untuk menganalisis kenapa state detection tidak akurat.
Menampilkan RAW metrics untuk memahami pattern EEG sebenarnya.

Jalankan: python debug_states.py
"""

import time
import numpy as np
from collections import deque

from eeg.acquisition import EEGAcquisition
from eeg.preprocessing import EEGPreprocessor
from eeg.features import EEGFeatureExtractor
from eeg.analysis import CognitiveAnalyzer


def print_header():
    print("\n" + "=" * 80)
    print(" 🔬 EEG DEBUG MODE - Analisis State Detection ")
    print("=" * 80)


def print_raw_bands(features: dict):
    """Print raw band power values."""
    bands = ["theta", "alpha", "beta", "delta", "gamma"]
    print("\n  📊 RAW BAND POWER (per channel):")
    for band in bands:
        if band in features:
            values = features[band]
            avg = np.mean(values)
            print(f"     {band:6s}: {avg:8.4f}  │ channels: {[f'{v:.4f}' for v in values]}")


def print_ratios(features: dict):
    """Print ratio calculations."""
    print("\n  📈 RATIO CALCULATIONS:")
    for ratio in ["theta_alpha", "beta_alpha", "alpha_beta"]:
        if ratio in features:
            values = features[ratio]
            avg = np.mean(values)
            print(f"     {ratio:12s}: {avg:6.3f}  │ per ch: {[f'{v:.3f}' for v in values]}")


def print_analysis_detail(result: dict, baseline: dict):
    """Print detailed analysis breakdown."""
    metrics = result.get('metrics', {})
    scores = result.get('scores', {})
    debug_info = result.get('debug', {})
    
    print("\n  🧮 NORMALIZED METRICS (after baseline):")
    print(f"     θ/α normalized: {metrics.get('theta_alpha', 0):.3f}")
    print(f"     β/α normalized: {metrics.get('beta_alpha', 0):.3f}")
    print(f"     α/β normalized: {metrics.get('alpha_beta', 0):.3f}")
    
    print("\n  📍 YOUR BASELINE (from calibration):")
    for k, v in baseline.items():
        print(f"     {k}: {v:.3f}")
    
    print("\n  🎯 STATE SCORES:")
    for state, score in sorted(scores.items(), key=lambda x: -x[1]):
        bar = "█" * int(score * 20)
        print(f"     {state:8s}: {score:.0%} {bar}")
    
    print("\n  ℹ️  DEBUG INFO:")
    print(f"     Variability: {debug_info.get('variability', 0):.3f}")
    print(f"     Stability: {debug_info.get('stability', 0):.2f}")
    print(f"     Calibrated: {debug_info.get('calibrated', False)}")


def analyze_issue(features: dict, result: dict, baseline: dict):
    """Analyze potential issues based on the data."""
    issues = []
    
    # Get raw values
    theta_raw = np.mean(features.get("theta", [0]))
    alpha_raw = np.mean(features.get("alpha", [0]))
    beta_raw = np.mean(features.get("beta", [0]))
    
    theta_alpha_raw = np.mean(features.get("theta_alpha", [1]))
    beta_alpha_raw = np.mean(features.get("beta_alpha", [1]))
    alpha_beta_raw = np.mean(features.get("alpha_beta", [1]))
    
    metrics = result.get('metrics', {})
    state = result.get('state', 'unknown')
    
    # Check for high alpha (eyes closed pattern)
    if alpha_raw > 0.5 and alpha_beta_raw > 1.5:
        issues.append("⚡ HIGH ALPHA detected - kemungkinan mata tertutup/rileks")
        issues.append("   → Ini bisa menyebabkan RELAXED terdeteksi, bukan FATIGUE")
    
    # Check baseline issues
    if baseline.get('theta_alpha', 1) > 1.3:
        issues.append("⚠️  BASELINE θ/α tinggi - calibration mungkin dilakukan saat ngantuk")
    
    if baseline.get('alpha_beta', 1) > 1.3:
        issues.append("⚠️  BASELINE α/β tinggi - calibration mungkin dilakukan saat terlalu rileks")
    
    # Check for theta spike
    if theta_raw > alpha_raw * 1.5:
        issues.append("💤 THETA SPIKE - indikasi drowsiness yang kuat")
    
    # Check for beta dominance
    if beta_raw > alpha_raw * 1.5:
        issues.append("🔥 BETA DOMINANT - seharusnya FOCUSED atau STRESS")
    
    # State-specific analysis
    if state == "fatigue" and beta_raw > theta_raw:
        issues.append("❓ ANOMALY: State=FATIGUE tapi Beta > Theta")
        issues.append("   → Kemungkinan false positive, cek signal quality")
    
    if state == "focused" and alpha_raw > beta_raw:
        issues.append("❓ ANOMALY: State=FOCUSED tapi Alpha > Beta")  
        issues.append("   → Seharusnya RELAXED, threshold mungkin perlu adjustment")
    
    return issues


def main():
    print_header()
    
    # Initialize
    eeg = EEGAcquisition()
    eeg.connect()
    
    preprocessor = EEGPreprocessor(sampling_rate=eeg.sampling_rate, driving_mode=True)
    extractor = EEGFeatureExtractor(sampling_rate=eeg.sampling_rate)
    analyzer = CognitiveAnalyzer()
    
    # =========================
    # CALIBRATION - PENTING!
    # =========================
    print("\n" + "=" * 80)
    print(" ⚠️  CALIBRATION PHASE - SANGAT PENTING! ")
    print("=" * 80)
    print("""
    INSTRUKSI KALIBRAS YANG BENAR:
    1. Duduk tegak, mata TERBUKA
    2. Pandang lurus ke depan (bukan layar)
    3. Rileks tapi TETAP ALERT (seperti siap mengemudi)
    4. JANGAN merem, JANGAN ngantuk, JANGAN tegang
    5. Proses akan berlangsung 10 detik
    """)
    
    input("Tekan ENTER ketika sudah siap untuk kalibras...")
    
    print("\n[CALIBRATION] Memulai kalibras...\n")
    analyzer.start_calibration()
    
    for i in range(5):
        print(f"  Mengumpulkan sample {i+1}/5...")
        raw_data, _ = eeg.pull_chunk(duration=2.0)
        
        if raw_data.size > 0:
            clean_data, quality = preprocessor.process(raw_data)
            if clean_data.size > 0 and quality > 0.3:
                features = extractor.extract(clean_data)
                analyzer.add_calibration_sample(features)
    
    print("\n[INFO] Kalibras selesai!")
    print(f"  Baseline θ/α: {analyzer.baseline['theta_alpha']:.3f}")
    print(f"  Baseline β/α: {analyzer.baseline['beta_alpha']:.3f}")
    print(f"  Baseline α/β: {analyzer.baseline['alpha_beta']:.3f}")
    
    # Check if baseline looks off
    if analyzer.baseline['theta_alpha'] > 1.2:
        print("\n  ⚠️  WARNING: Baseline θ/α terlalu tinggi!")
        print("     Kemungkinan kamu ngantuk saat kalibras.")
        print("     Pertimbangkan ulangi kalibras setelah istirahat.")
    
    if analyzer.baseline['alpha_beta'] > 1.5:
        print("\n  ⚠️  WARNING: Baseline α/β terlalu tinggi!")
        print("     Kemungkinan kamu terlalu rileks saat kalibras.")
    
    # =========================
    # DEBUG MODE
    # =========================
    print("\n" + "=" * 80)
    print(" 🔬 ENTERING DEBUG MODE ")
    print("=" * 80)
    print("""
    Instruksi Testing:
    - Coba berbagai kondisi dan lihat raw metrics
    - FATIGUE test: perlahan tutup mata (JANGAN langsung)
    - FOCUSED test: hitung mundur dari 100 (dalam hati)
    - RELAXED test: napas dalam, pandang jauh
    - STRESS test: hitung 100-7-7-7... cepat
    
    Tekan Ctrl+C untuk berhenti
    """)
    
    try:
        iteration = 0
        while True:
            iteration += 1
            
            # Acquire
            raw_data, _ = eeg.pull_chunk(duration=2.0)
            if raw_data.size == 0:
                continue
            
            # Process
            clean_data, quality = preprocessor.process(raw_data)
            if clean_data.size == 0:
                continue
            
            # Extract
            features = extractor.extract(clean_data)
            
            # Analyze
            result = analyzer.analyze(features, signal_quality=quality)
            
            # =========================
            # DETAILED OUTPUT
            # =========================
            print("\n" + "=" * 80)
            print(f" ITERATION #{iteration} │ Quality: {quality:.0%} │ Time: {time.strftime('%H:%M:%S')}")
            print("=" * 80)
            
            # Final state
            state_emoji = {
                "fatigue": "😴", "stress": "😰", "focused": "🎯",
                "relaxed": "😌", "normal": "😊", "unknown": "❓"
            }
            emoji = state_emoji.get(result['state'], "?")
            print(f"\n  🎯 DETECTED STATE: {emoji} {result['state'].upper()} "
                  f"(confidence: {result['confidence']:.0%})")
            
            # Raw band powers
            print_raw_bands(features)
            
            # Ratios
            print_ratios(features)
            
            # Detailed analysis
            print_analysis_detail(result, analyzer.baseline)
            
            # Issue detection
            issues = analyze_issue(features, result, analyzer.baseline)
            if issues:
                print("\n  🔍 POTENTIAL ISSUES:")
                for issue in issues:
                    print(f"     {issue}")
            
            time.sleep(2.0)
    
    except KeyboardInterrupt:
        print("\n\n[INFO] Debug session ended")
        eeg.close()


if __name__ == "__main__":
    main()
