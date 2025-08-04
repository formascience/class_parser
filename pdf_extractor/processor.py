"""
PDF text extraction and tree structure processing
"""

import os
import re
import pdfplumber
from typing import List, Dict, Tuple, Optional


class PDFProcessor:
    """Handles PDF text extraction and conversion to hierarchical tree structure"""
    
    #region __init__
    def __init__(self, indent_tolerance: int = 5, max_tree_depth: int = 3, 
                 enable_fragmentation_filtering: bool = True,
                 fragmentation_threshold: float = 0.7,
                 skip_pages: List[int] = None,
                 delete_fragmented_pages: bool = True):
        self.bullet_chars = "•◦‣▪–"
        self.banner_regex = re.compile(r"^L\\d?SpS:")
        self.indent_tolerance = indent_tolerance
        self.max_tree_depth = max_tree_depth
        self.enable_fragmentation_filtering = enable_fragmentation_filtering
        self.fragmentation_threshold = fragmentation_threshold
        self.skip_pages = skip_pages or []
        self.delete_fragmented_pages = delete_fragmented_pages
    #endregion
    
    #region get_all_trees
    def get_all_trees(self, pdf_path: str) -> List[dict]:
        """
        Get all slide trees exactly like original pdf_to_dict.py - for comparison
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of all slide trees (before any separation)
        """
        deck = self._extract_lines(pdf_path)
        slides = self._split_bullets(deck)
        trees = [self._create_bullet_tree(slide, self.max_tree_depth) for slide in slides]
        return trees
    #endregion


    def process_pdf(self, pdf_path: str, specified_plan_slide: Optional[int] = None) -> Tuple[Optional[dict], List[dict]]:
        """
        Process PDF with STRICT plan detection - no automatic derivation
        
        Args:
            pdf_path: Path to the PDF file
            specified_plan_slide: Optional slide number (1-based) to use as plan slide
            
        Returns:
            Tuple of (course_plan, course_content) where:
            - course_plan: Explicit plan slide or None if not found
            - course_content: All slides (or all except plan if plan found)
        """
        trees = self.get_all_trees(pdf_path)
        course_plan, found_explicit = self.extract_course_plan(pdf_path, specified_plan_slide)
        
        if found_explicit and course_plan:
            # Remove plan slide from content
            plan_page = course_plan.get('page', -1)
            course_content = [tree for tree in trees if tree.get('page') != plan_page]
        else:
            # No plan found - return all slides as content
            course_content = trees
        
        return course_plan, course_content

    def analyze_pdf_structure(self, pdf_path: str, specified_plan_slide: Optional[int] = None) -> dict:
        """
        Analyze PDF structure and provide detailed information about plan detection
        
        Args:
            pdf_path: Path to the PDF file
            specified_plan_slide: Optional slide number (1-based) to use as plan slide
            
        Returns:
            Dictionary with detailed analysis of the PDF structure and plan detection
        """
        trees = self.get_all_trees(pdf_path)
        course_plan, found_explicit = self.extract_course_plan(pdf_path, specified_plan_slide)
        course_content, plan_info = self.get_course_content_without_plan(pdf_path, specified_plan_slide)
        
        # Analyze slide titles for plan indicators
        plan_candidates = []
        for tree in trees:
            title = tree.get('title', '').lower()
            page = tree.get('page', 0)
            plan_keywords = ['plan', 'agenda', 'sommaire', 'table des matières']
            
            has_plan_keyword = any(keyword in title for keyword in plan_keywords)
            has_nested_structure = False  # Removed automatic structure analysis
            has_multiple_items = len(tree.get('tree', [])) >= 3
            
            plan_candidates.append({
                'page': page,
                'title': tree.get('title', ''),
                'has_plan_keyword': has_plan_keyword,
                'has_nested_structure': has_nested_structure,
                'has_multiple_items': has_multiple_items,
                'plan_score': sum([has_plan_keyword, has_nested_structure, has_multiple_items])
            })
        
        return {
            'total_slides': len(trees),
            'found_explicit_plan': found_explicit,
            'plan_slide_page': course_plan.get('page') if found_explicit and course_plan else None,
            'plan_title': course_plan.get('title', '') if course_plan else '',
            'content_slides_count': len(course_content),
            'plan_detection_method': plan_info['detection_method'],
            'plan_candidates': sorted(plan_candidates, key=lambda x: x['plan_score'], reverse=True),
            'slides_overview': [
                {
                    'page': tree.get('page'),
                    'title': tree.get('title', ''),
                    'tree_items_count': len(tree.get('tree', []))
                }
                for tree in trees
            ]
        }
    #endregion
    
    #region process_course_plan_pdf
    def process_course_plan_pdf(self, pdf_path: str) -> dict:
        """
        Process PDF that contains only course plan content
        
        Args:
            pdf_path: Path to the PDF file containing only course plan
            
        Returns:
            Course plan tree structure
        """
        trees = self.get_all_trees(pdf_path)
        
        if not trees:
            return {"page": 1, "title": "", "tree": []}
        
        # If single page, return that page as course plan
        if len(trees) == 1:
            return trees[0]
        
        # If multiple pages, combine them into a single course plan structure
        # Take title from first page and combine all trees
        combined_tree = []
        first_title = trees[0]["title"] if trees else ""
        
        for tree in trees:
            combined_tree.extend(tree["tree"])
        
        return {
            "page": 1,
            "title": first_title,
            "tree": combined_tree
        }
    
    def extract_course_plan(self, pdf_path: str, specified_plan_slide: Optional[int] = None) -> Tuple[Optional[dict], bool]:
        """
        STRICT extraction of explicit course plan slides only
        
        Only considers slides with BIG FONT headers containing plan keywords
        AND located within the first 10 slides.
        OR uses user-specified slide number if provided.
        No fallbacks, no derivation - let the LLM handle plan creation.
        
        Args:
            pdf_path: Path to the PDF file
            specified_plan_slide: Optional slide number (1-based) to use as plan slide
            
        Returns:
            Tuple of (course_plan, found_explicit_plan) where:
            - course_plan: The explicit plan slide or None if not found
            - found_explicit_plan: True if plan found (auto-detected or user-specified)
        """
        trees = self.get_all_trees(pdf_path)
        
        if not trees:
            return None, False
        
        # If user specified a plan slide, use that directly
        if specified_plan_slide is not None:
            for tree in trees:
                if tree.get('page') == specified_plan_slide:
                    return tree, True
            # Specified slide not found
            return None, False
        
        # STRICT: Only find slides with big font headers containing plan keywords IN FIRST 10 SLIDES
        plan_keywords = ['plan', 'agenda', 'outline', 'sommaire', 'table', 'contenu', 'table des matières']
        max_plan_slide = 10  # Plan must be in first 10 slides
        
        with pdfplumber.open(pdf_path) as pdf:
            for idx, page in enumerate(pdf.pages, 1):
                # STRICT: Skip if beyond first 10 slides
                if idx > max_plan_slide:
                    break
                    
                words = page.extract_words(use_text_flow=True, extra_attrs=["size"])
                
                if not words:
                    continue
                    
                # Find the biggest font size on the page (title)
                max_size = max(w["size"] for w in words)
                
                # Get the title text (biggest font words)
                title_words = sorted([w for w in words if abs(w["size"] - max_size) < 0.5], 
                                    key=lambda w: w["x0"])
                title_text = " ".join(w["text"] for w in title_words).lower()
                
                # STRICT CHECK: Title must contain plan keywords AND be in big font AND in first 10 slides
                if any(keyword in title_text for keyword in plan_keywords):
                    # Find corresponding tree for this page
                    for tree in trees:
                        if tree.get('page') == idx:
                            return tree, True
        
        # No explicit plan slide found in first 10 slides
        return None, False
    #endregion
    
    #region check_plan_detection_details
    def check_plan_detection_details(self, pdf_path: str) -> dict:
        """
        Get detailed information about plan detection process for debugging
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with detailed plan detection information
        """
        plan_keywords = ['plan', 'agenda', 'outline', 'sommaire', 'table', 'contenu', 'table des matières']
        detection_details = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for idx, page in enumerate(pdf.pages, 1):
                words = page.extract_words(use_text_flow=True, extra_attrs=["size"])
                
                if not words:
                    detection_details.append({
                        'page': idx,
                        'has_words': False,
                        'title_text': '',
                        'max_font_size': 0,
                        'contains_keywords': False,
                        'found_keywords': []
                    })
                    continue
                    
                # Find the biggest font size on the page (title)
                max_size = max(w["size"] for w in words)
                
                # Get the title text (biggest font words)
                title_words = sorted([w for w in words if abs(w["size"] - max_size) < 0.5], 
                                    key=lambda w: w["x0"])
                title_text = " ".join(w["text"] for w in title_words)
                title_lower = title_text.lower()
                
                # Check for keywords
                found_keywords = [kw for kw in plan_keywords if kw in title_lower]
                contains_keywords = len(found_keywords) > 0
                
                detection_details.append({
                    'page': idx,
                    'has_words': True,
                    'title_text': title_text,
                    'max_font_size': max_size,
                    'contains_keywords': contains_keywords,
                    'found_keywords': found_keywords
                })
        
        return {
            'plan_keywords_searched': plan_keywords,
            'detection_method': 'strict_big_font_keywords_only',
            'pages_analyzed': len(detection_details),
            'page_details': detection_details
        }
    #endregion
    
    
    def get_course_content_without_plan(self, pdf_path: str, specified_plan_slide: Optional[int] = None) -> Tuple[List[dict], dict]:
        """
        Get course content slides with STRICT plan detection info
        
        Args:
            pdf_path: Path to the PDF file
            specified_plan_slide: Optional slide number (1-based) to use as plan slide
            
        Returns:
            Tuple of (course_content, plan_info) where plan_info includes strict detection results
        """
        trees = self.get_all_trees(pdf_path)
        course_plan, found_explicit = self.extract_course_plan(pdf_path, specified_plan_slide)
        
        if found_explicit and course_plan:
            plan_slide_page = course_plan.get('page', -1)
            course_content = [tree for tree in trees if tree.get('page') != plan_slide_page]
        else:
            course_content = trees
            plan_slide_page = None
        
        # Determine detection method
        if specified_plan_slide is not None:
            detection_method = 'user_specified' if found_explicit else 'user_specified_not_found'
        else:
            detection_method = 'strict_big_font_keywords' if found_explicit else 'none_found'
        
        plan_info = {
            'plan': course_plan,
            'found_explicit_plan': found_explicit,
            'plan_slide_page': plan_slide_page,
            'detection_method': detection_method,
            'specified_slide': specified_plan_slide
        }
        
        return course_content, plan_info
    
    def extract_plan_from_specified_slide(self, pdf_path: str, slide_number: int) -> Tuple[Optional[dict], str]:
        """
        Extract plan from a user-specified slide with validation and feedback
        
        Args:
            pdf_path: Path to the PDF file
            slide_number: Slide number (1-based) to use as plan slide
            
        Returns:
            Tuple of (course_plan, status_message) where:
            - course_plan: The plan slide data or None if not found
            - status_message: Human-readable status message
        """
        trees = self.get_all_trees(pdf_path)
        
        if not trees:
            return None, f"PDF has no slides"
        
        if slide_number < 1 or slide_number > len(trees):
            return None, f"Slide {slide_number} does not exist. PDF has {len(trees)} slides."
        
        # Find the specified slide
        for tree in trees:
            if tree.get('page') == slide_number:
                slide_title = tree.get('title', 'Untitled Slide')
                return tree, f"✅ Using slide {slide_number} as plan: '{slide_title}'"
        
        return None, f"❌ Slide {slide_number} not found in processed slides"
    
    def set_max_tree_depth(self, max_depth: int) -> None:
        """
        Set maximum tree depth for bullet point nesting
        
        Args:
            max_depth: Maximum allowed depth (1-based). Default is 3.
                      1 = only top level, 2 = two levels, 3 = three levels, etc.
        """
        if max_depth < 1:
            raise ValueError("max_depth must be at least 1")
        self.max_tree_depth = max_depth
        print(f"📊 Tree depth limit set to {max_depth} levels")
    
    def set_skip_pages(self, pages: List[int]) -> None:
        """
        Set pages to skip during extraction
        
        Args:
            pages: List of page numbers (1-based) to skip
        """
        self.skip_pages = pages
        print(f"🚫 Will skip pages: {pages}")
    
    def set_fragmentation_filtering(self, enabled: bool, threshold: float = 0.7) -> None:
        """
        Configure fragmentation filtering
        
        Args:
            enabled: Whether to enable fragmentation filtering
            threshold: Fragmentation ratio threshold (0.0 to 1.0)
        """
        self.enable_fragmentation_filtering = enabled
        self.fragmentation_threshold = threshold
        print(f"🔧 Fragmentation filtering: {'enabled' if enabled else 'disabled'}")
        if enabled:
            print(f"   Threshold: {threshold:.1%}")
    
    def set_fragmented_page_handling(self, delete_immediately: bool = True) -> None:
        """
        Configure how fragmented pages are handled
        
        Args:
            delete_immediately: If True, delete fragmented pages. If False, try to reconstruct them.
        """
        self.delete_fragmented_pages = delete_immediately
        action = "DELETE immediately" if delete_immediately else "try to RECONSTRUCT"
        print(f"🗑️  Fragmented pages will be: {action}")
    
    def get_tree_depth_info(self) -> dict:
        """
        Get information about current tree depth settings
        
        Returns:
            Dictionary with depth configuration info
        """
        return {
            'max_tree_depth': self.max_tree_depth,
            'indent_tolerance': self.indent_tolerance,
            'description': f"Trees limited to {self.max_tree_depth} levels of nesting"
        }
    
    def _extract_lines(self, pdf_path: str) -> List[dict]:
        """Extract lines from PDF pages with banner filtering and fragmentation cleanup"""
        deck = []
        banner_hits = {}

        with pdfplumber.open(pdf_path) as pdf:
            for idx, page in enumerate(pdf.pages, 1):
                # Skip manually specified pages
                if idx in self.skip_pages:
                    print(f"⏭️  Skipping page {idx} (manually specified)")
                    continue
                    
                words = page.extract_words(use_text_flow=True, extra_attrs=["size"])
                rows: Dict[float, List[dict]] = {}
                
                for word in words:
                    text = word["text"].strip()
                    if self.banner_regex.match(text):
                        banner_hits[text] = banner_hits.get(text, 0) + 1
                        continue
                    
                    y = round(word["top"], 1)
                    rows.setdefault(y, []).append(word)

                lines = []
                for y in sorted(rows):
                    row_words = sorted(rows[y], key=lambda w: w["x0"])
                    
                    # Try to merge fragmented words first
                    merged_words = self._merge_fragmented_words(row_words)
                    
                    x0 = merged_words[0]["x0"]
                    text = " ".join(w["text"] for w in merged_words)
                    
                    # Clean fragmented text
                    text = self._clean_fragmented_text(text)
                    text = re.sub(rf"\s*{idx}\s*$", "", text).strip()
                    
                    if text:
                        lines.append((x0, text, merged_words))

                deck.append({
                    "page": idx,
                    "title": self._extract_slide_title(words),
                    "lines": lines
                })

        # Filter out banner texts that appear on most pages
        banner_texts = {text for text, count in banner_hits.items() 
                       if count / len(deck) >= 0.8}
        
        for slide in deck:
            slide["lines"] = [(x, t, rw) for x, t, rw in slide["lines"] 
                             if t not in banner_texts]

        # NEW: Filter out heavily fragmented pages (if enabled)
        if self.enable_fragmentation_filtering:
            print(f"📄 Extracted {len(deck)} pages, checking for fragmentation...")
            filtered_deck = self._filter_fragmented_pages(
                deck, 
                self.fragmentation_threshold,
                min_meaningful_lines=5,
                delete_fragmented=self.delete_fragmented_pages
            )
            print(f"✅ Keeping {len(filtered_deck)} pages after fragmentation filtering")
            return filtered_deck
        else:
            return deck
    #endregion
    
    #region _extract_slide_title
    def _extract_slide_title(self, words: List[dict], top_cutoff: int = 150, use_biggest_font: int = 1) -> str:
        """Extract slide title - EXACT original logic"""
        if not words: 
            return ""
        
        # If flag is 1, find the biggest font string from all words
        if use_biggest_font == 1:
            max_size = max(w["size"] for w in words)
            biggest_font_words = sorted([w for w in words 
                                       if abs(w["size"] - max_size) < 0.5],
                                      key=lambda w: w["x0"])
            title_text = " ".join(w["text"] for w in biggest_font_words)
            return self._clean_fragmented_text(title_text)
        
        # Original logic for when flag is not 1
        top_words = [w for w in words if w["top"] < top_cutoff]
        if not top_words: 
            return ""
        max_size = max(w["size"] for w in top_words)
        title_words = sorted([w for w in top_words
                              if abs(w["size"] - max_size) < 0.5],
                             key=lambda w: w["x0"])
        title_text = " ".join(w["text"] for w in title_words)
        return self._clean_fragmented_text(title_text)
    #endregion
    
    #region _first_bullet_x
    def _first_bullet_x(self, row_words: List[dict]) -> Optional[float]:
        """Find x-position of first bullet character in row - EXACT original"""
        for w in row_words:
            if any(c in w["text"] for c in self.bullet_chars):
                return w["x0"]
        return None
    #endregion
    
    #region _explode_line
    def _explode_line(self, x0: float, line: str, row_words: List[dict], page_idx: int) -> List[dict]:
        """
        If the row is "Parent • child • child", use x‑pos of the first bullet
        glyph for all children so that INTRO and "Le génome humain" share the
        SAME indent. - EXACT original
        """
        line = re.sub(rf"\s*{page_idx}\s*$", "", line).strip()
        if "•" not in line:
            return [{"indent": x0, "text": line}]

        head, tail = line.split("•", 1)
        head = head.strip()
        out = []

        # parent node (if any)
        if head:
            out.append({"indent": x0, "text": head})

        bullet_x = self._first_bullet_x(row_words) or x0
        children = [frag.strip() for frag in tail.split("•") if frag.strip()]
        out.extend({"indent": bullet_x, "text": c} for c in children)
        return out
    #endregion
    
    #region _split_bullets
    def _split_bullets(self, deck: List[dict]) -> List[dict]:
        """Convert deck lines to individual bullet items - EXACT original"""
        slides = []
        for sl in deck:
            bullets = []
            for x, txt, row in sl["lines"]:
                bullets.extend(self._explode_line(x, txt, row, sl["page"]))
            slides.append({"page": sl["page"], "title": sl["title"], "bullets": bullets})
        return slides
    #endregion
    
    #region _create_bullet_tree
    def _create_bullet_tree(self, slide: dict, max_depth: int = 3) -> dict:
        """Convert flat bullet list to nested tree structure with depth limit"""
        bullets = slide["bullets"]
        if not bullets:
            return {"page": slide["page"], "title": slide["title"], "tree": []}

        indents = sorted({b["indent"] for b in bullets})
        # cluster indents - EXACT original logic
        groups, cur = [], [indents[0]]
        for x in indents[1:]:
            if x - cur[-1] <= self.indent_tolerance: 
                cur.append(x)
            else: 
                groups.append(cur)
                cur = [x]
        groups.append(cur)
        
        # LIMIT DEPTH: Only use first max_depth groups to prevent deep nesting
        if len(groups) > max_depth:
            groups = groups[:max_depth]
            # Reassign remaining indents to the last allowed depth level
            last_group = groups[-1]
            for i, g in enumerate(groups):
                for indent_val in g:
                    if i >= max_depth:
                        last_group.extend(g)
                        break
        
        depth = {x: min(i, max_depth - 1) for i, g in enumerate(groups) for x in g}

        root, stack = [], []
        for b in bullets:
            lvl = depth.get(b["indent"], max_depth - 1)  # Default to max depth if not found
            lvl = min(lvl, max_depth - 1)  # Ensure we don't exceed max depth
            
            node = {"text": b["text"], "children": []}
            while len(stack) > lvl: 
                stack.pop()
            (root if not stack else stack[-1]["children"]).append(node)
            stack.append(node)

        return {"page": slide["page"], "title": slide["title"], "tree": root} 
    #endregion

    # region _clean_fragmented_text
    def _clean_fragmented_text(self, text: str) -> str:
        """
        Clean up fragmented text where characters are separated by spaces.
        Example: "h e l l o   w o r l d" -> "hello world"
        """
        if not text:
            return text
            
        # Split into words/tokens
        words = text.split()
        if len(words) <= 2:
            return text
            
        # Count single characters (letters, numbers, or common punctuation)
        single_char_count = sum(1 for word in words 
                               if len(word) == 1 and (word.isalnum() or word in ".,;:!?()[]{}"))
            
        # If more than 50% are single characters, treat as fragmented
        if single_char_count / len(words) > 0.5:
            result = []
            current_word = ""
            
            for i, word in enumerate(words):
                # Single character that should be merged
                if len(word) == 1 and word.isalnum():
                    current_word += word
                # Single punctuation - end current word and add punctuation
                elif len(word) == 1 and word in ".,;:!?":
                    if current_word:
                        result.append(current_word)
                        current_word = ""
                    result.append(word)
                # Multi-character word or special cases
                else:
                    if current_word:
                        result.append(current_word)
                        current_word = ""
                    result.append(word)
            
            # Don't forget the last word
            if current_word:
                result.append(current_word)
                
            return " ".join(result)
        
        return text

    def _merge_fragmented_words(self, row_words: List[dict], y_tolerance: float = 2.0) -> List[dict]:
        """
        Merge fragmented words that are on the same line and close together.
        This handles cases where PDF extraction splits words into individual characters.
        """
        if not row_words:
            return row_words
            
        # Sort by x position
        sorted_words = sorted(row_words, key=lambda w: w["x0"])
        merged = []
        current_group = [sorted_words[0]]
        
        for word in sorted_words[1:]:
            # Check if this word should be merged with the current group
            last_word = current_group[-1]
            
            # Calculate distance between words
            distance = word["x0"] - (last_word["x0"] + last_word.get("width", 10))
            
            # If words are very close (less than average character width) and single characters
            if (distance < 8 and 
                len(word["text"].strip()) == 1 and 
                len(last_word["text"].strip()) == 1 and
                abs(word["top"] - last_word["top"]) < y_tolerance):
                current_group.append(word)
            else:
                # Merge current group if it has multiple single characters
                if len(current_group) > 1 and all(len(w["text"].strip()) == 1 for w in current_group):
                    merged_text = "".join(w["text"].strip() for w in current_group)
                    merged_word = current_group[0].copy()
                    merged_word["text"] = merged_text
                    merged.append(merged_word)
                else:
                    merged.extend(current_group)
                current_group = [word]
        
        # Handle last group
        if len(current_group) > 1 and all(len(w["text"].strip()) == 1 for w in current_group):
            merged_text = "".join(w["text"].strip() for w in current_group)
            merged_word = current_group[0].copy()
            merged_word["text"] = merged_text
            merged.append(merged_word)
        else:
            merged.extend(current_group)
        
        return merged

    def debug_text_extraction(self, pdf_path: str, page_num: int = 1) -> dict:
        """
        Debug method to inspect raw text extraction for a specific page.
        Helps identify fragmentation issues.
        """
        with pdfplumber.open(pdf_path) as pdf:
            if page_num > len(pdf.pages):
                return {"error": f"Page {page_num} doesn't exist"}
                
            page = pdf.pages[page_num - 1]
            words = page.extract_words(use_text_flow=True, extra_attrs=["size"])
            
            # Analyze fragmentation
            single_chars = [w for w in words if len(w["text"].strip()) == 1]
            multi_chars = [w for w in words if len(w["text"].strip()) > 1]
            
            # Group words by y position (rows)
            rows = {}
            for word in words:
                y = round(word["top"], 1)
                rows.setdefault(y, []).append(word)
            
            row_analysis = []
            for y in sorted(rows.keys()):
                row_words = sorted(rows[y], key=lambda w: w["x0"])
                raw_text = " ".join(w["text"] for w in row_words)
                cleaned_text = self._clean_fragmented_text(raw_text)
                
                row_analysis.append({
                    "y_position": y,
                    "word_count": len(row_words),
                    "raw_text": raw_text,
                    "cleaned_text": cleaned_text,
                    "is_fragmented": raw_text != cleaned_text
                })
            
            return {
                "page": page_num,
                "total_words": len(words),
                "single_char_words": len(single_chars),
                "multi_char_words": len(multi_chars),
                "fragmentation_ratio": len(single_chars) / len(words) if words else 0,
                "rows": row_analysis,
                "sample_single_chars": [w["text"] for w in single_chars[:10]],
                "sample_multi_chars": [w["text"] for w in multi_chars[:10]]
            }
    #endregion

    def debug_bullet_parsing(self, pdf_path: str, page_num: int = 4) -> dict:
        """
        Debug the bullet parsing process to see where individual characters are being created
        """
        with pdfplumber.open(pdf_path) as pdf:
            if page_num > len(pdf.pages):
                return {"error": f"Page {page_num} doesn't exist"}
                
            # Extract lines for this page (same as _extract_lines but for single page)
            page = pdf.pages[page_num - 1]
            words = page.extract_words(use_text_flow=True, extra_attrs=["size"])
            rows = {}
            
            for word in words:
                text = word["text"].strip()
                if self.banner_regex.match(text):
                    continue
                y = round(word["top"], 1)
                rows.setdefault(y, []).append(word)

            lines = []
            for y in sorted(rows):
                row_words = sorted(rows[y], key=lambda w: w["x0"])
                merged_words = self._merge_fragmented_words(row_words)
                x0 = merged_words[0]["x0"]
                text = " ".join(w["text"] for w in merged_words)
                text = self._clean_fragmented_text(text)
                text = re.sub(rf"\s*{page_num}\s*$", "", text).strip()
                
                if text:
                    lines.append((x0, text, merged_words))

            # Debug the bullet explosion process
            print(f"🔍 DEBUGGING PAGE {page_num} BULLET PARSING:")
            print(f"Found {len(lines)} lines")
            
            bullets = []
            for i, (x, txt, row) in enumerate(lines):
                print(f"\nLine {i}: '{txt[:100]}{'...' if len(txt) > 100 else ''}'")
                
                # Call _explode_line and see what it produces
                exploded = self._explode_line(x, txt, row, page_num)
                print(f"  Exploded into {len(exploded)} bullet items:")
                
                for j, bullet in enumerate(exploded):
                    bullet_text = bullet['text'][:50] + '...' if len(bullet['text']) > 50 else bullet['text']
                    print(f"    {j}: '{bullet_text}' (indent: {bullet['indent']})")
                    
                    # Check if this is a single character
                    if len(bullet['text'].strip()) == 1:
                        print(f"      ⚠️  SINGLE CHARACTER DETECTED!")
                
                bullets.extend(exploded)
            
            # Show final bullet structure
            print(f"\n📊 FINAL BULLET SUMMARY:")
            print(f"Total bullets: {len(bullets)}")
            single_char_bullets = [b for b in bullets if len(b['text'].strip()) == 1]
            print(f"Single character bullets: {len(single_char_bullets)}")
            
            if single_char_bullets:
                print(f"Single chars: {[b['text'] for b in single_char_bullets[:20]]}")
            
            return {
                "page": page_num,
                "lines_count": len(lines),
                "bullets_count": len(bullets),
                "single_char_bullets": len(single_char_bullets),
                "bullets": bullets,
                "lines": [(x, txt) for x, txt, _ in lines]
            }

    def _is_heavily_fragmented_page(self, lines: List[tuple], fragmentation_threshold: float = 0.7) -> bool:
        """
        Check if a page is heavily fragmented (too many single-character lines)
        
        Args:
            lines: List of (x, text, words) tuples
            fragmentation_threshold: If more than this ratio are single chars, consider fragmented
        
        Returns:
            True if page is heavily fragmented
        """
        if not lines:
            return False
            
        short_lines = sum(1 for x, text, words in lines if len(text.strip()) <= 2)
        fragmentation_ratio = short_lines / len(lines)
        
        return fragmentation_ratio > fragmentation_threshold

    def _reconstruct_fragmented_lines(self, lines: List[tuple], max_distance: float = 50.0) -> List[tuple]:
        """
        Try to reconstruct fragmented text by grouping nearby single characters
        
        Args:
            lines: List of (x, text, words) tuples  
            max_distance: Maximum distance between characters to group them
        
        Returns:
            Reconstructed lines with merged characters
        """
        if not lines:
            return lines
        
        # Separate normal lines from fragmented ones
        normal_lines = []
        fragmented_chars = []
        
        for x, text, words in lines:
            if len(text.strip()) <= 2 and text.strip().isalnum():
                fragmented_chars.append((x, text.strip(), words))
            else:
                normal_lines.append((x, text, words))
        
        # Group fragmented characters by proximity
        if not fragmented_chars:
            return lines
        
        # Sort by x position
        fragmented_chars.sort(key=lambda item: item[0])
        
        reconstructed_lines = []
        current_group = [fragmented_chars[0]]
        
        for char_data in fragmented_chars[1:]:
            x, text, words = char_data
            last_x = current_group[-1][0]
            
            # If characters are close together, group them
            if abs(x - last_x) <= max_distance:
                current_group.append(char_data)
            else:
                # Finish current group and start new one
                if len(current_group) >= 3:  # Only reconstruct if we have enough chars
                    merged_text = "".join(item[1] for item in current_group)
                    avg_x = sum(item[0] for item in current_group) / len(current_group)
                    reconstructed_lines.append((avg_x, merged_text, current_group[0][2]))
                
                current_group = [char_data]
        
        # Handle last group
        if len(current_group) >= 3:
            merged_text = "".join(item[1] for item in current_group)
            avg_x = sum(item[0] for item in current_group) / len(current_group)
            reconstructed_lines.append((avg_x, merged_text, current_group[0][2]))
        
        # Combine normal lines with reconstructed lines
        all_lines = normal_lines + reconstructed_lines
        
        # Sort by x position to maintain order
        all_lines.sort(key=lambda item: item[0])
        
        return all_lines

    def _filter_fragmented_pages(self, deck: List[dict], 
                           fragmentation_threshold: float = 0.7,
                           min_meaningful_lines: int = 5,
                           delete_fragmented: bool = True) -> List[dict]:
        """
        Filter out or clean up heavily fragmented pages
        
        Args:
            deck: List of slide dictionaries
            fragmentation_threshold: Fragmentation ratio threshold
            min_meaningful_lines: Minimum lines needed to keep a page
            delete_fragmented: If True, delete fragmented pages immediately. If False, try to reconstruct.
        
        Returns:
            Filtered deck with fragmentation handled
        """
        filtered_deck = []
        
        for slide in deck:
            lines = slide["lines"]
            
            if self._is_heavily_fragmented_page(lines, fragmentation_threshold):
                short_lines = sum(1 for x, t, w in lines if len(t.strip()) <= 2)
                print(f"🚨 Page {slide['page']}: Heavily fragmented ({len(lines)} lines, {short_lines} short)")
                
                if delete_fragmented:
                    print(f"   ❌ Deleting fragmented page {slide['page']}")
                    continue  # Skip this page entirely
                else:
                    # Try to reconstruct fragmented text (old behavior)
                    reconstructed_lines = self._reconstruct_fragmented_lines(lines)
                    meaningful_lines = [l for l in reconstructed_lines if len(l[1].strip()) > 3]
                    
                    if len(meaningful_lines) >= min_meaningful_lines:
                        print(f"   ✅ Reconstructed to {len(reconstructed_lines)} lines "
                              f"({len(meaningful_lines)} meaningful)")
                        slide["lines"] = reconstructed_lines
                        filtered_deck.append(slide)
                    else:
                        print(f"   ❌ Deleting page - insufficient meaningful content")
                        continue
            else:
                # Page is fine, keep as-is
                filtered_deck.append(slide)
        
        return filtered_deck