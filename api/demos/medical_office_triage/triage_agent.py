"""
Medical Office Triage Voice Agent System
=========================================

🎯 LEARNING OBJECTIVES:
This demo teaches you how to build a multi-agent voice AI system:

1. Multi-Agent Architecture - How to create multiple specialized agents
2. Agent-to-Agent Transfer - How to transfer between agents seamlessly
3. Context Preservation - How to maintain conversation history across transfers
4. Specialized Agent Roles - How to create agents with distinct responsibilities
5. Chat History Management - How to truncate and preserve relevant context
6. Shared State Management - How to share data across agent transfers

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Setup - Import libraries and load environment variables
Step 2: UserData - Define shared state structure
Step 3: BaseAgent - Common functionality for all agents
Step 4: Specialized Agents - TriageAgent, SupportAgent, BillingAgent
Step 5: Entrypoint - Initialize and connect all agents to LiveKit rooms

Key Concept: Multi-agent systems use multiple specialized agents that can transfer
between each other while preserving conversation context. This enables complex
workflows where different agents handle different aspects of a conversation.
"""

# ============================================================================
# STEP 1: SETUP & IMPORTS
# ============================================================================
"""
Understanding the Imports:
- dotenv: Loads environment variables from .env file
- logging: For debugging and monitoring agent behavior
- dataclasses: For structured data storage
- livekit.agents: Core LiveKit agents framework
- livekit.agents.voice: Voice-specific agent components
- livekit.plugins: Provider plugins for STT, TTS, LLM
- utils: Local utility for loading prompts from YAML files

💡 Why Multi-Agent Systems?
Multi-agent systems allow you to:
1. Create specialized agents for different tasks (triage, support, billing)
2. Transfer conversations between agents seamlessly
3. Preserve context across transfers
4. Handle complex workflows with multiple steps
5. Scale by adding new specialized agents
"""
import logging
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, AgentSession, RunContext
from livekit.plugins import deepgram, silero
from utils.livekit_utils import get_livekit_llm
from prompt_utils import load_prompt

logger = logging.getLogger("medical-office-triage")
logger.setLevel(logging.INFO)

load_dotenv()


# ============================================================================
# UTILITY: MARKDOWN STRIPPING
# ============================================================================
"""
Utility function to strip markdown formatting from text.

This is a safety measure to ensure that even if the LLM outputs markdown
despite instructions, it will be removed before being spoken by TTS.

Voice agents should always output plain natural English, never markdown.
"""
import re

def strip_markdown(text: str) -> str:
    """
    Remove markdown formatting from text to ensure plain natural speech.
    
    Removes:
    - Markdown headers (# ## ###)
    - Bold/italic (*text* **text**)
    - Code blocks (```code```)
    - Inline code (`code`)
    - Links ([text](url))
    - Lists (- item, * item, 1. item)
    - Horizontal rules (---)
    - Blockquotes (> text)
    """
    if not text:
        return text
    
    # Remove code blocks (```code```)
    text = re.sub(r'```[\s\S]*?```', '', text)
    
    # Remove inline code (`code`)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # Remove markdown headers (# ## ###)
    text = re.sub(r'^#{1,6}\s+(.+)$', r'\1', text, flags=re.MULTILINE)
    
    # Remove bold (**text** or __text__)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    
    # Remove italic (*text* or _text_)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    
    # Remove links ([text](url))
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # Remove list markers (- * + 1. 2. etc.)
    text = re.sub(r'^[\s]*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # Remove horizontal rules
    text = re.sub(r'^---+$', '', text, flags=re.MULTILINE)
    
    # Remove blockquotes
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
    
    # Clean up extra whitespace
    text = re.sub(r'\n\s*\n', '\n', text)
    text = text.strip()
    
    return text


# ============================================================================
# STEP 2: USERDATA (Shared State)
# ============================================================================
"""
What is Shared State?
- Stores data that persists across agent transfers
- Allows agents to access each other's instances
- Enables context preservation during transfers

Key Components:
- personas: Dictionary mapping agent names to agent instances
- prev_agent: Reference to the previous agent (for context transfer)
- ctx: Job context for accessing room information

💡 Why Shared State?
This enables seamless agent transfers while maintaining conversation context.
"""
@dataclass
class UserData:
    """Stores data and agents to be shared across the session"""
    personas: dict[str, Agent] = field(default_factory=dict)
    prev_agent: Optional[Agent] = None
    ctx: Optional[JobContext] = None

    def summarize(self) -> str:
        """Return a summary of user data for agent context"""
        return "User data: Medical office triage system with multiple specialized agents"

# Type alias for easier typing
RunContext_T = RunContext[UserData]


# ============================================================================
# STEP 3: BASEAGENT (Common Functionality)
# ============================================================================
"""
What is a Base Agent?
A base class that provides common functionality for all agents:
- Context preservation during transfers
- Chat history truncation
- Room attribute updates
- Agent transfer logic

Key Methods:
- on_enter(): Called when agent enters the conversation
- _truncate_chat_ctx(): Truncates chat history to keep relevant context
- _transfer_to_agent(): Handles agent transfer with context preservation

💡 Why a Base Class?
- Reduces code duplication
- Ensures consistent behavior across agents
- Centralizes context management logic
- Makes it easy to add new agents
"""
class BaseAgent(Agent):
    """
    Base class for all medical office agents.
    
    Provides common functionality:
    - Context preservation during transfers
    - Chat history management
    - Room attribute tracking
    - Agent transfer coordination
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    async def on_enter(self) -> None:
        """
        Called when agent enters the conversation
        
        This lifecycle hook:
        1. Updates room attributes to track current agent
        2. Preserves context from previous agent
        3. Truncates chat history to keep relevant messages
        4. Adds system message with agent role
        5. Starts conversation generation
        """
        agent_name = self.__class__.__name__
        logger.info(f"Entering {agent_name}")

        userdata: UserData = self.session.userdata
        
        # Update room attributes to track which agent is active
        if userdata.ctx and userdata.ctx.room:
            await userdata.ctx.room.local_participant.set_attributes({"agent": agent_name})

        chat_ctx = self.chat_ctx.copy()

        # Preserve context from previous agent
        if userdata.prev_agent:
            # Truncate previous agent's chat history to keep last 6 messages
            items_copy = self._truncate_chat_ctx(
                userdata.prev_agent.chat_ctx.items, keep_function_call=True
            )
            # Avoid duplicate items
            existing_ids = {item.id for item in chat_ctx.items}
            items_copy = [item for item in items_copy if item.id not in existing_ids]
            chat_ctx.items.extend(items_copy)

        # Add system message with agent role
        chat_ctx.add_message(
            role="system",
            content=f"You are the {agent_name}. {userdata.summarize()}"
        )
        await self.update_chat_ctx(chat_ctx)
        self.session.generate_reply()

    def _truncate_chat_ctx(
        self,
        items: list,
        keep_last_n_messages: int = 6,
        keep_system_message: bool = False,
        keep_function_call: bool = False,
    ) -> list:
        """
        Truncates the chat context to keep the last n messages
        
        This helps:
        - Prevent context from growing too large
        - Keep relevant conversation history
        - Remove old messages that may not be relevant
        - Maintain function call context if needed
        """
        def _valid_item(item) -> bool:
            """Check if item should be kept"""
            if not keep_system_message and item.type == "message" and item.role == "system":
                return False
            if not keep_function_call and item.type in ["function_call", "function_call_output"]:
                return False
            return True

        new_items = []
        # Process items in reverse to get last N messages
        for item in reversed(items):
            if _valid_item(item):
                new_items.append(item)
            if len(new_items) >= keep_last_n_messages:
                break
        new_items = new_items[::-1]  # Reverse back to chronological order

        # Remove leading function calls if they exist
        while new_items and new_items[0].type in ["function_call", "function_call_output"]:
            new_items.pop(0)

        return new_items

    async def _transfer_to_agent(self, name: str, context: RunContext_T) -> Agent:
        """
        Transfers to another agent while preserving context
        
        This method:
        1. Gets the next agent from userdata
        2. Updates previous agent reference
        3. Returns the new agent instance
        
        The new agent's on_enter() will handle context preservation.
        """
        userdata = context.userdata
        current_agent = context.session.current_agent
        next_agent = userdata.personas[name]
        userdata.prev_agent = current_agent

        return next_agent


# ============================================================================
# STEP 4: SPECIALIZED AGENTS
# ============================================================================
"""
What are Specialized Agents?
Each agent has a specific role and expertise:
- TriageAgent: Initial point of contact, routes patients to appropriate department
- SupportAgent: Handles medical services (appointments, prescriptions, records)
- BillingAgent: Manages billing, insurance, and payment questions

Each agent:
1. Uses BaseAgent as parent class
2. Loads specialized prompts from YAML files
3. Has transfer tools to move to other agents
4. Uses voice components (STT, TTS, LLM, VAD)

💡 Try This: Add a new specialized agent (e.g., AppointmentAgent) to handle scheduling!
"""

class TriageAgent(BaseAgent):
    """
    Medical Office Triage Agent.
    
    This is the initial point of contact that:
    - Greets patients and determines their needs
    - Routes patients to Support or Billing agents
    - Handles initial assessment questions
    """
    
    def __init__(self) -> None:
        super().__init__(
            instructions=load_prompt('triage_prompt.yaml'),
            stt=deepgram.STTv2(model="flux-general-en", eager_eot_threshold=0.3),
            llm=get_livekit_llm(),
            tts=deepgram.TTS(model="aura-asteria-en"),
            vad=silero.VAD.load()
        )
    
    async def on_enter(self) -> None:
        """
        Called when TriageAgent enters the room
        
        This overrides BaseAgent's on_enter to:
        1. Set up context (calls parent)
        2. Get patient name from room
        3. Personalize the greeting
        4. Start conversation with warm welcome
        """
        # First call parent to set up context and attributes
        await super().on_enter()
        
        # Get patient name from room
        patient_name = None
        try:
            userdata: UserData = self.session.userdata
            if userdata.ctx and userdata.ctx.room:
                room = userdata.ctx.room
                if room.remote_participants:
                    # Get first remote participant's name
                    remote_participant = next(iter(room.remote_participants.values()), None)
                    if remote_participant and remote_participant.name:
                        patient_name = remote_participant.name.strip()
        except Exception:
            # If we can't get the room, just proceed without personalization
            pass
        
        # Personalize greeting with patient name
        if patient_name and patient_name.lower() != "patient":
            greeting = f"Hello {patient_name}! Welcome to our medical office. How can I help you today?"
        else:
            greeting = "Hello! Welcome to our medical office. How can I help you today?"
        
        await self.session.say(greeting, allow_interruptions=True)

    @function_tool
    async def transfer_to_support(self, context: RunContext_T) -> Agent:
        """
        Transfers patient to Patient Support agent
        
        Called when the patient needs help with:
        - Appointment scheduling
        - Prescription refills
        - Medical records requests
        - General healthcare questions
        """
        await self.session.say("I'll transfer you to our Patient Support team who can help with your medical services request.")
        return await self._transfer_to_agent("support", context)

    @function_tool
    async def transfer_to_billing(self, context: RunContext_T) -> Agent:
        """
        Transfers patient to Medical Billing agent
        
        Called when the patient needs help with:
        - Insurance questions
        - Medical bills
        - Payment plans
        - Billing inquiries
        """
        await self.session.say("I'll transfer you to our Medical Billing department who can assist with your insurance and payment questions.")
        return await self._transfer_to_agent("billing", context)


class SupportAgent(BaseAgent):
    """
    Patient Support Agent.
    
    Handles medical services including:
    - Appointment scheduling
    - Prescription refills
    - Medical records requests
    - General healthcare questions
    """
    
    def __init__(self) -> None:
        super().__init__(
            instructions=load_prompt('support_prompt.yaml'),
            stt=deepgram.STTv2(model="flux-general-en", eager_eot_threshold=0.3),
            llm=get_livekit_llm(),
            tts=deepgram.TTS(model="aura-asteria-en"),
            vad=silero.VAD.load()
        )

    @function_tool
    async def transfer_to_triage(self, context: RunContext_T) -> Agent:
        """Transfers back to Triage agent if needed"""
        await self.session.say("I'll transfer you back to our Medical Office Triage agent who can better direct your inquiry.")
        return await self._transfer_to_agent("triage", context)

    @function_tool
    async def transfer_to_billing(self, context: RunContext_T) -> Agent:
        """Transfers to Billing agent if patient has billing questions"""
        await self.session.say("I'll transfer you to our Medical Billing department for assistance with your insurance and payment questions.")
        return await self._transfer_to_agent("billing", context)


class BillingAgent(BaseAgent):
    """
    Medical Billing Agent.
    
    Manages billing, insurance, and payment questions:
    - Insurance information
    - Copayments
    - Medical bills
    - Payment processing
    - Billing inquiries
    """
    
    def __init__(self) -> None:
        super().__init__(
            instructions=load_prompt('billing_prompt.yaml'),
            stt=deepgram.STTv2(model="flux-general-en", eager_eot_threshold=0.3, eot_threshold=0.3),
            llm=get_livekit_llm(),
            tts=deepgram.TTS(model="aura-asteria-en"),
            vad=silero.VAD.load()
        )

    @function_tool
    async def transfer_to_triage(self, context: RunContext_T) -> Agent:
        """Transfers back to Triage agent if needed"""
        await self.session.say("I'll transfer you back to our Medical Office Triage agent who can better direct your inquiry.")
        return await self._transfer_to_agent("triage", context)

    @function_tool
    async def transfer_to_support(self, context: RunContext_T) -> Agent:
        """Transfers to Support agent if patient has medical service questions"""
        await self.session.say("I'll transfer you to our Patient Support team who can help with your medical services request.")
        return await self._transfer_to_agent("support", context)


# ============================================================================
# STEP 5: ENTRYPOINT (Job Execution)
# ============================================================================
"""
What is an Entrypoint?
The main function called when LiveKit dispatches a job to this agent system.

How It Works:
1. LiveKit detects a user joined a room
2. LiveKit dispatches job to available agent worker
3. entrypoint() function is called with JobContext
4. All agents are created and registered in UserData
5. Agent session starts with TriageAgent (initial contact)
6. Conversation begins, agents can transfer as needed

Multi-Agent Initialization:
- Create all agent instances
- Register them in UserData.personas dictionary
- Start session with TriageAgent (first point of contact)
- Agents can transfer to each other using their transfer tools
"""
async def entrypoint(ctx: JobContext):
    """
    Main entrypoint for the medical office triage agent system.
    
    This function:
    1. Checks if room name matches medical office pattern (filters out other demos)
    2. Connects to the LiveKit room (ctx.connect())
    3. Creates UserData to store shared state
    4. Initializes all three agents (Triage, Support, Billing)
    5. Registers agents in UserData.personas dictionary
    6. Creates AgentSession with UserData
    7. Starts session with TriageAgent (initial contact)
    
    The TriageAgent will greet the patient and determine their needs,
    then transfer to the appropriate agent as needed.
    """
    # Only handle rooms with "medical_" prefix to avoid interference with other demos
    if not ctx.room.name.startswith("medical_"):
        logger.info(f"Ignoring room {ctx.room.name} - not a medical office room")
        return
    
    # Connect to the room first
    await ctx.connect()
    
    # Create shared state
    userdata = UserData(ctx=ctx)
    
    # Initialize all agents
    triage_agent = TriageAgent()
    support_agent = SupportAgent()
    billing_agent = BillingAgent()

    # Register all agents in the userdata
    userdata.personas.update({
        "triage": triage_agent,
        "support": support_agent,
        "billing": billing_agent
    })

    # Create session with shared userdata
    session = AgentSession[UserData](userdata=userdata)

    # Start with TriageAgent (initial point of contact)
    await session.start(
        agent=triage_agent,
        room=ctx.room,
    )


# ============================================================================
# LEARNING CHECKLIST
# ============================================================================
"""
After reading this code, you should understand:

✓ How to build multi-agent voice AI systems
✓ How to create specialized agents with distinct roles
✓ How to transfer between agents with context preservation
✓ How to manage conversation history across transfers
✓ How to structure shared state for agent coordination

Next Steps:
1. Add a new specialized agent (e.g., AppointmentAgent)
2. Experiment with different context truncation strategies
3. Modify transfer logic to add custom handoff messages
4. Try different LLM models or temperature settings
5. Add more sophisticated state management

Questions to Consider:
- How would you handle multiple concurrent patient calls?
- How would you persist conversation history across sessions?
- What happens if an agent disconnects during transfer?
- How would you add more specialized agents?
- How could you integrate with a patient management system?

💡 Key Multi-Agent Concepts:
- Agent Specialization: Each agent has a specific role and expertise
- Context Preservation: Conversation history maintained across transfers
- Agent Transfer: Seamless handoff between agents
- Coordination: Agents work together to handle complex workflows
- Shared State: Data that persists across agent transfers
"""

if __name__ == "__main__":
    # Register with explicit agent name for explicit dispatch (like survey-agent example)
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name="medical-triage-agent"))

