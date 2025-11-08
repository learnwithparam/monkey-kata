"""
Bedtime Story Generator
=======================

🎯 LEARNING OBJECTIVES:
This demo teaches you how to build an AI-powered application step by step:

1. LLM Integration - How to connect and use AI models
2. Prompt Engineering - How to craft effective prompts
3. Streaming Responses - How to create real-time, ChatGPT-like experiences
4. Input Validation - How to ensure data quality
5. API Design - How to build clean, RESTful endpoints

📚 LEARNING FLOW:
Follow this code from top to bottom to understand how each piece works:

Step 1: Setup - Import libraries and configure the router
Step 2: Data Models - Define request structure with validation
Step 3: Prompt Engineering - Craft the instruction for the AI
Step 4: Story Generation - Stream the AI's response in real-time
Step 5: API Endpoints - Expose functionality via HTTP

Let's start building!
"""

# ============================================================================
# STEP 1: SETUP & IMPORTS
# ============================================================================
"""
Understanding the Imports:
- FastAPI: Web framework for building APIs
- StreamingResponse: Enables real-time streaming (like ChatGPT)
- BaseModel: Provides automatic data validation
- AsyncGenerator: Allows streaming data piece by piece
- json: Formats data for Server-Sent Events (SSE)
- get_llm_provider: Helper to connect to AI models (Gemini, OpenAI, etc.)
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import AsyncGenerator
import json

from utils.llm_provider import get_llm_provider, get_provider_config

# Create a router - groups all endpoints under /bedtime-story
router = APIRouter(prefix="/bedtime-story", tags=["bedtime-story"])

# Initialize the AI provider (automatically selects based on your API keys)
llm_provider = get_llm_provider()


# ============================================================================
# STEP 2: DATA MODELS (Request Validation)
# ============================================================================
"""
What is a Data Model?
- Defines the structure of incoming requests
- Automatically validates data (type checking, required fields)
- Provides clear error messages if validation fails
- Think of it as a "contract" for what your API expects

Example: If someone sends character_age as "five" instead of 5,
FastAPI will automatically return a 422 error with a helpful message.
"""
class StoryRequest(BaseModel):
    """Defines what data we need to generate a story"""
    
    character_name: str = Field(
        ..., 
        min_length=1, 
        max_length=50,
        description="The name of the story's main character"
    )
    
    character_age: int = Field(
        ..., 
        ge=1, 
        le=18,
        description="Age of the character (1-18 years)"
    )
    
    story_theme: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="The theme or topic of the story (e.g., 'friendship', 'adventure')"
    )
    
    story_length: str = Field(
        ...,
        description="Desired length: 'short', 'medium', or 'long'"
    )


# ============================================================================
# STEP 3: PROMPT ENGINEERING
# ============================================================================
"""
What is Prompt Engineering?
- The art of writing instructions that guide AI to produce desired output
- Good prompts are: clear, specific, and structured
- This is where you teach the AI what you want

Key Prompt Engineering Techniques Used Here:
1. Role-Setting: Tell the AI who it is ("bedtime storyteller")
2. Context: Provide user inputs (character name, age, theme)
3. Instructions: Specify format, length, style
4. Constraints: Set boundaries (age-appropriate, specific word count)

💡 Try This: Modify this prompt and see how the story quality changes!
"""
def build_story_prompt(request: StoryRequest) -> str:
    """
    Builds a well-structured prompt for the AI
    
    This function takes user inputs and combines them into a clear
    instruction that tells the AI exactly what kind of story to write.
    """
    # Define length requirements - maps user selection to specific instructions
    length_map = {
        "short": "3-5 paragraphs, approximately 40-60 words",
        "medium": "5-7 paragraphs, approximately 100-150 words",
        "long": "8-12 paragraphs, approximately 200-300 words"
    }
    
    # Build the prompt step by step for clarity
    prompt = f"""You are a creative and gentle bedtime storyteller.

Write a personalized bedtime story with these details:
- Main character: {request.character_name}, age {request.character_age}
- Theme: {request.story_theme}
- Length: {length_map.get(request.story_length, length_map['medium'])}

Requirements:
1. Start with an engaging title
2. Write in clear paragraphs with natural breaks
3. Make it age-appropriate for a {request.character_age}-year-old
4. End with a gentle moral lesson about kindness, bravery, or friendship
5. Keep the tone warm, comforting, and suitable for bedtime

Begin the story now:"""

    return prompt


# ============================================================================
# STEP 4: STORY GENERATION (Streaming Logic)
# ============================================================================
"""
What is Streaming?
- Instead of waiting for the entire story, send it piece by piece
- Creates a "typing" effect like ChatGPT
- Feels faster and more interactive to users

How Streaming Works:
1. AI generates text in small chunks (tokens)
2. Each chunk is sent immediately to the frontend
3. Frontend displays chunks as they arrive
4. User sees story appear in real-time

Technical Details:
- Uses async generators (async functions with 'yield')
- Formats as Server-Sent Events (SSE) with "data: {json}\n\n"
- Keeps connection alive until story is complete
"""
async def generate_story_stream(request: StoryRequest) -> AsyncGenerator[str, None]:
    """
    Generates and streams a story in real-time
    
    This is an async generator - it yields chunks of data as they're generated.
    Each yield sends data to the frontend immediately.
    """
    # Step 1: Notify frontend that connection is established
    yield f"data: {json.dumps({'status': 'connected', 'message': 'Starting story generation...'})}\n\n"
    
    try:
        # Step 2: Build the prompt from user inputs
        prompt = build_story_prompt(request)
        
        # Step 3: Stream the story content from the AI
        # The AI generates text chunk by chunk, and we forward each chunk immediately
        story_content = ""
        try:
            async for chunk in llm_provider.generate_stream(
                prompt,
                temperature=0.8,  # Controls creativity (0.0 = deterministic, 1.0+ = creative)
                max_tokens=800    # Limits story length
            ):
                story_content += chunk
                # Send each chunk to frontend as it arrives
                yield f"data: {json.dumps({'content': chunk})}\n\n"
        except (RuntimeError, StopIteration) as e:
            # StopIteration and some RuntimeErrors indicate normal completion
            # (some async frameworks convert StopIteration to RuntimeError)
            error_str = str(e).lower()
            if "stopiteration" in error_str or "async generator" in error_str:
                # Generator finished normally - this is expected, not an error
                pass
            else:
                # Other RuntimeError - re-raise as it's a real error
                raise
        
        # Step 4: Signal that generation is complete
        yield f"data: {json.dumps({'done': True, 'status': 'completed'})}\n\n"
        
    except Exception as e:
        # Handle errors gracefully
        error_message = f"Error generating story: {str(e)}"
        yield f"data: {json.dumps({'error': error_message, 'status': 'error'})}\n\n"


# ============================================================================
# STEP 5: API ENDPOINTS
# ============================================================================
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
    
    In a real application, this might:
    - Come from a database
    - Be user-customizable
    - Include theme descriptions or images
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


# ============================================================================
# LEARNING CHECKLIST
# ============================================================================
"""
After reading this code, you should understand:

✓ How to validate incoming data with Pydantic models
✓ How to build effective prompts for AI models
✓ How streaming works (async generators, SSE format)
✓ How to structure API endpoints with FastAPI
✓ How to handle errors gracefully

Next Steps:
1. Modify the prompt to change story style
2. Experiment with temperature values (0.2 vs 0.8 vs 1.2)
3. Add a new input field (e.g., secondary character)
4. Add post-processing (e.g., format validation, content filtering)
5. Try implementing a "continue story" feature

Questions to Consider:
- What happens if the API key is invalid?
- How would you add content safety checks?
- How could you save stories to a database?
- What metrics would you track in production?
"""