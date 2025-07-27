"""
Command-line interface for the Audio Extractor.

This module provides a user-friendly CLI for video-to-text processing
with comprehensive options and progress reporting.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .audio_processor import VideoToTextPipeline
from .transcription import WhisperTranscriber
from .utils.config import get_logger, get_supported_formats, validate_config

logger = get_logger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Audio Extractor - Convert video to text using AI transcription",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        %(prog)s video.mp4
        %(prog)s video.mp4 -o transcript.txt -c 3.0 -l en
        %(prog)s video.mp4 --json-output --timestamps
        %(prog)s audio.wav --audio-only -c 2.0
                """
    )
    
    # Input
    parser.add_argument(
        "input_file",
        help="Path to input video or audio file"
    )
    
    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "-o", "--output",
        help="Output file path (default: input_name_transcript.txt)"
    )
    output_group.add_argument(
        "--json-output",
        action="store_true",
        help="Save output as JSON with metadata"
    )
    output_group.add_argument(
        "--keep-audio",
        action="store_true",
        help="Keep extracted audio file"
    )
    output_group.add_argument(
        "--keep-chunks",
        action="store_true",
        help="Keep audio chunk files"
    )
    
    # Audio processing options
    audio_group = parser.add_argument_group("Audio Processing")
    audio_group.add_argument(
        "-c", "--chunk-duration",
        type=float,
        default=5.0,
        help="Chunk duration in minutes (default: 5.0)"
    )
    audio_group.add_argument(
        "--overlap",
        type=float,
        default=0.0,
        help="Overlap between chunks in seconds (default: 0.0)"
    )
    audio_group.add_argument(
        "--audio-only",
        action="store_true",
        help="Process existing audio file (skip video extraction)"
    )
    
    # Transcription options
    transcription_group = parser.add_argument_group("Transcription Options")
    transcription_group.add_argument(
        "-l", "--language",
        help="Language code (e.g., en, es, fr) - auto-detect if not specified"
    )
    transcription_group.add_argument(
        "--prompt",
        help="Context prompt to guide transcription"
    )
    transcription_group.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Sampling temperature 0.0-1.0 (default: 0.0 for deterministic)"
    )
    transcription_group.add_argument(
        "--timestamps",
        action="store_true",
        help="Include word-level timestamps (requires JSON output)"
    )
    
    # Utility options
    util_group = parser.add_argument_group("Utility")
    util_group.add_argument(
        "--validate",
        action="store_true",
        help="Validate configuration and exit"
    )
    util_group.add_argument(
        "--estimate-cost",
        action="store_true",
        help="Estimate transcription cost and exit"
    )
    util_group.add_argument(
        "--supported-formats",
        action="store_true",
        help="Show supported file formats and exit"
    )
    util_group.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    util_group.add_argument(
        "--version",
        action="version",
        version="Audio Extractor 0.1.0"
    )
    
    return parser


def check_input_file(file_path: str, audio_only: bool = False) -> Path:
    """
    Validate input file exists and has supported format.
    
    Args:
        file_path: Path to input file
        audio_only: Whether processing audio file only
        
    Returns:
        Path object to the input file
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format not supported
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    formats = get_supported_formats()
    supported_extensions = (
        formats['audio_input'] if audio_only 
        else formats['video_input'] + formats['audio_input']
    )
    
    if path.suffix.lower() not in supported_extensions:
        file_type = "audio" if audio_only else "video/audio"
        raise ValueError(
            f"Unsupported {file_type} format: {path.suffix}\n"
            f"Supported formats: {', '.join(supported_extensions)}"
        )
    
    return path


def generate_output_path(input_path: Path, json_output: bool = False) -> str:
    """Generate default output path based on input file."""
    stem = input_path.stem
    extension = ".json" if json_output else ".txt"
    return str(input_path.parent / f"{stem}_transcript{extension}")


def estimate_processing_cost(input_path: Path, chunk_duration: float) -> dict:
    """Estimate processing cost for the input file."""
    try:
        import ffmpeg
        probe = ffmpeg.probe(str(input_path))
        duration_seconds = float(probe['format']['duration'])
        duration_minutes = duration_seconds / 60
        
        # Create transcriber to get cost estimate
        transcriber = WhisperTranscriber()
        cost_info = transcriber.estimate_cost(duration_minutes)
        
        # Add processing info
        num_chunks = max(1, int(duration_minutes / chunk_duration))
        cost_info.update({
            'file_duration_minutes': duration_minutes,
            'estimated_chunks': num_chunks,
            'chunk_duration_minutes': chunk_duration
        })
        
        return cost_info
        
    except Exception as e:
        logger.error(f"Failed to estimate cost: {e}")
        return {'error': str(e)}


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Set up logging level
    if args.verbose:
        import logging
        logging.getLogger('audio_extractor').setLevel(logging.DEBUG)
    
    try:
        # Handle utility commands
        if args.validate:
            logger.info("Validating configuration...")
            if validate_config():
                logger.info("✓ Configuration is valid")
                return 0
            else:
                logger.error("✗ Configuration validation failed")
                return 1
        
        if args.supported_formats:
            formats = get_supported_formats()
            print("Supported file formats:")
            for category, extensions in formats.items():
                print(f"  {category}: {', '.join(extensions)}")
            return 0
        
        # Validate input file
        input_path = check_input_file(args.input_file, args.audio_only)
        logger.info(f"Processing input file: {input_path}")
        
        # Handle cost estimation
        if args.estimate_cost:
            logger.info("Estimating processing cost...")
            cost_info = estimate_processing_cost(input_path, args.chunk_duration)
            
            if 'error' in cost_info:
                logger.error(f"Cost estimation failed: {cost_info['error']}")
                return 1
            
            print(f"\nCost Estimation:")
            print(f"  File duration: {cost_info['file_duration_minutes']:.1f} minutes")
            print(f"  Estimated chunks: {cost_info['estimated_chunks']}")
            print(f"  Estimated cost: ${cost_info['estimated_cost_usd']:.3f} USD")
            print(f"  Price per minute: ${cost_info['price_per_minute']:.3f}")
            return 0
        
        # Validate configuration
        if not validate_config():
            logger.error("Configuration validation failed. Use --validate for details.")
            return 1
        
        # Generate output path if not provided
        output_path = args.output or generate_output_path(input_path, args.json_output)
        
        # Handle timestamps requirement
        if args.timestamps and not args.json_output:
            logger.warning("Timestamps require JSON output. Enabling --json-output.")
            args.json_output = True
            if not args.output:
                output_path = generate_output_path(input_path, True)
        
        # Initialize pipeline
        logger.info("Initializing processing pipeline...")
        pipeline = VideoToTextPipeline(
            chunk_duration_minutes=args.chunk_duration,
            overlap_seconds=args.overlap
        )
        
        # Process video/audio
        if args.audio_only:
            logger.info("Processing audio file...")
            # For audio-only, we need to use the chunker and transcriber directly
            from .audio_processor import AudioChunker
            
            chunker = AudioChunker(args.chunk_duration, args.overlap)
            transcriber = WhisperTranscriber()
            
            chunk_paths = chunker.split_audio(str(input_path))
            transcriptions = transcriber.transcribe_chunks(
                chunk_paths,
                language=args.language,
                prompt=args.prompt
            )
            
            # Combine transcriptions
            full_transcription = "\n\n".join(transcriptions)
            
            # Save result
            if args.json_output:
                metadata = {
                    'input_file': str(input_path),
                    'chunk_duration_minutes': args.chunk_duration,
                    'overlap_seconds': args.overlap,
                    'language': args.language,
                    'audio_only': True
                }
                transcriber.save_transcription(
                    full_transcription, output_path, "json", metadata
                )
            else:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(full_transcription)
            
            # Cleanup
            if not args.keep_chunks:
                chunker.cleanup()
        
        else:
            logger.info("Processing video file...")
            # Full video processing pipeline
            result = pipeline.process_video(
                video_path=str(input_path),
                language=args.language,
                keep_audio=args.keep_audio,
                keep_chunks=args.keep_chunks
            )
            
            # Transcribe chunks
            transcriber = WhisperTranscriber()
            
            if args.timestamps:
                # Process with timestamps (single file approach)
                logger.info("Transcribing with timestamps...")
                timestamp_result = transcriber.transcribe_with_timestamps(
                    result['audio_path'], args.language
                )
                
                # Save with full metadata
                metadata = {
                    'input_file': str(input_path),
                    'video_info': result['video_info'],
                    'chunk_info': result['chunk_info'],
                    'pipeline_metadata': result['pipeline_metadata'],
                    'timestamps': True
                }
                
                transcriber.save_transcription(
                    timestamp_result['text'], output_path, "json", 
                    {**metadata, 'timestamp_data': timestamp_result}
                )
            
            else:
                # Regular chunk transcription
                transcriptions = transcriber.transcribe_chunks(
                    result['chunk_paths'],
                    language=args.language,
                    prompt=args.prompt
                )
                
                full_transcription = "\n\n".join(transcriptions)
                
                # Save result
                if args.json_output:
                    metadata = {
                        'input_file': str(input_path),
                        'video_info': result['video_info'],
                        'chunk_info': result['chunk_info'],
                        'pipeline_metadata': result['pipeline_metadata'],
                        'transcription_stats': transcriber.get_stats()
                    }
                    transcriber.save_transcription(
                        full_transcription, output_path, "json", metadata
                    )
                else:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(full_transcription)
        
        # Report completion
        logger.info(f"✓ Transcription completed successfully!")
        logger.info(f"✓ Output saved to: {output_path}")
        
        # Show statistics
        if hasattr(transcriber, 'get_stats'):
            stats = transcriber.get_stats()
            logger.info(f"✓ Statistics: {stats['successful_requests']} requests, "
                       f"{stats['total_characters_transcribed']} characters transcribed")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 