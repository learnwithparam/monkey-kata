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
    
    # Callback for non-thinking events (legacy progress updates)
    def update_progress(step_data):
        if isinstance(step_data, str):
            msg = step_data
        else:
            msg = step_data.get("message", "")
            target = step_data.get("target")
            tool = step_data.get("tool")
            
            # Enhance message with target info if available
            if target:
                if tool == "search_web":
                    msg = f"Searching: {target}"
                elif tool == "scrape_website":
                    msg = f"Reading: {target}"
                else:
                    msg = f"{msg}: {target}"
                    
        # Create a log entry format that matches what the frontend expects for logs
        entry = {
            "timestamp": datetime.now().isoformat(), 
            "content": msg,
            "type": "log"
        }
        if session_id in analysis_sessions: 
            # Also append to steps for persistence
            analysis_sessions[session_id]["steps"].append(entry)
        
        # Put in queue
        try:
             step_queue.put_nowait(entry)
        except asyncio.QueueFull:
             pass

    set_progress_callback(update_progress)
    
    # Subscribe to thinking events
    thinking_streamer.add_callback(lambda e: step_queue.put_nowait({"step": e.to_dict()}))
    
    async def run_analysis():
        nonlocal final_report
        try:
            final_report = await run_competitor_analysis(company_name, competitors, focus_areas, thinking_streamer)
            analysis_sessions[session_id]["status"] = "completed"
            analysis_sessions[session_id]["report"] = final_report
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            analysis_sessions[session_id]["status"] = "error"
            step_queue.put_nowait({"error": str(e)})
        finally:
            analysis_complete.set()
            set_progress_callback(None)
            thinking_streamer.close()
    
    # Start analysis in background
    asyncio.create_task(run_analysis())
    
    # Initial connection message
    yield f"data: {json.dumps({'status': 'connected', 'session_id': session_id})}\n\n"
    
    # Stream events
    while not analysis_complete.is_set() or not step_queue.empty():
        try:
            # Wait for next event with short timeout to check completion
            step = await asyncio.wait_for(step_queue.get(), timeout=0.1)
            
            # If it's a "step" (thinking event), wrap it properly
            if "step" in step:
                yield f"data: {json.dumps(step)}\n\n"
            # If it's a log entry
            elif "type" in step and step["type"] == "log":
                yield f"data: {json.dumps(step)}\n\n"
            # If it's an error
            elif "error" in step:
                yield f"data: {json.dumps(step)}\n\n"
            # Generic fallback
            else:
                 yield f"data: {json.dumps({'step': step})}\n\n"

        except asyncio.TimeoutError:
            continue
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            break
            
    if final_report: 
        yield f"data: {json.dumps({'done': True, 'report': final_report})}\n\n"
