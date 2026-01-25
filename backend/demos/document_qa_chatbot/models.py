from pydantic import BaseModel
from typing import Optional

class QuestionRequest(BaseModel):
    """Request to ask a question about a document"""
    question: str
    document_id: str
    max_chunks: int = 5  # How many relevant chunks to retrieve
    use_hybrid: bool = True # Use hybrid retrieval (Dense + Sparse)


class ProcessingStatus(BaseModel):
    """Status of document processing"""
    document_id: str
    status: str  # "processing", "completed", "error"
    progress: int  # 0-100
    message: str
    pages_count: int = 0  # Frontend expects this field name
    error: Optional[str] = None
