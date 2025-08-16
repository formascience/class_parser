"""
Two-pass outline generation (Branch A) - when plan is provided
Based on the actual implementation from poc.ipynb
"""

import logging
from typing import Any, Dict, Optional

from openai import OpenAI

logger = logging.getLogger(__name__)

from ..models import Content
from .prompt_manager import PromptManager


class OutlineTwoPass:
    """Handles outline generation when a course plan is provided (Branch A)"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-5-mini"):
        """
        Initialize outline generator with OpenAI client
        
        Args:
            api_key: OpenAI API key (uses environment variable if None)
            model: OpenAI model to use for generation
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.prompt_manager = PromptManager()
    
    def build_outline(self, 
                     plan_text: str,
                     course_metadata: Optional[Dict[str, Any]] = None,
                     custom_config: Optional[Dict[str, Any]] = None) -> Content:
        """
        Generate hierarchical outline from plan text (Branch A)
        Based on the exact implementation from poc.ipynb
        
        Args:
            plan_text: Extracted plan text from PDF or separate source
            course_metadata: Course information (level, subject, etc.) - not used in current implementation
            custom_config: Custom generation parameters - not used in current implementation
            
        Returns:
            Content object with hierarchical outline structure (empty content arrays)
        """
        # Get system prompt for outline generation from plan
        system_prompt = self.prompt_manager.get_outline_from_plan_system_prompt()
        
        try:
            logger.debug("Starting outline generation from plan text (%d chars)", len(plan_text))
            # Use the exact API call from poc.ipynb
            response = self.client.responses.parse(
                model=self.model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": plan_text}
                ],
                reasoning={
                    "effort": "low",
                },
                text={"verbosity": "low"},  # type: ignore
                text_format=Content
            )
            
            outline = response.output_parsed
            if outline is None:
                logger.error("OpenAI API returned None for outline generation")
                raise Exception("No result returned from API")
            
            # Flatten if there's only one top-level section (as done in poc.ipynb)
            while len(outline.sections) == 1:
                outline.sections = outline.sections[0].subsections
            
            # Assign IDs to sections (as done in poc.ipynb)
            self._assign_ids(outline)
            
            logger.debug("Successfully generated outline with %d sections", len(outline.sections))
            return outline
            
        except Exception as e:
            logger.error("Failed to generate outline: %s", str(e))
            raise Exception(f"Failed to generate outline: {str(e)}")
    
    def _assign_ids(self, outline: Content):
        """
        Assign IDs to sections following the pattern from poc.ipynb
        """
        def assign_ids_recursive(sec, parent_id: str = "", parent_section=None):
            # Determine current section number
            if parent_id == "":
                # Top level section
                existing_top_level = len([s for s in outline.sections if s.id.startswith('SEC_')])
                sec.id = f"SEC_{existing_top_level + 1}"
            else:
                # Subsection - append next number to parent id
                parent_nums = parent_id.replace("SEC_", "")
                sibling_count = len([s for s in parent_section.subsections if s.id.startswith(f"SEC_{parent_nums}.")])
                sec.id = f"SEC_{parent_nums}.{sibling_count + 1}"
            
            # Recursively assign ids to subsections
            for sub in sec.subsections:
                assign_ids_recursive(sub, sec.id, sec)
        
        for section in outline.sections:
            assign_ids_recursive(section)