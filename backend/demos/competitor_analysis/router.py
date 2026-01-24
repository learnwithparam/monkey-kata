from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
import uuid
import logging

from .models import AnalysisRequest, AnalysisResponse, AnalysisResult, ServiceInfo
from .service import process_analysis, stream_analysis_steps, analysis_sessions

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/competitor-analysis", tags=["competitor-analysis"])

@router.get("/health", response_model=ServiceInfo)
async def health_check():
    return ServiceInfo(
        status="healthy",
        service="competitor-analysis",
        description="Multi-agent competitor analysis"
    )

@router.post("/start-analysis", response_model=AnalysisResponse)
async def start_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    session_id = str(uuid.uuid4())
    analysis_sessions[session_id] = {
        "session_id": session_id, "status": "processing", "message": "Initializing...",
        "company_name": request.company_name, "competitors": request.competitors,
        "focus_areas": request.focus_areas, "steps": []
    }
    background_tasks.add_task(process_analysis, session_id, request.company_name, request.competitors, request.focus_areas)
    return AnalysisResponse(session_id=session_id, status="processing", message="Started", **request.dict())

@router.post("/start-analysis-stream")
async def start_analysis_stream(request: AnalysisRequest):
    session_id = str(uuid.uuid4())
    analysis_sessions[session_id] = {
        "session_id": session_id, "status": "processing", "message": "Initializing...",
        "company_name": request.company_name, "competitors": request.competitors,
        "focus_areas": request.focus_areas, "steps": []
    }
    return StreamingResponse(
        stream_analysis_steps(session_id, request.company_name, request.competitors, request.focus_areas or []),
        media_type="text/event-stream"
    )

@router.get("/status/{session_id}", response_model=AnalysisResponse)
async def get_status(session_id: str):
    if session_id not in analysis_sessions: raise HTTPException(status_code=404)
    return AnalysisResponse(**analysis_sessions[session_id])

@router.get("/result/{session_id}", response_model=AnalysisResult)
async def get_result(session_id: str):
    if session_id not in analysis_sessions: raise HTTPException(status_code=404)
    s = analysis_sessions[session_id]
    if s["status"] in ["processing", "researching"]: raise HTTPException(status_code=400, detail="In progress")
    return AnalysisResult(**s)
