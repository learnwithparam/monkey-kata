"""Legal Case Intake Service"""
from typing import List, Dict, Any, Optional, AsyncGenerator
import asyncio
import json
import logging
import uuid

from .models import CaseIntake

logger = logging.getLogger(__name__)

intake_sessions: Dict[str, Dict[str, Any]] = {}


async def process_case(case_id: str, case_intake: CaseIntake):
    """Background task to process a legal case intake"""
    try:
        session = intake_sessions[case_id]
        session["status"] = "processing"
        session["message"] = "Analyzing case details..."
        
        # Simulate processing (replace with actual LegalIntakeFlow if available)
        await asyncio.sleep(1)
        
        session["status"] = "completed"
        session["message"] = "Case processing complete"
        session["intake_summary"] = f"Case type: {case_intake.case_type}. Description: {case_intake.case_description[:100]}..."
        session["risk_assessment"] = "Medium risk based on case details"
        session["recommended_action"] = "Schedule initial consultation"
        
    except Exception as e:
        logger.error(f"Error processing case: {e}")
        if case_id in intake_sessions:
            intake_sessions[case_id]["status"] = "error"
            intake_sessions[case_id]["message"] = f"Error: {str(e)}"


async def stream_case_processing(case_id: str, case_intake: CaseIntake) -> AsyncGenerator[str, None]:
    """Stream case processing updates"""
    step_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
    complete = asyncio.Event()
    
    async def run_processing():
        try:
            session = intake_sessions[case_id]
            session["status"] = "processing"
            
            # Step 1: Document analysis
            step_queue.put_nowait({"message": "Analyzing case documents..."})
            await asyncio.sleep(0.5)
            
            # Step 2: Risk assessment
            step_queue.put_nowait({"message": "Performing risk assessment..."})
            await asyncio.sleep(0.5)
            
            # Step 3: Generate summary
            step_queue.put_nowait({"message": "Generating case summary..."})
            await asyncio.sleep(0.5)
            
            session["status"] = "completed"
            session["intake_summary"] = f"Case type: {case_intake.case_type}. {case_intake.case_description[:100]}..."
            session["risk_assessment"] = "Medium risk based on case details"
            session["recommended_action"] = "Schedule initial consultation"
        except Exception as e:
            logger.error(f"Error: {e}")
            intake_sessions[case_id]["status"] = "error"
        finally:
            complete.set()
    
    asyncio.create_task(run_processing())
    yield f"data: {json.dumps({'status': 'connected'})}\n\n"
    
    while not complete.is_set() or not step_queue.empty():
        try:
            step = await asyncio.wait_for(step_queue.get(), timeout=0.1)
            yield f"data: {json.dumps({'step': step})}\n\n"
        except asyncio.TimeoutError:
            continue
    
    s = intake_sessions[case_id]
    if s["status"] == "completed":
        yield f"data: {json.dumps({'done': True, 'result': s})}\n\n"
