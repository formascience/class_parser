from __future__ import annotations

import json
from typing import List

from ...models import Slides


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


# Optional system prompt related to one-shot flows (kept for compatibility)
ONE_SHOT_SYSTEM_PROMPT = """Vous êtes un expert en structuration pédagogique. À partir d'un deck non structuré ou bruité, 
                            commencez par établir une checklist concise (3-7 points) des étapes clés à effectuer avant de traiter la structuration.
                            Générez un plan hiérarchique fiable ainsi qu'un mapping précis des slides. Après avoir structuré le contenu, vérifiez en 1-2 phrases la cohérence et  l’exhaustivité du plan, et ajustez si nécessaire.
                            Produisez une structuration claire, logique et adaptée à l'enseignement, en vous assurant de l’exhaustivité du plan et de la pertinence de l’agencement des contenus.
                            Ne mentionnez jamais la source des slides, l'université, le professeur, l'institut, etc.
                            Ignorez le contenu sur l'administratrif, le cursus, organisation des modules, etc.
                            Capturez uniquement le contenu du cours de medecine contenu dans les slides."""


