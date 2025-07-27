"""PDF processor for extracting content from PDF slides."""

import os
import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging
from PIL import Image
import io

logger = logging.getLogger(__name__)

@dataclass
class SlideContent:
    """Container for slide content."""
    page_number: int
    text: str
    images: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    bbox: Optional[Tuple[float, float, float, float]] = None

@dataclass
class PDFMetadata:
    """Container for PDF metadata."""
    title: str
    author: str
    subject: str
    creator: str
    producer: str
    creation_date: str
    modification_date: str
    page_count: int

class PDFProcessor:
    """Process PDF files to extract slides content."""
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize PDF processor.
        
        Args:
            output_dir: Directory to save extracted content
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.output_dir / "images").mkdir(exist_ok=True)
        (self.output_dir / "slides").mkdir(exist_ok=True)
        (self.output_dir / "text").mkdir(exist_ok=True)
    
    def extract_pdf_metadata(self, pdf_path: str) -> PDFMetadata:
        """
        Extract metadata from PDF.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            PDFMetadata object with PDF information
        """
        doc = fitz.open(pdf_path)
        metadata = doc.metadata
        
        return PDFMetadata(
            title=metadata.get('title', ''),
            author=metadata.get('author', ''),
            subject=metadata.get('subject', ''),
            creator=metadata.get('creator', ''),
            producer=metadata.get('producer', ''),
            creation_date=metadata.get('creationDate', ''),
            modification_date=metadata.get('modDate', ''),
            page_count=doc.page_count
        )
    
    def extract_text_from_page(self, page: fitz.Page) -> str:
        """
        Extract text from a PDF page.
        
        Args:
            page: PyMuPDF page object
            
        Returns:
            Extracted text string
        """
        try:
            # Extract text with layout preservation
            text = page.get_text("text")
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from page: {e}")
            return ""
    
    def extract_images_from_page(self, page: fitz.Page, page_num: int) -> List[Dict[str, Any]]:
        """
        Extract images from a PDF page.
        
        Args:
            page: PyMuPDF page object
            page_num: Page number
            
        Returns:
            List of image information dictionaries
        """
        images = []
        image_list = page.get_images()
        
        for img_index, img in enumerate(image_list):
            try:
                # Get image data
                xref = img[0]
                base_image = page.parent.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                # Save image
                image_filename = f"page_{page_num:03d}_img_{img_index:02d}.{image_ext}"
                image_path = self.output_dir / "images" / image_filename
                
                with open(image_path, "wb") as img_file:
                    img_file.write(image_bytes)
                
                # Get image dimensions and position
                image_dict = page.get_image_info()[img_index] if img_index < len(page.get_image_info()) else {}
                
                images.append({
                    "filename": image_filename,
                    "path": str(image_path),
                    "size": len(image_bytes),
                    "format": image_ext,
                    "dimensions": (base_image.get("width"), base_image.get("height")),
                    "position": image_dict.get("bbox") if image_dict else None
                })
                
            except Exception as e:
                logger.error(f"Error extracting image {img_index} from page {page_num}: {e}")
        
        return images
    
    def convert_page_to_image(self, page: fitz.Page, page_num: int, 
                            dpi: int = 300) -> str:
        """
        Convert PDF page to image.
        
        Args:
            page: PyMuPDF page object
            page_num: Page number
            dpi: Resolution for image conversion
            
        Returns:
            Path to saved image file
        """
        try:
            # Convert page to image
            mat = fitz.Matrix(dpi/72, dpi/72)  # 72 is default DPI
            pix = page.get_pixmap(matrix=mat)
            
            # Save as PNG
            image_filename = f"slide_{page_num:03d}.png"
            image_path = self.output_dir / "slides" / image_filename
            
            pix.save(str(image_path))
            pix = None  # Free memory
            
            return str(image_path)
            
        except Exception as e:
            logger.error(f"Error converting page {page_num} to image: {e}")
            return ""
    
    def extract_slide_content(self, pdf_path: str, 
                            extract_images: bool = True,
                            convert_to_images: bool = True,
                            dpi: int = 300) -> List[SlideContent]:
        """
        Extract comprehensive content from PDF slides.
        
        Args:
            pdf_path: Path to PDF file
            extract_images: Whether to extract embedded images
            convert_to_images: Whether to convert slides to images
            dpi: Resolution for slide image conversion
            
        Returns:
            List of SlideContent objects
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        doc = fitz.open(pdf_path)
        slides = []
        
        logger.info(f"Processing PDF with {doc.page_count} pages")
        
        for page_num in range(doc.page_count):
            try:
                page = doc[page_num]
                
                # Extract text
                text = self.extract_text_from_page(page)
                
                # Extract images if requested
                images = []
                if extract_images:
                    images = self.extract_images_from_page(page, page_num + 1)
                
                # Convert to image if requested
                slide_image_path = ""
                if convert_to_images:
                    slide_image_path = self.convert_page_to_image(page, page_num + 1, dpi)
                
                # Get page metadata
                metadata = {
                    "page_size": page.rect,
                    "rotation": page.rotation,
                    "slide_image": slide_image_path,
                    "image_count": len(images),
                    "text_length": len(text)
                }
                
                slide_content = SlideContent(
                    page_number=page_num + 1,
                    text=text,
                    images=images,
                    metadata=metadata,
                    bbox=(page.rect.x0, page.rect.y0, page.rect.x1, page.rect.y1)
                )
                
                slides.append(slide_content)
                
                logger.info(f"Processed slide {page_num + 1}: {len(text)} chars, {len(images)} images")
                
            except Exception as e:
                logger.error(f"Error processing page {page_num + 1}: {e}")
        
        doc.close()
        return slides
    
    def save_extracted_text(self, slides: List[SlideContent], filename: str = "extracted_text.txt"):
        """
        Save extracted text to file.
        
        Args:
            slides: List of SlideContent objects
            filename: Output filename
        """
        text_path = self.output_dir / "text" / filename
        
        with open(text_path, 'w', encoding='utf-8') as f:
            for slide in slides:
                f.write(f"=== SLIDE {slide.page_number} ===\n")
                f.write(slide.text)
                f.write("\n\n")
        
        logger.info(f"Saved extracted text to {text_path}")
    
    def get_extraction_summary(self, slides: List[SlideContent]) -> Dict[str, Any]:
        """
        Get summary of extraction results.
        
        Args:
            slides: List of SlideContent objects
            
        Returns:
            Summary dictionary
        """
        total_text_length = sum(len(slide.text) for slide in slides)
        total_images = sum(len(slide.images) for slide in slides)
        
        return {
            "total_slides": len(slides),
            "total_text_length": total_text_length,
            "total_images": total_images,
            "slides_with_text": len([s for s in slides if s.text.strip()]),
            "slides_with_images": len([s for s in slides if s.images]),
            "average_text_per_slide": total_text_length / len(slides) if slides else 0
        } 