"""
Influencer Discovery Data Models
=================================

Pydantic models for validating and structuring influencer discovery data.
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from datetime import datetime


class InfluencerProfile(BaseModel):
    """Represents a single influencer profile"""
    username: str = Field(..., description="Instagram username (without @)")
    profile_url: str = Field(..., description="Full URL to Instagram profile")
    follower_count: Optional[int] = Field(None, description="Number of followers")
    bio: Optional[str] = Field(None, description="Profile bio/description")
    content_focus: Optional[str] = Field(None, description="Main content focus (AI, tech, etc.)")
    has_own_platform: Optional[bool] = Field(None, description="Whether they have their own platform")
    collaboration_potential: Optional[str] = Field(None, description="Assessment of collaboration potential")
    location: Optional[str] = Field(None, description="Location if available")


class DiscoveryRequest(BaseModel):
    """Request to start influencer discovery"""
    min_followers: int = Field(default=10000, ge=1000, description="Minimum follower count")
    max_followers: Optional[int] = Field(None, description="Maximum follower count (optional)")
    content_keywords: List[str] = Field(
        default=["AI", "tech", "technology"],
        description="Keywords related to content focus"
    )
    location: str = Field(default="India", description="Target location")
    count: int = Field(default=5, ge=1, le=10, description="Number of influencers to find (1-10)")


class DiscoveryResponse(BaseModel):
    """Response with discovery status"""
    session_id: str
    status: str
    message: str
    criteria: DiscoveryRequest


class DiscoveryResult(BaseModel):
    """Final discovery results"""
    session_id: str
    status: str
    influencers: List[InfluencerProfile]
    total_found: int
    search_queries_used: List[str]
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class ServiceInfo(BaseModel):
    """Health check response"""
    status: str
    service: str
    description: str

