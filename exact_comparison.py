"""
Exact comparison between original pdf_to_dict.py and OOP version
Compares the full trees list before any separation
"""

from pprint import pprint

def get_original_trees():
    """Get trees using original pdf_to_dict.py logic"""
    from pdf_to_dict import extract_lines, split_bullets, bullet_tree
    
    # Use the same PDF path as original
    PDF = "./volume/slides/cours_1.pdf"
    
    # Exact original flow
    deck = extract_lines(PDF)
    slides = split_bullets(deck)
    trees = [bullet_tree(sl) for sl in slides]
    
    return trees

def get_oop_trees():
    """Get trees using new OOP PDFProcessor"""
    from pdf_extractor import PDFProcessor
    
    processor = PDFProcessor()
    
    # Use the same PDF path as original
    PDF = "./volume/slides/cours_1.pdf"
    
    # Get all trees (before separation)
    trees = processor.get_all_trees(PDF)
    
    return trees

def compare_trees():
    """Compare the two outputs"""
    print("🔍 Getting original trees...")
    try:
        original_trees = get_original_trees()
        print(f"✅ Original: {len(original_trees)} trees extracted")
    except Exception as e:
        print(f"❌ Original failed: {e}")
        return
    
    print("\n🔍 Getting OOP trees...")
    try:
        oop_trees = get_oop_trees()
        print(f"✅ OOP: {len(oop_trees)} trees extracted")
    except Exception as e:
        print(f"❌ OOP failed: {e}")
        return
    
    # Compare lengths
    if len(original_trees) != len(oop_trees):
        print(f"❌ Length mismatch: Original={len(original_trees)}, OOP={len(oop_trees)}")
        return
    
    # Compare each tree
    all_match = True
    for i, (orig, oop) in enumerate(zip(original_trees, oop_trees)):
        if orig != oop:
            print(f"❌ Tree {i} differs!")
            print("Original:")
            pprint(orig, width=120)
            print("\nOOP:")
            pprint(oop, width=120)
            all_match = False
            break
    
    if all_match:
        print("✅ 🎉 PERFECT MATCH! All trees are identical!")
        print("\nFirst tree:")
        pprint(original_trees[0], width=120)
    else:
        print("❌ Trees differ")

if __name__ == "__main__":
    print("🚀 Comparing exact trees output...")
    print("=" * 50)
    compare_trees() 