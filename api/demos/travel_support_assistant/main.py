"""
Travel Customer Support Assistant
==================================

🎯 LEARNING OBJECTIVES:
This demo teaches you how to build a real-world travel support assistant with function calling:

1. Function Calling - How agents use tools to access booking data
2. Tool Definition - How to create travel support tools
3. AutoGen Integration - How to build support agents with AutoGen
4. Production Patterns - How to structure tools for customer support

📚 REAL-WORLD USE CASE:
A Travel Customer Support Assistant (like Booking.com) that helps customers with:
- Booking lookups and modifications
- Hotel availability and information
- Flight status and changes
- Taxi/transportation booking
- Travel itinerary management

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Setup - Import libraries and configure the router
Step 2: Data Models - Define request structures with validation
Step 3: Support Tools - Create tools for booking data access
Step 4: Booking Tools - Create tools for hotel and taxi booking
Step 5: Agent Setup - Configure AutoGen support assistant with tools
Step 6: API Endpoints - Expose functionality via HTTP

Key Concept: This assistant solves real customer support problems by combining
AI reasoning with tools for booking data and external travel services.
"""

# ============================================================================
# STEP 1: SETUP & IMPORTS
# ============================================================================
"""
Understanding the Imports:
- FastAPI: Web framework for building APIs
- BaseModel: Provides automatic data validation
- StreamingResponse: For real-time streaming responses
- AutoGen: Framework for building conversational AI agents with tools
- asyncio: For handling async operations

Key Components:
- AssistantAgent: AutoGen agent that can use tools (function calling)
- ChatCompletionClient: Model client for LLM integration
- TextMessage: Message format for AutoGen agents
- BOOKINGS_DB: Simulated booking database (defined below)
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, AsyncGenerator
import json
import os
from datetime import datetime, timedelta
import logging
import random

from utils.llm_provider import get_provider_config

# AutoGen imports
try:
    from autogen_agentchat.agents import AssistantAgent
    from autogen_agentchat.messages import (
        TextMessage,
        ModelClientStreamingChunkEvent,
        ToolCallRequestEvent,
        ToolCallExecutionEvent,
    )
    from autogen_agentchat.base import Response
    from autogen_core import CancellationToken
    from autogen_ext.models.openai import OpenAIChatCompletionClient
    # Try to import Gemini client if available
    try:
        from autogen_ext.models.gemini import GeminiChatCompletionClient
        GEMINI_CLIENT_AVAILABLE = True
    except ImportError:
        GEMINI_CLIENT_AVAILABLE = False
        GeminiChatCompletionClient = None
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    AssistantAgent = None
    TextMessage = None
    ModelClientStreamingChunkEvent = None
    ToolCallRequestEvent = None
    ToolCallExecutionEvent = None
    Response = None
    CancellationToken = None
    ChatCompletionClient = None
    OpenAIChatCompletionClient = None
    GEMINI_CLIENT_AVAILABLE = False
    GeminiChatCompletionClient = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/travel-support", tags=["travel-support"])

# ============================================================================
# DATABASE & STATE (In-Memory Storage)
# ============================================================================
"""
In-Memory Storage for Demo:
- agent_sessions: Stores conversation sessions and message history
- BOOKINGS_DB: Simulated booking database with sample bookings

Note: This uses in-memory storage for simplicity. In production,
you'd use a persistent database (PostgreSQL, MongoDB, etc.) and
a session store (Redis, etc.) for scalability.

Database Structure:
- BOOKINGS_DB: Dictionary mapping booking_id to booking details
  Each booking contains: booking_id, customer_name, hotel, 
  check_in, check_out, status, room_type
"""
# In-memory state for demo (use database in production)
agent_sessions: Dict[str, Dict[str, Any]] = {}

# Simulated booking database (in production, this would be a real database)
BOOKINGS_DB = {
    "BK123456": {
        "booking_id": "BK123456",
        "customer_name": "John Smith",
        "hotel": "Grand Hotel Paris",
        "check_in": "2024-02-15",
        "check_out": "2024-02-18",
        "status": "confirmed",
        "room_type": "Deluxe Suite"
    },
    "BK789012": {
        "booking_id": "BK789012",
        "customer_name": "Sarah Johnson",
        "hotel": "Beach Resort Barcelona",
        "check_in": "2024-03-01",
        "check_out": "2024-03-05",
        "status": "confirmed",
        "room_type": "Ocean View"
    }
}


# ============================================================================
# STEP 2: DATA MODELS
# ============================================================================
"""
What is a Data Model?
- Defines the structure of incoming requests and responses
- Automatically validates data (type checking, required fields)
- Provides clear error messages if validation fails
- Think of it as a "contract" for what your API expects

Models:
- ChatRequest: User message and session information
- ToolCall: Information about tool execution
- ChatResponse: Assistant response with tool usage info
- SessionInfo: Session metadata and statistics
"""
class ChatRequest(BaseModel):
    """Request to chat with the travel support assistant"""
    message: str = Field(..., min_length=1, description="The user's message or question")
    session_id: Optional[str] = Field(None, description="Optional session ID for conversation continuity")


class ToolCall(BaseModel):
    """Information about a tool call"""
    tool_name: str
    arguments: Dict[str, Any]
    result: str
    timestamp: str


class ChatResponse(BaseModel):
    """Travel support assistant response with tool usage information"""
    response: str
    session_id: str
    tool_calls: List[ToolCall] = []


class SessionInfo(BaseModel):
    """Session information"""
    session_id: str
    message_count: int
    tool_call_count: int
    created_at: str


# ============================================================================
# STEP 3: SUPPORT TOOLS (Booking Data Access)
# ============================================================================
"""
What are Support Tools?
- Functions the support assistant can call to access booking data
- When a customer asks "What's my booking status?", the LLM calls lookup_booking()
- The tool queries the booking database and returns customer information
- The assistant incorporates the result into a helpful response

Tool Execution Flow:
1. Customer asks a question
2. LLM analyzes the question and decides which tool to use
3. Tool executes and queries the booking database
4. Tool returns structured data
5. LLM incorporates the data into a natural language response

Key Learning: Tools are just Python functions with:
- Type hints (for automatic schema generation)
- Docstrings (for tool descriptions)
- Return values (that the LLM can use)
"""

def lookup_booking(booking_id: str) -> str:
    """
    Looks up customer booking information by booking ID.
    
    Use this tool when the customer provides a booking ID or asks about:
    - Booking status
    - Booking details
    - Hotel information
    - Check-in/check-out dates
    
    Args:
        booking_id: The booking reference number (e.g., "BK123456")
    
    Returns:
        Booking information including hotel, dates, status, and room type
    """
    booking_id = booking_id.upper().strip()
    
    if booking_id in BOOKINGS_DB:
        booking = BOOKINGS_DB[booking_id]
        return f"""Booking Found:
- Booking ID: {booking['booking_id']}
- Customer: {booking['customer_name']}
- Hotel: {booking['hotel']}
- Check-in: {booking['check_in']}
- Check-out: {booking['check_out']}
- Status: {booking['status']}
- Room Type: {booking['room_type']}"""
    else:
        return f"Booking {booking_id} not found. Please verify your booking reference number."


def search_hotels(city: str, check_in: Optional[str] = None, check_out: Optional[str] = None) -> str:
    """
    Searches for available hotels in a city with prices and ratings.
    
    Use this tool when the customer asks about:
    - Hotel availability
    - Hotels in a specific city
    - Booking a new hotel
    
    Args:
        city: Name of the city to search
        check_in: Check-in date (optional, format: YYYY-MM-DD)
        check_out: Check-out date (optional, format: YYYY-MM-DD)
    
    Returns:
        List of available hotels with prices and ratings
    """
    # Simulated hotel database
    hotels_db = {
        "paris": [
            {"name": "Grand Hotel Paris", "price": 150, "rating": 4.5, "available": True},
            {"name": "Eiffel Tower View Hotel", "price": 200, "rating": 4.8, "available": True},
            {"name": "Champs-Élysées Boutique", "price": 120, "rating": 4.2, "available": True}
        ],
        "barcelona": [
            {"name": "Beach Resort Barcelona", "price": 180, "rating": 4.6, "available": True},
            {"name": "Gothic Quarter Hotel", "price": 140, "rating": 4.4, "available": True},
            {"name": "Sagrada Familia View", "price": 160, "rating": 4.7, "available": True}
        ],
        "london": [
            {"name": "Thames Riverside Hotel", "price": 170, "rating": 4.5, "available": True},
            {"name": "Westminster Palace Inn", "price": 190, "rating": 4.6, "available": True},
            {"name": "Covent Garden Boutique", "price": 130, "rating": 4.3, "available": True}
        ]
    }
    
    city_lower = city.lower().strip()
    
    if city_lower in hotels_db:
        hotels = hotels_db[city_lower]
        date_info = ""
        if check_in and check_out:
            date_info = f" for {check_in} to {check_out}"
        
        result = f"Available hotels in {city.title()}{date_info}:\n\n"
        for i, hotel in enumerate(hotels, 1):
            result += f"{i}. {hotel['name']}\n"
            result += f"   Price: €{hotel['price']}/night | Rating: {hotel['rating']}/5.0\n"
        
        return result
    else:
        return f"No hotels found for {city}. Available cities: Paris, Barcelona, London"


def check_flight_status(flight_number: Optional[str] = None, booking_id: Optional[str] = None) -> str:
    """
    Checks flight status including departure time, gate, and delays.
    
    Use this tool when the customer asks about:
    - Flight status
    - Flight delays
    - Flight information
    
    Args:
        flight_number: Flight number (e.g., "AA1234")
        booking_id: Booking ID to look up associated flight
    
    Returns:
        Flight status information including departure time, gate, and status
    """
    # Simulated flight status
    if booking_id and booking_id.upper() in BOOKINGS_DB:
        # Generate flight info based on booking
        flight_number = f"AA{random.randint(1000, 9999)}"
    
    if not flight_number:
        return "Please provide either a flight number or booking ID to check flight status."
    
    # Simulated flight statuses
    statuses = ["On Time", "Delayed 15 min", "Boarding", "Departed"]
    gates = ["A12", "B5", "C8", "D3"]
    
    status = random.choice(statuses)
    gate = random.choice(gates)
    departure = (datetime.now() + timedelta(hours=random.randint(1, 4))).strftime("%H:%M")
    
    return f"""Flight {flight_number.upper()} Status:
- Departure Time: {departure}
- Gate: {gate}
- Status: {status}
- Destination: Confirmed"""


# ============================================================================
# STEP 4: BOOKING TOOLS (External Travel Services)
# ============================================================================
"""
What are Booking Tools?
- Tools that interact with external travel services
- Enable the assistant to book hotels, order taxis, and modify bookings
- In production, these would connect to real hotel booking APIs, taxi services, etc.

Booking Tools for Travel Support:
- Hotel Booking: Connect to hotel reservation systems
- Taxi Services: Integrate with taxi/ride-sharing companies
- Booking Modifications: Handle cancellations and changes

Tool Execution Flow:
1. Customer requests an action (e.g., "Book a hotel")
2. LLM extracts parameters (hotel name, dates, guest name)
3. Tool executes the booking action
4. Tool updates the booking database
5. LLM confirms the booking to the customer
"""

def book_hotel(hotel_name: str, city: str, check_in: str, check_out: str, guest_name: str) -> str:
    """
    Books a hotel room and returns booking confirmation with booking ID.
    
    Use this tool when the customer wants to:
    - Book a new hotel
    - Make a hotel reservation
    - Confirm a hotel booking
    
    Args:
        hotel_name: Name of the hotel to book
        city: City where the hotel is located
        check_in: Check-in date (YYYY-MM-DD)
        check_out: Check-out date (YYYY-MM-DD)
        guest_name: Name of the guest
    
    Returns:
        Booking confirmation with booking ID
    """
    try:
        # In production, this would connect to hotel booking API
        # For demo, we simulate the booking
        
        # Generate booking ID
        booking_id = f"BK{random.randint(100000, 999999)}"
        
        # Add to bookings database
        BOOKINGS_DB[booking_id] = {
            "booking_id": booking_id,
            "customer_name": guest_name,
            "hotel": hotel_name,
            "check_in": check_in,
            "check_out": check_out,
            "status": "confirmed",
            "room_type": "Standard Room"
        }
        
        return f"""Hotel booking confirmed!

Booking Details:
- Booking ID: {booking_id}
- Hotel: {hotel_name}, {city}
- Guest: {guest_name}
- Check-in: {check_in}
- Check-out: {check_out}
- Status: Confirmed

Your booking has been processed through our hotel booking system."""
    except Exception as e:
        return f"Error booking hotel: {str(e)}. Please try again or contact support."


def book_taxi(pickup_location: str, destination: str, pickup_time: Optional[str] = None) -> str:
    """
    Books a taxi and returns confirmation with driver details and ETA.
    
    Use this tool when the customer wants to:
    - Book a taxi
    - Arrange transportation
    - Order a ride
    
    Args:
        pickup_location: Pickup address or location
        destination: Destination address or location
        pickup_time: Preferred pickup time (optional, defaults to now)
    
    Returns:
        Taxi booking confirmation with driver details and ETA
    """
    try:
        # In production, this would connect to taxi service API
        # For demo, we simulate the booking
        
        if not pickup_time:
            pickup_time = datetime.now().strftime("%H:%M")
        
        # Generate booking details
        driver_name = random.choice(["Michael", "Emma", "David", "Sophia"])
        driver_phone = f"+1-555-{random.randint(1000, 9999)}"
        eta = random.randint(5, 15)
        vehicle_type = random.choice(["Standard", "Premium", "SUV"])
        estimated_fare = random.randint(15, 50)
        
        return f"""Taxi booking confirmed!

Booking Details:
- Pickup: {pickup_location}
- Destination: {destination}
- Pickup Time: {pickup_time}
- Vehicle: {vehicle_type}
- Estimated Fare: ${estimated_fare}
- ETA: {eta} minutes

Driver Information:
- Driver: {driver_name}
- Phone: {driver_phone}

Your taxi will arrive in approximately {eta} minutes."""
    except Exception as e:
        return f"Error booking taxi: {str(e)}. Please try again or contact support."


def cancel_booking(booking_id: str, reason: Optional[str] = None) -> str:
    """
    Cancels a booking and returns cancellation confirmation with refund details.
    
    Use this tool when the customer wants to:
    - Cancel a booking
    - Request a refund
    - Modify booking dates
    
    Args:
        booking_id: Booking ID to cancel
        reason: Optional cancellation reason
    
    Returns:
        Cancellation confirmation with refund information
    """
    booking_id = booking_id.upper().strip()
    
    if booking_id in BOOKINGS_DB:
        booking = BOOKINGS_DB[booking_id]
        
        # Update status
        booking["status"] = "cancelled"
        booking["cancelled_at"] = datetime.now().isoformat()
        booking["cancellation_reason"] = reason or "Customer request"
        
        # Calculate refund (simplified)
        refund_amount = random.randint(80, 100)  # Percentage
        
        return f"""Booking cancellation processed!

Cancellation Details:
- Booking ID: {booking_id}
- Hotel: {booking['hotel']}
- Cancellation Reason: {reason or 'Customer request'}
- Refund: {refund_amount}% of booking amount
- Refund will be processed within 5-7 business days

Your booking has been successfully cancelled."""
    else:
        return f"Booking {booking_id} not found. Please verify your booking reference number."


# List of available support tools
AVAILABLE_TOOLS = [
    lookup_booking,
    search_hotels,
    check_flight_status,
    book_hotel,
    book_taxi,
    cancel_booking
]


# ============================================================================
# STEP 5: AGENT SETUP (AutoGen)
# ============================================================================
"""
What is AutoGen?
- Framework for building multi-agent conversational AI systems
- Agents can use function calling to access tools automatically
- Supports streaming and tool execution
- Production-ready for customer support applications

What is Function Calling for Travel Support?
- LLMs can decide to call functions (tools) during customer support conversations
- The LLM sees available tools and their descriptions
- When appropriate, the LLM requests a tool call
- We execute the tool and return the result
- The LLM incorporates the result into a helpful customer support response

Agent Configuration:
1. Set up LLM model client (OpenAI-compatible API)
2. Create AutoGen AssistantAgent with system message
3. Pass tools as a list to the agent
4. Agent can now use tools automatically during conversations

Key Learning: AutoGen uses:
- AssistantAgent: Main agent class
- tools parameter: List of functions (tools are auto-detected from function signatures)
- model_client: ChatCompletionClient for LLM integration
- on_messages_stream: For streaming responses
"""
def create_model_client():
    """
    Creates a model client for the AutoGen agent using the existing LLM provider utility
    
    Returns:
        ChatCompletionClient configured for the selected provider
    """
    if not AUTOGEN_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="AutoGen not available. Install with: pip install 'autogen-agentchat[openai]'"
        )
    
    try:
        # Get provider configuration
        config = get_provider_config()
        provider_name = config["provider_name"]
        
        # Use Gemini's native client if available
        if provider_name == "gemini" and GEMINI_CLIENT_AVAILABLE:
            return GeminiChatCompletionClient(
                api_key=config["api_key"],
                model=config["model"],
            )
        
        # Build AutoGen client config for OpenAI-compatible providers
        client_config = {
            "api_key": config["api_key"],
            "model": config["model"],
        }
        
        # Add base_url if provided
        if config["base_url"]:
            client_config["base_url"] = config["base_url"]
            # For non-OpenAI models, provide model_info with required fields
            # Determine family based on provider
            if provider_name == "fireworks":
                family = "llama"  # Most Fireworks models are Llama-based
            elif provider_name == "openrouter":
                family = "gpt-4o"  # Default to gpt-4o family for OpenRouter
            else:
                family = "gpt-4o"  # Default fallback
            
            client_config["model_info"] = {
                "function_calling": True,
                "json_output": False,
                "vision": False,
                "family": family,
            }
        
        return OpenAIChatCompletionClient(**client_config)
    except Exception as e:
        logger.error(f"Error creating model client: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create model client: {str(e)}"
        )


def create_agent_with_tools(session_id: str) -> AssistantAgent:
    """
    Creates an AutoGen agent with travel support tools
    
    This function:
    1. Creates a model client for LLM integration
    2. Creates an AssistantAgent with system message
    3. Passes all travel support tools to the agent
    4. Returns the configured agent
    
    Key Learning: Tools are passed as a list. AutoGen automatically:
    - Extracts function signatures and docstrings
    - Creates tool schemas for the LLM
    - Handles tool calling and execution
    """
    if not AUTOGEN_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="AutoGen not available. Install with: pip install 'autogen-agentchat[openai]'"
        )
    
    try:
        # Create model client
        model_client = create_model_client()
        
        # Create AutoGen agent with tools
        agent = AssistantAgent(
            name="travel_support_assistant",
            model_client=model_client,
            system_message="""You are a professional travel customer support assistant (like Booking.com support).
Your role is to help customers with:
- Booking lookups and status checks
- Hotel searches and reservations
- Flight status inquiries
- Taxi bookings
- Booking modifications and cancellations

Guidelines:
- Be professional, clear, and concise
- Do NOT use emojis or casual language
- Use proper formatting with clear spacing and line breaks
- Format lists and information in a structured, easy-to-read manner
- Use the available tools to access booking data and perform actions
- Always provide accurate, helpful information to customers""",
            tools=AVAILABLE_TOOLS,  # Pass tools as a list
            model_client_stream=True,  # Enable streaming
            reflect_on_tool_use=True,  # Reflect on tool results before responding
        )
        
        return agent
        
    except Exception as e:
        logger.error(f"Error setting up AutoGen agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize AutoGen agent: {str(e)}"
        )


# ============================================================================
# STEP 6: API ENDPOINTS
# ============================================================================
"""
API Endpoints:
- POST /chat/stream: Chat with the travel support assistant (streaming)
- GET /tools: List all available support tools
- GET /sessions/{session_id}: Get session information
- POST /sessions/{session_id}/clear: Clear a session
- GET /health: Health check endpoint

Streaming Chat Flow:
1. Initialize or get existing session
2. Create AutoGen agent with tools
3. Process customer message through agent
4. AutoGen handles tool calling automatically
5. Stream response with tool call information

Key Learning: AutoGen API uses:
- on_messages_stream: For streaming responses
- ModelClientStreamingChunkEvent: For text chunks
- Response: For final response with tool calls
"""
async def generate_chat_stream(
    session_id: str,
    message: str
) -> AsyncGenerator[str, None]:
    """
    Generate streaming chat response with tool usage using AutoGen
    
    This is the main support assistant execution pipeline:
    1. Initialize or get existing session
    2. Create AutoGen agent with tools
    3. Process customer message through agent
    4. Handle tool calls automatically (AutoGen handles this)
    5. Stream response with tool call information
    
    Key Learning: AutoGen's on_messages_stream:
    - Yields events as they happen (streaming chunks, tool calls, final response)
    - Handles tool execution automatically
    - Provides structured events for different message types
    """
    try:
        # Initialize session if needed
        if session_id not in agent_sessions:
            agent_sessions[session_id] = {
                "session_id": session_id,
                "messages": [],
                "tool_calls": [],
                "created_at": datetime.now().isoformat(),
                "message_count": 0,
                "tool_call_count": 0
            }
        
        session = agent_sessions[session_id]
        
        # Create agent with tools (create new agent for each request to ensure fresh state)
        agent = create_agent_with_tools(session_id)
        
        # Add current user message to session
        session["messages"].append({"role": "user", "content": message})
        session["message_count"] += 1
        
        # Track tool calls and response
        tool_calls_used = []
        final_response = ""
        
        # Process message through agent with streaming
        # AutoGen handles tool calling automatically
        async for event in agent.on_messages_stream(
            messages=[TextMessage(content=message, source="user")],
            cancellation_token=CancellationToken(),
        ):
            # Handle tool call requests (when LLM decides to call a tool)
            if isinstance(event, ToolCallRequestEvent):
                for tool_call in event.content:
                    # Extract tool call information
                    tool_name = getattr(tool_call, 'name', 'unknown')
                    tool_args = {}
                    if hasattr(tool_call, 'arguments'):
                        tool_args = tool_call.arguments
                    elif hasattr(tool_call, 'args'):
                        tool_args = tool_call.args
                    
                    tool_calls_used.append({
                        "tool_name": tool_name,
                        "arguments": tool_args if isinstance(tool_args, dict) else {},
                        "result": "",  # Will be filled when execution completes
                        "timestamp": datetime.now().isoformat()
                    })
                    # Stream tool call info
                    yield f"data: {json.dumps({'tool_calls': [tool_calls_used[-1]], 'type': 'tools'})}\n\n"
            
            # Handle tool call execution results
            elif isinstance(event, ToolCallExecutionEvent):
                for result in event.content:
                    # Extract result information
                    result_name = getattr(result, 'name', None)
                    result_content = ""
                    if hasattr(result, 'content'):
                        result_content = result.content
                    elif hasattr(result, 'result'):
                        result_content = str(result.result)
                    else:
                        result_content = str(result)
                    
                    # Find matching tool call and update result
                    if result_name:
                        for tool_call in tool_calls_used:
                            if tool_call["tool_name"] == result_name:
                                tool_call["result"] = result_content
                                break
                    # Stream updated tool call info
                    yield f"data: {json.dumps({'tool_calls': tool_calls_used, 'type': 'tools'})}\n\n"
            
            # Handle streaming text chunks
            elif isinstance(event, ModelClientStreamingChunkEvent):
                chunk = event.content
                final_response += chunk
                # Stream chunk to frontend
                yield f"data: {json.dumps({'content': chunk, 'type': 'text'})}\n\n"
            
            # Handle final response
            elif isinstance(event, Response):
                # Extract final message content
                if hasattr(event, 'chat_message') and isinstance(event.chat_message, TextMessage):
                    final_response = event.chat_message.content
                
                # Send completion with final response
                yield f"data: {json.dumps({'done': True, 'response': final_response, 'tool_calls': tool_calls_used, 'type': 'complete'})}\n\n"
        
        # Update session
        session["messages"].append({"role": "assistant", "content": final_response})
        if tool_calls_used:
            session["tool_calls"].extend(tool_calls_used)
            session["tool_call_count"] += len(tool_calls_used)
            
    except Exception as e:
        logger.error(f"Error in chat stream: {e}", exc_info=True)
        yield f"data: {json.dumps({'error': str(e), 'type': 'error'})}\n\n"


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Chat with the travel support assistant with streaming response
    
    This endpoint:
    1. Creates or uses existing session
    2. Processes customer query through assistant with tools
    3. Streams response in real-time
    4. Includes tool call information
    
    The assistant can use tools for booking lookups, hotel searches, flight status,
    hotel booking, taxi services, and booking modifications.
    """
    session_id = request.session_id or f"session_{datetime.now().timestamp()}"
    
    return StreamingResponse(
        generate_chat_stream(session_id, request.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# Example queries for each tool (matching static demo data)
TOOL_EXAMPLES = {
    'lookup_booking': 'What\'s my booking status for BK123456?',
    'search_hotels': 'Search hotels in Paris',
    'check_flight_status': 'Check flight status for AA1234',
    'book_hotel': 'Book a hotel in Barcelona for March 1-5',
    'book_taxi': 'I need a taxi from airport to Grand Hotel Paris',
    'cancel_booking': 'Cancel my booking BK123456',
}

@router.get("/tools")
async def list_tools():
    """List all available support tools with examples"""
    tools_info = []
    for tool_func in AVAILABLE_TOOLS:
        tool_name = tool_func.__name__
        tools_info.append({
            "name": tool_name,
            "description": tool_func.__doc__ or f"Tool: {tool_name}",
            "example": TOOL_EXAMPLES.get(tool_name, ""),
        })
    
    return {
        "tools": tools_info,
        "autogen_available": AUTOGEN_AVAILABLE
    }


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session information"""
    if session_id not in agent_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = agent_sessions[session_id]
    return SessionInfo(
        session_id=session_id,
        message_count=session["message_count"],
        tool_call_count=session["tool_call_count"],
        created_at=session["created_at"]
    )


@router.post("/sessions/{session_id}/clear")
async def clear_session(session_id: str):
    """Clear a session"""
    if session_id in agent_sessions:
        agent_sessions[session_id] = {
            "session_id": session_id,
            "messages": [],
            "tool_calls": [],
            "created_at": datetime.now().isoformat(),
            "message_count": 0,
            "tool_call_count": 0
        }
        return {"message": "Session cleared"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "travel-support",
        "autogen_available": AUTOGEN_AVAILABLE,
        "tools_count": len(AVAILABLE_TOOLS)
    }


# ============================================================================
# LEARNING CHECKLIST
# ============================================================================
"""
After reading this code, you should understand:

✓ How to build a real-world travel support assistant with tools
✓ How function calling works for customer support use cases
✓ How to structure production-ready support assistant APIs
✓ How streaming works with support tool calls
✓ How to use AutoGen for building agents with tools

Key Concepts:
- Support Tools: Functions that access booking data and customer information
- Function Calling: LLM decides when to use support tools automatically
- AutoGen: Framework for building multi-agent customer support AI applications
- AssistantAgent: AutoGen agent class with built-in tool support

Real-World Applications:
- Booking lookups and customer service
- Hotel availability and reservations
- Flight status and travel information
- Taxi and transportation booking
- Booking modifications and cancellations

Next Steps:
1. Add more support tools (payment processing, loyalty programs, etc.)
2. Integrate real hotel booking APIs and taxi services
3. Add tool result caching for performance
4. Implement support analytics and usage tracking
5. Add authentication and rate limiting for production use

Questions to Consider:
- How would you handle tool errors in a customer support context?
- What security considerations exist for booking tool execution?
- How would you rate limit tool usage for customer support?
- How could you add tool result caching for frequently accessed bookings?
- What monitoring and analytics would you add for support insights?
"""
