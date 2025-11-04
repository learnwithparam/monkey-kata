"""
Restaurant Booking Voice Agent
==============================

🎯 LEARNING OBJECTIVES:
This demo teaches you how to build a LiveKit voice AI agent:

1. Voice Agent Architecture - How to structure a LiveKit voice agent
2. Speech-to-Text (STT) - How to configure STT for real-time transcription
3. Text-to-Speech (TTS) - How to configure TTS for natural voice responses
4. Tool Calling - How to give agents tools to perform actions (add items, view menu, place order)
5. State Management - How to maintain conversation context and order state
6. Voice Activity Detection (VAD) - How to detect when users are speaking
7. Turn Detection - How to manage conversation flow and interruptions
8. Personalization - How to greet customers by name and personalize interactions

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Setup - Import libraries and load environment variables
Step 2: Menu Data - Define restaurant menu structure
Step 3: Order State - Initialize in-memory order storage
Step 4: Tool Functions - Create agent tools for menu and order management
Step 5: Agent Instructions - Build conversational prompts for the LLM
Step 6: Agent Class - Configure STT, TTS, LLM, and tools
Step 7: Entrypoint - Connect agent to LiveKit rooms

Key Concept: LiveKit voice agents are worker processes that connect to LiveKit rooms
and handle real-time audio streaming. They use STT to understand user speech, LLM to
generate responses, and TTS to speak responses. Tools allow agents to perform actions
like adding items to orders, viewing the menu, and placing orders.
"""

# ============================================================================
# STEP 1: SETUP & IMPORTS
# ============================================================================
"""
Understanding the Imports:
- dotenv: Loads environment variables from .env file
- livekit.agents: Core LiveKit agents framework
  - JobContext: Context for agent job execution
  - WorkerOptions: Configuration for agent worker
  - cli: Command-line interface for running agents
  - function_tool: Decorator for creating agent tools
  - get_job_context: Access current job context
- livekit.agents.voice: Voice-specific agent components
  - Agent: Base class for voice agents
  - AgentSession: Manages agent's conversation session
- livekit.plugins: Provider plugins for STT, TTS, LLM
  - silero: Voice Activity Detection (VAD)
  - deepgram: Speech-to-Text (STT) and Text-to-Speech (TTS)
  - openai: LLM provider (supports Fireworks via .with_fireworks())
- asyncio: For async operations

Why Separate Processes?
LiveKit agents run as separate worker processes that:
1. Register with LiveKit server as available workers
2. Wait for LiveKit to dispatch jobs (when users join rooms)
3. Handle real-time audio streams continuously
4. Run independently from your API server

This is different from traditional API endpoints because real-time audio
processing requires long-lived connections and LiveKit manages job dispatch.
"""
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, function_tool, get_job_context
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import silero, deepgram, openai
import asyncio

load_dotenv()


# ============================================================================
# STEP 2: MENU DATA
# ============================================================================
"""
Menu Structure:
This is a simplified menu structure that matches the API's menu.

In production, you would:
- Load menu from a database
- Fetch menu from an API endpoint
- Support dynamic menu updates
- Handle menu versioning

The menu is organized by categories:
- appetizers: Starter items
- mains: Main course dishes
- desserts: Sweet treats
- drinks: Beverages

Each item has:
- id: Unique identifier (for matching orders)
- name: Display name (used for matching user requests)
- price: Price in USD (for order totals)
"""
MENU = {
    "appetizers": [
        {"id": "app_001", "name": "Caesar Salad", "price": 8.99},
        {"id": "app_002", "name": "Bruschetta", "price": 7.99},
        {"id": "app_003", "name": "Mozzarella Sticks", "price": 6.99},
    ],
    "mains": [
        {"id": "main_001", "name": "Grilled Salmon", "price": 22.99},
        {"id": "main_002", "name": "Ribeye Steak", "price": 28.99},
        {"id": "main_003", "name": "Pasta Carbonara", "price": 16.99},
        {"id": "main_004", "name": "Margherita Pizza", "price": 14.99},
    ],
    "desserts": [
        {"id": "dess_001", "name": "Chocolate Lava Cake", "price": 7.99},
        {"id": "dess_002", "name": "Tiramisu", "price": 6.99},
    ],
    "drinks": [
        {"id": "drink_001", "name": "Coca Cola", "price": 2.99},
        {"id": "drink_002", "name": "Iced Tea", "price": 2.99},
        {"id": "drink_003", "name": "Orange Juice", "price": 3.99},
    ],
}

# ============================================================================
# STEP 3: ORDER STATE
# ============================================================================
"""
Order State Management:
This is a simple in-memory order storage. In production, you would:
- Store orders in a database (PostgreSQL, MongoDB, etc.)
- Track orders per user/session
- Handle concurrent orders
- Persist order history
- Add order status tracking

Current Implementation:
- Single global order_items list
- Cleared after order is placed
- No user session tracking
- No order history

For production, consider:
- Dictionary mapping session_id -> order_items
- Database persistence
- Order status (pending, confirmed, completed)
- Payment integration
"""
order_items = []


# ============================================================================
# STEP 4: TOOL FUNCTIONS (Agent Capabilities)
# ============================================================================
"""
Tool Functions:
These are the "tools" or "functions" that the agent can call during conversation.
Tools allow agents to perform actions beyond just generating text.

How Tool Calling Works:
1. User says something that triggers tool usage (e.g., "I'd like a Caesar Salad")
2. LLM decides to call a tool (e.g., add_item_to_order)
3. Tool function executes with provided parameters
4. Tool returns result (e.g., "Added Caesar Salad to your order")
5. LLM incorporates result into its response
6. Agent speaks the response to the user

Key Design Principles:
- Tools should be async functions
- Tools should return natural language strings (not markdown)
- Tools should handle errors gracefully
- Tools should be idempotent when possible
- Tools should validate inputs
"""


@function_tool()
async def add_item_to_order(item_name: str) -> str:
    """
    Add an item to the customer's order.
    
    Call this when the customer wants to order something.
    Find the item by name in the menu and add it to their order.
    
    Args:
        item_name: The name of the item the customer wants to order
    
    Returns:
        Confirmation message
    """
    # Search for item in menu
    item_found = None
    for category, items in MENU.items():
        for item in items:
            if item["name"].lower() == item_name.lower():
                item_found = item
                break
        if item_found:
            break
    
    if not item_found:
        # Try partial match
        for category, items in MENU.items():
            for item in items:
                if item_name.lower() in item["name"].lower():
                    item_found = item
                    break
            if item_found:
                break
    
    if item_found:
        order_items.append(item_found)
        return f"Added {item_found['name']} (${item_found['price']:.2f}) to your order."
    else:
        return f"I couldn't find '{item_name}' on the menu. Could you please specify the exact item name?"


@function_tool()
async def view_current_order() -> str:
    """
    Show the customer their current order with items and total price.
    
    Call this when the customer asks what they've ordered or wants to see their order.
    
    Returns:
        Natural conversational order summary
    """
    if not order_items:
        return "Your order is currently empty."
    
    total = sum(item["price"] for item in order_items)
    items_list = []
    for item in order_items:
        items_list.append(f"{item['name']} for ${item['price']:.2f}")
    
    return f"You have {', '.join(items_list)}. Your total comes to ${total:.2f}."


@function_tool()
async def get_menu_items(category: str = "all") -> str:
    """
    Get menu items by category or all items.
    
    Call this when the customer asks about the menu, what's available, or about specific categories.
    
    Args:
        category: The category to show (appetizers, mains, desserts, drinks) or "all" for everything
    
    Returns:
        Natural conversational menu description
    """
    if category.lower() == "all":
        # Return natural conversational text, not markdown
        menu_parts = []
        for cat_name, items in MENU.items():
            items_list = []
            for item in items:
                items_list.append(f"{item['name']} for ${item['price']:.2f}")
            menu_parts.append(f"For {cat_name}, we have {', '.join(items_list)}.")
        return " ".join(menu_parts)
    else:
        category_lower = category.lower()
        for cat_name, items in MENU.items():
            if category_lower in cat_name.lower():
                items_list = []
                for item in items:
                    items_list.append(f"{item['name']} for ${item['price']:.2f}")
                return f"For {cat_name}, we have {', '.join(items_list)}."
        return f"I couldn't find the category '{category}'. Available categories: {', '.join(MENU.keys())}"


@function_tool()
async def place_order() -> str:
    """
    Place the order and clear the order state.
    
    Call this when the customer is ready to finalize their order.
    
    Returns:
        Order confirmation message
    """
    if not order_items:
        return "You don't have any items in your order yet."
    
    total = sum(item["price"] for item in order_items)
    items_list = ", ".join([item["name"] for item in order_items])
    
    # Clear order for next customer
    order_items.clear()
    
    return f"Perfect! I've placed your order for: {items_list}. Your total is ${total:.2f}. Your order will be ready shortly. Thank you!"


# ============================================================================
# STEP 5: AGENT INSTRUCTIONS
# ============================================================================
"""
Agent Instructions:
This is the "system prompt" that tells the LLM how to behave as a restaurant assistant.

Key Elements:
- Role definition: "You are a friendly restaurant order assistant"
- Menu context: Available items for the agent to reference
- Behavioral guidelines: How to interact with customers
- Tool usage instructions: When and how to use each tool
- Response style: Keep responses short and natural for voice

Voice-Specific Considerations:
- Responses must be short (1-2 sentences, under 20 words)
- No markdown formatting (TTS will read it literally)
- Natural conversational language
- Personalize using customer's name
- Confirm orders before placing them

The instructions are dynamically built to include the current menu items,
making the agent aware of what's available without hardcoding.
"""
def build_instructions() -> str:
    """Build agent instructions with current menu context"""
    menu_summary = "Available items: "
    all_items = []
    for items in MENU.values():
        all_items.extend([item["name"] for item in items])
    menu_summary += ", ".join(all_items)
    
    return f"""You are a friendly and helpful restaurant order assistant. Your job is to help customers place their orders.

{menu_summary}

Guidelines:
- Use the customer's name when addressing them (it will be provided in the context)
- Greet customers warmly by name when they connect
- Be conversational and friendly, like a real restaurant server
- Keep responses SHORT and natural - maximum 1-2 sentences under 20 words for voice conversation
- When customers ask about the menu, use the get_menu_items tool and then speak the menu items naturally in conversation
- When customers want to order something, use the add_item_to_order tool
- When customers want to see their order, use the view_current_order tool and read it naturally
- When customers are ready to place their order, use the place_order tool
- If a customer asks about an item not on the menu, politely let them know
- Always confirm orders before placing them
- Personalize your responses using the customer's name naturally throughout the conversation
- Output plain text only - no markdown, no formatting, just natural spoken language

Keep responses concise and natural. Speak conversationally, not robotically.
"""


# ============================================================================
# STEP 6: AGENT CLASS (Voice Agent Configuration)
# ============================================================================
"""
RestaurantAgent Configuration:

This class configures all the components needed for a voice AI agent:

1. STT (Speech-to-Text):
   - Provider: Deepgram Flux-General model
   - Model: "flux-general-en" - Fast, accurate English transcription
   - eager_eot_threshold: 0.3 - Lower threshold for faster end-of-turn detection
     (Lower = agent responds faster, Higher = waits longer for user to finish)

2. LLM (Large Language Model):
   - Provider: Fireworks AI (via OpenAI plugin)
   - Model: Qwen3-235B - Fast, efficient inference for voice conversations
   - Temperature: 0.7 - Balanced creativity and consistency
   - Note: max_tokens not supported by with_fireworks(), controlled via instructions

3. TTS (Text-to-Speech):
   - Provider: Deepgram Aura Asteria
   - Model: "aura-asteria-en" - Natural, expressive English voice
   - LiveKit handles text normalization automatically

4. VAD (Voice Activity Detection):
   - Provider: Silero
   - Detects when user is speaking vs. silence
   - Helps manage conversation flow and reduce unnecessary processing

5. Tools:
   - List of function tools the agent can call
   - Tools are automatically available to the LLM during conversation

6. Turn Detection:
   - Handled by eager_eot_threshold in STT config
   - Lower threshold = faster turn-taking
   - Alternative: MultilingualModel (requires model download)
"""
class RestaurantAgent(Agent):
    """
    Restaurant booking voice agent with order management tools.
    
    This agent:
    - Connects to LiveKit rooms when customers join
    - Listens to customer speech (STT)
    - Processes requests and generates responses (LLM)
    - Speaks responses naturally (TTS)
    - Calls tools to perform actions (add items, view menu, place order)
    - Maintains conversation context and order state
    """
    
    def __init__(self) -> None:
        super().__init__(
            instructions=build_instructions(),
            stt=deepgram.STTv2(model="flux-general-en", eager_eot_threshold=0.3),
            llm=openai.LLM.with_fireworks(
                model="accounts/fireworks/models/qwen3-235b-a22b-instruct-2507",
                temperature=0.7,
            ),
            tts=deepgram.TTS(model="aura-asteria-en"),
            vad=silero.VAD.load(),
            tools=[add_item_to_order, view_current_order, get_menu_items, place_order],
            # Turn detection handled by eager_eot_threshold in STT config
        )
    
    async def on_enter(self):
        """
        Called when agent enters the room - greet the customer by name.
        
        This is a lifecycle hook that runs when the agent first connects to a room.
        It's the perfect place to:
        - Greet the customer
        - Get the customer's name from the room
        - Initialize conversation
        - Set up any session-specific state
        
        How to Access Room Information:
        - Use get_job_context() to get the current job context
        - Access ctx.room to get room information
        - Use room.remote_participants to get participant names
        
        Note: This is called AFTER the user has already joined the room,
        so we can safely access participant information.
        """
        # Get participant name from room
        customer_name = None
        try:
            job_ctx = get_job_context()
            room = job_ctx.room if job_ctx else None
            if room and room.remote_participants:
                # Get first remote participant's name
                remote_participant = next(iter(room.remote_participants.values()), None)
                if remote_participant and remote_participant.name:
                    customer_name = remote_participant.name.strip()
        except Exception:
            # If we can't get the room, just proceed without personalization
            pass
        
        # Personalize greeting with customer name
        if customer_name and customer_name.lower() != "customer":
            greeting = f"Hello {customer_name}! Welcome to our restaurant. How can I help you today?"
        else:
            greeting = "Hello! Welcome to our restaurant. How can I help you today?"
        
        await self.session.say(greeting, allow_interruptions=True)


# ============================================================================
# STEP 7: ENTRYPOINT (Job Execution)
# ============================================================================
"""
Entrypoint Function:
This is the main function that gets called when LiveKit dispatches a job to this agent.

How It Works:
1. LiveKit detects a user joined a room
2. LiveKit dispatches job to available agent worker
3. entrypoint() function is called with JobContext
4. Agent connects to the room
5. Agent session starts and begins voice conversation
6. Conversation continues until user disconnects or agent stops

JobContext:
- Contains room information
- Contains job metadata
- Provides connection management
- Handles cleanup on disconnect

AgentSession:
- Manages the conversation lifecycle
- Handles STT/TTS streaming
- Manages tool calling
- Tracks conversation state
"""
async def entrypoint(ctx: JobContext):
    """
    Main entrypoint for the restaurant agent.
    
    This function is called by LiveKit when a user joins a room that needs an agent.
    
    Flow:
    1. Connect to the LiveKit room (ctx.connect())
    2. Create an agent session (AgentSession())
    3. Create the agent instance (RestaurantAgent())
    4. Start the session with agent and room (session.start())
    5. Voice conversation begins automatically
    
    The agent will automatically:
    - Call on_enter() when it joins
    - Listen to user speech (STT)
    - Generate responses (LLM)
    - Speak responses (TTS)
    - Call tools when needed
    - Handle disconnections gracefully
    """
    await ctx.connect()
    
    # Create agent session and start the agent
    session = AgentSession()
    agent = RestaurantAgent()
    await session.start(
        agent=agent,
        room=ctx.room
    )


# ============================================================================
# MAIN EXECUTION
# ============================================================================
"""
How to Run:
1. Development mode: python restaurant_agent.py dev
2. Production mode: python restaurant_agent.py start

The CLI handles:
- Worker registration with LiveKit
- Job dispatch and execution
- Error handling and retries
- Logging and monitoring
- Graceful shutdown
"""


if __name__ == "__main__":
    # Register with explicit agent name for explicit dispatch (prevents conflicts with other agents)
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name="restaurant-agent"))
