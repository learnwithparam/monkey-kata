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
    Intelligently map resume data to a form field using AI.
    
    This function uses an AI agent to understand the form field context
    and automatically extract the appropriate value from resume data,
    similar to how browser-use or playwright AI agents work.
    
    Args:
        resume_data: Parsed resume data
        field: Form field to fill
        
    Returns:
        String value for the field
    """
    provider = get_llm_provider()
    
    # Format resume data for the agent
    resume_summary = f"""Resume Data Available:
- Name: {resume_data.name}
- Email: {resume_data.email}
- Phone: {resume_data.phone or "Not provided"}
- Address: {resume_data.address or "Not provided"}
- Work Experience: {len(resume_data.work_experience)} position(s)
  {chr(10).join([f"  • {exp.role} at {exp.company} ({exp.start_date} - {exp.end_date or 'Present'})" for exp in resume_data.work_experience[:3]])}
- Education: {len(resume_data.education)} entry/entries
  {chr(10).join([f"  • {edu.degree} from {edu.institution}" + (f" ({edu.graduation_date})" if edu.graduation_date else "") for edu in resume_data.education[:3]])}
- Skills: {', '.join(resume_data.skills[:10]) if resume_data.skills else "None"}
- Summary: {resume_data.summary or "Not provided"}"""
    
    # Create intelligent prompt for the AI agent
    prompt = f"""You are an AI agent that automatically fills form fields by intelligently mapping resume data to form fields.

Your task: Analyze the form field and extract the most appropriate value from the resume data.

Form Field Information:
- Field Name: {field.name}
- Field Label: {field.label}
- Field Type: {field.type}
- Section: {field.section}
- Required: {field.required}

{resume_summary}

Instructions:
1. Understand what information the form field is asking for based on its name, label, and section
2. Find the most relevant data from the resume that matches this field
3. Format the data appropriately for the field type:
   - For text/textarea fields: Provide formatted, readable text
   - For email fields: Provide email address only
   - For tel/phone fields: Provide phone number only
   - For work experience fields: Format as a clear list with company, role, dates, and description
   - For education fields: Format as a clear list with degree, institution, and dates
   - For skills fields: Format as comma-separated list or bullet points
4. If the field asks for multiple items (like work experience or education), format them clearly with line breaks
5. If no relevant data exists in the resume, return an empty string

Return ONLY the value to fill in the field. Do not include explanations, labels, or additional text.
Format the output exactly as it should appear in the form field."""
    
    try:
        value = await provider.generate_text(
            prompt,
            temperature=0.1,  # Low temperature for consistent, accurate extraction
            max_tokens=500
        )
        
        # Clean up the response - remove any explanations or extra text
        value = value.strip()
        
        # Remove common prefixes that LLMs sometimes add
        prefixes_to_remove = [
            "The value is:",
            "Value:",
            "Answer:",
            "Field value:",
            "Here's the value:",
        ]
        for prefix in prefixes_to_remove:
            if value.lower().startswith(prefix.lower()):
                value = value[len(prefix):].strip()
        
        return value
        
    except Exception as e:
        logger.error(f"Error mapping field {field.name} with AI agent: {e}")
        # Fallback: return empty string if AI fails
        return ""

