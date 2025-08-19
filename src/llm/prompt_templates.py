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
- Jamais de sections: Crédits ou références ou mentions légales du cours. Uniquement le contenu du cours.
- Ignore le contenu sur l'administratrif, le cursus, organisation des modules, etc.
- Capture uniquement le contenu du cours de medecine contenu dans les slides.

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
# ONE SHOT TEMPLATE (Filtered) - Exclude admin/cursus slides from outline+mapping
# =============================================================================


def build_outline_and_mapping_prompt_no_admin(slides: List[Slides]) -> str:
    """Generate one-shot prompt that EXCLUDES administrative/cursus slides

    - Do not create outline sections from admin/cursus/organizational slides
    - Do not map admin/cursus slides; it's allowed that some slide_ids are omitted
    """
    slides_json = json.dumps(
        [s.model_dump() for s in slides], ensure_ascii=False, indent=2
    )
    return f"""
OBJECTIF (FILTRÉ)
À partir de la liste ordonnée de diapositives, produire UNIQUEMENT:
1) Un plan de cours hiérarchique cohérent (OUTLINE) de profondeur maximale 3 basé sur le CONTENU PÉDAGOGIQUE.
2) Un MAPPING qui associe chaque section aux identifiants des slides PÉDAGOGIQUES pertinents.

DONNÉES
SLIDES: liste d'objets {{id, title, content}} dans l'ordre d'apparition. Attention: le champ "title" n'est PAS fiable. Il peut être un artefact de mise en forme. Déduire les titres à partir du contenu.
{slides_json}

EXCLUSIONS (À FILTRER ABSOLUMENT)
- Ne PAS créer de section et NE PAS mapper les slides de type administratif / cursus / logistique:
  * informations de cursus, organisation du semestre, calendrier, planning, ECTS, crédits, coefficients
  * modalités/critères d'évaluation, examens, barème, présence/assiduité, consignes de contrôle
  * informations d'enseignant (nom, email, bureau), logos, remerciements, contact, page de garde
  * objectifs du module (généraux), approche pédagogique, consignes de TD/TP, règles de classe
  * bibliographie générique, références institutionnelles, disclaimers, pages vides ou séparateurs
- Ne PAS inclure les diapositives d'introduction/aperçu qui ne portent pas sur le contenu disciplinaire:
  * titres généraux, sommaires/plan du cours, objectifs d'apprentissage, contexte, enjeux, motivation
  * "Introduction", "Contexte", "Objectifs", "Plan", "Sommaire", "Pourquoi ce cours?", "Agenda"
  * historiques/chronologies générales, rappels organisationnels
- Indices forts d'exclusion (liste non exhaustive): "ECTS", "coefficient", "évaluation", "examen",
  "barème", "modalités", "enseignant", "contact", "planning", "calendrier", "organisation",
  "TD", "TP", "administratif", "règlement", "bibliographie", "pré-requis", "prérequis", "campus",
  "introduction", "contexte", "objectifs", "plan du cours", "sommaire", "agenda".
- La position en début/fin de deck est fréquente mais non suffisante. Décider à partir du contenu.

POINT DE DÉMARRAGE
- Démarrer l'OUTLINE directement à la première diapositive qui contient du contenu pédagogique réel
  (définitions disciplinaires, mécanismes, structures, équations, listes scientifiques, etc.).
- Ne pas créer de section d'en-tête nommée "Introduction"/"Objectifs"/"Plan" à moins qu'elle contienne
  des définitions ou concepts scientifiques essentiels; dans ce cas, la renommer avec un titre descriptif
  du domaine traité (ex.: "Principes de la catalyse enzymatique").

SCHÉMA DE SORTIE - STRICTEMENT OBLIGATOIRE
Un JSON valide avec exactement deux clés de premier niveau: "outline" et "mapping".

class ContentSection(BaseModel):
    id: str
    title: str
    content: List[str]
    subsections: List["ContentSection"]

class Content(BaseModel):
    sections: List[ContentSection]

class MappingItem(BaseModel):
    section_id: str
    slide_ids: List[str]

class OutlineAndMapping(BaseModel):
    outline: Content
    mapping: List[MappingItem]

CONTRAINTES OUTLINE
- Profondeur maximale: 3 niveaux (SEC_1, SEC_1.1, SEC_1.1.1)
- Les titres sont générés à partir du CONTENU PÉDAGOGIQUE réel (définitions, mécanismes, concepts, listes à puces disciplinaires, etc.)
- Ne créer AUCUNE section à partir de slides filtrées (admin/cursus/logistique)
- Le champ "content" de chaque section doit être [] à ce stade

CONTRAINTES MAPPING (AVEC FILTRAGE)
- Mapper UNIQUEMENT des slide_ids correspondant à du contenu pédagogique.
- Ignorer systématiquement les slides d'introduction/aperçu et administratives dans le mapping.
- Il est NORMAL que certaines slides n'apparaissent PAS dans le mapping si elles ont été filtrées.
- N'utiliser que des identifiants existants; ne pas inventer de slides ni de sections.

HEURISTIQUES DE STRUCTURATION
- Regrouper par thèmes disciplinaires (définitions, mécanismes, exemples, listes scientifiques, équations)
- Détecter et ignorer les slides d'intro/outro non pédagogiques même si elles contiennent des listes
- En cas d'ambiguïté, privilégier l'exclusion des slides manifestement non pédagogiques

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


# =============================================================================
# STRUCTURED WRITER TEMPLATE - Enhanced with formatting support
# =============================================================================


def build_system_prompt_structured() -> str:
    """
    Enhanced system prompt that encourages structured formatting
    """
    return """Tu es un expert en rédaction pédagogique. Ta tâche est de transformer du contenu brut de slides en contenu de cours structuré et aéré.

Règles de contenu :
- Ne mentionne jamais la source des slides, l'université, le professeur, l'institut, etc.
- Traite TOUTES les sections du JSON (ne t'arrête pas à la première)
- Pour chaque section, synthétise tous les éléments content[] en contenu cohérent
- Conserve la structure JSON exacte (mêmes IDs, titres, ordre)
- Style académique fluide

Règles de formatage - UTILISE LA STRUCTURE :
- Privilégie les listes à puces (•) pour les énumérations, caractéristiques, étapes
- Utilise les listes numérotées (1., 2., 3.) pour les processus séquentiels
- Alterne entre paragraphes et listes pour aérer le texte
- Maximum 3-4 phrases par paragraphe
- Une liste = 2-6 éléments maximum

Syntaxe pour les listes dans le JSON :
- Liste à puces : commence par "• " (bullet + espace)
- Liste numérotée : commence par "1. ", "2. ", etc.
- Paragraphe normal : pas de préfixe spécial

Exemple de bon formatage :
"La représentation de Fischer respecte trois règles fondamentales :

• La chaîne carbonée la plus longue est disposée verticalement
• Le carbone le plus oxydé est placé en haut  
• L'orientation des substituants est indiquée par des liaisons horizontales (devant) et verticales (derrière)

Cette convention permet une lecture standardisée des molécules organiques."""


def build_assistant_prompt_structured() -> str:
    """
    Enhanced assistant prompt with structured formatting example
    """
    return """Voici un exemple de transformation attendue avec formatage structuré :

INPUT EXEMPLE:
```json
{
  "sections": [
    {
      "id": "SEC_1",
      "title": "Représentation de Fischer",
      "content": [
        "Biochimie\\nReprésentation Fischer\\n• Chaîne carbonée verticale\\n• Carbone oxydé en haut\\n• Substituants horizontaux/verticaux\\n• Convention standardisée\\n1",
        "Biochimie\\nRègles application\\n• Liaison horizontale = devant\\n• Liaison verticale = derrière\\n• Rotation interdite\\n• Projection plane obligatoire\\n2"
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
      "title": "Représentation de Fischer",
      "content": [
        "La représentation de Fischer constitue une méthode standardisée pour projeter les molécules organiques tridimensionnelles sur un plan bidimensionnel.",
        
        "Cette convention respecte trois règles fondamentales :",
        
        "• La chaîne carbonée la plus longue est disposée verticalement",
        "• Le carbone le plus oxydé est placé en haut",
        "• L'orientation des substituants est indiquée par des liaisons horizontales (devant) et verticales (derrière)",
        
        "L'application rigoureuse de ces règles nécessite le respect de contraintes spécifiques :",
        
        "1. Les liaisons horizontales représentent les substituants orientés vers l'observateur",
        "2. Les liaisons verticales indiquent les substituants orientés vers l'arrière",
        "3. Aucune rotation de la molécule n'est autorisée une fois la projection établie",
        
        "Cette méthode permet une lecture uniforme et non ambiguë des structures moléculaires complexes."
      ],
      "subsections": []
    }
  ]
}
```

Maintenant traite le JSON fourni en suivant ce modèle :"""


def build_prompt_fill_content_structured(content_json: str) -> str:
    """
    Enhanced version with structured formatting support
    """
    return f"""
**SYSTEM:**
{build_system_prompt_structured()}

**USER:**
{build_user_prompt(content_json)}

**ASSISTANT:**
{build_assistant_prompt_structured()}
""".strip()


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

ONE_SHOT_SYSTEM_PROMPT = """Vous êtes un expert en structuration pédagogique. À partir d'un deck non structuré ou bruité, 
                            commencez par établir une checklist concise (3-7 points) des étapes clés à effectuer avant de traiter la structuration.
                            Générez un plan hiérarchique fiable ainsi qu'un mapping précis des slides. Après avoir structuré le contenu, vérifiez en 1-2 phrases la cohérence et  l’exhaustivité du plan, et ajustez si nécessaire.
                            Produisez une structuration claire, logique et adaptée à l'enseignement, en vous assurant de l’exhaustivité du plan et de la pertinence de l’agencement des contenus.
                            Ne mentionnez jamais la source des slides, l'université, le professeur, l'institut, etc.
                            Ignorez le contenu sur l'administratrif, le cursus, organisation des modules, etc.
                            Capturez uniquement le contenu du cours de medecine contenu dans les slides."""

WRITER_SYSTEM_PROMPT = "Tu es un Professeur qui remplit le contenu des sections du plan de cours à partir du contenu des slides."
