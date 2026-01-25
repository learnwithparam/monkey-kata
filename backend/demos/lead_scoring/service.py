from typing import List, Dict, Any, Optional
import logging
import asyncio

from .models import Candidate, CandidateScore, ScoredCandidate
from .lead_scoring_crews import score_candidates_parallel, generate_emails_parallel
from utils.thinking_streamer import ThinkingStreamer

logger = logging.getLogger(__name__)

processing_sessions: Dict[str, Dict[str, Any]] = {}
email_results: Dict[str, List[Dict[str, str]]] = {}

async def process_lead_scoring(
    session_id: str,
    candidates: List[Candidate],
    job_description: str,
    feedback: str,
    thinking_streamer: Optional[ThinkingStreamer] = None
):
    """Background task to score leads with progress tracking"""
    try:
        session = processing_sessions[session_id]
        is_rescoring = bool(feedback and feedback.strip())
        
        if is_rescoring:
            session["status"] = "scoring"
            session["message"] = "Lead Scoring Crew re-analyzing candidates..."
            session["workflow_stage"] = "rescoring"
        else:
            session["status"] = "scoring"
            session["message"] = "Lead Scoring Crew analyzing candidates..."
            session["workflow_stage"] = "initial_scoring"
        
        session["progress"] = 0
        session["scored_count"] = 0
        session["current_candidate"] = None
        session["partial_results"] = []
        total = len(candidates)
        
        def update_progress(current: int, total: int, candidate_name: Optional[str] = None, candidate_score: Optional[CandidateScore] = None):
            if session_id in processing_sessions:
                s = processing_sessions[session_id]
                s["progress"] = int((current / total) * 100) if total > 0 else 0
                s["scored_count"] = current
                
                if candidate_score:
                    if "partial_results" not in s: s["partial_results"] = []
                    candidate_data = next((c for c in candidates if c.id == candidate_score.id), None)
                    if candidate_data:
                        scored_candidate = ScoredCandidate(
                            id=candidate_data.id, name=candidate_data.name, email=candidate_data.email,
                            bio=candidate_data.bio, skills=candidate_data.skills,
                            score=candidate_score.score, reason=candidate_score.reason
                        )
                        partial_results = s["partial_results"]
                        existing_idx = next((i for i, r in enumerate(partial_results) if r["id"] == candidate_score.id), None)
                        if existing_idx is not None: partial_results[existing_idx] = scored_candidate.dict()
                        else: partial_results.append(scored_candidate.dict())
                        partial_results.sort(key=lambda x: x.get("score", 0), reverse=True)
                
                if candidate_name:
                    s["current_candidate"] = candidate_name
                    s["message"] = f"Evaluating {candidate_name} ({current}/{total})"
                    
                    # Emit to logs
                    if thinking_streamer:
                        ThinkingStreamer.add_event(
                            session_id, 
                            "processing", 
                            f"Evaluating candidate: {candidate_name} ({current}/{total})", 
                            progress=int((current / total) * 100) if total > 0 else 0
                        )
                else:
                    s["current_candidate"] = None
                    s["message"] = f"Completed {current} of {total} candidates"
                    
                    # Emit to logs
                    if thinking_streamer:
                        ThinkingStreamer.add_event(
                            session_id, 
                            "processing", 
                            f"Completed batch: {current}/{total} candidates",
                            progress=int((current / total) * 100) if total > 0 else 0
                        )
        
        candidate_scores = await score_candidates_parallel(
            candidates, job_description, feedback, 
            progress_callback=update_progress, thinking_streamer=thinking_streamer
        )
        
        session["candidate_scores"] = [score.dict() for score in candidate_scores]
        scored_candidates = []
        score_dict = {score.id: score for score in candidate_scores}
        for candidate in candidates:
            score = score_dict.get(candidate.id)
            if score:
                scored_candidates.append(ScoredCandidate(
                    id=candidate.id, name=candidate.name, email=candidate.email,
                    bio=candidate.bio, skills=candidate.skills,
                    score=score.score, reason=score.reason
                ))
        
        scored_candidates_sorted = sorted(scored_candidates, key=lambda c: c.score, reverse=True)
        session["scored_candidates"] = [sc.dict() for sc in scored_candidates_sorted]
        session["status"] = "completed"
        session["message"] = "Scoring completed successfully"
        session["progress"] = 100
        
    except Exception as e:
        logger.error(f"Error processing leads: {e}")
        if session_id in processing_sessions:
            processing_sessions[session_id]["status"] = "error"
            processing_sessions[session_id]["message"] = f"Error: {str(e)}"
