"""
OpenAI Whisper API client for audio transcription.

This module handles communication with OpenAI's Whisper API for
high-quality speech-to-text transcription.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI

from audio_extractor.utils.config import get_config, get_logger

logger = get_logger(__name__)


class WhisperTranscriber:
    """
    Client for OpenAI Whisper API transcription services.
    
    This class handles authentication, API calls, and response processing
    for audio transcription using OpenAI's Whisper model.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "whisper-1"):
        """
        Initialize the Whisper transcriber.
        
        Args:
            api_key: OpenAI API key. If None, loads from environment.
            model: Whisper model to use (default: whisper-1)
        """
        config = get_config()
        self.api_key = api_key or config['openai_api_key']
        self.model = model or config['openai_model']
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)
        
        # Statistics tracking
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_audio_duration': 0.0,
            'total_characters_transcribed': 0
        }
    
    def transcribe_audio(self, 
                        audio_path: str, 
                        language: Optional[str] = None,
                        prompt: Optional[str] = None,
                        temperature: float = 0.0,
                        response_format: str = "text") -> str:
        """
        Transcribe a single audio file.
        
        Args:
            audio_path: Path to the audio file
            language: Language code (e.g., 'en', 'es', 'fr')
            prompt: Optional prompt to guide transcription
            temperature: Sampling temperature (0.0 = deterministic)
            response_format: Response format ('text', 'json', 'srt', 'vtt')
            
        Returns:
            Transcribed text
            
        Raises:
            FileNotFoundError: If audio file doesn't exist
            RuntimeError: If transcription fails
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Check file size (Whisper has 25MB limit)
        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        max_size = get_config()['max_file_size_mb']
        
        if file_size_mb > max_size:
            raise ValueError(f"Audio file too large: {file_size_mb:.1f}MB > {max_size}MB limit")
        
        logger.info(f"Transcribing audio file: {audio_path} ({file_size_mb:.1f}MB)")
        
        try:
            self.stats['total_requests'] += 1
            
            with open(audio_path, "rb") as audio_file:
                # Build parameters dict with only non-None values
                params = {
                    "model": self.model,
                    "file": audio_file,
                    "response_format": response_format,
                    "temperature": temperature,
                }
                if language:
                    params["language"] = language
                if prompt:
                    params["prompt"] = prompt
                
                # Make API call
                response = self.client.audio.transcriptions.create(**params)  # type: ignore
            
            # Extract text from response
            transcription = response.text if hasattr(response, 'text') else str(response)
            
            # Update statistics
            self.stats['successful_requests'] += 1
            self.stats['total_characters_transcribed'] += len(transcription)
            
            logger.info(f"Transcription completed: {len(transcription)} characters")
            return transcription
            
        except Exception as e:
            self.stats['failed_requests'] += 1
            logger.error(f"Transcription failed for {audio_path}: {e}")
            raise RuntimeError(f"Failed to transcribe audio: {e}")
    
    def transcribe_chunks(self, 
                         chunk_paths: List[str], 
                         language: Optional[str] = None,
                         prompt: Optional[str] = None,
                         preserve_order: bool = True,
                         combine_output: bool = True) -> List[str]:
        """
        Transcribe multiple audio chunks.
        
        Args:
            chunk_paths: List of paths to audio chunks
            language: Language code for all chunks
            prompt: Optional prompt for context
            preserve_order: Whether to maintain chunk order
            combine_output: Whether to return combined text or separate chunks
            
        Returns:
            List of transcribed texts (or single combined text if combine_output=True)
        """
        if not chunk_paths:
            logger.warning("No chunks provided for transcription")
            return []
        
        logger.info(f"Transcribing {len(chunk_paths)} audio chunks")
        
        transcriptions = []
        failed_chunks = []
        
        for i, chunk_path in enumerate(chunk_paths, 1):
            try:
                logger.debug(f"Transcribing chunk {i}/{len(chunk_paths)}: {chunk_path}")
                
                # Use chunk-specific prompt if provided
                chunk_prompt = f"{prompt} [Chunk {i}]" if prompt else None
                
                transcription = self.transcribe_audio(
                    chunk_path, 
                    language=language,
                    prompt=chunk_prompt,
                    response_format="text"
                )
                
                transcriptions.append({
                    'index': i - 1,
                    'path': chunk_path,
                    'text': transcription,
                    'success': True
                })
                
            except Exception as e:
                logger.error(f"Failed to transcribe chunk {i}: {e}")
                failed_chunks.append({'index': i - 1, 'path': chunk_path, 'error': str(e)})
                transcriptions.append({
                    'index': i - 1,
                    'path': chunk_path,
                    'text': "",
                    'success': False,
                    'error': str(e)
                })
        
        # Sort by index if preserving order
        if preserve_order:
            transcriptions.sort(key=lambda x: x['index'])
        
        # Report results
        successful = sum(1 for t in transcriptions if t['success'])
        logger.info(f"Transcription completed: {successful}/{len(chunk_paths)} chunks successful")
        
        if failed_chunks:
            logger.warning(f"Failed chunks: {[c['index'] + 1 for c in failed_chunks]}")
        
        # Return format based on combine_output
        if combine_output:
            # Return list of text strings only
            return [t['text'] for t in transcriptions]
        else:
            # Return full metadata
            return transcriptions
    
    def _convert_to_json_serializable(self, obj) -> Any:
        """
        Convert OpenAI transcription objects to JSON-serializable format.
        
        Args:
            obj: Object to convert (TranscriptionWord, TranscriptionSegment, or other)
            
        Returns:
            JSON-serializable representation of the object
        """
        if hasattr(obj, '__dict__'):
            # Convert object with attributes to dictionary
            return {key: self._convert_to_json_serializable(value) 
                   for key, value in obj.__dict__.items()}
        elif isinstance(obj, list):
            # Convert list of objects
            return [self._convert_to_json_serializable(item) for item in obj]
        elif isinstance(obj, dict):
            # Convert dictionary values
            return {key: self._convert_to_json_serializable(value) 
                   for key, value in obj.items()}
        else:
            # Return primitive types as-is
            return obj

    def _create_timestamp_text(self, segments_data: List[Dict[str, Any]]) -> str:
        """
        Create readable timestamp text format from segments data.
        
        Args:
            segments_data: List of segment dictionaries with start, end, and text
            
        Returns:
            Formatted text with timestamps (start:end text per line)
        """
        lines = []
        
        for segment in segments_data:
            start = segment.get('start', 0)
            end = segment.get('end', 0)
            text = segment.get('text', '').strip()
            
            if text:  # Only add non-empty segments
                # Format: start:end text
                line = f"{start:.2f}:{end:.2f} {text}"
                lines.append(line)
        
        return '\n'.join(lines)
    
    def _save_to_volume_transcripts(self, audio_path: str, result: Dict[str, Any], 
                                   serializable_segments: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Save transcription files to volume/transcripts folder structure.
        
        Args:
            audio_path: Original audio file path
            result: Transcription result dictionary
            serializable_segments: JSON-serializable segments data
            
        Returns:
            Dictionary with paths to saved files
        """
        audio_file_path = Path(audio_path)
        
        # Find the volume folder by looking for it in the path hierarchy
        volume_path = None
        current_path = audio_file_path.parent
        
        # Search up the directory tree for 'volume' folder
        while current_path != current_path.parent:
            if current_path.name == 'volume':
                volume_path = current_path
                break
            current_path = current_path.parent
        
        # If no volume folder found, create transcripts folder next to audio
        if volume_path is None:
            transcripts_folder = audio_file_path.parent / "transcripts"
        else:
            transcripts_folder = volume_path / "transcripts"
        
        # Create subfolders
        json_folder = transcripts_folder / "json"
        parsed_folder = transcripts_folder / "parsed"
        
        os.makedirs(json_folder, exist_ok=True)
        os.makedirs(parsed_folder, exist_ok=True)
        
        base_filename = audio_file_path.stem
        
        # Save JSON transcription
        json_filename = f"{base_filename}_transcription.json"
        json_path = json_folder / json_filename
        
        serializable_words = self._convert_to_json_serializable(result['words'])
        
        self.save_transcription(
            transcription=result['text'],
            output_path=str(json_path),
            format="json",
            metadata={
                'audio_file': str(audio_file_path),
                'language': result['language'],
                'duration': result['duration'],
                'words': serializable_words,
                'segments': serializable_segments,
                'has_timestamps': True,
                'transcription_type': 'with_timestamps'
            }
        )
        
        # Create and save parsed timestamp text
        parsed_filename = f"{base_filename}_timestamps.txt"
        parsed_path = parsed_folder / parsed_filename
        
        timestamp_text = self._create_timestamp_text(serializable_segments)
        
        with open(parsed_path, 'w', encoding='utf-8') as f:
            f.write(f"# Timestamp Transcription: {base_filename}\n")
            f.write(f"# Duration: {result['duration']:.2f} seconds\n")
            f.write(f"# Language: {result['language']}\n")
            f.write(f"# Format: start_time:end_time text\n")
            f.write("#" + "="*50 + "\n\n")
            f.write(timestamp_text)
        
        return {
            'json_file': str(json_path),
            'parsed_file': str(parsed_path),
            'transcripts_folder': str(transcripts_folder)
        }

    def transcribe_with_timestamps(self, audio_path: str, 
                                        language: Optional[str] = None, 
                                        prompt: Optional[str] = None,
                                        timestamp_granularities: Optional[List[str]] = None,
                                        output_folder: Optional[str] = None, 
                                        save_to_file: bool = True) -> Dict[str, Any]:
        """
        Transcribe audio with word-level timestamps.
        
        Args:
            audio_path: Path to the audio file
            language: Language code
            prompt: Context prompt for transcription
            timestamp_granularities: List of granularities (e.g., ["word"], ["segment"], ["word", "segment"])
            output_folder: Custom output folder (if None, uses volume/transcripts structure)
            save_to_file: Whether to automatically save the transcription to file
            
        Returns:
            Dictionary with text, timestamp information, and output file paths if saved
        """
        logger.info(f"Transcribing with timestamps: {audio_path}")
        
        # Set default timestamp granularities if not provided
        if timestamp_granularities is None:
            timestamp_granularities = ["word", "segment"]
        
        try:
            with open(audio_path, "rb") as audio_file:
                params = {
                    "model": self.model,
                    "file": audio_file,
                    "response_format": "verbose_json",
                    "timestamp_granularities": timestamp_granularities
                }
                if language:
                    params["language"] = language
                if prompt:
                    params["prompt"] = prompt
                response = self.client.audio.transcriptions.create(**params)  # type: ignore
            
            result = {
                'text': response.text,
                'language': response.language,
                'duration': response.duration,
                'words': response.words if hasattr(response, 'words') else [],
                'segments': response.segments if hasattr(response, 'segments') else []
            }
            
            # Save to file if requested
            if save_to_file:
                # Convert objects to JSON-serializable format
                serializable_segments = self._convert_to_json_serializable(result['segments'])
                
                if output_folder is None:
                    # Use volume/transcripts structure
                    saved_files = self._save_to_volume_transcripts(audio_path, result, serializable_segments)
                    result.update(saved_files)
                    
                    logger.info(f"JSON transcription saved to: {saved_files['json_file']}")
                    logger.info(f"Parsed timestamps saved to: {saved_files['parsed_file']}")
                    
                else:
                    # Use custom output folder (original behavior)
                    audio_file_path = Path(audio_path)
                    os.makedirs(output_folder, exist_ok=True)
                    
                    output_filename = f"{audio_file_path.stem}_transcription.json"
                    output_path = os.path.join(output_folder, output_filename)
                    
                    serializable_words = self._convert_to_json_serializable(result['words'])
                    
                    self.save_transcription(
                        transcription=result['text'],
                        output_path=output_path,
                        format="json",
                        metadata={
                            'audio_file': str(audio_file_path),
                            'language': result['language'],
                            'duration': result['duration'],
                            'words': serializable_words,
                            'segments': serializable_segments,
                            'has_timestamps': True,
                            'transcription_type': 'with_timestamps'
                        }
                    )
                    
                    result['output_file'] = output_path
                    logger.info(f"Transcription with timestamps saved to: {output_path}")
            
            return result
            
        except Exception as e:
            logger.error(f"Timestamp transcription failed: {e}")
            raise RuntimeError(f"Failed to transcribe with timestamps: {e}")
    
    def save_transcription(self, 
                          transcription: str, 
                          output_path: str,
                          format: str = "txt",
                          metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Save transcription to file with optional metadata.
        
        Args:
            transcription: The transcribed text
            output_path: Path to save the transcription
            format: Output format ('txt', 'json')
            metadata: Optional metadata to include
            
        Returns:
            Path to the saved file
        """
        output_path_obj = Path(output_path)
        
        if format.lower() == "json":
            # Save as structured JSON
            data = {
                'transcription': transcription,
                'metadata': metadata or {},
                'stats': self.get_stats()
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        else:
            # Save as plain text
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(transcription)
                
                # Add metadata as comments if provided
                if metadata:
                    f.write('\n\n# Metadata\n')
                    for key, value in metadata.items():
                        f.write(f"# {key}: {value}\n")
        
        logger.info(f"Transcription saved: {output_path}")
        return str(output_path)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get transcription statistics.
        
        Returns:
            Dictionary with usage statistics
        """
        return {
            **self.stats,
            'success_rate': (
                self.stats['successful_requests'] / max(self.stats['total_requests'], 1)
            ) * 100,
            'avg_characters_per_request': (
                self.stats['total_characters_transcribed'] / max(self.stats['successful_requests'], 1)
            )
        }
    
    def reset_stats(self):
        """Reset statistics counters."""
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_audio_duration': 0.0,
            'total_characters_transcribed': 0
        }
        logger.info("Statistics reset")
    
    def estimate_cost(self, audio_duration_minutes: float) -> Dict[str, float]:
        """
        Estimate transcription cost based on audio duration.
        
        Args:
            audio_duration_minutes: Duration of audio in minutes
            
        Returns:
            Dictionary with cost estimates
        """
        # OpenAI Whisper pricing (as of 2024)
        price_per_minute = 0.006  # $0.006 per minute
        
        estimated_cost = audio_duration_minutes * price_per_minute
        
        return {
            'duration_minutes': audio_duration_minutes,
            'estimated_cost_usd': estimated_cost,
            'price_per_minute': price_per_minute,
            'currency': 'USD'
        } 