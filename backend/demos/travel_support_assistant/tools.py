import random
import subprocess
import json
import sys
import os
import asyncio
from typing import Optional, Dict

from .utils import get_bookings, get_hotels, get_flights, search_policies_rag

# In-Memory State for "Write" operations (updates the loaded data temporarily for the session)
# In production, this would write to a DB.
SESSION_BOOKINGS = {}

def _get_all_bookings():
    # Merge file-based mock data with session-based new bookings
    all_bookings = get_bookings().copy()
    all_bookings.update(SESSION_BOOKINGS)
    return all_bookings

def lookup_booking(booking_id: str) -> str:
    """Looks up customer booking information by booking ID."""
    booking_id = booking_id.upper().strip()
    bookings = _get_all_bookings()
    
    if booking_id in bookings:
        booking = bookings[booking_id]
        return f"""Booking Found:
- Booking ID: {booking['booking_id']}
- Customer: {booking['customer_name']}
- Hotel: {booking['hotel']}
- City: {booking.get('city', 'Unknown')}
- Check-in: {booking['check_in']}
- Check-out: {booking['check_out']}
- Status: {booking['status']}
- Room Type: {booking['room_type']}
- Total Price: {booking.get('total_price', 'N/A')} {booking.get('currency', '')}"""
    return f"Booking {booking_id} not found."

def search_hotels(city: str) -> str:
    """Searches for available hotels in a city."""
    city_lower = city.lower().strip()
    hotels_db = get_hotels()
    
    if city_lower in hotels_db:
        hotels = hotels_db[city_lower]
        result = f"Available hotels in {city.title()}:\n\n"
        for i, hotel in enumerate(hotels, 1):
            amenities = ", ".join(hotel.get('amenities', []))
            result += f"{i}. {hotel['name']} | {hotel.get('total_price', hotel['price'])} {hotel['currency']}/night | {hotel['rating']}/5.0\n   Amenities: {amenities}\n"
        return result
    return f"No hotels found for {city}."

def check_flight_status(flight_number: str) -> str:
    """Checks flight status."""
    flight_number = flight_number.upper().strip()
    flights_db = get_flights()
    
    if flight_number in flights_db:
        flight = flights_db[flight_number]
        return f"Flight {flight['flight_number']} ({flight['origin']} -> {flight['destination']}): {flight['status']} | Gate: {flight['gate']}"
    
    # Fallback for demo purposes if not in DB
    return f"Flight {flight_number} record not found in live database (Simulated)."

def search_policies(query: str) -> str:
    """
    Searches the travel policy knowledge base (e.g., cancellation rules, baggage, refunds).
    Use this tool when the user asks about rules, rights, or policy questions.
    """
    return search_policies_rag(query)

def book_hotel(hotel_name: str, city: str, check_in: str, check_out: str, guest_name: str) -> str:
    """Books a hotel room."""
    booking_id = f"BK{random.randint(100000, 999999)}"
    SESSION_BOOKINGS[booking_id] = {
        "booking_id": booking_id,
        "customer_name": guest_name,
        "hotel": hotel_name,
        "city": city,
        "check_in": check_in,
        "check_out": check_out,
        "status": "confirmed",
        "room_type": "Standard Room",
        "total_price": 200, # Simulated
        "currency": "EUR"
    }
    return f"Hotel booking confirmed! ID: {booking_id}"

def book_taxi(pickup_location: str, destination: str, pickup_time: Optional[str] = None) -> str:
    """Books a taxi."""
    pickup_time = pickup_time or "Immediate"
    return f"Taxi booking confirmed! From {pickup_location} to {destination} at {pickup_time}."

def cancel_booking(booking_id: str, reason: Optional[str] = None) -> str:
    """Cancels a booking."""
    booking_id = booking_id.upper().strip()
    bookings = _get_all_bookings()
    
    if booking_id in bookings:
        # Check if we can write to it (simulate write)
        if booking_id in SESSION_BOOKINGS:
            SESSION_BOOKINGS[booking_id]["status"] = "cancelled"
            return f"Booking {booking_id} cancelled."
        elif booking_id in get_bookings():
             # We can't modify the static file in memory permanently in this simple script without reloading, 
             # so we will just return success for the demo.
             return f"Booking {booking_id} cancellation processed (Demo Success). Refund of {bookings[booking_id].get('total_price', 0)} initiated."
    
    return f"Booking {booking_id} not found."

async def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """
    Converts currency using the external MCP server.
    Use this tool when the user asks for prices in a different currency.
    """
    # Path to the MCP server script
    script_path = os.path.join(os.path.dirname(__file__), "mcp_server.py")
    
    # We use the 'mcp' library's client capabilities, or simpler: 
    # since we built the server with FastMCP which supports stdio, 
    # we can use a client to talk to it. 
    # HOWEVER, for a single generic tool call in this demo without setting up a full async MCP Client session manager 
    # inside the AutoGen loop (which is complex), the easiest way to *demonstrate* it 
    # is to treat the MCP server as a CLI tool we invoke.
    # But to be "Real MCP", we should try to talk JSON-RPC.
    
    # Simpler approach for this specific demo tool wrapper:
    # Connect, generic request, response, disconnect.
    
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    
    server_params = StdioServerParameters(
        command=sys.executable, # Use the current python interpreter
        args=[script_path],
        env=dict(os.environ) # Pass env
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Call the tool
                result = await session.call_tool("convert_currency", arguments={
                    "amount": amount,
                    "from_currency": from_currency,
                    "to_currency": to_currency
                })
                
                # Result is a CallToolResult object
                if result.content and len(result.content) > 0:
                    return result.content[0].text
                return "No output from currency converter."
                
    except Exception as e:
        return f"MCP Currency Converter Error: {str(e)}"


AVAILABLE_TOOLS = [lookup_booking, search_hotels, check_flight_status, search_policies, book_hotel, book_taxi, cancel_booking, convert_currency]
