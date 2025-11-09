"""
Lead Scoring Crews
==================

🎯 LEARNING OBJECTIVES:
This module teaches you how to build CrewAI crews for lead scoring:

1. Agent Design - How to create specialized agents with roles, goals, and backstories
2. Task Definition - How to define tasks that agents execute
3. Crew Creation - How to orchestrate agents and tasks into crews
4. Parallel Processing - How to run multiple crews concurrently

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Agent Creation - Create specialized agents for scoring and email generation
Step 2: Task Definition - Define tasks with detailed descriptions
Step 3: Crew Assembly - Combine agents and tasks into crews
Step 4: Crew Execution - Run crews and extract results

Key Concept: Crews are specialized teams of agents. Each crew handles one specific
part of the workflow, making the system modular and maintainable.
"""

import asyncio
import logging
from typing import List
from crewai import Agent, Crew, Process, Task

# Import our shared LLM provider utilities
from utils.llm_provider import get_crewai_llm

# Import models from shared models file
from .models import Candidate, CandidateScore, ScoredCandidate

logger = logging.getLogger(__name__)


# ============================================================================
# STEP 1: LEAD SCORING CREW
# ============================================================================
"""
Lead Scoring Crew:
This crew scores a single candidate against a job description.

The crew consists of:
- HR Evaluation Agent: Specialized agent that evaluates candidate fit
- Evaluation Task: Task that scores the candidate and provides reasoning

Key Learning: Each crew is created fresh for each candidate. This allows
us to customize the task description with candidate-specific information.
"""
async def score_candidate(
    candidate: Candidate,
    job_description: str,
    additional_feedback: str = ""
) -> CandidateScore:
    """
    Score a single candidate using CrewAI
    
    This function:
    1. Creates an HR Evaluation Agent
    2. Creates an evaluation task with candidate-specific information
    3. Assembles them into a crew
    4. Runs the crew and extracts the score
    
    Args:
        candidate: Candidate to score
        job_description: Job description to score against
        additional_feedback: Optional feedback for scoring refinement
    
    Returns:
        CandidateScore with id, score, and reason
    """
    try:
        # Create CrewAI LLM using shared provider system
        llm = get_crewai_llm(temperature=0.3)
        
        # Create HR Evaluation Agent
        hr_agent = Agent(
            role="Senior HR Evaluation Expert",
            goal="Analyze candidates' qualifications and compare them against the job description to provide a score and reasoning",
            backstory="""As a Senior HR Evaluation Expert, you have extensive experience in assessing candidate profiles. 
            You excel at evaluating how well candidates match job descriptions by analyzing their skills, experience, 
            cultural fit, and growth potential. Your professional background allows you to provide comprehensive 
            evaluations with clear reasoning.""",
            verbose=True,
            llm=llm,
        )
        
        # Create evaluation task with detailed scoring criteria
        task_description = f"""You are evaluating a candidate for a specific job position. Your task is to provide a PRECISE and GRANULAR score (1-100) based on how well the candidate matches the job requirements.

CRITICAL SCORING RULES:
- Use the FULL 1-100 range - don't cluster scores around similar numbers
- Use SPECIFIC numbers like 87, 73, 64, 52, 41 - NOT round numbers like 85, 75, 65, 50
- Even candidates with similar backgrounds MUST receive DIFFERENT scores (at least 3-5 point difference)
- Be granular: If two candidates are close, differentiate by 3-7 points based on subtle differences
- NO two candidates should have identical scores unless they are truly identical (which is extremely rare)

DETAILED SCORING CRITERIA (Calculate each dimension precisely):
1. SKILL MATCH (0-30 points): Count exact skill matches from job description
   - 5+ exact matches: 27-30 points (be specific: 28, 29, 30)
   - 3-4 exact matches: 20-26 points (be specific: 21, 23, 25)
   - 1-2 exact matches: 12-19 points (be specific: 14, 16, 18)
   - Partial matches only: 6-11 points (be specific: 7, 9, 11)
   - No relevant skills: 0-5 points (be specific: 2, 3, 4)

2. RELEVANT EXPERIENCE (0-30 points): Assess depth and relevance of experience
   - 3+ years relevant experience: 26-30 points (be specific: 27, 28, 30)
   - 1-2 years relevant experience: 18-25 points (be specific: 19, 22, 24)
   - Some relevant projects/internships: 10-17 points (be specific: 12, 14, 16)
   - Limited/unrelated experience: 3-9 points (be specific: 4, 6, 8)
   - No relevant experience: 0-2 points (be specific: 0, 1, 2)

3. QUALITY & DEPTH (0-25 points): Evaluate achievements and project quality
   - Exceptional: Published work, major projects, leadership: 22-25 points (be specific: 23, 24, 25)
   - Strong: Multiple quality projects, good portfolio: 16-21 points (be specific: 17, 19, 20)
   - Good: Some projects, decent portfolio: 10-15 points (be specific: 11, 13, 14)
   - Basic: Simple projects, minimal portfolio: 4-9 points (be specific: 5, 7, 8)
   - Minimal: Little to show: 0-3 points (be specific: 1, 2, 3)

4. CULTURAL FIT & GROWTH POTENTIAL (0-15 points): Assess fit and potential
   - Excellent indicators: 13-15 points (be specific: 13, 14, 15)
   - Good indicators: 9-12 points (be specific: 9, 10, 11)
   - Some indicators: 5-8 points (be specific: 5, 6, 7)
   - Unclear/limited: 0-4 points (be specific: 1, 2, 3)

CALCULATION PROCESS:
1. Score each dimension independently using the ranges above
2. Sum the four dimensions to get total score (0-100)
3. If total is above 100, cap at 100
4. Use SPECIFIC numbers - avoid clustering at 75, 80, 85, etc.
5. Ensure granularity: If calculating 18+22+15+12=67, consider if it should be 65, 68, or 71 based on nuances

CANDIDATE INFORMATION
---------------------
Candidate ID: {candidate.id}
Name: {candidate.name}
Bio: {candidate.bio}
Skills: {candidate.skills}

JOB DESCRIPTION
---------------
{job_description if job_description else "No specific job description provided. Evaluate based on general software engineering/technical skills."}

{additional_feedback}

YOUR TASK:
1. Calculate each dimension score separately (be specific, not round numbers)
2. Sum them to get total score (use granular numbers like 67, 73, 81, not 70, 75, 80)
3. Provide detailed reasoning showing your calculation for each dimension
4. Include the candidate's unique ID: {candidate.id}

REMEMBER: 
- Use granular scoring (67, 73, 81) NOT round numbers (70, 75, 80)
- Even similar candidates must differ by at least 3-5 points
- Show your work: explain how you calculated each dimension score"""
        
        evaluate_task = Task(
            description=task_description,
            agent=hr_agent,
            expected_output="A CandidateScore object with id, score (1-100), and detailed reasoning",
            output_pydantic=CandidateScore,
        )
        
        # Create crew
        crew = Crew(
            agents=[hr_agent],
            tasks=[evaluate_task],
            process=Process.sequential,
            verbose=True,
        )
        
        # Run crew in thread pool to avoid blocking
        result = await asyncio.to_thread(crew.kickoff)
        
        # Try to extract Pydantic result
        if hasattr(result, 'pydantic') and result.pydantic:
            score_result = result.pydantic
            logger.info(f"Successfully scored candidate {candidate.id} ({candidate.name}): {score_result.score}")
            return score_result
        elif hasattr(result, 'raw'):
            # Fallback: try to parse from raw output
            logger.warning(f"Result doesn't have pydantic attribute for candidate {candidate.id}, trying raw output")
            raw_output = str(result.raw) if hasattr(result.raw, '__str__') else str(result)
            logger.debug(f"Raw output for candidate {candidate.id}: {raw_output[:200]}")
            # Try to extract score from raw output (basic fallback)
            import re
            score_match = re.search(r'score["\']?\s*[:=]\s*(\d+)', raw_output, re.IGNORECASE)
            if score_match:
                extracted_score = int(score_match.group(1))
                return CandidateScore(
                    id=candidate.id,
                    score=extracted_score,
                    reason=f"Score extracted from output: {raw_output[:200]}"
                )
        
        # Last resort fallback
        logger.error(f"Could not extract score for candidate {candidate.id} from result: {type(result)}")
        return CandidateScore(
            id=candidate.id,
            score=50,  # Neutral score instead of 75
            reason="Error: Could not parse score from agent output. Please check logs."
        )
    except Exception as e:
        logger.error(f"Error scoring candidate {candidate.id}: {e}")
        return CandidateScore(
            id=candidate.id,
            score=0,
            reason=f"Error during scoring: {str(e)}"
        )


async def score_candidates_parallel(
    candidates: List[Candidate],
    job_description: str,
    additional_feedback: str = "",
    progress_callback=None
) -> List[CandidateScore]:
    """
    Score multiple candidates in parallel with progress tracking
    
    This function creates scoring tasks for all candidates and runs them
    concurrently using asyncio.gather(), with progress updates.
    
    Args:
        candidates: List of candidates to score
        job_description: Job description to score against
        additional_feedback: Optional feedback for scoring refinement
        progress_callback: Optional callback function(current_index, total, candidate_name)
    
    Returns:
        List of CandidateScore objects
    """
    total = len(candidates)
    results = []
    
    # Process candidates one by one to provide progress updates
    # (We could do batches, but one-by-one gives better progress granularity)
    for idx, candidate in enumerate(candidates):
        # Update progress before scoring
        if progress_callback:
            progress_callback(idx, total, candidate.name, None)
        
        # Score the candidate
        score = await score_candidate(candidate, job_description, additional_feedback)
        results.append(score)
        
        # Update progress after scoring with the actual score result
        if progress_callback:
            progress_callback(idx + 1, total, None, score)
    
    logger.info(f"Finished scoring {len(results)} candidates")
    return results


# ============================================================================
# STEP 2: EMAIL GENERATION CREW
# ============================================================================
"""
Email Generation Crew:
This crew generates personalized emails for candidates.

The crew consists of:
- Email Followup Agent: Specialized agent that crafts personalized emails
- Email Task: Task that generates email based on candidate status

Key Learning: The email content differs based on whether we're proceeding
with the candidate (invitation) or not (rejection).
"""
async def generate_email_for_candidate(
    candidate: ScoredCandidate,
    proceed_with_candidate: bool
) -> str:
    """
    Generate email for a single candidate using CrewAI
    
    This function:
    1. Creates an Email Followup Agent
    2. Creates an email task with candidate-specific information
    3. Assembles them into a crew
    4. Runs the crew and extracts the email content
    
    Args:
        candidate: Scored candidate to generate email for
        proceed_with_candidate: Whether to proceed with this candidate
    
    Returns:
        Email content as string
    """
    try:
        # Create CrewAI LLM using shared provider system
        llm = get_crewai_llm(temperature=0.3)
        
        # Create Email Followup Agent
        email_agent = Agent(
            role="HR Coordinator",
            goal="Compose personalized follow-up emails to candidates based on their bio and whether they are being pursued for the job. If we are proceeding, request availability for a Zoom call. Otherwise, send a polite rejection email.",
            backstory="""You are an HR professional named Sarah who works at CrewAI with excellent communication skills 
            and a talent for crafting personalized and thoughtful emails to job candidates. You understand the importance 
            of maintaining a positive and professional tone in all correspondence.""",
            verbose=True,
            allow_delegation=False,
            llm=llm,
        )
        
        # Create email task
        proceed_text = "Yes, we want to proceed with this candidate" if proceed_with_candidate else "No, we are not proceeding with this candidate"
        
        task_description = f"""Compose personalized follow-up emails for candidates who applied to a specific job.

You will use the candidate's name, bio, and whether the company wants to proceed with them to generate the email. 
If the candidate is proceeding, ask them for their availability for a Zoom call in the upcoming days. 
If not, send a polite rejection email.

CANDIDATE DETAILS
-----------------
Candidate ID: {candidate.id}
Name: {candidate.name}
Bio:
{candidate.bio}

PROCEEDING WITH CANDIDATE: {proceed_text}

ADDITIONAL INSTRUCTIONS
-----------------------
- If we are proceeding, ask for their availability for a Zoom call within the next few days.
- If we are not proceeding, send a polite rejection email, acknowledging their effort in applying and appreciating their time.

Expected output: A personalized email based on the candidate's information. It should be professional and respectful, 
either inviting them for a Zoom call or letting them know we are pursuing other candidates."""
        
        email_task = Task(
            description=task_description,
            agent=email_agent,
            expected_output="A personalized email content as a string, either inviting the candidate for a Zoom call or politely rejecting them",
            verbose=True,
        )
        
        # Create crew
        crew = Crew(
            agents=[email_agent],
            tasks=[email_task],
            process=Process.sequential,
            verbose=True,
        )
        
        # Run crew in thread pool to avoid blocking
        result = await asyncio.to_thread(crew.kickoff)
        
        email_content = result.raw if hasattr(result, 'raw') else str(result)
        return email_content
        
    except Exception as e:
        logger.error(f"Error generating email for {candidate.id}: {e}")
        return f"Error generating email: {str(e)}"


async def generate_emails_parallel(
    scored_candidates: List[ScoredCandidate],
    top_candidate_ids: set
) -> List[dict]:
    """
    Generate emails for all candidates in parallel
    
    This function creates email generation tasks for all candidates and runs them
    concurrently using asyncio.gather().
    
    Args:
        scored_candidates: List of scored candidates
        top_candidate_ids: Set of IDs for top candidates (get invitation emails)
    
    Returns:
        List of email results with candidate_id, candidate_name, email_content, is_top_candidate
    """
    async def generate_email(candidate: ScoredCandidate) -> dict:
        proceed_with_candidate = candidate.id in top_candidate_ids
        email_content = await generate_email_for_candidate(candidate, proceed_with_candidate)
        
        return {
            "candidate_id": candidate.id,
            "candidate_name": candidate.name,
            "email_content": email_content,
            "is_top_candidate": proceed_with_candidate
        }
    
    tasks = [asyncio.create_task(generate_email(c)) for c in scored_candidates]
    email_results = await asyncio.gather(*tasks)
    
    logger.info(f"Generated {len(email_results)} emails")
    return list(email_results)
