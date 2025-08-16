"""
Prompt templates for AI-powered course content generation.
Based on the actual prompts used in poc.ipynb.
"""

import json
from typing import List

from ..models import Slides

# =============================================================================
# ONE SHOT TEMPLATE - Outline and Mapping Generation (Branch B - No Plan)
# =============================================================================

def build_outline_and_mapping_prompt(slides: List[Slides]) -> str:
    """Generate the one-shot prompt for outline and mapping when no plan is provided"""
    slides_json = json.dumps(
        [s.model_dump() for s in slides], ensure_ascii=False, indent=2
    )
    return f"""
OBJECTIF
A partir de la liste ordonnée de diapositives, produire:
1) Un plan de cours hiérarchique cohérent (OUTLINE) de profondeur maximale 3.
2) Un MAPPING associant chaque section du plan aux identifiants de slides pertinents.

DONNÉES
SLIDES: liste d'objets {{id, title, content}} dans l'ordre d'apparition. Attention: le champ "title" n'est PAS fiable. Il correspond souvent à la plus grande police parmi les 5 premières lignes et peut être trompeur. Déduire les titres de sections à partir du contenu réel.
{slides_json}

SCHÉMA DE SORTIE - STRICTEMENT OBLIGATOIRE
Un JSON valide avec exactement deux clés de premier niveau: "outline" et "mapping".

class ContentSection(BaseModel):
    id: str                           # SEC_1, SEC_1.1, SEC_1.1.1
    title: str                        # 5 à 12 mots, clair et informatif
    content: List[str]                # Toujours [] à ce stade
    subsections: List["ContentSection"]

class Content(BaseModel):
    sections: List[ContentSection]

class MappingItem(BaseModel):
    section_id: str                   # Doit exister dans outline
    slide_ids: List[str]              # Identifiants "SL_xxx" fournis en entrée

class OutlineAndMapping(BaseModel):
    outline: Content
    mapping: List[MappingItem]

CONTRAINTES OUTLINE
- Profondeur maximale: 3 niveaux. Exemple autorisé: SEC_2.3.1. Exemple interdit: SEC_2.3.1.4.
- Numérotation continue par niveau: SEC_1, SEC_2, ... puis SEC_2.1, SEC_2.2, etc.
- L'ordre du plan suit la progression implicite des SLIDES.
- Les titres sont générés à partir du contenu des slides. Traiter "title" comme indice faible seulement.
- Le champ "content" de chaque section doit être [].

CONTRAINTES MAPPING
- Chaque section du plan apparaît exactement une fois dans "mapping" via son "section_id".
- Chaque slide_id fourni apparaît au moins une fois dans l'ensemble de "mapping".
- Une slide peut être mappée à plusieurs sections si pertinent. Favoriser des groupes contigus.
- N'utiliser que des identifiants existants.

HEURISTIQUES DE STRUCTURATION
- Regrouper par thèmes en s'appuyant sur: mots-clés dominants, listes à puces, définitions, exemples, transitions comme "Introduction", "Objectifs", "Méthodes", "Résultats", "Conclusion".
- Détecter les limites de sections par changements nets de vocabulaire, apparition de nouveaux items de liste, ou marqueurs forts.
- Ignorer le bruit: en-têtes répétés, numéros de page, crédits, filigranes, sauf si une section Bibliographie est manifeste.
- En cas d'ambiguïté, assigner la slide à la section la plus spécifique qui couvre la majorité de son contenu.

FORMAT DE SORTIE - EXEMPLE FACTICE
{{
  "outline": {{
    "sections": [
      {{
        "id": "SEC_1",
        "title": "Contexte du domaine et objectifs d apprentissage",
        "content": [],
        "subsections": [
          {{
            "id": "SEC_1.1",
            "title": "Problématique centrale et périmètre du cours",
            "content": [],
            "subsections": []
          }},
          {{
            "id": "SEC_1.2",
            "title": "Organisation du cours et attendus",
            "content": [],
            "subsections": []
          }}
        ]
      }},
      {{
        "id": "SEC_2",
        "title": "Notions fondamentales et définitions clés",
        "content": [],
        "subsections": []
      }}
    ]
  }},
  "mapping": [
    {{ "section_id": "SEC_1",   "slide_ids": ["SL_001", "SL_002"] }},
    {{ "section_id": "SEC_1.1", "slide_ids": ["SL_003"] }},
    {{ "section_id": "SEC_1.2", "slide_ids": ["SL_004", "SL_005"] }},
    {{ "section_id": "SEC_2",   "slide_ids": ["SL_006", "SL_007", "SL_008"] }}
  ]
}}

SORTIE
- Retourner uniquement le JSON valide conforme à OutlineAndMapping.
- Aucune explication ni commentaire hors du JSON.
""".strip()

# =============================================================================
# OUTLINE FROM PLAN TEMPLATE - Two-pass outline generation (Branch A)
# =============================================================================

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

# =============================================================================
# MAPPING FROM OUTLINE TEMPLATE - Two-pass mapping (Branch A)
# =============================================================================

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
{{
  "mapping": [
    {{ "section_id": "SEC_1", "slide_ids": ["SL_001", "SL_002"] }},
    {{ "section_id": "SEC_1.1", "slide_ids": ["SL_003", "SL_004"] }}
  ]
}}

CONTRAINTES À RESPECTER IMPÉRATIVEMENT
- Chaque "section_id" présent dans PLAN_JSON doit apparaître **exactement une fois**.
- Chaque "slide_id" présent dans SLIDES doit apparaître **au moins une fois** (aucune slide orpheline).
- "slide_ids" est un tableau d'identifiants ; l'ordre interne n'a pas d'importance.
- N'utilise **que** des identifiants existants ; n'invente pas de clés ni de champs.
- AUCUNE explication, commentaire ou clé supplémentaire : la sortie doit être **uniquement** le JSON demandé.
""".strip()

# =============================================================================
# WRITER TEMPLATE - Final content enhancement
# =============================================================================

def build_system_prompt() -> str:
    """
    Prompt système définissant le rôle et les règles
    """
    return """Tu es un expert en rédaction pédagogique. Ta tâche est de transformer du contenu brut de slides en paragraphes de cours structurés.

Règles :
- Ne Mentione jamais la source des slides, l'université, le professeur, l'institut, etc.
- Traite TOUTES les sections du JSON (ne t'arrête pas à la première)
- Pour chaque section, synthétise tous les éléments content[] en 2-10 paragraphes cohérents
- Chaque paragraphe = maximum 10 phrases liées au titre de la section
- Conserve la structure JSON exacte (mêmes IDs, titres, ordre)
- Style académique fluide"""


def build_user_prompt(content_json: str) -> str:
    """
    Prompt utilisateur avec le contenu à traiter
    """
    return content_json


def build_assistant_prompt() -> str:
    """
    Prompt assistant avec exemple d'input/output
    """
    return """Voici un exemple de transformation attendue :

INPUT EXEMPLE:
```json
{
  "sections": [
    {
      "id": "SEC_1",
      "title": "Introduction aux Algorithmes",
      "content": [
        "CS101: Algorithmique\\nAlgorithmes\\n• Définition: séquence d'instructions\\n• Résolution problèmes\\n• Entrée → Traitement → Sortie\\n• Propriétés essentielles\\n1",
        "CS101: Algorithmique\\nCaractéristiques\\n• Fini (nombre étapes)\\n• Non-ambigu\\n• Déterministe\\n• Efficacité importante\\n• Complexité temporelle/spatiale\\n2",
        "CS101: Algorithmique\\nTypes d'algorithmes\\n• Itératifs vs Récursifs\\n• Diviser pour régner\\n• Gloutons (greedy)\\n• Programmation dynamique\\nExemples concrets\\n3"
      ],
      "subsections": [
        {
          "id": "SEC_1.1",
          "title": "Notation Big-O",
          "content": [
            "CS101: Algorithmique\\nComplexité algorithmique\\n• Notation O(n)\\n• Mesure efficacité\\n• Pire cas considéré\\n• Croissance asymptotique\\n4",
            "CS101: Algorithmique\\nExemples complexités\\n• O(1) - constant\\n• O(log n) - logarithmique\\n• O(n) - linéaire\\n• O(n²) - quadratique\\n• O(2^n) - exponentielle\\n5"
          ],
          "subsections": []
        }
      ]
    },
    {
      "id": "SEC_2", 
      "title": "Structures de Données",
      "content": [
        "CS101: Algorithmique\\nStructures fondamentales\\n• Tableaux (arrays)\\n• Listes chaînées\\n• Piles (stacks)\\n• Files (queues)\\n• Organisation mémoire\\n6",
        "CS101: Algorithmique\\nOpérations de base\\n• Insertion / Suppression\\n• Recherche / Accès\\n• Parcours / Tri\\n• Complexité variable\\n• Trade-offs temps/espace\\n7"
      ],
      "subsections": []
    }
  ]
}
```

OUTPUT EXEMPLE:
```json
{
  "sections": [
    {
      "id": "SEC_1",
      "title": "Introduction aux Algorithmes", 
      "content": [
        "Un algorithme constitue une séquence finie et ordonnée d'instructions permettant de résoudre un problème spécifique ou d'accomplir une tâche donnée. Cette approche systématique transforme des données d'entrée en résultats de sortie par l'application d'un processus de traitement déterministe et reproductible.",
        "Les algorithmes présentent des caractéristiques fondamentales qui garantissent leur validité : ils doivent être finis dans le nombre d'étapes, non-ambigus dans leur interprétation, et déterministes dans leur exécution. L'efficacité algorithmique, mesurée par les complexités temporelle et spatiale, constitue un critère essentiel d'évaluation de leur performance.",
        "La classification des algorithmes distingue plusieurs approches méthodologiques selon leur stratégie de résolution : les algorithmes itératifs et récursifs, les méthodes diviser-pour-régner, les algorithmes gloutons, et la programmation dynamique. Chaque paradigme offre des avantages spécifiques selon la nature du problème à traiter."
      ],
      "subsections": [
        {
          "id": "SEC_1.1",
          "title": "Notation Big-O",
          "content": [
            "La notation Big-O fournit un outil mathématique pour caractériser la complexité algorithmique en décrivant la croissance asymptotique du temps d'exécution ou de l'espace mémoire requis. Cette mesure considère le comportement dans le pire cas et permet de comparer objectivement l'efficacité de différents algorithmes.",
            "Les classes de complexité courantes s'organisent selon une hiérarchie croissante : O(1) pour les opérations à temps constant, O(log n) pour les algorithmes logarithmiques, O(n) pour les traitements linéaires, O(n²) pour les approches quadratiques, et O(2^n) pour les solutions exponentielles. Cette classification guide le choix algorithmique selon les contraintes de performance requises."
          ],
          "subsections": []
        }
      ]
    },
    {
      "id": "SEC_2",
      "title": "Structures de Données",
      "content": [
        "Les structures de données fondamentales organisent et stockent l'information selon des patterns spécifiques adaptés aux besoins algorithmiques : les tableaux offrent un accès direct par index, les listes chaînées permettent une allocation dynamique, tandis que les piles et files implémentent des politiques d'accès particulières. L'organisation mémoire influence directement les performances d'accès et de manipulation.",
        "Les opérations de base sur ces structures - insertion, suppression, recherche, accès, parcours et tri - présentent des complexités variables selon l'implémentation choisie. Ces trade-offs entre temps d'exécution et espace mémoire orientent la sélection de la structure la plus appropriée selon les contraintes spécifiques de chaque application."
      ],
      "subsections": []
    }
  ]
}
```

Maintenant traite le JSON fourni en suivant ce modèle :"""


def build_prompt_fill_content(content_json: str) -> str:
    """
    Version legacy - maintenant utilise les 3 fonctions séparées ci-dessus
    """
    return f"""
**SYSTEM:**
{build_system_prompt()}

**USER:**
{build_user_prompt(content_json)}

**ASSISTANT:**
{build_assistant_prompt()}
""".strip()

# =============================================================================
# SYSTEM PROMPTS FOR DIFFERENT ROLES
# =============================================================================

ONE_SHOT_SYSTEM_PROMPT = "Tu es un expert en structuration pédagogique. Tu infères un plan hiérarchique fiable et un mapping de slides à partir d'un deck bruité."

WRITER_SYSTEM_PROMPT = "Tu es un Professeur qui remplit le contenu des sections du plan de cours à partir du contenu des slides."