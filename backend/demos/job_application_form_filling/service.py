from typing import Dict, Any, AsyncGenerator
import json
import logging
import asyncio

from .models import ResumeData, FormStructure, FormField
from .form_agent import fill_form_from_resume
from utils.thinking_streamer import ThinkingStreamer

logger = logging.getLogger(__name__)
sessions: Dict[str, Dict[str, Any]] = {}

async def stream_form_filling(session_id: str, form_structure: FormStructure) -> AsyncGenerator[str, None]:
    if session_id not in sessions:
        yield f"data: {json.dumps({'error': 'Session not found'})}\n\n"
        return
        
    session = sessions[session_id]
    resume_data = ResumeData(**session["resume_data"])
    
    # Initialize ThinkingStreamer
    thinking_streamer = ThinkingStreamer(agent_name="Form Agent")
    step_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
    complete = asyncio.Event()
    
    # Subscribe to thinking events
    def on_thinking_event(event):
        step_queue.put_nowait({"thinking": event.__dict__})
        
    thinking_streamer.add_callback(on_thinking_event)
    
    # Initial connection message
    yield f"data: {json.dumps({'status': 'connected', 'message': 'Initializing form agent...'})}\n\n"
    
    async def run_filling():
        try:
            # Emit starting event
            await thinking_streamer.emit_thinking("start", "Initializing autonomous form filling agent...")
            
            async for update in fill_form_from_resume(resume_data, form_structure, thinking_streamer):
                # Put direct updates (logs, field updates) into queue
                step_queue.put_nowait(update)
                
            sessions[session_id]["status"] = "completed"
            complete.set()
        except Exception as e:
            logger.error(f"Error filling form: {e}")
            sessions[session_id]["status"] = "error"
            sessions[session_id]["error"] = str(e)
            step_queue.put_nowait({"error": str(e)})
            complete.set()
        finally:
            thinking_streamer.close()

    # Start background task
    asyncio.create_task(run_filling())
    
    # Stream events from queue
    while not complete.is_set() or not step_queue.empty():
        try:
            # Wait for next event with short timeout
            data = await asyncio.wait_for(step_queue.get(), timeout=0.1)
            yield f"data: {json.dumps(data)}\n\n"
        except asyncio.TimeoutError:
            continue
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            break
            
    yield f"data: {json.dumps({'done': True, 'status': 'completed'})}\n\n"
