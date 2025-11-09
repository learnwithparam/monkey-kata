"""
Lead Scoring Data Models
=========================

🎯 LEARNING OBJECTIVES:
This module defines the data models used throughout the lead scoring demo:

1. Candidate - Represents a candidate from CSV upload
2. CandidateScore - Score and reasoning for a candidate
3. ScoredCandidate - Candidate with their score attached

Key Learning: Separating models into their own file:
- Eliminates circular imports
- Makes models reusable across modules
- Keeps code organized and maintainable
"""

from pydantic import BaseModel


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

