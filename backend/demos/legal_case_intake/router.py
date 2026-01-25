from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
import uuid
import logging

from .models import CaseIntake, CaseIntakeRequest, CaseIntakeResponse, CaseReviewRequest, CaseReviewResponse, AdditionalInfoRequest, ServiceInfo
from .service import process_case, stream_case_processing, intake_sessions

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/legal-case-intake", tags=["legal-case-intake"])

@router.get("/health", response_model=ServiceInfo)
async def health_check():
    return ServiceInfo(status="healthy", service="legal-case-intake", description="Legal intake system")

@router.post("/submit-case", response_model=CaseIntakeResponse)
async def submit_case(request: CaseIntakeRequest, background_tasks: BackgroundTasks):
    case_id = str(uuid.uuid4())
    case_intake = CaseIntake(**request.dict())
    intake_sessions[case_id] = {
        "case_id": case_id, "status": "processing", "message": "Initializing...",
        "intake_data": case_intake.dict(), "steps": [], "previously_provided_info": ""
    }
    background_tasks.add_task(process_case, case_id, case_intake)
    return CaseIntakeResponse(case_id=case_id, status="processing", message="Started")

@router.post("/submit-case-stream")
async def submit_case_stream(request: CaseIntakeRequest):
    case_id = str(uuid.uuid4())
    case_intake = CaseIntake(**request.dict())
    intake_sessions[case_id] = {
        "case_id": case_id, "status": "processing", "message": "Initializing...",
        "intake_data": case_intake.dict(), "steps": [], "previously_provided_info": ""
    }
    return StreamingResponse(
        stream_case_processing(case_id, case_intake),
        media_type="text/event-stream"
    )

@router.post("/provide-additional-info", response_model=CaseIntakeResponse)
async def provide_additional_info(request: AdditionalInfoRequest):
    case_id = request.case_id
    if case_id not in intake_sessions:
        raise HTTPException(status_code=404, detail="Case not found")
        
    session = intake_sessions[case_id]
    case_intake = CaseIntake(**session["intake_data"])
    
    # Process with new info (this will block until agents finish)
    # Ideally should be async/streaming too, but frontend expects JSON response
    # For better UX, this could be refactored to return "processing" and let client poll or stream
    # But for now we'll wait (it might take 10-20s)
    updated_session = await process_case(case_id, case_intake, request.additional_info)
    
    return CaseIntakeResponse(**updated_session)

@router.get("/status/{case_id}", response_model=CaseIntakeResponse)
async def get_status(case_id: str):
    if case_id not in intake_sessions: raise HTTPException(status_code=404)
    return CaseIntakeResponse(**intake_sessions[case_id])

@router.post("/review/{case_id}", response_model=CaseReviewResponse)
async def submit_lawyer_review(case_id: str, request: CaseReviewRequest):
    if case_id not in intake_sessions: raise HTTPException(status_code=404)
    s = intake_sessions[case_id]
    s["lawyer_notes"] = request.lawyer_notes
    s["lawyer_decision"] = request.lawyer_decision
    s["status"] = "approved" if request.lawyer_decision == "approve" else "rejected"
    return CaseReviewResponse(case_id=case_id, intake_data=CaseIntake(**s["intake_data"]), **s)
