"""
Form Filling Agent
==================

Agent that intelligently fills job application forms from resume data.
"""

import logging
import asyncio
from typing import Dict, Any, AsyncGenerator, Callable, Optional

from utils.llm_provider import get_llm_provider
from .models import ResumeData, FormField, FormStructure

logger = logging.getLogger(__name__)

# Progress callback for streaming updates
_progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None


def set_progress_callback(callback: Optional[Callable[[Dict[str, Any]], None]]):
    """Set the progress callback for streaming updates"""
    global _progress_callback
    _progress_callback = callback


def report_progress(message: str, field_name: str = "", field_label: str = "", value: str = "", section: str = "", progress: float = 0.0):
    """Report progress update"""
    if _progress_callback:
        _progress_callback({
            "message": message,
            "field_name": field_name,
            "field_label": field_label,
            "value": value,
            "section": section,
            "progress": progress
        })


async def fill_form_from_resume(
    resume_data: ResumeData,
    form_structure: FormStructure
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Agentic form filling: AI agent autonomously understands form structure
    and available data, then intelligently fills all fields.
    
    This uses an agentic approach where the AI:
    1. Analyzes the entire form structure
    2. Understands all available resume data
    3. Creates a mapping strategy
    4. Fills fields intelligently based on semantic understanding
    
    Args:
        resume_data: Parsed resume data
        form_structure: Form structure with fields to fill
        
    Yields:
        Dictionary with field filling updates
    """
    try:
        logger.info(f"Starting fill_form_from_resume with {len(form_structure.fields)} fields")
        provider = get_llm_provider()
        total_fields = len(form_structure.fields)
        
        logger.info(f"Total fields to fill: {total_fields}")
        
        report_progress(
            "AI Agent: Analyzing form structure and available data...",
            progress=0.0
        )
        
        # Step 1: Agent understands the form structure and data
        logger.info("Waiting before agent analysis...")
        await asyncio.sleep(1.0)  # Brief pause for user to see the analysis
        
        # Step 2: Agent generates all field values in one intelligent pass
        logger.info("Calling agentic_form_filling...")
        filled_values = await agentic_form_filling(resume_data, form_structure, provider)
        logger.info(f"Agent returned {len(filled_values)} filled values")
        
        # Step 3: Stream the filled values field by field
        logger.info("Starting to stream filled values field by field...")
        filled_count = 0
        for field in form_structure.fields:
            filled_count += 1
            progress = filled_count / total_fields
            
            value = filled_values.get(field.name, "")
            logger.info(f"Filling field {filled_count}/{total_fields}: {field.name} = {value[:50] if value else '(empty)'}...")
            
            # Report progress
            report_progress(
                f"Filling {field.label}...",
                field_name=field.name,
                field_label=field.label,
                value=value,
                section=field.section,
                progress=progress
            )
            
            # Yield update
            yield {
                "field_name": field.name,
                "field_label": field.label,
                "value": value,
                "section": field.section,
                "progress": progress,
                "message": f"Filled {field.label}"
            }
            
            # 2 second delay between fields for better user experience
            logger.debug(f"Waiting 2 seconds before next field...")
            await asyncio.sleep(2.0)
        
        report_progress(
            "Form filling completed!",
            progress=1.0
        )
        
        # 3 second delay before showing completion/submit button
        await asyncio.sleep(3.0)
        
        yield {
            "done": True,
            "status": "completed",
            "message": "All fields filled successfully",
            "progress": 1.0
        }
        
    except Exception as e:
        logger.error(f"Error filling form: {e}")
        yield {
            "error": str(e),
            "status": "error",
            "message": f"Error filling form: {str(e)}"
        }


async def agentic_form_filling(
    resume_data: ResumeData,
    form_structure: Optional[FormStructure] = None,
    provider = None
) -> Dict[str, str]:
    """
    Agentic form filling: AI agent autonomously discovers form structure and fills it.
    
    This is a truly dynamic, agentic approach where the AI:
    - Can work with ANY form structure (passed dynamically)
    - If no structure provided, agent discovers fields from context
    - Understands all available data
    - Makes autonomous decisions about field mapping
    - Generates all values in one intelligent pass
    
    The agent doesn't rely on hardcoded templates - it adapts to any form structure.
    
    Args:
        resume_data: Parsed resume data
        form_structure: Optional form structure (if None, agent discovers it)
        provider: LLM provider (if None, gets default)
        
    Returns:
        Dictionary mapping field names to their filled values
    """
    logger.info("Starting agentic_form_filling...")
    if provider is None:
        provider = get_llm_provider()
        logger.info("LLM provider initialized")
    # Format complete resume data
    work_exp_text = ""
    if resume_data.work_experience:
        work_exp_text = "\n".join([
            f"- {exp.role} at {exp.company} ({exp.start_date} - {exp.end_date or 'Present'})\n  {exp.description}"
            for exp in resume_data.work_experience
        ])
    
    education_text = ""
    if resume_data.education:
        education_text = "\n".join([
            f"- {edu.degree} from {edu.institution}" + 
            (f" ({edu.graduation_date})" if edu.graduation_date else "") +
            (f" - GPA: {edu.gpa}" if edu.gpa else "")
            for edu in resume_data.education
        ])
    
    resume_context = f"""Available Resume Data:

Personal Information:
- Name: {resume_data.name}
- Email: {resume_data.email}
- Phone: {resume_data.phone or "Not provided"}
- Address: {resume_data.address or "Not provided"}

Work Experience:
{work_exp_text if work_exp_text else "No work experience listed"}

Education:
{education_text if education_text else "No education listed"}

Skills:
{', '.join(resume_data.skills) if resume_data.skills else "No skills listed"}

Professional Summary:
{resume_data.summary or "Not provided"}"""
    
    # Format form structure (dynamically discovered or provided)
    if form_structure:
        form_fields_text = "\n".join([
            f"Field: {field.name}\n  Label: {field.label}\n  Type: {field.type}\n  Section: {field.section}\n  Required: {field.required}"
            for field in form_structure.fields
        ])
        
        form_context = f"""Form Structure (Discovered/Provided):

Sections: {', '.join(form_structure.sections)}

Fields:
{form_fields_text}"""
    else:
        # Agent must discover form structure dynamically
        form_context = """Form Structure: 
The form structure is not predefined. You must intelligently determine what fields a typical job application form would have based on the resume data available. Common fields include: personal information (name, email, phone, address), work experience, education, skills, and other relevant sections."""
    
    # Agentic prompt: AI agent autonomously discovers and fills the form
    if form_structure:
        field_names_instruction = f"- Use the EXACT field names from the form structure: {', '.join([f.name for f in form_structure.fields])}"
    else:
        field_names_instruction = "- Determine appropriate field names based on standard job application forms (e.g., full_name, email, phone, work_experience, education, skills)"
    
    agent_prompt = f"""You are an autonomous AI agent that dynamically discovers and fills job application forms.

Your mission: 
1. Understand the form structure (whether provided or discover it dynamically)
2. Understand all available resume data
3. Autonomously map resume data to form fields
4. Generate all field values intelligently

{form_context}

{resume_context}

Agent Instructions:
1. **Form Understanding**: 
   - If form structure is provided, use it exactly
   - If not provided, intelligently determine what fields a job application form should have
   - Consider standard sections: Personal Information, Work Experience, Education, Skills

2. **Data Mapping**:
   - Match resume data to form fields semantically (e.g., "Full Name"/"Name" = name, "Email Address"/"Email" = email)
   - Understand field types and format data accordingly:
     * text/email/tel: Single value
     * textarea: Multi-line formatted text
   - For work experience/education: Format as readable lists with proper structure
   - For skills: Format as comma-separated or bullet points

3. **Intelligent Decisions**:
   - Handle variations in field names (e.g., "Work History" vs "Work Experience")
   - Format dates consistently
   - Handle missing data gracefully (empty string if not available)
   - Ensure values are ready for direct insertion into form fields

4. **Output Format**:
{field_names_instruction}
- Return a JSON object mapping each field name to its filled value
- Format values exactly as they should appear in the form
- For multi-line fields, use \\n for line breaks
- If a field has no relevant data, use an empty string ""

Return ONLY valid JSON in this format:
{{
  "field_name_1": "filled value 1",
  "field_name_2": "filled value 2",
  ...
}}

Do not include explanations, labels, or additional text outside the JSON."""
    
    try:
        logger.info("Calling LLM provider to generate field values...")
        logger.debug(f"Prompt length: {len(agent_prompt)} characters")
        response = await provider.generate_text(
            agent_prompt,
            temperature=0.1,  # Low temperature for consistent, accurate results
            max_tokens=2000
        )
        logger.info(f"LLM response received, length: {len(response)} characters")
        logger.debug(f"Response preview: {response[:200]}...")
        
        # Parse JSON response
        import json
        import re
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            logger.debug("Extracted JSON from response")
        else:
            json_str = response
            logger.warning("No JSON pattern found, using full response")
        
        # Parse JSON
        try:
            filled_values = json.loads(json_str)
            logger.info(f"Agent successfully filled {len(filled_values)} fields")
            logger.debug(f"Filled values keys: {list(filled_values.keys())}")
            return filled_values
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse agent response as JSON: {e}")
            logger.error(f"Response was: {response[:500]}")
            # Fallback: return empty dict
            return {}
        
    except Exception as e:
        logger.error(f"Error in agentic form filling: {e}", exc_info=True)
        return {}


