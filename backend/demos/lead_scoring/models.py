"""
Lead Scoring Data Models
=========================
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class Candidate(BaseModel):
    """Candidate data from CSV"""
    id: str
    name: str
    email: str
    bio: str
    skills: str


class CandidateScore(BaseModel):
    """Score and reasoning for a candidate"""
    id: str
    score: int
    reason: str


class ScoredCandidate(BaseModel):
    """Candidate with score"""
    id: str
    name: str
    email: str
    bio: str
    skills: str
    score: int
    reason: str


class LeadScoringResponse(BaseModel):
    """Response with processing status"""
    session_id: str
    status: str
    message: str = ""
    total_leads: int = 0
    progress: int = 0
    current_candidate: Optional[str] = None
    scored_count: int = 0
    workflow_stage: Optional[str] = None
    partial_results: Optional[List[Dict[str, Any]]] = None


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
