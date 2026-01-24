from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import Response, StreamingResponse
from .service import generate_coloring_page
from utils.thinking_streamer import ThinkingStreamer
import json
from typing import Optional

router = APIRouter(prefix="/image-to-drawing", tags=["image-to-drawing"])

@router.post("/convert")
async def convert_image(
    file: UploadFile = File(...),
    session_id: Optional[str] = None
):
    """
    Convert an uploaded image to a coloring book page using LLM image generation
    """
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload JPG, PNG, or WebP images."
        )
    
    try:
        image_bytes = await file.read()
        
        max_size = 10 * 1024 * 1024
        if len(image_bytes) > max_size:
            raise HTTPException(
                status_code=400,
                detail="File size too large. Maximum size is 10MB."
            )
        
        original_filename = file.filename or "image"
        name_without_ext = original_filename.rsplit('.', 1)[0] if '.' in original_filename else original_filename
        download_filename = f"{name_without_ext}-colorbook.png"
        
        generated_image = await generate_coloring_page(image_bytes, session_id)
        
        return Response(
            content=generated_image,
            media_type="image/png",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate coloring page: {str(e)}"
        )


@router.get("/stream/{session_id}")
async def stream_thinking(session_id: str):
    """Stream thinking events for image processing"""
    async def event_generator():
        async for event in ThinkingStreamer.stream_events(session_id):
            yield f"data: {json.dumps(event.to_dict())}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        from utils.llm_provider import get_provider_config
        config = get_provider_config()
        return {
            "status": "healthy",
            "service": "image-to-drawing",
            "provider": config["provider_name"]
        }
    except:
        return {
            "status": "unhealthy",
            "service": "image-to-drawing",
            "message": "No LLM provider configured"
        }
