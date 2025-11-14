"""
Job Application Form Filling Data Models
========================================

Data models for job application form filling workflow.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


class WorkExperience(BaseModel):
    """Work experience entry"""
    company: str = Field(..., description="Company name")
    role: str = Field(..., description="Job title/role")
    start_date: str = Field(..., description="Start date")
    end_date: Optional[str] = Field(None, description="End date (None if current)")
    description: str = Field(..., description="Job description/responsibilities")


class Education(BaseModel):
    """Education entry"""
    degree: str = Field(..., description="Degree name")
    institution: str = Field(..., description="Institution name")
    graduation_date: Optional[str] = Field(None, description="Graduation date")
    gpa: Optional[str] = Field(None, description="GPA if available")


class ResumeData(BaseModel):
    """Extracted resume/CV data"""
    # Personal Information
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[str] = Field(None, description="Address")
    
    # Work Experience
    work_experience: List[WorkExperience] = Field(default_factory=list, description="Work experience entries")
    
    # Education
    education: List[Education] = Field(default_factory=list, description="Education entries")
    
    # Skills
    skills: List[str] = Field(default_factory=list, description="List of skills")
    
    # Additional
    summary: Optional[str] = Field(None, description="Professional summary")


class FormField(BaseModel):
    """Individual form field definition"""
    name: str = Field(..., description="Field name")
    label: str = Field(..., description="Field label")
    type: str = Field(..., description="Field type (text, email, tel, textarea, etc.)")
    section: str = Field(..., description="Form section this field belongs to")
    value: Optional[str] = Field(None, description="Field value")
    required: bool = Field(default=True, description="Whether field is required")


class FormStructure(BaseModel):
    """Form structure definition"""
    sections: List[str] = Field(..., description="List of form sections")
    fields: List[FormField] = Field(..., description="List of form fields")


class JobListing(BaseModel):
    """Job listing data structure"""
    job_title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: str = Field(..., description="Job location")
    description: str = Field(..., description="Job description")
    requirements: List[str] = Field(default_factory=list, description="Job requirements")
    benefits: List[str] = Field(default_factory=list, description="Job benefits")
    application_instructions: Optional[str] = Field(None, description="Application instructions")


class ResumeUploadResponse(BaseModel):
    """Response after resume upload and parsing"""
    session_id: str = Field(..., description="Session ID for tracking")
    resume_data: ResumeData = Field(..., description="Parsed resume data")
    status: str = Field(default="parsed", description="Processing status")
    message: str = Field(default="Resume parsed successfully", description="Status message")


class FormFillProgress(BaseModel):
    """Form filling progress update"""
    field_name: str = Field(..., description="Field being filled")
    field_label: str = Field(..., description="Field label")
    value: str = Field(..., description="Value being filled")
    section: str = Field(..., description="Section name")
    progress: float = Field(..., description="Overall progress (0-1)")
    message: str = Field(..., description="Progress message")


class FormFillResponse(BaseModel):
    """Response with filled form data"""
    session_id: str = Field(..., description="Session ID")
    filled_fields: List[FormField] = Field(..., description="List of filled form fields")
    status: str = Field(default="completed", description="Completion status")
    message: str = Field(default="Form filled successfully", description="Status message")

