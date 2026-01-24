import base64
import os
import logging
from typing import Optional, Dict, Any
import mimetypes

logger = logging.getLogger(__name__)

class InvoiceUtils:
    """Utilities for processing invoice files (images and PDFs)"""
    
    @staticmethod
    def encode_image_to_base64(file_path: str) -> Optional[str]:
        """Convert an image or PDF file to base64 string."""
        try:
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return None
                
            with open(file_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image to base64: {e}")
            return None

    @staticmethod
    def get_mime_type(file_path: str) -> str:
        """Get the mime type of a file."""
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or "application/octet-stream"


def get_invoice_utils():
    return InvoiceUtils()
