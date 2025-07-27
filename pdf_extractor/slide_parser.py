"""Slide parser for analyzing and structuring extracted PDF slide content."""

import re
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from collections import Counter
import logging

from .pdf_processor import SlideContent

logger = logging.getLogger(__name__)

@dataclass
class ParsedSlide:
    """Container for parsed slide content."""
    page_number: int
    title: Optional[str]
    bullet_points: List[str]
    paragraphs: List[str]
    keywords: List[str]
    slide_type: str
    importance_score: float
    raw_content: SlideContent

@dataclass
class PresentationStructure:
    """Container for overall presentation structure."""
    title_slide: Optional[ParsedSlide]
    content_slides: List[ParsedSlide]
    summary_slides: List[ParsedSlide]

    total_slides: int
    main_topics: List[str]
    keyword_frequency: Dict[str, int]

class SlideParser:
    """Parse and analyze extracted slide content."""
    
    def __init__(self):
        """Initialize slide parser."""
        # Common slide title patterns
        self.title_patterns = [
            r'^([A-Z][^.!?]*(?:[.!?]|$))',  # Starts with capital, ends with punctuation or end
            r'^(\d+\.?\s+[A-Z][^.!?]*)',    # Starts with number
            r'^([A-Z\s]{10,50})\n',          # All caps short line
            r'^(.{1,60})\n\n',               # Short line followed by double newline
        ]
        
        # Bullet point patterns
        self.bullet_patterns = [
            r'^\s*[•·▪▫▸▹►▻⁃]\s*(.+)',      # Various bullet symbols
            r'^\s*[-*]\s*(.+)',              # Dash or asterisk
            r'^\s*\d+[.)]\s*(.+)',           # Numbered lists
            r'^\s*[a-zA-Z][.)]\s*(.+)',      # Lettered lists
        ]
        
        # Common stop words for keyword extraction
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
        }
    
    def extract_title(self, text: str) -> Optional[str]:
        """
        Extract the most likely title from slide text.
        
        Args:
            text: Raw slide text
            
        Returns:
            Extracted title or None
        """
        if not text.strip():
            return None
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if not lines:
            return None
        
        # Try different title extraction patterns
        for pattern in self.title_patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                title = match.group(1).strip()
                if 5 <= len(title) <= 100:  # Reasonable title length
                    return title
        
        # Fallback: use first non-empty line if it's not too long
        first_line = lines[0]
        if len(first_line) <= 100:
            return first_line
        
        return None
    
    def extract_bullet_points(self, text: str) -> List[str]:
        """
        Extract bullet points from slide text.
        
        Args:
            text: Raw slide text
            
        Returns:
            List of bullet point text
        """
        bullet_points = []
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            for pattern in self.bullet_patterns:
                match = re.match(pattern, line)
                if match:
                    bullet_text = match.group(1).strip()
                    if bullet_text and len(bullet_text) > 3:  # Minimum length
                        bullet_points.append(bullet_text)
                    break
        
        return bullet_points
    
    def extract_paragraphs(self, text: str, exclude_bullets: bool = True) -> List[str]:
        """
        Extract paragraph content from slide text.
        
        Args:
            text: Raw slide text
            exclude_bullets: Whether to exclude bullet point lines
            
        Returns:
            List of paragraph text
        """
        paragraphs = []
        
        # Split by double newlines or similar paragraph separators
        potential_paragraphs = re.split(r'\n\s*\n', text)
        
        for para in potential_paragraphs:
            para = para.strip()
            if not para or len(para) < 20:  # Skip very short content
                continue
            
            # Skip if it looks like a title (too short, all caps, etc.)
            if len(para) < 50 and (para.isupper() or para.count(' ') < 3):
                continue
            
            # Skip bullet points if requested
            if exclude_bullets:
                lines = para.split('\n')
                filtered_lines = []
                for line in lines:
                    is_bullet = any(re.match(pattern, line.strip()) for pattern in self.bullet_patterns)
                    if not is_bullet:
                        filtered_lines.append(line)
                para = '\n'.join(filtered_lines).strip()
            
            if para and len(para) >= 20:
                paragraphs.append(para)
        
        return paragraphs
    
    def extract_keywords(self, text: str, min_freq: int = 1, max_keywords: int = 20) -> List[str]:
        """
        Extract important keywords from slide text.
        
        Args:
            text: Raw slide text
            min_freq: Minimum frequency for a word to be considered
            max_keywords: Maximum number of keywords to return
            
        Returns:
            List of keywords sorted by importance
        """
        if not text:
            return []
        
        # Clean and tokenize text
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
        # Filter out stop words and short words
        meaningful_words = [
            word for word in words 
            if len(word) > 3 and word not in self.stop_words
        ]
        
        # Count word frequencies
        word_freq = Counter(meaningful_words)
        
        # Filter by minimum frequency and get top keywords
        keywords = [
            word for word, freq in word_freq.most_common(max_keywords)
            if freq >= min_freq
        ]
        
        return keywords


    def classify_slide_type(self, parsed_slide: 'ParsedSlide') -> str:
        """
        Classify the type of slide based on its content.
        
        Args:
            parsed_slide: ParsedSlide object
            
        Returns:
            Slide type classification
        """
        text = parsed_slide.raw_content.text.lower()
        title = (parsed_slide.title or '').lower()
        
        # Title slide indicators
        title_indicators = ['title', 'introduction', 'overview', 'agenda', 'outline']
        if any(indicator in title for indicator in title_indicators):
            return 'title'
        
        # Summary/conclusion slide indicators
        summary_indicators = ['summary', 'conclusion', 'recap', 'key points', 'takeaways']
        if any(indicator in title for indicator in summary_indicators):
            return 'summary'
        
        # Content analysis
        if len(parsed_slide.bullet_points) > 3:
            return 'bullet_list'
        elif len(parsed_slide.paragraphs) > 0:
            return 'text_heavy'
        elif len(parsed_slide.raw_content.images) > 0:
            return 'image_heavy'
        elif parsed_slide.page_number == 1:
            return 'title'
        else:
            return 'content'
    
    def calculate_importance_score(self, parsed_slide: 'ParsedSlide') -> float:
        """
        Calculate importance score for a slide.
        
        Args:
            parsed_slide: ParsedSlide object
            
        Returns:
            Importance score (0.0 to 1.0)
        """
        score = 0.0
        
        # Text content weight
        text_length = len(parsed_slide.raw_content.text)
        if text_length > 0:
            score += min(text_length / 500, 0.3)  # Max 0.3 for text length
        
        # Bullet points weight
        bullet_count = len(parsed_slide.bullet_points)
        score += min(bullet_count * 0.05, 0.2)  # Max 0.2 for bullets
        
        # Keyword density weight
        keyword_count = len(parsed_slide.keywords)
        score += min(keyword_count * 0.02, 0.2)  # Max 0.2 for keywords
        
        # Image content weight
        image_count = len(parsed_slide.raw_content.images)
        score += min(image_count * 0.1, 0.2)  # Max 0.2 for images
        
        # Slide type weight
        type_weights = {
            'title': 0.1,
            'summary': 0.3,
            'bullet_list': 0.25,
            'text_heavy': 0.2,
            'image_heavy': 0.15,
            'content': 0.2
        }
        score += type_weights.get(parsed_slide.slide_type, 0.1)
        
        return min(score, 1.0)
    
    def parse_slides(self, slides: List[SlideContent]) -> List[ParsedSlide]:
        """
        Parse a list of slide content into structured format.
        
        Args:
            slides: List of SlideContent objects
            
        Returns:
            List of ParsedSlide objects
        """
        parsed_slides = []
        
        for slide in slides:
            try:
                # Extract structured content
                title = self.extract_title(slide.text)
                bullet_points = self.extract_bullet_points(slide.text)
                paragraphs = self.extract_paragraphs(slide.text)
                keywords = self.extract_keywords(slide.text)
                
                # Create parsed slide
                parsed_slide = ParsedSlide(
                    page_number=slide.page_number,
                    title=title,
                    bullet_points=bullet_points,
                    paragraphs=paragraphs,
                    keywords=keywords,
                    slide_type='',  # Will be set below
                    importance_score=0.0,  # Will be calculated below
                    raw_content=slide
                )
                
                # Classify and score
                parsed_slide.slide_type = self.classify_slide_type(parsed_slide)
                parsed_slide.importance_score = self.calculate_importance_score(parsed_slide)
                
                parsed_slides.append(parsed_slide)
                
                logger.debug(f"Parsed slide {slide.page_number}: {parsed_slide.slide_type}, score: {parsed_slide.importance_score:.2f}")
                
            except Exception as e:
                logger.error(f"Error parsing slide {slide.page_number}: {e}")
        
        return parsed_slides
    
    def analyze_presentation_structure(self, parsed_slides: List[ParsedSlide]) -> PresentationStructure:
        """
        Analyze the overall structure of the presentation.
        
        Args:
            parsed_slides: List of ParsedSlide objects
            
        Returns:
            PresentationStructure object
        """
        # Identify slide types
        title_slide = None
        content_slides = []
        summary_slides = []
        
        for slide in parsed_slides:
            if slide.slide_type == 'title' and title_slide is None:
                title_slide = slide
            elif slide.slide_type == 'summary':
                summary_slides.append(slide)
            else:
                content_slides.append(slide)
        
        # Extract main topics (from high-importance slide titles)
        main_topics = []
        for slide in sorted(parsed_slides, key=lambda x: x.importance_score, reverse=True)[:5]:
            if slide.title:
                main_topics.append(slide.title)
        
        # Calculate overall keyword frequency
        all_keywords = []
        for slide in parsed_slides:
            all_keywords.extend(slide.keywords)
        keyword_frequency = dict(Counter(all_keywords))
        
        return PresentationStructure(
            title_slide=title_slide,
            content_slides=content_slides,
            summary_slides=summary_slides,
            total_slides=len(parsed_slides),
            main_topics=main_topics,
            keyword_frequency=keyword_frequency
        )
    
    def generate_presentation_summary(self, structure: PresentationStructure) -> str:
        """
        Generate a text summary of the presentation.
        
        Args:
            structure: PresentationStructure object
            
        Returns:
            Summary text
        """
        summary_parts = []
        
        # Title and basic info
        title = structure.title_slide.title if structure.title_slide else "Untitled Presentation"
        summary_parts.append(f"Presentation: {title}")
        summary_parts.append(f"Total slides: {structure.total_slides}")
        
        # Main topics
        if structure.main_topics:
            summary_parts.append("\nMain Topics:")
            for i, topic in enumerate(structure.main_topics[:5], 1):
                summary_parts.append(f"{i}. {topic}")
        
        # Key keywords
        if structure.keyword_frequency:
            top_keywords = sorted(structure.keyword_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
            summary_parts.append(f"\nKey terms: {', '.join([kw for kw, _ in top_keywords])}")
        
        # Slide distribution
        content_count = len(structure.content_slides)
        summary_count = len(structure.summary_slides)
        summary_parts.append(f"\nSlide breakdown: {content_count} content slides, {summary_count} summary slides")
        
        return "\n".join(summary_parts) 