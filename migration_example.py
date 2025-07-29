"""
Migration Example: From Script-based to OOP Approach
"""

# OLD WAY (from parsed_pdf_api_calls.py and pdf_to_dict.py):
# --------------------------------------------------------------

# # Step 1: Manual PDF processing
# PDF = "./volume/slides/cours_1.pdf"
# deck = extract_lines(PDF)
# slides = split_bullets(deck)
# trees = [bullet_tree(sl) for sl in slides]
# course_plan = trees[1]
# trees.pop(1)
# course_content = trees

# # Step 2: Manual API calls  
# client = OpenAI()
# # Phase 1
# result_p1 = client.responses.parse(
#     model="gpt-4.1-2025-04-14",
#     input=[...],
#     text_format=Content,
# )
# outline = result_p1.output_parsed

# # Phase 2
# result2 = client.responses.parse(
#     model="gpt-4.1-2025-04-14", 
#     input=[...],
#     text_format=Content,
# )
# course_draft = result2.output_parsed

# # Step 3: Manual course creation and export
# cours_1 = Course(
#     name="Les molécules du vivant",
#     subject="Biologie",
#     year=2025,
#     professor="Professeur 1",
# )
# cours_1.content = course_draft
# cours_1.export_to_docx()


# NEW WAY (OOP Approach):
# --------------------------------------------------------------

from pdf_extractor import CoursePipeline

def new_approach():
    """Same workflow but with clean OOP structure"""
    
    # Initialize pipeline - handles all the complex setup
    pipeline = CoursePipeline()
    
    # Single method call does everything:
    # - PDF extraction and processing
    # - Two-phase AI content generation  
    # - Course creation and DOCX export
    course = pipeline.process_course(
        pdf_filename="cours_1.pdf",  # Will look in volume/slides/
        course_name="Les molécules du vivant",
        subject="Biologie", 
        year=2025,
        professor="Professeur 1"
    )
    
    return course

def advanced_usage():
    """More advanced usage examples"""
    
    pipeline = CoursePipeline()
    
    # Example 1: Custom volume directory
    pipeline.set_volume_directory("my_custom_volume")
    
    # Example 2: Process from full path
    course = pipeline.process_course_from_path(
        pdf_path="/path/to/my/course.pdf",
        course_name="Advanced Biology",
        output_filename="my_custom_output.docx"
    )
    
    # Example 3: Check available PDFs
    available_pdfs = pipeline.get_available_pdfs()
    print("Available PDFs:", available_pdfs)
    
    # Example 4: Access individual components if needed
    pdf_processor = pipeline.pdf_processor
    content_generator = pipeline.content_generator
    
    # You can still use them individually for custom workflows
    course_plan, course_content = pdf_processor.process_pdf("my_file.pdf")
    
    return course

if __name__ == "__main__":
    print("🚀 Running new OOP approach...")
    try:
        course = new_approach()
        print(f"✅ Success! Generated course: {course.name}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🔧 Advanced usage examples...")
    advanced_usage() 