"""
Restaurant Booking Voice AI
===========================

🎯 LEARNING OBJECTIVES:
This demo teaches you how to build a voice-enabled AI agent for restaurant bookings:

1. LiveKit Integration - How to connect voice AI agents to real-time audio
2. Token Generation - How to create secure JWT tokens for LiveKit connections
3. Voice Agent Architecture - How voice agents work separately from the API
4. Real-time Audio - How speech-to-text and text-to-speech work in voice AI
5. Tool Calling - How agents use tools to perform actions (add items, view menu)

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Setup - Import libraries and configure the router
Step 2: Data Models - Define request structures with validation
Step 3: Menu Data - Simple restaurant menu structure
Step 4: Token Generation - Create LiveKit access tokens
Step 5: API Endpoints - Expose functionality via HTTP

Key Concept: Voice AI agents use LiveKit to handle real-time audio streaming.
The agent runs separately as a worker process and connects to LiveKit rooms,
while the frontend connects to the same room to enable voice conversations.
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

# LiveKit SDK for token generation
try:
    from livekit import api
except ImportError:
    api = None

# Create a router - groups all endpoints under /restaurant-booking
router = APIRouter(prefix="/restaurant-booking", tags=["restaurant-booking"])


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
- MenuResponse: Returns available menu items
- ServiceInfo: Health check information
"""
class ConnectionRequest(BaseModel):
    """Defines what data we need to connect to voice room"""
    participant_name: Optional[str] = "Customer"


class ConnectionResponse(BaseModel):
    """LiveKit connection details returned to frontend"""
    server_url: str
    room_name: str
    participant_name: str
    participant_token: str


class MenuResponse(BaseModel):
    """Menu items response"""
    menu: dict
    categories: list[str]


class ServiceInfo(BaseModel):
    """Health check response"""
    status: str
    service: str
    description: str


# ============================================================================
# STEP 3: MENU DATA
# ============================================================================
"""
Simple Restaurant Menu:
This is a simplified menu structure for the restaurant booking demo.
In a real application, this would come from a database.

The menu is organized by categories:
- appetizers: Starter items
- mains: Main course dishes
- desserts: Sweet treats
- drinks: Beverages

Each item has:
- id: Unique identifier
- name: Display name
- description: Item description
- price: Price in USD
"""
RESTAURANT_MENU = {
    "appetizers": [
        {
            "id": "app_001",
            "name": "Caesar Salad",
            "description": "Fresh romaine lettuce with Caesar dressing",
            "price": 8.99
        },
        {
            "id": "app_002",
            "name": "Bruschetta",
            "description": "Toasted bread with tomatoes, garlic, and basil",
            "price": 7.99
        },
        {
            "id": "app_003",
            "name": "Mozzarella Sticks",
            "description": "Breaded mozzarella with marinara sauce",
            "price": 6.99
        }
    ],
    "mains": [
        {
            "id": "main_001",
            "name": "Grilled Salmon",
            "description": "Fresh salmon with lemon butter sauce and vegetables",
            "price": 22.99
        },
        {
            "id": "main_002",
            "name": "Ribeye Steak",
            "description": "12oz ribeye with mashed potatoes and asparagus",
            "price": 28.99
        },
        {
            "id": "main_003",
            "name": "Pasta Carbonara",
            "description": "Creamy pasta with bacon and parmesan",
            "price": 16.99
        },
        {
            "id": "main_004",
            "name": "Margherita Pizza",
            "description": "Classic pizza with tomato, mozzarella, and basil",
            "price": 14.99
        }
    ],
    "desserts": [
        {
            "id": "dess_001",
            "name": "Chocolate Lava Cake",
            "description": "Warm chocolate cake with vanilla ice cream",
            "price": 7.99
        },
        {
            "id": "dess_002",
            "name": "Tiramisu",
            "description": "Classic Italian dessert with coffee and mascarpone",
            "price": 6.99
        }
    ],
    "drinks": [
        {
            "id": "drink_001",
            "name": "Coca Cola",
            "description": "Classic cola",
            "price": 2.99
        },
        {
            "id": "drink_002",
            "name": "Iced Tea",
            "description": "Freshly brewed iced tea",
            "price": 2.99
        },
        {
            "id": "drink_003",
            "name": "Orange Juice",
            "description": "Fresh squeezed orange juice",
            "price": 3.99
        }
    ]
}


# ============================================================================
# STEP 4: TOKEN GENERATION
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
    return f"restaurant_{''.join(secrets.choice(alphabet) for _ in range(8))}"


def generate_participant_identity() -> str:
    """Generate a unique participant identity"""
    return f"customer_{secrets.token_hex(4)}"


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
# STEP 5: API ENDPOINTS
# ============================================================================
"""
What is an API Endpoint?
- A URL that clients can call to access functionality
- Each endpoint does one specific thing
- Uses HTTP methods (GET, POST, etc.) to indicate the action

Endpoint Design Principles:
1. Clear naming (/connection, /menu, /health)
2. Single responsibility (each endpoint does one thing)
3. Proper HTTP methods (POST for creating, GET for reading)
4. Meaningful responses (status codes, clear data)

Understanding the Code Flow:
POST /restaurant-booking/connection
  → Validates request (automatic via Pydantic)
  → Generates unique room name and participant identity
  → Creates LiveKit access token
  → Returns connection details
  → Frontend connects to LiveKit room
  → Agent connects to same room (runs separately)
  → Voice conversation begins
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
    a voice conversation with the restaurant booking agent.
    
    The agent itself runs separately (see restaurant_agent.py) and
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
        participant_name = request.participant_name.strip() if request.participant_name else "Customer"
        
        if not participant_name or len(participant_name) < 2:
            raise HTTPException(
                status_code=400,
                detail="Please provide a valid name (at least 2 characters)"
            )
        
        # Create access token
        participant_token = create_access_token(room_name, participant_identity, participant_name)
        
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


@router.get("/menu", response_model=MenuResponse)
async def get_menu():
    """
    Returns available menu items
    
    This is used by the frontend to display the menu and by the
    agent to understand what items are available.
    """
    return MenuResponse(
        menu=RESTAURANT_MENU,
        categories=list(RESTAURANT_MENU.keys())
    )


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
        service="restaurant-booking",
        description="Voice AI restaurant booking system with LiveKit integration"
    )


@router.get("/learning-objectives")
async def get_learning_objectives():
    """Get learning objectives for this demo"""
    return {
        "demo": "Restaurant Booking Voice AI",
        "objectives": [
            "Understand LiveKit integration for real-time voice AI",
            "Learn how to create conversational voice agents",
            "Implement tool calling for agent actions (order items, view menu)",
            "Build state management for conversation context",
            "Create real-time audio streaming with speech-to-text and text-to-speech"
        ],
        "technologies": [
            "LiveKit",
            "Voice AI",
            "Real-time Audio",
            "Speech-to-Text",
            "Text-to-Speech",
            "Tool Calling"
        ],
        "concepts": [
            "Voice Agents",
            "Real-time Audio Streaming",
            "Conversational AI",
            "State Management",
            "LiveKit Rooms"
        ]
    }


# ============================================================================
# LEARNING CHECKLIST
# ============================================================================
"""
After reading this code, you should understand:

✓ How LiveKit token generation works
✓ How to create secure room connections
✓ How to structure menu data for voice agents
✓ How to build API endpoints for voice AI demos
✓ How the frontend and agent connect via LiveKit rooms

Next Steps:
1. Set up LiveKit server (cloud or self-hosted)
2. Create the restaurant agent (restaurant_agent.py)
3. Build the frontend connection component
4. Test the voice conversation flow
5. Add more menu items and order management features

Questions to Consider:
- How would you handle multiple concurrent orders?
- How would you persist order history?
- What happens if the agent disconnects?
- How would you add payment processing?
- How could you integrate with a POS system?

Key Voice AI Concepts:
- STT (Speech-to-Text): Converts user speech to text
- TTS (Text-to-Speech): Converts agent responses to speech
- VAD (Voice Activity Detection): Detects when user is speaking
- Turn Detection: Manages conversation flow and interruptions
- Tool Calling: Allows agents to perform actions (add items to order)
"""

