"""
Job Application Form Filling API
================================

🎯 LEARNING OBJECTIVES:
This demo teaches you how to build an AI agent system for form automation:

1. Document parsing - Extract structured data from PDF resumes
2. Agent-based form filling - AI agents automatically fill forms
3. Real-time streaming - Stream form filling progress for better UX
4. Structured data extraction - Using LLMs to extract structured data

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Setup - Import libraries and configure the router
Step 2: Data Models - Define request structures with validation
Step 3: Resume Parsing - Extract structured data from PDFs
Step 4: Form Filling Agent - Intelligently fill form fields
Step 5: API Endpoints - Expose functionality via HTTP

Key Concept: This demo shows how AI agents can automate form completion
by parsing unstructured documents and intelligently mapping data to form fields.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, AsyncGenerator
import uuid
import logging
import asyncio
import json
import tempfile
import os
import shutil

from .models import (
    ResumeData, ResumeUploadResponse, FormStructure, FormFillResponse,
    FormField, JobListing
)
from .resume_parser import parse_resume_pdf
from .form_agent import fill_form_from_resume, set_progress_callback
from .html_parser import parse_html_form

logger = logging.getLogger(__name__)

# Create a router - groups all endpoints under /job-application-form-filling
router = APIRouter(prefix="/job-application-form-filling", tags=["job-application-form-filling"])

# In-memory storage for sessions
sessions: Dict[str, Dict[str, Any]] = {}


# ============================================================================
# STEP 2: DATA MODELS
# ============================================================================
class ServiceInfo(BaseModel):
    """Health check response"""
    status: str
    service: str
    description: str


# ============================================================================
# STEP 3: HELPER FUNCTIONS
# ============================================================================
def _get_job_listing_data() -> JobListing:
    """Get the job listing data"""
    return JobListing(
        job_title="Senior Software Engineer - AI/ML",
        company="TechCorp Innovations",
        location="San Francisco, CA (Remote Available)",
        description="""
We are looking for an experienced Software Engineer to join our AI/ML team. 
You will work on cutting-edge AI applications, build scalable systems, and 
collaborate with a talented team of engineers and researchers.

Key Responsibilities:
- Design and develop AI/ML applications and services
- Build scalable backend systems using modern technologies
- Collaborate with cross-functional teams
- Write clean, maintainable, and well-documented code
- Participate in code reviews and technical discussions
        """.strip(),
        requirements=[
            "5+ years of software engineering experience",
            "Strong proficiency in Python, JavaScript, or similar languages",
            "Experience with AI/ML frameworks (TensorFlow, PyTorch, etc.)",
            "Knowledge of cloud platforms (AWS, GCP, Azure)",
            "Excellent problem-solving and communication skills",
            "Bachelor's degree in Computer Science or related field"
        ],
        benefits=[
            "Competitive salary and equity package",
            "Comprehensive health, dental, and vision insurance",
            "Flexible work hours and remote work options",
            "Professional development budget",
            "401(k) with company matching",
            "Unlimited PTO"
        ],
        application_instructions="Please upload your resume and complete the application form. Our AI system will help pre-fill your information."
    )


# ============================================================================
# STEP 4: STREAMING FORM FILLING
# ============================================================================
async def stream_form_filling(
    session_id: str,
    form_structure: FormStructure
) -> AsyncGenerator[str, None]:
    """Stream form filling updates in real-time"""
    try:
        logger.info(f"Starting stream_form_filling for session: {session_id}")
        
        if session_id not in sessions:
            logger.error(f"Session not found: {session_id}")
            yield f"data: {json.dumps({'error': 'Session not found', 'status': 'error'})}\n\n"
            return
        
        session = sessions[session_id]
        resume_data = session.get("resume_data")
        
        if not resume_data:
            logger.error(f"Resume data not found for session: {session_id}")
            yield f"data: {json.dumps({'error': 'Resume data not found', 'status': 'error'})}\n\n"
            return
        
        logger.info(f"Found resume data for session: {session_id}")
        
        # Convert dict to ResumeData model
        try:
            resume_data_obj = ResumeData(**resume_data)
            logger.info(f"Parsed resume data: {resume_data_obj.name}")
        except Exception as e:
            logger.error(f"Error parsing resume data: {e}", exc_info=True)
            yield f"data: {json.dumps({'error': f'Invalid resume data: {str(e)}', 'status': 'error'})}\n\n"
            return
        
        if not form_structure or not form_structure.fields:
            logger.error("No form structure or fields provided")
            yield f"data: {json.dumps({'error': 'No form structure provided', 'status': 'error'})}\n\n"
            return
        
        logger.info(f"Form structure has {len(form_structure.fields)} fields")
        
        # Set up progress callback
        step_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        processing_complete = asyncio.Event()
        
        def update_progress(progress_data: Dict[str, Any]):
            """Update session and queue step for streaming"""
            try:
                step_queue.put_nowait(progress_data)
                logger.debug(f"Progress update: {progress_data.get('message', '')}")
            except Exception as e:
                logger.warning(f"Error queuing progress: {e}")
        
        set_progress_callback(update_progress)
        
        # Start form filling in background
        async def run_filling():
            try:
                logger.info("Starting fill_form_from_resume...")
                async for update in fill_form_from_resume(resume_data_obj, form_structure):
                    logger.debug(f"Form filling update: {update.get('field_name', 'general')}")
                    step_queue.put_nowait(update)
                logger.info("Form filling completed successfully")
                processing_complete.set()
            except Exception as e:
                logger.error(f"Error in form filling: {e}", exc_info=True)
                step_queue.put_nowait({
                    "error": str(e),
                    "status": "error",
                    "message": f"Error filling form: {str(e)}"
                })
                processing_complete.set()
            finally:
                set_progress_callback(None)
        
        # Start filling task
        filling_task = asyncio.create_task(run_filling())
        logger.info("Form filling task started")
        
        # Stream initial connection
        yield f"data: {json.dumps({'status': 'connected', 'message': 'Starting form filling...', 'session_id': session_id}, ensure_ascii=False)}\n\n"
        
        # Stream updates
        filled_fields = []
        while not processing_complete.is_set():
            try:
                try:
                    update = await asyncio.wait_for(step_queue.get(), timeout=0.1)
                    
                    # Handle done signal
                    if update.get("done"):
                        # Store filled fields in session (convert to dict for storage)
                        filled_fields_dict = [field.dict() for field in filled_fields]
                        session["filled_fields"] = filled_fields_dict
                        session["status"] = "completed"
                        
                        yield f"data: {json.dumps({'done': True, 'status': 'completed', 'message': 'Form filled successfully', 'filled_fields': filled_fields_dict}, ensure_ascii=False)}\n\n"
                        break
                    
                    # Handle error
                    if update.get("error"):
                        yield f"data: {json.dumps({'error': update.get('error'), 'status': 'error'}, ensure_ascii=False)}\n\n"
                        break
                    
                    # Handle field update
                    if update.get("field_name"):
                        field = FormField(
                            name=update["field_name"],
                            label=update["field_label"],
                            type="text",  # Will be set from form structure
                            section=update.get("section", ""),
                            value=update.get("value", "")
                        )
                        filled_fields.append(field)
                        
                        field_data = {
                            "field": {
                                "name": update["field_name"],
                                "label": update["field_label"],
                                "value": update.get("value", ""),
                                "section": update.get("section", "")
                            },
                            "progress": update.get("progress", 0),
                            "message": update.get("message", ""),
                            "status": "filling"
                        }
                        yield f"data: {json.dumps(field_data, ensure_ascii=False)}\n\n"
                    
                except asyncio.TimeoutError:
                    if processing_complete.is_set():
                        break
                    await asyncio.sleep(0.05)
                    continue
                    
            except Exception as e:
                logger.error(f"Error in streaming loop: {e}")
                break
        
        # Wait for task to complete
        await filling_task
        
        # Get any remaining items
        while not step_queue.empty():
            try:
                update = step_queue.get_nowait()
                if update.get("field_name"):
                    field = FormField(
                        name=update["field_name"],
                        label=update["field_label"],
                        type="text",
                        section=update.get("section", ""),
                        value=update.get("value", "")
                    )
                    filled_fields.append(field)
                    field_data = {
                        "field": {
                            "name": update["field_name"],
                            "label": update["field_label"],
                            "value": update.get("value", ""),
                            "section": update.get("section", "")
                        },
                        "progress": update.get("progress", 0),
                        "status": "filling"
                    }
                    yield f"data: {json.dumps(field_data, ensure_ascii=False)}\n\n"
            except Exception:
                break
        
    except Exception as e:
        logger.error(f"Error streaming form filling: {e}")
        error_str = str(e).replace('\x00', '').replace('\r', '')
        yield f"data: {json.dumps({'error': error_str, 'status': 'error'}, ensure_ascii=False)}\n\n"
        set_progress_callback(None)


# ============================================================================
# STEP 5: API ENDPOINTS
# ============================================================================
@router.get("/health", response_model=ServiceInfo)
async def health_check():
    """Health check endpoint"""
    return ServiceInfo(
        status="healthy",
        service="job-application-form-filling",
        description="AI-powered job application form auto-filling system"
    )


@router.get("/job-listing", response_model=JobListing)
async def get_job_listing():
    """Get the job listing"""
    return _get_job_listing_data()


@router.get("/form-structure", response_model=FormStructure)
async def get_form_structure_endpoint():
    """
    Get a sample form structure (for demo/display purposes only).
    
    Note: The actual form filling uses HTML parsing to discover form structure dynamically.
    This endpoint is only for displaying a sample structure in the UI.
    """
    # Return a simple sample structure for UI display
    # The actual form filling will parse HTML to discover the real structure
    from .form_template import get_form_structure
    return get_form_structure()


@router.post("/upload-resume", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload and parse a resume PDF
    
    This endpoint:
    1. Accepts a PDF resume file
    2. Parses the resume to extract structured data
    3. Returns parsed data with session ID
    
    Args:
        file: Resume PDF file
        
    Returns:
        ResumeUploadResponse with parsed data and session ID
    """
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported. Please upload a .pdf file."
            )
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Save file temporarily
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, f"{session_id}_{file.filename}")
        
        try:
            with open(temp_file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # Parse resume
            logger.info(f"Parsing resume for session: {session_id}")
            resume_data = await parse_resume_pdf(temp_file_path)
            
            if not resume_data:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to parse resume. Please ensure the PDF contains readable text."
                )
            
            # Store in session
            sessions[session_id] = {
                "session_id": session_id,
                "resume_data": resume_data.dict(),
                "status": "parsed",
                "created_at": asyncio.get_event_loop().time()
            }
            
            logger.info(f"Resume parsed successfully for session: {session_id}")
            
            return ResumeUploadResponse(
                session_id=session_id,
                resume_data=resume_data,
                status="parsed",
                message="Resume parsed successfully"
            )
            
        finally:
            # Clean up temp file
            try:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Error cleaning up temp files: {e}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading resume: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing resume: {str(e)}"
        )


class FormFillStreamRequest(BaseModel):
    """Request body for form filling stream"""
    html_content: Optional[str] = None  # HTML content to parse form structure from


@router.post("/fill-form-stream")
async def fill_form_stream(
    session_id: str = Query(..., description="Session ID from resume upload"),
    request: Optional[FormFillStreamRequest] = Body(None)
):
    """
    Stream form filling updates in real-time
    
    This endpoint:
    1. Parses HTML content to discover form structure dynamically
    2. Uses AI agent to fill the discovered form fields
    3. Streams progress updates in real-time
    
    The agent discovers form structure by parsing HTML - no hardcoded templates!
    
    Args:
        session_id: Session ID from resume upload
        request: Request body with html_content (HTML of the form page)
        
    Returns:
        SSE stream with field-by-field updates
    """
    try:
        logger.info(f"Starting form filling stream for session: {session_id}")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        
        # Parse HTML to discover form structure
        form_structure = None
        if request and request.html_content:
            logger.info("Parsing HTML content to discover form structure...")
            try:
                form_structure = parse_html_form(request.html_content)
                logger.info(f"Discovered {len(form_structure.fields)} fields in {len(form_structure.sections)} sections")
            except Exception as e:
                logger.error(f"Error parsing HTML: {e}", exc_info=True)
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to parse HTML form: {str(e)}"
                )
        else:
            logger.warning("No HTML content provided, cannot discover form structure")
            raise HTTPException(
                status_code=400,
                detail="html_content is required to discover form structure"
            )
        
        if not form_structure or not form_structure.fields:
            logger.warning("No form fields discovered from HTML")
            raise HTTPException(
                status_code=400,
                detail="No form fields found in HTML content"
            )
        
        logger.info(f"Starting form filling with {len(form_structure.fields)} fields")
        
        return StreamingResponse(
            stream_form_filling(session_id, form_structure),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting form filling stream: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error starting form filling: {str(e)}"
        )


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get session information"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return sessions[session_id]

