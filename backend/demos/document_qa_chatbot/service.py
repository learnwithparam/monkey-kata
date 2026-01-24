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

# In-memory storage for STATUS only
# Data is now in Qdrant
processing_status: Dict[str, Dict[str, Any]] = {}

async def process_document_background(
    document_id: str, 
    file_path: str, 
    chunk_size: int, 
    chunk_overlap: int
):
    """
    Background task to process a document: Parse -> Chunk -> Embed -> Store in Qdrant
    """
    try:
        # Step 1: Update status - starting
        processing_status[document_id] = {
            "document_id": document_id,
            "status": "processing",
            "progress": 10,
            "message": "Parsing document with Docling...",
            "pages_count": 0
        }
        
        # Step 2: Parse document (extract text from PDF/Word/text)
        document_content = await document_processor.parse_document(file_path)
        
        if not document_content:
            raise Exception("Failed to parse document")
        
        # Step 3: Update status - chunking
        processing_status[document_id].update({
            "progress": 30,
            "message": "Semantic chunking..."
        })
        
        # Step 4: Split content into chunks
        chunks_data = document_processor.chunk_document(
            document_content, 
            chunk_size, 
            chunk_overlap
        )
        
        # Step 5: Generate embeddings (Dense 384-dim)
        processing_status[document_id].update({
            "progress": 50,
            "message": "Generating embeddings (all-MiniLM-L6-v2)..."
        })
        
        # Extract content list for batch embedding
        texts = [chunk['content'] for chunk in chunks_data]
        embeddings_list = await document_processor.generate_embeddings(texts)
        
        # Step 6: Create DocumentChunk objects
        documents = []
        for i, chunk_data in enumerate(chunks_data):
            doc = DocumentChunk(
                content=chunk_data['content'],
                document_id=document_id,
                chunk_index=i,
                page_number=chunk_data.get('page_number', 1),
                metadata={
                    "title": document_content.get("title", ""),
                    "document_id": document_id,
                    "chunk_size": len(chunk_data['content']),
                },
                # Attach vectors for upsert
                vector=embeddings_list[i]
            )
            documents.append(doc)
        
        # Step 7: Store in Qdrant
        processing_status[document_id].update({
            "progress": 90,
            "message": "Indexing in Qdrant Vector Database..."
        })
        
        rag_pipeline.upsert_documents(document_id, documents)
        
        # Step 8: Mark as completed
        actual_pages = document_content.get('pages', 1)
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
        import traceback
        traceback.print_exc()
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
    
    # Step 3: Notify frontend we're starting
    yield f"data: {json.dumps({'status': 'connected', 'message': 'Analyzing your question...'})}\n\n"
    
    # Step 4: Generate embedding for the question
    yield f"data: {json.dumps({'status': 'processing', 'message': 'Finding relevant content in document...'})}\n\n"
    
    await thinking_streamer.emit_thinking("reasoning", "Converting question to vector (all-MiniLM)...")
    
    # We use generate_embeddings which returns a list, so we take [0]
    query_embedding_task = asyncio.create_task(document_processor.generate_embeddings([request.question]))
    
    # Concurrent wait for embedding and thinking events
    while not query_embedding_task.done():
        while not step_queue.empty():
            step = step_queue.get_nowait()
            yield f"data: {json.dumps({'thinking': step.__dict__})}\n\n"
        await asyncio.sleep(0.1)
        
    query_vectors_list = await query_embedding_task
    query_vectors = query_vectors_list[0]
    
    # Step 5: Find most relevant chunks using Qdrant Dense Search + Reranking
    await thinking_streamer.emit_thinking("reasoning", "Performing Dense Search + Cross-Encoder Reranking...")
    relevant_chunks = rag_pipeline.retrieve_relevant_chunks(
        query_text=request.question,
        query_vector=query_vectors,
        document_id=document_id,
        max_chunks=request.max_chunks,
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
