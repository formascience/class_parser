"""Configuration utilities for the audio extractor package."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Set level from parameter or environment variable
    log_level = level or os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Avoid duplicate handlers
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logger.level)
        
        # Formatter
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
    
    return logger


def get_config() -> Dict[str, Any]:
    """
    Get application configuration from environment variables.
    
    Returns:
        Dictionary with configuration settings
    """
    return {
        # OpenAI API settings
        'openai_api_key': os.getenv('OPENAI_API_KEY'),
        'openai_model': os.getenv('OPENAI_MODEL', 'whisper-1'),
        
        # Audio processing settings
        'default_chunk_duration': float(os.getenv('DEFAULT_CHUNK_DURATION_MINUTES', '5.0')),
        'default_overlap': float(os.getenv('DEFAULT_OVERLAP_SECONDS', '0.0')),
        'audio_sample_rate': int(os.getenv('AUDIO_SAMPLE_RATE', '16000')),
        'audio_channels': int(os.getenv('AUDIO_CHANNELS', '1')),
        
        # File handling
        'temp_dir': os.getenv('TEMP_DIR'),
        'max_file_size_mb': int(os.getenv('MAX_FILE_SIZE_MB', '25')),
        
        # Logging
        'log_level': os.getenv('LOG_LEVEL', 'INFO'),
        
        # Feature flags
        'enable_video_info': os.getenv('ENABLE_VIDEO_INFO', 'true').lower() == 'true',
        'auto_cleanup': os.getenv('AUTO_CLEANUP', 'true').lower() == 'true',
    }


def validate_config() -> bool:
    """
    Validate that required configuration is present.
    
    Returns:
        True if configuration is valid, False otherwise
    """
    config = get_config()
    logger = get_logger(__name__)
    
    # Check for required API key
    if not config['openai_api_key']:
        logger.error("OPENAI_API_KEY environment variable is required")
        return False
    
    # Check file size limits
    if config['max_file_size_mb'] <= 0:
        logger.error("MAX_FILE_SIZE_MB must be positive")
        return False
    
    # Check audio settings
    if config['audio_sample_rate'] <= 0:
        logger.error("AUDIO_SAMPLE_RATE must be positive")
        return False
    
    if config['audio_channels'] not in [1, 2]:
        logger.error("AUDIO_CHANNELS must be 1 (mono) or 2 (stereo)")
        return False
    
    return True


def setup_directories(config: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """
    Set up required directories for the application.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Dictionary with created directory paths
    """
    if config is None:
        config = get_config()
    
    logger = get_logger(__name__)
    
    # Base temp directory
    base_temp = config.get('temp_dir') or os.path.join(os.getcwd(), 'temp')
    
    directories = {
        'temp': base_temp,
        'audio': os.path.join(base_temp, 'audio'),
        'chunks': os.path.join(base_temp, 'chunks'),
        'transcripts': os.path.join(base_temp, 'transcripts')
    }
    
    # Create directories
    for name, path in directories.items():
        Path(path).mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {name} -> {path}")
    
    return directories


def get_supported_formats() -> Dict[str, list]:
    """
    Get supported file formats for different operations.
    
    Returns:
        Dictionary with supported formats
    """
    return {
        'video_input': ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'],
        'audio_input': ['.wav', '.mp3', '.flac', '.aac', '.ogg', '.m4a'],
        'audio_output': ['.wav'],  # Optimized for Whisper
        'transcript_output': ['.txt', '.json', '.srt', '.vtt']
    } 