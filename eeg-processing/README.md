# 🧠 Fumorive EEG Processing Module

Real-time EEG acquisition, processing, dan cognitive state analysis untuk **Driver Monitoring System** menggunakan **Muse 2** headband.

## 📋 Overview

Module ini adalah bagian dari **Fumorive** - sistem monitoring pengemudi berbasis EEG dan face detection. Module EEG bertanggung jawab untuk:

- 📡 Akuisisi data EEG real-time dari Muse 2 via Bluetooth/LSL
- 🔧 Preprocessing sinyal EEG (filtering, normalization)
- 📊 Ekstraksi fitur (band power: delta, theta, alpha, beta, gamma)
- 🧠 Analisis kognitif (fatigue, stress, focus detection)
- 🚀 Streaming data ke Backend Fumorive

---

## 📁 Project Structure

```
eeg-processing/
├── main.py                 # Standalone driver monitoring (testing)
├── server.py               # 🆕 Backend streaming bridge
├── debug_states.py         # 🔧 Debugging tool untuk calibration
├── check_stream.py         # Utility: cek LSL streams
├── config.py               # Konfigurasi sistem
├── utils.py                # Utility functions
├── requirements.txt        # Python dependencies
│
├── eeg/                    # Core EEG modules
│   ├── __init__.py
│   ├── acquisition.py      # LSL stream acquisition
│   ├── preprocessing.py    # Signal filtering & cleaning
│   ├── features.py         # Feature extraction (PSD, ratios)
│   └── analysis.py         # Cognitive state analysis
│
└── tests/                  # Unit tests
    └── test_acquisition.py
```

---

## ⚠️ Requirements

### Python Version
```
Python 3.10.x atau 3.11.x (WAJIB)
```
> ⚠️ **PENTING:** `muselsl` TIDAK kompatibel dengan Python 3.12+

### Hardware
- Muse 2 Headband
- Bluetooth adapter

---

## 🚀 Installation

### 1. Setup Virtual Environment
```bash
cd eeg-processing

# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Verify Setup
```bash
python --version  # Harus 3.10.x atau 3.11.x
python check_stream.py
```

---

## 🎮 Usage

### Mode 1: Standalone Testing (tanpa Backend)

Untuk testing EEG processing tanpa backend:

```bash
# Terminal 1: Start Muse LSL stream
muselsl stream

# Terminal 2: Run standalone monitor
python main.py
```

### Mode 2: Debug States (untuk Calibration)

Jika state detection tidak akurat:

```bash
python debug_states.py
```

### Mode 3: 🆕 Stream ke Backend Fumorive

Untuk production dengan backend:

```bash
# Terminal 1: Start Muse LSL
muselsl stream

# Terminal 2: Start Backend (dari folder backend/)
uvicorn main:app --reload

# Terminal 3: Start EEG Server
python server.py --session-id YOUR_SESSION_UUID
```

**Arguments:**
- `--session-id` (required): Session UUID dari backend
- `--backend-url`: Backend URL (default: http://localhost:8000)
- `--save-db`: Simpan data ke database
- `--no-calibrate`: Skip calibration phase

---

## 🧠 Cognitive States

| State | Internal | Backend | Indicator |
|-------|----------|---------|-----------|
| 😴 Fatigue | `fatigue` | `fatigued` | High θ/α ratio (> 1.4) |
| 😰 Stress | `stress` | `alert` | Very high β/α (> 1.8) |
| 🎯 Focused | `focused` | `alert` | Moderate β/α (1.2-1.8) |
| 😌 Relaxed | `relaxed` | `alert` | High α/β (> 1.3) |
| 😊 Normal | `normal` | `alert` | Balanced ratios |

### Fatigue Score Mapping
| Score | Backend State |
|-------|---------------|
| 0-39% | `alert` |
| 40-69% | `drowsy` |
| 70-100% | `fatigued` |

---

## 🔧 Calibration Guide

Kalibrasi yang BENAR sangat penting untuk akurasi deteksi:

### ✅ Instruksi Kalibrasi
1. **Duduk tegak** - posisi seperti akan mengemudi
2. **Mata TERBUKA** - pandang lurus ke depan
3. **Rileks tapi ALERT** - tidak ngantuk, tidak tegang
4. **Durasi: 10 detik**

### ❌ Hindari Saat Kalibrasi
- Jangan merem
- Jangan dalam kondisi ngantuk
- Jangan terlalu tegang/stress
- Jangan sambil melihat layar

---

## 📊 Testing Each State

Untuk memverifikasi setiap state terdeteksi dengan benar:

| State | Test Method |
|-------|-------------|
| FATIGUE | Perlahan tutup mata 70%, tahan 30 detik |
| STRESS | Hitung mundur 100-7-7-7... dengan cepat |
| FOCUSED | Hitung mundur 50-3-3-3... dengan tenang |
| RELAXED | Napas dalam, pandang kejauhan |
| NORMAL | Duduk santai, mata terbuka |

---

## 🐛 Troubleshooting

### No LSL stream found
```bash
# 1. Cek Bluetooth connection
# 2. Restart Muse LSL
muselsl stream

# 3. Verify stream
python check_stream.py
```

### Baseline θ/α tinggi
Kalibrasi dilakukan saat ngantuk. Solusi:
1. Istirahat 5-10 menit
2. Cuci muka
3. Kalibrasi ulang

### State detection tidak akurat
```bash
python debug_states.py
```
Amati raw metrics dan sesuaikan threshold di `config.py`.

### Cannot connect to backend
Pastikan backend running:
```bash
cd ../backend
uvicorn main:app --reload
```

---

## 🔗 Integration dengan Backend

EEG data dikirim via HTTP POST ke `/api/v1/eeg/stream`:

```json
{
    "session_id": "uuid-string",
    "timestamp": "2026-02-05T10:30:00Z",
    "sample_rate": 256,
    "channels": {
        "TP9": 0.123, "AF7": 0.456,
        "AF8": 0.789, "TP10": 0.234
    },
    "processed": {
        "theta_power": 0.45,
        "alpha_power": 0.67,
        "theta_alpha_ratio": 0.67,
        "fatigue_score": 32.5,
        "cognitive_state": "alert"
    }
}
```

---

## 📚 References

- [Muse LSL](https://github.com/alexandrebarachant/muse-lsl)
- [Lab Streaming Layer](https://labstreaminglayer.readthedocs.io/)
- [EEG Band Frequencies](https://en.wikipedia.org/wiki/Electroencephalography)

---

## 👥 Fumorive Team

Part of the Fumorive Driver Monitoring System.
