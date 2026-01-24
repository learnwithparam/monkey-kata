# Travel Customer Support Assistant

Learn function calling and multi-agent workflows by building a real-world travel support assistant (like Booking.com) that helps customers with booking lookups, hotel reservations, flight status, and taxi bookings using **AutoGen**.

## Learning Objectives

Master the fundamentals of **Function Calling** and **Agentic AI** through hands-on implementation:

  - **Tool Definition:** How to create Python functions that an LLM can understand and call.
  - **Tool Calling:** How an LLM decides *which* tool to call, with *what* arguments, based on user-prompts.
  - **Agent Design:** Build a basic two-agent (User-Assistant) system with AutoGen.
  - **Tool Execution:** Configure an agent to *execute* function calls and return the results to the LLM.
  - **Multi-Agent Orchestration:** (Advanced) Scale your system from a simple two-agent pair to a multi-agent "group chat" for more complex, specialized tasks.

## System Architecture (Final Target)

This project will guide you from a simple two-agent setup to a more robust multi-agent "group chat" orchestrated by a supervisor, all wrapped in a FastAPI for web use.

```mermaid
graph TD
    A["Frontend User"] -->|1. HTTP Request| B["FastAPI Server"];
    B -->|2. initiate_chat()| C["UserProxyAgent"];
    
    subgraph "AutoGen GroupChat"
        C <--> D["GroupChatManager (Supervisor)"];
        D <--> E[BookingAgent]
        D <--> F[SearchAgent]
    end
    
    C -->|3. Tool Execution| G[Mock Database]
    B -->|4. HTTP Response| A;

    style A fill:#e1f5fe
    style B fill:#e8f5e8
    style C fill:#fce4ec
    style D fill:#f3e5f5
    style E fill:#e0f2f1
    style F fill:#e0f2f1
    style G fill:#fff9c4
```

## Quick Start

### Prerequisites

1.  **Dependencies:**
    The required dependencies are already in `api/requirements.txt`:

      * `autogen-agentchat[openai]`
      * `autogen-ext[openai]`
        These will be automatically installed when you run `make dev`.

2.  **Environment Variables:**

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

### Example Customer Queries

Once running, try these queries to see function calling in action:

  - "What's my booking status for BK123456?"
  - "Search hotels in Paris for February 15-18"
  - "Check flight status for AA1234"
  - "Book a hotel in Barcelona for March 1-5"
  - "I need a taxi from airport to Grand Hotel Paris"
  - "Cancel my booking BK123456"

-----

## Your Learning Path: Incremental Challenges

Follow these incremental challenges to build your application. Each one adds a new layer of functionality and learning.

### Challenge 1: The Basic Chat (Two Agents)

**Goal:** Get a basic AutoGen chat working between a `UserProxyAgent` (for the user) and an `AssistantAgent` (the LLM). No tools yet.

  * **Architecture:**
    ```mermaid
    graph TD
        A[UserProxyAgent] <--> B[AssistantAgent]
        
        style A fill:#fce4ec
        style B fill:#e0f7fa
    ```
  * **Your Task:**
    1.  In a new Python script, import `autogen`.
    2.  Define an `AssistantAgent` ("assistant") with a simple system message: "You are a helpful travel assistant."
    3.  Define a `UserProxyAgent` ("user\_proxy") with `human_input_mode="NEVER"` and `code_execution_config=False`.
    4.  Use `user_proxy.initiate_chat(assistant, message="Hello, who are you?")`.
  * **Key Concepts:** `UserProxyAgent`, `AssistantAgent`, `initiate_chat`, System Message.
  * **Observation:** You've created the simplest possible agentic "chat." The `UserProxyAgent` delivers the message, the `AssistantAgent` (LLM) responds, and the chat ends.

-----

### Challenge 2: The First Tool (Read-Only)

**Goal:** Introduce function calling. Give the assistant *one* tool, `lookup_booking`, and configure the user proxy to *execute* it.

  * **Architecture:**
    ```mermaid
    graph TD
        A[UserProxyAgent] <--> B[AssistantAgent]
        A -->|Calls| C["@tool def lookup_booking()"];
        
        style A fill:#fce4ec
        style B fill:#e0f7fa
        style C fill:#fff9c4
    ```
  * **Your Task:**
    1.  Create an in-memory `MOCK_BOOKINGS` dictionary (e.g., `{"BK123456": {"status": "Confirmed"}}`).
    2.  Define a Python function `lookup_booking(booking_id: str) -> str`.
    3.  Decorate it with `@tool` (from `autogen.agentchat.contrib.agent_builder.tool_utils`).
    4.  **Register the tool:** When creating your `AssistantAgent`, pass `tools=[lookup_booking]` to its `llm_config`.
    5.  **Enable execution:** When creating your `UserProxyAgent`, set `human_input_mode="NEVER"` and `code_execution_config={"executor": autogen.coding.LocalCommandLineCodeExecutor(work_dir="coding")}`. *This is how the proxy knows it's allowed to run the functions.*
    6.  Test with: `user_proxy.initiate_chat(assistant, message="What's my booking status for BK123456?")`
  * **Key Concepts:** **Function Calling**, **`@tool` Decorator**, LLM as a Router, Tool Execution, `llm_config`.
  * **Observation:** Watch the terminal\! You'll see the LLM respond not with words, but with a *function call*. The `UserProxyAgent` then runs the function, gets the result, and sends it *back* to the LLM, which then formulates a natural language answer.

-----

### Challenge 3: The "Eyes and Ears" (Expanding Read Tools)

**Goal:** Build out the full set of *information-gathering* tools.

  * **Your Task:**
    1.  Implement the other "read" tools: `Google Hotels(city: str)` and `check_flight_status(flight_id: str)`.
    2.  Decorate them with `@tool`.
    3.  Add them to the `tools` list in the `AssistantAgent`'s `llm_config`.
  * **Experiment:**
      * Try: `"Search hotels in Paris"`
      * Try: `"What's the status of flight AA123?"`
      * Try a complex query: `"My booking is BK123456. Can you check its status and also look for hotels in Paris?"`
  * **Key Concepts:** Toolset Expansion, LLM Tool Choice, Argument Inference.
  * **Observation:** The LLM is now acting as a router, correctly *choosing* which of your three tools to call based on the user's prompt. It also intelligently extracts the arguments (like "Paris" or "AA123").

-----

### Challenge 4: The "Hands" (State-Changing Tools)

**Goal:** Introduce "write" actions—tools that *change* the state of your mock database.

  * **Your Task:**
    1.  Implement the "write" tools: `book_hotel(hotel_name: str, city: str)` and `cancel_booking(booking_id: str)`.
    2.  These functions should *modify* your `MOCK_BOOKINGS` dictionary (e.g., adding a new entry or changing a status to "Cancelled").
    3.  Decorate them with `@tool` and add them to the `AssistantAgent`'s `tools` list.
  * **Experiment:**
    1.  Run a chat: `"Book the 'Grand Hotel' in Paris."`
    2.  In a *new* chat: `"What's the status of my 'Grand Hotel' booking?"` (The `lookup_booking` tool should now find it).
    3.  In a *third* chat: `"Please cancel my 'Grand Hotel' booking."`
    4.  In a *fourth* chat: `"What's the status of my 'Grand Hotel' booking now?"` (It should say "Cancelled").
  * **Key Concepts:** State Management, "Write" vs. "Read" Tools, System State.

-----

### Challenge 5: The API Wrapper (Connecting to Frontend)

**Goal:** Put your two-agent system behind a FastAPI endpoint so the frontend can talk to it.

  * **Architecture:**
    ```mermaid
    graph TD
        A["Frontend"] -->|HTTP| B["FastAPI Endpoint (/chat/stream)"];
        B -->|Manages| C[Agent Session]
        style A fill:#e1f5fe
        style B fill:#e8f5e8
        style C fill:#fce4ec
    ```
  * **Your Task:**
    1.  Create a `main.py` with FastAPI.
    2.  Create a `/chat/stream` endpoint.
    3.  Inside the endpoint, you will need to manage the agent state. **This is the hardest part.** A simple (but not scalable) way is to create *new* agents for every single request and run `initiate_chat`.
    4.  (Advanced) A better way is to use a session ID and store the agent's chat history in a dictionary, then use `user_proxy.send()` and `user_proxy.receive()` to continue a conversation.
    5.  Connect the frontend to this new endpoint.
  * **Key Concepts:** API Integration, FastAPI, Session Management, Streaming Responses, Stateless vs. Stateful.

-----

### Challenge 6 (Bonus): The "Supervisor" (Multi-Agent Chat)

**Goal:** Refactor your simple two-agent system into a more robust, specialized `GroupChat` for better task management.

  * **Architecture:**
    ```mermaid
    graph TD
        A["UserProxyAgent"] <--> B["GroupChatManager (Supervisor)"];
        B <--> C[SearchAgent]
        B <--> D[BookingAgent]
        
        style A fill:#fce4ec
        style B fill:#f3e5f5
        style C fill:#e0f2f1
        style D fill:#e0f2f1
    ```
  * **Your Task:**
    1.  Instead of one `AssistantAgent`, create *two*:
          * `SearchAgent`: Its `llm_config` only has the "read" tools (`lookup_booking`, `Google Hotels`, etc.).
          * `BookingAgent`: Its `llm_config` only has the "write" tools (`book_hotel`, `cancel_booking`).
    2.  Create a `GroupChat` and a `GroupChatManager` (this is your new "Supervisor").
    3.  Add all agents (`UserProxyAgent`, `SearchAgent`, `BookingAgent`) to the `GroupChat`.
    4.  Initiate the chat with the `GroupChatManager`.
  * **Key Concepts:** `GroupChat`, `GroupChatManager`, Multi-Agent Systems, Agent Specialization, Orchestration.
  * **Observation:** The conversation log is now much more complex. The Supervisor agent directs traffic, asking the `SearchAgent` to find info and then (if needed) asking the `BookingAgent` to perform an action. This is a far more scalable and modular pattern.

-----

### Challenge 7 (Bonus): Add More Tools

**Goal:** Extend the assistant with new tools, like the original challenges suggested.

  * **Your Task:**
    1.  Create a new function `check_loyalty_points(customer_id: str)` that returns a mock point value.
    2.  Create `book_taxi(from_location: str, to_location: str)`.
    3.  Decorate them and add them to the appropriate agent's `tools` list (e.g., `check_loyalty_points` to `SearchAgent`, `book_taxi` to `BookingAgent`).
    4.  Test by asking: "What are my loyalty points?" or "I need a taxi from the airport."
  * **Key Concepts:** Tool Expansion, Modularity.

## Configuration

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

## Key Agentic AI Concepts

### **What You'll Discover:**

1.  **Agents are "Routers":** The primary job of an LLM in an agentic system is to act as a "router." It decides if it can answer directly, or if it *must* call a function (a "tool") to get the information it needs.
2.  **Tool \> Prompt:** A well-defined tool is more reliable than a complex prompt. Instead of trying to *teach* an LLM all your booking info (which is impossible), you *give it a tool* to look up that info.
3.  **The "Executor" Agent:** In AutoGen, the `UserProxyAgent` is often co-opted to be the "tool executor." The `AssistantAgent` *suggests* the function call, and the `UserProxyAgent` *runs* the code and provides the result.
4.  **Multi-Agent Specialization:** As systems get complex, it's better to have multiple, simple, specialized agents (one for booking, one for searching) managed by a "Supervisor" than one giant, monolithic agent that does everything.
5.  **State is Your Responsibility:** The agent system doesn't "know" it booked a hotel unless your `book_hotel` tool actually changes a database or in-memory state that the `lookup_booking` tool can read from.

## Production Considerations

1.  **Security**: Never let an agent execute arbitrary code. Only give it specific, sandboxed tools. Validate all inputs from the LLM before passing them to a database or external API.
2.  **Rate Limiting**: Implement rate limiting on your API endpoint to prevent abuse.
3.  **Error Handling**: Your tools *must* be robust. What if `lookup_booking` gets an ID that doesn't exist? It should return a clear error message (e.g., "Booking not found") for the LLM to use.
4.  **Monitoring**: Log every tool call, its arguments, and its result. This is invaluable for debugging *why* an agent made a certain decision.
5.  **Caching**: Cache results from non-changing tools (like `Google Hotels` for a popular city) to reduce API calls and latency.

## Critical Thinking Questions

1.  How would you handle a tool error in a customer-facing way? If the `book_hotel` API fails, what should the agent say?
2.  What security risks exist in letting an LLM decide which function to call and with what arguments? How do you mitigate them?
3.  What if the user's request is ambiguous? "Book me a flight." How do you design the *agent* to ask follow-up questions (e.g., "Where to? On what date?") *before* it tries to call a tool?
4.  How could you add tool-result caching for frequently accessed bookings?
5.  How would you handle a "real" database instead of the mock dictionary? Where would the database connection live?

## Further Learning

  - [AutoGen AgentChat Documentation](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/index.html)
  - [AutoGen Function Calling with Tools](https://microsoft.github.io/autogen/stable//user-guide/core-user-guide/components/tools.html)
  - [OpenAI Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)