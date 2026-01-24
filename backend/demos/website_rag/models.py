from pydantic import BaseModel, HttpUrl
from typing import Optional

"""
Request Models:
- URLRequest: Specifies which URL to process and how to chunk it
- QuestionRequest: Specifies the question and which URL to query
- ProcessingStatus: Shows the current state of URL processing

These models ensure type safety and automatic validation.
"""

class URLRequest(BaseModel):
    """Request to add and process a URL"""
    url: HttpUrl
    chunk_size: int = 500  # Characters per chunk
    chunk_overlap: int = 50  # Overlap between chunks (helps preserve context)


class QuestionRequest(BaseModel):
    """Request to ask a question about a URL's content"""
    question: str
    url: HttpUrl
    max_chunks: int = 5  # How many relevant chunks to retrieve


class ProcessingStatus(BaseModel):
    """Status of URL processing"""
    url: str
    status: str  # "processing", "completed", "error"
    progress: int  # 0-100
    message: str
    documents_count: int = 0
    error: Optional[str] = None
