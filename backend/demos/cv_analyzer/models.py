from pydantic import BaseModel
from typing import Optional, List

class ProcessingStatus(BaseModel):
    """Status of CV processing"""
    document_id: str
    status: str  # "processing", "completed", "error"
    progress: int  # 0-100
    message: str
    pages_count: int = 0
    error: Optional[str] = None


class CVAnalysisResponse(BaseModel):
    """Complete CV analysis result from multi-agent system"""
    overall_score: int  # From Scorer Agent
    strengths: List[str]  # From Strengths Agent
    weaknesses: List[str]  # From Weaknesses Agent
    improvement_suggestions: List[str]  # From Suggester Agent
    keyword_match_score: int
    experience_relevance: int
    skills_alignment: int
    format_score: int


class ServiceInfo(BaseModel):
    """Health check response"""
    status: str
    service: str
    description: str
    documents_processed: int
    total_chunks: int
