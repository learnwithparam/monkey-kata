from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import StreamingResponse
import uuid
import tempfile
import shutil
import os

from .models import QuestionRequest, ProcessingStatus
from .service import (
    process_document_background,
    generate_document_rag_stream,
    processing_status,
    document_data,
    document_embeddings
)

router = APIRouter(prefix="/document-qa-chatbot", tags=["document-qa-chatbot"])

@router.post("/upload-document")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    chunk_size: int = 500,
    chunk_overlap: int = 50
):
    """
    Upload a document for Q&A processing
    """
    # Validate file type
    allowed_types = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain'
    ]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail="Unsupported file type. Please upload PDF, Word, or text files."
        )
    
    # Generate unique document ID
    document_id = str(uuid.uuid4())
    
    # Save file temporarily
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}")
    temp_path = temp_file.name
    temp_file.close()
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Initialize processing status
    processing_status[document_id] = {
        "document_id": document_id,
        "status": "processing",
        "progress": 0,
        "message": "Queued for processing...",
        "pages_count": 0
    }
    
    # Start background processing
    background_tasks.add_task(
        process_document_background,
        document_id,
        temp_path,
        chunk_size,
        chunk_overlap
    )
    
    return {
        "message": f"Document uploaded successfully: {file.filename}",
        "document_id": document_id,
        "status": "processing"
    }


@router.get("/status/{document_id}")
async def get_processing_status(document_id: str):
    """Get processing status for a specific document"""
    if document_id not in processing_status:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return ProcessingStatus(**processing_status[document_id])


@router.post("/ask/stream")
async def ask_question_stream(request: QuestionRequest):
    """
    Ask a question about a document with streaming response
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
    """Clear all processed documents (useful for testing)"""
    document_data.clear()
    document_embeddings.clear()
    processing_status.clear()
    return {"message": "All sessions cleared"}


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "document-qa-chatbot",
        "documents_processed": len(document_data),
        "total_chunks": sum(len(docs['documents']) for docs in document_data.values())
    }
