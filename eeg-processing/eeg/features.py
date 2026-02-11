"""
features.py
===========
Module for EEG feature extraction.

Purpose:
Extract meaningful EEG features (band power, ratios)
for cognitive state analysis (fatigue, stress, focus).
"""

import numpy as np
from scipy.signal import welch
from typing import Dict, Tuple


class EEGFeatureExtractor:
    """
    EEG feature extraction using spectral analysis.
    """

    def __init__(
        self,
        sampling_rate: float,
        nperseg: int = 256
    ):
        """
        Initialize feature extractor.

        Parameters
        ----------
        sampling_rate : float
            EEG sampling rate (Hz)
        nperseg : int
            Segment length for Welch PSD
        """
        self.fs = sampling_rate
        self.nperseg = nperseg

        # Frequency bands (Hz)
        self.bands = {
            "delta": (1, 4),
            "theta": (4, 8),
            "alpha": (8, 13),
            "beta": (13, 30),
            "gamma": (30, 45)
        }

    # =========================
    # CORE METHODS
    # =========================
    def _band_power(
        self,
        freqs: np.ndarray,
        psd: np.ndarray,
        band: Tuple[float, float]
    ) -> float:
        """
        Compute band power using PSD integration.
        """
        low, high = band
        idx = np.logical_and(freqs >= low, freqs <= high)
        return np.trapz(psd[idx], freqs[idx])

    def compute_band_powers(self, data: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Compute band power for each EEG channel.

        Parameters
        ----------
        data : np.ndarray
            Clean EEG data (samples, channels)

        Returns
        -------
        Dict[str, np.ndarray]
            Band powers per channel
        """
        band_powers = {band: [] for band in self.bands}

        for ch in range(data.shape[1]):
            freqs, psd = welch(
                data[:, ch],
                fs=self.fs,
                nperseg=self.nperseg
            )

            for band, freq_range in self.bands.items():
                power = self._band_power(freqs, psd, freq_range)
                band_powers[band].append(power)

        # Convert to numpy arrays
        for band in band_powers:
            band_powers[band] = np.array(band_powers[band])

        return band_powers

    # =========================
    # RATIO FEATURES
    # =========================
    def compute_ratios(
        self,
        band_powers: Dict[str, np.ndarray]
    ) -> Dict[str, np.ndarray]:
        """
        Compute cognitive EEG ratios.

        Returns
        -------
        Dict[str, np.ndarray]
            Ratio features per channel
        """
        eps = 1e-8  # avoid division by zero

        ratios = {
            "theta_alpha": band_powers["theta"] / (band_powers["alpha"] + eps),
            "beta_alpha": band_powers["beta"] / (band_powers["alpha"] + eps),
            "alpha_beta": band_powers["alpha"] / (band_powers["beta"] + eps)
        }

        return ratios

    # =======================   ==
    # FULL PIPELINE
    # =========================
    def extract(self, data: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Full feature extraction pipeline.

        Parameters
        ----------
        data : np.ndarray
            Clean EEG data (samples, channels)

        Returns
        -------
        Dict[str, np.ndarray]
            EEG features
        """
        if data.size == 0:
            return {}

        band_powers = self.compute_band_powers(data)
        ratios = self.compute_ratios(band_powers)

        features = {
            **band_powers,
            **ratios
        }

        return features
