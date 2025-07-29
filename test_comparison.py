"""
Test script to compare outputs between original and OOP versions
"""

import json
from pprint import pprint

# Original approach (from pdf_to_dict.py)
def original_approach():
    """Run the original PDF processing logic"""
    import sys
    import os
    sys.path.append('.')
    
    # Import the original functions
    from pdf_to_dict import extract_lines, split_bullets, bullet_tree
    
    PDF = "./cours_1_first_10_slides.pdf"  # Using the PDF in root directory
    
    if not os.path.exists(PDF):
        print(f"❌ PDF not found: {PDF}")
        return None, None
    
    deck = extract_lines(PDF)
    slides = split_bullets(deck)
    trees = [bullet_tree(sl) for sl in slides]
    
    # Original logic
    course_plan = trees[1]
    trees.pop(1)  # Remove page 1 (course plan)
    course_content = trees
    
    return course_plan, course_content

# New OOP approach
def oop_approach():
    """Run the new OOP PDF processing logic"""
    from pdf_extractor import PDFProcessor
    
    processor = PDFProcessor()
    PDF = "./cours_1_first_10_slides.pdf"
    
    try:
        course_plan, course_content = processor.process_pdf(PDF)
        return course_plan, course_content
    except Exception as e:
        print(f"❌ OOP approach failed: {e}")
        return None, None

def compare_outputs():
    """Compare the outputs of both approaches"""
    print("🔍 Comparing outputs...")
    
    # Get outputs from both approaches
    orig_plan, orig_content = original_approach()
    oop_plan, oop_content = oop_approach()
    
    if orig_plan is None or oop_plan is None:
        print("❌ One or both approaches failed")
        return
    
    # Compare course plans
    print("\n📋 COURSE PLAN COMPARISON:")
    print("=" * 50)
    
    plan_match = orig_plan == oop_plan
    print(f"Course plans match: {'✅ YES' if plan_match else '❌ NO'}")
    
    if not plan_match:
        print("\nOriginal course plan:")
        pprint(orig_plan, width=120)
        print("\nOOP course plan:")
        pprint(oop_plan, width=120)
    
    # Compare course content
    print("\n📚 COURSE CONTENT COMPARISON:")
    print("=" * 50)
    
    content_match = orig_content == oop_content
    print(f"Course content match: {'✅ YES' if content_match else '❌ NO'}")
    print(f"Original content length: {len(orig_content)}")
    print(f"OOP content length: {len(oop_content)}")
    
    if not content_match:
        print("\nFirst difference found:")
        for i, (orig, oop) in enumerate(zip(orig_content, oop_content)):
            if orig != oop:
                print(f"Difference at index {i}:")
                print("Original:", orig)
                print("OOP:", oop)
                break
    
    # Overall result
    overall_match = plan_match and content_match
    print(f"\n🎯 OVERALL RESULT: {'✅ PERFECT MATCH' if overall_match else '❌ DIFFERENCES FOUND'}")

if __name__ == "__main__":
    compare_outputs() 