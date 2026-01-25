from typing import Dict, Any, AsyncGenerator
import json
import logging
import asyncio

from .models import ResumeData, FormStructure, FormField
from .form_agent import fill_form_from_resume, set_progress_callback

logger = logging.getLogger(__name__)
sessions: Dict[str, Dict[str, Any]] = {}

async def stream_form_filling(session_id: str, form_structure: FormStructure) -> AsyncGenerator[str, None]:
    if session_id not in sessions: yield f"data: {json.dumps({'error': 'Session not found'})}\n\n"; return
    session = sessions[session_id]
    resume_data = ResumeData(**session["resume_data"])
    
    step_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
    complete = asyncio.Event()
    
    def update_progress(data): step_queue.put_nowait(data)
    set_progress_callback(update_progress)
    
    async def run_filling():
        try:
            async for update in fill_form_from_resume(resume_data, form_structure):
                step_queue.put_nowait(update)
            complete.set()
        except: complete.set()
        finally: set_progress_callback(None)

    asyncio.create_task(run_filling())
    yield f"data: {json.dumps({'status': 'connected'})}\n\n"
    
    while not complete.is_set() or not step_queue.empty():
        try:
            upd = await asyncio.wait_for(step_queue.get(), timeout=0.1)
            yield f"data: {json.dumps(upd)}\n\n"
        except asyncio.TimeoutError: continue
