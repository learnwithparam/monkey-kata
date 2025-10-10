"""
Bedtime Story Generator API
===========================

🎯 LEARNING OBJECTIVES FOR BOOTCAMP STUDENTS:

This demo teaches core AI engineering concepts:

1. STREAMING RESPONSES (Server-Sent Events)
   - How to create real-time streaming APIs like ChatGPT
   - Using async generators for word-by-word streaming
   - Proper SSE formatting with data: prefix

2. LLM INTEGRATION
   - How to integrate with different LLM providers (Gemini, OpenAI)
   - Prompt engineering for structured JSON output
   - Error handling and fallback strategies

3. JSON PARSING & ERROR HANDLING
   - Robust JSON extraction from LLM responses
   - Graceful fallbacks when parsing fails
   - Multiple error handling layers

4. FASTAPI BEST PRACTICES
   - Pydantic models for request validation
   - Proper async/await patterns
   - Router organization and tags

Key Files to Study:
- main.py (this file) - API endpoints and streaming logic
- utils/llm_provider.py - LLM integration patterns
- frontend/page.tsx - How to consume streaming APIs

🚀 Try This:
1. Start the API: docker compose up
2. Visit: http://localhost:4020/demos/bedtime-story
3. Watch the network tab to see streaming in action!
"""

# ============================================================================
# IMPORTS
# ============================================================================
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import AsyncGenerator
import asyncio
import json
from utils.llm_provider import get_llm_provider

# ============================================================================
# ROUTER SETUP
# ============================================================================
# Create a router with prefix and tags for organization
# This groups all bedtime story endpoints under /bedtime-story
router = APIRouter(prefix="/bedtime-story", tags=["bedtime-story"])

# Initialize LLM provider (Gemini, OpenAI, or Mock based on environment)
llm_provider = get_llm_provider()

# ============================================================================
# DATA MODELS
# ============================================================================
class StoryRequest(BaseModel):
    """
    Pydantic model for story generation requests
    
    This ensures type safety and automatic validation of incoming data.
    FastAPI will automatically validate that:
    - character_name is a string
    - character_age is an integer  
    - story_theme is a string
    - story_length is a string
    
    If validation fails, FastAPI returns a 422 error with details.
    """
    character_name: str
    character_age: int
    story_theme: str
    story_length: str

# ============================================================================
# PROMPT ENGINEERING
# ============================================================================
def create_simple_prompt(request: StoryRequest) -> str:
    """
    Create a well-structured prompt for the LLM
    
    🎯 KEY PROMPT ENGINEERING CONCEPTS:
    
    1. CLEAR INSTRUCTIONS: Be specific about what you want
    2. STRUCTURED OUTPUT: Request JSON format for easy parsing
    3. LENGTH CONTROL: Use user input to control output length
    4. FORMATTING INSTRUCTIONS: Tell the LLM how to format the output
    5. CONTEXT: Include character details for personalization
    
    This is a simple prompt - in production, you'd use more sophisticated
    techniques like few-shot examples, chain-of-thought, etc.
    """
    # Define length requirements based on user selection
    length_requirements = {
        "short": "3-5 paragraphs, about 40-60 words",
        "medium": "5-7 paragraphs, about 100-150 words", 
        "long": "8-12 paragraphs, about 200-300 words"
    }
    
    return f"""Write a personalized bedtime story for a {request.character_age}-year-old named {request.character_name} about {request.story_theme}.

Make it {length_requirements[request.story_length]} and write in proper paragraphs with clear breaks between them.

Start with an engaging title that captures the adventure, then tell the story naturally. End with a gentle moral lesson that emphasizes the importance of kindness, bravery, or friendship. Let the title and moral flow organically within the narrative without explicit labels."""

# ============================================================================
# STREAMING GENERATOR
# ============================================================================
async def generate_story_stream(request: StoryRequest) -> AsyncGenerator[str, None]:
    """
    Generate story with real-time streaming using Server-Sent Events (SSE)
    
    🎯 KEY CONCEPTS FOR BOOTCAMP STUDENTS:
    
    1. ASYNC GENERATORS: Use 'yield' to stream data in real-time
    2. SERVER-SENT EVENTS: Format data as "data: {json}\n\n"
    3. ERROR HANDLING: Multiple fallback layers for robustness
    4. JSON PARSING: Extract structured data from LLM responses
    5. STREAMING UX: Word-by-word streaming for ChatGPT-like experience
    
    This function demonstrates how to create streaming APIs that feel
    responsive and engaging to users.
    """
    try:
        # Step 1: Send initial connection confirmation
        yield f"data: {json.dumps({'status': 'connected', 'message': 'Starting story generation...'})}\n\n"
        
        # Step 2: Create the prompt and get LLM response
        prompt = create_simple_prompt(request)
        
        # Stream the story content directly from LLM
        story_content = ""
        async for chunk in llm_provider.generate_stream(prompt, temperature=0.8, max_tokens=800):
            story_content += chunk
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        
        # Send completion signal
        yield f"data: {json.dumps({'done': True, 'status': 'completed'})}\n\n"
        
    except Exception as e:
        # Handle any unexpected errors gracefully
        yield f"data: {json.dumps({'error': str(e), 'status': 'error'})}\n\n"

# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/stream")
async def stream_story(request: StoryRequest):
    """
    Main streaming endpoint for story generation
    
    🎯 KEY CONCEPTS:
    
    1. STREAMING RESPONSE: Uses FastAPI's StreamingResponse for real-time data
    2. MEDIA TYPE: "text/event-stream" is the standard for Server-Sent Events
    3. HEADERS: Cache-Control and Connection headers for proper SSE behavior
    4. ASYNC GENERATOR: Passes the async generator to StreamingResponse
    
    The frontend will receive a stream of data like:
    data: {"status": "connected", "message": "Starting..."}
    data: {"metadata": {"title": "Story Title", "moral": "Lesson"}}
    data: {"content": "Once upon a time..."}
    data: {"done": true, "status": "completed"}
    """
    return StreamingResponse(
        generate_story_stream(request),
        media_type="text/event-stream",  # Changed to proper SSE media type
        headers={
            "Cache-Control": "no-cache",  # Prevent caching of streaming data
            "Connection": "keep-alive",   # Keep connection alive for streaming
        }
    )

@router.get("/themes")
async def get_story_themes():
    """
    Get available story themes
    
    This endpoint provides the list of themes that users can select from.
    In a production app, this might come from a database or config file.
    """
    return {
        "themes": [
            "adventure", "friendship", "courage", "kindness", 
            "imagination", "family", "animals", "magic", 
            "space", "underwater", "forest", "castle"
        ]
    }

@router.get("/health")
async def health_check():
    """
    Health check endpoint
    
    This is useful for:
    - Monitoring system health
    - Load balancer health checks
    - Debugging connection issues
    """
    return {
        "status": "healthy",
        "service": "bedtime-story-generator",
        "description": "Simple AI bedtime story generator for learning"
    }

"""
LEARNING NOTES FOR STUDENTS:
===========================

1. SIMPLE PROMPT ENGINEERING:
   - Clear, specific instructions
   - Tell AI exactly what format you want (JSON)
   - Specify requirements clearly

2. STREAMING:
   - Split response into chunks and stream them
   - Creates "typing" effect in frontend
   - Shows real-time AI processing

3. ERROR HANDLING:
   - Try to parse JSON, but have fallbacks
   - Always handle errors gracefully
   - Never crash the application

4. API DESIGN:
   - Simple endpoints that do one thing
   - Clear request/response models
   - Good HTTP status codes

5. CODE ORGANIZATION:
   - Functions have single responsibilities
   - Clear variable names
   - Comments explain the "why"
"""