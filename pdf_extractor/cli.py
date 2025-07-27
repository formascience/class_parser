"""Command-line interface for PDF slide extraction and parsing."""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from .pdf_processor import PDFProcessor
from .slide_parser import SlideParser

def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def extract_command(args):
    """Handle the extract command."""
    processor = PDFProcessor(output_dir=args.output_dir)
    
    try:
        # Extract PDF metadata
        metadata = processor.extract_pdf_metadata(args.pdf_file)
        print(f"Processing PDF: {metadata.title or 'Untitled'}")
        print(f"Author: {metadata.author}")
        print(f"Pages: {metadata.page_count}")
        
        # Extract slide content
        slides = processor.extract_slide_content(
            pdf_path=args.pdf_file,
            extract_images=not args.no_images,
            convert_to_images=not args.no_slide_images,
            dpi=args.dpi
        )
        
        # Save extracted text
        if args.save_text:
            processor.save_extracted_text(slides, "extracted_slides.txt")
        
        # Get extraction summary
        summary = processor.get_extraction_summary(slides)
        print(f"\nExtraction Summary:")
        print(f"- Total slides: {summary['total_slides']}")
        print(f"- Total text length: {summary['total_text_length']:,} characters")
        print(f"- Total images: {summary['total_images']}")
        print(f"- Slides with text: {summary['slides_with_text']}")
        print(f"- Slides with images: {summary['slides_with_images']}")
        
        # Save results as JSON if requested
        if args.json_output:
            output_data = {
                'metadata': metadata.__dict__,
                'summary': summary,
                'slides': [
                    {
                        'page_number': slide.page_number,
                        'text': slide.text,
                        'image_count': len(slide.images),
                        'metadata': slide.metadata
                    }
                    for slide in slides
                ]
            }
            
            json_path = Path(args.output_dir) / "extraction_results.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            print(f"Results saved to: {json_path}")
        
        print(f"\nOutput saved to: {args.output_dir}")
        
    except Exception as e:
        logging.error(f"Error processing PDF: {e}")
        sys.exit(1)

def parse_command(args):
    """Handle the parse command."""
    processor = PDFProcessor(output_dir=args.output_dir)
    parser = SlideParser()
    
    try:
        # Extract slides first
        print("Extracting PDF content...")
        slides = processor.extract_slide_content(
            pdf_path=args.pdf_file,
            extract_images=False,  # Focus on text parsing
            convert_to_images=False,
            dpi=args.dpi
        )
        
        # Parse slides
        print("Parsing slide structure...")
        parsed_slides = parser.parse_slides(slides)
        
        # Analyze presentation structure
        structure = parser.analyze_presentation_structure(parsed_slides)
        
        # Generate summary
        summary = parser.generate_presentation_summary(structure)
        print(f"\n{summary}")
        
        # Detailed slide analysis
        if args.detailed:
            print(f"\nDetailed Slide Analysis:")
            print("=" * 50)
            
            for slide in parsed_slides:
                print(f"\nSlide {slide.page_number} ({slide.slide_type}):")
                print(f"Importance Score: {slide.importance_score:.2f}")
                
                if slide.title:
                    print(f"Title: {slide.title}")
                
                if slide.bullet_points:
                    print(f"Bullet Points ({len(slide.bullet_points)}):")
                    for bp in slide.bullet_points[:3]:  # Show first 3
                        print(f"  • {bp}")
                    if len(slide.bullet_points) > 3:
                        print(f"  ... and {len(slide.bullet_points) - 3} more")
                
                if slide.keywords:
                    print(f"Keywords: {', '.join(slide.keywords[:10])}")
                
                print("-" * 30)
        
        # Save parsing results
        if args.json_output:
            output_data = {
                'presentation_summary': summary,
                'structure': {
                    'title_slide': structure.title_slide.__dict__ if structure.title_slide else None,
                    'total_slides': structure.total_slides,
                    'main_topics': structure.main_topics,
                    'keyword_frequency': structure.keyword_frequency
                },
                'parsed_slides': [
                    {
                        'page_number': slide.page_number,
                        'title': slide.title,
                        'slide_type': slide.slide_type,
                        'importance_score': slide.importance_score,
                        'bullet_points': slide.bullet_points,
                        'keywords': slide.keywords,
                        'text_length': len(slide.raw_content.text)
                    }
                    for slide in parsed_slides
                ]
            }
            
            json_path = Path(args.output_dir) / "parsing_results.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            print(f"\nParsing results saved to: {json_path}")
        
    except Exception as e:
        logging.error(f"Error parsing PDF: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Extract and parse slides from PDF presentations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract all content from a PDF
  python -m pdf_extractor extract presentation.pdf

  # Extract without images to save space
  python -m pdf_extractor extract presentation.pdf --no-images --no-slide-images

  # Parse slide structure and content
  python -m pdf_extractor parse presentation.pdf --detailed

  # Extract with custom output directory and DPI
  python -m pdf_extractor extract presentation.pdf -o output --dpi 200
        """
    )
    
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose logging')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract content from PDF slides')
    extract_parser.add_argument('pdf_file', help='Path to PDF file')
    extract_parser.add_argument('-o', '--output-dir', default='pdf_output',
                               help='Output directory (default: pdf_output)')
    extract_parser.add_argument('--no-images', action='store_true',
                               help='Skip extracting embedded images')
    extract_parser.add_argument('--no-slide-images', action='store_true',
                               help='Skip converting slides to images')
    extract_parser.add_argument('--dpi', type=int, default=300,
                               help='DPI for slide image conversion (default: 300)')
    extract_parser.add_argument('--save-text', action='store_true',
                               help='Save extracted text to file')
    extract_parser.add_argument('--json-output', action='store_true',
                               help='Save results as JSON')
    extract_parser.set_defaults(func=extract_command)
    
    # Parse command
    parse_parser = subparsers.add_parser('parse', help='Parse and analyze slide structure')
    parse_parser.add_argument('pdf_file', help='Path to PDF file')
    parse_parser.add_argument('-o', '--output-dir', default='pdf_output',
                             help='Output directory (default: pdf_output)')
    parse_parser.add_argument('--detailed', action='store_true',
                             help='Show detailed analysis of each slide')
    parse_parser.add_argument('--json-output', action='store_true',
                             help='Save parsing results as JSON')
    parse_parser.add_argument('--dpi', type=int, default=150,
                             help='DPI for any image conversion (default: 150)')
    parse_parser.set_defaults(func=parse_command)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    setup_logging(args.verbose)
    args.func(args)

if __name__ == '__main__':
    main() 