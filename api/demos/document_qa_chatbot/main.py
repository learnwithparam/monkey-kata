"""
Document QA Chatbot Demo API
============================

🎯 LEARNING OBJECTIVES FOR BOOTCAMP STUDENTS:

This demo teaches advanced document processing and RAG concepts:

1. DOCUMENT PARSING & EXTRACTION
   - How to parse various document types (PDF, Word, text, etc.)
   - Handling different content structures and formats
   - Using LlamaIndex for robust document processing

2. GENERIC DOCUMENT ANALYSIS
   - Content understanding and summarization
   - Key information extraction
   - Document structure analysis

3. SEMANTIC CHUNKING FOR ANY TEXT
   - Preserving context across chunks
   - Handling different document types
   - Maintaining document structure

4. RAG PIPELINE FOR DOCUMENT Q&A
   - Generic prompt engineering for any document type
   - Context-aware response generation
   - Citation and source tracking

Key Files to Study:
- main.py (this file) - API endpoints and document analysis pipeline
- document_utils.py - Document parsing and analysis
- frontend/page.tsx - How to consume document analysis APIs

🚀 Try This:
1. Start the API: docker compose up
2. Visit: http://localhost:4020/demos/document-qa-chatbot
3. Upload any document and ask questions!
"""

# ============================================================================
# IMPORTS
# ============================================================================
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, AsyncGenerator
import asyncio
import json
import uuid
from datetime import datetime
import os
import logging
import tempfile
import shutil
from utils.llm_provider import get_llm_provider
from .document_utils import LegalDocumentProcessor, LegalRAGPipeline

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# ROUTER SETUP
# ============================================================================
router = APIRouter(prefix="/document-qa-chatbot", tags=["document-qa-chatbot"])

# Initialize providers
llm_provider = get_llm_provider()
document_processor = LegalDocumentProcessor()
document_rag_pipeline = LegalRAGPipeline(llm_provider)

# In-memory storage for demo (use database in production)
document_data = {}  # document_id -> document data
document_embeddings = {}  # document_id -> embeddings
processing_status = {}  # document_id -> status

# Session cleanup - simple in-memory storage
last_activity = {}  # document_id -> timestamp

def cleanup_inactive_sessions():
    """Clean up sessions that have been inactive for 5+ minutes"""
    import time
    current_time = time.time()
    inactive_docs = []
    
    for doc_id, timestamp in last_activity.items():
        if current_time - timestamp > 300:  # 5 minutes
            inactive_docs.append(doc_id)
    
    for doc_id in inactive_docs:
        # Clean up data
        document_data.pop(doc_id, None)
        document_embeddings.pop(doc_id, None)
        processing_status.pop(doc_id, None)
        last_activity.pop(doc_id, None)
        print(f"Cleaned up inactive session for document: {doc_id}")

# ============================================================================
# DATA MODELS
# ============================================================================
class DocumentUploadRequest(BaseModel):
    """Request model for document upload"""
    chunk_size: int = 500
    chunk_overlap: int = 50

class QuestionRequest(BaseModel):
    """Request model for asking questions"""
    question: str
    document_id: str
    max_chunks: int = 5

class ProcessingStatus(BaseModel):
    """Status of document processing"""
    document_id: str
    status: str  # "processing", "completed", "error"
    progress: int  # 0-100
    message: str
    pages_count: int = 0
    error: Optional[str] = None

class DocumentChunk(BaseModel):
    """A document chunk with metadata"""
    content: str
    document_id: str
    chunk_index: int
    page_number: int
    metadata: Dict[str, Any]


# ============================================================================
# BACKGROUND PROCESSING
# ============================================================================
async def process_document_background(document_id: str, file_path: str, chunk_size: int, chunk_overlap: int):
    """Background task to process a document using LlamaIndex"""
    try:
        print(f"🚀 Starting background processing for document: {document_id}")
        print(f"📁 File path: {file_path}")
        print(f"✅ File exists: {os.path.exists(file_path)}")
        
        # Update status
        processing_status[document_id] = ProcessingStatus(
            document_id=document_id,
            status="processing",
            progress=10,
            message="Starting to parse document with LlamaIndex..."
        )
        
        # Parse document
        print(f"📄 Parsing document: {file_path}")
        document_content = await document_processor.parse_document(file_path)
        print(f"✅ Parsing result: {document_content is not None}")
        
        if not document_content:
            print("❌ Failed to parse document")
            raise Exception("Failed to parse document")
        
        content = document_content.get('content', '')
        print(f"📄 Document content length: {len(content)}")
        print(f"📄 Content preview: {content[:200]}...")
        
        processing_status[document_id] = ProcessingStatus(
            document_id=document_id,
            status="processing",
            progress=40,
            message="Document parsed, creating vector index..."
        )
        
        # Chunk the content
        chunks = document_processor.chunk_document(document_content, chunk_size, chunk_overlap)
        documents = []
        
        for i, chunk in enumerate(chunks):
            doc = DocumentChunk(
                content=chunk['content'],
                document_id=document_id,
                chunk_index=i,
                page_number=chunk.get('page_number', 1),
                metadata={
                    "title": document_content.get("title", ""),
                    "document_id": document_id,
                    "chunk_size": len(chunk['content']),
                    "created_at": datetime.now().isoformat()
                }
            )
            documents.append(doc)
        
        processing_status[document_id] = ProcessingStatus(
            document_id=document_id,
            status="processing",
            progress=70,
            message="Generating embeddings with LlamaIndex..."
        )
        
        # Generate embeddings
        embeddings = await document_processor.generate_embeddings([doc.content for doc in documents])
        
        # Store results
        document_data[document_id] = {
            'documents': documents,
            'content': document_content,
            'file_path': file_path,
            'processor': document_processor
        }
        document_embeddings[document_id] = embeddings
        
        # Mark as completed
        print(f"🎉 Processing completed for document: {document_id}")
        processing_status[document_id] = ProcessingStatus(
            document_id=document_id,
            status="completed",
            progress=100,
            message="Processing completed successfully",
            pages_count=len(chunks)
        )
        print(f"✅ Final status: {processing_status[document_id].status}")
        
        # Clean up temporary file
        try:
            os.remove(file_path)
        except:
            pass
        
    except Exception as e:
        print(f"Error processing document {document_id}: {str(e)}")
        processing_status[document_id] = ProcessingStatus(
            document_id=document_id,
            status="error",
            progress=0,
            message="Processing failed",
            error=str(e)
        )
        
        # Clean up temporary file
        try:
            os.remove(file_path)
        except:
            pass

# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/upload-document")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    chunk_size: int = 500,
    chunk_overlap: int = 50
):
    """
    Upload a document for analysis
    
    This endpoint accepts PDF, Word, or text files and starts
    background processing for document parsing and indexing.
    """
    try:
        print(f"Received document upload: {file.filename}")
        
        # Clean up inactive sessions first
        cleanup_inactive_sessions()
        
        # Validate file type
        allowed_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain'
        ]
        
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Unsupported file type. Please upload PDF, Word, or text files.")
        
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        # Save file temporarily
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}")
        temp_path = temp_file.name
        temp_file.close()
        
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Initialize processing status
        processing_status[document_id] = ProcessingStatus(
            document_id=document_id,
            status="processing",
            progress=0,
            message="Queued for processing..."
        )
        
        # Start background processing
        print(f"Adding background task for document: {document_id}")
        background_tasks.add_task(
            process_document_background,
            document_id,
            temp_path,
            chunk_size,
            chunk_overlap
        )
        print(f"Background task added successfully")
        
        # Update activity timestamp
        import time
        last_activity[document_id] = time.time()
        
        return {
            "message": f"Document uploaded successfully: {file.filename}",
            "document_id": document_id,
            "status": "processing"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")

@router.get("/status/{document_id}")
async def get_processing_status(document_id: str):
    """Get processing status for a specific document"""
    if document_id not in processing_status:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return processing_status[document_id]


async def generate_document_rag_stream(request: QuestionRequest) -> AsyncGenerator[str, None]:
    """
    Generate document RAG response with streaming
    """
    try:
        # Clean up inactive sessions first
        cleanup_inactive_sessions()
        
        document_id = request.document_id
        
        # Check if document is processed
        if document_id not in processing_status or processing_status[document_id].status != "completed":
            yield f"data: {json.dumps({'error': f'Document not yet processed: {document_id}', 'status': 'error'})}\n\n"
            return
        
        # Update activity timestamp
        import time
        last_activity[document_id] = time.time()
        
        # Get documents and embeddings
        if document_id not in document_data or document_id not in document_embeddings:
            yield f"data: {json.dumps({'error': 'No document data available', 'status': 'error'})}\n\n"
            return
        
        documents = document_data[document_id]['documents']
        embeddings = document_embeddings[document_id]
        
        # Send initial status
        yield f"data: {json.dumps({'status': 'connected', 'message': 'Analyzing your question...'})}\n\n"
        
        # Retrieve relevant chunks
        yield f"data: {json.dumps({'status': 'processing', 'message': 'Finding relevant content...'})}\n\n"
        # Generate query embedding
        query_embedding = await document_processor.generate_embeddings([request.question])
        
        # Retrieve relevant chunks
        relevant_chunks = document_rag_pipeline.retrieve_relevant_chunks(
            query_embedding[0],
            embeddings,
            documents,
            request.max_chunks
        )
        
        # Send sources
        yield f"data: {json.dumps({'sources': [{'url': f'Page {chunk.page_number}', 'content': chunk.content[:200] + '...'} for chunk in relevant_chunks]})}\n\n"
        
        # Generate streaming answer
        yield f"data: {json.dumps({'status': 'generating', 'message': 'Generating answer...'})}\n\n"
        
        try:
            async for chunk in document_rag_pipeline.generate_answer_stream(request.question, relevant_chunks):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            
            # Send completion
            yield f"data: {json.dumps({'done': True, 'status': 'completed'})}\n\n"
        except Exception as e:
            logger.error(f"Error in streaming generation: {e}")
            yield f"data: {json.dumps({'error': f'Error generating response: {str(e)}', 'status': 'error'})}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e), 'status': 'error'})}\n\n"

@router.post("/ask/stream")
async def ask_question_stream(request: QuestionRequest):
    """
    Ask a question about the document with streaming response
    
    This provides real-time streaming of the document analysis,
    with proper context and source tracking.
    """
    return StreamingResponse(
        generate_document_rag_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@router.post("/clear")
async def clear_all_sessions():
    """Clear all sessions - useful for testing"""
    global document_data, document_embeddings, processing_status, last_activity
    document_data.clear()
    document_embeddings.clear()
    processing_status.clear()
    last_activity.clear()
    return {"message": "All sessions cleared"}

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "document-qa-chatbot",
        "description": "Generic document analysis and Q&A system",
        "documents_processed": len(document_data),
        "total_chunks": sum(len(docs['documents']) for docs in document_data.values())
    }

@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify the service is working"""
    return {
        "message": "Document QA Chatbot API is working!",
        "timestamp": datetime.now().isoformat(),
        "processing_status_count": len(processing_status),
        "document_data_count": len(document_data)
    }


"""
LEARNING NOTES FOR STUDENTS:
===========================

1. DOCUMENT PROCESSING:
   - Use LlamaIndex for robust document parsing
   - Handle various document types (PDF, Word, text)
   - Preserve document structure and formatting
   - Extract metadata like page numbers and sections

2. GENERIC DOCUMENT ANALYSIS:
   - Content understanding and summarization
   - Key information extraction
   - Document structure analysis
   - Generic prompt engineering for any document type

3. RAG PIPELINE CONSIDERATIONS:
   - Use generic prompts and context
   - Maintain accuracy and avoid hallucination
   - Provide proper citations and sources
   - Consider document type in responses

4. PRODUCTION CONSIDERATIONS:
   - Implement proper document security
   - Add document type detection
   - Use appropriate embedding models
   - Implement audit trails and logging
"""
