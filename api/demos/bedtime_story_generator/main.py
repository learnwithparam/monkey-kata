"""
Bedtime Story Generator Demo
============================

A simple, clean demo showing:
- Streaming responses from LLM
- Basic prompt engineering
- Real-time UI updates
- Error handling

Perfect for teaching bootcamp students the fundamentals of LLM integration.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import AsyncGenerator
import asyncio
import json
import os
from utils.llm_provider import get_llm_provider

# Initialize router
router = APIRouter(prefix="/bedtime-story", tags=["bedtime-story"])

# Initialize LLM provider
llm_provider = get_llm_provider()

class StoryRequest(BaseModel):
    """Request model for story generation"""
    character_name: str
    character_age: int
    story_theme: str
    story_length: str = "short"  # short, medium, long

class StoryResponse(BaseModel):
    """Response model for story metadata"""
    character_name: str
    character_age: int
    story_theme: str
    story_length: str
    total_tokens: int = 0

def create_story_prompt(request: StoryRequest) -> str:
    """Create a well-structured prompt for story generation"""
    length_instructions = {
        "short": "Write a short bedtime story (2-3 paragraphs)",
        "medium": "Write a medium-length bedtime story (4-6 paragraphs)", 
        "long": "Write a longer bedtime story (7-10 paragraphs)"
    }
    
    return f"""You are a creative children's story writer. Write a {request.story_length} bedtime story with these details:

Character: {request.character_name}, age {request.character_age}
Theme: {request.story_theme}

{length_instructions[request.story_length]}

Requirements:
- Use simple, child-friendly language
- Include a positive moral or lesson
- Make it engaging and imaginative
- End with a peaceful, sleepy conclusion
- Use descriptive language that paints pictures

Begin the story now:"""

async def generate_story_stream(request: StoryRequest) -> AsyncGenerator[str, None]:
    """Generate story with streaming response"""
    try:
        prompt = create_story_prompt(request)
        
        # Use the LLM provider for streaming
        async for chunk in llm_provider.generate_stream(
            prompt,
            temperature=0.8,
            max_tokens=1000
        ):
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        
        # Send completion signal
        yield f"data: {json.dumps({'done': True})}\n\n"
        
    except Exception as e:
        error_msg = f"data: {json.dumps({'error': str(e)})}\n\n"
        yield error_msg

@router.post("/generate", response_model=StoryResponse)
async def generate_story(request: StoryRequest):
    """Generate a bedtime story (non-streaming endpoint for metadata)"""
    try:
        # Validate input
        if not request.character_name.strip():
            raise HTTPException(status_code=400, detail="Character name is required")
        
        if request.character_age < 3 or request.character_age > 12:
            raise HTTPException(status_code=400, detail="Character age must be between 3 and 12")
        
        if not request.story_theme.strip():
            raise HTTPException(status_code=400, detail="Story theme is required")
        
        return StoryResponse(
            character_name=request.character_name,
            character_age=request.character_age,
            story_theme=request.story_theme,
            story_length=request.story_length
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating story: {str(e)}")

@router.post("/stream")
async def stream_story(request: StoryRequest):
    """Generate a bedtime story with streaming response"""
    try:
        # Validate input
        if not request.character_name.strip():
            raise HTTPException(status_code=400, detail="Character name is required")
        
        if request.character_age < 3 or request.character_age > 12:
            raise HTTPException(status_code=400, detail="Character age must be between 3 and 12")
        
        if not request.story_theme.strip():
            raise HTTPException(status_code=400, detail="Story theme is required")
        
        return StreamingResponse(
            generate_story_stream(request),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/plain; charset=utf-8"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error streaming story: {str(e)}")

@router.get("/themes")
async def get_story_themes():
    """Get available story themes"""
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
            "castle",
            "learning",
            "sharing",
            "bravery"
        ]
    }

@router.get("/health")
async def health_check():
    """Health check for the bedtime story service"""
    from utils.llm_provider import LLMProviderFactory
    
    return {
        "status": "healthy",
        "service": "bedtime-story-generator",
        "features": ["streaming", "prompt-engineering", "error-handling"],
        "llm_provider": type(llm_provider).__name__,
        "available_providers": LLMProviderFactory.get_available_providers()
    }
