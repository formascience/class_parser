import importlib
import course

# Reload the helper module to get the latest changes
importlib.reload(course)

from course import Course, SlideMapping, ContentSection, Content


# Reload the helper module to get the latest changes
importlib.reload(course)

# -------------------- PHASE 1: OUTLINE CREATION --------------------
PHASE_1_SYSTEM_PROMPT = """
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

client = OpenAI()

result_p1 = client.responses.parse(
    model="gpt-4.1-2025-04-14",
    input=[
        {"role": "system",    "content": PHASE_1_SYSTEM_PROMPT},
        {"role": "assistant", "content": json.dumps({"course_plan": course_plan}, ensure_ascii=False)},
        {"role": "user",      "content": json.dumps({"course_content": course_content}, ensure_ascii=False)}
    ],
    text_format=Content,
)

outline: Content = result_p1.output_parsed



from course import Content

# -------- 2. Build the two JSON payloads ---------------
assistant_json = outline.model_dump_json()
slides_json    = json.dumps({"course_content": course_content}, ensure_ascii=False)
#  course_content is still the list of slide dicts you fed in Phase 1
#  (each dict has 'page', 'title', 'tree', … )

# -------- 3. Prompt for the writer model ---------------
PHASE_2_SYSTEM_PROMPT = """
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

result2 = client.responses.parse(
    model="gpt-4.1-2025-04-14",
    input=[
        {"role": "system",    "content": PHASE_2_SYSTEM_PROMPT},
        {"role": "assistant", "content": assistant_json},
        {"role": "user",      "content": slides_json},
    ],
    text_format=Content,     # guarantees parse‑able output
)

course_draft: Content = result2.output_parsed
print("✅ Phase 2 done – got", len(course_draft.sections), "top‑level sections")


import importlib
from course import Course, Content




cours_1 = Course(
    name="Les molécules du vivant",
    subject="Biologie",
    year=2025,
    professor="Professeur 1",

)
cours_1.content = course_draft


cours_1.export_to_docx()