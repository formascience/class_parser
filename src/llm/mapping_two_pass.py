"""
Two-pass section-slide mapping (Branch A) - when plan and outline are provided
Based on the actual implementation from poc.ipynb
"""

import logging
import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

from openai import OpenAI

logger = logging.getLogger(__name__)

from ..models import Content, SectionSlideMapping, Slides
from .prompt_manager import PromptManager

load_dotenv()


class MappingTwoPass:
    """Handles section-to-slide mapping when outline is already generated (Branch A)"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-5-mini"):
        """
        Initialize mapping generator with OpenAI client
        
        Args:
            api_key: OpenAI API key (uses environment variable if None)
            model: OpenAI model to use for generation
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.prompt_manager = PromptManager()
    
    def build_mapping(self, 
                     slides: List[Slides],
                     outline: Content,
                     course_metadata: Optional[Dict[str, Any]] = None,
                     custom_config: Optional[Dict[str, Any]] = None) -> SectionSlideMapping:
        """
        Generate section-to-slide mapping based on outline and slides (Branch A)
        Based on the exact implementation from poc.ipynb
        
        Args:
            slides: List of Slides objects containing slide content
            outline: Content object with hierarchical outline structure
            course_metadata: Course information (not used in current implementation)
            custom_config: Custom generation parameters (not used in current implementation)
            
        Returns:
            SectionSlideMapping object mapping sections to slides
        """
        # Convert slides to the format expected by the prompt (as done in poc.ipynb)
        slides_data = [slide.model_dump() for slide in slides]
        
        # Get the outline as JSON
        outline_json = outline.model_dump_json()
        
        # Generate the mapping prompt
        user_prompt = self.prompt_manager.get_mapping_prompt(outline_json, slides_data)
        
        try:
            logger.debug("Starting mapping generation for %d slides and %d sections", 
                        len(slides), len(outline.sections))
            
            # Get configuration from environment variables
            reasoning_effort = os.getenv("MAPPING_TWOPASS_REASONING_EFFORT", "medium")
            text_verbosity = os.getenv("MAPPING_TWOPASS_TEXT_VERBOSITY", "low")

            logger.debug(f"Mapping with verbosity: {text_verbosity} and reasoning effort: {reasoning_effort}")
            
            # Use the exact API call from poc.ipynb
            response = self.client.responses.parse(
                model=self.model,
                input=[{"role": "user", "content": user_prompt}],
                text_format=SectionSlideMapping,
                reasoning={"effort": reasoning_effort},
                text={"verbosity": text_verbosity},  # type: ignore
            )
            
            result = response.output_parsed
            if result is None:
                logger.error("OpenAI API returned None for mapping generation")
                raise Exception("No result returned from API")
            
            logger.debug("Successfully generated mapping with %d entries", len(result.mapping))
            return result
            
        except Exception as e:
            logger.error("Failed to generate section-slide mapping: %s", str(e))
            raise Exception(f"Failed to generate section-slide mapping: {str(e)}")