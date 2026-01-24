from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import json
from utils.llm_provider import LLMProvider

logger = logging.getLogger(__name__)

class InvoiceItem(BaseModel):
    """Structured data for a single item in an invoice"""
    description: str = Field(description="Description of the product or service")
    quantity: Optional[float] = Field(None, description="Quantity of the item")
    unit_price: Optional[float] = Field(None, description="Price per unit")
    amount: float = Field(description="Total amount for this line item")

class InvoiceData(BaseModel):
    """Structured data extracted from an invoice"""
    is_invoice: bool = Field(description="Whether the document is actually an invoice")
    vendor_name: Optional[str] = Field(None, description="Name of the company providing the invoice")
    invoice_number: Optional[str] = Field(None, description="The unique identifier for the invoice")
    invoice_date: Optional[str] = Field(None, description="Date the invoice was issued")
    due_date: Optional[str] = Field(None, description="Date the payment is due")
    items: List[InvoiceItem] = Field(default_factory=list, description="List of items or services billed")
    subtotal: Optional[float] = Field(None, description="Total before taxes")
    tax_amount: Optional[float] = Field(None, description="Amount of tax applied")
    total_amount: Optional[float] = Field(None, description="The final total amount due")
    currency: Optional[str] = Field("USD", description="Currency of the invoice (e.g., USD, EUR, GBP)")

class InvoiceAnalyzer:
    """Multi-modal analysis for parsing invoices"""
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider

    async def analyze_invoice(self, base64_image: str, mime_type: str) -> InvoiceData:
        """
        Analyze an invoice image/PDF and extract structured data.
        
        Args:
            base64_image: Base64 encoded file content
            mime_type: Mime type of the file
            
        Returns:
            Structured InvoiceData object
        """
        prompt = """
        You are an expert invoice processing agent. Your task is to extract structured data from the provided document.
        
        1. First, determine if this document is an invoice, a receipt, or a similar billing document.
        2. If it IS an invoice, extract all relevant fields accurately.
        3. If it IS NOT an invoice, set `is_invoice` to false and return empty values for other fields.
        
        Extract the following fields in JSON format:
        - is_invoice: boolean
        - vendor_name: string
        - invoice_number: string
        - invoice_date: string (YYYY-MM-DD format if possible)
        - due_date: string (YYYY-MM-DD format if possible)
        - items: list of objects with (description, quantity, unit_price, amount)
        - subtotal: number
        - tax_amount: number
        - total_amount: number
        - currency: string (3-letter code, default USD)
        
        Return ONLY the JSON object.
        """
        
        # Check if we need to convert PDF to image
        # OpenAI-compatible providers (Fireworks, OpenRouter) typically don't support PDF inputs in image_url
        # Google Gemini supports PDFs natively
        
        provider_name = getattr(self.llm_provider, "provider_name", "")
        # If it's a PDF and NOT Gemini, reject it
        if mime_type == "application/pdf" and "gemini" not in provider_name.lower():
            logger.warning(f"PDF input is not supported for provider '{provider_name}'. Please use an image (PNG/JPG).")
            # Return a valid Empty InvoiceData to prevent frontend crashing
            return InvoiceData(
                is_invoice=False, 
                vendor_name="Error: PDF not supported with this provider. Please use an image."
            )

        # Build multimodal content for litellm
        content = [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{base64_image}"
                }
            }
        ]
        
        # Using the llm_provider directly for multimodal completion
        response_text = await self.llm_provider.generate_text(content)
        
        # Clean up response text if it contains markdown code blocks
        clean_json = response_text.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json.replace("```json", "", 1)
        if clean_json.endswith("```"):
            clean_json = clean_json.rsplit("```", 1)[0]
        clean_json = clean_json.strip()
        
        data = json.loads(clean_json)
        return InvoiceData(**data)
            

def get_invoice_analyzer(llm_provider: LLMProvider):
    return InvoiceAnalyzer(llm_provider)
