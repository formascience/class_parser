"""
Final content writing/enhancement - processes enriched content
Based on the actual implementation from poc.ipynb
"""

import logging
from typing import Any, Dict, Optional

from openai import OpenAI

logger = logging.getLogger(__name__)

from ..models import Content
from .prompt_manager import PromptManager


class Writer:
    """Handles final content enhancement and writing after enrichment with slides"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-5-mini"):
        """
        Initialize writer with OpenAI client
        
        Args:
            api_key: OpenAI API key (uses environment variable if None)
            model: OpenAI model to use for content enhancement
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.prompt_manager = PromptManager()
    
    def write_course(self, 
                    enriched_content: Content,
                    course_metadata: Optional[Dict[str, Any]] = None,
                    enhancement_config: Optional[Dict[str, Any]] = None,
                    verbosity: str = "high") -> Content:
        """
        Enhance and finalize course content that has been enriched with slide data
        Based on the exact implementation from poc.ipynb
        
        Args:
            enriched_content: Content object with sections filled with raw slide content
            course_metadata: Course information (not used in current implementation)
            enhancement_config: Custom enhancement parameters (not used in current implementation)
            verbosity: Controls model text verbosity ("low", "medium", "high")
            
        Returns:
            Content object with enhanced, polished content
        """
        # Get the content as JSON string
        content_json_str = enriched_content.model_dump_json()
        
        # Build the complete prompt (following poc.ipynb approach)
        prompt_to_send = self.prompt_manager.get_complete_writer_prompt(content_json_str)
        
        # Get system prompt
        system_prompt = self.prompt_manager.get_writer_role_prompt()
        
        try:
            logger.debug("Starting content enhancement for %d sections", len(enriched_content.sections))
            # Use the exact API call from poc.ipynb
            response = self.client.responses.parse(
                model=self.model,
                input=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {"role": "user", "content": prompt_to_send},
                ],
                text_format=Content,
                reasoning={"effort": "high"},  # for deep synthesis
                text={"verbosity": verbosity},  # type: ignore
            )
            
            result = response.output_parsed
            if result is None:
                logger.error("OpenAI API returned None for content enhancement")
                raise Exception("No result returned from API")
            
            logger.debug("Successfully enhanced content with %d sections", len(result.sections))
            return result
            
        except Exception as e:
            logger.error("Failed to enhance content: %s", str(e))
            raise Exception(f"Failed to enhance content: {str(e)}")