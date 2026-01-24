from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any, AsyncGenerator
import asyncio
import uuid
import json
import os
import logging
import tempfile
import shutil

from utils.llm_provider import get_provider_config
from .models import ProcessingStatus, CVAnalysisResponse, ServiceInfo
from .service import (
    process_cv_document,
    cv_analyzer,
    processing_status,
    document_data,
    document_embeddings
)
from .cv_agentic_analyzer import set_cv_progress_callback

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cv-analyzer", tags=["cv-analyzer"])

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


@router.get("/provider-info")
async def get_provider_info():
    """
    Get current LLM provider information
    """
    try:
        config = get_provider_config()
        return {
            "provider_name": config["provider_name"],
            "model": config["model"]
        }
    except Exception as e:
        return {
            "provider_name": "unknown",
            "model": "unknown",
            "error": str(e)
        }

@router.post("/upload-cv")
async def upload_cv(
    file: UploadFile = File(...),
    job_description: Optional[str] = Form(None)
):
    """
    Upload a CV document for analysis
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
        processing_status[document_id] = {
            "document_id": document_id,
            "status": "processing",
            "progress": 0,
            "message": "Starting CV processing...",
            "pages_count": 0
        }
        
        # Start background processing
        asyncio.create_task(process_cv_document(document_id, temp_file_path, job_description))
        
        logger.info(f"Started processing CV: {file.filename} (ID: {document_id})")
        
        return ProcessingStatus(**processing_status[document_id])
        
    except Exception as e:
        logger.error(f"Error uploading CV: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading CV: {str(e)}")

@router.get("/status/{document_id}", response_model=ProcessingStatus)
async def get_processing_status(document_id: str):
    """Get processing status for a specific document"""
    if document_id not in processing_status:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return ProcessingStatus(**processing_status[document_id])

@router.post("/analyze/{document_id}", response_model=CVAnalysisResponse)
async def analyze_cv(document_id: str, job_description: Optional[str] = None):
    """
    Analyze CV using multi-agent system
    """
    try:
        if document_id not in document_data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if processing_status[document_id]["status"] != "completed":
            raise HTTPException(status_code=400, detail="Document processing not completed")
        
        # Get document content
        document_content = document_data[document_id]["content"]
        
        # Run multi-agent CV analysis
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


@router.post("/analyze-stream/{document_id}")
async def analyze_cv_stream(document_id: str, job_description: Optional[str] = None):
    """
    Analyze CV using multi-agent system with real-time streaming
    """
    async def stream_analysis() -> AsyncGenerator[str, None]:
        step_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        analysis_complete = asyncio.Event()
        analysis_result = None
        analysis_error = None
        
        def capture_progress(step_data):
            """Capture progress events to queue for streaming"""
            try:
                step_queue.put_nowait(step_data)
            except asyncio.QueueFull:
                logger.warning("Progress queue full, dropping event")
        
        try:
            if document_id not in document_data:
                yield f"data: {json.dumps({'error': 'Document not found'})}\n\n"
                return
            
            if processing_status[document_id]["status"] != "completed":
                yield f"data: {json.dumps({'error': 'Document processing not completed'})}\n\n"
                return
            
            # Get document content
            document_content = document_data[document_id]["content"]
            
            # Set up progress callback
            set_cv_progress_callback(capture_progress)
            
            yield f"data: {json.dumps({'status': 'connected', 'message': 'Starting multi-agent CV analysis...'})}\n\n"
            
            # Run analysis in background
            async def run_analysis():
                nonlocal analysis_result, analysis_error
                try:
                    result = await cv_analyzer.analyze_cv(document_content, job_description or "")
                    analysis_result = result
                    analysis_complete.set()
                except Exception as e:
                    analysis_error = str(e)
                    analysis_complete.set()
                finally:
                    set_cv_progress_callback(None)
            
            # Start analysis task
            analysis_task = asyncio.create_task(run_analysis())
            
            # Stream progress events
            while not analysis_complete.is_set():
                try:
                    step_data = await asyncio.wait_for(step_queue.get(), timeout=0.1)
                    yield f"data: {json.dumps({'step': step_data})}\n\n"
                except asyncio.TimeoutError:
                    continue
            
            # Drain any remaining steps
            while not step_queue.empty():
                try:
                    step_data = step_queue.get_nowait()
                    yield f"data: {json.dumps({'step': step_data})}\n\n"
                except asyncio.QueueEmpty:
                    break
            
            # Send final result
            if analysis_error:
                yield f"data: {json.dumps({'done': True, 'status': 'error', 'error': analysis_error})}\n\n"
            elif analysis_result:
                yield f"data: {json.dumps({'done': True, 'status': 'completed', 'result': {'overall_score': analysis_result.overall_score, 'strengths': analysis_result.strengths, 'weaknesses': analysis_result.weaknesses, 'improvement_suggestions': analysis_result.improvement_suggestions, 'keyword_match_score': analysis_result.keyword_match_score, 'experience_relevance': analysis_result.experience_relevance, 'skills_alignment': analysis_result.skills_alignment, 'format_score': analysis_result.format_score, 'score_rationale': analysis_result.score_rationale, 'ats_analysis': analysis_result.ats_analysis}})}\n\n"
            
            await analysis_task
            
        except Exception as e:
            logger.error(f"Error in streaming analysis: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            set_cv_progress_callback(None)
    
    return StreamingResponse(
        stream_analysis(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/learning-objectives")
async def get_learning_objectives():
    """Get learning objectives for this demo"""
    return {
        "demo": "CV Analyzer",
        "objectives": [
            "Understand LangGraph workflow orchestration for multi-agent systems",
            "Learn CV-specific document processing and section detection",
            "Implement specialized agents for different analysis tasks",
            "Build cost-effective AI systems with targeted prompts",
            "Create structured analysis pipelines with fallback mechanisms",
            "Design user-friendly APIs for complex AI workflows"
        ],
        "technologies": [
            "Workflow Orchestration",
            "Document Processing", 
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
