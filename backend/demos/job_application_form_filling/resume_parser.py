"""
Resume Parser
=============

Parses resume/CV documents and extracts structured data using LLM.
"""

import logging
import tempfile
import shutil
import os
from typing import Optional
from llama_index.core import SimpleDirectoryReader

from utils.llm_provider import get_llm_provider
from .models import ResumeData, WorkExperience, Education

logger = logging.getLogger(__name__)


async def parse_resume_pdf(file_path: str) -> Optional[ResumeData]:
    """
    Parse a resume PDF and extract structured data.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        ResumeData with extracted information, or None if parsing fails
    """
    try:
        logger.info(f"Parsing resume PDF: {file_path}")
        
        # Extract text from PDF using LlamaIndex
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, os.path.basename(file_path))
        shutil.copy2(file_path, temp_file)
        
        try:
            file_size = os.path.getsize(temp_file)
            logger.info(f"Resume file size: {file_size} bytes")

            if file_size == 0:
                raise Exception("Uploaded resume file is empty")
            
            resume_text = ""
            
            # Try method 1: LlamaIndex SimpleDirectoryReader
            try:
                reader = SimpleDirectoryReader(input_files=[temp_file])
                documents = reader.load_data()
                if documents:
                    resume_text = "\n".join([doc.text for doc in documents])
            except Exception as e:
                logger.warning(f"LlamaIndex extraction failed: {e}")

            # Try method 2: pymupdf4llm (fallback)
            if not resume_text:
                try:
                    import pymupdf4llm
                    logger.info("Falling back to pymupdf4llm for PDF extraction")
                    resume_text = pymupdf4llm.to_markdown(temp_file)
                except ImportError:
                    logger.warning("pymupdf4llm not installed, skipping fallback")
                except Exception as e:
                    logger.warning(f"pymupdf4llm extraction failed: {e}")

            if not resume_text:
                 raise Exception("No content extracted from resume (tried LlamaIndex and pymupdf4llm)")
                
        finally:
            # Clean up temp directory
            shutil.rmtree(temp_dir)
        
        if not resume_text or len(resume_text.strip()) < 50:
            raise Exception("Resume text too short or empty")
        
        logger.info(f"Extracted {len(resume_text)} characters from resume")
        
        # Use LLM to extract structured data
        provider = get_llm_provider()
        
        extraction_prompt = f"""Extract structured information from the following resume/CV.

Resume Text:
{resume_text}

Extract the following information in JSON format:
- name: Full name of the person
- email: Email address
- phone: Phone number (if available)
- address: Address (if available)
- work_experience: List of work experiences, each with:
  - company: Company name
  - role: Job title/role
  - start_date: Start date
  - end_date: End date (or "Present" if current)
  - description: Job description/responsibilities
- education: List of education entries, each with:
  - degree: Degree name
  - institution: Institution name
  - graduation_date: Graduation date (if available)
  - gpa: GPA (if available)
- skills: List of skills (technical skills, languages, certifications, etc.)
- summary: Professional summary (if available)

Return ONLY valid JSON matching this structure:
{{
  "name": "Full Name",
  "email": "email@example.com",
  "phone": "phone number or null",
  "address": "address or null",
  "work_experience": [
    {{
      "company": "Company Name",
      "role": "Job Title",
      "start_date": "Start Date",
      "end_date": "End Date or null",
      "description": "Job description"
    }}
  ],
  "education": [
    {{
      "degree": "Degree Name",
      "institution": "Institution Name",
      "graduation_date": "Date or null",
      "gpa": "GPA or null"
    }}
  ],
  "skills": ["skill1", "skill2", "skill3"],
  "summary": "Summary or null"
}}

Important:
- Extract only information that is explicitly stated in the resume
- If a field is not found, use null
- For dates, use the format as written in the resume
- For work experience, list in reverse chronological order (most recent first)
- For education, list in reverse chronological order (most recent first)
"""
        
        logger.info("Calling LLM to extract structured data from resume")
        response = await provider.generate_text(
            extraction_prompt,
            temperature=0.1,  # Low temperature for accurate extraction
            max_tokens=2000
        )
        
        # Parse JSON response
        import json
        import re
        
        # Try to extract JSON from response (handle cases where LLM adds extra text)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = response
        
        # Parse JSON
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response was: {response[:500]}")
            raise Exception(f"Failed to parse LLM response as JSON: {e}")
        
        # Convert to ResumeData model
        work_experience = []
        for exp in data.get("work_experience", []):
            work_experience.append(WorkExperience(
                company=exp.get("company") or "",
                role=exp.get("role") or "",
                start_date=exp.get("start_date") or "",
                end_date=exp.get("end_date"),
                description=exp.get("description") or ""
            ))
        
        education = []
        for edu in data.get("education", []):
            education.append(Education(
                degree=edu.get("degree") or "",
                institution=edu.get("institution") or "",
                graduation_date=edu.get("graduation_date"),
                gpa=edu.get("gpa")
            ))
        
        resume_data = ResumeData(
            name=data.get("name", ""),
            email=data.get("email", ""),
            phone=data.get("phone"),
            address=data.get("address"),
            work_experience=work_experience,
            education=education,
            skills=data.get("skills", []),
            summary=data.get("summary")
        )
        
        logger.info(f"Successfully parsed resume for: {resume_data.name}")
        return resume_data
        
    except Exception as e:
        logger.error(f"Error parsing resume: {e}")
        raise

