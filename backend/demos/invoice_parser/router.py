from fastapi import APIRouter, HTTPException, UploadFile, File
import os
import uuid
import logging
import tempfile

from .invoice_analyzer import InvoiceData, get_invoice_analyzer
from .invoice_utils import get_invoice_utils
from utils.llm_provider import get_llm_provider

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/invoice-parser", tags=["invoice-parser"])

vision_model = os.getenv("VISION_MODEL")
llm_provider = get_llm_provider(model=vision_model)
invoice_analyzer = get_invoice_analyzer(llm_provider)
invoice_utils = get_invoice_utils()

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "invoice-parser"}

@router.post("/upload", response_model=InvoiceData)
async def upload_invoice(file: UploadFile = File(...)):
    temp_file_path = None
    try:
        allowed_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.webp'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail="Unsupported file type")
            
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, f"{uuid.uuid4()}{file_extension}")
        with open(temp_file_path, "wb") as f: f.write(await file.read())
            
        mime_type = invoice_utils.get_mime_type(temp_file_path)
        base64_content = invoice_utils.encode_image_to_base64(temp_file_path)
        
        result = await invoice_analyzer.analyze_invoice(base64_content, mime_type)
        return result
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            os.rmdir(os.path.dirname(temp_file_path))

@router.get("/learning-objectives")
async def get_learning_objectives():
    return {
        "demo": "Invoice Parser",
        "objectives": ["Vision LLM extraction", "Structured output", "File handling"],
        "technologies": ["Multimodal AI", "Pydantic", "FastAPI"]
    }
