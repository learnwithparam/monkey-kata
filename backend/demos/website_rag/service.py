from typing import List, Dict, Any, AsyncGenerator
import json
from datetime import datetime
import asyncio
import logging

from utils.llm_provider import get_llm_provider
from .rag_utils import SimpleRAGPipeline, WebScraper, EmbeddingProvider, DocumentChunk, VectorStore
from .models import QuestionRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize providers
llm_provider = get_llm_provider()
embedding_provider = EmbeddingProvider()
web_scraper = WebScraper()
vector_store = VectorStore() # Persistent ChromaDB
rag_pipeline = SimpleRAGPipeline(llm_provider, embedding_provider, vector_store)

# In-memory status tracking (operations are now persisted in ChromaDB, but status is ephemeral)
# In a real production app, this should also be in a DB (e.g. Redis/Postgres)
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
            "message": "Chunking content with LangChain..."
        })
        
        # Step 4: Split content into chunks
        # Note: chunk_size overrides the default in the scraper
        chunks = web_scraper.chunk_content(content_data, chunk_size, chunk_overlap)
        
        if not chunks:
             raise Exception("No content chunks created")

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
                    "scraped_at": content_data.get("scraped_at", "")
                }
            )
            documents.append(doc)
        
        # Step 6: Update status - generating embeddings
        processing_status[url_str].update({
            "progress": 60,
            "message": "Generating embeddings & Indexing..."
        })
        
        # Step 7: Generate embeddings for all chunks
        embeddings = await embedding_provider.generate_embeddings(
            [doc.content for doc in documents]
        )
        
        # Step 8: Store in Vector Database (ChromaDB)
        vector_store.add_documents(documents, embeddings)
        
        # Step 9: Mark as completed
        processing_status[url_str].update({
            "status": "completed",
            "progress": 100,
            "message": "Processing completed successfully",
            "documents_count": len(documents)
        })
        
    except Exception as e:
        logger.error(f"Processing failed for {url}: {e}")
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
    
    # Step 1: Verify URL has been processed (simplified check using status dict)
    # Ideally check DB, but for demo UI feedback this is fine
    if url_str not in processing_status or processing_status[url_str]["status"] != "completed":
        # Allow if it's already in vector store (persistence check)
        # For now, we rely on the UI flow which calls process first.
        # In a real app, we would query the vector store to see if this URL exists.
        pass 
    
    # Step 3: Notify frontend we're starting
    yield f"data: {json.dumps({'status': 'connected', 'message': 'Processing your question...'})}\n\n"
    
    # Thinking Step: Analysis
    thinking_analysis = {'thinking': {'category': 'analysis', 'content': f'Analyzing question: "{request.question}"', 'timestamp': datetime.now().isoformat()}}
    yield f"data: {json.dumps(thinking_analysis)}\n\n"
    
    # Thinking Step: Planning
    yield f"data: {json.dumps({'thinking': {'category': 'planning', 'content': 'Querying ChromaDB vector store', 'timestamp': datetime.now().isoformat()}})}\n\n"
    
    # Step 5: Retrieval
    yield f"data: {json.dumps({'status': 'processing', 'message': 'Finding relevant information...'})}\n\n"
    
    # Retrieve relevant chunks (includes embedding + similarity search + reranking)
    # We filter by URL to ensure we only answer based on the requested site
    # (Though in a multi-site RAG we might want to search everything)
    
    try:
        relevant_chunks = await rag_pipeline.retrieve(
            query=request.question,
            filters={"url": url_str} 
        )
    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        yield f"data: {json.dumps({'error': f'Error retrieving documents: {str(e)}', 'status': 'error'})}\n\n"
        return

    # Thinking Step: Re-ranking
    thinking_rerank = {'thinking': {'category': 'processing', 'content': f'Re-ranking top candidates with Cross-Encoder for better accuracy. Found {len(relevant_chunks)} best matches.', 'timestamp': datetime.now().isoformat()}}
    yield f"data: {json.dumps(thinking_rerank)}\n\n"
    
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
