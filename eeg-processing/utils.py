"""
utils.py
========
Utility functions for EEG Systems.

Common helper functions used across modules.
"""

import os
import csv
import logging
from datetime import datetime
from typing import List, Optional
import numpy as np


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Setup logging configuration.
    
    Parameters
    ----------
    level : str
        Logging level (DEBUG, INFO, WARNING, ERROR)
    log_file : str, optional
        Path to log file. If None, logs to console only.
    
    Returns
    -------
    logging.Logger
        Configured logger instance
    """
    logger = logging.getLogger("eeg_systems")
    logger.setLevel(getattr(logging, level.upper()))
    
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def generate_timestamp() -> str:
    """
    Generate formatted timestamp string.
    
    Returns
    -------
    str
        Timestamp in format: YYYY-MM-DD-HH.MM.SS
    """
    return datetime.now().strftime("%Y-%m-%d-%H.%M.%S")


def ensure_directory(path: str) -> None:
    """
    Create directory if it doesn't exist.
    
    Parameters
    ----------
    path : str
        Directory path to create
    """
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"[INFO] Created directory: {path}")


def save_eeg_to_csv(
    data: np.ndarray,
    timestamps: np.ndarray,
    channel_labels: List[str],
    filepath: str
) -> None:
    """
    Save EEG data to CSV file.
    
    Parameters
    ----------
    data : np.ndarray
        EEG data array (samples, channels)
    timestamps : np.ndarray
        Timestamp array
    channel_labels : List[str]
        Channel names
    filepath : str
        Output file path
    """
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        header = ["timestamp"] + channel_labels
        writer.writerow(header)
        
        # Data rows
        for i in range(len(timestamps)):
            row = [timestamps[i]] + list(data[i])
            writer.writerow(row)
    
    print(f"[SUCCESS] Saved EEG data to: {filepath}")


def validate_eeg_data(data: np.ndarray) -> bool:
    """
    Validate EEG data array.
    
    Parameters
    ----------
    data : np.ndarray
        EEG data to validate
    
    Returns
    -------
    bool
        True if data is valid
    """
    if data is None:
        return False
    
    if data.size == 0:
        return False
    
    if np.isnan(data).any():
        print("[WARN] EEG data contains NaN values")
        return False
    
    if np.isinf(data).any():
        print("[WARN] EEG data contains infinite values")
        return False
    
    return True


def format_cognitive_result(result: dict) -> str:
    """
    Format cognitive analysis result for display.
    
    Parameters
    ----------
    result : dict
        Analysis result from CognitiveAnalyzer
    
    Returns
    -------
    str
        Formatted string for display
    """
    state_emoji = {
        "fatigue": "😴",
        "stress": "😰",
        "focused": "🎯",
        "normal": "😊",
        "unknown": "❓"
    }
    
    emoji = state_emoji.get(result.get("state", "unknown"), "❓")
    state = result.get("state", "unknown").upper()
    confidence = result.get("confidence", 0.0)
    
    output = f"\n{'='*40}\n"
    output += f"  {emoji} Cognitive State: {state}\n"
    output += f"  Confidence: {confidence:.2f}\n"
    output += f"{'='*40}\n"
    
    metrics = result.get("metrics", {})
    if metrics:
        output += "  Metrics:\n"
        for key, value in metrics.items():
            output += f"    • {key}: {value:.3f}\n"
    
    return output
