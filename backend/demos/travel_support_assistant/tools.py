import random
from datetime import datetime, timedelta
from typing import Optional, Dict

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

def lookup_booking(booking_id: str) -> str:
    """Looks up customer booking information by booking ID."""
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
    return f"Booking {booking_id} not found."

def search_hotels(city: str, check_in: Optional[str] = None, check_out: Optional[str] = None) -> str:
    """Searches for available hotels in a city."""
    hotels_db = {
        "paris": [{"name": "Grand Hotel Paris", "price": 150, "rating": 4.5}, {"name": "Eiffel Tower View Hotel", "price": 200, "rating": 4.8}],
        "barcelona": [{"name": "Beach Resort Barcelona", "price": 180, "rating": 4.6}, {"name": "Gothic Quarter Hotel", "price": 140, "rating": 4.4}],
        "london": [{"name": "Thames Riverside Hotel", "price": 170, "rating": 4.5}, {"name": "Westminster Palace Inn", "price": 190, "rating": 4.6}]
    }
    city_lower = city.lower().strip()
    if city_lower in hotels_db:
        hotels = hotels_db[city_lower]
        result = f"Available hotels in {city.title()}:\n\n"
        for i, hotel in enumerate(hotels, 1):
            result += f"{i}. {hotel['name']} | €{hotel['price']}/night | {hotel['rating']}/5.0\n"
        return result
    return f"No hotels found for {city}."

def check_flight_status(flight_number: Optional[str] = None, booking_id: Optional[str] = None) -> str:
    """Checks flight status."""
    if booking_id and booking_id.upper() in BOOKINGS_DB:
        flight_number = f"AA{random.randint(1000, 9999)}"
    if not flight_number: return "Please provide flight number or booking ID."
    return f"Flight {flight_number.upper()} Status: On Time | Gate: {random.choice(['A1', 'B2', 'C3'])}"

def book_hotel(hotel_name: str, city: str, check_in: str, check_out: str, guest_name: str) -> str:
    """Books a hotel room."""
    booking_id = f"BK{random.randint(100000, 999999)}"
    BOOKINGS_DB[booking_id] = {"booking_id": booking_id, "customer_name": guest_name, "hotel": hotel_name, "check_in": check_in, "check_out": check_out, "status": "confirmed", "room_type": "Standard Room"}
    return f"Hotel booking confirmed! ID: {booking_id}"

def book_taxi(pickup_location: str, destination: str, pickup_time: Optional[str] = None) -> str:
    """Books a taxi."""
    pickup_time = pickup_time or datetime.now().strftime("%H:%M")
    return f"Taxi booking confirmed! From {pickup_location} to {destination} at {pickup_time}."

def cancel_booking(booking_id: str, reason: Optional[str] = None) -> str:
    """Cancels a booking."""
    booking_id = booking_id.upper().strip()
    if booking_id in BOOKINGS_DB:
        BOOKINGS_DB[booking_id]["status"] = "cancelled"
        return f"Booking {booking_id} cancelled."
    return f"Booking {booking_id} not found."

AVAILABLE_TOOLS = [lookup_booking, search_hotels, check_flight_status, book_hotel, book_taxi, cancel_booking]
