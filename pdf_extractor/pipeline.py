"""
Main pipeline orchestrator for course processing workflow
"""

import os
from typing import Optional
from .processor import PDFProcessor
from .generator import ContentGenerator
from course import Course


class CoursePipeline:
    """Main orchestrator for the complete course processing workflow"""
    
    def __init__(self, openai_api_key: str = None, model: str = "gpt-4.1-2025-04-14"):
        """
        Initialize the course processing pipeline
        
        Args:
            openai_api_key: OpenAI API key (uses environment variable if None)
            model: OpenAI model to use for content generation
        """
        self.pdf_processor = PDFProcessor()
        self.content_generator = ContentGenerator(api_key=openai_api_key, model=model)
        
        # Default paths
        self.volume_dir = "volume"
        self.slides_dir = os.path.join(self.volume_dir, "slides")
        self.output_dir = self.volume_dir
        
        # Ensure directories exist
        self._ensure_directories()
    
    def process_course(
        self,
        pdf_filename: str,
        course_name: str,
        subject: str = "Médecine",
        year: Optional[int] = None,
        professor: Optional[str] = None,
        output_filename: Optional[str] = None
    ) -> Course:
        """
        Complete course processing workflow from PDF to DOCX
        
        Args:
            pdf_filename: Name of PDF file in volume/slides/ directory
            course_name: Name of the course
            subject: Subject area (default: "Biology")
            year: Academic year
            professor: Professor name
            output_filename: Custom output filename (optional)
            
        Returns:
            Course object with generated content
        """
        # Build full PDF path
        pdf_path = os.path.join(self.slides_dir, pdf_filename)
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        print(f"📄 Processing PDF: {pdf_filename}")
        
        # Step 1: Extract and process PDF
        course_plan, course_content = self.pdf_processor.process_pdf(pdf_path)
        print(f"✅ PDF processed - Plan extracted, {len(course_content)} content slides")
        
        # Step 2: Generate course content using AI
        print("🤖 Generating course content with AI...")
        content = self.content_generator.generate_course_content(course_plan, course_content)
        print(f"✅ Content generated - {len(content.sections)} sections created")
        
        # Step 3: Create Course object
        course = Course(
            name=course_name,
            subject=subject,
            year=year,
            professor=professor,
            content=content,
            total_slides=len(course_content) + 1  # +1 for plan slide
        )
        
        # Step 4: Export to DOCX
        if output_filename is None:
            safe_name = "".join(c for c in course_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            output_filename = f"{safe_name.replace(' ', '_')}.docx"
        
        output_path = os.path.join(self.output_dir, output_filename)
        course.export_to_docx(output_path)
        
        print(f"🎉 Course processing complete!")
        return course
    
    def process_course_from_path(
        self,
        pdf_path: str,
        course_name: str,
        subject: str = "Biology",
        year: Optional[int] = None,
        professor: Optional[str] = None,
        output_filename: Optional[str] = None
    ) -> Course:
        """
        Process course from full PDF path instead of filename in volume/slides/
        
        Args:
            pdf_path: Full path to PDF file
            course_name: Name of the course
            subject: Subject area (default: "Biology")
            year: Academic year
            professor: Professor name
            output_filename: Custom output filename (optional)
            
        Returns:
            Course object with generated content
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        print(f"📄 Processing PDF: {pdf_path}")
        
        # Step 1: Extract and process PDF
        course_plan, course_content = self.pdf_processor.process_pdf(pdf_path)
        print(f"✅ PDF processed - Plan extracted, {len(course_content)} content slides")
        
        # Step 2: Generate course content using AI
        print("🤖 Generating course content with AI...")
        content = self.content_generator.generate_course_content(course_plan, course_content)
        print(f"✅ Content generated - {len(content.sections)} sections created")
        
        # Step 3: Create Course object
        course = Course(
            name=course_name,
            subject=subject,
            year=year,
            professor=professor,
            content=content,
            total_slides=len(course_content) + 1  # +1 for plan slide
        )
        
        # Step 4: Export to DOCX
        if output_filename is None:
            safe_name = "".join(c for c in course_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            output_filename = f"{safe_name.replace(' ', '_')}.docx"
        
        output_path = os.path.join(self.output_dir, output_filename)
        course.export_to_docx(output_path)
        
        print(f"🎉 Course processing complete!")
        return course
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist"""
        directories = [self.volume_dir, self.slides_dir, self.output_dir]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def set_volume_directory(self, volume_dir: str):
        """
        Change the volume directory path
        
        Args:
            volume_dir: New volume directory path
        """
        self.volume_dir = volume_dir
        self.slides_dir = os.path.join(volume_dir, "slides")
        self.output_dir = volume_dir
        self._ensure_directories()
    
    def get_available_pdfs(self) -> list:
        """
        Get list of available PDF files in the slides directory
        
        Returns:
            List of PDF filenames
        """
        if not os.path.exists(self.slides_dir):
            return []
        
        return [f for f in os.listdir(self.slides_dir) if f.endswith('.pdf')] 