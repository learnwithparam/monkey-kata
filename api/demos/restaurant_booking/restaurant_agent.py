"""
Restaurant Booking Agent
========================

This is a simple LiveKit voice agent for restaurant order booking.

The agent connects to LiveKit rooms and handles voice conversations with customers
to take orders, answer menu questions, and manage the ordering process.

Run this agent separately from the API server:
    python restaurant_agent.py dev

This will start the agent and it will automatically connect to rooms when
customers join via the frontend.
"""

from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, function_tool
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import silero, deepgram, openai
import asyncio

load_dotenv()

# Simple menu structure (matches API)
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

# Order state (in production, use a database)
order_items = []


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
        Formatted order summary
    """
    if not order_items:
        return "Your order is currently empty."
    
    total = sum(item["price"] for item in order_items)
    items_list = "\n".join([f"- {item['name']}: ${item['price']:.2f}" for item in order_items])
    
    return f"Your current order:\n{items_list}\n\nTotal: ${total:.2f}"


@function_tool()
async def get_menu_items(category: str = "all") -> str:
    """
    Get menu items by category or all items.
    
    Call this when the customer asks about the menu, what's available, or about specific categories.
    
    Args:
        category: The category to show (appetizers, mains, desserts, drinks) or "all" for everything
    
    Returns:
        Formatted menu items
    """
    if category.lower() == "all":
        menu_text = "Here's our menu:\n\n"
        for cat_name, items in MENU.items():
            menu_text += f"{cat_name.title()}:\n"
            for item in items:
                menu_text += f"  - {item['name']}: ${item['price']:.2f}\n"
            menu_text += "\n"
        return menu_text
    else:
        category_lower = category.lower()
        for cat_name, items in MENU.items():
            if category_lower in cat_name.lower():
                menu_text = f"{cat_name.title()}:\n"
                for item in items:
                    menu_text += f"  - {item['name']}: ${item['price']:.2f}\n"
                return menu_text
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


def build_instructions() -> str:
    """Build agent instructions"""
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
- When customers ask about the menu, use the get_menu_items tool
- When customers want to order something, use the add_item_to_order tool
- When customers want to see their order, use the view_current_order tool
- When customers are ready to place their order, use the place_order tool
- If a customer asks about an item not on the menu, politely let them know
- Always confirm orders before placing them
- Personalize your responses using the customer's name naturally throughout the conversation

Keep responses concise and natural. Don't list all menu items unless asked.
"""


class RestaurantAgent(Agent):
    """Restaurant booking agent with order management tools."""
    
    def __init__(self) -> None:
        super().__init__(
            instructions=build_instructions(),
            stt=deepgram.STTv2(model="flux-general-en", eager_eot_threshold=0.4),
            llm=openai.LLM.with_fireworks(
                model="accounts/fireworks/models/qwen3-235b-a22b-instruct-2507",
                temperature=0.7
            ),
            tts=deepgram.TTS(model="aura-asteria-en"),
            vad=silero.VAD.load(),
            tools=[add_item_to_order, view_current_order, get_menu_items, place_order],
        )
    
    async def on_enter(self):
        """Called when agent enters the room - greet the customer by name"""
        # Get participant name from room
        customer_name = None
        room = self.session.room
        if room:
            # Wait for participants to join (max 2 seconds)
            for _ in range(20):
                await asyncio.sleep(0.1)
                for participant in room.remote_participants.values():
                    if participant.name and participant.name.strip():
                        customer_name = participant.name.strip()
                        break
                if customer_name:
                    break
        
        # Personalize greeting with customer name
        if customer_name and customer_name.lower() != "customer":
            greeting = f"Hello {customer_name}! Welcome to our restaurant. How can I help you today?"
        else:
            greeting = "Hello! Welcome to our restaurant. How can I help you today?"
        
        await self.session.say(greeting, allow_interruptions=True)


async def entrypoint(ctx: JobContext):
    """Main entrypoint for the restaurant agent"""
    await ctx.connect()
    
    # Create agent session and start the agent
    session = AgentSession()
    agent = RestaurantAgent()
    await session.start(
        agent=agent,
        room=ctx.room
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
