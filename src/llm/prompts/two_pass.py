from __future__ import annotations

from typing import List

OUTLINE_FROM_PLAN_SYSTEM_PROMPT = """
You are a course structure analyzer specialized in French academic content.  
Your task is to parse a raw course outline text containing numbered section titles (like "I.", "1.", "1.1.", etc.) or indented bullet points.
and generate a hierarchical JSON structure matching this Pydantic model:

class ContentSection:
    id: str = ""
    title: str
    content: str = ""
    subsections: List[ContentSection]

class Content:
    sections: List[ContentSection]

Requirements:
- Never mention the source of slides, university, professor, institute, etc.
- Detect all section titles and nest subsections correctly based on numbering.
- Maintain full recursive hierarchy.
- Return valid JSON exactly matching the Content model structure.
- Include every section and subsection with their titles.
- Ignore the content and the id of the sections, you only need to return the outline.
- Return ONLY the JSON, no additional text or explanation.
"""

def build_mapping_prompt(outline_json: str, slides: List[dict]) -> str:
    """
    Génère le prompt demandant au modèle de produire le mapping section→slides.

    Paramètres
    ----------
    outline_json : str   JSON du plan (chaque section possède un id SEC_***)
    slides       : list  Liste de dicts {"id": "SL_***", "title": ..., "content": ...}

    Retour
    ------
    str : prompt clair et contraignant, prêt pour client.responses.parse
    """
    return f"""
OBJECTIF
Associer chaque section du plan aux diapositives pertinentes.

DONNÉES
1) PLAN_JSON : (structure hiérarchique, chaque section a un identifiant unique "SEC_xxx")


This is the structure of the outline that you will receive:
class ContentSection(BaseModel):
    id: str
    title: str
    content: Optional[str] = ""
    subsections: List["ContentSection"] = Field(default_factory=list)
    
class Content(BaseModel):
    sections: List[ContentSection]

This is the actual outline:

{outline_json}

          


2) SLIDES : (liste ordonnée, chaque slide a un identifiant unique "SL_xxx")
{slides}

FORMAT DE SORTIE — STRICTEMENT OBLIGATOIRE
Un JSON **valide** contenant UNE SEULE clé de premier niveau : "mapping".

This is the pydantic model SectionSlideMapping that you will use to return the mapping:

class MappingItem(BaseModel):
    section_id: str
    slide_ids:  List[str]

class SectionSlideMapping(BaseModel):
    mapping: List[MappingItem]


Exemple de structure attendue :
{
  "mapping": [
    { "section_id": "SEC_1", "slide_ids": ["SL_001", "SL_002"] },
    { "section_id": "SEC_1.1", "slide_ids": ["SL_003", "SL_004"] }
  ]
}

CONTRAINTES À RESPECTER IMPÉRATIVEMENT
- Chaque "section_id" présent dans PLAN_JSON doit apparaître **exactement une fois**.
- Chaque "slide_id" présent dans SLIDES doit apparaître **au moins une fois** (aucune slide orpheline).
- "slide_ids" est un tableau d'identifiants ; l'ordre interne n'a pas d'importance.
- N'utilise **que** des identifiants existants ; n'invente pas de clés ni de champs.
- AUCUNE explication, commentaire ou clé supplémentaire : la sortie doit être **uniquement** le JSON demandé.
""".strip()


