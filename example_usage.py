"""
Example usage of the audio extractor classes.
"""

import os

from audio_extractor import (
    AudioChunker,
    AudioExtractor,
    VideoToTextPipeline,
    WhisperTranscriber,
)


def example_basic_usage():
    """Basic usage example - complete pipeline."""
    
    # Set your OpenAI API key as an environment variable
    # export OPENAI_API_KEY="your-api-key-here"
    
    # Initialize the complete pipeline with 3-minute chunks
    pipeline = VideoToTextPipeline(chunk_duration_minutes=3.0)
    
    # Process a video file
    video_path = "path/to/your/video.mp4"
    output_file = "transcription.txt"
    
    try:
        # Process video - this returns metadata, not the transcription
        result = pipeline.process_video(
            video_path=video_path,
            language="en"  # Optional: specify language
        )
        
        # Now transcribe the chunks
        transcriber = WhisperTranscriber()
        transcriptions = transcriber.transcribe_chunks(
            result['chunk_paths'],
            language="en"
        )
        
        # Combine and save
        full_transcription = "\n\n".join(transcriptions)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_transcription)
        
        print("Transcription completed successfully!")
        print(f"Full transcription saved to: {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")


def example_step_by_step():
    """Step-by-step usage example."""
    
    video_path = "path/to/your/video.mp4"
    
    # Step 1: Extract audio
    extractor = AudioExtractor()
    audio_path = extractor.extract_audio(video_path, "extracted_audio.wav")
    print(f"Audio extracted to: {audio_path}")
    
    # Step 2: Split into chunks (2-minute chunks)
    chunker = AudioChunker()
    chunk_paths = chunker.split_audio(audio_path, chunk_duration_minutes=2.0)
    print(f"Created {len(chunk_paths)} audio chunks")
    
    # Step 3: Transcribe chunks
    transcriber = WhisperTranscriber()
    transcriptions = transcriber.transcribe_chunks(chunk_paths)
    
    # Step 4: Combine and save
    full_transcription = "\n\n".join(transcriptions)
    with open("manual_transcription.txt", "w") as f:
        f.write(full_transcription)
    
    print("Manual transcription completed!")


def example_audio_only():
    """Example for processing existing audio files."""
    
    audio_path = "path/to/your/audio.wav"
    
    # Just split and transcribe existing audio (3-minute chunks)
    chunker = AudioChunker()
    transcriber = WhisperTranscriber()
    
    chunks = chunker.split_audio(audio_path, chunk_duration_minutes=3.0)
    transcriptions = transcriber.transcribe_chunks(chunks, language="es")  # Spanish
    
    full_text = "\n\n".join(transcriptions)
    print("Transcription:", full_text)


if __name__ == "__main__":
    print("Audio Extractor Examples")
    print("========================")
    print("Make sure to:")
    print("1. Install dependencies: poetry install")
    print("2. Set your OpenAI API key: export OPENAI_API_KEY='your-key'")
    print("3. Have ffmpeg installed on your system")
    print()
    
    # Uncomment the example you want to run:
    # example_basic_usage()
    # example_step_by_step()
    # example_audio_only() 