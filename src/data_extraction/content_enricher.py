"""
Content.enrich_with_slides() - deterministic content enrichment
Based on the existing implementation in models.py
"""

from typing import List

from ..models import Content, SectionSlideMapping, Slides


class ContentEnricher:
    """Handles deterministic content enrichment with slides"""
    
    def __init__(self):
        """Initialize content enricher"""
        pass
    
    def enrich_with_slides(self, 
                          content: Content, 
                          slides: List[Slides], 
                          mapping: SectionSlideMapping) -> Content:
        """
        Enrich Content object with slides data based on the mapping.
        This is a wrapper around the existing Content.enrich_with_slides method
        
        Args:
            content: Content object with outline structure
            slides: List of Slides objects containing the slide content
            mapping: SectionSlideMapping object that maps sections to slides
            
        Returns:
            Enriched Content object with slide content in sections
        """
        return content.enrich_with_slides(slides, mapping)