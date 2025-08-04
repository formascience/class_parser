#!/usr/bin/env python3
"""
Debug script for identifying and fixing fragmented text extraction from PDFs.

Usage:
    python debug_fragmented_text.py path/to/your.pdf [page_number]
"""

import sys
from pdf_extractor import PDFProcessor
from pprint import pprint

def debug_pdf_text_extraction(pdf_path: str, page_num: int = 1):
    """Debug text extraction for a specific page"""
    processor = PDFProcessor()
    
    print(f"🔍 Debugging PDF text extraction for: {pdf_path}")
    print(f"📄 Analyzing page {page_num}")
    print("=" * 60)
    
    # Get debug information
    debug_info = processor.debug_text_extraction(pdf_path, page_num)
    
    if "error" in debug_info:
        print(f"❌ Error: {debug_info['error']}")
        return
    
    # Print summary
    print(f"📊 EXTRACTION SUMMARY:")
    print(f"   Total words extracted: {debug_info['total_words']}")
    print(f"   Single character words: {debug_info['single_char_words']}")
    print(f"   Multi character words: {debug_info['multi_char_words']}")
    print(f"   Fragmentation ratio: {debug_info['fragmentation_ratio']:.2%}")
    
    if debug_info['fragmentation_ratio'] > 0.3:
        print(f"⚠️  HIGH FRAGMENTATION DETECTED!")
    else:
        print(f"✅ Fragmentation level is acceptable")
    
    print(f"\n🔤 SAMPLE CHARACTERS:")
    print(f"   Single chars: {debug_info['sample_single_chars']}")
    print(f"   Multi chars: {debug_info['sample_multi_chars'][:5]}")
    
    # Show problematic rows
    fragmented_rows = [row for row in debug_info['rows'] if row['is_fragmented']]
    if fragmented_rows:
        print(f"\n🚨 FRAGMENTED ROWS FOUND ({len(fragmented_rows)} rows):")
        for i, row in enumerate(fragmented_rows[:3]):  # Show first 3
            print(f"\n   Row {i+1} (y={row['y_position']}):")
            print(f"   Raw:     '{row['raw_text'][:100]}...'")
            print(f"   Cleaned: '{row['cleaned_text'][:100]}...'")
    
    return debug_info

def test_full_extraction(pdf_path: str):
    """Test the full extraction pipeline with cleaning"""
    processor = PDFProcessor()
    
    print(f"\n🧪 TESTING FULL EXTRACTION WITH CLEANING")
    print("=" * 60)
    
    try:
        # Get all trees with the new cleaning
        trees = processor.get_all_trees(pdf_path)
        
        print(f"📄 Extracted {len(trees)} slides")
        
        # Show first few slides
        for i, tree in enumerate(trees[:3]):
            print(f"\n📄 Slide {tree['page']}: '{tree['title'][:50]}...'")
            
            # Show tree structure (first few items)
            for j, item in enumerate(tree['tree'][:2]):
                print(f"   • {item['text'][:80]}...")
                if item['children']:
                    for k, child in enumerate(item['children'][:2]):
                        print(f"     ◦ {child['text'][:60]}...")
                        if k >= 1:
                            break
                if j >= 1:
                    break
        
        return trees
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_fragmented_text.py <pdf_path> [page_number]")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    page_num = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    
    try:
        # Debug specific page
        debug_info = debug_pdf_text_extraction(pdf_path, page_num)
        
        # Test full extraction
        trees = test_full_extraction(pdf_path)
        
        # If high fragmentation was detected, show recommendations
        if debug_info and debug_info.get('fragmentation_ratio', 0) > 0.3:
            print(f"\n💡 RECOMMENDATIONS:")
            print(f"   1. The PDF has significant text fragmentation")
            print(f"   2. The new cleaning methods should help merge fragmented text")
            print(f"   3. Check the 'Cleaned' versions in the output above")
            print(f"   4. If issues persist, the PDF may need manual preprocessing")
        
    except FileNotFoundError:
        print(f"❌ File not found: {pdf_path}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 