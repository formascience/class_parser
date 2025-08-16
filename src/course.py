"""
Course model and DOCX export functionality
"""

from typing import Optional

from docx import Document
from docx.shared import Inches
from pydantic import BaseModel

from .models import Content


class Course(BaseModel):
    """Course model containing metadata and content"""
    
    name: str
    subject: str = "Biology"
    year: Optional[int] = None
    professor: Optional[str] = None
    content: Optional[Content] = None
    total_slides: Optional[int] = None
    
    def print_outline(self) -> str:
        """Print course outline if content exists"""
        if self.content:
            return f"Course: {self.name}\nSubject: {self.subject}\nYear: {self.year}\nProfessor: {self.professor}\n\n{self.content.print_outline()}"
        return f"Course: {self.name} (No content available)"
    
    def print_content(self) -> str:
        """Print course content if available"""
        if self.content:
            return f"Course: {self.name}\nSubject: {self.subject}\nYear: {self.year}\nProfessor: {self.professor}\n\n{self.content.print_content()}"
        return f"Course: {self.name} (No content available)"
