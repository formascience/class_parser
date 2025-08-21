"""
FastAPI web interface for CoursePipeline - No Plan processing only
"""

import logging
import os
import tempfile
from typing import Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .data_extraction import SlidesExtractor
from .models import CourseMetadata
from .course import Course
from .pipeline import CoursePipeline

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Course Parser API",
    description="Generate structured course content from PDF slides",
    version="1.0.0"
)

# CORS configuration for local development (Vite dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Response Model
class ProcessingResponse(BaseModel):
    status: str
    course_name: str
    slides_processed: int
    sections_generated: int
    message: str

# Dependency to parse form data into CourseMetadata
async def parse_course_metadata(
    course_title: str = Form(..., description="Course title"),
    subject: str = Form(..., description="Subject area"), 
    block: str = Form(..., description="Academic block (e.g., SANTE, TRANSVERSAL)"),
    chapter: str = Form(..., description="Chapter or section"),
    name: Optional[str] = Form(None, description="Course name"),
    level: Optional[str] = Form(None, description="Academic level (e.g., L1, L2)"),
    semester: Optional[str] = Form(None, description="Semester (e.g., S1, S2)")
) -> CourseMetadata:
    """Parse form fields into CourseMetadata object"""
    return CourseMetadata(
        name=name,
        course_title=course_title,
        level=level,
        block=block,
        semester=semester,
        subject=subject,
        chapter=chapter
    )

# Helper functions
async def save_upload_to_temp(upload: UploadFile) -> str:
    """Save uploaded file to temporary location and return path"""
    if not upload.filename or not upload.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        content = await upload.read()
        tmp_file.write(content)
        tmp_file.flush()
        logger.info(f"Saved uploaded file to: {tmp_file.name}")
        return tmp_file.name

def cleanup_temp_file(file_path: str):
    """Remove temporary file"""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
            logger.info(f"Cleaned up temp file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup temp file {file_path}: {e}")



# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Course Parser API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/api/v1/courses/process/no-plan")
async def process_course_no_plan(
    metadata: CourseMetadata = Depends(parse_course_metadata),
    slides_file: UploadFile = File(..., description="PDF file containing course slides")
):
    """
    Process course slides without a plan using one-shot approach (Branch B)
    
    - **slides_file**: PDF file with course slides
    - **metadata**: Course metadata using existing CourseMetadata model
    """
    temp_slides_path = None
    
    try:
        logger.info(f"Starting course processing: {metadata.course_title}")
        
        # Step 1: Save uploaded file to temp location
        temp_slides_path = await save_upload_to_temp(slides_file)
        
        # Step 2: Extract slides from PDF
        logger.info("Extracting slides from PDF...")
        slides_extractor = SlidesExtractor()
        slides = slides_extractor.extract_slides(temp_slides_path)
        logger.info(f"Extracted {len(slides)} slides")
        
        if not slides:
            raise HTTPException(
                status_code=400, 
                detail="No valid slides found in the PDF. Please check the file format."
            )
        
        # Step 3: Process with pipeline (now save docx for download)
        logger.info("Processing course with pipeline...")
        pipeline = CoursePipeline()
        course, docx_path, docx_filename = pipeline.process_course_no_plan(
            slides=slides,
            metadata=metadata,
            save_json=True,   # Save JSON to volume/artifacts/json/
            save_docx=True,   # Now save docx for download
            template_path="volume/templates/fs_template.docx",  # Static options
            output_path="volume/artifacts",  # Will save to volume/artifacts/json/ and docx/
            test_mode=False,   # Static options
        )
        
        # Step 4: Get processing statistics
        stats = pipeline.get_processing_statistics(course)
        
        logger.info(f"Course processing completed successfully: {course.name}")
        logger.info("JSON and DOCX files saved to volume/artifacts/")

        #course = Course.load_from_json("volume/artifacts/json/code_genetique_et_traduction_20250820_221143.json")

        #docx_path, docx_filename = course.to_docx(template_path="volume/templates/fs_template.docx", output_path="volume/artifacts/docx")

        # Check if the docx_path from pipeline exists
        if not docx_path or not os.path.exists(docx_path):
            raise HTTPException(
                status_code=500,
                detail="Generated DOCX file not found after processing"
            )

        # Check if the file exists in the docx_path
        if not docx_filename or not docx_path or not os.path.exists(f"{docx_path}/{docx_filename}"):
            raise HTTPException(
                status_code=500,
                detail="Generated DOCX file not found after processing"
            )

        full_path = f"{docx_path}/{docx_filename}"

        logger.info(f"Returning generated docx file: {full_path}")

        
        
        # Return the generated docx file for download
        return FileResponse(
            path=full_path,
            filename=docx_filename,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={docx_filename}"}
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Course processing failed: {str(e)}"
        )
        
    finally:
        if temp_slides_path:
            cleanup_temp_file(temp_slides_path)

@app.post("/api/v1/courses/process/test")
async def process_course_test(
    metadata: CourseMetadata = Depends(parse_course_metadata),
    slides_file: UploadFile = File(..., description="PDF file containing course slides")
):
    """
    Test route that accepts PDF and returns a fake response with the existing docx file
    
    - **slides_file**: PDF file with course slides (for testing connection)
    - **metadata**: Course metadata
    """
    temp_slides_path = None
    
    try:
        logger.info(f"Test route called with course: {metadata.course_title}")
        
        # Save uploaded file to temp (just to validate it's a PDF)
        temp_slides_path = await save_upload_to_temp(slides_file)
        
        # Path to the existing docx file in class_parser root
        docx_path = "/Users/youssefjanjar/Documents/formascience/class_parser/Chapitre_5_transcription,_maturation_et_régulation_de_l'adn.docx"
        
        if not os.path.exists(docx_path):
            raise HTTPException(
                status_code=404,
                detail="Test docx file not found"
            )
        
        logger.info(f"Test route completed successfully, returning docx file")
        
        # Return the docx file for download
        return FileResponse(
            path=docx_path,
            filename="test_output.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": "attachment; filename=test_output.docx"}
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Test processing failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Test route failed: {str(e)}"
        )
        
    finally:
        if temp_slides_path:
            cleanup_temp_file(temp_slides_path)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
