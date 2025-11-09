"""
Image to Coloring Book Converter
=================================

🎯 LEARNING OBJECTIVES:
This demo teaches image-to-image generation using LLM models:

1. Image Upload Handling - How to accept image files
2. LLM Image Generation - How to use AI models for image transformation
3. Image-to-Image API - How to call img2img endpoints
4. Provider Pattern - How to use llm_provider utilities

📚 LEARNING FLOW:
Step 1: Setup - Import libraries and configure router
Step 2: Image Generation - Use LLM provider to generate coloring page
Step 3: API Endpoints - Expose functionality via HTTP
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response
from utils.llm_provider import get_llm_provider

router = APIRouter(prefix="/image-to-drawing", tags=["image-to-drawing"])


# ============================================================================
# STEP 2: IMAGE GENERATION
# ============================================================================
"""
Image Generation:
This function uses the LLM provider pattern to generate coloring pages.

Key Concepts:
- get_llm_provider(): Gets the configured provider (Fireworks, OpenAI, etc.)
- provider.generate_image(): Calls the provider's image generation method
- Same pattern as generate_text() and generate_stream() for text

Currently supported providers:
- Fireworks AI (FLUX model) - image-to-image ✅
- OpenAI (GPT Image 1) - image-to-image via edit API ✅
- OpenRouter - Learning challenge! 🎓
- Gemini - Learning challenge! 🎓
"""
async def generate_coloring_page(image_bytes: bytes) -> bytes:
    """Generate coloring page using configured LLM provider"""
    provider = get_llm_provider()
    
    prompt = (
        "Convert the provided input image into a coloring book sketch. "
        "Keep the exact same image - same subjects, same composition, same layout. "
        "Transform it to black line art on white background only. "
        "Remove all colors and shading. Keep the image identical, just as a coloring book sketch."
    )
    
    generated_image = await provider.generate_image(
        image_bytes=image_bytes,
        prompt=prompt
    )
    
    return generated_image


# ============================================================================
# STEP 3: API ENDPOINTS
# ============================================================================
"""
API Endpoints:
- POST /convert: Convert uploaded image to coloring page
- GET /health: Health check
"""
@router.post("/convert")
async def convert_image(file: UploadFile = File(...)):
    """
    Convert an uploaded image to a coloring book page using LLM image generation
    
    This endpoint:
    1. Accepts an image file (JPG, PNG, or WebP)
    2. Validates the file type and size
    3. Uses LLM image generation to create coloring page
    4. Returns the generated image
    
    Supported file types:
    - JPEG/JPG (.jpg, .jpeg)
    - PNG (.png)
    - WebP (.webp)
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
        
        # Generate filename with -colorbook suffix
        original_filename = file.filename or "image"
        name_without_ext = original_filename.rsplit('.', 1)[0] if '.' in original_filename else original_filename
        download_filename = f"{name_without_ext}-colorbook.png"
        
        # Use LLM image generation to create coloring page
        generated_image = await generate_coloring_page(image_bytes)
        
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
