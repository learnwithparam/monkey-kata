"""
Form Data Collection Voice Agent
=================================

🎯 LEARNING OBJECTIVES:
This demo teaches you how to build a voice agent that collects form data:

1. Voice Data Collection - How to collect form data via voice conversation
2. Structured Data Extraction - How to extract structured data from conversation
3. Form Field Detection - How to identify what form fields are needed
4. Data Validation - How to validate collected data before form filling

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Setup - Import libraries and load environment variables
Step 2: Data Collection State - Track collected form data
Step 3: Agent Instructions - Build prompts for data collection
Step 4: Agent Class - Configure STT, TTS, LLM
Step 5: Entrypoint - Connect agent to LiveKit rooms

Key Concept: This voice agent collects form data through natural conversation,
then the collected data is used to fill the form using browser automation.
"""

# ============================================================================
# STEP 1: SETUP & IMPORTS
# ============================================================================
from dotenv import load_dotenv
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import json
import httpx
import os
import asyncio

from livekit.agents import (
    JobContext,
    WorkerOptions,
    cli,
    function_tool,
)
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram, silero

from utils.livekit_utils import get_livekit_llm

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Fix for LiveKit pickling error when logging errors with unpicklable objects
_original_makeRecord = logging.Logger.makeRecord

def _safe_makeRecord(self, *args, **kwargs):
    """Sanitize extra dict to prevent pickling errors"""
    if 'extra' in kwargs and kwargs['extra']:
        extra = kwargs['extra']
        sanitized_extra = {}
        for key, value in extra.items():
            if isinstance(value, Exception):
                sanitized_extra[key] = f"{type(value).__name__}: {str(value)}"
            elif hasattr(value, '__class__'):
                class_name = value.__class__.__name__
                if 'MultiDict' in class_name or 'CIMultiDict' in class_name:
                    try:
                        sanitized_extra[key] = dict(value.items()) if hasattr(value, 'items') else str(value)
                    except:
                        sanitized_extra[key] = f"<{class_name}>"
                else:
                    try:
                        import pickle
                        pickle.dumps(value)
                        sanitized_extra[key] = value
                    except (TypeError, AttributeError, pickle.PicklingError):
                        try:
                            sanitized_extra[key] = str(value)
                        except:
                            sanitized_extra[key] = f"<{class_name}>"
            else:
                sanitized_extra[key] = value
        kwargs['extra'] = sanitized_extra
    return _original_makeRecord(self, *args, **kwargs)

logging.Logger.makeRecord = _safe_makeRecord


# ============================================================================
# STEP 2: DATA COLLECTION STATE
# ============================================================================
@dataclass
class FormDataState:
    """Tracks collected form data during voice conversation"""
    url: Optional[str] = None
    form_data: Dict[str, str] = field(default_factory=dict)
    collection_complete: bool = False

# Module-level storage for room name (similar to restaurant agent's order_items)
# Store current room name for tools to access
_current_room_name: Optional[str] = None


# ============================================================================
# STEP 3: AGENT INSTRUCTIONS
# ============================================================================
def build_instructions() -> str:
    """Build agent instructions for collecting B2B demo booking form data via voice"""
    return """You are a sales representative for CrispDream CRM, a leading SaaS CRM platform that helps businesses manage customer relationships, automate sales processes, and grow their revenue.

Your role is to have a natural conversation with potential customers to understand their needs and collect information for booking a personalized demo.

CONVERSATION FLOW:
1. Start by greeting them warmly and introducing yourself as a CrispDream CRM sales rep
2. Ask what they're looking for or what challenges they're facing with their current CRM or customer management
3. Listen to their needs and show genuine interest
4. Based on their needs, explain how CrispDream CRM can help them
5. Then naturally transition to collecting their information for a personalized demo

INFORMATION TO COLLECT (in a natural flow, not as a checklist):
- Company Name - Their company name
- Full Name - Their name
- Email Address - Their email for follow-up
- Phone Number - Contact number
- Company Size - Number of employees (ask naturally: "How many people are on your team?")
- Job Title - Their role (ask: "What's your role at the company?")
- Use Case - What they want to use CrispDream for (you'll learn this from the initial conversation)
- Message/Comments - Any additional information they share

IMPORTANT - FORM UPDATES:
- When the customer provides ANY information (name, email, phone, company name, etc.), IMMEDIATELY use the update_form_field or update_multiple_form_fields tool to save it
- Update the form in real-time as you collect information - don't wait until the end
- For example, if they say "My name is John Smith", immediately call update_form_field(field_name="full_name", field_value="John Smith")
- If they say "My email is john@acme.com", immediately call update_form_field(field_name="email", field_value="john@acme.com")
- If they provide multiple pieces of information at once, use update_multiple_form_fields with all the fields
- This ensures the form on their screen updates in real-time as you talk

GUIDELINES:
- Be warm, professional, and genuinely helpful - like a real sales rep from a successful SaaS company
- Start by understanding their needs, not immediately asking for information
- Make the conversation feel natural, not like filling out a form
- Show enthusiasm about how CrispDream can solve their specific challenges
- Ask follow-up questions based on what they tell you
- Once you understand their needs and they seem interested, then say something like "Great! Let me get your details so I can set up a personalized demo for you"
- Collect information naturally as part of the conversation flow
- ALWAYS use the tools to update form fields immediately when information is provided
- Confirm information when provided
- At the end, summarize what you learned about their needs and confirm their details

CRITICAL: Your responses will be spoken aloud by a text-to-speech system. You MUST:
- Output ONLY plain natural English text - NO markdown formatting whatsoever
- NO asterisks, underscores, backticks, or any markdown syntax
- NO bullet points, numbered lists, or formatting characters
- Write exactly as you would speak in a natural conversation
- Use contractions naturally (I'll, you're, we've)
- Speak conversationally, not robotically
- Keep responses SHORT - maximum 2-3 sentences for voice conversation

Remember: You're representing CrispDream CRM, a professional SaaS company. Be confident, helpful, and make the customer feel valued.
"""


# ============================================================================
# STEP 4: AGENT CLASS
# ============================================================================
async def send_form_data_to_api(room_name: str, form_data: Dict[str, str]):
    """Send collected form data to the API endpoint"""
    api_url = os.getenv("API_URL", "http://localhost:8000")
    endpoint = f"{api_url}/web-form-filling/voice-data"
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                endpoint,
                json={
                    "room_name": room_name,
                    "form_data": form_data
                }
            )
            if response.status_code == 200:
                logger.info(f"Successfully sent form data for room {room_name}")
            else:
                logger.warning(f"Failed to send form data: {response.status_code} - {response.text}")
    except Exception as e:
        logger.warning(f"Error sending form data to API: {e}")


@function_tool()
async def update_form_field(
    field_name: str,
    field_value: str
) -> str:
    """
    Update a form field with collected information.
    
    Use this tool when you have collected information from the customer.
    The form field will be updated in real-time on the customer's screen.
    
    Args:
        field_name: The name of the form field (e.g., "company_name", "email", "phone", "full_name", "company_size", "job_title", "use_case", "message")
        field_value: The value to set for this field
    
    Returns:
        Confirmation message
    """
    # Get room name from module-level storage (set in entrypoint, like restaurant agent pattern)
    if not _current_room_name:
        return "Error: Room name not available. Cannot update form field."
    
    room_name = _current_room_name
    
    # Map field names to API format
    field_mapping = {
        "company_name": "company_name",
        "company": "company_name",
        "email": "email",
        "email_address": "email",
        "phone": "phone",
        "phone_number": "phone",
        "full_name": "full_name",
        "name": "full_name",
        "company_size": "company_size",
        "size": "company_size",
        "employees": "company_size",
        "job_title": "job_title",
        "title": "job_title",
        "role": "job_title",
        "use_case": "use_case",
        "use case": "use_case",
        "message": "message",
        "comments": "message",
        "comment": "message",
    }
    
    # Normalize field name
    normalized_field = field_mapping.get(field_name.lower(), field_name.lower())
    
    # Send to API
    form_data = {normalized_field: field_value}
    await send_form_data_to_api(room_name, form_data)
    
    return f"Updated {normalized_field} field with: {field_value}"


@function_tool()
async def update_multiple_form_fields(
    company_name: Optional[str] = None,
    full_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    company_size: Optional[str] = None,
    job_title: Optional[str] = None,
    use_case: Optional[str] = None,
    message: Optional[str] = None,
) -> str:
    """
    Update multiple form fields at once with collected information.
    
    Use this tool when you have collected multiple pieces of information from the customer.
    All specified fields will be updated in real-time on the customer's screen.
    
    Args:
        company_name: Company name
        full_name: Full name of the contact person
        email: Email address
        phone: Phone number
        company_size: Company size (e.g., "1-10", "11-50", "51-200", "201-500", "500+")
        job_title: Job title or role
        use_case: What they want to use CrispDream for
        message: Additional comments or questions
    
    Returns:
        Confirmation message listing all updated fields
    """
    # Get room name from module-level storage (set in entrypoint, like restaurant agent pattern)
    if not _current_room_name:
        return "Error: Room name not available. Cannot update form fields."
    
    room_name = _current_room_name
    
    # Build form data dict with only non-None values
    form_data = {}
    updated_fields = []
    
    if company_name:
        form_data["company_name"] = company_name
        updated_fields.append("company_name")
    if full_name:
        form_data["full_name"] = full_name
        updated_fields.append("full_name")
    if email:
        form_data["email"] = email
        updated_fields.append("email")
    if phone:
        form_data["phone"] = phone
        updated_fields.append("phone")
    if company_size:
        form_data["company_size"] = company_size
        updated_fields.append("company_size")
    if job_title:
        form_data["job_title"] = job_title
        updated_fields.append("job_title")
    if use_case:
        form_data["use_case"] = use_case
        updated_fields.append("use_case")
    if message:
        form_data["message"] = message
        updated_fields.append("message")
    
    if not form_data:
        return "No fields to update. Please provide at least one field value."
    
    # Send to API
    await send_form_data_to_api(room_name, form_data)
    
    return f"Updated form fields: {', '.join(updated_fields)}"


class FormDataCollectionAgent(Agent):
    """
    Voice agent that collects form data through conversation.
    
    This agent:
    - Connects to LiveKit rooms when users join
    - Listens to user speech (STT)
    - Collects form URL and field data through conversation
    - Processes requests and generates responses (LLM)
    - Speaks responses naturally (TTS)
    - Uses tools to update form fields in real-time as data is collected
    """
    
    def __init__(self) -> None:
        super().__init__(
            instructions=build_instructions(),
            stt=deepgram.STTv2(model="flux-general-en", eager_eot_threshold=0.3),
            llm=get_livekit_llm(),
            tts=deepgram.TTS(model="aura-asteria-en"),
            vad=silero.VAD.load(),
            tools=[update_form_field, update_multiple_form_fields],
        )


# ============================================================================
# STEP 5: ENTRYPOINT
# ============================================================================
async def entrypoint(ctx: JobContext):
    """
    Main entrypoint for the form data collection agent.
    
    This function:
    1. Checks if room name matches web form pattern
    2. Connects to the LiveKit room
    3. Creates FormDataState to track collected data
    4. Creates AgentSession
    5. Starts session with FormDataCollectionAgent
    """
    # Only handle rooms with "form_" prefix
    if not ctx.room.name.startswith("form_"):
        logger.info(f"Ignoring room {ctx.room.name} - not a form filling room")
        return
    
    # Store room name for tools to access (similar to restaurant agent's order_items pattern)
    global _current_room_name
    _current_room_name = ctx.room.name
    
    # Connect to the room
    await ctx.connect()
    
    # Create agent session and start the agent
    session = AgentSession()
    agent = FormDataCollectionAgent()
    await session.start(
        agent=agent,
        room=ctx.room
    )


# ============================================================================
# WORKER CONFIGURATION
# ============================================================================
if __name__ == "__main__":
    # Register with explicit agent name for explicit dispatch (prevents conflicts with other agents)
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name="form-agent"))

