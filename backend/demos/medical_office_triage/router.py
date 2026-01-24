from fastapi import APIRouter, HTTPException
from datetime import timedelta
import os
import secrets
import string
import logging

try:
    from livekit import api
except ImportError:
    api = None

from .models import ConnectionRequest, ConnectionResponse, ServiceInfo

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/medical-office-triage", tags=["medical-office-triage"])

def generate_room_name() -> str:
    """Generate a unique room name"""
    alphabet = string.ascii_uppercase + string.digits
    return f"medical_{''.join(secrets.choice(alphabet) for _ in range(8))}"


def generate_participant_identity() -> str:
    """Generate a unique participant identity"""
    return f"patient_{secrets.token_hex(4)}"


def create_access_token(room_name: str, participant_identity: str, participant_name: str) -> str:
    """
    Create a LiveKit access token for joining a room
    """
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    
    if not api_key or not api_secret:
        raise HTTPException(
            status_code=500,
            detail="LiveKit credentials not configured. Please set LIVEKIT_API_KEY and LIVEKIT_API_SECRET environment variables."
        )
    
    if api is None:
        raise HTTPException(
            status_code=500,
            detail="LiveKit SDK not installed. Install with: pip install livekit"
        )
    
    try:
        token = api.AccessToken(api_key, api_secret) \
            .with_identity(participant_identity) \
            .with_name(participant_name) \
            .with_grants(api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )) \
            .with_ttl(timedelta(minutes=15))
        
        return token.to_jwt()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create LiveKit token: {str(e)}"
        )

@router.post("/connection", response_model=ConnectionResponse)
async def get_connection(request: ConnectionRequest):
    """
    Main endpoint: Generates LiveKit connection token for voice AI agent
    """
    try:
        server_url = os.getenv("LIVEKIT_URL")
        
        if not server_url:
            raise HTTPException(
                status_code=500,
                detail="LIVEKIT_URL environment variable not set. Please configure your LiveKit server URL in .env file."
            )
        
        if "wss://" not in server_url and "ws://" not in server_url:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid LIVEKIT_URL: '{server_url}'. Must be a WebSocket URL (wss:// or ws://)"
            )
        
        room_name = generate_room_name()
        participant_identity = generate_participant_identity()
        participant_name = request.participant_name.strip() if request.participant_name else "Patient"
        
        if not participant_name or len(participant_name) < 2:
            raise HTTPException(
                status_code=400,
                detail="Please provide a valid name (at least 2 characters)"
            )
        
        participant_token = create_access_token(room_name, participant_identity, participant_name)
        
        try:
            if api:
                lk_api = api.LiveKitAPI(
                    url=server_url.replace("wss://", "https://").replace("ws://", "http://"),
                    api_key=os.getenv("LIVEKIT_API_KEY"),
                    api_secret=os.getenv("LIVEKIT_API_SECRET"),
                )
                dispatch = await lk_api.agent_dispatch.create_dispatch(
                    api.CreateAgentDispatchRequest(
                        agent_name="medical-triage-agent",
                        room=room_name,
                        metadata='{"demo": "medical-office-triage"}'
                    )
                )
                logger.info(f"Created dispatch for medical-triage-agent in room {room_name}: {dispatch}")
                await lk_api.aclose()
        except Exception as e:
            logger.warning(f"Failed to dispatch medical triage agent: {e}")
        
        return ConnectionResponse(
            server_url=server_url,
            room_name=room_name,
            participant_name=participant_name,
            participant_token=participant_token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Error creating connection: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


@router.get("/health", response_model=ServiceInfo)
async def health_check():
    """ Health check endpoint """
    return ServiceInfo(
        status="healthy",
        service="medical-office-triage",
        description="Multi-agent voice AI medical office triage system with LiveKit integration"
    )


@router.get("/learning-objectives")
async def get_learning_objectives():
    """ Get learning objectives for this demo """
    return {
        "demo": "Medical Office Triage Voice AI",
        "objectives": [
            "Understand multi-agent architecture for complex voice AI systems",
            "Learn how to create specialized agents with distinct roles",
            "Implement agent-to-agent transfer with context preservation",
            "Build conversation history management across agent transfers",
            "Create coordinated workflows with multiple voice agents"
        ],
        "technologies": [
            "LiveKit",
            "Multi-Agent Systems",
            "Voice AI",
            "Real-time Audio",
            "Context Preservation",
            "Agent Coordination"
        ],
        "concepts": [
            "Multi-Agent Architecture",
            "Agent Transfer",
            "Context Preservation",
            "Specialized Agents",
            "LiveKit Rooms",
            "Conversation History Management"
        ]
    }
