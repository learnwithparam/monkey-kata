"""
Legal Case Intake Agents
========================

🎯 LEARNING OBJECTIVES:
This module teaches you how to create a multi-agent system with human-in-the-loop:

1. Multi-Agent Coordination - Multiple agents working together
2. Human-in-the-Loop - Integrating human review into the workflow
3. Context Preservation - Maintaining case information across agents
4. Workflow Orchestration - Coordinating intake, review, and approval

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Intake Agent - Collects case information
Step 2: Review Agent - Analyzes and summarizes the case
Step 3: Lawyer Agent - Human review and decision

Key Concept: This system demonstrates multi-agent coordination with human oversight,
showing how AI agents can handle initial processing while humans make final decisions.
"""

import logging
from typing import Dict, Any
from datetime import datetime
from crewai import Agent, Crew, Process, Task

from utils.llm_provider import get_crewai_llm
from .models import CaseIntake, CaseReview, CaseStatus
from .progress import report_progress

logger = logging.getLogger(__name__)


def create_intake_agent() -> Agent:
    """
    Create an Intake Agent that collects case information.
    
    This agent:
    - Asks clarifying questions if needed
    - Validates case information
    - Structures case data
    
    Returns:
        Agent ready to use
    """
    llm = get_crewai_llm(temperature=0.3)
    
    return Agent(
        role="Legal Case Intake Specialist",
        goal="Collect comprehensive case information from clients in a professional and empathetic manner",
        backstory="""You are an experienced legal intake specialist with excellent communication skills.
        You know how to ask the right questions to gather all necessary information while making
        clients feel heard and understood. You ensure all case details are accurately captured.""",
        verbose=True,
        llm=llm,
    )


def create_review_agent() -> Agent:
    """
    Create a Review Agent that analyzes cases.
    
    This agent:
    - Summarizes case information
    - Assesses case risks
    - Provides recommendations
    
    Returns:
        Agent ready to use
    """
    llm = get_crewai_llm(temperature=0.4)
    
    return Agent(
        role="Legal Case Review Analyst",
        goal="Analyze case information, assess risks, and provide recommendations for lawyer review",
        backstory="""You are a legal analyst with expertise in case evaluation. You review case
        information, identify key legal issues, assess potential risks, and provide clear
        recommendations to help lawyers make informed decisions.""",
        verbose=True,
        llm=llm,
    )


async def process_case_intake(case_intake: CaseIntake) -> Dict[str, Any]:
    """
    Process a case through the intake workflow.
    
    This function:
    1. Intake Agent validates and structures the case
    2. Review Agent analyzes and summarizes
    3. Returns case ready for lawyer review
    
    Args:
        case_intake: Initial case intake information
    
    Returns:
        Dictionary with processed case information
    """
    try:
        # Report workflow start
        report_progress(
            "Intake Agent: Starting case intake validation",
            agent="Intake Agent",
            tool="agent_invoke",
            target=f"Case Type: {case_intake.case_type}"
        )
        
        llm = get_crewai_llm(temperature=0.3)
        
        # Create agents
        intake_agent = create_intake_agent()
        review_agent = create_review_agent()
        
        report_progress(
            "Intake Agent: Validating case information and structure",
            agent="Intake Agent",
            tool="agent_processing",
            target="Checking required fields and data completeness"
        )
        
        # Intake task - validate and structure case
        intake_task = Task(
            description=f"""Review and validate the following case intake information:

Client Name: {case_intake.client_name}
Client Email: {case_intake.client_email}
Client Phone: {case_intake.client_phone or 'Not provided'}
Case Type: {case_intake.case_type}
Case Description: {case_intake.case_description}
Urgency: {case_intake.urgency}
Additional Info: {case_intake.additional_info or 'None'}

Your task:
1. Validate that all required information is present
2. Identify any missing critical information
3. Structure the case information clearly
4. Note any immediate concerns or red flags

Provide a structured summary of the validated case information.""",
            agent=intake_agent,
            expected_output="A structured summary of validated case information with any missing details noted"
        )
        
        # Review task - analyze and assess
        review_task = Task(
            description=f"""Analyze the following case and provide a comprehensive review:

Case Type: {case_intake.case_type}
Case Description: {case_intake.case_description}
Urgency: {case_intake.urgency}

Your task:
1. Create a concise summary of the case (2-3 paragraphs)
2. Assess potential legal risks and complexities
3. Identify key legal issues
4. Provide a recommendation for the lawyer (e.g., "Proceed with consultation", "Request additional information", "Refer to specialist")

Format your response as:
SUMMARY: [your summary]
RISK_ASSESSMENT: [your risk assessment]
RECOMMENDED_ACTION: [your recommendation]""",
            agent=review_agent,
            expected_output="A structured review with summary, risk assessment, and recommendation",
            context=[intake_task]
        )
        
        # Create crew and execute
        report_progress(
            "Intake Agent: Completed validation phase",
            agent="Intake Agent",
            tool="agent_complete",
            target="Case information validated and structured"
        )
        
        report_progress(
            "Review Agent: Starting case analysis and risk assessment",
            agent="Review Agent",
            tool="agent_invoke",
            target="Analyzing case details and legal implications"
        )
        
        crew = Crew(
            agents=[intake_agent, review_agent],
            tasks=[intake_task, review_task],
            process=Process.sequential,
            verbose=True
        )
        
        report_progress(
            "Review Agent: Processing case through CrewAI workflow",
            agent="Review Agent",
            tool="crew_execution",
            target="Running sequential agent tasks"
        )
        
        result = crew.kickoff()
        
        report_progress(
            "Review Agent: Completed case analysis",
            agent="Review Agent",
            tool="agent_complete",
            target="Generated summary, risk assessment, and recommendations"
        )
        
        # Parse the result
        report_progress(
            "Review Agent: Parsing analysis results",
            agent="Review Agent",
            tool="data_parsing",
            target="Extracting summary, risk assessment, and recommendations"
        )
        
        output_text = str(result)
        
        # Extract summary, risk assessment, and recommendation
        summary = ""
        risk_assessment = ""
        recommended_action = ""
        
        if "SUMMARY:" in output_text:
            parts = output_text.split("SUMMARY:")
            if len(parts) > 1:
                summary_part = parts[1].split("RISK_ASSESSMENT:")[0].strip()
                summary = summary_part
        
        if "RISK_ASSESSMENT:" in output_text:
            parts = output_text.split("RISK_ASSESSMENT:")
            if len(parts) > 1:
                risk_part = parts[1].split("RECOMMENDED_ACTION:")[0].strip()
                risk_assessment = risk_part
        
        if "RECOMMENDED_ACTION:" in output_text:
            parts = output_text.split("RECOMMENDED_ACTION:")
            if len(parts) > 1:
                recommended_action = parts[1].strip()
        
        # Fallback if parsing fails
        if not summary:
            summary = output_text[:500] + "..." if len(output_text) > 500 else output_text
        if not risk_assessment:
            risk_assessment = "Risk assessment pending lawyer review"
        if not recommended_action:
            recommended_action = "Review case with lawyer"
        
        report_progress(
            "Workflow: Case processing complete, ready for lawyer review",
            agent="Workflow Orchestrator",
            tool="workflow_complete",
            target="All agents completed, awaiting human review"
        )
        
        return {
            "intake_summary": summary,
            "risk_assessment": risk_assessment,
            "recommended_action": recommended_action,
            "full_output": output_text
        }
        
    except Exception as e:
        logger.error(f"Error processing case intake: {e}")
        raise

