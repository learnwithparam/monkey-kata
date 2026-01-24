from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse

from .models import URLRequest, QuestionRequest, ProcessingStatus
from .service import (
    process_url_background, 
    generate_rag_stream, 
    processing_status, 
    vector_store
)

router = APIRouter(prefix="/website-rag", tags=["website-rag"])

@router.post("/add-url")
async def add_url(request: URLRequest, background_tasks: BackgroundTasks):
    """
    Add a URL to process for RAG
    """
    url_str = str(request.url)
    
    # Initialize status if not exists
    if url_str not in processing_status:
        processing_status[url_str] = {
            "url": url_str,
            "status": "processing",
            "progress": 0,
            "message": "Queued for processing...",
            "documents_count": 0
        }
        
        # Start background processing
        background_tasks.add_task(
            process_url_background,
            url_str,
            request.chunk_size,
            request.chunk_overlap
        )
    
    return {
        "message": f"Started processing URL: {url_str}",
        "url": url_str,
        "status": "processing"
    }


@router.get("/status/{url:path}")
async def get_processing_status(url: str):
    """Get processing status for a specific URL"""
    if url not in processing_status:
        raise HTTPException(status_code=404, detail="URL not found")
    
    return ProcessingStatus(**processing_status[url])


@router.post("/ask/stream")
async def ask_question_stream(request: QuestionRequest):
    """
    Ask a question about a URL's content with streaming response
    """
    return StreamingResponse(
        generate_rag_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/clear")
async def clear_all_sessions():
    """Clear all processed URLs (useful for testing)"""
    vector_store.clear()
    processing_status.clear()
    return {"message": "All sessions cleared and vector store reset"}


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "website-rag",
        # We can't easily count "urls" in chroma without scanning, 
        # so we'll just show total chunks if possible or just success
        "vector_store": "chromadb",
        "collection_count": vector_store.collection.count()
    }
