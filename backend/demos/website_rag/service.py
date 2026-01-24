from typing import List, Dict, Any, AsyncGenerator
import json
from datetime import datetime
import asyncio

from utils.llm_provider import get_llm_provider
from .rag_utils import SimpleRAGPipeline, WebScraper, EmbeddingProvider, DocumentChunk
from .models import QuestionRequest

# Initialize providers
llm_provider = get_llm_provider()
embedding_provider = EmbeddingProvider()
web_scraper = WebScraper()
rag_pipeline = SimpleRAGPipeline(llm_provider, embedding_provider)

# In-memory storage (use database in production)
url_documents: Dict[str, List[DocumentChunk]] = {}
url_embeddings: Dict[str, List[List[float]]] = {}
processing_status: Dict[str, Dict[str, Any]] = {}

async def process_url_background(url: str, chunk_size: int, chunk_overlap: int):
    """
    Background task to process a URL through the RAG ingestion pipeline
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
        url_str = str(url)
        processing_status[url_str] = {
            "url": url_str,
            "status": "error",
            "progress": 0,
            "message": "Processing failed",
            "error": str(e),
            "documents_count": 0
        }

async def generate_rag_stream(request: QuestionRequest) -> AsyncGenerator[str, None]:
    """
    Generate RAG answer with streaming
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
    
    # Thinking Step: Analysis
    thinking_analysis = {'thinking': {'category': 'analysis', 'content': f'Analyzing question: "{request.question}"', 'timestamp': datetime.now().isoformat()}}
    yield f"data: {json.dumps(thinking_analysis)}\n\n"
    
    # Step 4: Generate embedding for the question
    yield f"data: {json.dumps({'status': 'processing', 'message': 'Analyzing question...'})}\n\n"
    query_embedding = await embedding_provider.generate_embeddings([request.question])
    
    # Thinking Step: Planning
    yield f"data: {json.dumps({'thinking': {'category': 'planning', 'content': 'Searching vector database for relevant content chunks', 'timestamp': datetime.now().isoformat()}})}\n\n"
    
    # Step 5: Find most relevant chunks using similarity search
    yield f"data: {json.dumps({'status': 'processing', 'message': 'Finding relevant information...'})}\n\n"
    relevant_chunks = rag_pipeline.retrieve_relevant_chunks(
        query_embedding[0],
        embeddings,
        documents,
        request.max_chunks
    )
    
    # Thinking Step: Processing
    thinking_processing = {'thinking': {'category': 'processing', 'content': f'Found {len(relevant_chunks)} relevant content chunks. Synthesizing answer...', 'timestamp': datetime.now().isoformat()}}
    yield f"data: {json.dumps(thinking_processing)}\n\n"
    
    # Step 6: Send sources to frontend (for transparency)
    yield f"data: {json.dumps({'sources': [{'url': chunk.url, 'content': chunk.content[:300] + '...'} for chunk in relevant_chunks]})}\n\n"
    
    # Step 7: Generate streaming answer with context
    yield f"data: {json.dumps({'status': 'generating', 'message': 'Generating answer...'})}\n\n"
    
    try:
        async for chunk in rag_pipeline.generate_answer_stream(request.question, relevant_chunks):
            yield f"data: {json.dumps({'content': chunk})}\n\n"
    except (RuntimeError, StopIteration) as e:
        error_str = str(e).lower()
        if "stopiteration" in error_str or "async generator" in error_str:
            pass
        else:
            yield f"data: {json.dumps({'error': f'Error generating response: {str(e)}', 'status': 'error'})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': f'Error generating response: {str(e)}', 'status': 'error'})}\n\n"
    
    # Thinking Step: Complete
    yield f"data: {json.dumps({'thinking': {'category': 'complete', 'content': 'Final answer generated based on website content.', 'timestamp': datetime.now().isoformat()}})}\n\n"
    
    # Step 8: Signal completion
    yield f"data: {json.dumps({'done': True, 'status': 'completed'})}\n\n"
