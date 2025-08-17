import textwrap
from typing import Any, Dict, List, Optional

import tiktoken
from pydantic import BaseModel, Field


class Slides(BaseModel):
    """Represents a slide with its content"""
    id: str
    title: str
    content: str


class CourseMetadata(BaseModel):
    """Minimal input metadata used to initialize a Course in the pipeline."""

    # Core identifiers
    name: str
    course_title: Optional[str] = None

    # Academic hierarchy
    level: Optional[str] = None  # e.g., L1, L2, L3, M1, M2
    block: Optional[str] = None  # e.g., BLOC_SANTE, TRANSVERSAL, DISCIPLINAIRE
    semester: Optional[str] = None  # e.g., S1, S2
    subject: Optional[str] = None
    chapter: Optional[str] = None

    # Additional optional metadata
    year: Optional[int] = None
    professor: Optional[str] = None

class MappingItem(BaseModel):
    section_id: str
    slide_ids: List[str]


class SectionSlideMapping(BaseModel):
    mapping: List[MappingItem]

    def visualize_mapping(self, outline: "Content") -> str:
        """
        Visualize the section-to-slides mapping with titles, counts, and slide IDs.

        Args:
            outline: The Content object containing the course structure with section titles

        Returns:
            A formatted string showing the mapping visualization
        """
        if not self.mapping:
            return "No mapping available"

        # Create a lookup dictionary for section IDs to titles
        section_lookup: Dict[str, Dict[str, Any]] = {}

        def collect_sections(sections: List["ContentSection"], depth: int = 0):
            for section in sections:
                section_lookup[section.id] = {"title": section.title, "depth": depth}
                collect_sections(section.subsections, depth + 1)

        collect_sections(outline.sections)

        result = "Section-to-Slides Mapping:\n"
        result += "=" * 60 + "\n\n"

        # Sort mapping by section_id for consistent output
        sorted_mapping = sorted(self.mapping, key=lambda x: x.section_id)

        for item in sorted_mapping:
            section_info = section_lookup.get(
                item.section_id,
                {"title": f"Unknown Section ({item.section_id})", "depth": 0},
            )

            indent = "  " * int(section_info["depth"])
            level_indicator = (
                f"[Level {section_info['depth']}]"
                if int(section_info["depth"]) > 0
                else "[Root]"
            )

            result += f"{indent}{level_indicator} {item.section_id}\n"
            result += f"{indent}Title: {section_info['title']}\n"
            result += f"{indent}Slides: {len(item.slide_ids)} slide(s)\n"
            result += f"{indent}Slide IDs: {', '.join(item.slide_ids)}\n"
            result += "\n"

        return result.rstrip()

    def get_section_summary(self, outline: "Content") -> Dict[str, Dict]:
        """
        Get a summary dictionary of the mapping for programmatic use.

        Args:
            outline: The Content object containing the course structure

        Returns:
            Dictionary mapping section_id to summary info
        """
        section_lookup: Dict[str, Dict[str, Any]] = {}

        def collect_sections(sections: List["ContentSection"], depth: int = 0):
            for section in sections:
                section_lookup[section.id] = {"title": section.title, "depth": depth}
                collect_sections(section.subsections, depth + 1)

        collect_sections(outline.sections)

        summary: Dict[str, Dict[str, Any]] = {}
        for item in self.mapping:
            section_info = section_lookup.get(
                item.section_id,
                {"title": f"Unknown Section ({item.section_id})", "depth": 0},
            )

            summary[item.section_id] = {
                "title": section_info["title"],
                "depth": section_info["depth"],
                "slide_count": len(item.slide_ids),
                "slide_ids": item.slide_ids,
            }

        return summary


class ContentSection(BaseModel):
    """A section that can contain both outline structure and content"""

    id: str
    title: str
    content: List[str] = Field(default_factory=list)
    subsections: List["ContentSection"] = Field(default_factory=list)

    def _print_section(self, indent_level: int = 0) -> str:
        """Helper method to print section outline with proper indentation (for phase 1)"""
        indent = "  " * indent_level
        result = f"{indent}{self.title}\n"

        for subsection in self.subsections:
            result += subsection._print_section(indent_level + 1)

        return result

    def get_token_count(self) -> int:
        """
        Calculate the token count for this section including all subsections.
        Dumps the section to JSON before encoding with tiktoken (GPT-4 encoding).

        Returns:
            int: Total number of tokens for this section and all subsections
        """

        # Get GPT-4 encoding
        encoder = tiktoken.get_encoding("cl100k_base")

        # Dump this section to JSON string
        section_json = self.model_dump_json()

        # Encode and count tokens
        token_count = len(encoder.encode(section_json))

        return token_count

    def _print_content_section(self, indent_level: int = 0) -> str:
        """Helper method to print section content with proper indentation and IDs (for phase 2)"""
        indent = "  " * indent_level
        level_indicator = f"[Level {indent_level}]" if indent_level > 0 else "[Root]"

        result = f"{indent}{level_indicator} ID: {self.id}\n"
        result += f"{indent}Title: {self.title}\n"

        if self.content and any(
            c.strip() for c in self.content
        ):  # Check if any content item has text
            result += f"{indent}Content:\n"
            for i, content_item in enumerate(self.content):
                if content_item.strip():  # Only show non-empty content
                    result += f"{indent}  [{i+1}] "
                    # Wrap content and add proper indentation
                    content_lines = textwrap.fill(
                        content_item.strip(), width=80 - len(indent) - 6
                    ).split("\n")
                    result += content_lines[0] + "\n"  # First line
                    for line in content_lines[
                        1:
                    ]:  # Remaining lines with extra indentation
                        result += f"{indent}      {line}\n"
        else:
            result += f"{indent}Content: [No content available]\n"

        result += "\n"  # Add spacing between sections

        # Recursively print subsections
        for subsection in self.subsections:
            result += subsection._print_content_section(indent_level + 1)

        return result


ContentSection.model_rebuild()


class Content(BaseModel):
    """Course structure that works for both outline (phase 1) and content (phase 2)"""

    sections: List[ContentSection]
    # Optional properties for slides integration
    slides: Optional[List[Slides]] = None
    mapping: Optional[SectionSlideMapping] = None

    def enrich_with_slides(self, slides: List[Slides], mapping: SectionSlideMapping) -> "Content":
        """
        Enrich this Content object with slides data based on the mapping.
        
        Args:
            slides: List of Slides objects containing the slide content
            mapping: SectionSlideMapping object that maps sections to slides
            
        Returns:
            Self for method chaining
        """
        self.slides = slides
        self.mapping = mapping
        self._enrich_content_with_slides()
        return self

    def _enrich_content_with_slides(self):
        """Add slides content directly to the content field of each ContentSection based on the mapping"""
        if not self.slides or not self.mapping:
            return
            
        # Create a lookup dictionary for slides by ID
        slides_lookup = {slide.id: slide for slide in self.slides}

        # Create a mapping from section_id to slide_ids
        section_to_slides = {}
        for mapping_item in self.mapping.mapping:
            section_to_slides[mapping_item.section_id] = mapping_item.slide_ids

        # Recursively enrich all sections
        def enrich_sections(sections: List[ContentSection]):
            for section in sections:
                # Get slide IDs mapped to this section
                slide_ids = section_to_slides.get(section.id, [])

                # Get raw content from slides
                raw_slides_content = []
                for slide_id in slide_ids:
                    if slide_id in slides_lookup:
                        raw_slides_content.append(slides_lookup[slide_id].content)

                # Update the section with slides content as a list
                section.content = raw_slides_content

                # Recursively process subsections
                enrich_sections(section.subsections)

        enrich_sections(self.sections)

    def print_outline(self) -> str:
        """Print the hierarchical outline with indentation (for phase 1)"""
        if not self.sections:
            return "No outline available"

        result = "Course Outline:\n"
        result += "=" * 50 + "\n"

        for section in self.sections:
            result += section._print_section()

        return result.rstrip()  # Remove trailing newline

    def print_content(self) -> str:
        """Print the hierarchical content with indentation, IDs, and depth levels"""
        if not self.sections:
            return "No content available"

        result = "Course Content:\n"
        result += "=" * 60 + "\n\n"

        for section in self.sections:
            result += section._print_content_section()

        return result.rstrip()  # Remove trailing newline

    def get_slides_summary(self) -> Dict[str, int]:
        """Get a summary of content length per section"""
        summary = {}

        def collect_section_slides(sections: List[ContentSection]):
            for section in sections:
                # Count total characters across all content items
                total_chars = sum(len(content_item) for content_item in section.content)
                summary[section.id] = total_chars
                collect_section_slides(section.subsections)

        collect_section_slides(self.sections)
        return summary

    def visualize_mapping(self) -> str:
        """Visualize the section-to-slides mapping if available"""
        if self.mapping:
            return self.mapping.visualize_mapping(self)
        return "No mapping available"


Content.model_rebuild()


class OutlineAndMapping(BaseModel):
    outline: Content
    mapping: List[MappingItem]


