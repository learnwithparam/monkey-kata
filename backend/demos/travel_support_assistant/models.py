from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    """Request to chat with the travel support assistant"""
    message: str = Field(..., min_length=1, description="The user's message or question")
    session_id: Optional[str] = Field(None, description="Optional session ID for conversation continuity")


class ToolCall(BaseModel):
    """Information about a tool call"""
    tool_name: str
    arguments: Dict[str, Any]
    result: str
    timestamp: str


class ChatResponse(BaseModel):
    """Travel support assistant response with tool usage information"""
    response: str
    session_id: str
    tool_calls: List[ToolCall] = []


class SessionInfo(BaseModel):
    """Session information"""
    session_id: str
    message_count: int
    tool_call_count: int
    created_at: str
