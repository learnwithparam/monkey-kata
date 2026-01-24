from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any, AsyncGenerator
import asyncio
import uuid
import json
import io
import csv
import logging

from .models import Candidate, ScoredCandidate, LeadScoringResponse, TopCandidatesResponse, FeedbackRequest, EmailGenerationRequest, EmailGenerationResponse, EmailResult, ServiceInfo, ScoredLead
from .service import process_lead_scoring, processing_sessions, email_results
from .lead_scoring_crews import generate_emails_parallel
from utils.thinking_streamer import ThinkingStreamer


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lead-scoring", tags=["lead-scoring"])

JOB_DESCRIPTION = """
# Python & AI Engineer
... (Standard Job Description)
"""

@router.get("/health", response_model=ServiceInfo)
async def health_check():
    return ServiceInfo(
        status="healthy",
        service="lead-scoring",
        description="AI-powered lead scoring using CrewAI",
        sessions_processed=len(processing_sessions)
    )

@router.post("/upload-leads", response_model=LeadScoringResponse)
async def upload_leads(file: UploadFile = File(...), job_description: Optional[str] = Form(None)):
    try:
        session_id = str(uuid.uuid4())
        content = await file.read()
        reader = csv.DictReader(io.StringIO(content.decode('utf-8')))
        candidates = [Candidate(**row) for row in reader]
        
        job_desc = job_description or JOB_DESCRIPTION
        processing_sessions[session_id] = {
            "session_id": session_id, "status": "processing", "candidates": [c.dict() for c in candidates],
            "candidate_scores": [], "scored_candidates": [], "feedback": "",
            "job_description": job_desc, "total_leads": len(candidates)
        }
        
        asyncio.create_task(process_lead_scoring(session_id, candidates, job_desc, ""))
        return LeadScoringResponse(session_id=session_id, status="processing", message="Processing leads...", total_leads=len(candidates))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{session_id}", response_model=LeadScoringResponse)
async def get_status(session_id: str):
    if session_id not in processing_sessions: raise HTTPException(status_code=404)
    s = processing_sessions[session_id]
    return LeadScoringResponse(session_id=session_id, **s)

@router.get("/top-candidates/{session_id}", response_model=TopCandidatesResponse)
async def get_top_candidates(session_id: str):
    if session_id not in processing_sessions: raise HTTPException(status_code=404)
    s = processing_sessions[session_id]
    all_c = [ScoredLead(**c) for c in s["scored_candidates"]]
    return TopCandidatesResponse(session_id=session_id, top_candidates=all_c[:3], all_candidates=all_c)

@router.post("/feedback")
async def provide_feedback(request: FeedbackRequest):
    if request.session_id not in processing_sessions: raise HTTPException(status_code=404)
    s = processing_sessions[request.session_id]
    candidates = [Candidate(**c) for c in s["candidates"]]
    asyncio.create_task(process_lead_scoring(request.session_id, candidates, s["job_description"], request.feedback))
    return {"message": "Re-scoring started"}

@router.post("/generate-emails", response_model=EmailGenerationResponse)
async def generate_emails(request: EmailGenerationRequest):
    if request.session_id not in processing_sessions: raise HTTPException(status_code=404)
    s = processing_sessions[request.session_id]
    scored_candidates = [ScoredCandidate(**c) for c in s["scored_candidates"]]
    top_ids = {c.id for c in scored_candidates[:3]} if request.proceed_with_top_3 else set()
    results = await generate_emails_parallel(scored_candidates, top_ids)
    emails = [EmailResult(**r) for r in results]
    email_results[request.session_id] = [e.dict() for e in emails]
    return EmailGenerationResponse(session_id=request.session_id, emails=emails, total_emails=len(emails))

@router.get("/stream/{session_id}")
async def stream_session(session_id: str):
    if session_id not in processing_sessions: raise HTTPException(status_code=404)
    async def event_generator():
        while True:
            s = processing_sessions[session_id]
            yield f"data: {json.dumps({'status_update': s})}\n\n"
            if s["status"] in ["completed", "error"]: break
            await asyncio.sleep(1)
        yield f"data: {json.dumps({'done': True})}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")
