"""
Main orchestrator for the complete course processing workflow
"""

import logging
import os
from typing import Any, Dict, List, Optional

from .course import Course
from .llm import MappingTwoPass, OutlineOneShot, OutlineTwoPass, Writer
from .models import Content, SectionSlideMapping, Slides

logger = logging.getLogger(__name__)


class CoursePipeline:
    """Main orchestrator for the complete course processing workflow"""
    
    def __init__(self, openai_api_key: Optional[str] = None, model: str = "gpt-5-mini"):
        """
        Initialize the course processing pipeline
        
        Args:
            openai_api_key: OpenAI API key (uses environment variable if None)
            model: OpenAI model to use for content generation
        """
        # Initialize LLM components
        self.outline_one_shot = OutlineOneShot(api_key=openai_api_key, model=model)
        self.outline_two_pass = OutlineTwoPass(api_key=openai_api_key, model=model)
        self.mapping_two_pass = MappingTwoPass(api_key=openai_api_key, model=model)
        self.writer = Writer(api_key=openai_api_key, model=model)
    
    def process_course_no_plan(self,
                              slides: List[Slides],
                              course_name: str,
                              subject: str = "Biology",
                              year: Optional[int] = None,
                              professor: Optional[str] = None) -> Course:
        """
        Process course using Branch B (no plan provided) - one-shot approach
        
        Args:
            slides: List of Slides objects
            course_name: Name of the course
            subject: Subject area
            year: Academic year
            professor: Professor name
            
        Returns:
            Course object with generated content
        """
        logger.info("🚀 Processing course '%s' (Branch B - No Plan)", course_name)
        logger.debug("📊 Total slides: %d", len(slides))
        
        # Step 1: Generate outline and mapping in one shot
        logger.info("🤖 Generating outline and mapping...")
        outline, mapping = self.outline_one_shot.build_outline_and_mapping(slides)
        logger.info("✅ Generated outline with %d sections", len(outline.sections))
        
        # Step 2: Enrich content with slides
        logger.info("🔗 Enriching content with slides...")
        enriched_content = outline.enrich_with_slides(slides, mapping)
        logger.info("✅ Content enriched with slide data")
        
        # Step 3: Final content writing
        logger.info("✍️ Enhancing content with AI...")
        final_content = self.writer.write_course(enriched_content)
        logger.info("✅ Content enhanced and finalized")
        
        # Step 4: Create Course object
        course = Course(
            name=course_name,
            subject=subject,
            year=year,
            professor=professor,
            content=final_content,
            total_slides=len(slides)
        )
        
        logger.info("🎉 Course processing complete!")
        return course
    
    def process_course_with_plan(self,
                                slides: List[Slides],
                                plan_text: str,
                                course_name: str,
                                subject: str = "Biology",
                                year: Optional[int] = None,
                                professor: Optional[str] = None) -> Course:
        """
        Process course using Branch A (plan provided) - two-pass approach
        
        Args:
            slides: List of Slides objects
            plan_text: Course plan text extracted from PDF
            course_name: Name of the course
            subject: Subject area
            year: Academic year
            professor: Professor name
            
        Returns:
            Course object with generated content
        """
        logger.info("🚀 Processing course '%s' (Branch A - Plan Provided)", course_name)
        logger.debug("📊 Total slides: %d", len(slides))
        
        # Step 1: Generate outline from plan
        logger.info("📝 Generating outline from plan...")
        outline = self.outline_two_pass.build_outline(plan_text)
        logger.info("✅ Generated outline with %d sections", len(outline.sections))
        
        # Step 2: Generate section-slide mapping
        logger.info("🗺️ Generating section-slide mapping...")
        mapping = self.mapping_two_pass.build_mapping(slides, outline)
        logger.info("✅ Generated section-slide mapping")
        
        # Step 3: Enrich content with slides
        logger.info("🔗 Enriching content with slides...")
        enriched_content = outline.enrich_with_slides(slides, mapping)
        logger.info("✅ Content enriched with slide data")
        
        # Step 4: Final content writing
        logger.info("✍️ Enhancing content with AI...")
        final_content = self.writer.write_course(enriched_content)
        logger.info("✅ Content enhanced and finalized")
        
        # Step 5: Create Course object
        course = Course(
            name=course_name,
            subject=subject,
            year=year,
            professor=professor,
            content=final_content,
            total_slides=len(slides)
        )
        
        logger.info("🎉 Course processing complete!")
        return course
    
    
    def get_processing_statistics(self, course: Course) -> Dict[str, Any]:
        """
        Get statistics about the processed course
        
        Args:
            course: Processed Course object
            
        Returns:
            Dictionary with processing statistics
        """
        if not course.content:
            return {"error": "No content available"}
        
        stats = {
            "course_name": course.name,
            "subject": course.subject,
            "total_slides": course.total_slides,
            "total_sections": len(course.content.sections),
            "sections_with_content": 0,
            "total_content_items": 0,
            "total_characters": 0
        }
        
        def count_sections(sections):
            for section in sections:
                if section.content:
                    stats["sections_with_content"] += 1
                    stats["total_content_items"] += len(section.content)
                    for content_item in section.content:
                        if isinstance(content_item, str):
                            stats["total_characters"] += len(content_item)
                count_sections(section.subsections)
        
        count_sections(course.content.sections)
        return stats