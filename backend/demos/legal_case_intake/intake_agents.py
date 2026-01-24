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
from typing import Dict, Any, Optional
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


async def process_case_intake(case_intake: CaseIntake, previously_provided_info: Optional[str] = None) -> Dict[str, Any]:
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
        
        # Build context with previously provided info
        context_note = ""
        if previously_provided_info:
            context_note = f"\n\nPREVIOUSLY PROVIDED INFORMATION (already collected, do not ask again):\n{previously_provided_info}\n\n"
        
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
{context_note}
Your task:
1. Validate that all required information is present
2. Identify ONLY the NEW missing critical information (ignore what was already provided)
3. Structure the case information clearly
4. Note any immediate concerns or red flags
5. If information was already provided in previous rounds, do NOT ask for it again

Provide a structured summary of the validated case information.""",
            agent=intake_agent,
            expected_output="A structured summary of validated case information with any NEW missing details noted"
        )
        
        # Review task - analyze and assess
        review_task = Task(
            description=f"""Analyze the following case and provide a comprehensive review:

Case Type: {case_intake.case_type}
Case Description: {case_intake.case_description}
Urgency: {case_intake.urgency}
Client Phone: {case_intake.client_phone or 'Not provided'}

IMPORTANT VALIDATION RULES:
- If a phone number is provided (in any format like +153892839283, (555) 123-4567, etc.), it is VALID and should NOT be requested again
- If a date is mentioned (like "October 27, 2025"), validate it correctly - October 27, 2025 is BEFORE November 12, 2025, so it's in the PAST, not future
- Only request information that is TRULY missing, not information that was already provided

Your task:
1. Create a concise summary of the case (2-3 paragraphs)
2. Assess potential legal risks and complexities
3. Identify key legal issues
4. Provide a recommendation for the lawyer (e.g., "Proceed with consultation", "Request additional information", "Refer to specialist")
5. ONLY request additional information if it is genuinely missing - do NOT request phone numbers or dates that were already provided

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
            risk_assessment = "Risk assessment pending review"
        if not recommended_action:
            recommended_action = "Review case information"
        
        # Determine if more information is needed
        needs_more_info = False
        missing_info = []
        is_complete = False
        
        # Check what information we have - use proper validation
        import re
        from datetime import datetime as dt
        
        # Phone number validation - check if phone field exists and has valid format
        phone_text = (case_intake.client_phone or '').strip()
        # Also check if phone is mentioned in description or additional info
        all_text = f"{case_intake.case_description} {case_intake.additional_info or ''}"
        all_text_lower = all_text.lower()
        # Look for phone patterns: +1, (555), 555-1234, +153892839283, etc.
        # Match: + followed by 10-15 digits, or standard US format, or international format
        phone_patterns = [
            r'\+\d{10,15}',  # International format like +153892839283
            r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # Standard US format
            r'\d{10,15}',  # Plain digits (10-15 digits)
        ]
        has_phone = bool(phone_text) or any(re.search(pattern, all_text) for pattern in phone_patterns)
        
        # Date/timeline validation - look for actual dates and validate they're in the past
        # Check for date patterns: "October 27, 2025", "10/27/2025", "2025-10-27", etc.
        date_patterns = [
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}\b',
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
            r'\b(on|occurred|happened|date|timeline|when)\s+[^.]{0,50}(january|february|march|april|may|june|july|august|september|october|november|december|\d{1,2}[/-]\d{1,2})',
            r'\b\d{1,2}\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}\b',
        ]
        
        # Find date matches
        date_matches = []
        for pattern in date_patterns:
            matches = re.finditer(pattern, all_text, re.IGNORECASE)
            date_matches.extend([m.group() for m in matches])
        
        has_date = len(date_matches) > 0
        
        # If dates found, validate they're in the past (not future)
        if has_date:
            try:
                current_date = dt.now()
                valid_past_dates = []
                
                # Month name to number mapping
                months = {
                    'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
                    'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12
                }
                
                for date_str in date_matches:
                    try:
                        parsed_date = None
                        date_lower = date_str.lower()
                        
                        # Try parsing "October 27, 2025" format
                        for month_name, month_num in months.items():
                            if month_name in date_lower:
                                # Extract day and year
                                parts = date_str.split()
                                day = None
                                year = None
                                for part in parts:
                                    if part.replace(',', '').isdigit():
                                        if len(part.replace(',', '')) == 4:
                                            year = int(part.replace(',', ''))
                                        else:
                                            day = int(part.replace(',', ''))
                                if day and year:
                                    parsed_date = dt(year, month_num, day)
                                    break
                        
                        # Try parsing "10/27/2025" or "2025-10-27" format
                        if not parsed_date:
                            for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y', '%d/%m/%Y']:
                                try:
                                    parsed_date = dt.strptime(date_str, fmt)
                                    break
                                except ValueError:
                                    continue
                        
                        # If we successfully parsed a date, check if it's in the past
                        if parsed_date:
                            # Check if it's in the past (allow up to 1 day in future for timezone issues)
                            if parsed_date.date() <= current_date.date():
                                valid_past_dates.append(parsed_date)
                            else:
                                # Future date - still count as having a date, but agent can flag it
                                valid_past_dates.append(parsed_date)
                        else:
                            # If parsing fails, assume it's a valid date mention
                            valid_past_dates.append(None)
                    except (ValueError, TypeError, AttributeError):
                        # If parsing fails, assume it's a valid date mention
                        valid_past_dates.append(None)
                
                # If we found dates, consider it as having a date
                # (even if some are future-dated, the agent can handle that)
                has_date = len(valid_past_dates) > 0 or len(date_matches) > 0
            except Exception:
                # Fallback: if any date pattern found, consider it as having a date
                has_date = len(date_matches) > 0
        
        # Location validation - look for actual location indicators
        location_patterns = [
            r'\b(location|where|jurisdiction|address|city|state|county|country|street|avenue|road|boulevard|drive|place)\s+[^.]{0,100}',
            r'\b(in|at|near|located)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*',  # "in New York", "at 123 Main St"
        ]
        has_location = any(re.search(pattern, all_text, re.IGNORECASE) for pattern in location_patterns)
        
        has_detailed_desc = len(case_intake.case_description) >= 150
        has_additional_info = bool(case_intake.additional_info and len(case_intake.additional_info.strip()) > 20)
        
        # Analyze the recommendation to determine next steps
        recommendation_lower = recommended_action.lower()
        output_lower = output_text.lower()
        
        # Check if agent explicitly says we need more info
        if "request additional information" in recommendation_lower or "need more" in recommendation_lower or ("missing" in recommendation_lower and "no missing" not in recommendation_lower):
            needs_more_info = True
            # Extract what's missing from the output, but only what's actually missing
            missing_parts = []
            
            # Only add to missing if it's actually missing AND mentioned in the output
            # But first verify it's truly missing by checking the actual data
            if not has_phone and ("phone" in output_lower or "contact" in output_lower or "telephone" in output_lower):
                missing_parts.append("client phone number")
            if not has_date and ("date" in output_lower or "when" in output_lower or "timeline" in output_lower or "occurred" in output_lower):
                missing_parts.append("incident date or timeline")
            if not has_location and ("location" in output_lower or "where" in output_lower or "jurisdiction" in output_lower or "address" in output_lower):
                missing_parts.append("location or jurisdiction")
            if not has_detailed_desc and ("detailed" in output_lower or "more information" in output_lower or "description" in output_lower):
                missing_parts.append("more detailed case description")
            if not has_additional_info and ("additional" in output_lower or "more details" in output_lower):
                missing_parts.append("additional supporting information or evidence")
            
            # If we have everything but agent still says missing, check if it's about something else
            if not missing_parts and needs_more_info:
                # Agent might be asking for something specific mentioned in the output
                missing_parts = ["additional case details as specified by the review"]
        elif "proceed" in recommendation_lower or "complete" in recommendation_lower or ("ready" in recommendation_lower and "not ready" not in recommendation_lower):
            # Only mark complete if we have essential info
            if has_phone and has_detailed_desc:
                is_complete = True
            else:
                # Still need basic info
                needs_more_info = True
                if not has_phone:
                    missing_info.append("client phone number")
                if not has_detailed_desc:
                    missing_info.append("more detailed case description")
        
        # If we have all basic info and agent says proceed, mark complete
        if not needs_more_info and has_phone and has_detailed_desc:
            is_complete = True
        
        missing_info = missing_parts if missing_parts else missing_info
        
        report_progress(
            f"Workflow: Case analysis complete - {'All information collected' if is_complete else 'Additional information needed' if needs_more_info else 'Ready for review'}",
            agent="Workflow Orchestrator",
            tool="workflow_complete",
            target="Analysis complete"
        )
        
        return {
            "intake_summary": summary,
            "risk_assessment": risk_assessment,
            "recommended_action": recommended_action,
            "full_output": output_text,
            "needs_more_info": needs_more_info,
            "missing_info": missing_info,
            "is_complete": is_complete
        }
        
    except Exception as e:
        logger.error(f"Error processing case intake: {e}")
        raise

