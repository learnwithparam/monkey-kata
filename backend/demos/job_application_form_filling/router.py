from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Body
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Optional
import uuid
import tempfile
import os
import shutil

from .models import ResumeUploadResponse, FormStructure, JobListing, ServiceInfo, FormField
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

@router.get("/job-listing", response_model=JobListing)
async def get_job_listing():
    return JobListing(
        job_title="Senior AI Engineer",
        company="TechCorp AI",
        location="San Francisco, CA (Hybrid)",
        description="""We are looking for an experienced AI Engineer to lead our LLM infrastructure team. 
        
        You will be responsible for designing and implementing scalable AI solutions, optimizing model performance, and working closely with our product leads to deliver cutting-edge AI features.
        
        The ideal candidate has a strong background in deep learning, distributed systems, and modern software engineering practices.""",
        requirements=[
            "5+ years of Python experience",
            "Experience with PyTorch or TensorFlow",
            "Knowledge of RAG systems and Vector Databases",
            "Experience deploying LLMs in production",
            "Strong communication skills"
        ],
        benefits=[
            "Competitive salary and equity",
            "Remote work options",
            "Health, Dental, and Vision insurance",
            "401(k) matching",
            "Unlimited PTO"
        ],
        application_instructions="Please upload your resume and fill out the application form below ensuring all sections are complete."
    )

@router.get("/form-structure", response_model=FormStructure)
async def get_form_structure():
    return FormStructure(
        sections=["Personal Information", "Work Experience", "Education", "Additional Information"],
        fields=[
            # Personal Information
            FormField(name="name", label="Full Name", type="text", section="Personal Information"),
            FormField(name="email", label="Email Address", type="email", section="Personal Information"),
            FormField(name="phone", label="Phone Number", type="tel", section="Personal Information"),
            FormField(name="address", label="Address", type="text", section="Personal Information", required=False),
            
            # Work Experience
            FormField(name="company", label="Company Name", type="text", section="Work Experience"),
            FormField(name="role", label="Job Title", type="text", section="Work Experience"),
            FormField(name="start_date", label="Start Date", type="text", section="Work Experience"),
            FormField(name="end_date", label="End Date", type="text", section="Work Experience", required=False),
            FormField(name="description", label="Job Description", type="textarea", section="Work Experience"),
            
            # Education
            FormField(name="degree", label="Degree", type="text", section="Education"),
            FormField(name="institution", label="Institution", type="text", section="Education"),
            FormField(name="graduation_date", label="Graduation Date", type="text", section="Education"),
            FormField(name="gpa", label="GPA", type="text", section="Education", required=False),
            
            # Additional Information
            FormField(name="linkedin", label="LinkedIn Profile", type="url", section="Additional Information", required=False),
            FormField(name="portfolio", label="Portfolio URL", type="url", section="Additional Information", required=False),
            FormField(name="cover_letter", label="Cover Letter", type="textarea", section="Additional Information", required=False)
        ]
    )
