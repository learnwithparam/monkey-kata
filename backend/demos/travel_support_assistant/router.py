from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from .models import ChatRequest, SessionInfo
from .service import generate_chat_stream, agent_sessions
import uuid

router = APIRouter(prefix="/travel-support", tags=["travel-support"])

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    return StreamingResponse(
        generate_chat_stream(session_id, request.message),
        media_type="text/event-stream"
    )

@router.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    if session_id not in agent_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    s = agent_sessions[session_id]
    return SessionInfo(
        session_id=session_id,
        message_count=s["message_count"],
        tool_call_count=s["tool_call_count"],
        created_at=s["created_at"]
    )
