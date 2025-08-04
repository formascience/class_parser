#!/bin/bash

# Script pour créer la structure de données académique
# Basé sur le fichier academic_structure.yaml

set -e  # Arrêter en cas d'erreur

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
YAML_FILE="$SCRIPT_DIR/academic_structure.yaml"
BASE_DIR="$SCRIPT_DIR"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Fonction pour slugifier un titre (convertir en nom de dossier valide)
slugify() {
    local input="$1"
    # Convertir en minuscules, remplacer espaces par underscores, supprimer caractères spéciaux
    echo "$input" | tr '[:upper:]' '[:lower:]' | \
                    sed 's/[àáâãäå]/a/g' | \
                    sed 's/[èéêë]/e/g' | \
                    sed 's/[ìíîï]/i/g' | \
                    sed 's/[òóôõö]/o/g' | \
                    sed 's/[ùúûü]/u/g' | \
                    sed 's/[ç]/c/g' | \
                    sed 's/[^a-z0-9 ]//g' | \
                    sed 's/ /_/g' | \
                    sed 's/__*/_/g' | \
                    sed 's/^_\|_$//g'
}

# Fonction pour créer les métadonnées d'un cours
create_course_metadata() {
    local course_path="$1"
    local level_id="$2"
    local block_id="$3"
    local semester_id="$4"
    local subject_id="$5"
    local subject_label="$6"
    local ues="$7"
    local chapter_num="$8"
    local course_title="$9"
    
    local metadata_dir="$course_path/metadata"
    
    # course_info.json
    cat > "$metadata_dir/course_info.json" << EOF
{
  "academic_path": {
    "level": "$level_id",
    "block": "$block_id",
    "semester": "$semester_id",
    "subject": "$subject_id",
    "chapter": "CHAPITRE_$chapter_num",
    "course_title": "$course_title"
  },
  "ue_info": {
    "code": "$ues",
    "full_name": "$ues - $subject_label"
  },
  "professor": {
    "name": "",
    "email": "",
    "department": ""
  },
  "created_at": "$(date -Iseconds)",
  "last_modified": "$(date -Iseconds)",
  "version": "1.0"
}
EOF

    # processing_log.json
    cat > "$metadata_dir/processing_log.json" << EOF
{
  "steps": [
    {
      "step": "folder_creation",
      "timestamp": "$(date -Iseconds)",
      "status": "completed",
      "details": "Course folder structure created"
    }
  ]
}
EOF

    # timestamps.json
    cat > "$metadata_dir/timestamps.json" << EOF
{
  "folder_created": "$(date -Iseconds)",
  "last_upload": null,
  "last_processing": null,
  "last_generation": null
}
EOF
}

# Fonction pour créer un README dans chaque dossier de cours
create_course_readme() {
    local course_path="$1"
    local level_id="$2"
    local block_label="$3"
    local semester_label="$4" 
    local subject_label="$5"
    local ues="$6"
    local chapter_num="$7"
    local course_title="$8"
    
    cat > "$course_path/README.md" << EOF
# $course_title

## Informations du Cours

- **Niveau**: $level_id
- **Bloc**: $block_label
- **Semestre**: $semester_label
- **Matière**: $subject_label
- **UE**: $ues
- **Chapitre**: $chapter_num
- **Titre**: $course_title

## Structure des Dossiers

\`\`\`
├── inputs/
│   ├── slides/          # Fichiers PDF des diapositives
│   └── course_plan/     # Fichiers PDF du plan de cours
├── outputs/
│   ├── draft/           # Documents DOCX générés automatiquement
│   └── final/           # Documents DOCX finalisés par le professeur
├── metadata/
│   ├── course_info.json    # Informations du cours
│   ├── processing_log.json # Journal des traitements
│   └── timestamps.json     # Horodatage des étapes
└── temp/                # Fichiers temporaires de traitement
\`\`\`

## Utilisation

1. **Upload**: Placez vos fichiers PDF dans \`inputs/slides/\` et \`inputs/course_plan/\`
2. **Traitement**: Le système génère automatiquement le DOCX dans \`outputs/draft/\`
3. **Finalisation**: Corrigez et placez la version finale dans \`outputs/final/\`

## Métadonnées

Les métadonnées du cours sont automatiquement maintenues dans le dossier \`metadata/\`.
EOF
}

# Vérifier que yq est installé
check_yq() {
    if ! command -v yq &> /dev/null; then
        log_error "yq n'est pas installé. Installation en cours..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            if command -v brew &> /dev/null; then
                brew install yq
            else
                log_error "Homebrew n'est pas installé. Installez yq manuellement: https://github.com/mikefarah/yq"
                exit 1
            fi
        else
            log_error "Installez yq manuellement: https://github.com/mikefarah/yq"
            exit 1
        fi
    fi
}

# Fonction principale pour créer la structure
create_academic_structure() {
    log_info "Début de la création de la structure académique..."
    
    # Vérifier que le fichier YAML existe
    if [[ ! -f "$YAML_FILE" ]]; then
        log_error "Fichier YAML non trouvé: $YAML_FILE"
        exit 1
    fi
    
    # Créer le répertoire de base
    local base_path="$BASE_DIR/$(yq eval '.folder_structure.base_path' "$YAML_FILE")"
    mkdir -p "$base_path"
    
    # Créer les dossiers templates et archives
    mkdir -p "$BASE_DIR/data/templates/docx_templates"
    mkdir -p "$BASE_DIR/data/templates/processing_configs"
    mkdir -p "$BASE_DIR/data/archives/old_versions"
    
    log_info "Structure de base créée dans: $base_path"
    
    # Parcourir tous les niveaux
    local levels_count=$(yq eval '.academic_structure.levels | length' "$YAML_FILE")
    
    for ((level_idx=0; level_idx<levels_count; level_idx++)); do
        local level_id=$(yq eval ".academic_structure.levels[$level_idx].id" "$YAML_FILE")
        local level_label=$(yq eval ".academic_structure.levels[$level_idx].label" "$YAML_FILE")
        local blocks_count=$(yq eval ".academic_structure.levels[$level_idx].blocks | length" "$YAML_FILE")
        
        log_info "Traitement du niveau: $level_id ($level_label)"
        
        # Créer le dossier du niveau
        local level_path="$base_path/$level_id"
        mkdir -p "$level_path"
        
        # Parcourir tous les blocs
        for ((block_idx=0; block_idx<blocks_count; block_idx++)); do
            local block_id=$(yq eval ".academic_structure.levels[$level_idx].blocks[$block_idx].id" "$YAML_FILE")
            local block_label=$(yq eval ".academic_structure.levels[$level_idx].blocks[$block_idx].label" "$YAML_FILE")
            local semesters_count=$(yq eval ".academic_structure.levels[$level_idx].blocks[$block_idx].semesters | length" "$YAML_FILE")
            
            log_info "  Traitement du bloc: $block_id ($block_label)"
            
            # Créer le dossier du bloc
            local block_path="$level_path/$block_id"
            mkdir -p "$block_path"
            
            # Parcourir tous les semestres
            for ((semester_idx=0; semester_idx<semesters_count; semester_idx++)); do
                local semester_id=$(yq eval ".academic_structure.levels[$level_idx].blocks[$block_idx].semesters[$semester_idx].id" "$YAML_FILE")
                local semester_label=$(yq eval ".academic_structure.levels[$level_idx].blocks[$block_idx].semesters[$semester_idx].label" "$YAML_FILE")
                local subjects_count=$(yq eval ".academic_structure.levels[$level_idx].blocks[$block_idx].semesters[$semester_idx].subjects | length" "$YAML_FILE")
                
                log_info "    Traitement du semestre: $semester_id ($semester_label)"
                
                # Créer le dossier du semestre
                local semester_path="$block_path/$semester_id"
                mkdir -p "$semester_path"
                
                # Parcourir toutes les matières
                for ((subject_idx=0; subject_idx<subjects_count; subject_idx++)); do
                    local subject_id=$(yq eval ".academic_structure.levels[$level_idx].blocks[$block_idx].semesters[$semester_idx].subjects[$subject_idx].id" "$YAML_FILE")
                    local subject_label=$(yq eval ".academic_structure.levels[$level_idx].blocks[$block_idx].semesters[$semester_idx].subjects[$subject_idx].label" "$YAML_FILE")
                    local chapters_count=$(yq eval ".academic_structure.levels[$level_idx].blocks[$block_idx].semesters[$semester_idx].subjects[$subject_idx].chapters" "$YAML_FILE")
                    local ues=$(yq eval ".academic_structure.levels[$level_idx].blocks[$block_idx].semesters[$semester_idx].subjects[$subject_idx].ues[0]" "$YAML_FILE")
                    
                    log_info "      Traitement de la matière: $subject_id ($subject_label) - $chapters_count chapitres"
                    
                    # Créer le dossier de la matière
                    local subject_path="$semester_path/$subject_id"
                    mkdir -p "$subject_path"
                    
                    # Créer les chapitres (1 à chapters_count)
                    for ((chapter=1; chapter<=chapters_count; chapter++)); do
                        local chapter_id="CHAPITRE_$chapter"
                        local chapter_path="$subject_path/$chapter_id"
                        mkdir -p "$chapter_path"
                        
                        log_info "        Création du chapitre: $chapter_id"
                        
                        # Créer un exemple de cours pour certains chapitres
                        local example_course_title="Chapitre $chapter"
                        local course_slug=$(slugify "$example_course_title")
                        local course_path="$chapter_path/$course_slug"
                        
                        # Créer la structure des dossiers pour le cours
                        mkdir -p "$course_path/inputs/slides"
                        mkdir -p "$course_path/inputs/course_plan" 
                        mkdir -p "$course_path/outputs/draft"
                        mkdir -p "$course_path/outputs/final"
                        mkdir -p "$course_path/metadata"
                        mkdir -p "$course_path/temp"
                        
                        # Créer les métadonnées et README
                        create_course_metadata "$course_path" "$level_id" "$block_id" "$semester_id" "$subject_id" "$subject_label" "$ues" "$chapter" "$example_course_title"
                        create_course_readme "$course_path" "$level_id" "$block_label" "$semester_label" "$subject_label" "$ues" "$chapter" "$example_course_title"
                        
                        log_success "        ✓ Cours créé: $course_path"
                    done
                done
            done
        done
    done
}

# Fonction pour créer des exemples spécifiques
create_sample_courses() {
    log_info "Création des cours d'exemple spécifiques..."
    
    local create_samples=$(yq eval '.examples.create_sample_courses' "$YAML_FILE")
    
    if [[ "$create_samples" == "true" ]]; then
        local samples_count=$(yq eval '.examples.sample_courses | length' "$YAML_FILE")
        
        for ((sample_idx=0; sample_idx<samples_count; sample_idx++)); do
            local level_id=$(yq eval ".examples.sample_courses[$sample_idx].level_id" "$YAML_FILE")
            local block_id=$(yq eval ".examples.sample_courses[$sample_idx].block_id" "$YAML_FILE")
            local semester_id=$(yq eval ".examples.sample_courses[$sample_idx].semester_id" "$YAML_FILE")
            local subject_id=$(yq eval ".examples.sample_courses[$sample_idx].subject_id" "$YAML_FILE")
            local chapter=$(yq eval ".examples.sample_courses[$sample_idx].chapter" "$YAML_FILE")
            local course_title=$(yq eval ".examples.sample_courses[$sample_idx].course_title" "$YAML_FILE")
            
            local course_slug=$(slugify "$course_title")
            local base_path="$BASE_DIR/$(yq eval '.folder_structure.base_path' "$YAML_FILE")"
            local sample_path="$base_path/$level_id/$block_id/$semester_id/$subject_id/CHAPITRE_$chapter/$course_slug"
            
            # Si le cours n'existe pas déjà, le créer
            if [[ ! -d "$sample_path" ]]; then
                mkdir -p "$sample_path/inputs/slides"
                mkdir -p "$sample_path/inputs/course_plan"
                mkdir -p "$sample_path/outputs/draft"
                mkdir -p "$sample_path/outputs/final"
                mkdir -p "$sample_path/metadata"
                mkdir -p "$sample_path/temp"
                
                # Obtenir les informations de la matière
                local subject_label=""
                local ues=""
                local block_label=""
                local semester_label=""
                
                # Rechercher les labels dans le YAML (simplifié pour cet exemple)
                subject_label="Exemple de matière"
                ues="UE1"
                block_label="Exemple de bloc"
                semester_label="Exemple de semestre"
                
                create_course_metadata "$sample_path" "$level_id" "$block_id" "$semester_id" "$subject_id" "$subject_label" "$ues" "$chapter" "$course_title"
                create_course_readme "$sample_path" "$level_id" "$block_label" "$semester_label" "$subject_label" "$ues" "$chapter" "$course_title"
                
                log_success "✓ Cours d'exemple créé: $sample_path"
            fi
        done
    fi
}

# Fonction pour afficher un résumé
show_summary() {
    log_info "Résumé de la structure créée:"
    
    local base_path="$BASE_DIR/$(yq eval '.folder_structure.base_path' "$YAML_FILE")"
    
    echo ""
    echo "📊 Statistiques:"
    echo "  • Niveaux: $(find "$base_path" -maxdepth 1 -type d | wc -l | tr -d ' ')"
    echo "  • Blocs: $(find "$base_path" -maxdepth 2 -type d -name "BLOC_*" | wc -l | tr -d ' ')"
    echo "  • Semestres: $(find "$base_path" -maxdepth 3 -type d -name "S*" | wc -l | tr -d ' ')"
    echo "  • Matières: $(find "$base_path" -mindepth 4 -maxdepth 4 -type d | wc -l | tr -d ' ')"
    echo "  • Chapitres: $(find "$base_path" -mindepth 5 -maxdepth 5 -type d -name "CHAPITRE_*" | wc -l | tr -d ' ')"
    echo "  • Cours: $(find "$base_path" -mindepth 6 -maxdepth 6 -type d | wc -l | tr -d ' ')"
    echo ""
    
    log_success "Structure académique créée avec succès!"
    log_info "Base de données: $base_path"
    log_info "Documentation: $SCRIPT_DIR/data_structure.md"
}

# Fonction principale
main() {
    echo "🎓 Générateur de Structure Académique"
    echo "====================================="
    echo ""
    
    # Vérifier les prérequis
    check_yq
    
    # Créer la structure
    create_academic_structure
    
    # Créer les exemples
    create_sample_courses
    
    # Afficher le résumé
    show_summary
}

# Options de ligne de commande
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Afficher cette aide"
        echo "  --clean        Nettoyer la structure existante avant création"
        echo "  --dry-run      Afficher ce qui serait créé sans le faire"
        echo ""
        exit 0
        ;;
    --clean)
        log_warning "Nettoyage de la structure existante..."
        rm -rf "$BASE_DIR/data/courses"
        log_success "Structure nettoyée!"
        main
        ;;
    --dry-run)
        log_info "Mode dry-run activé (simulation uniquement)"
        # TODO: Implémenter le mode dry-run
        ;;
    *)
        main
        ;;
esac 