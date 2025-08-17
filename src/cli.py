"""
Command Line Interface for Class Parser
Automatically detects Branch A (with plan) or Branch B (no plan)
"""

import argparse
import logging

# Load environment variables at the top of the CLI module
import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Get the project root directory (parent of src)
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"

# Load environment variables
load_dotenv(env_path)

from .data_extraction import PlanExtractor, SlidesExtractor
from .models import CourseMetadata
from .pipeline import CoursePipeline

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Set our package to appropriate level
    logging.getLogger("src").setLevel(level)


def detect_branch_and_process(
    slides_pdf: Path,
    plan_pdf: Optional[Path] = None,
    plan_page: Optional[int] = None,
    metadata: CourseMetadata = CourseMetadata(name="Generated Course", subject="Biology"),
    save_json: bool = False,
    save_docx: bool = False,
    template_path: str = "volume/fs_template.docx",
    model: str = "gpt-5-mini",
) -> None:
    """
    Automatically detect branch and process course
    
    Args:
        slides_pdf: Path to PDF containing slides
        plan_pdf: Optional path to PDF containing plan (Branch A)
        plan_page: Optional specific page number in slides_pdf to use as plan
        course_name: Name of the course
        subject: Subject area
        year: Academic year
        professor: Professor name

        model: OpenAI model to use
    """
    # Initialize pipeline
    pipeline = CoursePipeline(model=model)
    
    # Extract slides
    logger.info("📄 Extracting slides from %s", slides_pdf)
    slides_extractor = SlidesExtractor()
    slides = slides_extractor.extract_slides(str(slides_pdf))
    logger.info("✅ Extracted %d slides", len(slides))
    
    # Determine branch and extract plan if needed
    plan_text = None
    branch = "B"  # Default to Branch B (no plan)
    
    if plan_pdf:
        # Branch A: Separate plan PDF provided
        logger.info("📋 Plan PDF provided, using Branch A (two-pass)")
        plan_extractor = PlanExtractor()
        plan_text = plan_extractor.extract_plan_from_pdf(str(plan_pdf))
        branch = "A"
        logger.info("✅ Extracted plan from separate PDF (%d chars)", len(plan_text))
        
    elif plan_page:
        # Branch A: Specific page in slides PDF is the plan
        logger.info("📋 Plan page specified, using Branch A (two-pass)")
        plan_extractor = PlanExtractor()
        plan_text = plan_extractor.extract_plan_from_page(str(slides_pdf), plan_page)
        branch = "A"
        logger.info("✅ Extracted plan from page %d (%d chars)", plan_page, len(plan_text))
    
    else:
        # Branch B: No plan provided
        logger.info("🤖 No plan provided, using Branch B (one-shot)")
    
    # Process course using appropriate branch
    if branch == "A":
        assert plan_text is not None  # We know it's not None in Branch A
        course = pipeline.process_course_with_plan(
            slides=slides,
            plan_text=plan_text,
            metadata=metadata,
            save_json=save_json,
            save_docx=save_docx,
            template_path=template_path,
        )
    else:
        course = pipeline.process_course_no_plan(
            slides=slides,
            metadata=metadata,
            save_json=save_json,
            save_docx=save_docx,
            template_path=template_path,
        )
    
    # Show statistics
    stats = pipeline.get_processing_statistics(course)
    logger.info("📊 Processing complete!")
    logger.info("   - Branch: %s", branch)
    logger.info("   - Slides processed: %d", stats["total_slides"])
    logger.info("   - Sections generated: %d", stats["total_sections"])
    
    # Print course content
    print("\n" + "="*80)
    print("GENERATED COURSE CONTENT")
    print("="*80)
    print(course.print_content())


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Class Parser - Generate structured course content from PDF slides",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Branch B (one-shot, no plan)
  python -m src.cli slides.pdf --course "Biology 101" --save-docx --save-json
  
  # Branch A (two-pass, with separate plan PDF)
  python -m src.cli slides.pdf --plan-pdf plan.pdf --course "Biology 101" --save-docx
  
  # Branch A (two-pass, plan is page 2 of slides PDF)
  python -m src.cli slides.pdf --plan-page 2 --course "Biology 101"
  
  # Full example with metadata
  python -m src.cli slides.pdf --plan-page 2 \\
    --course "Advanced Biology" --subject "Biology" \\
    --level L1 --semester S1 --block SANTE \\
    --year 2024 --professor "Dr. Smith" --save-docx --verbose
        """
    )
    
    # Required arguments
    parser.add_argument(
        "slides_pdf",
        type=Path,
        help="Path to PDF file containing slides"
    )
    
    # Plan options (mutually exclusive)
    plan_group = parser.add_mutually_exclusive_group()
    plan_group.add_argument(
        "--plan-pdf",
        type=Path,
        help="Path to separate PDF file containing course plan (Branch A)"
    )
    plan_group.add_argument(
        "--plan-page",
        type=int,
        help="Page number in slides PDF to use as plan (Branch A, 1-based)"
    )
    
    # Course metadata
    parser.add_argument(
        "--course",
        default="Generated Course",
        help="Course name (default: Generated Course)"
    )
    parser.add_argument(
        "--course-title",
        help="Display title to use in the document (default: same as --course)",
    )
    parser.add_argument(
        "--subject",
        default="Biology",
        help="Subject area (default: Biology)"
    )
    parser.add_argument("--level", help="Academic level (e.g., L1, L2, M1)")
    parser.add_argument("--block", help="Block name (e.g., SANTE)")
    parser.add_argument("--semester", help="Semester (e.g., S1, S2)")
    parser.add_argument("--chapter", help="Chapter identifier")
    parser.add_argument(
        "--year",
        type=int,
        help="Academic year"
    )
    parser.add_argument(
        "--professor",
        help="Professor name"
    )
    
    # Model options
    parser.add_argument(
        "--model",
        default="gpt-5-mini",
        help="OpenAI model to use (default: gpt-5-mini)"
    )
    # Output flags
    parser.add_argument(
        "--save-json",
        action="store_true",
        help="Save the resulting course as JSON under volume/artifacts",
    )
    parser.add_argument(
        "--save-docx",
        action="store_true",
        help="Export the resulting course to DOCX using the template",
    )
    parser.add_argument(
        "--template-path",
        default="volume/fs_template.docx",
        type=str,
        help="Path to the Word template to use for DOCX export",
    )
    
    # Logging
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Validate inputs
    if not args.slides_pdf.exists():
        logger.error("❌ Slides PDF not found: %s", args.slides_pdf)
        sys.exit(1)
    
    if args.plan_pdf and not args.plan_pdf.exists():
        logger.error("❌ Plan PDF not found: %s", args.plan_pdf)
        sys.exit(1)
    
    try:
        metadata = CourseMetadata(
            name=args.course,
            course_title=args.course_title or None,
            subject=args.subject or None,
            level=args.level or None,
            block=args.block or None,
            semester=args.semester or None,
            chapter=args.chapter or None,
            year=args.year or None,
            professor=args.professor or None,
        )

        detect_branch_and_process(
            slides_pdf=args.slides_pdf,
            plan_pdf=args.plan_pdf,
            plan_page=args.plan_page,
            metadata=metadata,
            save_json=args.save_json,
            save_docx=args.save_docx,
            template_path=args.template_path,
            model=args.model,
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error("❌ Processing failed: %s", str(e))
        if args.verbose:
            logger.exception("Full traceback:")
        sys.exit(1)


if __name__ == "__main__":
    main()
