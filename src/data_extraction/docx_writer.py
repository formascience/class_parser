from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from docx import Document
from docx.shared import Pt, RGBColor


class DocxWriter:
    """Generate a professionally formatted .docx from a Course-like object.

    The provided ``course`` object is expected to expose at least the following
    attributes used by this writer: ``name``, ``course_title``, ``level``,
    ``block``, ``semester``, ``subject``, and ``content`` (with hierarchical
    sections structure matching the models in ``src/models.py``).
    """

    def __init__(
        self,
        template_path: str = "volume/fs_template.docx",
        title_font: str = "Manrope",
        title_size: int = 16,
        title_color: tuple[int, int, int] = (0, 0, 0),
        content_font: str = "Arial",
        content_size: int = 10,
        table_font: str = "Arial",
        table_size: int = 11,
        table_color: tuple[int, int, int] = (0, 0, 0),
    ) -> None:
        self.template_path = template_path

        # Title formatting
        self.title_font = title_font
        self.title_size = title_size
        self.title_color = title_color

        # Content formatting
        self.content_font = content_font
        self.content_size = content_size

        # Table formatting
        self.table_font = table_font
        self.table_size = table_size
        self.table_color = table_color

    def fill_template(self, course: Any, output_path: Optional[str] = None) -> str:
        """Fill the Word template with course metadata and content.

        Returns the path to the saved .docx file.
        """
        doc = Document(self.template_path)

        # Page-level spacing: ensure a consistent gap after page header on all pages
        for section in doc.sections:
            section.header_distance = Pt(24)  # distance from page top to header
            section.top_margin = Pt(108)  # 1.5 inches to keep body below header
            section.left_margin = Pt(72)
            section.right_margin = Pt(72)
            section.bottom_margin = Pt(72)

        self._fill_title(doc, course)
        self._fill_table(doc, course)
        self._fill_header(doc, course)

        if getattr(course, "content", None):
            self._write_content(doc, course.content)

        if not output_path:
            saved_name = (course.name or "course").lower().replace(" ", "_")
            output_path = f"volume/artifacts/{saved_name}_filled.docx"

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        doc.save(output_path)
        return output_path

    def _fill_title(self, doc: Any, course: Any) -> None:
        for paragraph in doc.paragraphs:
            if "TITRE DU COURS" in paragraph.text:
                paragraph.text = getattr(course, "course_title", None) or course.name
                for run in paragraph.runs:
                    run.font.name = self.title_font
                    run.font.size = Pt(self.title_size)
                    run.font.bold = True
                    r, g, b = self.title_color
                    run.font.color.rgb = RGBColor(r, g, b)
                break

    def _fill_table(self, doc: Any, course: Any) -> None:
        if len(doc.tables) == 0:
            return

        table = doc.tables[0]
        cells_data = [
            (0, 0, f"BLOC {getattr(course, 'block', None) or 'SANTE'}"),
            (1, 0, getattr(course, "subject", "")),
            (0, 1, "Auteur : RonéoAI"),
            (1, 1, f"Date : {datetime.now().strftime('%Y-%m-%d')}")
        ]

        for row, col, text in cells_data:
            cell = table.rows[row].cells[col]
            cell.text = text
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.name = self.table_font
                    run.font.size = Pt(self.table_size)
                    r, g, b = self.table_color
                    run.font.color.rgb = RGBColor(r, g, b)

    def _fill_header(self, doc: Any, course: Any) -> None:
        for paragraph in doc.paragraphs:
            if "L1.SpS" in paragraph.text:
                new_level = f"{getattr(course, 'level', None) or 'L1'}.{getattr(course, 'semester', None) or 'S1'}"
                paragraph.text = paragraph.text.replace("L1.SpS", new_level)
                break

    def _write_content(self, doc: Any, content: Any) -> None:
        for i, section in enumerate(content.sections, start=1):
            roman_title = f"{self._to_roman(i)}. {section.title}"
            heading1 = doc.add_paragraph(roman_title, style="Heading 1")

            heading1_format = heading1.paragraph_format
            heading1_format.space_before = Pt(36)
            heading1_format.space_after = Pt(12)

            for run in heading1.runs:
                run.font.name = self.title_font  # Level 0 uses title font
                run.font.size = Pt(self.title_size)
                run.font.bold = True
                # Leaf green
                run.font.color.rgb = RGBColor(34, 139, 34)

            if section.content:
                for content_item in section.content:
                    if content_item and content_item.strip():
                        p = doc.add_paragraph(content_item.strip())
                        p.paragraph_format.space_after = Pt(6)
                        p.paragraph_format.line_spacing = 1.15
                        for run in p.runs:
                            run.font.name = self.content_font
                            run.font.size = Pt(self.content_size)

            self._write_subsections(doc, section.subsections, i)

    def _write_subsections(
        self, doc: Any, subsections: list[Any], parent_num: int | str, level: int = 1
    ) -> None:
        for j, subsection in enumerate(subsections, start=1):
            if level == 1:
                subtitle = f"{j}. {subsection.title}"
                heading = doc.add_paragraph(subtitle, style="Heading 2")
                heading.paragraph_format.space_before = Pt(12)
                heading.paragraph_format.space_after = Pt(6)
                for run in heading.runs:
                    run.font.name = self.table_font
                    run.font.size = Pt(self.title_size - 2)
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(0, 0, 0)
            elif level == 2:
                subtitle = f"{parent_num}.{j} {subsection.title}"
                heading = doc.add_paragraph(subtitle, style="Heading 3")
                heading.paragraph_format.space_before = Pt(10)
                heading.paragraph_format.space_after = Pt(6)
                for run in heading.runs:
                    run.font.name = self.table_font
                    run.font.size = Pt(self.title_size - 3)
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(0, 0, 0)
            else:
                subtitle = f"{parent_num}.{j} {subsection.title}"
                heading = doc.add_paragraph(subtitle)
                heading.paragraph_format.space_before = Pt(8)
                heading.paragraph_format.space_after = Pt(4)
                for run in heading.runs:
                    run.font.name = self.table_font
                    run.font.size = Pt(self.title_size - 4)
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(0, 0, 0)

            if getattr(subsection, "content", None):
                for content_item in subsection.content:
                    if content_item and content_item.strip():
                        p = doc.add_paragraph(content_item.strip())
                        p.paragraph_format.space_after = Pt(6)
                        p.paragraph_format.line_spacing = 1.15
                        for run in p.runs:
                            run.font.name = self.content_font
                            run.font.size = Pt(self.content_size)

            if getattr(subsection, "subsections", None):
                self._write_subsections(
                    doc, subsection.subsections, f"{parent_num}.{j}", level + 1
                )

    def _to_roman(self, num: int) -> str:
        vals = [10, 9, 5, 4, 1]
        syms = ["X", "IX", "V", "IV", "I"]
        roman = ""
        for val, sym in zip(vals, syms):
            count = num // val
            roman += sym * count
            num -= val * count
        return roman


