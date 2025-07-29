"""
PDF text extraction and tree structure processing
"""

import os
import re
import pdfplumber
from typing import List, Dict, Tuple, Optional


class PDFProcessor:
    """Handles PDF text extraction and conversion to hierarchical tree structure"""
    
    def __init__(self, indent_tolerance: int = 5):
        self.bullet_chars = "•◦‣▪–"
        self.banner_regex = re.compile(r"^L\\d?SpS:")
        self.indent_tolerance = indent_tolerance
    
    def get_all_trees(self, pdf_path: str) -> List[dict]:
        """
        Get all slide trees exactly like original pdf_to_dict.py - for comparison
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of all slide trees (before any separation)
        """
        deck = self._extract_lines(pdf_path)
        slides = self._split_bullets(deck)
        trees = [self._create_bullet_tree(slide) for slide in slides]
        return trees
    
    def process_pdf(self, pdf_path: str) -> Tuple[dict, List[dict]]:
        """
        Process PDF and return course plan and content
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Tuple of (course_plan, course_content) where course_plan is from page 2
            and course_content is all other pages
        """
        trees = self.get_all_trees(pdf_path)
        
        # Extract course plan (page 2) and remaining content - matching original logic
        course_plan = trees[1]  # Get the course plan (typically page 2)
        trees.pop(1)  # Remove course plan from trees
        course_content = trees  # Remaining slides
        
        return course_plan, course_content
    
    def _extract_lines(self, pdf_path: str) -> List[dict]:
        """Extract lines from PDF pages with banner filtering"""
        deck = []
        banner_hits = {}

        with pdfplumber.open(pdf_path) as pdf:
            for idx, page in enumerate(pdf.pages, 1):
                words = page.extract_words(use_text_flow=True, extra_attrs=["size"])
                rows: Dict[float, List[dict]] = {}
                
                for word in words:
                    text = word["text"].strip()
                    if self.banner_regex.match(text):
                        banner_hits[text] = banner_hits.get(text, 0) + 1
                        continue
                    
                    y = round(word["top"], 1)
                    rows.setdefault(y, []).append(word)

                lines = []
                for y in sorted(rows):
                    row_words = sorted(rows[y], key=lambda w: w["x0"])
                    x0 = row_words[0]["x0"]
                    text = " ".join(w["text"] for w in row_words)
                    text = re.sub(rf"\s*{idx}\s*$", "", text).strip()
                    
                    if text:
                        lines.append((x0, text, row_words))

                deck.append({
                    "page": idx,
                    "title": self._extract_slide_title(words),
                    "lines": lines
                })

        # Filter out banner texts that appear on most pages
        banner_texts = {text for text, count in banner_hits.items() 
                       if count / len(deck) >= 0.8}
        
        for slide in deck:
            slide["lines"] = [(x, t, rw) for x, t, rw in slide["lines"] 
                             if t not in banner_texts]

        return deck
    
    def _extract_slide_title(self, words: List[dict], top_cutoff: int = 150, use_biggest_font: int = 1) -> str:
        """Extract slide title - EXACT original logic"""
        if not words: 
            return ""
        
        # If flag is 1, find the biggest font string from all words
        if use_biggest_font == 1:
            max_size = max(w["size"] for w in words)
            biggest_font_words = sorted([w for w in words 
                                       if abs(w["size"] - max_size) < 0.5],
                                      key=lambda w: w["x0"])
            return " ".join(w["text"] for w in biggest_font_words)
        
        # Original logic for when flag is not 1
        top_words = [w for w in words if w["top"] < top_cutoff]
        if not top_words: 
            return ""
        max_size = max(w["size"] for w in top_words)
        title_words = sorted([w for w in top_words
                              if abs(w["size"] - max_size) < 0.5],
                             key=lambda w: w["x0"])
        return " ".join(w["text"] for w in title_words)
    
    def _first_bullet_x(self, row_words: List[dict]) -> Optional[float]:
        """Find x-position of first bullet character in row - EXACT original"""
        for w in row_words:
            if any(c in w["text"] for c in self.bullet_chars):
                return w["x0"]
        return None
    
    def _explode_line(self, x0: float, line: str, row_words: List[dict], page_idx: int) -> List[dict]:
        """
        If the row is "Parent • child • child", use x‑pos of the first bullet
        glyph for all children so that INTRO and "Le génome humain" share the
        SAME indent. - EXACT original
        """
        line = re.sub(rf"\s*{page_idx}\s*$", "", line).strip()
        if "•" not in line:
            return [{"indent": x0, "text": line}]

        head, tail = line.split("•", 1)
        head = head.strip()
        out = []

        # parent node (if any)
        if head:
            out.append({"indent": x0, "text": head})

        bullet_x = self._first_bullet_x(row_words) or x0
        children = [frag.strip() for frag in tail.split("•") if frag.strip()]
        out.extend({"indent": bullet_x, "text": c} for c in children)
        return out
    
    def _split_bullets(self, deck: List[dict]) -> List[dict]:
        """Convert deck lines to individual bullet items - EXACT original"""
        slides = []
        for sl in deck:
            bullets = []
            for x, txt, row in sl["lines"]:
                bullets.extend(self._explode_line(x, txt, row, sl["page"]))
            slides.append({"page": sl["page"], "title": sl["title"], "bullets": bullets})
        return slides
    
    def _create_bullet_tree(self, slide: dict) -> dict:
        """Convert flat bullet list to nested tree structure - EXACT copy from original"""
        bullets = slide["bullets"]
        if not bullets:
            return {"page": slide["page"], "title": slide["title"], "tree": []}

        indents = sorted({b["indent"] for b in bullets})
        # cluster indents - EXACT original logic
        groups, cur = [], [indents[0]]
        for x in indents[1:]:
            if x - cur[-1] <= self.indent_tolerance: 
                cur.append(x)
            else: 
                groups.append(cur)
                cur = [x]
        groups.append(cur)
        depth = {x: i for i, g in enumerate(groups) for x in g}

        root, stack = [], []
        for b in bullets:
            lvl = depth[b["indent"]]
            node = {"text": b["text"], "children": []}
            while len(stack) > lvl: 
                stack.pop()
            (root if not stack else stack[-1]["children"]).append(node)
            stack.append(node)

        return {"page": slide["page"], "title": slide["title"], "tree": root} 