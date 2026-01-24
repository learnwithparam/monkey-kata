from typing import List, Dict, Any, AsyncGenerator
import json
import asyncio
import os

from utils.llm_provider import get_llm_provider
from utils.thinking_streamer import ThinkingStreamer
from .document_utils import DocumentProcessor, RAGPipeline, DocumentChunk
from .models import QuestionRequest

# Initialize providers
llm_provider = get_llm_provider()
document_processor = DocumentProcessor()
rag_pipeline = RAGPipeline(llm_provider)

# In-memory storage (use database in production)
document_data: Dict[str, Dict[str, Any]] = {}
document_embeddings: Dict[str, List[List[float]]] = {}
processing_status: Dict[str, Dict[str, Any]] = {}

async def process_document_background(
    document_id: str, 
    file_path: str, 
    chunk_size: int, 
    chunk_overlap: int
):
    """
    Background task to process a document through the RAG ingestion pipeline
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

async def generate_document_rag_stream(request: QuestionRequest) -> AsyncGenerator[str, None]:
    """
    Generate RAG answer with streaming
    """
    document_id = request.document_id
    
    # Initialize thinking streamer
    thinking_streamer = ThinkingStreamer()
    step_queue = asyncio.Queue()
    
    # Add callback to thinking streamer to push events into our local queue
    def on_thinking_event(event):
        step_queue.put_nowait(event)
    
    thinking_streamer.add_callback(on_thinking_event)
    
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
    
    await thinking_streamer.emit_thinking("reasoning", "Converting your question into a vector embedding...")
    query_embedding_task = asyncio.create_task(document_processor.generate_embeddings([request.question]))
    
    # Concurrent wait for embedding and thinking events
    while not query_embedding_task.done():
        while not step_queue.empty():
            step = step_queue.get_nowait()
            yield f"data: {json.dumps({'thinking': step.__dict__})}\n\n"
        await asyncio.sleep(0.1)
        
    query_embedding = await query_embedding_task
    
    # Step 5: Find most relevant chunks using similarity search
    await thinking_streamer.emit_thinking("reasoning", "Searching for the most relevant document sections...")
    relevant_chunks = rag_pipeline.retrieve_relevant_chunks(
        query_embedding[0],
        embeddings,
        documents,
        request.max_chunks,
        thinking_streamer=thinking_streamer
    )
    
    # Drain remaining thinking events from the queue
    while not step_queue.empty():
        step = step_queue.get_nowait()
        yield f"data: {json.dumps({'thinking': step.__dict__})}\n\n"
    
    # Step 6: Send sources to frontend (for transparency)
    yield f"data: {json.dumps({'sources': [{'url': f'Page {chunk.page_number}', 'content': chunk.content[:300] + '...'} for chunk in relevant_chunks]})}\n\n"
    
    # Step 7: Generate streaming answer with document context
    yield f"data: {json.dumps({'status': 'generating', 'message': 'Generating answer...'})}\n\n"
    
    try:
        async for chunk in rag_pipeline.generate_answer_stream(request.question, relevant_chunks, thinking_streamer=thinking_streamer):
            # Drain thinking events before yielding content
            while not step_queue.empty():
                step = step_queue.get_nowait()
                yield f"data: {json.dumps({'thinking': step.__dict__})}\n\n"
            yield f"data: {json.dumps({'content': chunk})}\n\n"
    except (RuntimeError, StopIteration) as e:
        error_str = str(e).lower()
        if "stopiteration" in error_str or "async generator" in error_str:
            pass
        else:
            yield f"data: {json.dumps({'error': f'Error generating response: {str(e)}', 'status': 'error'})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': f'Error generating response: {str(e)}', 'status': 'error'})}\n\n"
    
    # Step 8: Signal completion
    yield f"data: {json.dumps({'done': True, 'status': 'completed'})}\n\n"
