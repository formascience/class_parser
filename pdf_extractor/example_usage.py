"""Example usage of the PDF extractor module."""

from pdf_extractor import PDFProcessor, SlideParser

def extract_and_parse_example():
    """Example of extracting and parsing PDF slides."""
    
    # Initialize processor and parser
    processor = PDFProcessor(output_dir="example_output")
    parser = SlideParser()
    
    # Path to your PDF file
    pdf_path = "example_presentation.pdf"
    
    try:
        # Extract PDF metadata
        print("Extracting PDF metadata...")
        metadata = processor.extract_pdf_metadata(pdf_path)
        print(f"Title: {metadata.title}")
        print(f"Author: {metadata.author}")
        print(f"Pages: {metadata.page_count}")
        
        # Extract slide content
        print("\nExtracting slide content...")
        slides = processor.extract_slide_content(
            pdf_path=pdf_path,
            extract_images=True,
            convert_to_images=True,
            dpi=300
        )
        
        # Get extraction summary
        summary = processor.get_extraction_summary(slides)
        print(f"\nExtraction Summary:")
        print(f"- Total slides: {summary['total_slides']}")
        print(f"- Total text: {summary['total_text_length']:,} characters")
        print(f"- Total images: {summary['total_images']}")
        
        # Parse slides
        print("\nParsing slide structure...")
        parsed_slides = parser.parse_slides(slides)
        
        # Analyze presentation structure
        structure = parser.analyze_presentation_structure(parsed_slides)
        
        # Generate summary
        presentation_summary = parser.generate_presentation_summary(structure)
        print(f"\n{presentation_summary}")
        
        # Show detailed analysis for top 3 most important slides
        print("\nTop 3 Most Important Slides:")
        print("=" * 40)
        
        top_slides = sorted(parsed_slides, key=lambda x: x.importance_score, reverse=True)[:3]
        
        for slide in top_slides:
            print(f"\nSlide {slide.page_number} - {slide.slide_type.upper()}")
            print(f"Importance Score: {slide.importance_score:.2f}")
            
            if slide.title:
                print(f"Title: {slide.title}")
            
            if slide.bullet_points:
                print(f"Bullet Points:")
                for bp in slide.bullet_points[:3]:
                    print(f"  • {bp}")
            
            if slide.keywords:
                print(f"Keywords: {', '.join(slide.keywords[:5])}")
            
            print("-" * 30)
        
        # Save extracted text
        processor.save_extracted_text(slides, "extracted_presentation.txt")
        print(f"\nExtracted text saved to: example_output/text/extracted_presentation.txt")
        
    except FileNotFoundError:
        print(f"PDF file not found: {pdf_path}")
        print("Please place a PDF file named 'example_presentation.pdf' in the current directory")
    except Exception as e:
        print(f"Error processing PDF: {e}")

def simple_text_extraction_example():
    """Simple example of just extracting text from PDF."""
    
    processor = PDFProcessor(output_dir="simple_output")
    pdf_path = "example_presentation.pdf"
    
    try:
        # Extract only text content (no images)
        slides = processor.extract_slide_content(
            pdf_path=pdf_path,
            extract_images=False,
            convert_to_images=False
        )
        
        # Print text from each slide
        for slide in slides:
            print(f"=== SLIDE {slide.page_number} ===")
            print(slide.text)
            print("\n" + "-" * 50 + "\n")
            
    except FileNotFoundError:
        print(f"PDF file not found: {pdf_path}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("PDF Extractor Example Usage")
    print("==========================")
    
    # Run the full extraction and parsing example
    extract_and_parse_example()
    
    print("\n" + "="*50 + "\n")
    
    # Run simple text extraction
    print("Simple Text Extraction:")
    simple_text_extraction_example() 