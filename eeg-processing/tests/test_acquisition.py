"""
test_acquisition.py
====================
Unit tests untuk EEG Acquisition module.

Usage:
    cd eeg-processing
    python -m pytest tests/test_acquisition.py -v
    
    atau tanpa pytest:
    python tests/test_acquisition.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eeg.acquisition import EEGAcquisition


def test_basic_acquisition():
    """Test basic EEG acquisition connection and data pull."""
    print("\n" + "=" * 50)
    print(" TEST: Basic EEG Acquisition")
    print("=" * 50)
    
    try:
        eeg = EEGAcquisition()
        print("[INFO] EEGAcquisition instance created")
        
        eeg.connect()
        print("[INFO] Connected to LSL stream")
        
        data, ts = eeg.pull_chunk(duration=2)
        print(f"[INFO] Data shape: {data.shape}")
        print(f"[INFO] Timestamps: {len(ts)} samples")
        
        assert data.size > 0, "No data received"
        assert len(ts) > 0, "No timestamps received"
        
        eeg.close()
        print("[SUCCESS] Test passed!")
        return True
        
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        return False


def test_sampling_rate():
    """Test sampling rate matches Muse 2 spec (256 Hz)."""
    print("\n" + "=" * 50)
    print(" TEST: Sampling Rate")
    print("=" * 50)
    
    try:
        eeg = EEGAcquisition()
        eeg.connect()
        
        print(f"[INFO] Sampling rate: {eeg.sampling_rate} Hz")
        assert 250 <= eeg.sampling_rate <= 260, f"Unexpected sampling rate: {eeg.sampling_rate}"
        
        eeg.close()
        print("[SUCCESS] Test passed!")
        return True
        
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print(" Fumorive EEG Acquisition Tests")
    print("=" * 60)
    print("\n⚠️  Pastikan 'muselsl stream' sudah berjalan!")
    
    results = []
    results.append(("Basic Acquisition", test_basic_acquisition()))
    results.append(("Sampling Rate", test_sampling_rate()))
    
    print("\n" + "=" * 60)
    print(" TEST SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name}: {status}")
    
    all_passed = all(r[1] for r in results)
    print("\n" + ("All tests passed! 🎉" if all_passed else "Some tests failed."))
