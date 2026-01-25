"""Legal Case Intake Service"""
from typing import List, Dict, Any, Optional, AsyncGenerator
import asyncio
import json
import logging
import uuid
from functools import partial

from .models import CaseIntake, CaseIntakeResponse
from .intake_agents import process_case_intake
from .progress import set_progress_callback

logger = logging.getLogger(__name__)

# In-memory storage for demo purposes
intake_sessions: Dict[str, Dict[str, Any]] = {}


async def process_case(case_id: str, case_intake: CaseIntake, previously_provided_info: Optional[str] = None) -> Dict[str, Any]:
    """
    Process a legal case intake using AI agents.
    
    Args:
        case_id: Unique case identifier
        case_intake: The case data
        previously_provided_info: Additional info provided by user in subsequent rounds
        
    Returns:
        The processing result
    """
    try:
        session = intake_sessions.get(case_id)
        if not session:
            logger.error(f"Session not found for {case_id}")
            return {}
            
        session["status"] = "processing"
        session["message"] = "AI Agents analyzing case details..."
        
        # Run the actual agent workflow
        # Note: This is a synchronous call that we run in a thread pool to avoid blocking
        result = await asyncio.to_thread(
            process_case_intake, 
            case_intake, 
            previously_provided_info
        )
        
        # Update session with results
        session["status"] = "completed" if result.get("is_complete") else "needs_reflection" # Status distinguishes flow state
        session["message"] = "Analysis complete"
        session["intake_summary"] = result.get("intake_summary")
        session["risk_assessment"] = result.get("risk_assessment")
        session["recommended_action"] = result.get("recommended_action")
        session["needs_more_info"] = result.get("needs_more_info", False)
        session["missing_info"] = result.get("missing_info", [])
        session["is_complete"] = result.get("is_complete", False)
        
        # Keep track of the accumulated info for context
        if previously_provided_info:
            current_info = session.get("previously_provided_info", "")
            session["previously_provided_info"] = f"{current_info}\nUser added: {previously_provided_info}".strip()
            
        return session
        
    except Exception as e:
        logger.error(f"Error processing case: {e}")
        if case_id in intake_sessions:
            intake_sessions[case_id]["status"] = "error"
            intake_sessions[case_id]["message"] = f"Error: {str(e)}"
        return {"error": str(e)}


async def stream_case_processing(case_id: str, case_intake: CaseIntake) -> AsyncGenerator[str, None]:
    """
    Stream case processing updates via SSE.
    
    This mechanism sets a global callback to capture agent progress events
    and streams them to the client.
    """
    step_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
    completion_event = asyncio.Event()
    
    # Callback to push updates to the queue
    def progress_callback(step_data: Dict[str, Any]):
        step_queue.put_nowait(step_data)
        
        # Also store steps in the session for history
        if case_id in intake_sessions:
            if "steps" not in intake_sessions[case_id]:
                intake_sessions[case_id]["steps"] = []
            intake_sessions[case_id]["steps"].append(step_data)

    # Set the callback (note: this is global, so it assumes one request at a time for this demo)
    # In a production app, we'd pass a context object or use contextvars
    set_progress_callback(progress_callback)
    
    # Yield initial connection message
    yield f"data: {json.dumps({'status': 'connected', 'case_id': case_id, 'message': 'Connected to intake agents...'})}\n\n"
    
    # Run processing in background
    processing_task = asyncio.create_task(process_case(case_id, case_intake))
    
    # Loop to yield events from queue until processing is done
    while not processing_task.done():
        try:
            # Wait for a step or a small timeout to check task status
            step = await asyncio.wait_for(step_queue.get(), timeout=0.1)
            yield f"data: {json.dumps({'step': step})}\n\n"
        except asyncio.TimeoutError:
            continue
            
    # Flush any remaining steps
    while not step_queue.empty():
        step = step_queue.get_nowait()
        yield f"data: {json.dumps({'step': step})}\n\n"
        
    # Check for exceptions
    try:
        result = await processing_task
        if "error" in result:
             yield f"data: {json.dumps({'error': result['error']})}\n\n"
        else:
             yield f"data: {json.dumps({'done': True, 'result': result, 'status': result.get('status')})}\n\n"
    except Exception as e:
        logger.error(f"Task failed: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
