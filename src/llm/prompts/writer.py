from __future__ import annotations

WRITER_SYSTEM_PROMPT = "Tu es un Professeur qui remplit le contenu des sections du plan de cours à partir du contenu des slides."


def build_system_prompt() -> str:
    return """Tu es un expert en rédaction pédagogique. Ta tâche est de transformer du contenu brut de slides en paragraphes de cours structurés.

Règles :
- Ne Mentione jamais la source des slides, l'université, le professeur, l'institut, etc.
- Traite TOUTES les sections du JSON (ne t'arrête pas à la première)
- Pour chaque section, synthétise tous les éléments content[] en 2-10 paragraphes cohérents
- Chaque paragraphe = maximum 10 phrases liées au titre de la section
- Conserve la structure JSON exacte (mêmes IDs, titres, ordre)
- Style académique fluide"""


def build_user_prompt(content_json: str) -> str:
    return content_json


def build_assistant_prompt() -> str:
    return """Voici un exemple de transformation attendue :

INPUT EXEMPLE:
```json
{...}
```

OUTPUT EXEMPLE:
```json
{...}
```

Maintenant traite le JSON fourni en suivant ce modèle :"""


def build_system_prompt_structured() -> str:
    return """Tu es un expert en rédaction pédagogique. Ta tâche est de transformer du contenu brut de slides en contenu de cours structuré et aéré.

Règles de formatage - UTILISE LA STRUCTURE :
- Privilégie les listes à puces (•) pour les énumérations, caractéristiques, étapes
- Utilise les listes numérotées (1., 2., 3.) pour les processus séquentiels
- Alterne entre paragraphes et listes pour aérer le texte
- Maximum 3-4 phrases par paragraphe
- Une liste = 2-6 éléments maximum

Syntaxe pour les listes dans le JSON :
- Liste à puces : commence par "• " (bullet + espace)
- Liste numérotée : commence par "1. ", "2. ", etc.
- Paragraphe normal : pas de préfixe spécial"""


def build_assistant_prompt_structured() -> str:
    return """Voici un exemple de transformation attendue avec formatage structuré :

INPUT EXEMPLE:
```json
{...}
```

OUTPUT EXEMPLE:
```json
{...}
```

Maintenant traite le JSON fourni en suivant ce modèle :"""


def build_prompt_fill_content_structured(content_json: str) -> str:
    return f"""
**SYSTEM:**
{build_system_prompt_structured()}

**USER:**
{build_user_prompt(content_json)}

**ASSISTANT:**
{build_assistant_prompt_structured()}
""".strip()


def build_prompt_fill_content(content_json: str) -> str:
    return f"""
**SYSTEM:**
{build_system_prompt()}

**USER:**
{build_user_prompt(content_json)}

**ASSISTANT:**
{build_assistant_prompt()}
""".strip()


# Optional role prompt kept for compatibility (one-shot system)
ONE_SHOT_SYSTEM_PROMPT = """Vous êtes un expert en structuration pédagogique. À partir d'un deck non structuré ou bruité, 
                            commencez par établir une checklist concise (3-7 points) des étapes clés à effectuer avant de traiter la structuration.
                            Générez un plan hiérarchique fiable ainsi qu'un mapping précis des slides. Après avoir structuré le contenu, vérifiez en 1-2 phrases la cohérence et  l’exhaustivité du plan, et ajustez si nécessaire.
                            Produisez une structuration claire, logique et adaptée à l'enseignement, en vous assurant de l’exhaustivité du plan et de la pertinence de l’agencement des contenus.
                            Ne mentionnez jamais la source des slides, l'université, le professeur, l'institut, etc.
                            Ignorez le contenu sur l'administratrif, le cursus, organisation des modules, etc.
                            Capturez uniquement le contenu du cours de medecine contenu dans les slides."""


