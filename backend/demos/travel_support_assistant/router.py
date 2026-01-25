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

@router.get("/tools")
async def get_tools():
    """Get available tools"""
    from .tools import AVAILABLE_TOOLS
    import inspect
    
    TOOL_EXAMPLES = {
        "lookup_booking": "What's the status of booking BK123456?",
        "search_hotels": "Find me a hotel in Paris with a pool.",
        "check_flight_status": "Is flight AA101 on time?",
        "search_policies": "What is the cancellation policy?",
        "book_hotel": "Book 3 nights at Grand Hotel Paris starting Feb 15th for John.",
        "book_taxi": "I need a taxi from the airport to Grand Hotel Paris.",
        "cancel_booking": "Cancel booking BK123456.",
        "convert_currency": "How much is 200 USD in EUR?"
    }

    tools_list = []
    for tool in AVAILABLE_TOOLS:
        description = inspect.getdoc(tool) or "No description available."
        tools_list.append({
            "name": tool.__name__,
            "description": description.split("\n")[0], # First line only for brevity
            "example": TOOL_EXAMPLES.get(tool.__name__)
        })
        
    return {"tools": tools_list}
