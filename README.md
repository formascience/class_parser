# Audio Extractor

A Python project that extracts audio from video files, splits it into chunks, and transcribes the audio using OpenAI's Whisper API.

## Features

- **Video to Audio Extraction**: Extract audio from video files using FFmpeg
- **Audio Chunking**: Split audio files into configurable time chunks
- **Whisper Transcription**: Transcribe audio chunks using OpenAI's Whisper API
- **Object-Oriented Design**: Clean, modular classes for each functionality
- **Command-Line Interface**: Easy-to-use CLI for batch processing

## Prerequisites

1. **Python 3.8+**
2. **Poetry** - for dependency management
3. **FFmpeg** - for video/audio processing
4. **OpenAI API Key** - for Whisper transcription

### Installing FFmpeg

**macOS (with Homebrew):**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

## Setup

1. **Clone and setup the project:**
```bash
cd formascience
poetry install
```

2. **Set your OpenAI API key:**
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

Or create a `.env` file in the project root:
```
OPENAI_API_KEY=your_openai_api_key_here
```

## Usage

### Command Line Interface

**Basic usage:**
```bash
poetry run extract-audio path/to/video.mp4
```

**With custom chunk duration (in minutes):**
```bash
poetry run extract-audio path/to/video.mp4 -c 3.0
```

**Save transcription to file:**
```bash
poetry run extract-audio path/to/video.mp4 -o transcription.txt
```

**Specify language:**
```bash
poetry run extract-audio path/to/video.mp4 -l en
```

### Python API

**Complete Pipeline (Recommended):**
```python
from audio_extractor.main import VideoToTextPipeline

# Initialize with 5-minute chunks
pipeline = VideoToTextPipeline(chunk_duration_minutes=5.0)

# Process video and get transcription
transcription = pipeline.process_video(
    video_path="path/to/video.mp4",
    output_file="transcription.txt",
    language="en"  # optional
)

print(transcription)
```

**Step-by-step Usage:**
```python
from audio_extractor.main import AudioExtractor, AudioChunker, WhisperTranscriber

# Step 1: Extract audio from video
extractor = AudioExtractor()
audio_path = extractor.extract_audio("video.mp4", "audio.wav")

# Step 2: Split audio into chunks
chunker = AudioChunker(chunk_duration_minutes=3.0)
chunk_paths = chunker.split_audio(audio_path, "chunks/")

# Step 3: Transcribe chunks
transcriber = WhisperTranscriber()
transcriptions = transcriber.transcribe_chunks(chunk_paths)

# Step 4: Combine results
full_transcription = "\n\n".join(transcriptions)
```

**Audio-only Processing:**
```python
from audio_extractor.main import AudioChunker, WhisperTranscriber

# Process existing audio file
chunker = AudioChunker(chunk_duration_minutes=2.0)
transcriber = WhisperTranscriber()

chunks = chunker.split_audio("existing_audio.wav")
transcriptions = transcriber.transcribe_chunks(chunks, language="es")
full_text = "\n\n".join(transcriptions)
```

## Classes Overview

### `AudioExtractor`
- Extracts audio from video files using FFmpeg
- Outputs 16kHz mono WAV files optimized for Whisper

### `AudioChunker`
- Splits audio files into smaller chunks
- Configurable chunk duration in minutes
- Uses pydub for audio processing

### `WhisperTranscriber`
- Transcribes audio using OpenAI's Whisper API
- Supports multiple languages
- Handles both single files and chunk lists

### `VideoToTextPipeline`
- Complete end-to-end pipeline
- Combines all functionality in a single class
- Handles temporary file management

## Configuration Options

- **Chunk Duration**: Configurable chunk size (default: 5 minutes)
- **Language**: Specify transcription language (auto-detect if not specified)
- **Output Format**: Text files with UTF-8 encoding
- **Audio Format**: 16kHz mono WAV (optimized for Whisper)

## Examples

See `example_usage.py` for comprehensive examples of different usage patterns.

## Error Handling

The application includes robust error handling for:
- Missing video/audio files
- FFmpeg processing errors
- OpenAI API errors
- File I/O errors

## Cost Considerations

OpenAI Whisper API pricing is based on audio duration. Splitting into chunks doesn't affect cost, but be mindful of:
- Long videos = higher costs
- API rate limits for concurrent requests

## License

This project is for educational/personal use. Please ensure you have appropriate licenses for any media files you process.

## Contributing

Feel free to submit issues and enhancement requests! 