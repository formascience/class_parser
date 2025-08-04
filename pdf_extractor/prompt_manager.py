"""
Prompt manager that handles dynamic prompt generation using templates.
"""

from typing import Dict, Any, Optional
import json
from .course import Content, SlideMapping
from .prompt_templates import (
    PHASE1_SYSTEM_TEMPLATE,
    PHASE2_SYSTEM_TEMPLATE,
    DEFAULT_PHASE1_CONFIG,
    DEFAULT_PHASE2_CONFIG,
    DEFAULT_CONTENT_REQUIREMENTS
)

class PromptManager:
    """Manages AI prompts with dynamic schema generation and variable injection"""
    
    def __init__(self):
        self.phase1_template = PHASE1_SYSTEM_TEMPLATE
        self.phase2_template = PHASE2_SYSTEM_TEMPLATE
    
    def get_phase1_prompt(self, 
                         course_metadata: Optional[Dict[str, Any]] = None,
                         custom_variables: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate Phase 1 prompt with dynamic variables including course metadata
        
        Args:
            course_metadata: Course information to inject (level, block, subject, etc.)
            custom_variables: Additional variables to override defaults
        """
        
        # Start with default config
        config = DEFAULT_PHASE1_CONFIG.copy()
        
        # Add course metadata
        if course_metadata:
            config.update(course_metadata)
        
        # Override with custom variables
        if custom_variables:
            config.update(custom_variables)
        
        # Generate dynamic schemas
        config['content_schema'] = self._generate_content_schema()
        config['slide_mapping_schema'] = self._generate_slide_mapping_schema()
        
        # Set default values for missing fields
        config.setdefault('level', 'N/A')
        config.setdefault('block', 'N/A')
        config.setdefault('semester', 'N/A')
        config.setdefault('subject', 'N/A')
        config.setdefault('chapter', 'N/A')
        config.setdefault('title', 'N/A')
        config.setdefault('total_slides', 'N/A')
        
        # Substitute variables in template
        return self.phase1_template.substitute(**config)
    
    def get_phase2_prompt(self, 
                         course_metadata: Optional[Dict[str, Any]] = None,
                         content_requirements: Optional[Dict[str, Any]] = None,
                         custom_variables: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate Phase 2 prompt with dynamic variables including course metadata
        
        Args:
            course_metadata: Course information to inject (level, block, subject, etc.)
            content_requirements: Custom content generation requirements
            custom_variables: Additional variables to override defaults
        """
        
        # Start with default config
        config = DEFAULT_PHASE2_CONFIG.copy()
        
        # Add course metadata
        if course_metadata:
            config.update(course_metadata)
        
        # Add content requirements
        requirements = content_requirements or DEFAULT_CONTENT_REQUIREMENTS
        config['content_requirements'] = json.dumps(requirements, indent=2)
        
        # Override with custom variables
        if custom_variables:
            config.update(custom_variables)
        
        # Generate dynamic schema
        config['content_schema'] = self._generate_content_schema()
        
        # Set default values for missing fields
        config.setdefault('level', 'N/A')
        config.setdefault('block', 'N/A')
        config.setdefault('semester', 'N/A')
        config.setdefault('subject', 'N/A')
        config.setdefault('chapter', 'N/A')
        config.setdefault('title', 'N/A')
        
        # Substitute variables in template
        return self.phase2_template.substitute(**config)
    
    def _generate_content_schema(self) -> str:
        """Generate JSON schema example from Content Pydantic model"""
        example = {
            "sections": [
                {
                    "title": "Chapter 1: Introduction",
                    "content": [],  # Will be filled in phase 2
                    "subsections": [
                        {
                            "title": "ML Basics",
                            "content": [],
                            "subsections": []
                        }
                    ]
                }
            ],
            "slide_mappings": [
                {"slide_number": 1, "section_path": ["Chapter 1: Introduction"]},
                {"slide_number": 2, "section_path": ["Chapter 1: Introduction", "ML Basics"]}
            ]
        }
        return json.dumps(example, indent=2)
    
    def _generate_slide_mapping_schema(self) -> str:
        """Generate schema info for SlideMapping"""
        example = {
            "slide_number": "int - The slide page number",
            "section_path": "List[str] - Hierarchical path to the section"
        }
        return json.dumps(example, indent=2) 