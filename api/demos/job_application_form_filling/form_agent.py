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
from .form_template import get_form_structure

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
    Fill form fields from resume data, streaming updates field by field.
    
    Args:
        resume_data: Parsed resume data
        form_structure: Form structure with fields to fill
        
    Yields:
        Dictionary with field filling updates
    """
    try:
        provider = get_llm_provider()
        total_fields = len(form_structure.fields)
        filled_count = 0
        
        report_progress(
            "Starting form filling process...",
            progress=0.0
        )
        
        # Process each field
        for field in form_structure.fields:
            filled_count += 1
            progress = filled_count / total_fields
            
            # Map resume data to form field
            value = await map_resume_data_to_field(resume_data, field)
            
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


async def map_resume_data_to_field(resume_data: ResumeData, field: FormField) -> str:
    """
    Map resume data to a specific form field.
    
    Args:
        resume_data: Parsed resume data
        field: Form field to fill
        
    Returns:
        String value for the field
    """
    field_name = field.name.lower()
    
    # Direct mappings
    if field_name == "full_name":
        return resume_data.name
    
    elif field_name == "email":
        return resume_data.email
    
    elif field_name == "phone":
        return resume_data.phone or ""
    
    elif field_name == "address":
        return resume_data.address or ""
    
    elif field_name == "work_experience":
        # Format work experience as text
        if not resume_data.work_experience:
            return "No work experience listed"
        
        formatted = []
        for exp in resume_data.work_experience:
            exp_text = f"{exp.role} at {exp.company}"
            if exp.start_date:
                exp_text += f" ({exp.start_date}"
                if exp.end_date:
                    exp_text += f" - {exp.end_date}"
                else:
                    exp_text += " - Present"
                exp_text += ")"
            if exp.description:
                exp_text += f"\n{exp.description}"
            formatted.append(exp_text)
        
        return "\n\n".join(formatted)
    
    elif field_name == "education":
        # Format education as text
        if not resume_data.education:
            return "No education listed"
        
        formatted = []
        for edu in resume_data.education:
            edu_text = f"{edu.degree}"
            if edu.institution:
                edu_text += f" from {edu.institution}"
            if edu.graduation_date:
                edu_text += f" ({edu.graduation_date})"
            if edu.gpa:
                edu_text += f" - GPA: {edu.gpa}"
            formatted.append(edu_text)
        
        return "\n".join(formatted)
    
    elif field_name == "skills":
        # Format skills as comma-separated or list
        if not resume_data.skills:
            return "No skills listed"
        
        return ", ".join(resume_data.skills)
    
    else:
        # Use LLM for intelligent mapping if field doesn't match directly
        provider = get_llm_provider()
        
        prompt = f"""Given the following resume data and form field, extract the appropriate value.

Resume Data:
Name: {resume_data.name}
Email: {resume_data.email}
Phone: {resume_data.phone or "Not provided"}
Address: {resume_data.address or "Not provided"}
Work Experience: {len(resume_data.work_experience)} positions
Education: {len(resume_data.education)} entries
Skills: {', '.join(resume_data.skills[:5]) if resume_data.skills else "None"}

Form Field:
Name: {field.name}
Label: {field.label}
Section: {field.section}
Type: {field.type}

Extract the most appropriate value from the resume data for this field.
If no relevant data is found, return an empty string.

Return only the value, no explanation."""
        
        try:
            value = await provider.generate_text(prompt, temperature=0.1, max_tokens=200)
            return value.strip()
        except Exception as e:
            logger.warning(f"Error mapping field {field.name} with LLM: {e}")
            return ""

