"""
Legal Case Intake Data Models
==============================

Data models for legal case intake workflow.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class CaseStatus(str, Enum):
    """Case status enumeration"""
    INTAKE = "intake"
    REVIEW = "review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING_LAWYER = "pending_lawyer"


class CaseIntake(BaseModel):
    """Initial case intake information"""
    client_name: str = Field(..., description="Client's full name")
    client_email: str = Field(..., description="Client's email address")
    client_phone: Optional[str] = Field(None, description="Client's phone number")
    case_type: str = Field(..., description="Type of legal case")
    case_description: str = Field(..., description="Detailed description of the case")
    urgency: str = Field(default="normal", description="Urgency level: low, normal, high, urgent")
    additional_info: Optional[str] = Field(None, description="Any additional information")


class CaseIntakeRequest(BaseModel):
    """Request to start case intake"""
    client_name: str = Field(..., min_length=1, description="Client's full name")
    client_email: str = Field(..., description="Client's email address")
    client_phone: Optional[str] = Field(None, description="Client's phone number")
    case_type: str = Field(..., min_length=1, description="Type of legal case")
    case_description: str = Field(..., min_length=10, description="Detailed description of the case")
    urgency: str = Field(default="normal", description="Urgency level: low, normal, high, urgent")
    additional_info: Optional[str] = Field(None, description="Any additional information")


class CaseIntakeResponse(BaseModel):
    """Response with case intake status"""
    case_id: str
    status: str
    message: str
    steps: Optional[List[Dict[str, Any]]] = None
    needs_more_info: Optional[bool] = False
    missing_info: Optional[List[str]] = None
    is_complete: Optional[bool] = False
    intake_summary: Optional[str] = None
    risk_assessment: Optional[str] = None
    recommended_action: Optional[str] = None


class CaseReviewRequest(BaseModel):
    """Request for lawyer review"""
    case_id: str
    lawyer_notes: Optional[str] = Field(None, description="Lawyer's review notes")
    lawyer_decision: str = Field(..., description="Lawyer's decision: approve, reject, request_info")


class CaseReviewResponse(BaseModel):
    """Response with case review information"""
    case_id: str
    status: str
    intake_data: CaseIntake
    intake_summary: Optional[str] = None
    risk_assessment: Optional[str] = None
    recommended_action: Optional[str] = None
    lawyer_notes: Optional[str] = None
    lawyer_decision: Optional[str] = None


class AdditionalInfoRequest(BaseModel):
    """Request to provide additional case information"""
    case_id: str
    additional_info: str = Field(..., description="Additional information requested by the AI")


class CaseReview(BaseModel):
    """Case review information"""
    case_id: str
    intake_data: CaseIntake
    intake_summary: str = Field(..., description="AI-generated summary of the case")
    risk_assessment: str = Field(..., description="AI assessment of case risks")
    recommended_action: str = Field(..., description="AI recommendation")
    lawyer_notes: Optional[str] = Field(None, description="Lawyer's review notes")
    lawyer_decision: Optional[str] = Field(None, description="Lawyer's decision: approve, reject, request_info")
    status: CaseStatus = CaseStatus.INTAKE


class CaseResult(BaseModel):
    """Final case result"""
    case_id: str
    status: CaseStatus
    intake_data: CaseIntake
    intake_summary: str
    risk_assessment: str
    recommended_action: str
    lawyer_notes: Optional[str] = None
    lawyer_decision: Optional[str] = None
    created_at: datetime
    reviewed_at: Optional[datetime] = None


class ServiceInfo(BaseModel):
    """Health check response"""
    status: str
    service: str
    description: str


