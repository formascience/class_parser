"""
Content generation using OpenAI API for course structure and content
"""

import json
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from openai import OpenAI
from .course import Content
from .prompt_manager import PromptManager

if TYPE_CHECKING:
    from .course import Course


class ContentGenerator:
    """Handles AI-powered course content generation through OpenAI API"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4.1-mini"):
        """
        Initialize content generator with OpenAI client
        
        Args:
            api_key: OpenAI API key (uses environment variable if None)
            model: OpenAI model to use for generation
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.prompt_manager = PromptManager()
    
    def generate_course_content(self, 
                              course_plan: dict, 
                              course_content: List[dict],
                              course_metadata: Optional[Dict[str, Any]] = None,
                              generation_config: Optional[Dict[str, Any]] = None) -> Content:
        """
        Generate complete course content through two-phase process
        
        Args:
            course_plan: Course plan structure from PDF
            course_content: List of course slide content
            course_metadata: Additional course information (level, subject, etc.)
            generation_config: Custom generation parameters
            
        Returns:
            Content object with filled sections and slide mappings
        """
        config = generation_config or {}
        
        # Phase 1: Create outline structure
        outline = self._phase1_create_outline(
            course_plan, 
            course_content, 
            course_metadata,
            config.get('phase1', {})
        )
        
        # Phase 2: Fill content
        complete_content = self._phase2_fill_content(
            outline, 
            course_content,
            course_metadata,
            config.get('phase2', {})
        )
        
        return complete_content
    
    def process_course_content(self,
                             course_content: List[dict],
                             course_plan: Optional[dict] = None,
                             course_metadata: Optional[Dict[str, Any]] = None,
                             generation_config: Optional[Dict[str, Any]] = None) -> Content:
        """
        Process course content with optional separate course plan
        
        Args:
            course_content: List of course slide content
            course_plan: Optional course plan structure (if None, will try to extract from slides)
            course_metadata: Additional course information (level, subject, etc.)
            generation_config: Custom generation parameters
            
        Returns:
            Content object with filled sections and slide mappings
        """
        config = generation_config or {}
        
        # If no course plan provided, try to extract it from course content
        if course_plan is None:
            course_plan = self._extract_course_plan_from_content(course_content)
        
        # Phase 1: Create outline structure
        outline = self._phase1_create_outline(
            course_plan, 
            course_content, 
            course_metadata,
            config.get('phase1', {})
        )
        
        # Phase 2: Fill content
        complete_content = self._phase2_fill_content(
            outline, 
            course_content,
            course_metadata,
            config.get('phase2', {})
        )
        
        return complete_content
    
    def _extract_course_plan_from_content(self, course_content: List[dict]) -> dict:
        """
        Extract course plan from course content slides
        
        Args:
            course_content: List of course slide content
            
        Returns:
            Extracted course plan dictionary
        """
        # Look for slides that might contain the course plan
        plan_keywords = ['plan', 'agenda', 'outline', 'sommaire', 'table', 'contenu']
        
        for slide in course_content:
            slide_title = slide.get('title', '').lower()
            
            # Check if slide title contains plan-related keywords
            if any(keyword in slide_title for keyword in plan_keywords):
                return {
                    'page': slide.get('page', 0),
                    'title': slide.get('title', 'Course Plan'),
                    'tree': slide.get('tree', [])
                }
        
        # If no plan slide found, create a basic plan from all slide titles
        return self._create_basic_plan_from_titles(course_content)
    
    def _create_basic_plan_from_titles(self, course_content: List[dict]) -> dict:
        """
        Create a basic course plan from slide titles when no plan slide is found
        
        Args:
            course_content: List of course slide content
            
        Returns:
            Basic course plan dictionary
        """
        sections = []
        
        for slide in course_content:
            title = slide.get('title', f"Slide {slide.get('page', 'Unknown')}")
            sections.append({
                'text': title,
                'children': []
            })
        
        return {
            'page': 1,
            'title': 'Generated Course Plan',
            'tree': [{
                'text': 'Course Content',
                'children': [{
                    'text': 'Course Sections',
                    'children': sections
                }]
            }]
                 }
    
    def generate_from_course_object(self,
                                  course_content: List[dict],
                                  course: Optional['Course'] = None,
                                  course_plan: Optional[dict] = None,
                                  generation_config: Optional[Dict[str, Any]] = None) -> Content:
        """
        Generate course content from a Course object with metadata
        
        Args:
            course_content: List of course slide content
            course: Course object containing metadata (level, subject, etc.)
            course_plan: Optional course plan structure
            generation_config: Custom generation parameters
            
        Returns:
            Content object with filled sections and slide mappings
        """
        # Extract course metadata if Course object is provided
        course_metadata = None
        if course:
            course_metadata = {
                'level': course.level,
                'block': course.block,
                'semester': course.semester,
                'subject': course.subject,
                'chapter': course.chapter,
                'title': course.title,
                'total_slides': course.total_slides or len(course_content),
                'year': course.year
            }
        
        return self.process_course_content(
            course_content=course_content,
            course_plan=course_plan,
            course_metadata=course_metadata,
            generation_config=generation_config
        )
     
    def _phase1_create_outline(self, 
                             course_plan: dict, 
                             course_content: List[dict],
                             course_metadata: Optional[Dict[str, Any]] = None,
                             phase1_config: Optional[Dict[str, Any]] = None) -> Content:
        """Phase 1: Create hierarchical outline with slide mappings"""
        config = phase1_config or {}
        
        # Generate dynamic prompt
        system_prompt = self.prompt_manager.get_phase1_prompt(
            course_metadata=course_metadata,
            custom_variables=config.get('custom_variables', {})
        )
        
        assistant_message = json.dumps({"course_plan": course_plan}, ensure_ascii=False)
        user_message = json.dumps({"course_content": course_content}, ensure_ascii=False)
        
        response = self.client.responses.parse(
            model=self.model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "assistant", "content": assistant_message},
                {"role": "user", "content": user_message}
            ],
            text_format=Content,
        )
        
        return response.output_parsed
    
    def _phase2_fill_content(self, 
                           outline: Content, 
                           course_content: List[dict],
                           course_metadata: Optional[Dict[str, Any]] = None,
                           phase2_config: Optional[Dict[str, Any]] = None) -> Content:
        """Phase 2: Fill outline with detailed content"""
        config = phase2_config or {}
        
        # Generate dynamic prompt
        system_prompt = self.prompt_manager.get_phase2_prompt(
            course_metadata=course_metadata,
            content_requirements=config.get('content_requirements'),
            custom_variables=config.get('custom_variables', {})
        )
        
        assistant_message = outline.model_dump_json()
        user_message = json.dumps({"course_content": course_content}, ensure_ascii=False)
        
        response = self.client.responses.parse(
            model=self.model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "assistant", "content": assistant_message},
                {"role": "user", "content": user_message},
            ],
            text_format=Content,
        )
        
        return response.output_parsed
    

    
 