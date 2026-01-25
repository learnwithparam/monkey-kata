from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from utils.llm_provider import get_provider_config
from .models import StoryRequest
from .service import generate_story_stream

# Create a router - groups all endpoints under /bedtime-story
router = APIRouter(prefix="/bedtime-story", tags=["bedtime-story"])

"""
What is an API Endpoint?
- A URL that clients can call to access functionality
- Each endpoint does one specific thing
- Uses HTTP methods (GET, POST, etc.) to indicate the action

Endpoint Design Principles:
1. Clear naming (/stream, /themes, /health)
2. Single responsibility (each endpoint does one thing)
3. Proper HTTP methods (POST for creating, GET for reading)
4. Meaningful responses (status codes, clear data)

Understanding the Code Flow:
POST /bedtime-story/stream
  → Validates request (automatic via Pydantic)
  → Calls generate_story_stream()
  → Returns StreamingResponse that sends data in real-time
  → Frontend receives chunks and displays them
"""
@router.post("/stream")
async def stream_story(request: StoryRequest):
    """
    Main endpoint: Generates and streams a bedtime story
    
    This endpoint:
    1. Receives story parameters (character name, age, theme, length)
    2. Validates the data automatically (via Pydantic model)
    3. Streams the generated story in real-time
    4. Returns a StreamingResponse for Server-Sent Events
    
    Frontend Usage:
    The frontend connects to this endpoint and listens for events:
    - First event: {"status": "connected", "message": "..."}
    - Following events: {"content": "Once upon a time..."}
    - Final event: {"done": true, "status": "completed"}
    """
    return StreamingResponse(
        generate_story_stream(request),
        media_type="text/event-stream",  # Standard SSE format
        headers={
            "Cache-Control": "no-cache",  # Prevent caching
            "Connection": "keep-alive",    # Keep connection open
        }
    )


@router.get("/themes")
async def get_story_themes():
    """
    Returns available story themes
    
    This is a simple utility endpoint that provides the frontend
    with a list of themes users can choose from.
    """
    return {
        "themes": [
            "adventure",
            "friendship",
            "courage",
            "kindness",
            "imagination",
            "family",
            "animals",
            "magic",
            "space",
            "underwater",
            "forest",
            "castle"
        ]
    }


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Useful for:
    - Monitoring system status
    - Load balancer checks
    - Debugging connection issues
    
    Returns a simple status to confirm the API is running.
    """
    return {
        "status": "healthy",
        "service": "bedtime-story-generator"
    }


@router.get("/provider-info")
async def get_provider_info():
    """
    Get current LLM provider information
    
    Returns the provider name so frontend can show appropriate warnings.
    """
    try:
        config = get_provider_config()
        return {
            "provider_name": config["provider_name"],
            "model": config["model"]
        }
    except Exception as e:
        return {
            "provider_name": "unknown",
            "model": "unknown",
            "error": str(e)
        }
