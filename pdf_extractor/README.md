# PDF Slide Extractor & Parser

A comprehensive Python module for extracting, parsing, and organizing content from PDF presentations with intelligent section detection.

## 🌟 Features

### Core Extraction
- **Text Extraction**: Extract all text content from PDF slides
- **Image Extraction**: Save embedded images from slides
- **Slide Images**: Convert each slide to high-resolution images
- **Metadata Extraction**: Get PDF metadata (title, author, page count, etc.)

### Advanced Parsing
- **Title Detection**: Automatically identify slide titles
- **Bullet Point Extraction**: Parse bullet points and lists
- **Paragraph Extraction**: Extract paragraph content
- **Keyword Analysis**: Identify important terms and topics

### 🎯 Section Detection (NEW!)
- **Smart Section Detection**: Automatically identify section divider slides
- **Section Organization**: Group slides into logical sections
- **Section-Based Extraction**: Extract content by individual sections
- **Section Analysis**: Get keywords and summaries for each section

## 📦 Installation

Add the required dependencies to your project:

```bash
poetry add pymupdf pillow
# or with pip
pip install pymupdf pillow
```

## 🚀 Quick Start

### Basic Usage

```python
from pdf_extractor import PDFProcessor, SlideParser

# Initialize
processor = PDFProcessor(output_dir="output")
parser = SlideParser()

# Extract slides
slides = processor.extract_slide_content("presentation.pdf")

# Parse structure
parsed_slides = parser.parse_slides(slides)
structure = parser.analyze_presentation_structure(parsed_slides)

# Show sections
for section in structure.sections:
    print(f"Section: {section.title}")
    print(f"Slides: {section.start_page}-{section.end_page}")
```

### CLI Usage

The module provides several CLI commands:

#### 1. Extract All Content
```bash
# Basic extraction
python -m pdf_extractor extract presentation.pdf

# With custom options
python -m pdf_extractor extract presentation.pdf \
    --output-dir my_output \
    --dpi 300 \
    --save-text \
    --json-output
```

#### 2. Parse Structure & Find Sections
```bash
# Analyze slide structure
python -m pdf_extractor parse presentation.pdf --detailed

# Results show:
# - Overall presentation summary
# - Section breakdown
# - Slide types and importance scores
# - Keywords and topics
```

#### 3. Analyze & Extract Sections
```bash
# Show all sections
python -m pdf_extractor sections presentation.pdf

# Extract each section to separate directories
python -m pdf_extractor sections presentation.pdf --extract-sections

# With detailed analysis
python -m pdf_extractor sections presentation.pdf --detailed --json-output
```

#### 4. Extract Specific Section
```bash
# Extract only section 2
python -m pdf_extractor extract-section presentation.pdf 2

# With images and metadata
python -m pdf_extractor extract-section presentation.pdf 3 \
    --json-output \
    --output-dir section_3_output
```

## 🎯 Section Detection

The module automatically detects section divider slides based on:

### Detection Criteria
- **Clear Title**: Slide has a prominent title
- **Minimal Content**: Little additional text beyond the title
- **Section Keywords**: Contains words like "Chapter", "Section", "Part", "Lesson"
- **Pattern Matching**: Matches patterns like "Chapter 1:", "Section A", "Part 2"
- **Structural Position**: Appears at logical breakpoints

### Examples of Detected Section Dividers
✅ **DETECTED**:
- "Chapter 1: Introduction"
- "Section 2: Methodology" 
- "Part A: Background"
- "Lesson 3: Advanced Topics"
- "Overview" (minimal content)

❌ **NOT DETECTED**:
- "Detailed Analysis Results" (has bullet points and charts)
- "Implementation Steps" (contains code examples)
- "Case Study: Company X" (has substantial content)

## 📊 Output Structure

### Directory Layout
```
output/
├── images/              # Extracted embedded images
│   ├── page_001_img_00.png
│   └── page_002_img_01.jpg
├── slides/              # Slide images (PNG)
│   ├── slide_001.png
│   └── slide_002.png
├── text/                # Extracted text files
│   └── extracted_slides.txt
├── sections/            # Section-based organization
│   ├── section_01_Introduction/
│   │   ├── section_text.txt
│   │   └── section_info.json
│   └── section_02_Methodology/
│       ├── section_text.txt
│       └── section_info.json
├── extraction_results.json
├── parsing_results.json
└── sections_summary.json
```

### JSON Output Examples

#### Section Summary
```json
{
  "presentation_title": "Machine Learning Fundamentals",
  "total_sections": 3,
  "sections": [
    {
      "section_number": 1,
      "title": "Chapter 1: Introduction",
      "start_page": 2,
      "end_page": 8,
      "total_slides": 7,
      "keywords": ["machine", "learning", "introduction", "basics"],
      "summary": "Contains 7 slides | 12 bullet points | Key topics: machine, learning, introduction"
    }
  ]
}
```

#### Parsing Results
```json
{
  "presentation_summary": "Presentation: ML Course\nTotal slides: 45\nOrganized into 5 sections...",
  "structure": {
    "total_slides": 45,
    "sections": [...],
    "main_topics": ["Introduction", "Algorithms", "Applications"],
    "keyword_frequency": {"machine": 15, "learning": 12, "algorithm": 8}
  },
  "parsed_slides": [
    {
      "page_number": 1,
      "title": "Machine Learning Course",
      "slide_type": "title",
      "importance_score": 0.7,
      "bullet_points": [],
      "keywords": ["machine", "learning", "course"]
    }
  ]
}
```

## 🔧 Advanced Configuration

### Custom Section Detection
```python
parser = SlideParser()

# Check if a slide is a section divider
is_divider = parser.is_section_divider(parsed_slide)

# Customize detection by modifying parser attributes
parser.section_keywords.extend(['module', 'unit', 'phase'])
```

### Processing Options
```python
# Fine-tune extraction
slides = processor.extract_slide_content(
    pdf_path="presentation.pdf",
    extract_images=True,      # Extract embedded images
    convert_to_images=True,   # Convert slides to images  
    dpi=300                   # Image resolution
)

# Customize parsing
parsed_slides = parser.parse_slides(slides)

# Custom keyword extraction
keywords = parser.extract_keywords(
    text="sample text",
    min_freq=2,              # Minimum word frequency
    max_keywords=15          # Maximum keywords to return
)
```

## 🎓 Use Cases

### For Educators
- **Course Organization**: Split lecture slides by topics/chapters
- **Content Analysis**: Identify key concepts and terms
- **Material Preparation**: Extract specific sections for assignments

### For Students  
- **Study Organization**: Break down long presentations into manageable sections
- **Note Taking**: Extract text content section by section
- **Review Preparation**: Focus on specific topics/chapters

### For Researchers
- **Content Analysis**: Analyze presentation structure and topics
- **Data Extraction**: Get structured data from slide content
- **Batch Processing**: Process multiple presentations systematically

## 🛠️ Development

### Running Examples
```bash
# Run the example usage file
cd pdf_extractor
python example_usage.py
```

### Testing Section Detection
The example file includes a demo of the section detection logic:
```python
from pdf_extractor.example_usage import demonstrate_section_detection_logic
demonstrate_section_detection_logic()
```

## 📝 CLI Command Reference

| Command | Purpose | Key Options |
|---------|---------|-------------|
| `extract` | Extract all content | `--save-text`, `--json-output`, `--dpi` |
| `parse` | Analyze structure | `--detailed`, `--json-output` |
| `sections` | Work with sections | `--extract-sections`, `--detailed` |
| `extract-section` | Get specific section | `--json-output`, section number |

### Common Options
- `--output-dir`: Custom output directory
- `--no-images`: Skip embedded image extraction
- `--no-slide-images`: Skip slide-to-image conversion
- `--dpi`: Image resolution (default: 300)
- `--json-output`: Save structured JSON results
- `--detailed`: Show detailed analysis

## 🔍 Tips & Best Practices

1. **Section Detection**: Works best with consistently formatted presentations
2. **Large PDFs**: Use `--no-images` for faster processing of text-only extraction
3. **High Quality**: Use `--dpi 600` for publication-quality slide images
4. **Organization**: Use `--extract-sections` to get cleanly organized output
5. **Analysis**: Use `--detailed` with `parse` command for comprehensive analysis

---

**Note**: Place your PDF file in the project directory and ensure it's named correctly when running examples. The section detection algorithm is designed for educational and professional presentations with clear structural divisions. 