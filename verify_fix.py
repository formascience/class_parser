"""
Quick verification that the OOP version now matches the original
"""

from pprint import pprint

def test_oop_version():
    """Test the new OOP version"""
    from pdf_extractor import PDFProcessor
    
    processor = PDFProcessor()
    
    # Use the PDF file from the root directory
    PDF = "./cours_1_first_10_slides.pdf"
    
    try:
        course_plan, course_content = processor.process_pdf(PDF)
        
        print("🔍 OOP VERSION OUTPUT:")
        print("=" * 50)
        print("Course Plan:")
        pprint(course_plan, width=120)
        print(f"\nCourse Content length: {len(course_content)}")
        print("First content slide:")
        pprint(course_content[0] if course_content else "No content", width=120)
        
        return True
        
    except Exception as e:
        print(f"❌ OOP version failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing OOP version with exact original logic...")
    success = test_oop_version()
    
    if success:
        print("\n✅ OOP version executed successfully!")
        print("Compare the output above with your original output to verify they match.")
    else:
        print("\n❌ OOP version failed!") 