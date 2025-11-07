# Travel Customer Support Assistant

Learn function calling and tool integration by building a real-world travel support assistant (like Booking.com) that helps customers with booking lookups, hotel reservations, flight status, and taxi bookings.

## 🎯 Learning Objectives

Master the fundamentals of **Function Calling and Tool Integration** through hands-on implementation:

1. **Function Calling** - How agents use tools to access booking data
2. **Support Tool Definition** - How to create tools for customer support
3. **AutoGen Integration** - How to build support agents with AutoGen
4. **Production Patterns** - How to structure tools for customer support

## 📚 Real-World Use Case

### Travel Customer Support Assistant

A practical customer support assistant that helps travelers with:
- **Booking Lookups** - Find and check booking status
- **Hotel Search** - Search available hotels and make reservations
- **Flight Status** - Check flight information and status
- **Taxi Booking** - Arrange transportation
- **Booking Modifications** - Cancel or modify bookings

### Tools (Function Calling)

Tools allow the support assistant to access booking data. When a customer asks "What's my booking status for BK123456?", the assistant:

1. Recognizes it needs to look up booking data
2. Calls the `lookup_booking` tool
3. Gets the booking information
4. Incorporates it into a helpful customer support response

### External Service Integration

Tools can connect to external travel services:
- **Hotel Booking Systems** - Connect to hotel reservation APIs
- **Taxi Services** - Integrate with taxi/ride-sharing companies
- **Flight Systems** - Access airline booking systems
- **Payment Processing** - Handle booking payments securely

## 🛠️ Available Support Tools

This demo includes:

1. **Booking Lookup** - Find customer booking information
2. **Hotel Search** - Search available hotels by city
3. **Flight Status** - Check flight information and status
4. **Hotel Booking** - Book hotels via hotel booking system
5. **Taxi Booking** - Book taxis via taxi service
6. **Cancel Booking** - Cancel bookings via booking system

## 🚀 Quick Start

```bash
# Start the demo
make dev

# Visit: http://localhost:4020/demos/travel-support
```

### Prerequisites

1. **Dependencies:**

   The required dependencies are already included in `api/requirements.txt`:
   - `autogen-agentchat[openai]` - AutoGen AgentChat API
   - `autogen-ext[openai]` - AutoGen extensions for OpenAI

   These will be automatically installed when you run `make dev` or `make install`.

2. **Environment Variables:**

   ```bash
   # In api/.env
   # Required: LLM API Key
   OPENAI_API_KEY=your-key-here
   # OR
   FIREWORKS_API_KEY=your-key-here

   # Optional: Model configuration
   OPENAI_MODEL=gpt-4o-mini
   OPENAI_BASE_URL=https://api.fireworks.ai/inference/v1  # For Fireworks
   ```

### Running the Demo

#### Option 1: Docker (Recommended)

```bash
# Start all services (API and Frontend)
make dev

# Visit: http://localhost:4020/demos/travel-support
```

#### Option 2: Manual (Local Development)

```bash
# First, install dependencies
make install

# Terminal 1: Start API server
cd api
python -m uvicorn main:app --reload --port 8000

# Terminal 2: Start Frontend
cd frontend
npm run dev

# Visit: http://localhost:4020/demos/travel-support
```

**Note:** The API will be available at `http://localhost:8000` and the frontend at `http://localhost:4020`. Make sure your `api/.env` file has the required API keys.

## 🎯 Example Customer Queries

Try these queries to see function calling in action:

- "What's my booking status for BK123456?"
- "Search hotels in Paris for February 15-18"
- "Check flight status for AA1234"
- "Book a hotel in Barcelona for March 1-5"
- "I need a taxi from airport to Grand Hotel Paris"
- "Cancel my booking BK123456"

### How It Works

1. Customer sends a support request
2. LLM analyzes the request
3. If booking data is needed, LLM calls lookup tool
4. If booking action is needed, LLM calls booking tool
5. Tool executes and returns result
6. LLM incorporates result into helpful response
7. Response is streamed back to customer

## 📖 Code Structure

```
main.py
├── Support Tools (Step 3)
│   ├── lookup_booking()
│   ├── search_hotels()
│   └── check_flight_status()
├── Booking Tools (Step 4)
│   ├── book_hotel()
│   ├── book_taxi()
│   └── cancel_booking()
├── Agent Setup (Step 5)
│   └── create_agent_with_tools()
└── API Endpoints (Step 6)
    ├── POST /chat/stream
    ├── GET /tools
    ├── GET /sessions/{session_id}
    └── GET /health
```

## 🎓 Learning Challenges

Follow these incremental challenges to build your application. Each one adds a new layer of functionality and learning.

### Challenge 1: Add a Support Tool

**Goal:** Extend the assistant with a new tool for checking loyalty program points or rewards.

- **Your Task:**
  1. Create a new function `check_loyalty_points(customer_id: str)` that returns loyalty points
  2. Add it to the `AVAILABLE_TOOLS` list
  3. The AutoGen agent will automatically detect and use the new tool (no manual registration needed!)
  4. Test it by asking "What are my loyalty points?"

- **Key Concepts:** Tool Definition, AutoGen Automatic Tool Detection, Function Calling.

-----

### Challenge 2: Integrate Real Hotel Booking API

**Goal:** Connect to a real hotel booking API instead of using simulated data.

- **Your Task:**
  1. Choose a hotel booking API (e.g., Booking.com API, Expedia API, Amadeus API)
  2. Replace the `book_hotel()` function to make real API calls
  3. Handle API errors gracefully
  4. Update the booking database with real booking confirmations

- **Key Concepts:** External API Integration, Error Handling, HTTP Requests.

-----

### Challenge 3: Add Booking History

**Goal:** Track and display customer booking history across multiple bookings.

- **Your Task:**
  1. Extend the booking database structure to track booking history
  2. Create a new tool `get_booking_history(customer_name: str)` 
  3. Update the database when new bookings are made
  4. Display booking history in the chat interface

- **Key Concepts:** Data Modeling, Database Design, Tool Design.

-----

### Challenge 4: Add Payment Processing

**Goal:** Integrate payment processing for booking payments.

- **Your Task:**
  1. Create a new tool `process_payment(booking_id: str, amount: float, payment_method: str)`
  2. Integrate with a payment API (e.g., Stripe, PayPal)
  3. Update booking status after successful payment
  4. Handle payment failures gracefully

- **Key Concepts:** Payment Integration, Security, Error Handling.

## 🏗️ Production Considerations

1. **Security**: Validate and secure booking data access
2. **Rate Limiting**: Limit tool calls per customer/session
3. **Error Handling**: Gracefully handle booking system failures
4. **Monitoring**: Track support tool usage and performance
5. **Caching**: Cache frequently accessed booking data
6. **Authentication**: Secure customer data access

## 📚 Further Reading

- [AutoGen AgentChat Documentation](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/index.html)
- [AutoGen Function Calling with Tools](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/tools.html)
- [AutoGen FastAPI Example](https://github.com/microsoft/autogen/tree/main/python/samples/agentchat_fastapi)
- [Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)

## ❓ Reflection Questions

1. How would you handle tool errors in a customer support context?
2. What security considerations exist for booking tool execution?
3. How would you rate limit tool usage for customer support?
4. How could you add tool result caching for frequently accessed bookings?
5. What monitoring would you add for production support systems?

