"""
Competitor Analysis Research Agent API
======================================

🎯 LEARNING OBJECTIVES:
This demo teaches you how to build a multi-agent research system:

1. Tool calling & function integration - Agents use web search and scraping tools
2. Multi-agent coordination - Research, Analysis, and Report agents work together
3. Web search integration - Using DuckDuckGo for internet research
4. Workflow orchestration - Coordinating multiple agents in sequence

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Setup - Import libraries and configure the router
Step 2: Data Models - Define request structures with validation
Step 3: API Endpoints - Expose functionality via HTTP
Step 4: Agent Orchestration - Coordinate multiple agents

Key Concept: This demo shows how multiple specialized agents work together
to complete a complex task. Each agent has specific tools and expertise.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, AsyncGenerator
import uuid
import logging
import asyncio
import json
from datetime import datetime

from .agents import run_competitor_analysis

logger = logging.getLogger(__name__)

# Create a router - groups all endpoints under /competitor-analysis
router = APIRouter(prefix="/competitor-analysis", tags=["competitor-analysis"])

# In-memory storage for analysis sessions
analysis_sessions: Dict[str, Dict[str, Any]] = {}


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
- AnalysisRequest: Input for starting competitor analysis
- AnalysisResponse: Status and session information
- AnalysisResult: Final analysis report
"""
class AnalysisRequest(BaseModel):
    """Request to start competitor analysis"""
    company_name: str = Field(..., min_length=1, description="Name of the company to analyze")
    competitors: List[str] = Field(..., min_items=1, description="List of competitor company names")
    focus_areas: Optional[List[str]] = Field(
        default=["pricing", "features", "market position"],
        description="Areas to focus on in the analysis"
    )


class AnalysisResponse(BaseModel):
    """Response with analysis status"""
    session_id: str
    status: str
    message: str
    company_name: str
    competitors: List[str]
    steps: Optional[List[Dict[str, Any]]] = None  # Track research steps with agent/tool info


class AnalysisResult(BaseModel):
    """Final analysis report"""
    session_id: str
    status: str
    company_name: str
    competitors: List[str]
    report: Optional[str] = None
    error: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None  # Track research steps with agent/tool info


class ServiceInfo(BaseModel):
    """Health check response"""
    status: str
    service: str
    description: str


# ============================================================================
# STEP 3: BACKGROUND PROCESSING
# ============================================================================
"""
Background Processing:
When analysis is requested, we process it asynchronously:
1. Create a session
2. Run research agent to gather information
3. Run analysis agent to analyze data
4. Run report agent to create final report
5. Store results in session
"""
async def process_analysis(
    session_id: str,
    company_name: str,
    competitors: List[str],
    focus_areas: List[str]
):
    """Background task to run competitor analysis"""
    from .tools import set_progress_callback
    
    try:
        session = analysis_sessions[session_id]
        session["status"] = "researching"
        session["message"] = "Research Agent: Gathering competitor information from the web..."
        session["steps"] = []  # Initialize steps list
        
        # Set up progress callback to update session
        def update_progress(step_message: str):
            """Update session with progress steps"""
            if session_id in analysis_sessions:
                step_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "message": step_message
                }
                analysis_sessions[session_id]["steps"].append(step_entry)
                analysis_sessions[session_id]["message"] = step_message
                logger.info(f"Progress [{session_id}]: {step_message}")
        
        # Set the progress callback
        set_progress_callback(update_progress)
        
        # Run the multi-agent analysis workflow
        report = await run_competitor_analysis(
            company_name=company_name,
            competitors=competitors,
            focus_areas=focus_areas
        )
        
        # Update session with results
        session["status"] = "completed"
        session["message"] = "✅ Analysis complete! Report generated successfully."
        session["report"] = report
        
        # Clear progress callback
        set_progress_callback(None)
        
        logger.info(f"Completed analysis for session: {session_id}")
        
    except Exception as e:
        logger.error(f"Error processing analysis for session {session_id}: {e}")
        if session_id in analysis_sessions:
            analysis_sessions[session_id]["status"] = "error"
            analysis_sessions[session_id]["message"] = f"❌ Error: {str(e)}"
            analysis_sessions[session_id]["error"] = str(e)
        set_progress_callback(None)


async def stream_analysis_steps(
    session_id: str,
    company_name: str,
    competitors: List[str],
    focus_areas: List[str]
) -> AsyncGenerator[str, None]:
    """Stream analysis steps in real-time"""
    from .tools import set_progress_callback
    
    # Create a queue to collect steps
    step_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
    analysis_complete = asyncio.Event()
    analysis_error = None
    final_report = None
    
    try:
        session = analysis_sessions[session_id]
        session["status"] = "researching"
        session["message"] = "Research Agent: Gathering competitor information from the web..."
        session["steps"] = []
        
        def update_progress(step_data):
            """Update session and queue step for streaming"""
            try:
                if session_id in analysis_sessions:
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
                    
                    analysis_sessions[session_id]["steps"].append(step_entry)
                    analysis_sessions[session_id]["message"] = step_entry["message"]
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
        
        # Start analysis in background
        async def run_analysis():
            nonlocal analysis_error, final_report
            try:
                report = await run_competitor_analysis(
                    company_name=company_name,
                    competitors=competitors,
                    focus_areas=focus_areas
                )
                session["status"] = "completed"
                session["message"] = "✅ Analysis complete! Report generated successfully."
                session["report"] = report
                final_report = report
                analysis_complete.set()
            except Exception as e:
                session["status"] = "error"
                session["message"] = f"❌ Error: {str(e)}"
                session["error"] = str(e)
                analysis_error = str(e)
                analysis_complete.set()
            finally:
                set_progress_callback(None)
        
        # Start analysis task
        analysis_task = asyncio.create_task(run_analysis())
        
        # Stream initial connection
        yield f"data: {json.dumps({'status': 'connected', 'message': 'Starting competitor analysis...'})}\n\n"
        
        # Stream steps as they come
        while not analysis_complete.is_set():
            try:
                # Wait for next step with short timeout to check completion
                try:
                    step_data = await asyncio.wait_for(step_queue.get(), timeout=0.1)
                    # Stream the step immediately
                    logger.info(f"Streaming step: {step_data.get('message', '')[:50]}...")
                    yield f"data: {json.dumps({'step': step_data, 'status': 'processing'})}\n\n"
                except asyncio.TimeoutError:
                    # No step available, check if analysis is done
                    if analysis_complete.is_set():
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
        
        # Wait for analysis to complete
        await analysis_task
        
        # Send final result
        if final_report:
            yield f"data: {json.dumps({'done': True, 'status': 'completed', 'report': final_report})}\n\n"
        elif analysis_error:
            yield f"data: {json.dumps({'done': True, 'status': 'error', 'error': analysis_error})}\n\n"
        
    except Exception as e:
        logger.error(f"Error streaming analysis for session {session_id}: {e}")
        yield f"data: {json.dumps({'error': str(e), 'status': 'error'})}\n\n"
        set_progress_callback(None)


# ============================================================================
# STEP 4: API ENDPOINTS
# ============================================================================
"""
API Endpoints:
- POST /start-analysis: Start a new competitor analysis
- GET /status/{session_id}: Get analysis status
- GET /result/{session_id}: Get final analysis report
- GET /health: Health check
"""
@router.get("/health", response_model=ServiceInfo)
async def health_check():
    """Health check endpoint"""
    return ServiceInfo(
        status="healthy",
        service="competitor-analysis",
        description="Multi-agent competitor analysis research system with web search integration"
    )


@router.post("/start-analysis", response_model=AnalysisResponse)
async def start_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Start a competitor analysis workflow
    
    This endpoint:
    1. Creates a new analysis session
    2. Starts background processing with multiple agents
    3. Returns session ID for status checking
    
    The analysis uses three agents:
    - Research Agent: Gathers information from the web
    - Analysis Agent: Analyzes competitive positioning
    - Report Agent: Creates comprehensive report
    """
    try:
        session_id = str(uuid.uuid4())
        
        # Initialize session
        analysis_sessions[session_id] = {
            "session_id": session_id,
            "status": "processing",
            "message": "Initializing competitor analysis...",
            "company_name": request.company_name,
            "competitors": request.competitors,
            "focus_areas": request.focus_areas,
            "report": None,
            "error": None,
            "steps": []  # Track research steps
        }
        
        # Start background processing
        background_tasks.add_task(
            process_analysis,
            session_id,
            request.company_name,
            request.competitors,
            request.focus_areas or ["pricing", "features", "market position"]
        )
        
        logger.info(f"Started analysis for session: {session_id}")
        
        return AnalysisResponse(
            session_id=session_id,
            status="processing",
            message="Competitor analysis started. Use the session_id to check status.",
            company_name=request.company_name,
            competitors=request.competitors
        )
        
    except Exception as e:
        logger.error(f"Error starting analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting analysis: {str(e)}")


@router.post("/start-analysis-stream")
async def start_analysis_stream(request: AnalysisRequest):
    """
    Start a competitor analysis workflow with real-time streaming
    
    This endpoint streams research steps in real-time as they happen,
    similar to ChatGPT/Grok's deep research display.
    """
    try:
        session_id = str(uuid.uuid4())
        
        # Initialize session
        analysis_sessions[session_id] = {
            "session_id": session_id,
            "status": "processing",
            "message": "Initializing competitor analysis...",
            "company_name": request.company_name,
            "competitors": request.competitors,
            "focus_areas": request.focus_areas,
            "report": None,
            "error": None,
            "steps": []
        }
        
        logger.info(f"Started streaming analysis for session: {session_id}")
        
        return StreamingResponse(
            stream_analysis_steps(
                session_id,
                request.company_name,
                request.competitors,
                request.focus_areas or ["pricing", "features", "market position"]
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
        
    except Exception as e:
        logger.error(f"Error starting streaming analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting analysis: {str(e)}")


@router.get("/status/{session_id}", response_model=AnalysisResponse)
async def get_status(session_id: str):
    """Get analysis status for a session"""
    if session_id not in analysis_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = analysis_sessions[session_id]
    return AnalysisResponse(
        session_id=session_id,
        status=session["status"],
        message=session["message"],
        company_name=session["company_name"],
        competitors=session["competitors"],
        steps=session.get("steps", [])
    )


@router.get("/result/{session_id}", response_model=AnalysisResult)
async def get_result(session_id: str):
    """Get final analysis result for a session"""
    if session_id not in analysis_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = analysis_sessions[session_id]
    
    if session["status"] == "processing" or session["status"] == "researching":
        raise HTTPException(
            status_code=400,
            detail="Analysis still in progress. Please check status endpoint."
        )
    
    return AnalysisResult(
        session_id=session_id,
        status=session["status"],
        company_name=session["company_name"],
        competitors=session["competitors"],
        report=session.get("report"),
        error=session.get("error"),
        steps=session.get("steps", [])
    )


@router.get("/learning-objectives")
async def get_learning_objectives():
    """Get learning objectives for this demo"""
    return {
        "demo": "Competitor Analysis Research Agent",
        "objectives": [
            "Understand tool calling and function integration in AI agents",
            "Learn multi-agent coordination and communication patterns",
            "Implement web search integration using DuckDuckGo",
            "Build workflow orchestration for complex research tasks",
            "Create specialized agents with distinct roles and tools"
        ],
        "technologies": [
            "LangChain Agents",
            "DuckDuckGo Search",
            "Web Scraping",
            "Multi-Agent Systems",
            "FastAPI"
        ],
        "concepts": [
            "Tool Calling",
            "Multi-Agent Coordination",
            "Web Search Integration",
            "Workflow Orchestration",
            "Agent Specialization"
        ]
    }

