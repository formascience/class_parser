"""
Class Parser - Course content generation from PDF slides
"""

# Course and Pipeline
from .course import Course

# LLM modules
from .llm import MappingTwoPass, OutlineOneShot, OutlineTwoPass, PromptManager, Writer

# Core models
from .models import Content, ContentSection, MappingItem, SectionSlideMapping, Slides
from .pipeline import CoursePipeline

__all__ = [
    # Models
    'Content',
    'ContentSection', 
    'Slides',
    'SectionSlideMapping',
    'MappingItem',
    
    # Core classes
    'Course',
    'CoursePipeline',
    
    # LLM modules
    'OutlineOneShot',
    'OutlineTwoPass',
    'MappingTwoPass',
    'Writer',
    'PromptManager'
]

__version__ = "0.1.0"
