# Class Parser

AI-powered content extraction toolkit for educational materials.

## 📁 PDF Extractor (`pdf_extractor/`)

Extract and structure content from PDF lecture slides.

**Key Features:**
- Extract text from PDF slides and convert to hierarchical tree structures
- Separate course plans from content slides  
- Generate structured documents using OpenAI GPT models
- Complete pipeline from PDF → structured content → DOCX output

**Usage:**
```python
from pdf_extractor import CoursePipeline

pipeline = CoursePipeline(openai_api_key="your-key")
course = pipeline.process_course(
    pdf_filename="lecture.pdf",
    course_name="Biology 101", 
    subject="Biology"
)
```

## 🎵 Audio Extractor (`audio_extractor/`)

Convert video lectures to transcribed text using AI.

**Key Features:**
- Extract audio from video files (MP4, AVI, MOV, etc.)
- Split audio into optimal chunks for processing
- Transcribe using OpenAI Whisper API
- CLI interface with progress tracking and multiple output formats

**Usage:**
```bash
# Command line
python -m audio_extractor.cli lecture.mp4 -o transcript.txt

# Python API  
from audio_extractor import VideoToTextPipeline

pipeline = VideoToTextPipeline(openai_api_key="your-key")
transcript = pipeline.process_video("lecture.mp4")
```

## Installation

```bash
pip install poetry
poetry install
```

**Requirements:** Python 3.9+, FFmpeg, OpenAI API key 