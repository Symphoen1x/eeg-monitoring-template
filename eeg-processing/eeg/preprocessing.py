"""
preprocessing.py
=================
Module for EEG signal preprocessing for Driver Monitoring System.
Includes filtering, artifact attenuation (NOT rejection), and robust normalization.

Purpose:
Clean raw EEG data from Muse 2 for real-time driver fatigue/stress detection.
Optimized for driving conditions where motion artifacts are expected.

Key Design Choices for Driving:
- Artifact ATTENUATION instead of rejection (to maintain continuous monitoring)
- Robust statistics (median) instead of mean
- Adaptive thresholds based on driving context
- No aggressive data rejection (dangerous for safety-critical application)
"""

import numpy as np
from scipy.signal import butter, filtfilt, iirnotch, medfilt
from scipy.ndimage import uniform_filter1d
from typing import Optional, Tuple, Dict


class EEGPreprocessor:
    """
    EEG preprocessing pipeline optimized for Driver Monitoring System.
    
    Key differences from lab-based preprocessing:
    - Uses artifact attenuation instead of rejection
    - Maintains data continuity for safety-critical monitoring
    - Robust to motion artifacts from driving
    """

    def __init__(
        self,
        sampling_rate: float,
        lowcut: float = 1.0,
        highcut: float = 30.0,  # Reduced from 40Hz - less muscle artifact
        notch_freq: Optional[float] = 50.0,
        filter_order: int = 4,
        driving_mode: bool = True  # Enable driving-specific preprocessing
    ):
        """
        Initialize EEG preprocessor for driver monitoring.

        Parameters
        ----------
        sampling_rate : float
            Sampling rate of EEG signal (Hz)
        lowcut : float
            Low cutoff frequency (Hz)
        highcut : float
            High cutoff frequency (Hz) - default 30Hz to reduce EMG artifacts
        notch_freq : float or None
            Power line frequency (50 or 60 Hz), None to disable
        filter_order : int
            Order of Butterworth filter
        driving_mode : bool
            Enable driving-optimized preprocessing (artifact attenuation)
        """
        self.fs = sampling_rate
        self.lowcut = lowcut
        self.highcut = highcut
        self.notch_freq = notch_freq
        self.filter_order = filter_order
        self.driving_mode = driving_mode
        
        # Adaptive baseline tracking
        self._baseline_buffer: list = []
        self._baseline_window = 30  # 30 windows (~60 seconds)

        self._bandpass_b, self._bandpass_a = self._design_bandpass()
        self._notch_b, self._notch_a = self._design_notch()

    # =========================
    # FILTER DESIGN
    # =========================
    def _design_bandpass(self) -> Tuple[np.ndarray, np.ndarray]:
        nyq = 0.5 * self.fs
        low = self.lowcut / nyq
        high = self.highcut / nyq

        b, a = butter(
            self.filter_order,
            [low, high],
            btype="bandpass"
        )
        return b, a

    def _design_notch(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        if self.notch_freq is None:
            return None, None

        nyq = 0.5 * self.fs
        freq = self.notch_freq / nyq
        b, a = iirnotch(freq, Q=30)
        return b, a

    # =========================
    # PREPROCESSING STEPS
    # =========================
    def bandpass_filter(self, data: np.ndarray) -> np.ndarray:
        """
        Apply bandpass filter.

        Parameters
        ----------
        data : np.ndarray
            EEG data (samples, channels)

        Returns
        -------
        np.ndarray
            Filtered EEG data
        """
        return filtfilt(self._bandpass_b, self._bandpass_a, data, axis=0)

    def notch_filter(self, data: np.ndarray) -> np.ndarray:
        """
        Apply notch filter to remove powerline noise.
        """
        if self._notch_b is None:
            return data

        return filtfilt(self._notch_b, self._notch_a, data, axis=0)

    def baseline_correction(self, data: np.ndarray) -> np.ndarray:
        """
        Remove DC offset using mean subtraction.
        """
        baseline = np.mean(data, axis=0)
        return data - baseline

    def normalize(self, data: np.ndarray) -> np.ndarray:
        """
        Z-score normalization per channel.
        """
        mean = np.mean(data, axis=0)
        std = np.std(data, axis=0)
        std[std == 0] = 1.0  # prevent division by zero
        return (data - mean) / std

    # =========================
    # DRIVING-OPTIMIZED METHODS
    # =========================
    def robust_baseline_correction(self, data: np.ndarray) -> np.ndarray:
        """
        Remove DC offset using MEDIAN (more robust to artifacts).
        Better than mean for driving conditions with motion artifacts.
        """
        baseline = np.median(data, axis=0)
        return data - baseline

    def robust_normalize(self, data: np.ndarray) -> np.ndarray:
        """
        Robust normalization using median and MAD (Median Absolute Deviation).
        More resistant to outliers from motion artifacts.
        """
        median = np.median(data, axis=0)
        mad = np.median(np.abs(data - median), axis=0)
        mad[mad == 0] = 1.0  # prevent division by zero
        # Scale MAD to approximate std (for normal distribution)
        return (data - median) / (mad * 1.4826)

    def attenuate_artifacts(self, data: np.ndarray, threshold_factor: float = 3.0) -> np.ndarray:
        """
        Attenuate (NOT reject) extreme values using soft clipping.
        
        This is critical for driving monitoring:
        - We CANNOT reject data (safety-critical application)
        - We ATTENUATE extreme values instead
        
        Parameters
        ----------
        data : np.ndarray
            EEG data (samples, channels)
        threshold_factor : float
            Factor of MAD for threshold (default 3.0 = ~3 std)
            
        Returns
        -------
        np.ndarray
            Data with attenuated artifacts
        """
        for ch in range(data.shape[1]):
            channel = data[:, ch]
            median = np.median(channel)
            mad = np.median(np.abs(channel - median))
            
            if mad == 0:
                continue
                
            threshold = threshold_factor * mad * 1.4826
            
            # Soft clipping: compress values beyond threshold
            upper = median + threshold
            lower = median - threshold
            
            # Apply soft sigmoid-like compression
            above_mask = channel > upper
            below_mask = channel < lower
            
            if np.any(above_mask):
                excess = channel[above_mask] - upper
                data[above_mask, ch] = upper + np.tanh(excess / threshold) * threshold * 0.5
                
            if np.any(below_mask):
                excess = lower - channel[below_mask]
                data[below_mask, ch] = lower - np.tanh(excess / threshold) * threshold * 0.5
        
        return data

    def smooth_temporal(self, data: np.ndarray, window_size: int = 5) -> np.ndarray:
        """
        Apply temporal smoothing using moving median.
        Reduces high-frequency noise while preserving signal shape.
        
        Parameters
        ----------
        data : np.ndarray
            EEG data (samples, channels)
        window_size : int
            Size of median filter window (must be odd)
            
        Returns
        -------
        np.ndarray
            Smoothed data
        """
        if window_size % 2 == 0:
            window_size += 1
            
        smoothed = np.zeros_like(data)
        for ch in range(data.shape[1]):
            smoothed[:, ch] = medfilt(data[:, ch], kernel_size=window_size)
        
        return smoothed

    def compute_signal_quality(self, data: np.ndarray) -> float:
        """
        Compute signal quality score (0-1) WITHOUT rejecting data.
        Used for confidence weighting in analysis.
        
        Parameters
        ----------
        data : np.ndarray
            EEG data (samples, channels)
            
        Returns
        -------
        float
            Quality score (1.0 = good, 0.0 = poor)
        """
        if data.size == 0:
            return 0.0
            
        quality = 1.0
        
        # Check 1: Flat line detection (loose electrode)
        std_per_channel = np.std(data, axis=0)
        flat_ratio = np.sum(std_per_channel < 0.1) / len(std_per_channel)
        quality -= flat_ratio * 0.3
        
        # Check 2: Excessive high-frequency noise
        diff = np.diff(data, axis=0)
        noise_level = np.mean(np.abs(diff))
        expected_noise = np.median(std_per_channel) * 0.5
        if expected_noise > 0:
            noise_ratio = min(noise_level / expected_noise, 2.0) - 1.0
            quality -= max(0, noise_ratio) * 0.2
        
        # Check 3: Artifact proportion
        for ch in range(data.shape[1]):
            median = np.median(data[:, ch])
            mad = np.median(np.abs(data[:, ch] - median))
            if mad > 0:
                outliers = np.abs(data[:, ch] - median) > 4 * mad * 1.4826
                artifact_ratio = np.sum(outliers) / len(outliers)
                quality -= artifact_ratio * 0.1
        
        return max(0.0, min(1.0, quality))

    # =========================
    # PIPELINE
    # =========================
    def process(self, data: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Full preprocessing pipeline optimized for driver monitoring.

        Parameters
        ----------
        data : np.ndarray
            Raw EEG data (samples, channels)

        Returns
        -------
        Tuple[np.ndarray, float]
            (Preprocessed EEG data, signal quality score)
            
        Note
        ----
        For driving mode:
        - Uses artifact ATTENUATION (not rejection)
        - Uses robust statistics (median-based)
        - Always returns data (never rejects for safety)
        """
        if data.size == 0:
            return data, 0.0

        # Compute quality BEFORE processing (on raw data)
        quality = self.compute_signal_quality(data)

        # Step 1: Bandpass filter (removes drift and high-freq noise)
        data = self.bandpass_filter(data)
        
        # Step 2: Notch filter (removes power line interference)
        data = self.notch_filter(data)
        
        if self.driving_mode:
            # Driving-optimized pipeline
            
            # Step 3: Attenuate artifacts (NOT reject)
            data = self.attenuate_artifacts(data, threshold_factor=3.0)
            
            # Step 4: Light temporal smoothing
            data = self.smooth_temporal(data, window_size=3)
            
            # Step 5: Robust baseline correction (median-based)
            data = self.robust_baseline_correction(data)
            
            # Step 6: Robust normalization (MAD-based)
            data = self.robust_normalize(data)
        else:
            # Standard lab-based pipeline
            data = self.baseline_correction(data)
            data = self.normalize(data)

        return data, quality
