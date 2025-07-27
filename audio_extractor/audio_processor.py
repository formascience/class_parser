"""
Core audio processing functionality for video-to-text pipeline.

This module contains all the classes needed to extract audio from video files,
split audio into manageable chunks, and coordinate the overall processing pipeline.
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import List, Optional

import ffmpeg
from pydub import AudioSegment

from .utils.config import get_logger

logger = get_logger(__name__)


class AudioExtractor:
    """
    Extract audio from video files using FFmpeg.
    
    This class handles the conversion of video files to audio format optimized
    for speech recognition systems like Whisper (16kHz, mono, WAV).
    """
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize the AudioExtractor.
        
        Args:
            temp_dir: Optional directory for temporary files. If None, creates one automatically.
        """
        self.temp_dir = temp_dir or tempfile.mkdtemp()
        self._ensure_temp_dir()
    
    def _ensure_temp_dir(self):
        """Ensure the temporary directory exists."""
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir, exist_ok=True)
    
    def extract_audio(self, video_path: str, output_path: Optional[str] = None) -> str:
        """
        Extract audio from video file.
        
        Args:
            video_path: Path to the input video file
            output_path: Optional path for output audio file. If None, creates temp file.
            
        Returns:
            Path to the extracted audio file
            
        Raises:
            FileNotFoundError: If video file doesn't exist
            RuntimeError: If FFmpeg extraction fails
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        video_name = Path(video_path).stem


        if not os.path.exists(output_path):
            os.makedirs(output_path, exist_ok=True)

        output_path = os.path.join(output_path, f"{video_name}_audio.wav")
        logger.info(f"Extracting audio from {video_path}")
        
        try:
            # Extract audio optimized for speech recognition
            (
                ffmpeg
                .input(video_path)
                .output(
                    output_path, 
                    acodec='pcm_s16le',  # 16-bit PCM
                    ac=1,                # Mono channel
                    ar='16000'           # 16kHz sample rate (optimal for Whisper)
                )
                .overwrite_output()
                .run(quiet=True, capture_stdout=True, capture_stderr=True)
            )
            
            logger.info(f"Audio extracted successfully: {output_path}")
            return output_path
            
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"FFmpeg extraction failed: {error_msg}")
            raise RuntimeError(f"Failed to extract audio: {error_msg}")
    
    def get_video_info(self, video_path: str) -> dict:
        """
        Get information about the video file.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dictionary with video information
        """
        try:
            probe = ffmpeg.probe(video_path)
            video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            audio_info = next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)
            
            return {
                'duration': float(probe['format']['duration']),
                'video_codec': video_info['codec_name'],
                'audio_codec': audio_info['codec_name'] if audio_info else None,
                'resolution': f"{video_info['width']}x{video_info['height']}",
                'fps': eval(video_info['r_frame_rate'])
            }
        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
            return {}
    
    def cleanup(self):
        """Clean up temporary files."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
            logger.info("Temporary files cleaned up")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.cleanup()
        except:
            pass  # Ignore cleanup errors during destruction


class AudioChunker:
    """
    Split audio files into smaller, manageable chunks.
    
    This class handles the segmentation of large audio files into smaller pieces
    suitable for API processing with size/time limits.
    """
    
    def __init__(self, chunk_duration_minutes: float = 5.0, overlap_seconds: float = 0.0):
        """
        Initialize the AudioChunker.
        
        Args:
            chunk_duration_minutes: Duration of each chunk in minutes
            overlap_seconds: Overlap between chunks in seconds (helps with continuity)
        """
        self.chunk_duration_ms = int(chunk_duration_minutes * 60 * 1000)
        self.overlap_ms = int(overlap_seconds * 1000)
        self.temp_dir = tempfile.mkdtemp()
    
    def split_audio(self, audio_path: str, output_dir: Optional[str] = None, 
                   chunk_duration_minutes: Optional[float] = None) -> List[str]:
        """
        Split audio file into chunks.
        
        Args:
            audio_path: Path to the input audio file
            output_dir: Directory to save chunks. If None, creates folder named after file.
            chunk_duration_minutes: Chunk duration in minutes. If None, uses default from init.
            
        Returns:
            List of paths to audio chunks
            
        Raises:
            FileNotFoundError: If audio file doesn't exist
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Use custom chunk duration if provided
        chunk_duration_ms = (
            int(chunk_duration_minutes * 60 * 1000) 
            if chunk_duration_minutes 
            else self.chunk_duration_ms
        )
        
        # Create output directory based on file name if not provided
        audio_name = Path(audio_path).stem
        if output_dir is None:
            base_dir = Path(audio_path).parent
            output_dir = str(base_dir / f"{audio_name}_chunks")
        
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"Splitting audio into {chunk_duration_ms/60000:.1f} minute chunks")
        logger.info(f"Output directory: {output_dir}")
        
        # Load audio file
        audio = AudioSegment.from_file(audio_path)
        total_duration_ms = len(audio)
        
        # Calculate chunk positions with overlap
        chunk_paths = []
        start_time = 0
        chunk_num = 1
        
        while start_time < total_duration_ms:
            end_time = min(start_time + chunk_duration_ms, total_duration_ms)
            
            # Extract chunk
            chunk = audio[start_time:end_time]
            chunk_path = os.path.join(output_dir, f"{audio_name}_chunk_{chunk_num:03d}.wav")
            
            # Export chunk
            chunk.export(chunk_path, format="wav")
            chunk_paths.append(chunk_path)
            
            logger.debug(f"Created chunk {chunk_num}: {chunk_path} ({len(chunk)/1000:.1f}s)")
            
            # Move to next chunk with overlap consideration
            start_time = end_time - self.overlap_ms
            chunk_num += 1
            
            # Prevent infinite loop
            if end_time >= total_duration_ms:
                break
        
        logger.info(f"Created {len(chunk_paths)} audio chunks")
        return chunk_paths
    
    def get_chunk_info(self, chunk_paths: List[str]) -> List[dict]:
        """
        Get information about each chunk.
        
        Args:
            chunk_paths: List of chunk file paths
            
        Returns:
            List of dictionaries with chunk information
        """
        chunk_info = []
        for i, path in enumerate(chunk_paths):
            try:
                audio = AudioSegment.from_file(path)
                chunk_info.append({
                    'index': i,
                    'path': path,
                    'duration_seconds': len(audio) / 1000,
                    'size_bytes': os.path.getsize(path)
                })
            except Exception as e:
                logger.error(f"Error getting info for chunk {path}: {e}")
                chunk_info.append({
                    'index': i,
                    'path': path,
                    'error': str(e)
                })
        
        return chunk_info
    
    def cleanup(self):
        """Clean up temporary files."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
            logger.info("Chunker temporary files cleaned up")


class VideoToTextPipeline:
    """
    Complete pipeline orchestrating video-to-text conversion.
    
    This class coordinates the entire process: video → audio → chunks → transcription.
    """
    
    def __init__(self, 
                 chunk_duration_minutes: float = 5.0,
                 overlap_seconds: float = 0.0,
                 temp_dir: Optional[str] = None):
        """
        Initialize the complete pipeline.
        
        Args:
            chunk_duration_minutes: Duration of each audio chunk in minutes
            overlap_seconds: Overlap between chunks in seconds
            temp_dir: Optional directory for temporary files
        """
        self.temp_dir = temp_dir or tempfile.mkdtemp()
        self.extractor = AudioExtractor(temp_dir=self.temp_dir)
        self.chunker = AudioChunker(
            chunk_duration_minutes=chunk_duration_minutes,
            overlap_seconds=overlap_seconds
        )
        
        # Store pipeline metadata
        self.metadata = {
            'chunk_duration_minutes': chunk_duration_minutes,
            'overlap_seconds': overlap_seconds,
            'temp_dir': self.temp_dir
        }
    
    def process_video(self, 
                     video_path: str, 
                     output_file: Optional[str] = None,
                     language: Optional[str] = None,
                     keep_audio: bool = False,
                     keep_chunks: bool = False) -> dict:
        """
        Process video through the complete pipeline.
        
        Args:
            video_path: Path to the input video file
            output_file: Optional path to save the final transcription
            language: Language code for transcription
            keep_audio: Whether to keep the extracted audio file
            keep_chunks: Whether to keep the chunk files
            
        Returns:
            Dictionary with processing results and metadata
        """
        logger.info(f"Starting video processing pipeline: {video_path}")
        
        try:
            # Step 1: Extract audio
            logger.info("Step 1: Extracting audio from video")
            audio_path = self.extractor.extract_audio(video_path)
            
            # Step 2: Get video info
            video_info = self.extractor.get_video_info(video_path)
            
            # Step 3: Split into chunks
            logger.info("Step 2: Splitting audio into chunks")
            chunk_paths = self.chunker.split_audio(audio_path)
            chunk_info = self.chunker.get_chunk_info(chunk_paths)
            
            # Prepare result metadata
            result = {
                'status': 'audio_processed',
                'video_path': video_path,
                'audio_path': audio_path,
                'chunk_paths': chunk_paths,
                'video_info': video_info,
                'chunk_info': chunk_info,
                'pipeline_metadata': self.metadata,
                'chunks_ready_for_transcription': True
            }
            
            # Clean up if requested
            if not keep_chunks:
                # Will be cleaned up by transcription module
                pass
            
            if not keep_audio:
                # Mark for cleanup after transcription
                result['cleanup_audio'] = True
            
            logger.info(f"Audio processing completed. {len(chunk_paths)} chunks ready for transcription")
            return result
            
        except Exception as e:
            logger.error(f"Pipeline processing failed: {e}")
            raise RuntimeError(f"Video processing pipeline failed: {e}")
    
    def get_pipeline_stats(self) -> dict:
        """Get statistics about the current pipeline configuration."""
        return {
            'chunk_duration_minutes': self.metadata['chunk_duration_minutes'],
            'overlap_seconds': self.metadata['overlap_seconds'],
            'temp_dir': self.temp_dir,
            'temp_dir_exists': os.path.exists(self.temp_dir)
        }
    
    def cleanup(self):
        """Clean up all temporary files."""
        self.extractor.cleanup()
        self.chunker.cleanup()
        
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
            logger.info("Pipeline temporary files cleaned up")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.cleanup()
        except:
            pass  # Ignore cleanup errors during destruction 