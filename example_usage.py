"""
Example usage of the OOP course processing pipeline
"""

from pdf_extractor import CoursePipeline

def main():
    pipeline = CoursePipeline()
    # Example 1: Process a PDF from volume/slides/ directory
    try:
        course = pipeline.process_course(
            pdf_filename="cours_1.pdf",
            course_name="Les molécules du vivant",
            subject="Biologie",
            year=2025,
            professor="Professeur 1"
        )
        print(f"✅ Course '{course.name}' processed successfully!")
        print(f"📊 Total sections: {len(course.content.sections)}")
        print(f"📄 Total slides: {course.total_slides}")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("Available PDFs:", pipeline.get_available_pdfs())
    
    # Example 2: Process a PDF from full path
    try:
        course2 = pipeline.process_course_from_path(
            pdf_path="./cours_1_first_10_slides.pdf",  # Full path
            course_name="Introduction to Biology",
            subject="Biology"
        )
        print(f"✅ Course '{course2.name}' processed successfully!")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 