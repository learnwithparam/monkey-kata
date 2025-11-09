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
        
        # Create evaluation task
        task_description = f"""Evaluate a candidate's bio based on the provided job description.

Use your expertise to carefully assess how well the candidate fits the job requirements. Consider key factors such as:
- Skill match
- Relevant experience
- Cultural fit
- Growth potential

CANDIDATE BIO
-------------
Candidate ID: {candidate.id}
Name: {candidate.name}
Bio:
{candidate.bio}

JOB DESCRIPTION
---------------
{job_description}

ADDITIONAL INSTRUCTIONS
-----------------------
Your final answer MUST include:
- The candidates unique ID
- A score between 1 and 100. Don't use numbers like 100, 75, or 50. Instead, use specific numbers like 87, 63, or 42.
- A detailed reasoning, considering the candidate's skill match, experience, cultural fit, and growth potential.
{additional_feedback}

Expected output: A very specific score from 1 to 100 for the candidate, along with a detailed reasoning explaining why you assigned this score."""
        
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
        
        if hasattr(result, 'pydantic'):
            return result.pydantic
        else:
            logger.warning(f"Result doesn't have pydantic attribute for candidate {candidate.id}")
            return CandidateScore(
                id=candidate.id,
                score=75,
                reason="Score generated successfully"
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
    additional_feedback: str = ""
) -> List[CandidateScore]:
    """
    Score multiple candidates in parallel
    
    This function creates scoring tasks for all candidates and runs them
    concurrently using asyncio.gather().
    
    Args:
        candidates: List of candidates to score
        job_description: Job description to score against
        additional_feedback: Optional feedback for scoring refinement
    
    Returns:
        List of CandidateScore objects
    """
    tasks = [asyncio.create_task(score_candidate(c, job_description, additional_feedback)) for c in candidates]
    candidate_scores = await asyncio.gather(*tasks)
    
    logger.info(f"Finished scoring {len(candidate_scores)} candidates")
    return list(candidate_scores)


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
