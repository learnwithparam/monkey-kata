"""
Document QA Chatbot
===================

🎯 LEARNING OBJECTIVES:
This demo teaches you how to build a document Q&A system using RAG:

1. Document Parsing - How to extract text from PDFs, Word docs, and text files
2. Text Chunking - How to split documents into searchable pieces
3. Embeddings - How to convert text into vectors for similarity search
4. Vector Search - How to find relevant information in documents
5. RAG Pipeline - How to answer questions using document context

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Setup - Initialize providers and storage
Step 2: Data Models - Define request structures
Step 3: Background Processing - Parse and index documents
Step 4: Query Processing - Find relevant chunks and generate answers
Step 5: API Endpoints - Expose functionality via HTTP

Key Concept: Documents are too large to fit in LLM context windows.
RAG solves this by finding relevant sections and using only those.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, AsyncGenerator
import json
import uuid
import tempfile
import shutil
import os

from utils.llm_provider import get_llm_provider
from .document_utils import DocumentProcessor, RAGPipeline, DocumentChunk

# ============================================================================
# STEP 1: SETUP & INITIALIZATION
# ============================================================================
"""
Understanding Document RAG Components:
- LLM Provider: Generates answers (we know this from bedtime story demo)
- Document Processor: Parses PDFs, Word docs, text files
- RAG Pipeline: Finds relevant chunks and generates answers
- Embeddings: Converts text to searchable vectors

In-Memory Storage:
- document_data: Stores parsed documents and chunks
- document_embeddings: Stores vector embeddings for each document
- processing_status: Tracks document processing progress

Note: This uses in-memory storage for simplicity. In production,
you'd use a persistent vector database like Pinecone or Weaviate.
"""
router = APIRouter(prefix="/document-qa-chatbot", tags=["document-qa-chatbot"])

# Initialize providers
llm_provider = get_llm_provider()
document_processor = DocumentProcessor()
rag_pipeline = RAGPipeline(llm_provider)

# In-memory storage (use database in production)
document_data: Dict[str, Dict[str, Any]] = {}
document_embeddings: Dict[str, List[List[float]]] = {}
processing_status: Dict[str, Dict[str, Any]] = {}


# ============================================================================
# STEP 2: DATA MODELS
# ============================================================================
"""
Request Models:
- QuestionRequest: Specifies the question and which document to query
- ProcessingStatus: Shows the current state of document processing

These models ensure type safety and automatic validation.
"""
class QuestionRequest(BaseModel):
    """Request to ask a question about a document"""
    question: str
    document_id: str
    max_chunks: int = 5  # How many relevant chunks to retrieve


class ProcessingStatus(BaseModel):
    """Status of document processing"""
    document_id: str
    status: str  # "processing", "completed", "error"
    progress: int  # 0-100
    message: str
    pages_count: int = 0  # Frontend expects this field name
    error: Optional[str] = None


# ============================================================================
# STEP 3: BACKGROUND PROCESSING (Document Ingestion)
# ============================================================================
"""
The Document Ingestion Pipeline:
This processes uploaded documents and creates a searchable index:

1. Parse: Extract text from PDF, Word, or text files
2. Chunk: Split content into smaller, manageable pieces
3. Embed: Convert chunks into vector embeddings
4. Store: Save embeddings for similarity search

Why Background Processing?
- Document parsing can take time (especially PDFs)
- Embedding generation is CPU-intensive
- We don't want to block the API while processing
"""
async def process_document_background(
    document_id: str, 
    file_path: str, 
    chunk_size: int, 
    chunk_overlap: int
):
    """
    Background task to process a document through the RAG ingestion pipeline
    
    This runs asynchronously so the API can respond immediately while
    processing happens in the background.
    """
    try:
        # Step 1: Update status - starting
        processing_status[document_id] = {
            "document_id": document_id,
            "status": "processing",
            "progress": 10,
            "message": "Parsing document...",
            "pages_count": 0
        }
        
        # Step 2: Parse document (extract text from PDF/Word/text)
        document_content = await document_processor.parse_document(file_path)
        
        if not document_content:
            raise Exception("Failed to parse document")
        
        # Step 3: Update status - chunking
        processing_status[document_id].update({
            "progress": 40,
            "message": "Chunking content..."
        })
        
        # Step 4: Split content into chunks
        chunks = document_processor.chunk_document(
            document_content, 
            chunk_size, 
            chunk_overlap
        )
        
        # Step 5: Create document chunk objects with metadata
        documents = []
        for i, chunk_data in enumerate(chunks):
            doc = DocumentChunk(
                content=chunk_data['content'],
                document_id=document_id,
                chunk_index=i,
                page_number=chunk_data.get('page_number', 1),
                metadata={
                    "title": document_content.get("title", ""),
                    "document_id": document_id,
                    "chunk_size": len(chunk_data['content']),
                }
            )
            documents.append(doc)
        
        # Step 6: Update status - generating embeddings
        processing_status[document_id].update({
            "progress": 70,
            "message": "Generating embeddings..."
        })
        
        # Step 7: Generate embeddings for all chunks
        embeddings = await document_processor.generate_embeddings(
            [doc.content for doc in documents]
        )
        
        # Step 8: Store in memory (in production, use vector database)
        document_data[document_id] = {
            'documents': documents,
            'content': document_content,
            'file_path': file_path
        }
        document_embeddings[document_id] = embeddings
        
        # Step 9: Mark as completed
        # Use actual page count from document content, or estimate based on chunks
        actual_pages = document_content.get('pages', len(documents))
        processing_status[document_id].update({
            "status": "completed",
            "progress": 100,
            "message": f"Successfully processed document! Found {actual_pages} pages.",
            "pages_count": actual_pages
        })
        
        # Clean up temporary file
        try:
            os.remove(file_path)
        except:
            pass
        
    except Exception as e:
        # Handle errors gracefully
        processing_status[document_id] = {
            "document_id": document_id,
            "status": "error",
            "progress": 0,
            "message": "Processing failed",
            "error": str(e),
            "pages_count": 0
        }
        
        # Clean up temporary file
        try:
            os.remove(file_path)
        except:
            pass


# ============================================================================
# STEP 4: QUERY PROCESSING (RAG Pipeline)
# ============================================================================
"""
The Query Pipeline:
When a user asks a question about a document:

1. Embed Query: Convert the question into a vector
2. Similarity Search: Find document chunks most similar to the question
3. Build Context: Combine relevant chunks into prompt
4. Generate Answer: Use LLM to answer based on document context

Why This Works:
- We only send relevant document sections to the LLM
- The LLM has the exact information it needs to answer
- Much better than trying to send entire document content
"""
async def generate_document_rag_stream(request: QuestionRequest) -> AsyncGenerator[str, None]:
    """
    Generate RAG answer with streaming
    
    This is the complete RAG query pipeline:
    1. Check if document is processed
    2. Generate embedding for the question
    3. Find most relevant document chunks
    4. Generate answer using LLM with document context
    """
    document_id = request.document_id
    
    # Step 1: Verify document has been processed
    if document_id not in processing_status or processing_status[document_id]["status"] != "completed":
        yield f"data: {json.dumps({'error': f'Document not yet processed. Please wait for processing to complete.', 'status': 'error'})}\n\n"
        return
    
    if document_id not in document_data or document_id not in document_embeddings:
        yield f"data: {json.dumps({'error': 'No document data available', 'status': 'error'})}\n\n"
        return
    
    # Step 2: Get stored documents and embeddings
    documents = document_data[document_id]['documents']
    embeddings = document_embeddings[document_id]
    
    # Step 3: Notify frontend we're starting
    yield f"data: {json.dumps({'status': 'connected', 'message': 'Analyzing your question...'})}\n\n"
    
    # Step 4: Generate embedding for the question
    yield f"data: {json.dumps({'status': 'processing', 'message': 'Finding relevant content in document...'})}\n\n"
    query_embedding = await document_processor.generate_embeddings([request.question])
    
    # Step 5: Find most relevant chunks using similarity search
    relevant_chunks = rag_pipeline.retrieve_relevant_chunks(
        query_embedding[0],
        embeddings,
        documents,
        request.max_chunks
    )
    
    # Step 6: Send sources to frontend (for transparency)
    # Frontend expects 'content' field
    yield f"data: {json.dumps({'sources': [{'url': f'Page {chunk.page_number}', 'content': chunk.content[:300] + '...'} for chunk in relevant_chunks]})}\n\n"
    
    # Step 7: Generate streaming answer with document context
    yield f"data: {json.dumps({'status': 'generating', 'message': 'Generating answer...'})}\n\n"
    
    async for chunk in rag_pipeline.generate_answer_stream(request.question, relevant_chunks):
        yield f"data: {json.dumps({'content': chunk})}\n\n"
    
    # Step 8: Signal completion
    yield f"data: {json.dumps({'done': True, 'status': 'completed'})}\n\n"


# ============================================================================
# STEP 5: API ENDPOINTS
# ============================================================================
"""
API Endpoints:
- POST /upload-document: Upload and process a document (ingestion)
- GET /status/{document_id}: Check processing status
- POST /ask/stream: Ask a question about the document (query pipeline)
- POST /clear: Clear all data (for testing)
- GET /health: Health check
"""
@router.post("/upload-document")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    chunk_size: int = 500,
    chunk_overlap: int = 50
):
    """
    Upload a document for Q&A processing
    
    This endpoint:
    1. Accepts PDF, Word, or text files
    2. Saves file temporarily
    3. Starts background processing (parsing, chunking, embedding)
    4. Returns immediately with document_id
    
    The actual processing happens in the background, so this endpoint
    responds quickly while the document is being indexed.
    
    Supported file types:
    - PDF (.pdf)
    - Word (.doc, .docx)
    - Text (.txt)
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
    
    This is the main RAG query endpoint. It:
    1. Finds relevant document chunks using similarity search
    2. Generates an answer using the LLM with document context
    3. Streams the answer in real-time (like ChatGPT)
    
    Frontend Usage:
    Connect to this endpoint and listen for events:
    - Status updates: {"status": "processing", "message": "..."}
    - Sources: {"sources": [...]}
    - Content chunks: {"content": "..."}
    - Completion: {"done": true, "status": "completed"}
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


# ============================================================================
# LEARNING CHECKLIST
# ============================================================================
"""
After reading this code, you should understand:

✓ How to parse different document types (PDF, Word, text)
✓ How to chunk documents for optimal retrieval
✓ How embeddings enable semantic search across documents
✓ How similarity search finds relevant sections
✓ How to build a complete document Q&A pipeline

Key Document RAG Concepts:
- Ingestion: Upload → parse → chunk → embed → store
- Query: Question → embed → search → context → answer
- Why Document RAG: Documents are too large for LLM context windows

Next Steps:
1. Try different chunk sizes and see how it affects answers
2. Experiment with max_chunks parameter (how many chunks to retrieve)
3. Upload multiple documents and see cross-document retrieval
4. Try different document types (PDF vs Word vs text)
5. Implement a persistent vector database instead of in-memory storage

Questions to Consider:
- What happens if a document is very long (100+ pages)?
- How would you handle documents with tables or images?
- What if the document is in a different language?
- How would you improve the chunking strategy for legal/technical documents?
- What are the trade-offs between chunk size and retrieval quality?
"""