from fastapi import APIRouter, HTTPException, UploadFile, File
import os
import tempfile
import logging
import uuid
from typing import Optional, List, Dict, Any
from .invoice_analyzer import InvoiceData, get_invoice_analyzer
from .invoice_utils import get_invoice_utils
from utils.llm_provider import get_llm_provider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/invoice-parser", tags=["invoice-parser"])

# Initialize components
# Use specific vision model if configured, otherwise default to provider's model
vision_model = os.getenv("VISION_MODEL")
if vision_model:
    logger.info(f"Using specific vision model: {vision_model}")

llm_provider = get_llm_provider(model=vision_model)
invoice_analyzer = get_invoice_analyzer(llm_provider)
invoice_utils = get_invoice_utils()

@router.get("/health")
async def health_check():
    """Health check for the invoice parser service"""
    return {"status": "healthy", "service": "invoice-parser"}

@router.post("/upload", response_model=InvoiceData)
async def upload_invoice(file: UploadFile = File(...)):
    """
    Upload and parse an invoice image or PDF.
    
    This endpoint:
    1. Validates the file type
    2. Saves the file temporarily
    3. Converts it to base64
    4. Uses multimodal LLM to extract structured data
    """
    temp_file_path = None
    try:
        # Validate file type
        allowed_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.webp'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
            
        # Create temp file
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, f"{uuid.uuid4()}{file_extension}")
        
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            
        # Get mime type and base64
        mime_type = invoice_utils.get_mime_type(temp_file_path)
        base64_content = invoice_utils.encode_image_to_base64(temp_file_path)
        
        if not base64_content:
            raise HTTPException(status_code=500, detail="Failed to process image content")
            
        # Analyze with multimodal LLM
        result = await invoice_analyzer.analyze_invoice(base64_content, mime_type)
        
        logger.info(f"Invoice parsed successfully: {file.filename}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing invoice: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error parsing invoice: {str(e)}")
        
    finally:
        # Clean up temp file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                os.rmdir(os.path.dirname(temp_file_path))
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file: {e}")

@router.get("/learning-objectives")
async def get_learning_objectives():
    """Get learning objectives for this demo"""
    return {
        "demo": "Invoice Parser",
        "objectives": [
            "Use multimodal LLMs (vision) to extract text and structure from images",
            "Define strict Pydantic schemas for consistent structured output",
            "Handle different file types (images, PDFs) in an AI pipeline",
            "Implement fallback logic for non-matching documents"
        ],
        "technologies": ["Multimodal AI", "Pydantic", "FastAPI", "Image Processing"],
        "concepts": ["Multimodal RAG", "Structured Extraction", "Visual Document Analysis"]
    }
