from utils.llm_provider import get_image_provider
from utils.thinking_streamer import ThinkingStreamer
import asyncio
from typing import Optional
from .prompts import KIDS_COLORING_PAGE_PROMPT

async def generate_coloring_page(image_bytes: bytes, session_id: Optional[str] = None) -> bytes:
    """Generate coloring page using configured image LLM provider"""
    provider = get_image_provider()
    
    if session_id:
        ThinkingStreamer.add_event(session_id, "analysis", "Analyzing image composition for kid-friendly update...")
        await asyncio.sleep(0.5)
        ThinkingStreamer.add_event(session_id, "planning", "Simplifying shapes and removing shading...")
        await asyncio.sleep(0.5)
        ThinkingStreamer.add_event(session_id, "processing", "Generating bold line art sketch...")
    
    generated_image = await provider.generate_image(
        image_bytes=image_bytes,
        prompt=KIDS_COLORING_PAGE_PROMPT
    )
    
    if session_id:
        ThinkingStreamer.add_event(session_id, "processing", "Finalizing high-contrast coloring page...")
    
    return generated_image
