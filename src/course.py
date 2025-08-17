"""
Course model
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from .data_extraction.docx_writer import DocxWriter
from .models import Content


class Course(BaseModel):
    """Course model containing metadata and content"""
    
    # Core identifiers
    name: str
    course_title: Optional[str] = None

    # Academic hierarchy (see data_structure.md)
    level: Optional[str] = None  # e.g., L1, L2, L3, M1, M2
    block: Optional[str] = None  # e.g., BLOC_SANTE, TRANSVERSAL, DISCIPLINAIRE
    semester: Optional[str] = None  # e.g., S1, S2
    subject: str = "UE-1 Constitution et transformation de la matière"  # Matière
    chapter: Optional[str] = None  # e.g., CHAPITRE_9

    # Content
    content: Optional[Content] = None
    # Additional metadata
    total_slides: Optional[int] = None
    
    def print_outline(self) -> str:
        """Print course outline if content exists"""
        if self.content:
            header = (
                f"Course: {self.course_title or self.name}\n"
                f"Level: {self.level}\n"
                f"Block: {self.block}\n"
                f"Semester: {self.semester}\n"
                f"Subject: {self.subject}\n"
                f"Chapter: {self.chapter}\n"
            )
            return f"{header}\n\n{self.content.print_outline()}"
        return f"Course: {self.name} (No content available)"
    
    def print_content(self) -> str:
        """Print course content if available"""
        if self.content:
            header = (
                f"Course: {self.course_title or self.name}\n"
                f"Level: {self.level}\n"
                f"Block: {self.block}\n"
                f"Semester: {self.semester}\n"
                f"Subject: {self.subject}\n"
                f"Chapter: {self.chapter}\n"
            )
            return f"{header}\n\n{self.content.print_content()}"
        return f"Course: {self.name} (No content available)"

        # Add these to your Course class
    def save_to_json(self, file_path: Optional[str] = None) -> str:
        """Save course to JSON file"""
        if not file_path:
            file_path = f"volume/artifacts/{self.name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Use Pydantic's built-in JSON serialization
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.model_dump_json(indent=2))
        
        print(f"💾 Course saved to: {file_path}")
        return file_path

    @classmethod
    def load_from_json(cls, file_path: str) -> 'Course':
        """Load course from JSON file"""
        if not file_path:
            raise ValueError("file_path is required")
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_str = f.read()
            
            # Use Pydantic's built-in JSON validation
            return cls.model_validate_json(json_str)

    # New: export to .docx using the production DocxWriter
    def to_docx(
        self,
        output_path: Optional[str] = None,
        template_path: str = "volume/fs_template.docx",
    ) -> str:
        """Render this course to a Word document and return the output path.

        Args:
            output_path: Optional explicit path for the .docx output. If not
                provided, a path under ``volume/artifacts`` is generated.
            template_path: Path to the Word template to use.
        """
        writer = DocxWriter(template_path=template_path)
        dest = writer.fill_template(self, output_path=output_path)
        print(f"📄 Course exported to DOCX: {dest}")
        return dest
