"""
EEG Processing Package - Fumorive Driver Monitoring
====================================================

Modules for EEG acquisition, preprocessing, feature extraction,
and cognitive analysis using Muse 2 headband.

Part of Fumorive Driver Monitoring System.
"""

from .acquisition import EEGAcquisition
from .preprocessing import EEGPreprocessor
from .features import EEGFeatureExtractor
from .analysis import CognitiveAnalyzer

__all__ = [
    "EEGAcquisition",
    "EEGPreprocessor", 
    "EEGFeatureExtractor",
    "CognitiveAnalyzer"
]

__version__ = "1.0.0"
__author__ = "Fumorive Team"
