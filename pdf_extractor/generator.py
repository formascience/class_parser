"""
Content generation using OpenAI API for course structure and content
"""

import json
from typing import Dict, List
from openai import OpenAI
from course import Content


class ContentGenerator:
    """Handles AI-powered course content generation through OpenAI API"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4.1-2025-04-14"):
        """
        Initialize content generator with OpenAI client
        
        Args:
            api_key: OpenAI API key (uses environment variable if None)
            model: OpenAI model to use for generation
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        
        self.phase1_prompt = self._get_phase1_system_prompt()
        self.phase2_prompt = self._get_phase2_system_prompt()
    
    def generate_course_content(self, course_plan: dict, course_content: List[dict]) -> Content:
        """
        Generate complete course content through two-phase process
        
        Args:
            course_plan: Course plan structure from PDF
            course_content: List of course slide content
            
        Returns:
            Content object with filled sections and slide mappings
        """
        # Phase 1: Create outline structure
        outline = self._phase1_create_outline(course_plan, course_content)
        
        # Phase 2: Fill content
        complete_content = self._phase2_fill_content(outline, course_content)
        
        return complete_content
    
    def _phase1_create_outline(self, course_plan: dict, course_content: List[dict]) -> Content:
        """Phase 1: Create hierarchical outline with slide mappings"""
        assistant_message = json.dumps({"course_plan": course_plan}, ensure_ascii=False)
        user_message = json.dumps({"course_content": course_content}, ensure_ascii=False)
        
        response = self.client.responses.parse(
            model=self.model,
            input=[
                {"role": "system", "content": self.phase1_prompt},
                {"role": "assistant", "content": assistant_message},
                {"role": "user", "content": user_message}
            ],
            text_format=Content,
        )
        
        return response.output_parsed
    
    def _phase2_fill_content(self, outline: Content, course_content: List[dict]) -> Content:
        """Phase 2: Fill outline with detailed content"""
        assistant_message = outline.model_dump_json()
        user_message = json.dumps({"course_content": course_content}, ensure_ascii=False)
        
        response = self.client.responses.parse(
            model=self.model,
            input=[
                {"role": "system", "content": self.phase2_prompt},
                {"role": "assistant", "content": assistant_message},
                {"role": "user", "content": user_message},
            ],
            text_format=Content,
        )
        
        return response.output_parsed
    
    def _get_phase1_system_prompt(self) -> str:
        """System prompt for Phase 1: Outline creation"""
        return """
You are a course structure analyzer. Your task is to create a hierarchical outline from course slides and course plan.

## INPUT STRUCTURE:
You will receive TWO inputs:

### Assistant Message - Course Plan:
A hierarchical course plan extracted from slides, like:
```json
{
  "course_plan": {
    "title": "Plan du cours | Agenda du cours | ...",
    "tree": [
      {
        "text": "Cours sur la biologie",
        "children": [
          {
            "text": "Plan du cours", 
            "children": [
              {
                "text": "Section 1",
                "children": [
                  {"text": "Sous section 1.1", "children": []}
                ]
              },
              {
                "text": "Section 2",
                "children": [
                  {"text": "Sous section 2.1", "children": []},
                  {"text": "Sous section 2.2", "children": []}
                ]
              }
            ]
          }
        ]
      }
    ]
  }
}
```

### User Message - Course Content:
All slides including the plan slide:
```json
{
  "course_content": [
    {
      "page": 1,
      "title": "Introduction to Machine Learning", 
      "tree": "extracted content from slide...",
      "images": ["path1.png", "path2.jpg"]
    },
    {
      "page": 2,
      "title": "Plan du cours",
      "tree": [...], // The hierarchical plan structure
      "images": ["diagram.png"]
    }
  ]
}
```

## OUTPUT STRUCTURE:
Return ONLY valid JSON matching this exact schema:
```json
{
  "sections": [
    {
      "title": "Introduction",
      "content": [],  // ALWAYS EMPTY
      "subsections": [
        {
          "title": "Sous section 1.1",
          "content": [],  // ALWAYS EMPTY 
          "subsections": []
        }
      ]
    }
  ],
  "slide_mappings": [
    {
      "slide_number": 1,
      "section_path": ["Section 1"]
    },
    {
      "slide_number": 2, 
      "section_path": ["Section 1", "Sous section 1.1"]
    }
  ]
}
```

## RULES:
1. Use the course_plan from assistant message as your PRIMARY guide for structure
2. Create logical hierarchical sections based on the plan's tree structure
3. NEVER fill the "content" arrays - leave them empty []
4. Map every slide from course_content to exactly one section path
5. Slides that match plan sections should be grouped accordingly
6. Use section titles from the course_plan when available, adapt as needed
7. Ensure slide_mappings covers ALL slides in course_content (including the plan slide)
8. The plan slide itself should be mapped to a top-level or intro section
"""
    
    def _get_phase2_system_prompt(self) -> str:
        """System prompt for Phase 2: Content filling"""
        return """
You are a medical content writer. Your task is to generate detailed course content for each section.

## INPUT STRUCTURE:
- **Assistant message**: Outline of the course and the slide mappings
- **User message**: Original slides data parsed from PDF

The assistant message contains the hierarchy and slide mappings:
```json
{
  "sections": [
    {
      "title": "Chapter 1: Introduction", 
      "content": [],  // Empty 
      "subsections": [...]
    }
  ],
  "slide_mappings": [
    {"slide_number": 1, "section_path": ["Chapter 1: Introduction"]},
    {"slide_number": 2, "section_path": ["Chapter 1: Introduction", "ML Basics"]}
  ]
}
```

## OUTPUT STRUCTURE:
Return the SAME JSON structure but with content arrays filled:
```json
{
  "sections": [
    {
      "title": "Chapter 1: Introduction",
      "content": [
        "L'intelligence artificielle représente...",
        "Les algorithmes d'apprentissage automatique...",
        "Cette approche révolutionnaire permet..."
      ],
      "subsections": [
        {
          "title": "ML Basics",
          "content": [
            "Le machine learning se définit comme...",
            "Les principales catégories incluent..."
          ],
          "subsections": []
        }
      ]
    }
  ],
  "slide_mappings": [
    // Return it EXACTLY the same as assistant message and don't put it in the "sections"
    {"slide_number": 1, "section_path": ["Chapter 1: Introduction"]},
    {"slide_number": 2, "section_path": ["Chapter 1: Introduction", "ML Basics"]}
  ]
}
```

## RULES:
1. For each section in slide_mappings, find corresponding slides from user message
2. Fill the content array of each sections with the content of the slides
3. Write 5-10 French paragraphs per section (≤5 sentences each)
4. Copy section titles EXACTLY - do not change hierarchy
5. Keep slide_mappings IDENTICAL to assistant message
6. Fill ALL content arrays, of all sections and subsections, even if only 1-2 paragraphs
7. Summarize slide content accurately and comprehensively
8. Use clear, educational language appropriate for students
9. Maintain logical flow between paragraphs within each section
""" 