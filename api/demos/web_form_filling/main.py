"""
Web Form Filling AI Bot API
===========================

🎯 LEARNING OBJECTIVES:
This demo teaches you how to build a browser automation agent:

1. Browser automation - Using Playwright to control browsers
2. Tool calling - Agents use browser tools to interact with web pages
3. Workflow orchestration - Coordinating navigation, detection, filling, and submission
4. Form field detection - Identifying and matching form fields

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Setup - Import libraries and configure the router
Step 2: Data Models - Define request structures with validation
Step 3: API Endpoints - Expose functionality via HTTP
Step 4: Agent Execution - Run form filling workflow

Key Concept: This demo shows how agents can use browser automation tools
to interact with web pages, demonstrating tool calling and workflow orchestration.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, HttpUrl
from typing import Dict, Optional, Any
import uuid
import logging

from .form_agent import fill_form_workflow

logger = logging.getLogger(__name__)

# Create a router - groups all endpoints under /web-form-filling
router = APIRouter(prefix="/web-form-filling", tags=["web-form-filling"])

# In-memory storage for form filling sessions
form_sessions: Dict[str, Dict[str, Any]] = {}


# ============================================================================
# STEP 2: DATA MODELS
# ============================================================================
class FormFillingRequest(BaseModel):
    """Request to fill a web form"""
    url: str = Field(..., description="URL of the webpage with the form")
    form_data: Dict[str, str] = Field(..., description="Dictionary mapping field identifiers to values")
    auto_submit: bool = Field(False, description="Whether to automatically submit the form after filling")


class FormFillingResponse(BaseModel):
    """Response with form filling status"""
    session_id: str
    status: str
    message: str
    url: str


class FormFillingResult(BaseModel):
    """Final form filling result"""
    session_id: str
    status: str
    url: str
    form_data: Dict[str, str]
    navigation: Optional[str] = None
    form_detection: Optional[str] = None
    form_filling: Optional[str] = None
    form_submission: Optional[str] = None
    submitted: bool = False
    error: Optional[str] = None


class ServiceInfo(BaseModel):
    """Health check response"""
    status: str
    service: str
    description: str


# ============================================================================
# STEP 3: BACKGROUND PROCESSING
# ============================================================================
async def process_form_filling(
    session_id: str,
    url: str,
    form_data: Dict[str, str],
    auto_submit: bool
):
    """Background task to fill form"""
    try:
        session = form_sessions[session_id]
        session["status"] = "processing"
        session["message"] = "Form Filling Agent: Navigating to webpage..."
        
        # Run the form filling workflow
        result = await fill_form_workflow(
            url=url,
            form_data=form_data,
            auto_submit=auto_submit
        )
        
        # Update session with results
        session["status"] = result.get("status", "completed")
        session["message"] = "Form filling completed successfully!" if result.get("status") == "success" else f"Error: {result.get('error', 'Unknown error')}"
        session.update(result)
        
        logger.info(f"Completed form filling for session: {session_id}")
        
    except Exception as e:
        logger.error(f"Error processing form filling for session {session_id}: {e}")
        if session_id in form_sessions:
            form_sessions[session_id]["status"] = "error"
            form_sessions[session_id]["message"] = f"Error: {str(e)}"
            form_sessions[session_id]["error"] = str(e)


# ============================================================================
# STEP 4: API ENDPOINTS
# ============================================================================
@router.get("/health", response_model=ServiceInfo)
async def health_check():
    """Health check endpoint"""
    return ServiceInfo(
        status="healthy",
        service="web-form-filling",
        description="AI-powered web form filling bot with browser automation"
    )


@router.post("/fill-form", response_model=FormFillingResponse)
async def fill_form(
    request: FormFillingRequest,
    background_tasks: BackgroundTasks
):
    """
    Start a form filling workflow
    
    This endpoint:
    1. Creates a new form filling session
    2. Starts background processing with the form filling agent
    3. Returns session ID for status checking
    
    The agent will:
    - Navigate to the URL
    - Detect form fields
    - Fill the form with provided data
    - Optionally submit the form
    """
    try:
        session_id = str(uuid.uuid4())
        
        # Validate URL
        if not request.url.startswith(('http://', 'https://')):
            raise HTTPException(
                status_code=400,
                detail="URL must start with http:// or https://"
            )
        
        # Initialize session
        form_sessions[session_id] = {
            "session_id": session_id,
            "status": "processing",
            "message": "Initializing form filling...",
            "url": request.url,
            "form_data": request.form_data,
            "auto_submit": request.auto_submit
        }
        
        # Start background processing
        background_tasks.add_task(
            process_form_filling,
            session_id,
            request.url,
            request.form_data,
            request.auto_submit
        )
        
        logger.info(f"Started form filling for session: {session_id}")
        
        return FormFillingResponse(
            session_id=session_id,
            status="processing",
            message="Form filling started. Use the session_id to check status.",
            url=request.url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting form filling: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting form filling: {str(e)}")


@router.get("/status/{session_id}", response_model=FormFillingResponse)
async def get_status(session_id: str):
    """Get form filling status for a session"""
    if session_id not in form_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = form_sessions[session_id]
    return FormFillingResponse(
        session_id=session_id,
        status=session["status"],
        message=session["message"],
        url=session["url"]
    )


@router.get("/result/{session_id}", response_model=FormFillingResult)
async def get_result(session_id: str):
    """Get final form filling result for a session"""
    if session_id not in form_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = form_sessions[session_id]
    
    if session["status"] == "processing":
        raise HTTPException(
            status_code=400,
            detail="Form filling still in progress. Please check status endpoint."
        )
    
    return FormFillingResult(
        session_id=session_id,
        status=session["status"],
        url=session["url"],
        form_data=session["form_data"],
        navigation=session.get("navigation"),
        form_detection=session.get("form_detection"),
        form_filling=session.get("form_filling"),
        form_submission=session.get("form_submission"),
        submitted=session.get("submitted", False),
        error=session.get("error")
    )


@router.get("/learning-objectives")
async def get_learning_objectives():
    """Get learning objectives for this demo"""
    return {
        "demo": "Web Form Filling AI Bot",
        "objectives": [
            "Understand browser automation using Playwright",
            "Learn tool calling for browser interactions",
            "Implement form field detection and matching",
            "Build workflow orchestration for form filling",
            "Create agents that interact with web pages"
        ],
        "technologies": [
            "Playwright",
            "Browser Automation",
            "LangChain Agents",
            "Tool Calling",
            "FastAPI"
        ],
        "concepts": [
            "Browser Automation",
            "Tool Calling",
            "Workflow Orchestration",
            "Form Field Detection",
            "Web Interaction"
        ]
    }

