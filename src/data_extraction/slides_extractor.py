"""
Extract slides from PDF - pure deterministic processing
Based on the exact implementation from poc.ipynb
"""

import logging
from statistics import mean
from typing import Any, Dict, List

import pdfplumber

logger = logging.getLogger(__name__)

from ..models import Slides


class SlidesExtractor:
    """Handles PDF slide extraction - pure deterministic processing"""
    
    def __init__(self, 
                 min_avg_len: int = 10,
                 max_lines: int = 20,
                 merge_tol: float = 2.0):
        """
        Initialize slides extractor with parameters
        
        Args:
            min_avg_len: Minimum average line length to consider a slide
            max_lines: Maximum number of lines to consider a slide
            merge_tol: Tolerance for merging words into rows
        """
        self.min_avg_len = min_avg_len
        self.max_lines = max_lines
        self.merge_tol = merge_tol
    
    def extract_slides(self, pdf_path: str) -> List[Slides]:
        """
        Extract slides from PDF file
        Based on the exact implementation from poc.ipynb
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of Slides objects
        """
        slides = []
        logger.debug("Starting slide extraction from %s", pdf_path)
        try:
            with pdfplumber.open(pdf_path) as pdf:
                logger.debug("PDF opened, found %d pages", len(pdf.pages))
                for page in pdf.pages:
                    txt = page.extract_text() or ""
                    lines = [l for l in txt.splitlines() if l.strip()]
                    if not lines:                      # page vide
                        continue
                    if mean(map(len, lines)) < self.min_avg_len or len(lines) > self.max_lines:
                        continue

                    words = page.extract_words(extra_attrs=["size"], use_text_flow=True)
                    # regroupe en lignes
                    rows, cur, cur_top = [], [], None
                    for w in sorted(words, key=lambda w: w["top"]):
                        if cur_top is None or abs(w["top"] - cur_top) <= self.merge_tol:
                            cur.append(w); cur_top = cur_top or w["top"]
                        else:
                            rows.append(cur); cur, cur_top = [w], w["top"]
                    if cur: rows.append(cur)

                    first5 = rows[:5]
                    title = (
                        " ".join(w["text"] for w in max(first5,
                                                        key=lambda r: mean(w["size"] for w in r)))
                        if first5 else f"Slide {page.page_number}"
                    )

                    slide = Slides(
                        id=f"SL_{page.page_number:03}",   # <─ identifiant slide
                        title=title,
                        content=txt.strip()
                    )
                    slides.append(slide)
        
            logger.debug("Successfully extracted %d slides", len(slides))
            return slides
            
        except Exception as e:
            logger.error("Failed to extract slides from %s: %s", pdf_path, str(e))
            raise
    
    def extract_raw_slides(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract slides as raw dictionaries (compatible with poc.ipynb format)
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of raw slide dictionaries
        """
        slides = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                txt = page.extract_text() or ""
                lines = [l for l in txt.splitlines() if l.strip()]
                if not lines:                      # page vide
                    continue
                if mean(map(len, lines)) < self.min_avg_len or len(lines) > self.max_lines:
                    continue

                words = page.extract_words(extra_attrs=["size"], use_text_flow=True)
                # regroupe en lignes
                rows, cur, cur_top = [], [], None
                for w in sorted(words, key=lambda w: w["top"]):
                    if cur_top is None or abs(w["top"] - cur_top) <= self.merge_tol:
                        cur.append(w); cur_top = cur_top or w["top"]
                    else:
                        rows.append(cur); cur, cur_top = [w], w["top"]
                if cur: rows.append(cur)

                first5 = rows[:5]
                title = (
                    " ".join(w["text"] for w in max(first5,
                                                    key=lambda r: mean(w["size"] for w in r)))
                    if first5 else f"Slide {page.page_number}"
                )

                slides.append({
                    "id": f"SL_{page.page_number:03}",   # <─ identifiant slide
                    "title": title,
                    "content": txt.strip()
                })
        
        return slides