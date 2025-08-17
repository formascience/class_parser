"""
Plan detection & extraction from PDF
Based on the exact implementation from poc.ipynb
"""

import logging
from typing import Optional

import pdfplumber

logger = logging.getLogger(__name__)


class PlanExtractor:
    """Handles plan text extraction from PDF files"""
    
    def __init__(self):
        """Initialize plan extractor"""
        pass
    
    def extract_pdf_text(self, pdf_path: str, page_number: Optional[int] = None) -> str:
        """
        Extract text from a PDF file, either from a specific page or the full document.
        Based on the exact implementation from poc.ipynb
        
        Args:
            pdf_path: Path to the PDF file
            page_number: Optional page number to extract (1-based). If None, extracts full PDF.
        
        Returns:
            Extracted text as string
        """
        logger.debug("Starting plan extraction from %s (page %s)", pdf_path, page_number or "all")
        try:
            with pdfplumber.open(pdf_path) as pdf:
                logger.debug("PDF opened, found %d pages", len(pdf.pages))
                if page_number is not None:
                    # Adjust for 0-based page indexing
                    page_idx = page_number - 1
                    if page_idx < 0 or page_idx >= len(pdf.pages):
                        logger.error("Page number %d is out of range (1-%d)", page_number, len(pdf.pages))
                        raise ValueError(f"Page number {page_number} is out of range")
                    
                    page = pdf.pages[page_idx]
                    text = page.extract_text(layout=True)
                    # Remove multiple consecutive newlines
                    plan_text = '\n'.join(line for line in text.splitlines() if line.strip())
                    logger.debug("Successfully extracted plan from page %d (%d chars)", page_number, len(plan_text))
                
                else:
                    # Extract full PDF
                    all_text = []
                    for page in pdf.pages:
                        text = page.extract_text(layout=True)
                        # Remove multiple consecutive newlines 
                        text = '\n'.join(line for line in text.splitlines() if line.strip())
                        all_text.append(text)
                    plan_text = '\n'.join(all_text)
                    logger.debug("Successfully extracted plan from full PDF (%d chars)", len(plan_text))

            return plan_text
            
        except Exception as e:
            logger.error("Failed to extract plan from %s: %s", pdf_path, str(e))
            raise
        
    def extract_plan_from_pdf(self, pdf_path: str) -> str:
        """
        Extract plan text from full PDF
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Full PDF text as plan
        """
        return self.extract_pdf_text(pdf_path)
    
    def extract_plan_from_page(self, pdf_path: str, page_number: int) -> str:
        """
        Extract plan text from specific page
        
        Args:
            pdf_path: Path to the PDF file
            page_number: Page number to extract (1-based)
            
        Returns:
            Page text as plan
        """
        return self.extract_pdf_text(pdf_path, page_number)
