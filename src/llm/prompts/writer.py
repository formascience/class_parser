from __future__ import annotations

WRITER_SYSTEM_PROMPT = "Tu es un Professeur qui remplit le contenu des sections du plan de cours à partir du contenu des slides."


def build_user_prompt(content_json: str) -> str:
    return content_json


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
{
  "sections": [
    {
      "id": "SEC_2",
      "title": "Glycolyse : étapes et régulation",
      "content": [
        "Phase préparatoire\n- Glucose → G6P (hexokinase)\n- G6P → F6P (phosphoglucose isomérase)\n- F6P → F1,6BP (phosphofructokinase)\nConsomme 2 ATP",
        "Phase de gain énergétique\nG3P → 1,3BPG → 3PG → 2PG → PEP → Pyruvate\nProduction nette : 2 ATP + 2 NADH",
        "Régulation allostérique\nPFK = enzyme clé\nInhibition : ATP, citrate\nActivation : AMP, ADP, Pi"
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
      "id": "SEC_2",
      "title": "Glycolyse : étapes et régulation", 
      "content": [
        "La glycolyse se déroule en deux phases distinctes aux rôles complémentaires. La phase préparatoire transforme le glucose en intermédiaires phosphorylés par une série de réactions enzymatiques spécialisées :",
        
        "• Phosphorylation du glucose en glucose-6-phosphate par l'hexokinase",
        "• Isomérisation en fructose-6-phosphate par la phosphoglucose isomérase", 
        "• Phosphorylation en fructose-1,6-bisphosphate par la phosphofructokinase",
        
        "Cette phase initiale consomme 2 molécules d'ATP par glucose métabolisé, constituant un investissement énergétique nécessaire.",
        
        "La phase de gain énergétique génère les bénéfices énergétiques de la voie glycolytique. Les transformations successives du glycéraldéhyde-3-phosphate conduisent à la formation de pyruvate selon la séquence suivante :",
        
        "1. Oxydation et phosphorylation en 1,3-bisphosphoglycérate",
        "2. Transfert du phosphate vers l'ADP (formation d'ATP)", 
        "3. Isomérisation et déshydratation jusqu'au phosphoénolpyruvate",
        "4. Seconde phosphorylation au niveau du substrat (formation d'ATP)",
        
        "Le bilan net de cette phase est la production de 2 ATP et 2 NADH par molécule de glucose.",
        
        "La régulation de la glycolyse s'exerce principalement au niveau de la phosphofructokinase, enzyme limitante de la voie. Cette régulation allostérique répond aux besoins énergétiques cellulaires : l'ATP et le citrate exercent une inhibition négative tandis que l'AMP, l'ADP et le phosphate inorganique activent l'enzyme."
      ],
      "subsections": []
    }
  ]
}
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

