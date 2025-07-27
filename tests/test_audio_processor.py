"""
Tests for the audio processor module.
"""

import os
import tempfile
from unittest.mock import MagicMock, Mock, patch

import pytest

from audio_extractor.audio_processor import (AudioChunker, AudioExtractor,
                                             VideoToTextPipeline)


class TestAudioExtractor:
    """Tests for the AudioExtractor class."""
    
    def test_init(self):
        """Test AudioExtractor initialization."""
        extractor = AudioExtractor()
        assert extractor.temp_dir is not None
        assert os.path.exists(extractor.temp_dir)
    
    def test_init_with_custom_temp_dir(self):
        """Test AudioExtractor with custom temp directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            extractor = AudioExtractor(temp_dir=temp_dir)
            assert extractor.temp_dir == temp_dir
    
    def test_extract_audio_file_not_found(self):
        """Test extract_audio with non-existent file."""
        extractor = AudioExtractor()
        
        with pytest.raises(FileNotFoundError):
            extractor.extract_audio("nonexistent_file.mp4")
    
    @patch('audio_extractor.audio_processor.ffmpeg')
    def test_extract_audio_success(self, mock_ffmpeg):
        """Test successful audio extraction."""
        # Create a mock video file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_video:
            temp_video.write(b"fake video content")
            video_path = temp_video.name
        
        try:
            # Mock ffmpeg chain
            mock_input = Mock()
            mock_output = Mock()
            mock_run = Mock()
            
            mock_ffmpeg.input.return_value = mock_input
            mock_input.output.return_value = mock_output
            mock_output.overwrite_output.return_value = mock_run
            mock_run.run.return_value = None
            
            extractor = AudioExtractor()
            result = extractor.extract_audio(video_path)
            
            # Verify the result
            assert result is not None
            assert result.endswith('_audio.wav')
            
            # Verify ffmpeg was called correctly
            mock_ffmpeg.input.assert_called_once_with(video_path)
            mock_run.run.assert_called_once()
            
        finally:
            os.unlink(video_path)


class TestAudioChunker:
    """Tests for the AudioChunker class."""
    
    def test_init_default(self):
        """Test AudioChunker default initialization."""
        chunker = AudioChunker()
        assert chunker.chunk_duration_ms == 5 * 60 * 1000  # 5 minutes in ms
        assert chunker.overlap_ms == 0
    
    def test_init_custom_duration(self):
        """Test AudioChunker with custom duration."""
        chunker = AudioChunker(chunk_duration_minutes=3.0, overlap_seconds=10.0)
        assert chunker.chunk_duration_ms == 3 * 60 * 1000  # 3 minutes in ms
        assert chunker.overlap_ms == 10 * 1000  # 10 seconds in ms
    
    def test_split_audio_file_not_found(self):
        """Test split_audio with non-existent file."""
        chunker = AudioChunker()
        
        with pytest.raises(FileNotFoundError):
            chunker.split_audio("nonexistent_audio.wav")
    
    @patch('audio_extractor.audio_processor.AudioSegment')
    def test_split_audio_success(self, mock_audio_segment):
        """Test successful audio splitting."""
        # Create a mock audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
            temp_audio.write(b"fake audio content")
            audio_path = temp_audio.name
        
        try:
            # Mock AudioSegment
            mock_audio = Mock()
            mock_audio.__len__ = Mock(return_value=600000)  # 10 minutes in ms
            mock_audio.__getitem__ = Mock(return_value=mock_audio)
            mock_audio_segment.from_file.return_value = mock_audio
            
            chunker = AudioChunker(chunk_duration_minutes=5.0)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                result = chunker.split_audio(audio_path, temp_dir)
                
                # Should create 2 chunks for 10 minutes of audio with 5-minute chunks
                assert len(result) == 2
                assert all(path.endswith('.wav') for path in result)
                
        finally:
            os.unlink(audio_path)


class TestVideoToTextPipeline:
    """Tests for the VideoToTextPipeline class."""
    
    def test_init_default(self):
        """Test pipeline default initialization."""
        pipeline = VideoToTextPipeline()
        assert pipeline.metadata['chunk_duration_minutes'] == 5.0
        assert pipeline.metadata['overlap_seconds'] == 0.0
    
    def test_init_custom_params(self):
        """Test pipeline with custom parameters."""
        pipeline = VideoToTextPipeline(
            chunk_duration_minutes=3.0,
            overlap_seconds=10.0
        )
        assert pipeline.metadata['chunk_duration_minutes'] == 3.0
        assert pipeline.metadata['overlap_seconds'] == 10.0
    
    def test_get_pipeline_stats(self):
        """Test getting pipeline statistics."""
        pipeline = VideoToTextPipeline()
        stats = pipeline.get_pipeline_stats()
        
        assert 'chunk_duration_minutes' in stats
        assert 'overlap_seconds' in stats
        assert 'temp_dir' in stats
        assert 'temp_dir_exists' in stats


@pytest.fixture
def mock_extractor():
    """Fixture providing a mocked AudioExtractor."""
    with patch('audio_extractor.audio_processor.AudioExtractor') as mock:
        mock_instance = Mock()
        mock_instance.extract_audio.return_value = "/fake/audio/path.wav"
        mock_instance.get_video_info.return_value = {
            'duration': 600.0,
            'video_codec': 'h264',
            'audio_codec': 'aac'
        }
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_chunker():
    """Fixture providing a mocked AudioChunker."""
    with patch('audio_extractor.audio_processor.AudioChunker') as mock:
        mock_instance = Mock()
        mock_instance.split_audio.return_value = [
            "/fake/chunk1.wav",
            "/fake/chunk2.wav"
        ]
        mock_instance.get_chunk_info.return_value = [
            {'index': 0, 'path': '/fake/chunk1.wav', 'duration_seconds': 300},
            {'index': 1, 'path': '/fake/chunk2.wav', 'duration_seconds': 300}
        ]
        mock.return_value = mock_instance
        yield mock_instance


def test_integration_process_video(mock_extractor, mock_chunker):
    """Test integrated video processing."""
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_video:
        temp_video.write(b"fake video content")
        video_path = temp_video.name
    
    try:
        pipeline = VideoToTextPipeline()
        result = pipeline.process_video(video_path)
        
        # Verify the result structure
        assert result['status'] == 'audio_processed'
        assert result['video_path'] == video_path
        assert result['chunks_ready_for_transcription'] is True
        assert 'audio_path' in result
        assert 'chunk_paths' in result
        assert 'video_info' in result
        assert 'chunk_info' in result
        
    finally:
        os.unlink(video_path) 