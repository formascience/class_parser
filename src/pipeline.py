"""
Main orchestrator for the complete course processing workflow
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml  # type: ignore

from .course import Course
from .data_extraction import PlanExtractor, SlidesExtractor
from .llm import MappingTwoPass, OutlineOneShot, OutlineTwoPass, Writer
from .models import Content, CourseMetadata, SectionSlideMapping, Slides

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
        output_dir: Optional[str] = None,
    ) -> Course:
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
        logger.info("🚀 Processing course '%s' (Branch B - No Plan)", metadata.name)
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
            name=metadata.name,
            course_title=metadata.course_title,
            level=metadata.level,
            block=metadata.block,
            semester=metadata.semester,
            subject=metadata.subject or "Biology",
            chapter=metadata.chapter,
            content=final_content,
            total_slides=len(slides),
        )

        # Optional saves
        if save_json:
            if output_dir:
                course.save_to_json(output_dir=output_dir+"/json/")
            else:
                course.save_to_json()
        if save_docx:
            if output_dir:
                course.to_docx(template_path=template_path, output_dir=output_dir+"/docx/")
            else:
                course.to_docx(template_path=template_path)
        
        logger.info("🎉 Course processing complete!")
        return course
    
    def process_course_with_plan(
        self,
        slides: List[Slides],
        plan_text: str,
        metadata: CourseMetadata,
        save_json: bool = False,
        save_docx: bool = False,
        template_path: str = "volume/fs_template.docx",
        output_dir: Optional[str] = None,
    ) -> Course:
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
        logger.info("🚀 Processing course '%s' (Branch A - Plan Provided)", metadata.name)
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
            name=metadata.name,
            course_title=metadata.course_title,
            level=metadata.level,
            block=metadata.block,
            semester=metadata.semester,
            subject=metadata.subject or "Biology",
            chapter=metadata.chapter,
            content=final_content,
            total_slides=len(slides),
        )

        # Optional saves
        if save_json:
            if output_dir:
                course.save_to_json(output_dir=output_dir+"/json/")
            else:
                course.save_to_json()
        if save_docx:
            if output_dir:
                course.to_docx(template_path=template_path, output_dir=output_dir+"/docx/")
            else:
                course.to_docx(template_path=template_path)
        
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
          outputs:  { save_json?, save_docx?, template_path?, output_dir? }
        """
        cfg_file = Path(config_path)
        if not cfg_file.exists():
            raise FileNotFoundError(f"Config file not found: {cfg_file}")
        raw = cfg_file.read_text(encoding="utf-8")
        if cfg_file.suffix.lower() in {".yaml", ".yml"}:
            if yaml is None:
                raise RuntimeError("PyYAML is required to read YAML configs. Install pyyaml.")
            data = yaml.safe_load(raw)  # type: ignore
        else:
            import json

            data = json.loads(raw)

        data = data or {}
        # Allow only the explicit minimal schema; warn on extras
        allowed_top = {"metadata", "inputs", "outputs"}
        for k in list(data.keys()):
            if k not in allowed_top:
                logger.warning("Ignoring unknown top-level key in config: %s", k)

        meta = data.get("metadata", {}) or {}
        inputs = data.get("inputs", {}) or {}
        outputs = data.get("outputs", {}) or {}

        allowed_meta = {
            "name",
            "course_title",
            "level",
            "block",
            "semester",
            "subject",
            "year",
            "professor",
        }
        for k in list(meta.keys()):
            if k not in allowed_meta:
                logger.warning("Ignoring unknown metadata key in config: %s", k)

        allowed_inputs = {"slides_pdf", "plan_pdf", "plan_page"}
        for k in list(inputs.keys()):
            if k not in allowed_inputs:
                logger.warning("Ignoring unknown inputs key in config: %s", k)

        allowed_outputs = {"save_json", "save_docx", "template_path", "output_dir"}
        for k in list(outputs.keys()):
            if k not in allowed_outputs:
                logger.warning("Ignoring unknown outputs key in config: %s", k)

        # Validate minimal fields
        if "name" not in meta:
            raise ValueError("Config.metadata.name is required")
        if not inputs.get("slides_pdf"):
            raise ValueError("Config.inputs.slides_pdf is required")

        metadata = CourseMetadata(**meta)

        slides_pdf = str(inputs.get("slides_pdf"))
        plan_pdf = inputs.get("plan_pdf")
        plan_page = inputs.get("plan_page")

        save_json = bool(outputs.get("save_json", False))
        save_docx = bool(outputs.get("save_docx", False))
        template_path = str(outputs.get("template_path", "volume/fs_template.docx"))
        output_dir = outputs.get("output_dir")

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
                metadata=metadata,
                save_json=save_json,
                save_docx=save_docx,
                template_path=template_path,
                output_dir=output_dir,
            )
        else:
            return self.process_course_no_plan(
                slides=slides,
                metadata=metadata,
                save_json=save_json,
                save_docx=save_docx,
                template_path=template_path,
                output_dir=output_dir,
            )