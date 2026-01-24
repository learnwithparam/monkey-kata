from typing import List, Optional, Dict, Any, AsyncGenerator
import logging
import asyncio
import json
from datetime import datetime

from .agents import run_competitor_analysis
from .tools import set_progress_callback
from utils.thinking_streamer import ThinkingStreamer

logger = logging.getLogger(__name__)

analysis_sessions: Dict[str, Dict[str, Any]] = {}

async def process_analysis(
    session_id: str, company_name: str, competitors: List[str], focus_areas: List[str]
):
    try:
        session = analysis_sessions[session_id]
        session["status"] = "researching"
        session["steps"] = []
        
        def update_progress(step_message: str):
            if session_id in analysis_sessions:
                step_entry = {"timestamp": datetime.now().isoformat(), "message": step_message}
                analysis_sessions[session_id]["steps"].append(step_entry)
                analysis_sessions[session_id]["message"] = step_message
        
        set_progress_callback(update_progress)
        report = await run_competitor_analysis(company_name, competitors, focus_areas)
        
        session["status"] = "completed"
        session["message"] = "Analysis complete!"
        session["report"] = report
        set_progress_callback(None)
    except Exception as e:
        logger.error(f"Error: {e}")
        if session_id in analysis_sessions:
            analysis_sessions[session_id]["status"] = "error"
            analysis_sessions[session_id]["message"] = f"Error: {str(e)}"
        set_progress_callback(None)

async def stream_analysis_steps(
    session_id: str, company_name: str, competitors: List[str], focus_areas: List[str]
) -> AsyncGenerator[str, None]:
    step_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
    analysis_complete = asyncio.Event()
    final_report = None
    thinking_streamer = ThinkingStreamer(agent_name="Competitor Analysis")
    
    def update_progress(step_data):
        msg = step_data if isinstance(step_data, str) else step_data.get("message", "")
        entry = {"timestamp": datetime.now().isoformat(), "message": msg}
        if session_id in analysis_sessions: analysis_sessions[session_id]["steps"].append(entry)
        step_queue.put_nowait(entry)

    set_progress_callback(update_progress)
    thinking_streamer.add_callback(lambda e: step_queue.put_nowait(e.__dict__))
    
    async def run_analysis():
        nonlocal final_report
        try:
            final_report = await run_competitor_analysis(company_name, competitors, focus_areas, thinking_streamer)
            analysis_sessions[session_id]["status"] = "completed"
            analysis_sessions[session_id]["report"] = final_report
        except Exception as e:
            analysis_sessions[session_id]["status"] = "error"
        finally:
            analysis_complete.set()
            set_progress_callback(None)
            thinking_streamer.close()

    asyncio.create_task(run_analysis())
    yield f"data: {json.dumps({'status': 'connected'})}\n\n"
    
    while not analysis_complete.is_set() or not step_queue.empty():
        try:
            step = await asyncio.wait_for(step_queue.get(), timeout=0.1)
            yield f"data: {json.dumps({'step': step})}\n\n"
        except asyncio.TimeoutError:
            continue
    
    if final_report: yield f"data: {json.dumps({'done': True, 'report': final_report})}\n\n"
