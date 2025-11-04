"""
Medical Office Triage Voice AI
===============================

🎯 LEARNING OBJECTIVES:
This demo teaches you how to build a multi-agent voice AI system:

1. Multi-Agent Architecture - How to create multiple specialized agents
2. Agent-to-Agent Transfer - How to transfer between agents with context preservation
3. Context Preservation - How to maintain conversation history across transfers
4. Voice Agent Coordination - How agents coordinate to handle complex workflows
5. Specialized Agent Roles - How to create agents with distinct responsibilities

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Setup - Import libraries and configure the router
Step 2: Data Models - Define request structures with validation
Step 3: Token Generation - Create LiveKit access tokens
Step 4: API Endpoints - Expose functionality via HTTP

Key Concept: Multi-agent systems use multiple specialized agents that can transfer
between each other while preserving conversation context. This enables complex
workflows where different agents handle different aspects of a conversation.
"""

# ============================================================================
# STEP 1: SETUP & IMPORTS
# ============================================================================
"""
Understanding the Imports:
- FastAPI: Web framework for building APIs
- BaseModel: Provides automatic data validation
- timedelta: For token expiration times
- os: Access to environment variables
- secrets: Cryptographically secure random generation
- string: String constants for random generation
- livekit.api: SDK for generating secure JWT tokens
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import timedelta
import os
import secrets
import string
import logging

# LiveKit SDK for token generation and agent dispatch
try:
    from livekit import api
except ImportError:
    api = None

logger = logging.getLogger(__name__)

# Create a router - groups all endpoints under /medical-office-triage
router = APIRouter(prefix="/medical-office-triage", tags=["medical-office-triage"])


# ============================================================================
# STEP 2: DATA MODELS (Request Validation)
# ============================================================================
"""
What is a Data Model?
- Defines the structure of incoming requests
- Automatically validates data (type checking, required fields)
- Provides clear error messages if validation fails
- Think of it as a "contract" for what your API expects

Models:
- ConnectionRequest: User info for connecting to voice room
- ConnectionResponse: Returns LiveKit connection details
- ServiceInfo: Health check information
"""
class ConnectionRequest(BaseModel):
    """Defines what data we need to connect to voice room"""
    participant_name: Optional[str] = "Patient"


class ConnectionResponse(BaseModel):
    """LiveKit connection details returned to frontend"""
    server_url: str
    room_name: str
    participant_name: str
    participant_token: str


class ServiceInfo(BaseModel):
    """Health check response"""
    status: str
    service: str
    description: str


# ============================================================================
# STEP 3: TOKEN GENERATION
# ============================================================================
"""
What is LiveKit Token Generation?
- LiveKit uses JWT tokens to authenticate connections
- Each user needs a unique token to join a room
- Tokens include permissions (can publish audio, can subscribe, etc.)
- Tokens expire after a set time (15 minutes default)

How It Works:
1. Generate a unique room name for this session
2. Create a participant identity (unique user identifier)
3. Generate a JWT token with room permissions
4. Return connection details to frontend

The frontend uses these details to connect to LiveKit and start voice conversation.
"""
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
    
    This function:
    1. Gets LiveKit credentials from environment variables
    2. Creates a token with room permissions
    3. Sets token expiration (15 minutes)
    4. Returns JWT token string
    """
    # Get LiveKit credentials from environment
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    
    if not api_key or not api_secret:
        raise HTTPException(
            status_code=500,
            detail="LiveKit credentials not configured. Please set LIVEKIT_API_KEY and LIVEKIT_API_SECRET environment variables."
        )
    
    # Use LiveKit SDK if available
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


# ============================================================================
# STEP 4: API ENDPOINTS
# ============================================================================
"""
What is an API Endpoint?
- A URL that clients can call to access functionality
- Each endpoint does one specific thing
- Uses HTTP methods (GET, POST, etc.) to indicate the action

Endpoint Design Principles:
1. Clear naming (/connection, /health)
2. Single responsibility (each endpoint does one thing)
3. Proper HTTP methods (POST for creating, GET for reading)
4. Meaningful responses (status codes, clear data)

Understanding the Code Flow:
POST /medical-office-triage/connection
  → Validates request (automatic via Pydantic)
  → Generates unique room name and participant identity
  → Creates LiveKit access token
  → Returns connection details
  → Frontend connects to LiveKit room
  → Multi-agent system connects to same room (runs separately)
  → Voice conversation begins with Triage Agent
"""
@router.post("/connection", response_model=ConnectionResponse)
async def get_connection(request: ConnectionRequest):
    """
    Main endpoint: Generates LiveKit connection token for voice AI agent
    
    This endpoint:
    1. Generates a unique room name for this session
    2. Creates a participant identity
    3. Generates a secure LiveKit access token
    4. Returns connection details (server URL, room name, token)
    
    The frontend uses these details to connect to LiveKit and start
    a voice conversation with the medical office triage system.
    
    The agent system runs separately (see triage_agent.py) and
    automatically connects to the same room when a participant joins.
    """
    try:
        # Get LiveKit server URL from environment
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
        
        # Generate unique session identifiers
        room_name = generate_room_name()
        participant_identity = generate_participant_identity()
        participant_name = request.participant_name.strip() if request.participant_name else "Patient"
        
        if not participant_name or len(participant_name) < 2:
            raise HTTPException(
                status_code=400,
                detail="Please provide a valid name (at least 2 characters)"
            )
        
        # Create access token
        participant_token = create_access_token(room_name, participant_identity, participant_name)
        
        # Explicitly dispatch the medical triage agent to this room (following survey-agent pattern)
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
            # Log error but don't fail the connection
            import logging
            logger = logging.getLogger(__name__)
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
    """
    Health check endpoint
    
    Useful for:
    - Monitoring system status
    - Load balancer checks
    - Debugging connection issues
    
    Returns:
        Service status information
    """
    return ServiceInfo(
        status="healthy",
        service="medical-office-triage",
        description="Multi-agent voice AI medical office triage system with LiveKit integration"
    )


@router.get("/learning-objectives")
async def get_learning_objectives():
    """Get learning objectives for this demo"""
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


# ============================================================================
# LEARNING CHECKLIST
# ============================================================================
"""
After reading this code, you should understand:

✓ How LiveKit token generation works
✓ How to create secure room connections
✓ How to structure API endpoints for multi-agent voice AI demos
✓ How the frontend and agent system connect via LiveKit rooms

Next Steps:
1. Set up LiveKit server (cloud or self-hosted)
2. Create the triage agent system (triage_agent.py)
3. Build the frontend connection component
4. Test the multi-agent voice conversation flow
5. Experiment with agent transfers and context preservation

Questions to Consider:
- How would you handle multiple concurrent patient calls?
- How would you persist conversation history across sessions?
- What happens if an agent disconnects during transfer?
- How would you add more specialized agents?
- How could you integrate with a patient management system?

Key Multi-Agent Concepts:
- Agent Specialization: Each agent has a specific role and expertise
- Context Preservation: Conversation history maintained across transfers
- Agent Transfer: Seamless handoff between agents
- Coordination: Agents work together to handle complex workflows
"""

