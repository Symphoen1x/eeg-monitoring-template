"""
acquisition.py
================
Module for EEG data acquisition from Muse 2 via LSL (muselsl).
Purpose : Acquire real-time EEG data for simulator-based cognitive analysis
"""

import time
import numpy as np
from pylsl import StreamInlet, resolve_streams
from typing import List, Tuple, Optional


class EEGAcquisition:
    """
    EEG Acquisition handler using LSL streams.
    """

    def __init__(
        self,
        stream_type: str = "EEG",
        timeout: int = 20,
        max_chunklen: int = 12
    ):
        """
        Initialize EEG acquisition.

        Parameters
        ----------
        stream_type : str
            LSL stream type to resolve (default: 'EEG')
        timeout : int
            Time (seconds) to wait for LSL stream
        max_chunklen : int
            Maximum samples per chunk pulled from LSL
        """
        self.stream_type = stream_type
        self.timeout = timeout
        self.max_chunklen = max_chunklen

        self.inlet: Optional[StreamInlet] = None
        self.channel_labels: List[str] = []
        self.sampling_rate: Optional[float] = None

    def connect(self) -> None:
        """
        Resolve and connect to EEG LSL stream.
        """
        print("[INFO] Resolving LSL EEG stream...")
        print(f"[DEBUG] Searching for {self.timeout} seconds...")
        
        # Use resolve_streams instead of resolve_byprop
        all_streams = resolve_streams(wait_time=self.timeout)
        print(f"[DEBUG] Found {len(all_streams)} total stream(s)")
        
        # Filter by stream type
        streams = [s for s in all_streams if s.type() == self.stream_type]
        print(f"[DEBUG] Found {len(streams)} EEG stream(s)")

        if not streams:
            raise RuntimeError("No EEG LSL stream found. Is muselsl stream running?")

        print("[DEBUG] Creating StreamInlet...")
        self.inlet = StreamInlet(
            streams[0],
            max_chunklen=self.max_chunklen,
            recover=True
        )
        print("[DEBUG] StreamInlet created")

        print("[DEBUG] Getting stream info...")
        info = self.inlet.info()
        self.sampling_rate = info.nominal_srate()
        print(f"[DEBUG] Sampling rate: {self.sampling_rate}")

        # Read channel labels using channel count
        print("[DEBUG] Reading channel labels...")
        n_channels = info.channel_count()
        print(f"[DEBUG] Channel count: {n_channels}")
        
        # Use default Muse channel labels if reading fails
        self.channel_labels = ["TP9", "AF7", "AF8", "TP10", "AUX"][:n_channels]

        print("[SUCCESS] Connected to EEG stream")
        print(f"          Sampling rate : {self.sampling_rate} Hz")
        print(f"          Channels      : {self.channel_labels}")

    def pull_chunk(self, duration: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Pull EEG data for a specific duration.

        Parameters
        ----------
        duration : float
            Duration in seconds

        Returns
        -------
        data : np.ndarray
            EEG data array with shape (samples, channels)
        timestamps : np.ndarray
            Corresponding timestamps
        """
        if self.inlet is None:
            raise RuntimeError("EEG stream not connected. Call connect() first.")

        data_buffer = []
        ts_buffer = []

        start_time = time.time()

        while (time.time() - start_time) < duration:
            chunk, timestamps = self.inlet.pull_chunk(timeout=0.5)

            if timestamps:
                data_buffer.append(chunk)
                ts_buffer.append(timestamps)

        if not data_buffer:
            return np.empty((0, 0)), np.empty((0,))

        data = np.vstack(data_buffer)
        timestamps = np.hstack(ts_buffer)

        return data, timestamps

    def get_latest_sample(self) -> Tuple[np.ndarray, float]:
        """
        Pull a single EEG sample.

        Returns
        -------
        sample : np.ndarray
            EEG sample (channels,)
        timestamp : float
            Sample timestamp
        """
        if self.inlet is None:
            raise RuntimeError("EEG stream not connected. Call connect() first.")

        sample, timestamp = self.inlet.pull_sample(timeout=1.0)

        if sample is None:
            raise RuntimeError("Failed to retrieve EEG sample.")

        return np.array(sample), timestamp

    def close(self) -> None:
        """
        Safely close EEG stream.
        """
        print("[INFO] Closing EEG stream...")
        self.inlet = None
