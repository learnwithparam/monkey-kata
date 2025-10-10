"""
Website RAG Demo API - Simple & Fast
====================================

🎯 LEARNING OBJECTIVES FOR BOOTCAMP STUDENTS:

This demo teaches core RAG (Retrieval-Augmented Generation) concepts:

1. WEB SCRAPING & CONTENT EXTRACTION
   - How to scrape and clean website content
   - Handling different content types and structures
   - Error handling for failed requests

2. SEMANTIC CHUNKING
   - How to split content into meaningful chunks
   - Preserving context across chunk boundaries
   - Optimizing chunk size for retrieval

3. VECTOR EMBEDDINGS
   - How to generate embeddings for text chunks
   - Using local embedding models for cost efficiency
   - Storing and retrieving vector embeddings

4. RAG PIPELINE WITH STREAMING
   - How to implement retrieval-augmented generation
   - Combining retrieved context with user queries
   - Real-time streaming responses like ChatGPT

Key Files to Study:
- main.py (this file) - API endpoints and RAG pipeline
- rag_utils.py - RAG implementation details
- frontend/page.tsx - How to consume RAG APIs

🚀 Try This:
1. Start the API: docker compose up
2. Visit: http://localhost:4020/demos/website-rag
3. Add URLs and ask questions about the content!
"""

# ============================================================================
# IMPORTS
# ============================================================================
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Any, Optional, AsyncGenerator
import asyncio
import json
import uuid
from datetime import datetime
import os
import logging
from utils.llm_provider import get_llm_provider
from .rag_utils import SimpleRAGPipeline, WebScraper, EmbeddingProvider

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# ROUTER SETUP
# ============================================================================
router = APIRouter(prefix="/website-rag", tags=["website-rag"])

# Initialize providers
llm_provider = get_llm_provider()
embedding_provider = EmbeddingProvider()
web_scraper = WebScraper()
rag_pipeline = SimpleRAGPipeline(llm_provider, embedding_provider)

# In-memory storage for demo (use database in production)
url_documents = {}  # url -> documents
url_embeddings = {}  # url -> embeddings
processing_status = {}  # url -> status

# Session cleanup - simple in-memory storage
last_activity = {}  # url -> timestamp

def cleanup_inactive_sessions():
    """Clean up sessions that have been inactive for 5+ minutes"""
    import time
    current_time = time.time()
    inactive_urls = []
    
    for url, timestamp in last_activity.items():
        if current_time - timestamp > 300:  # 5 minutes
            inactive_urls.append(url)
    
    for url in inactive_urls:
        # Clean up data
        url_documents.pop(url, None)
        url_embeddings.pop(url, None)
        processing_status.pop(url, None)
        last_activity.pop(url, None)
        print(f"Cleaned up inactive session for URL: {url}")

# ============================================================================
# DATA MODELS
# ============================================================================
class URLRequest(BaseModel):
    """Request model for adding URLs to process"""
    url: HttpUrl
    chunk_size: int = 500
    chunk_overlap: int = 50

class QuestionRequest(BaseModel):
    """Request model for asking questions"""
    question: str
    url: HttpUrl
    max_chunks: int = 5

class ProcessingStatus(BaseModel):
    """Status of URL processing"""
    url: str
    status: str  # "processing", "completed", "error"
    progress: int  # 0-100
    message: str
    documents_count: int = 0
    error: Optional[str] = None

class DocumentChunk(BaseModel):
    """A document chunk with metadata"""
    content: str
    url: str
    chunk_index: int
    metadata: Dict[str, Any]

# ============================================================================
# BACKGROUND PROCESSING
# ============================================================================
async def process_url_background(url: str, chunk_size: int, chunk_overlap: int):
    """Background task to process a URL and extract content"""
    try:
        print(f"Starting background processing for URL: {url}")
        
        # Update status
        processing_status[url] = ProcessingStatus(
            url=url,
            status="processing",
            progress=10,
            message="Starting to scrape content..."
        )
        
        # Scrape content
        print(f"Scraping content from: {url}")
        content = await web_scraper.scrape_url(url)
        print(f"Scraping result: {content is not None}")
        
        if not content:
            raise Exception("Failed to extract content from URL")
        
        processing_status[url] = ProcessingStatus(
            url=url,
            status="processing",
            progress=40,
            message="Content extracted, chunking documents..."
        )
        
        # Chunk the content
        chunks = web_scraper.chunk_content(content, chunk_size, chunk_overlap)
        documents = []
        
        for i, chunk in enumerate(chunks):
            doc = DocumentChunk(
                content=chunk,
                url=url,
                chunk_index=i,
                metadata={
                    "title": content.get("title", ""),
                    "url": url,
                    "chunk_size": len(chunk),
                    "created_at": datetime.now().isoformat()
                }
            )
            documents.append(doc)
        
        processing_status[url] = ProcessingStatus(
            url=url,
            status="processing",
            progress=70,
            message="Generating embeddings..."
        )
        
        # Generate embeddings
        embeddings = await embedding_provider.generate_embeddings([doc.content for doc in documents])
        
        # Store results
        url_documents[url] = documents
        url_embeddings[url] = embeddings
        
        # Mark as completed
        processing_status[url] = ProcessingStatus(
            url=url,
            status="completed",
            progress=100,
            message="Processing completed successfully",
            documents_count=len(documents)
        )
        
    except Exception as e:
        print(f"Error processing URL {url}: {str(e)}")
        processing_status[url] = ProcessingStatus(
            url=url,
            status="error",
            progress=0,
            message="Processing failed",
            error=str(e)
        )

# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/add-url")
async def add_url(request: URLRequest, background_tasks: BackgroundTasks):
    """
    Add a URL to process for RAG
    
    This endpoint starts background processing of a URL to extract content,
    chunk it, and generate embeddings for retrieval.
    """
    try:
        print(f"Received request to process URL: {request.url}")
        
        # Clean up inactive sessions first
        cleanup_inactive_sessions()
        
        url_str = str(request.url)
        print(f"Processing URL: {url_str}")
        
        if url_str not in processing_status:
            processing_status[url_str] = ProcessingStatus(
                url=url_str,
                status="processing",
                progress=0,
                message="Queued for processing..."
            )
            background_tasks.add_task(
                process_url_background,
                url_str,
                request.chunk_size,
                request.chunk_overlap
            )
            print(f"Added background task for: {url_str}")
        else:
            print(f"URL already in processing: {url_str}")
        
        # Update activity timestamp
        import time
        last_activity[url_str] = time.time()
        
        return {
            "message": f"Started processing URL: {url_str}",
            "url": url_str,
            "status": "processing"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start processing: {str(e)}")

@router.get("/status/{url:path}")
async def get_processing_status(url: str):
    """Get processing status for a specific URL"""
    if url not in processing_status:
        raise HTTPException(status_code=404, detail="URL not found")
    
    return processing_status[url]

@router.get("/status")
async def get_all_status():
    """Get processing status for all URLs"""
    return {
        "urls": list(processing_status.values()),
        "total_urls": len(processing_status),
        "completed": len([s for s in processing_status.values() if s.status == "completed"]),
        "processing": len([s for s in processing_status.values() if s.status == "processing"]),
        "errors": len([s for s in processing_status.values() if s.status == "error"])
    }

async def generate_rag_stream(request: QuestionRequest) -> AsyncGenerator[str, None]:
    """
    Generate RAG response with streaming
    """
    try:
        # Clean up inactive sessions first
        cleanup_inactive_sessions()
        
        url_str = str(request.url)
        
        # Check if URL is processed
        if url_str not in processing_status or processing_status[url_str].status != "completed":
            yield f"data: {json.dumps({'error': f'URL not yet processed: {url_str}', 'status': 'error'})}\n\n"
            return
        
        # Update activity timestamp
        import time
        last_activity[url_str] = time.time()
        
        # Get documents and embeddings
        if url_str not in url_documents or url_str not in url_embeddings:
            yield f"data: {json.dumps({'error': 'No documents available for the requested URL', 'status': 'error'})}\n\n"
            return
        
        documents = url_documents[url_str]
        embeddings = url_embeddings[url_str]
        
        # Send initial status
        yield f"data: {json.dumps({'status': 'connected', 'message': 'Processing your question...'})}\n\n"
        
        # Generate query embedding
        yield f"data: {json.dumps({'status': 'processing', 'message': 'Analyzing your question...'})}\n\n"
        query_embedding = await embedding_provider.generate_embeddings([request.question])
        
        # Retrieve relevant chunks
        yield f"data: {json.dumps({'status': 'processing', 'message': 'Finding relevant information...'})}\n\n"
        relevant_chunks = rag_pipeline.retrieve_relevant_chunks(
            query_embedding[0],
            embeddings,
            documents,
            request.max_chunks
        )
        
        # Send sources
        yield f"data: {json.dumps({'sources': [{'url': chunk.url, 'content': chunk.content[:200] + '...'} for chunk in relevant_chunks]})}\n\n"
        
        # Generate streaming answer
        yield f"data: {json.dumps({'status': 'generating', 'message': 'Generating answer...'})}\n\n"
        
        try:
            async for chunk in rag_pipeline.generate_answer_stream(request.question, relevant_chunks):
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
    Ask a question with streaming response
    
    This provides real-time streaming of the RAG answer,
    similar to ChatGPT's interface.
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
    """Clear all sessions - useful for testing"""
    global url_documents, url_embeddings, processing_status, last_activity
    url_documents.clear()
    url_embeddings.clear()
    processing_status.clear()
    last_activity.clear()
    return {"message": "All sessions cleared"}

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "website-rag",
        "description": "Simple RAG system for website content Q&A",
        "urls_processed": len(url_documents),
        "total_documents": sum(len(docs) for docs in url_documents.values())
    }

"""
LEARNING NOTES FOR STUDENTS:
===========================

1. RAG PIPELINE COMPONENTS:
   - Web Scraping: Extract content from URLs
   - Chunking: Split content into manageable pieces
   - Embeddings: Convert text to vectors for similarity search
   - Retrieval: Find relevant chunks for a query
   - Generation: Use LLM to answer based on retrieved context

2. SEMANTIC CHUNKING:
   - Split by sentences/paragraphs, not just characters
   - Preserve context across chunk boundaries
   - Use overlap to maintain coherence
   - Consider content type (headings, lists, etc.)

3. VECTOR SIMILARITY:
   - Use cosine similarity to find relevant chunks
   - Consider both semantic similarity and keyword matching
   - Implement ranking and filtering strategies

4. RAG LIMITATIONS:
   - Limited by the quality of retrieved chunks
   - May miss information split across chunks
   - Context window limitations
   - Hallucination if no relevant context found

5. PRODUCTION CONSIDERATIONS:
   - Use proper vector databases (Pinecone, Weaviate, etc.)
   - Implement caching for embeddings
   - Add monitoring and logging
   - Handle rate limiting and errors gracefully
"""