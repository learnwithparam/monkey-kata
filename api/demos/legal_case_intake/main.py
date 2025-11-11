"""
Legal Case Intake Workflow API
==============================

🎯 LEARNING OBJECTIVES:
This demo teaches you how to build a multi-agent system with human-in-the-loop:

1. Multi-agent coordination - Intake and Review agents work together
2. Human-in-the-loop - Lawyer review and approval workflow
3. Workflow orchestration - Coordinating intake, analysis, and review
4. Context preservation - Maintaining case information across workflow stages

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Setup - Import libraries and configure the router
Step 2: Data Models - Define request structures with validation
Step 3: API Endpoints - Expose functionality via HTTP
Step 4: Workflow Orchestration - Coordinate agents and human review

Key Concept: This demo shows how multiple agents can handle initial processing
while humans make final decisions, demonstrating human-in-the-loop patterns.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any, AsyncGenerator, List
from datetime import datetime
import uuid
import logging
import asyncio
import json

from .models import CaseIntake, CaseReview, CaseResult, CaseStatus
from .intake_agents import process_case_intake
from .progress import set_progress_callback

logger = logging.getLogger(__name__)

# Create a router - groups all endpoints under /legal-case-intake
router = APIRouter(prefix="/legal-case-intake", tags=["legal-case-intake"])

# In-memory storage for case sessions
case_sessions: Dict[str, Dict[str, Any]] = {}


# ============================================================================
# STEP 2: DATA MODELS
# ============================================================================
class CaseIntakeRequest(BaseModel):
    """Request to start case intake"""
    client_name: str = Field(..., min_length=1, description="Client's full name")
    client_email: EmailStr = Field(..., description="Client's email address")
    client_phone: Optional[str] = Field(None, description="Client's phone number")
    case_type: str = Field(..., min_length=1, description="Type of legal case")
    case_description: str = Field(..., min_length=10, description="Detailed description of the case")
    urgency: str = Field(default="normal", description="Urgency level: low, normal, high, urgent")
    additional_info: Optional[str] = Field(None, description="Any additional information")


class CaseIntakeResponse(BaseModel):
    """Response with case intake status"""
    case_id: str
    status: str
    message: str
    steps: Optional[List[Dict[str, Any]]] = None  # Track workflow steps


class CaseReviewRequest(BaseModel):
    """Request for lawyer review"""
    case_id: str
    lawyer_notes: Optional[str] = Field(None, description="Lawyer's review notes")
    lawyer_decision: str = Field(..., description="Lawyer's decision: approve, reject, request_info")


class CaseReviewResponse(BaseModel):
    """Response with case review information"""
    case_id: str
    status: str
    intake_data: CaseIntake
    intake_summary: str
    risk_assessment: str
    recommended_action: str
    lawyer_notes: Optional[str] = None
    lawyer_decision: Optional[str] = None


class ServiceInfo(BaseModel):
    """Health check response"""
    status: str
    service: str
    description: str


# ============================================================================
# STEP 3: BACKGROUND PROCESSING
# ============================================================================
async def process_case(
    case_id: str,
    case_intake: CaseIntake
):
    """Background task to process case through intake and review"""
    from .progress import set_progress_callback
    
    try:
        session = case_sessions[case_id]
        session["status"] = "processing"
        session["message"] = "Intake Agent: Collecting and validating case information..."
        session["steps"] = []
        
        # Set up progress callback to update session
        def update_progress(step_data):
            """Update session with progress steps"""
            try:
                if case_id in case_sessions:
                    # Handle both string (old format) and dict (new format)
                    if isinstance(step_data, str):
                        step_entry = {
                            "timestamp": datetime.now().isoformat(),
                            "message": step_data,
                            "agent": None,
                            "tool": None,
                            "target": None
                        }
                    else:
                        step_entry = {
                            "timestamp": datetime.now().isoformat(),
                            "message": step_data.get("message", ""),
                            "agent": step_data.get("agent"),
                            "tool": step_data.get("tool"),
                            "target": step_data.get("target")
                        }
                    
                    case_sessions[case_id]["steps"].append(step_entry)
                    case_sessions[case_id]["message"] = step_entry["message"]
                    logger.info(f"Progress [{case_id}]: {step_entry['message']}")
            except Exception as e:
                logger.error(f"Error in update_progress callback: {e}")
        
        # Set the progress callback
        set_progress_callback(update_progress)
        
        # Process case through agents
        result = await process_case_intake(case_intake)
        
        # Update session with results
        session["status"] = "pending_lawyer"
        session["message"] = "Case processed. Awaiting lawyer review."
        session["intake_summary"] = result["intake_summary"]
        session["risk_assessment"] = result["risk_assessment"]
        session["recommended_action"] = result["recommended_action"]
        session["created_at"] = datetime.now().isoformat()
        
        # Clear progress callback
        set_progress_callback(None)
        
        logger.info(f"Completed case processing for case: {case_id}")
        
    except Exception as e:
        logger.error(f"Error processing case {case_id}: {e}")
        if case_id in case_sessions:
            case_sessions[case_id]["status"] = "error"
            case_sessions[case_id]["message"] = f"Error: {str(e)}"
            case_sessions[case_id]["error"] = str(e)
        set_progress_callback(None)


async def stream_case_processing(
    case_id: str,
    case_intake: CaseIntake
) -> AsyncGenerator[str, None]:
    """Stream case processing steps in real-time"""
    from .progress import set_progress_callback
    
    # Create a queue to collect steps
    step_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
    processing_complete = asyncio.Event()
    processing_error = None
    final_result = None
    
    try:
        session = case_sessions[case_id]
        session["status"] = "processing"
        session["message"] = "Intake Agent: Collecting and validating case information..."
        session["steps"] = []
        
        def update_progress(step_data):
            """Update session and queue step for streaming"""
            try:
                if case_id in case_sessions:
                    # Handle both string (old format) and dict (new format)
                    if isinstance(step_data, str):
                        step_entry = {
                            "timestamp": datetime.now().isoformat(),
                            "message": step_data,
                            "agent": None,
                            "tool": None,
                            "target": None
                        }
                    else:
                        step_entry = {
                            "timestamp": datetime.now().isoformat(),
                            "message": step_data.get("message", ""),
                            "agent": step_data.get("agent"),
                            "tool": step_data.get("tool"),
                            "target": step_data.get("target")
                        }
                    
                    case_sessions[case_id]["steps"].append(step_entry)
                    case_sessions[case_id]["message"] = step_entry["message"]
                    # Add to queue for streaming (non-blocking)
                    try:
                        step_queue.put_nowait(step_entry)
                        logger.info(f"Queued step for streaming: {step_entry['message'][:50]}...")
                    except asyncio.QueueFull:
                        logger.warning("Step queue is full, skipping step")
                    except Exception as e:
                        logger.warning(f"Error queuing step: {e}")
            except Exception as e:
                logger.error(f"Error in update_progress callback: {e}")
        
        # Set the progress callback
        set_progress_callback(update_progress)
        
        # Start processing in background
        async def run_processing():
            nonlocal processing_error, final_result
            try:
                result = await process_case_intake(case_intake)
                
                session["status"] = "pending_lawyer"
                session["message"] = "Case processed. Awaiting lawyer review."
                session["intake_summary"] = result["intake_summary"]
                session["risk_assessment"] = result["risk_assessment"]
                session["recommended_action"] = result["recommended_action"]
                session["created_at"] = datetime.now().isoformat()
                
                final_result = result
                processing_complete.set()
            except Exception as e:
                session["status"] = "error"
                session["message"] = f"Error: {str(e)}"
                session["error"] = str(e)
                processing_error = str(e)
                processing_complete.set()
            finally:
                set_progress_callback(None)
        
        # Start processing task
        processing_task = asyncio.create_task(run_processing())
        
        # Stream initial connection with case_id
        yield f"data: {json.dumps({'status': 'connected', 'message': 'Starting case intake processing...', 'case_id': case_id})}\n\n"
        
        # Stream steps as they come
        while not processing_complete.is_set():
            try:
                # Wait for next step with short timeout to check completion
                try:
                    step_data = await asyncio.wait_for(step_queue.get(), timeout=0.1)
                    # Stream the step immediately
                    logger.info(f"Streaming step: {step_data.get('message', '')[:50]}...")
                    yield f"data: {json.dumps({'step': step_data, 'status': 'processing'})}\n\n"
                except asyncio.TimeoutError:
                    # No step available, check if processing is done
                    if processing_complete.is_set():
                        break
                    # Small delay to prevent busy waiting
                    await asyncio.sleep(0.05)
                    continue
                    
            except Exception as e:
                logger.error(f"Error in streaming loop: {e}")
                break
        
        # Get any remaining items from queue
        while not step_queue.empty():
            try:
                step_data = step_queue.get_nowait()
                yield f"data: {json.dumps({'step': step_data, 'status': 'processing'})}\n\n"
            except:
                break
        
        # Wait for processing to complete
        await processing_task
        
        # Send final result
        if final_result:
            yield f"data: {json.dumps({'done': True, 'status': 'pending_lawyer', 'result': final_result})}\n\n"
        elif processing_error:
            yield f"data: {json.dumps({'done': True, 'status': 'error', 'error': processing_error})}\n\n"
        
    except Exception as e:
        logger.error(f"Error streaming case processing for case {case_id}: {e}")
        yield f"data: {json.dumps({'error': str(e), 'status': 'error'})}\n\n"
        set_progress_callback(None)


# ============================================================================
# STEP 4: API ENDPOINTS
# ============================================================================
@router.get("/health", response_model=ServiceInfo)
async def health_check():
    """Health check endpoint"""
    return ServiceInfo(
        status="healthy",
        service="legal-case-intake",
        description="Multi-agent legal case intake system with human-in-the-loop review"
    )


@router.post("/submit-case", response_model=CaseIntakeResponse)
async def submit_case(
    request: CaseIntakeRequest,
    background_tasks: BackgroundTasks
):
    """
    Submit a new legal case for intake processing
    
    This endpoint:
    1. Creates a new case session
    2. Starts background processing with Intake and Review agents
    3. Returns case ID for status checking
    
    The workflow:
    - Intake Agent validates and structures case information
    - Review Agent analyzes case and provides recommendations
    - Case is then ready for lawyer review
    """
    try:
        case_id = str(uuid.uuid4())
        
        # Convert request to CaseIntake model
        case_intake = CaseIntake(
            client_name=request.client_name,
            client_email=request.client_email,
            client_phone=request.client_phone,
            case_type=request.case_type,
            case_description=request.case_description,
            urgency=request.urgency,
            additional_info=request.additional_info
        )
        
        # Initialize session
        case_sessions[case_id] = {
            "case_id": case_id,
            "status": "processing",
            "message": "Initializing case intake...",
            "intake_data": case_intake.dict(),
            "intake_summary": None,
            "risk_assessment": None,
            "recommended_action": None,
            "lawyer_notes": None,
            "lawyer_decision": None,
            "created_at": None,
            "reviewed_at": None,
            "steps": []
        }
        
        # Start background processing
        background_tasks.add_task(process_case, case_id, case_intake)
        
        logger.info(f"Started case processing for case: {case_id}")
        
        return CaseIntakeResponse(
            case_id=case_id,
            status="processing",
            message="Case submitted. Processing with Intake and Review agents..."
        )


@router.post("/submit-case-stream")
async def submit_case_stream(request: CaseIntakeRequest):
    """
    Submit a new legal case for intake processing with real-time streaming
    
    This endpoint streams workflow steps in real-time as they happen,
    showing which agent is doing what for educational purposes.
    """
    try:
        case_id = str(uuid.uuid4())
        
        # Convert request to CaseIntake model
        case_intake = CaseIntake(
            client_name=request.client_name,
            client_email=request.client_email,
            client_phone=request.client_phone,
            case_type=request.case_type,
            case_description=request.case_description,
            urgency=request.urgency,
            additional_info=request.additional_info
        )
        
        # Initialize session
        case_sessions[case_id] = {
            "case_id": case_id,
            "status": "processing",
            "message": "Initializing case intake...",
            "intake_data": case_intake.dict(),
            "intake_summary": None,
            "risk_assessment": None,
            "recommended_action": None,
            "lawyer_notes": None,
            "lawyer_decision": None,
            "created_at": None,
            "reviewed_at": None,
            "steps": []
        }
        
        logger.info(f"Started streaming case processing for case: {case_id}")
        
        return StreamingResponse(
            stream_case_processing(case_id, case_intake),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
        
    except Exception as e:
        logger.error(f"Error starting streaming case processing: {e}")
        raise HTTPException(status_code=500, detail=f"Error submitting case: {str(e)}")


@router.get("/status/{case_id}", response_model=CaseIntakeResponse)
async def get_status(case_id: str):
    """Get case processing status"""
    if case_id not in case_sessions:
        raise HTTPException(status_code=404, detail="Case not found")
    
    session = case_sessions[case_id]
    return CaseIntakeResponse(
        case_id=case_id,
        status=session["status"],
        message=session["message"],
        steps=session.get("steps", [])
    )


@router.get("/review/{case_id}", response_model=CaseReviewResponse)
async def get_case_for_review(case_id: str):
    """
    Get case information ready for lawyer review
    
    This endpoint returns the case with AI-generated summary and recommendations,
    ready for a lawyer to review and make a decision.
    """
    if case_id not in case_sessions:
        raise HTTPException(status_code=404, detail="Case not found")
    
    session = case_sessions[case_id]
    
    if session["status"] == "processing":
        raise HTTPException(
            status_code=400,
            detail="Case still being processed. Please wait."
        )
    
    if session["status"] != "pending_lawyer":
        raise HTTPException(
            status_code=400,
            detail=f"Case is not ready for review. Current status: {session['status']}"
        )
    
    intake_data = CaseIntake(**session["intake_data"])
    
    return CaseReviewResponse(
        case_id=case_id,
        status=session["status"],
        intake_data=intake_data,
        intake_summary=session["intake_summary"],
        risk_assessment=session["risk_assessment"],
        recommended_action=session["recommended_action"],
        lawyer_notes=session.get("lawyer_notes"),
        lawyer_decision=session.get("lawyer_decision")
    )


@router.post("/review/{case_id}", response_model=CaseReviewResponse)
async def submit_lawyer_review(
    case_id: str,
    request: CaseReviewRequest
):
    """
    Submit lawyer review and decision
    
    This is the human-in-the-loop step where a lawyer reviews the AI-processed
    case and makes a final decision.
    """
    if case_id not in case_sessions:
        raise HTTPException(status_code=404, detail="Case not found")
    
    session = case_sessions[case_id]
    
    if session["status"] != "pending_lawyer":
        raise HTTPException(
            status_code=400,
            detail=f"Case is not ready for review. Current status: {session['status']}"
        )
    
    # Validate decision
    valid_decisions = ["approve", "reject", "request_info"]
    if request.lawyer_decision.lower() not in valid_decisions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid decision. Must be one of: {', '.join(valid_decisions)}"
        )
    
    # Update session with lawyer review
    decision = request.lawyer_decision.lower()
    session["lawyer_notes"] = request.lawyer_notes
    session["lawyer_decision"] = decision
    session["reviewed_at"] = datetime.now().isoformat()
    
    if decision == "approve":
        session["status"] = "approved"
        session["message"] = "Case approved by lawyer"
    elif decision == "reject":
        session["status"] = "rejected"
        session["message"] = "Case rejected by lawyer"
    else:  # request_info
        session["status"] = "intake"
        session["message"] = "Lawyer requested additional information"
    
    intake_data = CaseIntake(**session["intake_data"])
    
    return CaseReviewResponse(
        case_id=case_id,
        status=session["status"],
        intake_data=intake_data,
        intake_summary=session["intake_summary"],
        risk_assessment=session["risk_assessment"],
        recommended_action=session["recommended_action"],
        lawyer_notes=session["lawyer_notes"],
        lawyer_decision=session["lawyer_decision"]
    )


@router.get("/result/{case_id}")
async def get_case_result(case_id: str):
    """Get final case result"""
    if case_id not in case_sessions:
        raise HTTPException(status_code=404, detail="Case not found")
    
    session = case_sessions[case_id]
    intake_data = CaseIntake(**session["intake_data"])
    
    return {
        "case_id": case_id,
        "status": session["status"],
        "intake_data": intake_data.dict(),
        "intake_summary": session["intake_summary"],
        "risk_assessment": session["risk_assessment"],
        "recommended_action": session["recommended_action"],
        "lawyer_notes": session.get("lawyer_notes"),
        "lawyer_decision": session.get("lawyer_decision"),
        "created_at": session.get("created_at"),
        "reviewed_at": session.get("reviewed_at")
    }


@router.get("/learning-objectives")
async def get_learning_objectives():
    """Get learning objectives for this demo"""
    return {
        "demo": "Legal Case Intake Workflow",
        "objectives": [
            "Understand multi-agent coordination in legal workflows",
            "Learn human-in-the-loop patterns for AI systems",
            "Implement workflow orchestration with agent coordination",
            "Build systems that combine AI processing with human oversight",
            "Create context preservation across workflow stages"
        ],
        "technologies": [
            "CrewAI",
            "Multi-Agent Systems",
            "Human-in-the-Loop",
            "Workflow Orchestration",
            "FastAPI"
        ],
        "concepts": [
            "Multi-Agent Coordination",
            "Human-in-the-Loop",
            "Workflow Orchestration",
            "Context Preservation",
            "Agent Specialization"
        ]
    }

