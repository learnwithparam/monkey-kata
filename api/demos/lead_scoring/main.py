"""
Lead Scoring API
=================

🎯 LEARNING OBJECTIVES:
This demo teaches you how to build a multi-crew lead scoring system with CrewAI:

1. CrewAI Crews - How to create specialized teams of agents
2. Human-in-the-Loop - How to integrate human feedback into AI workflows
3. Parallel Processing - How to score multiple leads concurrently
4. State Management - How to manage workflow state across multiple crews
5. Email Generation - How to generate personalized emails using AI agents

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Setup - Initialize providers and storage
Step 2: Data Models - Define request structures
Step 3: Utility Functions - Parse CSV, combine data, score and generate emails
Step 4: Background Processing - Async lead scoring workflow
Step 5: API Endpoints - Expose functionality via HTTP

Key Concept: This demo uses CrewAI to orchestrate multiple specialized crews
that work together to score leads, gather human feedback, and generate personalized emails.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import asyncio
import uuid
import logging
import csv
import io

from utils.llm_provider import get_llm_provider
from .lead_scoring_crews import score_candidates_parallel, generate_emails_parallel
from .models import Candidate, CandidateScore, ScoredCandidate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# STEP 1: SETUP & INITIALIZATION
# ============================================================================
"""
Understanding Lead Scoring Components:
- LLM Provider: Powers all AI agents (we know this from previous demos)
- Lead Score Crew: Scores individual candidates against job description
- Lead Response Crew: Generates personalized emails for candidates
- In-Memory Storage: Stores processing state and results

Multi-Crew Workflow:
Unlike simple single-agent systems, this uses multiple specialized crews:
1. Lead Score Crew: Evaluates candidates and assigns scores
2. Lead Response Crew: Generates personalized follow-up emails
3. Flow Orchestration: Coordinates crews with human-in-the-loop feedback

Note: This uses in-memory storage for simplicity. In production,
you'd use a persistent database and job queue system.
"""
router = APIRouter(prefix="/lead-scoring", tags=["lead-scoring"])

# Initialize providers
llm_provider = get_llm_provider()

# Default job description
JOB_DESCRIPTION = """
# Python & AI Engineer

**Position:** Python & AI Engineer  
**Duration:** 12-month contract with the possibility of extension based on performance and project needs.

We are seeking a motivated Python & AI Engineer to join our team and assist in the development of our cutting-edge AI-powered backend systems. This project involves building scalable APIs, integrating AI/ML models, and developing robust backend services using Python and modern frameworks.

**Key Responsibilities:**
- Develop and maintain Python-based backend services and RESTful APIs.
- Integrate AI/ML models and LLM APIs (OpenAI, Anthropic, etc.) into backend services.
- Build scalable microservices using FastAPI, Flask, or similar frameworks.
- Work with databases (PostgreSQL, MongoDB) and design efficient data models.
- Implement async processing, background jobs, and task queues.
- Collaborate with senior engineers to design and implement new features.
- Optimize API performance, handle caching, and ensure system reliability.
- Participate in code reviews and contribute to best practices.
- Troubleshoot and debug issues to ensure the highest quality of backend services.

**Qualifications:**
- 1-3 years of experience in backend development with Python.
- Proficiency in Python, async/await, and modern Python frameworks (FastAPI, Flask, Django).
- Experience with Node.js or similar backend technologies is a plus.
- Strong understanding of RESTful APIs, GraphQL, and API design principles.
- Experience with AI/ML libraries (LangChain, CrewAI, OpenAI SDK) is highly desirable.
- Familiarity with databases (SQL and NoSQL), ORMs, and data modeling.
- Experience with Git, Docker, and cloud platforms (AWS, GCP, Azure).
- Knowledge of message queues (RabbitMQ, Redis, Celery) and async processing.
- Strong problem-solving skills and attention to detail.
- Excellent communication and teamwork abilities.
- Ability to work independently and take initiative on projects.

**What We Offer:**
- Opportunity to work with cutting-edge AI technologies and LLM integrations.
- Collaborative and supportive work environment.
- Mentorship from senior engineers to help grow your skills.
- Potential for role extension and career advancement within the company.
- Flexible working hours and the possibility of remote work.

This role is ideal for someone looking to grow their skills in Python backend development, AI/ML integration, and building scalable systems while contributing to impactful projects.
"""

# In-memory storage (use database in production)
processing_sessions: Dict[str, Dict[str, Any]] = {}
email_results: Dict[str, List[Dict[str, str]]] = {}


# ============================================================================
# STEP 2: DATA MODELS
# ============================================================================
"""
Request Models:
- LeadScoringResponse: Processing status and session information
- ScoredLead: Individual lead with score and reasoning
- EmailGenerationRequest: Request to generate emails for scored leads
- EmailResult: Generated email for a specific lead

These models ensure type safety and automatic validation.
"""
class LeadScoringResponse(BaseModel):
    """Response with processing status"""
    session_id: str
    status: str
    message: str
    total_leads: int = 0
    progress: int = 0  # 0-100 percentage
    current_candidate: Optional[str] = None  # Name of candidate currently being scored
    scored_count: int = 0  # Number of candidates scored so far
    workflow_stage: Optional[str] = None  # "initial_scoring", "rescoring", "email_generation", etc.
    partial_results: Optional[List[Dict[str, Any]]] = None  # Partial results for real-time display


class ScoredLead(BaseModel):
    """Scored lead with analysis"""
    id: str
    name: str
    email: str
    bio: str
    skills: str
    score: int
    reason: str


class TopCandidatesResponse(BaseModel):
    """Top candidates for review"""
    session_id: str
    top_candidates: List[ScoredLead]
    all_candidates: List[ScoredLead]


class FeedbackRequest(BaseModel):
    """Human feedback for re-scoring"""
    session_id: str
    feedback: str = Field(..., min_length=1, description="Additional feedback for scoring")


class EmailGenerationRequest(BaseModel):
    """Request to generate emails"""
    session_id: str
    proceed_with_top_3: bool = Field(True, description="Whether to proceed with top 3 candidates")


class EmailResult(BaseModel):
    """Generated email for a lead"""
    candidate_id: str
    candidate_name: str
    email_content: str
    is_top_candidate: bool


class EmailGenerationResponse(BaseModel):
    """Response with generated emails"""
    session_id: str
    emails: List[EmailResult]
    total_emails: int


class ServiceInfo(BaseModel):
    """Health check response"""
    status: str
    service: str
    description: str
    sessions_processed: int


# ============================================================================
# STEP 3: UTILITY FUNCTIONS
# ============================================================================
"""
Utility Functions:
- parse_csv_leads: Parse CSV content into Candidate objects
- combine_candidates_with_scores: Merge candidate data with scores

Note: Crew creation and execution logic is in lead_scoring_crews.py
"""
async def parse_csv_leads(csv_content: str) -> List[Candidate]:
    """Parse CSV content into Candidate objects"""
    try:
        candidates = []
        reader = csv.DictReader(io.StringIO(csv_content))
        
        for row in reader:
            required_fields = ['id', 'name', 'email', 'bio', 'skills']
            if not all(field in row for field in required_fields):
                raise ValueError(f"Missing required fields. Expected: {required_fields}")
            
            candidate = Candidate(
                id=row['id'].strip(),
                name=row['name'].strip(),
                email=row['email'].strip(),
                bio=row['bio'].strip(),
                skills=row['skills'].strip()
            )
            candidates.append(candidate)
        
        if not candidates:
            raise ValueError("No candidates found in CSV file")
        
        return candidates
    
    except Exception as e:
        logger.error(f"Error parsing CSV: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")


def combine_candidates_with_scores(
    candidates: List[Candidate], candidate_scores: List[CandidateScore]
) -> List[ScoredCandidate]:
    """Combine candidates with their scores"""
    score_dict = {score.id: score for score in candidate_scores}
    
    scored_candidates = []
    for candidate in candidates:
        score = score_dict.get(candidate.id)
        if score:
            scored_candidates.append(
                ScoredCandidate(
                    id=candidate.id,
                    name=candidate.name,
                    email=candidate.email,
                    bio=candidate.bio,
                    skills=candidate.skills,
                    score=score.score,
                    reason=score.reason,
                )
            )
    
    return scored_candidates




# ============================================================================
# STEP 4: BACKGROUND PROCESSING
# ============================================================================
"""
Background Processing:
When leads are uploaded, we process them asynchronously:
1. Parse CSV into candidate objects
2. Score all candidates in parallel
3. Combine scores with candidate data
4. Sort by score
5. Store results in session
"""
async def process_lead_scoring(
    session_id: str,
    candidates: List[Candidate],
    job_description: str,
    feedback: str
):
    """Background task to score leads with progress tracking"""
    try:
        session = processing_sessions[session_id]
        is_rescoring = bool(feedback and feedback.strip())
        
        # Set initial status with context
        if is_rescoring:
            session["status"] = "scoring"
            session["message"] = "Lead Scoring Crew: HR Evaluation Agent re-analyzing candidates with your feedback..."
            session["workflow_stage"] = "rescoring"
        else:
            session["status"] = "scoring"
            session["message"] = "Lead Scoring Crew: HR Evaluation Agent analyzing candidates against job requirements..."
            session["workflow_stage"] = "initial_scoring"
        
        session["progress"] = 0
        session["scored_count"] = 0
        session["current_candidate"] = None
        session["partial_results"] = []  # Initialize for real-time results
        total = len(candidates)
        
        def update_progress(current: int, total: int, candidate_name: Optional[str] = None, candidate_score: Optional[CandidateScore] = None):
            """Update progress in session and store partial results for real-time display"""
            if session_id in processing_sessions:
                session = processing_sessions[session_id]
                progress = int((current / total) * 100) if total > 0 else 0
                session["progress"] = progress
                session["scored_count"] = current
                
                # Store partial results for real-time display
                if candidate_score:
                    # Initialize partial_results if not exists
                    if "partial_results" not in session:
                        session["partial_results"] = []
                    
                    # Find candidate data
                    candidate_data = next((c for c in candidates if c.id == candidate_score.id), None)
                    if candidate_data:
                        scored_candidate = ScoredCandidate(
                            id=candidate_data.id,
                            name=candidate_data.name,
                            email=candidate_data.email,
                            bio=candidate_data.bio,
                            skills=candidate_data.skills,
                            score=candidate_score.score,
                            reason=candidate_score.reason
                        )
                        # Update or add to partial results
                        partial_results = session["partial_results"]
                        existing_idx = next((i for i, r in enumerate(partial_results) if r["id"] == candidate_score.id), None)
                        if existing_idx is not None:
                            partial_results[existing_idx] = scored_candidate.dict()
                        else:
                            partial_results.append(scored_candidate.dict())
                        # Sort by score descending
                        partial_results.sort(key=lambda x: x.get("score", 0), reverse=True)
                
                if candidate_name:
                    session["current_candidate"] = candidate_name
                    if is_rescoring:
                        session["message"] = f"Lead Scoring Crew: HR Evaluation Agent re-evaluating {candidate_name} with your feedback ({current}/{total})"
                    else:
                        session["message"] = f"Lead Scoring Crew: HR Evaluation Agent evaluating {candidate_name} ({current}/{total})"
                else:
                    session["current_candidate"] = None
                    if current < total:
                        if is_rescoring:
                            session["message"] = f"Lead Scoring Crew: Completed {current} of {total} candidates (incorporating feedback)"
                        else:
                            session["message"] = f"Lead Scoring Crew: Completed {current} of {total} candidates"
                    else:
                        session["message"] = f"Lead Scoring Crew: Processing results and ranking candidates by score..."
        
        # Score all candidates with progress updates
        candidate_scores = await score_candidates_parallel(
            candidates,
            job_description,
            feedback,
            progress_callback=update_progress
        )
        
        # Store scores
        session["candidate_scores"] = [score.dict() for score in candidate_scores]
        
        # Combine candidates with scores
        scored_candidates = combine_candidates_with_scores(candidates, candidate_scores)
        
        # Sort by score
        scored_candidates_sorted = sorted(
            scored_candidates,
            key=lambda c: c.score,
            reverse=True
        )
        session["scored_candidates"] = [sc.dict() for sc in scored_candidates_sorted]
        
        # Update status
        session["status"] = "completed"
        if is_rescoring:
            session["message"] = f"Lead Scoring Crew: Successfully re-scored {len(candidate_scores)} candidates with your feedback"
        else:
            session["message"] = f"Lead Scoring Crew: Successfully scored {len(candidate_scores)} candidates"
        session["progress"] = 100
        session["current_candidate"] = None
        
        logger.info(f"Completed scoring for session: {session_id}")
        
    except Exception as e:
        logger.error(f"Error processing leads for session {session_id}: {e}")
        if session_id in processing_sessions:
            processing_sessions[session_id]["status"] = "error"
            processing_sessions[session_id]["message"] = f"Error: {str(e)}"


# ============================================================================
# STEP 5: API ENDPOINTS
# ============================================================================
"""
API Endpoints:
- POST /upload-leads: Upload CSV and start scoring
- GET /status/{session_id}: Get processing status
- GET /top-candidates/{session_id}: Get top candidates for review
- POST /feedback: Provide feedback for re-scoring
- POST /generate-emails: Generate emails for all leads
- GET /emails/{session_id}: Get generated emails
- GET /health: Health check
"""
@router.get("/health", response_model=ServiceInfo)
async def health_check():
    """Health check endpoint"""
    return ServiceInfo(
        status="healthy",
        service="lead-scoring",
        description="AI-powered lead scoring and email generation system using CrewAI",
        sessions_processed=len(processing_sessions)
    )


@router.post("/upload-leads", response_model=LeadScoringResponse)
async def upload_leads(
    file: UploadFile = File(...),
    job_description: Optional[str] = Form(None)
):
    """
    Upload CSV file with leads and start scoring process
    
    CSV Format: id,name,email,bio,skills
    """
    try:
        session_id = str(uuid.uuid4())
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        if not file.filename.lower().endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are supported. Please upload a .csv file.")
        
        # Read file content
        try:
            content = await file.read()
            csv_content = content.decode('utf-8')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="File encoding error. Please ensure the CSV file is UTF-8 encoded.")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
        
        # Parse CSV
        candidates = await parse_csv_leads(csv_content)
        
        # IMPORTANT: Job Description Priority
        # 1. If user provides a job description in the text area (non-empty), use that
        # 2. If user doesn't provide one (None or empty/whitespace-only string), use the default JOB_DESCRIPTION
        # This allows users to customize the job description for their specific needs
        # Example: User enters "Python Developer" → uses "Python Developer"
        #          User leaves it empty → uses default "Python & AI Engineer" description
        if job_description and job_description.strip():
            job_desc = job_description.strip()
        else:
            job_desc = JOB_DESCRIPTION
        
        # Initialize session
        processing_sessions[session_id] = {
            "session_id": session_id,
            "status": "processing",
            "candidates": [c.dict() for c in candidates],
            "candidate_scores": [],
            "scored_candidates": [],
            "feedback": "",
            "job_description": job_desc,
            "total_leads": len(candidates)
        }
        
        # Start background processing
        asyncio.create_task(
            process_lead_scoring(session_id, candidates, job_desc, "")
        )
        
        logger.info(f"Started processing {len(candidates)} leads for session: {session_id}")
        
        return LeadScoringResponse(
            session_id=session_id,
            status="processing",
            message=f"Processing {len(candidates)} leads...",
            total_leads=len(candidates),
            progress=0,
            current_candidate=None,
            scored_count=0,
            workflow_stage="initial_scoring"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading leads: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error uploading leads: {str(e)}")


@router.get("/status/{session_id}", response_model=LeadScoringResponse)
async def get_status(session_id: str):
    """Get processing status for a session"""
    if session_id not in processing_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = processing_sessions[session_id]
    return LeadScoringResponse(
        session_id=session_id,
        status=session["status"],
        message=session.get("message", ""),
        total_leads=session.get("total_leads", 0),
        progress=session.get("progress", 0),
        current_candidate=session.get("current_candidate"),
        scored_count=session.get("scored_count", 0),
        workflow_stage=session.get("workflow_stage")
    )


@router.get("/top-candidates/{session_id}", response_model=TopCandidatesResponse)
async def get_top_candidates(session_id: str):
    """Get top candidates for human review"""
    if session_id not in processing_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = processing_sessions[session_id]
    
    if session["status"] != "completed":
        raise HTTPException(status_code=400, detail="Scoring not completed yet. Please wait.")
    
    all_candidates = [ScoredLead(**c) for c in session["scored_candidates"]]
    top_candidates = all_candidates[:3]  # Show top 3 candidates
    
    return TopCandidatesResponse(
        session_id=session_id,
        top_candidates=top_candidates,
        all_candidates=all_candidates
    )


@router.post("/feedback", response_model=LeadScoringResponse)
async def provide_feedback(request: FeedbackRequest):
    """Provide feedback for re-scoring leads"""
    logger.info(f"Feedback request received for session: {request.session_id}")
    logger.info(f"Available sessions: {list(processing_sessions.keys())}")
    
    if request.session_id not in processing_sessions:
        logger.error(f"Session {request.session_id} not found in processing_sessions")
        raise HTTPException(
            status_code=404, 
            detail=f"Session not found. Available sessions: {list(processing_sessions.keys())[:5]}"
        )
    
    session = processing_sessions[request.session_id]
    session["feedback"] = request.feedback
    
    # Ensure candidates exist in session
    if "candidates" not in session or not session["candidates"]:
        raise HTTPException(
            status_code=400,
            detail="No candidates found in session. Please upload leads first."
        )
    
    candidates = [Candidate(**c) for c in session["candidates"]]
    job_description = session.get("job_description", "")
    
    # Start re-scoring with feedback
    asyncio.create_task(
        process_lead_scoring(request.session_id, candidates, job_description, request.feedback)
    )
    
    logger.info(f"Started re-scoring with feedback for session: {request.session_id}")
    
    return LeadScoringResponse(
        session_id=request.session_id,
        status="processing",
        message="Lead Scoring Crew: Starting re-scoring with your feedback...",
        total_leads=len(candidates),
        progress=0,
        current_candidate=None,
        scored_count=0,
        workflow_stage="rescoring"
    )


@router.post("/generate-emails", response_model=EmailGenerationResponse)
async def generate_emails(request: EmailGenerationRequest):
    """Generate personalized emails for all leads"""
    if request.session_id not in processing_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = processing_sessions[request.session_id]
    
    if session["status"] != "completed":
        raise HTTPException(status_code=400, detail="Scoring not completed yet. Please wait.")
    
    scored_candidates = [ScoredCandidate(**c) for c in session["scored_candidates"]]
    
    # Use top 3 candidates for email generation (or all if proceed_with_top_3 is False)
    top_candidate_ids = {c.id for c in scored_candidates[:3]} if request.proceed_with_top_3 else set()
    
    # Generate emails using crew functions
    email_results_list = await generate_emails_parallel(scored_candidates, top_candidate_ids)
    
    # Convert to EmailResult models
    generated_emails = [EmailResult(**result) for result in email_results_list]
    
    email_results[request.session_id] = [e.dict() for e in generated_emails]
    
    return EmailGenerationResponse(
        session_id=request.session_id,
        emails=generated_emails,
        total_emails=len(generated_emails)
    )


@router.get("/emails/{session_id}", response_model=EmailGenerationResponse)
async def get_emails(session_id: str):
    """Get generated emails for a session"""
    if session_id not in email_results:
        raise HTTPException(status_code=404, detail="Emails not found. Generate them first.")
    
    emails = [EmailResult(**e) for e in email_results[session_id]]
    
    return EmailGenerationResponse(
        session_id=session_id,
        emails=emails,
        total_emails=len(emails)
    )


@router.get("/learning-objectives")
async def get_learning_objectives():
    """Get learning objectives for this demo"""
    return {
        "demo": "Lead Scoring",
        "objectives": [
            "Understand CrewAI crews for orchestrating multi-agent workflows",
            "Learn human-in-the-loop patterns for AI systems",
            "Implement parallel processing for batch operations",
            "Build stateful workflows with feedback mechanisms",
            "Create personalized email generation systems",
            "Design APIs for complex AI workflows"
        ],
        "technologies": [
            "CrewAI",
            "Multi-Crew Orchestration",
            "Parallel Processing",
            "Human-in-the-Loop",
            "FastAPI"
        ],
        "concepts": [
            "Workflow Orchestration",
            "Lead Scoring",
            "Email Generation",
            "State Management",
            "Batch Processing"
        ]
    }