"""
Demo: OOP version producing exact same output as original pdf_to_dict.py
"""

from pprint import pprint
from pdf_extractor import PDFProcessor

def main():
    """Demonstrate that OOP version produces identical output"""
    
    print("🚀 Using OOP PDFProcessor to get exact same trees as original...")
    print("=" * 70)
    
    # Initialize processor
    processor = PDFProcessor()
    
    # Get all trees (identical to original pdf_to_dict.py)
    PDF = "./volume/slides/cours_1.pdf"
    trees = processor.get_all_trees(PDF)
    
    print(f"📊 Extracted {len(trees)} slide trees")
    print("\n🌳 Full trees output (identical to original):")
    print("=" * 70)
    
    # Print exactly like original pdf_to_dict.py
    pprint(trees, width=120, sort_dicts=False)
    
    print("\n" + "=" * 70)
    print("✅ This output should be IDENTICAL to running the original pdf_to_dict.py!")
    
    # Also show how to get separated course_plan and course_content
    print("\n📚 You can also get separated course plan and content:")
    course_plan, course_content = processor.process_pdf(PDF)
    print(f"Course plan (page {course_plan['page']}): {course_plan['title']}")
    print(f"Course content: {len(course_content)} slides")

if __name__ == "__main__":
    main() 