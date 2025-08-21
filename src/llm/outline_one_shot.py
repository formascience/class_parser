"""
One-shot outline and mapping generation (Branch B) - when no plan is provided
Based on the actual implementation from poc.ipynb
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from openai import OpenAI

from ..models import (
    Content,
    CourseMetadata,
    OutlineAndMapping,
    SectionSlideMapping,
    Slides,
)
from .prompt_manager import PromptManager

logger = logging.getLogger(__name__)


def _format_course_metadata_header(course_metadata: CourseMetadata) -> str:
    """Format a compact metadata header for the model context"""
    
    # Extract required fields from CourseMetadata model
    block = course_metadata.block  # Required field
    chapter = course_metadata.chapter  # Required field
    course_title = course_metadata.course_title  # Required field
    
    header = f"""CONTEXTE COURS
- Université de Strasbourg, Faculté de Médecine, première année
- Bloc: {block}
- Chapitre {chapter}: {course_title}
- Deck de diapositives d'un cours magistral de médecine

"""
    return header


class OutlineOneShot:
    """Handles combined outline and mapping generation when no plan is provided (Branch B)"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-5-mini"):
        """
        Initialize one-shot generator with OpenAI client
        
        Args:
            api_key: OpenAI API key (uses environment variable if None)
            model: OpenAI model to use for generation
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.prompt_manager = PromptManager()
    
    def build_outline_and_mapping(self, 
                                 slides: List[Slides],
                                 course_metadata: CourseMetadata,
                                 custom_config: Optional[Dict[str, Any]] = None) -> Tuple[Content, SectionSlideMapping]:
        """
        Generate both outline and section-slide mapping in one shot (Branch B)
        Based on the exact implementation from poc.ipynb
        
        Args:
            slides: List of Slides objects containing slide content
            course_metadata: CourseMetadata object (required - block, chapter, course_title/name)
            custom_config: Custom generation parameters (not used in current implementation)
            
        Returns:
            Tuple of (Content outline, SectionSlideMapping)
        """
        # Get the one-shot prompt
        base_prompt = self.prompt_manager.get_one_shot_prompt_no_admin(slides)
        
        # Add metadata header if provided
        metadata_header = _format_course_metadata_header(course_metadata)
        user_prompt = metadata_header + base_prompt
        
        system_prompt = self.prompt_manager.get_one_shot_system_prompt()
        
        try:
            logger.debug("Starting one-shot outline and mapping generation with %d slides", len(slides))
            # Use the exact API call from poc.ipynb
            response = self.client.responses.parse(
                model=self.model,
                input=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {"role": "user", "content": user_prompt},
                ],
                text_format=OutlineAndMapping,
                reasoning={"effort": "high"},
                text={"verbosity": "medium"},  # type: ignore
            )
            
            result = response.output_parsed
            if result is None:
                logger.error("OpenAI API returned None for output_parsed")
                raise Exception("No result returned from API")
                
            outline = result.outline
            mapping = SectionSlideMapping(mapping=result.mapping)
            
            logger.debug("Successfully generated outline with %d sections and mapping with %d entries", 
                        len(outline.sections), len(mapping.mapping))
            return outline, mapping
            
        except Exception as e:
            logger.error("Failed to generate outline and mapping: %s", str(e))
            raise Exception(f"Failed to generate outline and mapping: {str(e)}")