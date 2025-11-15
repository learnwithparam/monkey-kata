"""
Influencer Discovery API
========================

🎯 LEARNING OBJECTIVES:
This demo teaches you how to build a browser automation agent system:

1. Browser Automation - Using browser_use to control web browsers
2. Web Search Integration - Using DuckDuckGo for open-source search
3. Structured Data Extraction - Extracting influencer profiles from web
4. Real-time Streaming - Stream discovery progress for better UX
5. Dynamic Form Input - Accepting user criteria via form

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Setup - Import libraries and configure the router
Step 2: Data Models - Define request structures with validation
Step 3: Browser Agent - Agentic influencer discovery
Step 4: API Endpoints - Expose functionality via HTTP

Key Concept: This demo shows how AI agents can autonomously search the web,
analyze results, and extract structured data based on user-defined criteria.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, AsyncGenerator
import uuid
import logging
import asyncio
import json
from datetime import datetime

from .models import (
    DiscoveryRequest, DiscoveryResponse, DiscoveryResult,
    InfluencerProfile, ServiceInfo
)
from .browser_agent import discover_influencers_agentic, set_progress_callback

logger = logging.getLogger(__name__)

# Create a router - groups all endpoints under /influencer-discovery
router = APIRouter(prefix="/influencer-discovery", tags=["influencer-discovery"])

# In-memory storage for discovery sessions
discovery_sessions: Dict[str, Dict[str, Any]] = {}


# ============================================================================
# STEP 2: DATA MODELS
# ============================================================================
"""
What is a Data Model?
- Defines the structure of incoming requests
- Automatically validates data (type checking, required fields)
- Provides clear error messages if validation fails
- Think of it as a "contract" for what your API expects

Models:
- DiscoveryRequest: User-defined criteria for finding influencers
- DiscoveryResponse: Status and session information
- DiscoveryResult: Final discovery results with influencer profiles
"""


# ============================================================================
# STEP 3: BACKGROUND PROCESSING
# ============================================================================
"""
Background Processing:
- Runs discovery in the background so API responds immediately
- Updates session status as discovery progresses
- Stores results in memory (in production, use a database)
"""

async def run_discovery_task(session_id: str, request: DiscoveryRequest):
    """
    Background task to run influencer discovery.
    
    This function:
    1. Updates session status to "processing"
    2. Runs the discovery agent
    3. Stores results in the session
    4. Updates status to "completed" or "error"
    """
    try:
        discovery_sessions[session_id]["status"] = "processing"
        discovery_sessions[session_id]["started_at"] = datetime.now().isoformat()
        
        # Set up progress callback
        def progress_callback(data: Dict[str, Any]):
            if session_id in discovery_sessions:
                if "progress" not in discovery_sessions[session_id]:
                    discovery_sessions[session_id]["progress"] = []
                discovery_sessions[session_id]["progress"].append({
                    **data,
                    "timestamp": datetime.now().isoformat()
                })
        
        set_progress_callback(progress_callback)
        
        # Run discovery
        logger.info(f"Starting discovery for session {session_id}")
        profiles = await discover_influencers_agentic(request)
        
        # Store results
        discovery_sessions[session_id]["status"] = "completed"
        discovery_sessions[session_id]["influencers"] = [p.dict() for p in profiles]
        discovery_sessions[session_id]["total_found"] = len(profiles)
        discovery_sessions[session_id]["completed_at"] = datetime.now().isoformat()
        
        logger.info(f"Discovery completed for session {session_id}: {len(profiles)} profiles found")
        
    except Exception as e:
        logger.error(f"Error in discovery task for session {session_id}: {e}", exc_info=True)
        discovery_sessions[session_id]["status"] = "error"
        discovery_sessions[session_id]["error"] = str(e)
        discovery_sessions[session_id]["completed_at"] = datetime.now().isoformat()


async def stream_discovery_progress(
    session_id: str
) -> AsyncGenerator[str, None]:
    """
    Stream discovery progress updates as Server-Sent Events.
    
    This function:
    1. Polls the session for progress updates
    2. Streams updates as they occur
    3. Sends completion message when done
    """
    try:
        last_progress_count = 0
        
        while True:
            if session_id not in discovery_sessions:
                yield f"data: {json.dumps({'error': 'Session not found'})}\n\n"
                break
            
            session = discovery_sessions[session_id]
            status = session.get("status", "pending")
            
            # Send progress updates
            progress = session.get("progress", [])
            if len(progress) > last_progress_count:
                new_progress = progress[last_progress_count:]
                for update in new_progress:
                    yield f"data: {json.dumps(update)}\n\n"
                last_progress_count = len(progress)
            
            # Check if completed or error
            if status == "completed":
                result_data = {
                    "status": "completed",
                    "influencers": session.get("influencers", []),
                    "total_found": session.get("total_found", 0),
                    "completed_at": session.get("completed_at")
                }
                yield f"data: {json.dumps(result_data)}\n\n"
                break
            elif status == "error":
                error_data = {
                    "status": "error",
                    "error": session.get("error", "Unknown error")
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                break
            
            await asyncio.sleep(1)  # Poll every second
            
    except Exception as e:
        logger.error(f"Error in streaming loop: {e}", exc_info=True)
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


# ============================================================================
# STEP 4: API ENDPOINTS
# ============================================================================
"""
API Endpoints:
- POST /start-discovery: Start a new influencer discovery
- GET /status/{session_id}: Get discovery status
- GET /stream/{session_id}: Stream discovery progress
- GET /health: Health check
"""

@router.post("/start-discovery", response_model=DiscoveryResponse)
async def start_discovery(
    request: DiscoveryRequest,
    background_tasks: BackgroundTasks
):
    """
    Start a new influencer discovery session.
    
    This endpoint:
    1. Validates the request
    2. Creates a new session
    3. Starts background discovery task
    4. Returns session ID immediately
    """
    try:
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Initialize session
        discovery_sessions[session_id] = {
            "session_id": session_id,
            "status": "pending",
            "criteria": request.dict(),
            "influencers": [],
            "total_found": 0,
            "progress": [],
            "created_at": datetime.now().isoformat()
        }
        
        # Start background task
        background_tasks.add_task(run_discovery_task, session_id, request)
        
        logger.info(f"Started discovery session {session_id}")
        
        return DiscoveryResponse(
            session_id=session_id,
            status="pending",
            message="Discovery started. Use /stream/{session_id} to get progress.",
            criteria=request
        )
        
    except Exception as e:
        logger.error(f"Error starting discovery: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{session_id}", response_model=DiscoveryResult)
async def get_discovery_status(session_id: str):
    """
    Get the current status of a discovery session.
    
    Returns:
        DiscoveryResult with current status and results (if completed)
    """
    if session_id not in discovery_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = discovery_sessions[session_id]
    
    return DiscoveryResult(
        session_id=session_id,
        status=session.get("status", "unknown"),
        influencers=[
            InfluencerProfile(**p) for p in session.get("influencers", [])
        ],
        total_found=session.get("total_found", 0),
        search_queries_used=[],  # Could track this if needed
        completed_at=session.get("completed_at"),
        error=session.get("error")
    )


@router.get("/stream/{session_id}")
async def stream_discovery(session_id: str):
    """
    Stream discovery progress as Server-Sent Events.
    
    This endpoint:
    1. Streams real-time progress updates
    2. Sends completion message when done
    3. Handles errors gracefully
    """
    if session_id not in discovery_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return StreamingResponse(
        stream_discovery_progress(session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/health", response_model=ServiceInfo)
async def health_check():
    """Health check endpoint"""
    return ServiceInfo(
        status="healthy",
        service="influencer-discovery",
        description="Influencer discovery service using browser automation and web search"
    )

