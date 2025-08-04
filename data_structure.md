# Structure de Données pour le Workflow Académique

## Vue d'ensemble

Cette structure de dossiers reflète la hiérarchie académique définie dans `frontend/src/config/academicStructure.ts` et organise le workflow de traitement des cours de la faculté de médecine.

## Hiérarchie Académique

```
Niveau (L1, L2, L3, M1, M2)
├── Bloc (Santé, Transversal, Disciplinaire)
    ├── Semestre (S1, S2)
        ├── Matière (ex: Chimie, Mathématiques)
            ├── Chapitre (1-9)
                ├── Titre du cours (personnalisé)
```

## Structure des Dossiers

### Arborescence Principale

```
data/
├── courses/
│   ├── L1/                           # Niveau
│   │   ├── BLOC_SANTE/              # Bloc
│   │   │   ├── S1/                  # Semestre
│   │   │   │   ├── CONSTITUTION_MATIERE/  # Matière
│   │   │   │   │   ├── CHAPITRE_9/        # Chapitre
│   │   │   │   │   │   ├── introduction_concepts_fondamentaux/  # Titre du cours (slug)
│   │   │   │   │   │   │   ├── inputs/
│   │   │   │   │   │   │   │   ├── slides/
│   │   │   │   │   │   │   │   │   ├── *.pdf
│   │   │   │   │   │   │   │   └── course_plan/
│   │   │   │   │   │   │   │       └── *.pdf
│   │   │   │   │   │   │   ├── outputs/
│   │   │   │   │   │   │   │   ├── draft/
│   │   │   │   │   │   │   │   │   └── generated_course.docx
│   │   │   │   │   │   │   │   └── final/
│   │   │   │   │   │   │   │       └── corrected_course.docx
│   │   │   │   │   │   │   ├── metadata/
│   │   │   │   │   │   │   │   ├── course_info.json
│   │   │   │   │   │   │   │   ├── processing_log.json
│   │   │   │   │   │   │   │   └── timestamps.json
│   │   │   │   │   │   │   └── temp/
│   │   │   │   │   │   │       └── processing_files/
├── templates/
│   ├── docx_templates/
│   └── processing_configs/
└── archives/
    └── old_versions/
```

## Description des Dossiers

### 📂 `courses/`
Contient tous les cours organisés par hiérarchie académique.

### 📂 `inputs/`
**Fichiers d'entrée fournis par les professeurs**
- `slides/` : Fichiers PDF des diapositives du cours
- `course_plan/` : Fichiers PDF du plan du cours

### 📂 `outputs/`
**Fichiers générés par le système**
- `draft/` : Document DOCX généré automatiquement par l'IA
- `final/` : Document DOCX corrigé et finalisé par le professeur

### 📂 `metadata/`
**Informations de traitement et métadonnées**
- `course_info.json` : Informations du cours (titre, UE, professeur, etc.)
- `processing_log.json` : Journal des traitements effectués
- `timestamps.json` : Horodatage des différentes étapes

### 📂 `temp/`
**Fichiers temporaires de traitement**
- Fichiers intermédiaires générés pendant le processing
- Nettoyés automatiquement après traitement

### 📂 `templates/`
**Modèles et configurations**
- `docx_templates/` : Modèles DOCX pour la génération
- `processing_configs/` : Configurations de traitement par matière

### 📂 `archives/`
**Archivage des anciennes versions**
- Sauvegarde des versions précédentes des cours

## Format des Fichiers Métadonnées

### `course_info.json`
```json
{
  "academic_path": {
    "level": "L1",
    "block": "BLOC_SANTE",
    "semester": "S1",
    "subject": "CONSTITUTION_MATIERE",
    "chapter": "CHAPITRE_9",
    "course_title": "Introduction aux concepts fondamentaux"
  },
  "ue_info": {
    "code": "UE1",
    "full_name": "UE1 - Constitution et transformation de la matière"
  },
  "professor": {
    "name": "",
    "email": "",
    "department": ""
  },
  "created_at": "2024-01-XX",
  "last_modified": "2024-01-XX",
  "version": "1.0"
}
```

### `processing_log.json`
```json
{
  "steps": [
    {
      "step": "upload",
      "timestamp": "2024-01-XX 10:00:00",
      "files": ["slides_1.pdf", "plan_cours.pdf"],
      "status": "completed"
    },
    {
      "step": "pdf_extraction",
      "timestamp": "2024-01-XX 10:01:00",
      "input_files": ["slides_1.pdf"],
      "output_files": ["extracted_text.txt"],
      "status": "completed"
    },
    {
      "step": "docx_generation",
      "timestamp": "2024-01-XX 10:05:00",
      "input_files": ["extracted_text.txt", "course_plan.pdf"],
      "output_files": ["generated_course.docx"],
      "status": "completed"
    }
  ]
}
```

## Conventions de Nommage

### Slugification des Titres
Les titres de cours sont convertis en slugs pour les noms de dossiers :
- "Introduction aux concepts fondamentaux" → `introduction_concepts_fondamentaux`
- Caractères spéciaux supprimés, espaces remplacés par des underscores
- Tout en minuscules pour la cohérence

### Nommage des Fichiers
- **Slides** : `slides_[numero].pdf` (ex: `slides_1.pdf`, `slides_2.pdf`)
- **Plan de cours** : `course_plan_[description].pdf` (ex: `course_plan_chapitre9.pdf`)
- **Draft généré** : `generated_course_[version].docx` (ex: `generated_course_v1.docx`)
- **Version finale** : `final_course_[version].docx` (ex: `final_course_v1.docx`)

## Utilisation avec le Frontend

Le frontend de téléversement utilise cette structure pour :
1. **Déterminer le chemin** basé sur les sélections des dropdowns
2. **Créer les dossiers** automatiquement si nécessaire
3. **Organiser les uploads** dans les bons répertoires
4. **Suivre le statut** des traitements via les métadonnées

## Avantages de cette Structure

- ✅ **Hiérarchie claire** : Reflète exactement la structure académique
- ✅ **Évolutivité** : Facile d'ajouter de nouveaux niveaux/matières
- ✅ **Traçabilité** : Métadonnées complètes sur chaque traitement
- ✅ **Maintenance** : Séparation claire des inputs/outputs/temporaires
- ✅ **Archivage** : Gestion des versions et historique
- ✅ **Performance** : Structure optimisée pour l'accès et la recherche 