from utils.llm_provider import get_llm_provider
from utils.thinking_streamer import ThinkingStreamer
import asyncio
from typing import Optional

async def generate_coloring_page(image_bytes: bytes, session_id: Optional[str] = None) -> bytes:
    """Generate coloring page using configured LLM provider"""
    provider = get_llm_provider()
    
    if session_id:
        ThinkingStreamer.add_event(session_id, "analysis", "Analyzing image composition and identifying key subjects...")
        await asyncio.sleep(0.5)
        ThinkingStreamer.add_event(session_id, "planning", "Preparing coloring book transformation instructions...")
        await asyncio.sleep(0.5)
        ThinkingStreamer.add_event(session_id, "processing", "Transforming image to line art sketch...")
    
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
    
    if session_id:
        ThinkingStreamer.add_event(session_id, "processing", "Finalizing sketch and cleaning up line work...")
    
    return generated_image
