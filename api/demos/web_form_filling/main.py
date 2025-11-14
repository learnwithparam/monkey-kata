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
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, HttpUrl
from typing import Dict, Optional, Any
import uuid
import logging
import os
import secrets
import string
import json
import asyncio
from datetime import timedelta

from .form_agent import fill_form_workflow

# LiveKit SDK for token generation
try:
    from livekit import api
except ImportError:
    api = None

logger = logging.getLogger(__name__)

# Create a router - groups all endpoints under /web-form-filling
router = APIRouter(prefix="/web-form-filling", tags=["web-form-filling"])

# In-memory storage for form filling sessions
form_sessions: Dict[str, Dict[str, Any]] = {}

# In-memory storage for voice-collected form data (keyed by room_name)
voice_collected_data: Dict[str, Dict[str, str]] = {}


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


class ConnectionRequest(BaseModel):
    """Request to connect to voice agent"""
    participant_name: Optional[str] = "User"


class ConnectionResponse(BaseModel):
    """LiveKit connection details"""
    server_url: str
    room_name: str
    participant_name: str
    participant_token: str


# ============================================================================
# STEP 3: LIVEKIT TOKEN GENERATION
# ============================================================================
def generate_room_name() -> str:
    """Generates a unique room name for this session"""
    alphabet = string.ascii_uppercase + string.digits
    return f"form_{''.join(secrets.choice(alphabet) for _ in range(8))}"


def generate_participant_identity() -> str:
    """Generates a unique participant identity for this user"""
    return f"user_{secrets.token_hex(4)}"


def create_access_token(room_name: str, participant_identity: str, participant_name: str) -> str:
    """Creates a LiveKit access token for joining a room"""
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    
    if not api_key or not api_secret:
        raise HTTPException(
            status_code=500,
            detail="LiveKit credentials not configured. Please set LIVEKIT_API_KEY and LIVEKIT_API_SECRET environment variables."
        )
    
    if api is None:
        raise HTTPException(
            status_code=500,
            detail="LiveKit SDK not installed. Install with: pip install livekit"
        )
    
    try:
        token = api.AccessToken(api_key, api_secret) \
            .with_identity(participant_identity) \
            .with_name(participant_name) \
            .with_grants(api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )) \
            .with_ttl(timedelta(minutes=15))
        
        return token.to_jwt()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create LiveKit token: {str(e)}"
        )


# ============================================================================
# STEP 4: BACKGROUND PROCESSING WITH STREAMING
# ============================================================================
async def stream_form_filling(
    session_id: str,
    url: str,
    form_data: Dict[str, str],
    auto_submit: bool
):
    """Stream form filling steps in real-time"""
    from .form_agent import set_progress_callback
    from datetime import datetime
    
    # Create a queue to collect steps
    step_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
    processing_complete = asyncio.Event()
    processing_error = None
    final_result = None
    
    try:
        session = form_sessions[session_id]
        session["status"] = "processing"
        session["message"] = "Form Filling Agent: Starting form filling workflow..."
        session["steps"] = []
        
        def update_progress(step_data):
            """Update session and queue step for streaming"""
            try:
                if session_id in form_sessions:
                    step_entry = {
                        "timestamp": step_data.get("timestamp", datetime.now().isoformat()),
                        "message": step_data.get("message", ""),
                        "agent": step_data.get("agent"),
                        "tool": step_data.get("tool"),
                        "target": step_data.get("target")
                    }
                    form_sessions[session_id]["steps"].append(step_entry)
                    form_sessions[session_id]["message"] = step_entry["message"]
                    step_queue.put_nowait(step_entry)
            except Exception as e:
                logger.warning(f"Error updating progress: {e}")
        
        # Set the progress callback
        set_progress_callback(update_progress)
        
        # Run form filling in background
        async def run_filling():
            nonlocal final_result, processing_error
            try:
                result = await fill_form_workflow(
                    url=url,
                    form_data=form_data,
                    auto_submit=auto_submit
                )
                final_result = result
            except Exception as e:
                processing_error = e
                logger.error(f"Error in form filling workflow: {e}")
            finally:
                processing_complete.set()
                set_progress_callback(None)
        
        # Start processing task
        processing_task = asyncio.create_task(run_filling())
        
        # Stream steps as they come
        while not processing_complete.is_set():
            try:
                try:
                    step_data = await asyncio.wait_for(step_queue.get(), timeout=0.1)
                    # Clean step data to ensure JSON safety
                    clean_step = {
                        "timestamp": step_data.get("timestamp", ""),
                        "message": str(step_data.get("message", "")).replace('\x00', '').replace('\r', ''),
                        "agent": str(step_data.get("agent", "")) if step_data.get("agent") else None,
                        "tool": str(step_data.get("tool", "")) if step_data.get("tool") else None,
                        "target": str(step_data.get("target", "")) if step_data.get("target") else None,
                    }
                    yield f"data: {json.dumps({'step': clean_step, 'status': 'processing'}, ensure_ascii=False)}\n\n"
                except asyncio.TimeoutError:
                    if processing_complete.is_set():
                        break
                    await asyncio.sleep(0.05)
                    continue
            except Exception as e:
                logger.error(f"Error in streaming loop: {e}")
                break
        
        # Get any remaining items from queue
        while not step_queue.empty():
            try:
                step_data = step_queue.get_nowait()
                clean_step = {
                    "timestamp": step_data.get("timestamp", ""),
                    "message": str(step_data.get("message", "")).replace('\x00', '').replace('\r', ''),
                    "agent": str(step_data.get("agent", "")) if step_data.get("agent") else None,
                    "tool": str(step_data.get("tool", "")) if step_data.get("tool") else None,
                    "target": str(step_data.get("target", "")) if step_data.get("target") else None,
                }
                yield f"data: {json.dumps({'step': clean_step, 'status': 'processing'}, ensure_ascii=False)}\n\n"
            except Exception as e:
                logger.error(f"Error encoding remaining step: {e}")
                break
        
        # Wait for processing to complete
        await processing_task
        
        # Send final result
        if final_result:
            status = "success" if final_result.get("status") == "success" else "error"
            clean_result = {
                "url": str(final_result.get("url", "")).replace('\x00', '').replace('\r', ''),
                "form_data": final_result.get("form_data", {}),
                "navigation": str(final_result.get("navigation", "")).replace('\x00', '').replace('\r', '') if final_result.get("navigation") else None,
                "form_detection": str(final_result.get("form_detection", "")).replace('\x00', '').replace('\r', '') if final_result.get("form_detection") else None,
                "form_filling": str(final_result.get("form_filling", "")).replace('\x00', '').replace('\r', '') if final_result.get("form_filling") else None,
                "form_submission": str(final_result.get("form_submission", "")).replace('\x00', '').replace('\r', '') if final_result.get("form_submission") else None,
                "submitted": final_result.get("submitted", False),
            }
            yield f"data: {json.dumps({'done': True, 'status': status, 'result': clean_result}, ensure_ascii=False)}\n\n"
        elif processing_error:
            error_str = str(processing_error).replace('\x00', '').replace('\r', '')
            yield f"data: {json.dumps({'done': True, 'status': 'error', 'error': error_str}, ensure_ascii=False)}\n\n"
        
    except Exception as e:
        logger.error(f"Error streaming form filling for session {session_id}: {e}")
        error_str = str(e).replace('\x00', '').replace('\r', '')
        yield f"data: {json.dumps({'error': error_str, 'status': 'error'}, ensure_ascii=False)}\n\n"
        from .form_agent import set_progress_callback
        set_progress_callback(None)


# ============================================================================
# STEP 5: API ENDPOINTS
# ============================================================================
@router.post("/connection", response_model=ConnectionResponse)
async def get_connection(request: ConnectionRequest):
    """
    Generate LiveKit connection token for voice data collection agent
    
    This endpoint:
    1. Generates a unique room name for this session
    2. Creates a participant identity
    3. Generates a secure LiveKit access token
    4. Returns connection details (server URL, room name, token)
    
    The frontend uses these details to connect to LiveKit and start
    a voice conversation with the form data collection agent.
    """
    try:
        server_url = os.getenv("LIVEKIT_URL")
        
        if not server_url:
            raise HTTPException(
                status_code=500,
                detail="LIVEKIT_URL environment variable not set. Please configure your LiveKit server URL in .env file."
            )
        
        if "wss://" not in server_url and "ws://" not in server_url:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid LIVEKIT_URL: '{server_url}'. Must be a WebSocket URL (wss:// or ws://)"
            )
        
        # Generate unique session identifiers
        room_name = generate_room_name()
        participant_identity = generate_participant_identity()
        # Use provided name or generate a default
        participant_name = request.participant_name.strip() if request.participant_name and request.participant_name.strip() else f"User_{secrets.token_hex(3)}"
        
        # Create access token
        participant_token = create_access_token(room_name, participant_identity, participant_name)
        
        # Dispatch the form agent to this room
        try:
            if api:
                lk_api = api.LiveKitAPI(
                    url=server_url.replace("wss://", "https://").replace("ws://", "http://"),
                    api_key=os.getenv("LIVEKIT_API_KEY"),
                    api_secret=os.getenv("LIVEKIT_API_SECRET"),
                )
                dispatch = await lk_api.agent_dispatch.create_dispatch(
                    api.CreateAgentDispatchRequest(
                        agent_name="form-agent",
                        room=room_name,
                        metadata='{"demo": "web-form-filling"}'
                    )
                )
                logger.info(f"Created dispatch for form-agent in room {room_name}: {dispatch}")
                await lk_api.aclose()
        except Exception as e:
            logger.warning(f"Failed to dispatch form agent: {e}")
        
        return ConnectionResponse(
            server_url=server_url,
            room_name=room_name,
            participant_name=participant_name,
            participant_token=participant_token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Error creating connection: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


@router.post("/fill-form-stream")
async def fill_form_stream(
    request: FormFillingRequest
):
    """
    Start form filling workflow with real-time step streaming via SSE
    
    This endpoint:
    1. Creates a new form filling session
    2. Streams processing steps in real-time
    3. Returns final result when complete
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
            "auto_submit": request.auto_submit,
            "steps": []
        }
        
        logger.info(f"Started streaming form filling for session: {session_id}")
        
        return StreamingResponse(
            stream_form_filling(
                session_id,
                request.url,
                request.form_data,
                request.auto_submit
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting form filling stream: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting form filling: {str(e)}")


@router.get("/health", response_model=ServiceInfo)
async def health_check():
    """Health check endpoint"""
    return ServiceInfo(
        status="healthy",
        service="web-form-filling",
        description="AI-powered web form filling bot with browser automation and voice data collection"
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


class VoiceCollectedDataRequest(BaseModel):
    """Request to store voice-collected form data"""
    room_name: str = Field(..., description="LiveKit room name")
    form_data: Dict[str, str] = Field(..., description="Collected form data")


class VoiceCollectedDataResponse(BaseModel):
    """Response with voice-collected form data"""
    room_name: str
    form_data: Dict[str, str]
    collected_at: str


@router.post("/voice-data", response_model=VoiceCollectedDataResponse)
async def store_voice_collected_data(request: VoiceCollectedDataRequest):
    """
    Store form data collected via voice conversation
    
    This endpoint is called by the voice agent to store collected form data.
    The frontend polls this endpoint to update form fields in real-time.
    Data is merged with existing data, so multiple tool calls accumulate.
    """
    from datetime import datetime
    
    # Merge with existing data instead of replacing
    if request.room_name not in voice_collected_data:
        voice_collected_data[request.room_name] = {}
    
    # Update existing data with new data (merge)
    voice_collected_data[request.room_name].update(request.form_data)
    
    return VoiceCollectedDataResponse(
        room_name=request.room_name,
        form_data=voice_collected_data[request.room_name],
        collected_at=datetime.now().isoformat()
    )


@router.get("/voice-data/{room_name}")
async def get_voice_collected_data(room_name: str):
    """
    Get form data collected via voice conversation
    
    The frontend polls this endpoint to retrieve and populate form fields.
    Returns empty dict if no data is available yet (to avoid 404 errors during polling).
    """
    from datetime import datetime
    
    if room_name not in voice_collected_data:
        # Return empty data instead of 404 to allow graceful polling
        return VoiceCollectedDataResponse(
            room_name=room_name,
            form_data={},
            collected_at=datetime.now().isoformat()
        )
    
    return VoiceCollectedDataResponse(
        room_name=room_name,
        form_data=voice_collected_data[room_name],
        collected_at=datetime.now().isoformat()
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

