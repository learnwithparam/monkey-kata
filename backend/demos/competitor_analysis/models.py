"""Competitor Analysis Data Models"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


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
    steps: Optional[List[Dict[str, Any]]] = None


class AnalysisResult(BaseModel):
    """Final analysis report"""
    session_id: str
    status: str
    company_name: str
    competitors: List[str]
    report: Optional[str] = None
    error: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None


class ServiceInfo(BaseModel):
    """Health check response"""
    status: str
    service: str
    description: str
