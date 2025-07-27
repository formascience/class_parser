"""
Audio Extractor - AI-powered video to text transcription toolkit.

A Python package for extracting audio from video files, splitting into chunks,
and transcribing using AI models like OpenAI's Whisper.
"""

from .audio_processor import AudioChunker, AudioExtractor, VideoToTextPipeline
from .transcription import WhisperTranscriber

__version__ = "0.1.0"
__author__ = "Youssef Janjar"
__description__ = "AI-powered video to text transcription toolkit"

__all__ = [
    "AudioExtractor",
    "AudioChunker", 
    "VideoToTextPipeline",
    "WhisperTranscriber"
] 