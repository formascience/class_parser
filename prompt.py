def build_system_prompt() -> str:
    """
    Prompt système définissant le rôle et les règles
    """
    return """Tu es un expert en rédaction pédagogique. Ta tâche est de transformer du contenu brut de slides en paragraphes de cours structurés.

Règles :
- Traite TOUTES les sections du JSON (ne t'arrête pas à la première)
- Pour chaque section, synthétise tous les éléments content[] en 2-5 paragraphes cohérents
- Chaque paragraphe = 2-4 phrases liées au titre de la section
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


def build_prompt_fill_content(
    content_json: str
) -> str:
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


def build_prompt_fill_content_debug(
    content_json: str
) -> str:
    """
    Version debug pour diagnostiquer pourquoi le modèle ne traite qu'une section
    """
    return f"""
DIAGNOSTIC - Analysez ce JSON et dites-moi exactement ce que vous voyez :

{content_json}

Questions de diagnostic :
1. Combien de sections principales voyez-vous dans le tableau sections[] ?
2. Quels sont leurs IDs ? (SEC_1, SEC_2, etc.)
3. Quels sont leurs titres ?
4. Y a-t-il des sous-sections dans chaque section ?

Répondez seulement à ces questions sans traiter le contenu.
""".strip()


