from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Body
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Optional
import uuid
import tempfile
import os
import shutil

from .models import ResumeUploadResponse, FormStructure, JobListing, ServiceInfo
from .resume_parser import parse_resume_pdf
from .html_parser import parse_html_form
from .service import stream_form_filling, sessions

router = APIRouter(prefix="/job-application-form-filling", tags=["job-application-form-filling"])

@router.get("/health", response_model=ServiceInfo)
async def health_check():
    return ServiceInfo(status="healthy", service="job-application", description="Form filling system")

@router.post("/upload-resume", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)
    with open(temp_path, "wb") as f: f.write(await file.read())
    resume_data = await parse_resume_pdf(temp_path)
    sessions[session_id] = {"session_id": session_id, "resume_data": resume_data.dict(), "status": "parsed"}
    shutil.rmtree(temp_dir)
    return ResumeUploadResponse(session_id=session_id, resume_data=resume_data, status="parsed", message="Parsed")

@router.post("/fill-form-stream")
async def fill_form_stream(session_id: str = Query(...), html_content: str = Body(...)):
    form_structure = parse_html_form(html_content)
    return StreamingResponse(stream_form_filling(session_id, form_structure), media_type="text/event-stream")
