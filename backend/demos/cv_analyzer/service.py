from typing import Dict, Any, List, Optional
import logging
import os

from utils.llm_provider import get_llm_provider
from .cv_utils import CVDocumentProcessor
from .cv_agentic_analyzer import CVAnalyzer

logger = logging.getLogger(__name__)

# Initialize providers
llm_provider = get_llm_provider()
document_processor = CVDocumentProcessor()
cv_analyzer = CVAnalyzer(llm_provider)

# In-memory storage (use database in production)
document_data: Dict[str, Dict[str, Any]] = {}
document_embeddings: Dict[str, List[List[float]]] = {}
processing_status: Dict[str, Dict[str, Any]] = {}

async def process_cv_document(document_id: str, file_path: str, job_description: Optional[str]):
    """
    Background task to process a CV document through the ingestion pipeline
    """
    try:
        logger.info(f"Starting background processing for document: {document_id}")
        
        # Step 1: Update status - starting
        processing_status[document_id] = {
            "document_id": document_id,
            "status": "processing",
            "progress": 10,
            "message": "Parsing CV document...",
            "pages_count": 0
        }
        
        # Step 2: Parse document (extract text from PDF/Word/text)
        parsed_content = await document_processor.parse_document(file_path)
        
        if not parsed_content:
            raise Exception("Failed to parse CV document")
        
        # Step 3: Update status - processing
        processing_status[document_id].update({
            "progress": 50,
            "message": "Processing CV content..."
        })
        
        # Step 4: Chunk document (CV-specific section detection)
        chunks = document_processor.chunk_cv_document(parsed_content)
        
        # Step 5: Generate embeddings for all chunks
        chunk_texts = [chunk["content"] for chunk in chunks]
        embeddings = await document_processor.generate_embeddings(chunk_texts)
        
        # Step 6: Store document data
        document_data[document_id] = {
            "content": parsed_content["content"],
            "chunks": chunks,
            "job_description": job_description,
            "parsed_at": parsed_content["parsed_at"]
        }
        
        document_embeddings[document_id] = embeddings
        
        # Step 7: Mark as completed
        processing_status[document_id].update({
            "status": "completed",
            "progress": 100,
            "message": f"Processing completed successfully ({len(chunks)} chunks)",
            "pages_count": parsed_content["pages"]
        })
        
        logger.info(f"Processing completed for document: {document_id}")
        
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        processing_status[document_id] = {
            "document_id": document_id,
            "status": "error",
            "error": str(e),
            "message": "Processing failed",
            "progress": 0,
            "pages_count": 0
        }
    
    finally:
        # Clean up temporary file
        try:
            if os.path.exists(file_path):
                import shutil
                os.remove(file_path)
                os.rmdir(os.path.dirname(file_path))
        except Exception as e:
            logger.warning(f"Error cleaning up temp file: {e}")
