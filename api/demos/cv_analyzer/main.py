"""
CV Analyzer API
===============

🎯 LEARNING OBJECTIVES:
This demo teaches you how to build a multi-agent AI system:

1. Multi-Agent Systems - How to coordinate specialized AI agents
2. Workflow Orchestration - How to orchestrate complex AI pipelines
3. Document Processing - How to parse and structure CV documents
4. Agentic Design - How to decompose tasks into specialized agents
5. State Management - How agents share information through shared state
6. Cost Optimization - How targeted prompts reduce API costs

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Setup - Initialize providers and storage
Step 2: Data Models - Define request structures
Step 3: Background Processing - Parse and index CV documents
Step 4: Agentic Analysis - Multi-agent workflow for CV analysis
Step 5: API Endpoints - Expose functionality via HTTP

Key Concept: Multi-agent systems break complex tasks into specialized agents
that work together through a shared state. This improves quality, reduces costs,
and makes the system more maintainable.
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
from utils.llm_provider import get_llm_provider, get_provider_config
from .cv_utils import CVDocumentProcessor
from .cv_agentic_analyzer import CVAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# STEP 1: SETUP & INITIALIZATION
# ============================================================================
"""
Understanding CV Analyzer Components:
- LLM Provider: Powers all AI agents (we know this from previous demos)
- Document Processor: Parses CV documents (PDF, Word, text) and extracts sections
- CV Analyzer: Multi-agent system using LangGraph for orchestration
- Embeddings: Converts CV chunks to vectors for future semantic search

In-Memory Storage:
- document_data: Stores parsed CV content and chunks
- document_embeddings: Stores vector embeddings for each CV
- processing_status: Tracks CV processing progress

Multi-Agent System:
Unlike simple RAG (retrieve + generate), this uses multiple specialized agents
that work together:
1. Content Extractor: Structures raw CV into JSON
2. Strengths Analyzer: Identifies CV strengths
3. Weaknesses Analyzer: Finds areas for improvement
4. Improvement Suggester: Provides actionable suggestions
5. CV Scorer: Calculates overall score

Note: This uses in-memory storage for simplicity. In production,
you'd use a persistent vector database like Pinecone or Weaviate.
"""
router = APIRouter(prefix="/cv-analyzer", tags=["cv-analyzer"])

# Initialize providers
llm_provider = get_llm_provider()
document_processor = CVDocumentProcessor()
cv_analyzer = CVAnalyzer(llm_provider)

# In-memory storage (use database in production)
document_data: Dict[str, Dict[str, Any]] = {}
document_embeddings: Dict[str, List[List[float]]] = {}
processing_status: Dict[str, Dict[str, Any]] = {}


# ============================================================================
# STEP 2: DATA MODELS
# ============================================================================
"""
Request Models:
- ProcessingStatus: Shows the current state of CV processing
- CVAnalysisResponse: Comprehensive analysis results from multi-agent system
- ServiceInfo: Health check information

These models ensure type safety and automatic validation.
The CVAnalysisResponse includes scores and suggestions from multiple agents.
"""
class ProcessingStatus(BaseModel):
    """Status of CV processing"""
    document_id: str
    status: str  # "processing", "completed", "error"
    progress: int  # 0-100
    message: str
    pages_count: int = 0
    error: Optional[str] = None


class CVAnalysisResponse(BaseModel):
    """Complete CV analysis result from multi-agent system"""
    overall_score: int  # From Scorer Agent
    strengths: List[str]  # From Strengths Agent
    weaknesses: List[str]  # From Weaknesses Agent
    improvement_suggestions: List[str]  # From Suggester Agent
    keyword_match_score: int
    experience_relevance: int
    skills_alignment: int
    format_score: int


class ServiceInfo(BaseModel):
    """Health check response"""
    status: str
    service: str
    description: str
    documents_processed: int
    total_chunks: int

# ============================================================================
# STEP 3: BACKGROUND PROCESSING (CV Ingestion)
# ============================================================================
"""
The CV Ingestion Pipeline:
This processes uploaded CV documents and prepares them for analysis:

1. Parse: Extract text from PDF, Word, or text files
2. Chunk: Split content into CV-specific sections (Experience, Education, Skills, etc.)
3. Embed: Convert chunks into vector embeddings (for future semantic search)
4. Store: Save embeddings for potential future retrieval

Why Background Processing?
- CV parsing can take time (especially PDFs with complex formatting)
- Embedding generation is CPU-intensive
- We don't want to block the API while processing
- Allows real-time status updates to the frontend
"""
async def process_cv_document(document_id: str, file_path: str, job_description: Optional[str]):
    """
    Background task to process a CV document through the ingestion pipeline
    
    This runs asynchronously so the API can respond immediately while
    processing happens in the background.
    """
    try:
        logger.info(f"Starting background processing for document: {document_id}")
        
        # Step 1: Update status - starting
        processing_status[document_id] = {
            "document_id": document_id,
            "status": "processing",
            "progress": 10,
            "message": "Parsing CV document...",
            "pages_count": 0
        }
        
        # Step 2: Parse document (extract text from PDF/Word/text)
        parsed_content = await document_processor.parse_document(file_path)
        
        if not parsed_content:
            raise Exception("Failed to parse CV document")
        
        # Step 3: Update status - processing
        processing_status[document_id].update({
            "progress": 50,
            "message": "Processing CV content..."
        })
        
        # Step 4: Chunk document (CV-specific section detection)
        chunks = document_processor.chunk_cv_document(parsed_content)
        
        # Step 5: Generate embeddings for all chunks
        chunk_texts = [chunk["content"] for chunk in chunks]
        embeddings = await document_processor.generate_embeddings(chunk_texts)
        
        # Step 6: Store document data
        document_data[document_id] = {
            "content": parsed_content["content"],
            "chunks": chunks,
            "job_description": job_description,
            "parsed_at": parsed_content["parsed_at"]
        }
        
        document_embeddings[document_id] = embeddings
        
        # Step 7: Mark as completed
        processing_status[document_id].update({
            "status": "completed",
            "progress": 100,
            "message": f"Processing completed successfully ({len(chunks)} chunks)",
            "pages_count": parsed_content["pages"]
        })
        
        logger.info(f"Processing completed for document: {document_id}")
        
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        processing_status[document_id] = {
            "document_id": document_id,
            "status": "error",
            "error": str(e),
            "message": "Processing failed",
            "progress": 0,
            "pages_count": 0
        }
    
    finally:
        # Clean up temporary file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                os.rmdir(os.path.dirname(file_path))
        except Exception as e:
            logger.warning(f"Error cleaning up temp file: {e}")


# ============================================================================
# STEP 4: AGENTIC ANALYSIS (Multi-Agent Workflow)
# ============================================================================
"""
The Agentic Analysis Pipeline:
When a user requests CV analysis, we use a multi-agent system:

1. Content Extractor Agent: Structures raw CV into JSON format
2. Strengths Agent: Identifies key strengths
3. Weaknesses Agent: Finds areas for improvement
4. Suggester Agent: Generates actionable suggestions (uses weaknesses)
5. Scorer Agent: Calculates overall score (uses strengths + weaknesses)

Why Multi-Agent?
- Each agent has a focused, single responsibility
- Agents can read from and write to shared state
- Better quality: Specialized prompts outperform general prompts
- Cost-effective: Smaller, targeted prompts cost less
- Maintainable: Easy to modify or replace individual agents
- Collaborative: Agents build on each other's work

The workflow orchestrates this process, managing state transitions between agents.
"""
# (Analysis happens in cv_analyzer.analyze_cv() which coordinates all agents)


# ============================================================================
# STEP 5: API ENDPOINTS
# ============================================================================
"""
API Endpoints:
- POST /upload-cv: Upload and process a CV (ingestion)
- GET /status/{document_id}: Check processing status
- POST /analyze/{document_id}: Run multi-agent analysis (workflow)
- GET /health: Health check
- GET /learning-objectives: Get learning objectives
"""
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
    
    Returns the provider name so frontend can show appropriate warnings.
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
    
    This endpoint:
    1. Accepts PDF, Word, or text files
    2. Validates file type
    3. Saves file temporarily
    4. Starts background processing (parsing, chunking, embedding)
    5. Returns immediately with document_id
    
    The actual processing happens in the background, so this endpoint
    responds quickly while the CV is being indexed.
    
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
        
        # Initialize processing status as dict (for background updates)
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
    
    This is the main agentic analysis endpoint. It:
    1. Checks if CV is processed
    2. Runs the multi-agent workflow with specialized agents:
       - Content Extractor: Structures CV into JSON
       - Strengths Agent: Identifies strengths
       - Weaknesses Agent: Finds weaknesses
       - Suggester Agent: Generates improvement suggestions
       - Scorer Agent: Calculates overall score
    3. Returns comprehensive analysis results
    
    The multi-agent workflow runs in sequence, with each agent
    reading from and writing to shared state.
    
    Args:
        document_id: ID of the processed document
        job_description: Optional job description for targeted analysis
    
    Returns:
        Comprehensive CV analysis results from all agents
    """
    try:
        if document_id not in document_data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if processing_status[document_id]["status"] != "completed":
            raise HTTPException(status_code=400, detail="Document processing not completed")
        
        # Get document content
        document_content = document_data[document_id]["content"]
        
        # Run multi-agent CV analysis (workflow orchestrates all agents)
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

# Learning Objectives
# ============================================================================
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


# ============================================================================
# LEARNING CHECKLIST
# ============================================================================
"""
After reading this code, you should understand:

✓ How to process CV documents (PDF, Word, text)
✓ How CV-specific chunking works (section detection)
✓ How embeddings enable semantic search
✓ How multi-agent systems coordinate specialized agents
✓ How workflow orchestration coordinates agents with shared state
✓ Why multi-agent systems improve quality and reduce costs

Key Multi-Agent Concepts:
- Ingestion: Upload → parse → chunk → embed → store
- Analysis: CV content → Content Extractor → Strengths Agent → Weaknesses Agent → Suggester Agent → Scorer Agent
- State Management: Agents read from and write to shared state
- Why Multi-Agent: Specialized agents outperform general prompts

Next Steps:
1. Try analyzing different CVs and see how agents adapt
2. Experiment with different job descriptions and see analysis change
3. Add new agents (e.g., FormatChecker Agent, KeywordOptimizer Agent)
4. Modify agent prompts and see how it affects results
5. Implement parallel agent execution (strengths + weaknesses in parallel)

Questions to Consider:
- How would you handle conflicting agent opinions?
- How could you add a "human-in-the-loop" agent for review?
- What if one agent fails? Should the workflow continue?
- How would you optimize for cost vs quality?
- How could agents learn from user feedback?
"""
