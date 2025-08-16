"""
Prompt manager that handles dynamic prompt generation using templates.
Based on the actual prompts used in poc.ipynb.
"""

from typing import Any, Dict, List, Optional

from ..models import Slides
from .prompt_templates import (
    ONE_SHOT_SYSTEM_PROMPT,
    OUTLINE_FROM_PLAN_SYSTEM_PROMPT,
    WRITER_SYSTEM_PROMPT,
    build_assistant_prompt,
    build_mapping_prompt,
    build_outline_and_mapping_prompt,
    build_prompt_fill_content,
    build_system_prompt,
    build_user_prompt,
)


class PromptManager:
    """Manages AI prompts based on the actual prompts from poc.ipynb"""
    
    def __init__(self):
        pass
    
    def get_one_shot_prompt(self, slides: List[Slides]) -> str:
        """
        Generate one-shot prompt for Branch B (no plan provided)
        
        Args:
            slides: List of Slides objects to analyze
            
        Returns:
            Complete prompt for outline and mapping generation
        """
        return build_outline_and_mapping_prompt(slides)
    
    def get_one_shot_system_prompt(self) -> str:
        """Get system prompt for one-shot generation"""
        return ONE_SHOT_SYSTEM_PROMPT
    
    def get_outline_from_plan_system_prompt(self) -> str:
        """
        Get system prompt for outline generation from plan text (Branch A)
        
        Returns:
            System prompt for parsing plan text into hierarchical outline
        """
        return OUTLINE_FROM_PLAN_SYSTEM_PROMPT
    
    def get_mapping_prompt(self, outline_json: str, slides: List[dict]) -> str:
        """
        Generate mapping prompt for Branch A (plan provided)
        
        Args:
            outline_json: JSON string of the outline structure
            slides: List of slide dictionaries to map
            
        Returns:
            Complete prompt for section-slide mapping
        """
        return build_mapping_prompt(outline_json, slides)
    
    def get_writer_system_prompt(self) -> str:
        """Get system prompt for content writing/enhancement"""
        return build_system_prompt()
    
    def get_writer_user_prompt(self, content_json: str) -> str:
        """Get user prompt with content to enhance"""
        return build_user_prompt(content_json)
    
    def get_writer_assistant_prompt(self) -> str:
        """Get assistant prompt with examples"""
        return build_assistant_prompt()
    
    def get_complete_writer_prompt(self, content_json: str) -> str:
        """Get complete writer prompt (legacy format)"""
        return build_prompt_fill_content(content_json)
    
    def get_writer_role_prompt(self) -> str:
        """Get role-based system prompt for writer"""
        return WRITER_SYSTEM_PROMPT