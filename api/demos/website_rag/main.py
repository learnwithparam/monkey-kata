"""
Website RAG Chatbot
===================

🎯 LEARNING OBJECTIVES:
This demo teaches you how to build a RAG (Retrieval-Augmented Generation) system:

1. Web Scraping - How to extract content from websites
2. Text Chunking - How to split content into searchable pieces
3. Embeddings - How to convert text into vectors for similarity search
4. Vector Search - How to find relevant information
5. RAG Pipeline - How to combine retrieval with LLM generation

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Setup - Initialize providers and storage
Step 2: Data Models - Define request structures
Step 3: Background Processing - Scrape and index URLs
Step 4: Query Processing - Find relevant chunks and generate answers
Step 5: API Endpoints - Expose functionality via HTTP

Key Concept: RAG combines the power of search (finding relevant info) with
the power of LLMs (understanding and generating text).
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Any, Optional, AsyncGenerator
import json
import time

from utils.llm_provider import get_llm_provider
from .rag_utils import SimpleRAGPipeline, WebScraper, EmbeddingProvider, DocumentChunk

# ============================================================================
# STEP 1: SETUP & INITIALIZATION
# ============================================================================
"""
Understanding RAG Components:
- LLM Provider: Generates answers (we already know this)
- Embedding Provider: Converts text to vectors (numbers that represent meaning)
- Web Scraper: Extracts content from websites
- RAG Pipeline: Connects everything together

In-Memory Storage:
- url_documents: Stores the text chunks for each URL
- url_embeddings: Stores the vector embeddings for each URL
- processing_status: Tracks if a URL is being processed

Note: This uses in-memory storage for simplicity. In production,
you'd use a proper vector database like Pinecone, Weaviate, or ChromaDB.
"""
router = APIRouter(prefix="/website-rag", tags=["website-rag"])

# Initialize providers
llm_provider = get_llm_provider()
embedding_provider = EmbeddingProvider()
web_scraper = WebScraper()
rag_pipeline = SimpleRAGPipeline(llm_provider, embedding_provider)

# In-memory storage (use database in production)
url_documents: Dict[str, List[DocumentChunk]] = {}
url_embeddings: Dict[str, List[List[float]]] = {}
processing_status: Dict[str, Dict[str, Any]] = {}


# ============================================================================
# STEP 2: DATA MODELS
# ============================================================================
"""
Request Models:
- URLRequest: Specifies which URL to process and how to chunk it
- QuestionRequest: Specifies the question and which URL to query
- ProcessingStatus: Shows the current state of URL processing

These models ensure type safety and automatic validation.
"""
class URLRequest(BaseModel):
    """Request to add and process a URL"""
    url: HttpUrl
    chunk_size: int = 500  # Characters per chunk
    chunk_overlap: int = 50  # Overlap between chunks (helps preserve context)


class QuestionRequest(BaseModel):
    """Request to ask a question about a URL's content"""
    question: str
    url: HttpUrl
    max_chunks: int = 5  # How many relevant chunks to retrieve


class ProcessingStatus(BaseModel):
    """Status of URL processing"""
    url: str
    status: str  # "processing", "completed", "error"
    progress: int  # 0-100
    message: str
    documents_count: int = 0
    error: Optional[str] = None


# ============================================================================
# STEP 3: BACKGROUND PROCESSING (Ingestion Pipeline)
# ============================================================================
"""
The Ingestion Pipeline:
This is the "R" (Retrieval) part of RAG. It processes URLs and creates
a searchable index:

1. Scrape: Extract text content from the website
2. Chunk: Split content into smaller, manageable pieces
3. Embed: Convert chunks into vector embeddings
4. Store: Save embeddings for similarity search

Why Background Processing?
- Web scraping can take time
- Embedding generation is CPU-intensive
- We don't want to block the API while processing
"""
async def process_url_background(url: str, chunk_size: int, chunk_overlap: int):
    """
    Background task to process a URL through the RAG ingestion pipeline
    
    This runs asynchronously so the API can respond immediately while
    processing happens in the background.
    """
    try:
        url_str = str(url)
        
        # Step 1: Update status - starting
        processing_status[url_str] = {
            "url": url_str,
            "status": "processing",
            "progress": 10,
            "message": "Scraping website content...",
            "documents_count": 0
        }
        
        # Step 2: Scrape content from URL
        content_data = await web_scraper.scrape_url(url_str)
        
        if not content_data:
            raise Exception("Failed to extract content from URL")
        
        # Step 3: Update status - chunking
        processing_status[url_str].update({
            "progress": 40,
            "message": "Chunking content..."
        })
        
        # Step 4: Split content into chunks
        chunks = web_scraper.chunk_content(content_data, chunk_size, chunk_overlap)
        
        # Step 5: Create document objects with metadata
        documents = []
        for i, chunk_text in enumerate(chunks):
            doc = DocumentChunk(
                content=chunk_text,
                url=url_str,
                chunk_index=i,
                metadata={
                    "title": content_data.get("title", ""),
                    "url": url_str,
                    "chunk_size": len(chunk_text),
                }
            )
            documents.append(doc)
        
        # Step 6: Update status - generating embeddings
        processing_status[url_str].update({
            "progress": 70,
            "message": "Generating embeddings..."
        })
        
        # Step 7: Generate embeddings for all chunks
        embeddings = await embedding_provider.generate_embeddings(
            [doc.content for doc in documents]
        )
        
        # Step 8: Store in memory (in production, use vector database)
        url_documents[url_str] = documents
        url_embeddings[url_str] = embeddings
        
        # Step 9: Mark as completed
        processing_status[url_str].update({
            "status": "completed",
            "progress": 100,
            "message": "Processing completed successfully",
            "documents_count": len(documents)
        })
        
    except Exception as e:
        # Handle errors gracefully
        processing_status[url_str] = {
            "url": url_str,
            "status": "error",
            "progress": 0,
            "message": "Processing failed",
            "error": str(e),
            "documents_count": 0
        }


# ============================================================================
# STEP 4: QUERY PROCESSING (RAG Pipeline)
# ============================================================================
"""
The Query Pipeline:
This is where RAG magic happens. When a user asks a question:

1. Embed Query: Convert the question into a vector
2. Similarity Search: Find chunks most similar to the question
3. Build Context: Combine relevant chunks into prompt
4. Generate Answer: Use LLM to answer based on context

Why This Works:
- We only send relevant context to the LLM (saves tokens, improves accuracy)
- The LLM has the exact information it needs to answer
- Much better than trying to send entire website content
"""
async def generate_rag_stream(request: QuestionRequest) -> AsyncGenerator[str, None]:
    """
    Generate RAG answer with streaming
    
    This is the complete RAG query pipeline:
    1. Check if URL is processed
    2. Generate embedding for the question
    3. Find most relevant chunks
    4. Generate answer using LLM with context
    """
    url_str = str(request.url)
    
    # Step 1: Verify URL has been processed
    if url_str not in processing_status or processing_status[url_str]["status"] != "completed":
        yield f"data: {json.dumps({'error': f'URL not yet processed. Please wait for processing to complete.', 'status': 'error'})}\n\n"
        return
    
    if url_str not in url_documents or url_str not in url_embeddings:
        yield f"data: {json.dumps({'error': 'No documents available for this URL', 'status': 'error'})}\n\n"
        return
    
    # Step 2: Get stored documents and embeddings
    documents = url_documents[url_str]
    embeddings = url_embeddings[url_str]
    
    # Step 3: Notify frontend we're starting
    yield f"data: {json.dumps({'status': 'connected', 'message': 'Processing your question...'})}\n\n"
    
    # Step 4: Generate embedding for the question
    yield f"data: {json.dumps({'status': 'processing', 'message': 'Analyzing question...'})}\n\n"
    query_embedding = await embedding_provider.generate_embeddings([request.question])
    
    # Step 5: Find most relevant chunks using similarity search
    yield f"data: {json.dumps({'status': 'processing', 'message': 'Finding relevant information...'})}\n\n"
    relevant_chunks = rag_pipeline.retrieve_relevant_chunks(
        query_embedding[0],
        embeddings,
        documents,
        request.max_chunks
    )
    
    # Step 6: Send sources to frontend (for transparency)
    # Frontend expects 'content' field, not 'preview'
    yield f"data: {json.dumps({'sources': [{'url': chunk.url, 'content': chunk.content[:300] + '...'} for chunk in relevant_chunks]})}\n\n"
    
    # Step 7: Generate streaming answer with context
    yield f"data: {json.dumps({'status': 'generating', 'message': 'Generating answer...'})}\n\n"
    
    try:
        async for chunk in rag_pipeline.generate_answer_stream(request.question, relevant_chunks):
            yield f"data: {json.dumps({'content': chunk})}\n\n"
    except (RuntimeError, StopIteration) as e:
        # StopIteration and some RuntimeErrors indicate normal completion
        # (some async frameworks convert StopIteration to RuntimeError)
        error_str = str(e).lower()
        if "stopiteration" in error_str or "async generator" in error_str:
            # Generator finished normally - this is expected, not an error
            pass
        else:
            # Other RuntimeError - send error message
            yield f"data: {json.dumps({'error': f'Error generating response: {str(e)}', 'status': 'error'})}\n\n"
    except Exception as e:
        # Handle any other errors gracefully
        yield f"data: {json.dumps({'error': f'Error generating response: {str(e)}', 'status': 'error'})}\n\n"
    
    # Step 8: Signal completion
    yield f"data: {json.dumps({'done': True, 'status': 'completed'})}\n\n"


# ============================================================================
# STEP 5: API ENDPOINTS
# ============================================================================
"""
API Endpoints:
- POST /add-url: Start processing a URL (ingestion)
- GET /status/{url}: Check processing status
- POST /ask/stream: Ask a question (query pipeline)
- POST /clear: Clear all data (for testing)
- GET /health: Health check
"""
@router.post("/add-url")
async def add_url(request: URLRequest, background_tasks: BackgroundTasks):
    """
    Add a URL to process for RAG
    
    This endpoint:
    1. Accepts a URL and chunking parameters
    2. Starts background processing (scraping, chunking, embedding)
    3. Returns immediately with a status message
    
    The actual processing happens in the background, so this endpoint
    responds quickly while the URL is being indexed.
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
    
    This is the main RAG query endpoint. It:
    1. Finds relevant chunks using similarity search
    2. Generates an answer using the LLM with context
    3. Streams the answer in real-time (like ChatGPT)
    
    Frontend Usage:
    Connect to this endpoint and listen for events:
    - Status updates: {"status": "processing", "message": "..."}
    - Sources: {"sources": [...]}
    - Content chunks: {"content": "..."}
    - Completion: {"done": true, "status": "completed"}
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
    url_documents.clear()
    url_embeddings.clear()
    processing_status.clear()
    return {"message": "All sessions cleared"}


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "website-rag",
        "urls_processed": len(url_documents),
        "total_documents": sum(len(docs) for docs in url_documents.values())
    }


# ============================================================================
# LEARNING CHECKLIST
# ============================================================================
"""
After reading this code, you should understand:

✓ How RAG combines retrieval (search) with generation (LLM)
✓ How to scrape and clean website content
✓ How to chunk text for optimal retrieval
✓ How embeddings enable semantic search
✓ How similarity search finds relevant information
✓ How to build a complete RAG pipeline

Key RAG Concepts:
- Ingestion: Process content → chunks → embeddings → store
- Query: Question → embedding → search → context → answer
- Why RAG: Avoids context window limits, improves accuracy, provides sources

Next Steps:
1. Try different chunk sizes and see how it affects answers
2. Experiment with max_chunks parameter (how many chunks to retrieve)
3. Add multiple URLs and see how it finds relevant info across sources
4. Try different embedding models and compare results
5. Implement a persistent vector database instead of in-memory storage

Questions to Consider:
- What happens if the website content changes?
- How would you handle conflicting information from different sources?
- What if no relevant chunks are found for a question?
- How would you improve the chunking strategy?
- What are the trade-offs between chunk size and retrieval quality?
"""