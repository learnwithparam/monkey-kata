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
- livekit.agents: Framework for building voice AI agents
- livekit.agents.voice: Voice-specific components (Agent, AgentSession)
- livekit.plugins: Providers for STT, TTS, and LLM
- function_tool: Decorator to create tools agents can use

💡 Key Concept: Voice agents run as separate worker processes that handle
real-time audio streams. They connect to LiveKit rooms when users join.
"""
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, function_tool, get_job_context
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import silero, deepgram, openai

load_dotenv()


# ============================================================================
# STEP 2: MENU DATA
# ============================================================================
"""
What is Menu Data?
- Defines available restaurant items organized by categories
- Each item has an id, name, and price
- Used by the agent to understand what customers can order

💡 In production, you'd load this from a database or API.
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
What is Order State?
- Tracks items the customer has added to their order
- Stored in memory for this demo (simple list)
- Cleared when order is placed

💡 In production, use a database and track orders per user session.
"""
order_items = []


# ============================================================================
# STEP 4: TOOL FUNCTIONS
# ============================================================================
"""
What are Tools?
- Functions the agent can call during conversation
- When a user says "I'd like a Caesar Salad", the LLM calls add_item_to_order
- The tool executes and returns a result
- The agent incorporates the result into its spoken response

Key Tool Design Principles:
- Return natural language strings (not markdown) since they'll be spoken
- Keep responses conversational and friendly
- Handle errors gracefully with helpful messages
"""


@function_tool()
async def add_item_to_order(item_name: str) -> str:
    """
    Adds an item to the customer's order
    
    Searches the menu for the item and adds it to the order.
    Returns a friendly confirmation message that will be spoken to the customer.
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
    Shows the customer their current order
    
    Returns a natural conversational summary with items and total price.
    Perfect for when customers ask "What's in my order?" or "What's my total?"
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
    Gets menu items by category or all items
    
    Called when customers ask about the menu, what's available, or specific categories.
    Returns a natural conversational description that flows well in speech.
    
    Args:
        category: The category to show (appetizers, mains, desserts, drinks) or "all"
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
    Places the order and clears the order state
    
    Called when the customer is ready to finalize their order.
    Returns a friendly confirmation message with order summary and total.
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
What is Prompt Engineering for Voice Agents?
- The system prompt tells the LLM how to behave as a restaurant assistant
- Includes role definition, menu context, and behavioral guidelines
- Voice-specific: Keep responses short (1-2 sentences), no markdown
- Uses natural spoken language that flows in conversation

Key Voice Prompt Principles:
1. Keep responses concise (under 20 words for voice)
2. Use natural spoken language (not written text)
3. No markdown or formatting
4. Be conversational and friendly
5. Guide tool usage clearly

💡 Try This: Modify the prompt to change the agent's personality or response style!
"""
def build_instructions() -> str:
    """Build agent instructions with current menu context"""
    menu_summary = "Available items: "
    all_items = []
    for items in MENU.values():
        all_items.extend([item["name"] for item in items])
    menu_summary += ", ".join(all_items)
    
    return f"""You are a friendly and helpful restaurant order assistant at "The Estonian Octopus". Your job is to help customers place their orders.

{menu_summary}

Guidelines:
- Greet customers warmly by name when they connect (it will be provided in the context if available)
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
# STEP 6: AGENT CLASS
# ============================================================================
"""
What is a Voice Agent?
A voice agent combines multiple components to create a conversational AI:

- STT (Speech-to-Text): Converts user speech to text (Deepgram)
- LLM: Generates intelligent responses (Fireworks AI)
- TTS (Text-to-Speech): Converts responses to natural speech (Deepgram)
- VAD (Voice Activity Detection): Detects when user is speaking (Silero)
- Tools: Functions the agent can call to perform actions

Key Configuration:
- eager_eot_threshold: Controls response speed (lower = faster response)
  This determines how quickly the agent responds after the user stops speaking
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
                model="fireworks/llama-v3p1-8b-instruct",
                temperature=0.7,
            ),
            tts=deepgram.TTS(model="aura-asteria-en"),
            vad=silero.VAD.load(),
            tools=[add_item_to_order, view_current_order, get_menu_items, place_order],
            # Turn detection handled by eager_eot_threshold in STT config
        )
    
    async def on_enter(self):
        """
        Called when the agent enters the room
        
        This lifecycle hook:
        1. Gets the customer's name from the room
        2. Personalizes the greeting
        3. Starts the conversation with a warm welcome
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
# STEP 7: ENTRYPOINT
# ============================================================================
"""
What is an Entrypoint?
- Called when LiveKit dispatches a job (user joins a room)
- Connects to the room and creates an agent session
- Starts the conversation flow

How It Works:
1. User joins a LiveKit room (from frontend)
2. LiveKit dispatches job to available agent worker
3. entrypoint() function is called
4. Agent connects and starts conversation
5. Agent automatically handles STT, LLM, TTS, and tool calling
"""
async def entrypoint(ctx: JobContext):
    """
    Main entrypoint called when a user joins a room
    
    This function:
    1. Connects to the LiveKit room
    2. Creates an agent session
    3. Initializes the RestaurantAgent
    4. Starts the conversation (agent greets customer)
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
# LEARNING CHECKLIST
# ============================================================================
"""
After reading this code, you should understand:

✓ How to structure a voice AI agent with LiveKit
✓ How to configure STT, TTS, LLM, and VAD components
✓ How to create tools for agents to perform actions
✓ How to build conversational prompts for voice agents
✓ How agents connect to LiveKit rooms and handle conversations

Next Steps:
1. Modify the menu to add more items or categories
2. Experiment with different STT/TTS models
3. Adjust eager_eot_threshold to change response speed
4. Add new tools (e.g., modify_order, cancel_order)
5. Try different LLM models or temperature settings

Questions to Consider:
- What happens if the agent can't understand the customer's speech?
- How would you handle multiple concurrent orders?
- How would you persist order history?
- What happens if the agent disconnects mid-conversation?
- How could you add payment processing?

💡 Key Voice AI Concepts:
- STT: Converts speech to text
- TTS: Converts text to speech
- VAD: Detects when user is speaking
- Turn Detection: Manages conversation flow
- Tool Calling: Allows agents to perform actions
"""
if __name__ == "__main__":
    # Register with explicit agent name for explicit dispatch (prevents conflicts with other agents)
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name="restaurant-agent"))
