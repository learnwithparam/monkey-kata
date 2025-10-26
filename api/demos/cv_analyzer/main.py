"""
CV Analyzer API
==============

FastAPI endpoints for CV analysis and improvement suggestions.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import uuid
import os
import logging
import tempfile
import shutil
from utils.llm_provider import get_llm_provider
from .cv_utils import CVDocumentProcessor
from .cv_agentic_analyzer import CVAnalyzer

# Configure logging
logger = logging.getLogger(__name__)

# ROUTER SETUP
# ============================================================================
router = APIRouter(prefix="/cv-analyzer", tags=["cv-analyzer"])

# Initialize providers
llm_provider = get_llm_provider()
document_processor = CVDocumentProcessor()
cv_analyzer = CVAnalyzer(llm_provider)

# In-memory storage for demo (use database in production)
document_data = {}  # document_id -> document data
document_embeddings = {}  # document_id -> embeddings
processing_status = {}  # document_id -> status

# Pydantic Models
# ============================================================================
class ProcessingStatus(BaseModel):
    document_id: str
    status: str
    progress: int
    message: str
    pages_count: int
    error: Optional[str] = None

class CVAnalysisResponse(BaseModel):
    overall_score: int
    strengths: List[str]
    weaknesses: List[str]
    improvement_suggestions: List[str]
    keyword_match_score: int
    experience_relevance: int
    skills_alignment: int
    format_score: int

class ServiceInfo(BaseModel):
    status: str
    service: str
    description: str
    documents_processed: int
    total_chunks: int

# API Endpoints
# ============================================================================

@router.get("/health", response_model=ServiceInfo)
async def health_check():
    """Health check endpoint"""
    total_chunks = sum(len(embeddings) for embeddings in document_embeddings.values())
    
    return ServiceInfo(
        status="healthy",
        service="cv-analyzer",
        description="AI-powered CV analysis and improvement suggestion system",
        documents_processed=len(document_data),
        total_chunks=total_chunks
    )

@router.post("/upload-cv")
async def upload_cv(
    file: UploadFile = File(...),
    job_description: Optional[str] = Form(None)
):
    """
    Upload a CV document for analysis
    
    Args:
        file: CV document file (PDF, Word, or text)
        job_description: Optional job description for targeted analysis
    
    Returns:
        Processing status with document ID
    """
    try:
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        
        # Validate file type
        allowed_extensions = {'.pdf', '.doc', '.docx', '.txt'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Save uploaded file temporarily
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, f"{document_id}_{file.filename}")
        
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Initialize processing status
        processing_status[document_id] = ProcessingStatus(
            document_id=document_id,
            status="processing",
            progress=0,
            message="Starting CV processing...",
            pages_count=0
        )
        
        # Start background processing
        asyncio.create_task(process_cv_document(document_id, temp_file_path, job_description))
        
        logger.info(f"Started processing CV: {file.filename} (ID: {document_id})")
        
        return processing_status[document_id]
        
    except Exception as e:
        logger.error(f"Error uploading CV: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading CV: {str(e)}")

@router.get("/status/{document_id}", response_model=ProcessingStatus)
async def get_processing_status(document_id: str):
    """Get processing status for a document"""
    if document_id not in processing_status:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return processing_status[document_id]

@router.post("/analyze/{document_id}", response_model=CVAnalysisResponse)
async def analyze_cv(document_id: str, job_description: Optional[str] = None):
    """
    Analyze CV and provide improvement suggestions
    
    Args:
        document_id: ID of the processed document
        job_description: Optional job description for targeted analysis
    
    Returns:
        Comprehensive CV analysis results
    """
    try:
        if document_id not in document_data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if processing_status[document_id].status != "completed":
            raise HTTPException(status_code=400, detail="Document processing not completed")
        
        # Get document content
        document_content = document_data[document_id]["content"]
        
        # Run CV analysis
        analysis_result = await cv_analyzer.analyze_cv(document_content, job_description or "")
        
        logger.info(f"CV analysis completed for document: {document_id}")
        
        return CVAnalysisResponse(
            overall_score=analysis_result.overall_score,
            strengths=analysis_result.strengths,
            weaknesses=analysis_result.weaknesses,
            improvement_suggestions=analysis_result.improvement_suggestions,
            keyword_match_score=analysis_result.keyword_match_score,
            experience_relevance=analysis_result.experience_relevance,
            skills_alignment=analysis_result.skills_alignment,
            format_score=analysis_result.format_score
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing CV: {e}")
        raise HTTPException(status_code=500, detail=f"Error analyzing CV: {str(e)}")

# Background Processing
# ============================================================================

async def process_cv_document(document_id: str, file_path: str, job_description: Optional[str]):
    """Background task to process CV document"""
    try:
        logger.info(f"Starting background processing for document: {document_id}")
        
        # Update status
        processing_status[document_id].progress = 10
        processing_status[document_id].message = "Parsing CV document..."
        
        # Parse document
        parsed_content = await document_processor.parse_document(file_path)
        
        if not parsed_content:
            raise Exception("Failed to parse CV document")
        
        # Update status
        processing_status[document_id].progress = 50
        processing_status[document_id].message = "Processing CV content..."
        
        # Chunk document
        chunks = document_processor.chunk_cv_document(parsed_content)
        
        # Generate embeddings
        chunk_texts = [chunk["content"] for chunk in chunks]
        embeddings = await document_processor.generate_embeddings(chunk_texts)
        
        # Store document data
        document_data[document_id] = {
            "content": parsed_content["content"],
            "chunks": chunks,
            "job_description": job_description,
            "parsed_at": parsed_content["parsed_at"]
        }
        
        document_embeddings[document_id] = embeddings
        
        # Update status to completed
        processing_status[document_id].status = "completed"
        processing_status[document_id].progress = 100
        processing_status[document_id].message = f"Processing completed successfully ({len(chunks)} chunks)"
        processing_status[document_id].pages_count = parsed_content["pages"]
        
        logger.info(f"Processing completed for document: {document_id}")
        
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        processing_status[document_id].status = "error"
        processing_status[document_id].error = str(e)
        processing_status[document_id].message = "Processing failed"
    
    finally:
        # Clean up temporary file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                os.rmdir(os.path.dirname(file_path))
        except Exception as e:
            logger.warning(f"Error cleaning up temp file: {e}")

# Learning Objectives
# ============================================================================
LEARNING_OBJECTIVES = [
    "Understand LangGraph workflow orchestration for multi-agent systems",
    "Learn CV-specific document processing and section detection",
    "Implement specialized agents for different analysis tasks",
    "Build cost-effective AI systems with targeted prompts",
    "Create structured analysis pipelines with fallback mechanisms",
    "Design user-friendly APIs for complex AI workflows"
]

@router.get("/learning-objectives")
async def get_learning_objectives():
    """Get learning objectives for this demo"""
    return {
        "demo": "CV Analyzer",
        "objectives": LEARNING_OBJECTIVES,
        "technologies": [
            "LangGraph",
            "LangChain",
            "LlamaIndex", 
            "Sentence Transformers",
            "FastAPI",
            "Multi-Agent Systems"
        ],
        "concepts": [
            "Agent Orchestration",
            "Document Processing",
            "CV Analysis",
            "Improvement Suggestions",
            "Cost Optimization"
        ]
    }
