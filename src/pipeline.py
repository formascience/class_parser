"""
Main orchestrator for the complete course processing workflow
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .course import Course
from .data_extraction import PlanExtractor, SlidesExtractor
from .llm import MappingTwoPass, OutlineOneShot, OutlineTwoPass, Writer
from .models import Content, CourseMetadata, PipelineConfig, SectionSlideMapping, Slides

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
    
    def process_course_no_plan(
        self,
        slides: List[Slides],
        metadata: CourseMetadata,
        save_json: bool = False,
        save_docx: bool = False,
        template_path: str = "volume/fs_template.docx",
        output_path: Optional[str] = None,
        test_mode: bool = True,
    ) -> [Course, str]:
        """
        Process course using Branch B (no plan provided) - one-shot approach
        
        Args:
            slides: List of Slides objects
            metadata: Course metadata
            save_json: Whether to save the course as JSON
            save_docx: Whether to save the course as DOCX
            template_path: Path to the template DOCX file
            output_path: Path to the output directory
            test_mode: If True, only process first 10 slides for quick testing
            
        Returns:
            Course object with generated content
        """
        logger.info("🚀 Processing course '%s' (Branch B - No Plan)", metadata.name)
        logger.debug("📊 Total slides: %d", len(slides))
        
        # Apply test mode if enabled
        if test_mode and len(slides) > 10:
            slides = slides[:10]
            logger.warning("🧪 Test mode enabled: Processing only first 10 slides (%d total available)", len(slides))
        
        # Step 1: Generate outline and mapping in one shot
        logger.info("🤖 Generating outline and mapping...")
        outline, mapping = self.outline_one_shot.build_outline_and_mapping(slides, metadata)
        logger.info("✅ Generated outline with %d sections", len(outline.sections))
        
        # Step 2: Enrich content with slides
        logger.info("🔗 Enriching content with slides...")
        enriched_content = outline.enrich_with_slides(slides, mapping)
        logger.info("✅ Content enriched with slide data")
        
        # Step 3: Final content writing
        logger.info("✍️ Enhancing content with AI...")
        # Lower verbosity in test mode to speed up and reduce output size
        writer_verbosity = "low" if test_mode else "high"
        final_content = self.writer.write_course(enriched_content, verbosity=writer_verbosity)
        logger.info("✅ Content enhanced and finalized")
        
        # Step 4: Create Course object
        course = Course(
            name=metadata.name or metadata.course_title,  # Use course_title as fallback
            course_title=metadata.course_title,
            level=metadata.level,
            block=metadata.block,
            semester=metadata.semester,
            subject=metadata.subject,
            chapter=metadata.chapter,
            content=final_content,
            total_slides=len(slides),
        )

        # Optional saves
        if save_json:
            if output_path:
                course.save_to_json(output_path=output_path+"/json")
            else:
                course.save_to_json(output_path="volume/artifacts/json")
        if save_docx:
            if output_path:
                docx_path, docx_filename = course.to_docx(output_path=output_path+"/docx", template_path=template_path)
            else:
                docx_path, docx_filename = course.to_docx(output_path="volume/artifacts/docx", template_path=template_path)
        
        logger.info("🎉 Course processing complete!")
        return course, docx_path, docx_filename
    
    def process_course_with_plan(
        self,
        slides: List[Slides],
        plan_text: str,
        metadata: CourseMetadata,
        save_json: bool = False,
        save_docx: bool = False,
        template_path: str = "volume/fs_template.docx",
        output_path: Optional[str] = None,
        test_mode: bool = True,
    ) -> Course:
        """
        Process course using Branch A (plan provided) - two-pass approach
        
        Args:
            slides: List of Slides objects
            plan_text: Course plan text extracted from PDF
            metadata: Course metadata
            save_json: Whether to save the course as JSON
            save_docx: Whether to save the course as DOCX
            template_path: Path to the template DOCX file
            output_path: Path to the output directory
            test_mode: If True, only process first 10 slides for quick testing
            
        Returns:
            Course object with generated content
        """
        logger.info("🚀 Processing course '%s' (Branch A - Plan Provided)", metadata.name)
        logger.debug("📊 Total slides: %d", len(slides))
        
        # Apply test mode if enabled
        if test_mode and len(slides) > 10:
            slides = slides[:10]
            logger.warning("🧪 Test mode enabled: Processing only first 10 slides (%d total available)", len(slides))
        
        # Step 1: Generate outline from plan
        logger.info("📝 Generating outline from plan...")
        outline = self.outline_two_pass.build_outline(plan_text, metadata)
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
        # Lower verbosity in test mode to speed up and reduce output size
        writer_verbosity = "low" if test_mode else "high"
        final_content = self.writer.write_course(enriched_content, verbosity=writer_verbosity)
        logger.info("✅ Content enhanced and finalized")
        
        # Step 5: Create Course object
        course = Course(
            name=metadata.name or metadata.course_title,  # Use course_title as fallback
            course_title=metadata.course_title,
            level=metadata.level,
            block=metadata.block,
            semester=metadata.semester,
            subject=metadata.subject,
            chapter=metadata.chapter,
            content=final_content,
            total_slides=len(slides),
        )

        # Optional saves
        if save_json:
            if output_path:
                course.save_to_json(output_path=output_path+"/json")
            else:
                course.save_to_json(output_path="volume/artifacts/json")
            logger.info("💾 Course saved to JSON")
        if save_docx:
            if output_path:
                course.to_docx(output_path=output_path+"/docx", template_path=template_path)
            else:
                course.to_docx(output_path="volume/artifacts/docx", template_path=template_path)
            logger.info("💾 Course saved to DOCX")
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

    # Simple config-driven entry point
    def process_from_config(self, config_path: str) -> Course:
        """Read a YAML/JSON file and run the pipeline accordingly.

        Expected keys:
          metadata: { name, course_title?, level?, block?, semester?, subject?, year?, professor? }
          inputs:   { slides_pdf (required), plan_pdf?, plan_page? }
          outputs:  { save_json?, save_docx?, template_path?, output_dir?, test_mode? }
        """
        # Load and validate config using PipelineConfig
        config = PipelineConfig.load(config_path)
        
        # Validate minimal required fields
        if not config.inputs.get("slides_pdf"):
            raise ValueError("Config.inputs.slides_pdf is required")

        # Extract configuration values
        slides_pdf = str(config.inputs.get("slides_pdf"))
        plan_pdf = config.inputs.get("plan_pdf")
        plan_page = config.inputs.get("plan_page")

        save_json = bool(config.outputs.get("save_json", False))
        save_docx = bool(config.outputs.get("save_docx", False))
        template_path = str(config.outputs.get("template_path", "volume/fs_template.docx"))
        output_path = config.outputs.get("output_dir")
        test_mode = bool(config.outputs.get("test_mode", True))

        # Extract inputs
        slides_extractor = SlidesExtractor()
        slides = slides_extractor.extract_slides(slides_pdf)

        plan_text: Optional[str] = None
        if plan_pdf:
            plan_text = PlanExtractor().extract_plan_from_pdf(str(plan_pdf))
        elif plan_page:
            plan_text = PlanExtractor().extract_plan_from_page(slides_pdf, int(plan_page))

        if plan_text:
            return self.process_course_with_plan(
                slides=slides,
                plan_text=plan_text,
                metadata=config.metadata,
                save_json=save_json,
                save_docx=save_docx,
                template_path=template_path,
                output_path=output_path,
                test_mode=test_mode,
            )
        else:
            return self.process_course_no_plan(
                slides=slides,
                metadata=config.metadata,
                save_json=save_json,
                save_docx=save_docx,
                template_path=template_path,
                output_path=output_path,
                test_mode=test_mode,
            )