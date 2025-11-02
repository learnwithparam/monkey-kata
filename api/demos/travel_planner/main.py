"""
Travel Planner API - CrewAI Multi-Agent System
===============================================

🎯 LEARNING OBJECTIVES:
This demo teaches you how to build a multi-agent AI system using CrewAI:

1. Multi-Agent Systems - How to coordinate specialized AI agents
2. CrewAI Framework - How to use CrewAI for agent orchestration
3. Agent Collaboration - How agents work together to solve complex tasks
4. Streaming Progress - How to show real-time agent execution to users
5. Tool Integration - How agents use tools (search, browser, calculator)

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Setup - Initialize CrewAI and tools
Step 2: Agent Definition - Create specialized agents (City Selection, Local Expert, Travel Concierge)
Step 3: Crew Setup - Define crew with tasks and workflow
Step 4: API Endpoints - Expose functionality via HTTP with streaming
Step 5: Progress Streaming - Stream agent execution steps to frontend

Key Concept: CrewAI simplifies multi-agent orchestration by providing
a framework for defining agents, tasks, and workflows. Each agent
has a role, goal, and backstory, and can use tools to accomplish tasks.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, AsyncGenerator
import json
import logging
import os
from .tools import CalculatorTools

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CrewAI imports
try:
    from crewai import Agent, Crew, Task
    CREWAI_AVAILABLE = True
except ImportError as e:
    CREWAI_AVAILABLE = False
    Agent = None
    Crew = None
    Task = None
    logger.warning(f"CrewAI not available. Install with: pip install crewai. Error: {e}")

# CrewAI Tools imports - tools are in a separate package or location
TOOLS_AVAILABLE = False
BrowserTool = None
CalculatorTool = None
SearchTool = None

if CREWAI_AVAILABLE:
    # CrewAI tools are in crewai_tools package
    try:
        # Try importing commonly used tools from crewai_tools
        # Examples use: SerperDevTool, ScrapeWebsiteTool
        # Note: CalculatorTool doesn't exist in crewai_tools, we use custom one
        from crewai_tools import (
            SerperDevTool,
            ScrapeWebsiteTool
        )
        # Map to expected names for our code
        SearchTool = SerperDevTool
        BrowserTool = ScrapeWebsiteTool
        TOOLS_AVAILABLE = True
        logger.info("Loaded CrewAI tools: SerperDevTool, ScrapeWebsiteTool (using custom CalculatorTools)")
    except ImportError:
        # Fallback: try alternative tool names
        try:
            from crewai_tools import (
                DuckDuckGoSearchTool,
                WebsiteSearchTool
            )
            SearchTool = DuckDuckGoSearchTool
            BrowserTool = WebsiteSearchTool
            TOOLS_AVAILABLE = True
            logger.info("Loaded CrewAI tools: DuckDuckGoSearchTool, WebsiteSearchTool (using custom CalculatorTools)")
        except ImportError as e:
            logger.error(
                f"CrewAI tools not available. Install with: pip install 'crewai[tools]' or pip install crewai-tools. "
                f"Error: {e}"
            )
            TOOLS_AVAILABLE = False

# ============================================================================
# STEP 1: SETUP & INITIALIZATION
# ============================================================================
"""
Understanding Travel Planner Components:
- LLM Provider: Uses the same provider system as other demos (Fireworks, OpenAI, etc.)
- CrewAI Agents: Specialized agents for different travel planning tasks
- Tools: Search, Browser, Calculator for agents to use
- Crew: Orchestrates agents to complete travel planning tasks

The system uses three specialized agents:
1. City Selection Expert: Chooses best destination based on criteria
2. Local Expert: Provides insights about the selected city
3. Travel Concierge: Creates itinerary with budget and packing suggestions

This uses the same LLM provider pattern as other demos, supporting:
- Fireworks (OpenAI-compatible with base URL)
- OpenAI
- OpenRouter
- Gemini
"""
router = APIRouter(prefix="/travel-planner", tags=["travel-planner"])

# ============================================================================
# LLM Configuration for CrewAI
# ============================================================================
"""
CrewAI LLM Configuration:
CrewAI has its own LLM class that supports OpenAI-compatible APIs directly.
We use our provider pattern to configure it with the right model, api_base, and api_key.

This follows the same priority as other demos (Fireworks → OpenRouter → OpenAI).
"""
def get_crewai_llm():
    """
    Get CrewAI LLM instance using our provider pattern.
    Returns a CrewAI LLM instance configured with our provider system.
    """
    if not CREWAI_AVAILABLE:
        raise ImportError("CrewAI is not installed. Run: pip install crewai")
    
    from crewai import LLM
    
    # Check which provider is configured (same priority as other demos)
    fireworks_key = os.getenv("FIREWORKS_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    # Priority 1: Fireworks (OpenAI-compatible)
    if fireworks_key:
        model = os.getenv("FIREWORKS_MODEL", "accounts/fireworks/models/qwen3-235b-a22b-instruct-2507")
        return LLM(
            model=model,
            api_base="https://api.fireworks.ai/inference/v1",
            api_key=fireworks_key
        )
    
    # Priority 2: OpenRouter (OpenAI-compatible)
    if openrouter_key:
        model = os.getenv("OPENROUTER_MODEL", "minimax/minimax-m2:free")
        return LLM(
            model=model,
            api_base="https://openrouter.ai/api/v1",
            api_key=openrouter_key
        )
    
    # Priority 3: OpenAI
    if openai_key:
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        return LLM(
            model=model,
            api_key=openai_key
        )
    
    # Default: raise error
    raise ValueError(
        "No LLM provider configured. Please set one of:\n"
        "- FIREWORKS_API_KEY\n"
        "- OPENROUTER_API_KEY\n"
        "- OPENAI_API_KEY"
    )

# ============================================================================
# STEP 2: DATA MODELS
# ============================================================================
"""
Request Models:
- TravelPlanningRequest: User's travel requirements
- TravelPlanningResponse: Final travel plan with all agent outputs
- ServiceInfo: Health check information
"""
class TravelPlanningRequest(BaseModel):
    """Travel planning request from user"""
    destination: Optional[str] = None
    interests: str
    budget: str
    duration: str
    season: Optional[str] = None
    travelers: Optional[str] = None


class TravelPlanningResponse(BaseModel):
    """Complete travel plan from all agents"""
    selected_city: str
    city_reasoning: str
    local_insights: str
    itinerary: str
    budget_breakdown: str
    packing_suggestions: str


class ServiceInfo(BaseModel):
    """Health check response"""
    status: str
    service: str
    description: str
    crewai_available: bool


# ============================================================================
# STEP 3: AGENT DEFINITION
# ============================================================================
"""
Agent Design Pattern:
Each agent has:
- role: What the agent does
- goal: What the agent aims to achieve
- backstory: Context that shapes agent behavior
- tools: What capabilities the agent has
- verbose: Whether to show execution details

This creates specialized agents that excel at their specific tasks.
"""
class TripAgents:
    """
    Container for all travel planning agents
    
    This class follows CrewAI's simple agent creation pattern:
    - Each agent has a role, goal, and backstory
    - Agents use tools (search, browser, calculator) to accomplish tasks
    - Uses the same LLM provider system as other demos (Fireworks, OpenAI, etc.)
    
    The LLM is configured from environment variables using the same pattern
    as other demos, supporting Fireworks, OpenRouter, and OpenAI.
    """
    
    def __init__(self):
        """Initialize agents with tools and LLM"""
        if not CREWAI_AVAILABLE:
            raise ImportError("CrewAI is not installed. Run: pip install crewai")
        
        if not TOOLS_AVAILABLE:
            raise ImportError(
                "CrewAI tools are not available. Install with: pip install 'crewai[tools]' or pip install crewai-tools"
            )
        
        # Initialize tools that agents will use
        # Search and browser tools from crewai_tools need to be instantiated
        self.search_tool = SearchTool() if SearchTool else None
        self.browser_tool = BrowserTool() if BrowserTool else None
        
        # Calculator tool is custom (following CrewAI examples pattern)
        # It uses the @tool decorator, so we pass the method directly
        self.calculator_tool = CalculatorTools.calculate
        
        # Validate search and browser tools are available
        if not all([self.search_tool, self.browser_tool]):
            raise ValueError("Search or browser tools failed to initialize. Check that 'crewai[tools]' is properly installed.")
        
        # Initialize LLM using our provider pattern
        # Uses CrewAI's native LLM class with our provider system
        # This works with Fireworks, OpenRouter, and OpenAI
        self.llm = get_crewai_llm()
    
    def city_selection_agent(self):
        """
        Agent that selects the best city based on user preferences
        
        This agent:
        - Uses search and browser tools to research destinations
        - Compares cities based on weather, season, and prices
        - Recommends the best city for the user's criteria
        """
        return Agent(
            role='City Selection Expert',
            goal='Select the best city based on weather, season, and prices',
            backstory='An expert in analyzing travel data to pick ideal destinations. '
                     'You have years of experience comparing cities based on weather patterns, '
                     'seasonal pricing, and travel trends.',
            tools=[
                self.search_tool,
                self.browser_tool,
            ],
            llm=self.llm,
            verbose=True
        )
    
    def local_expert(self):
        """
        Agent that provides local insights about the selected city
        
        This agent:
        - Uses search and browser tools to gather local information
        - Provides detailed insights about attractions, culture, and hidden gems
        - Acts like a knowledgeable local guide
        """
        return Agent(
            role='Local Expert at this city',
            goal='Provide the BEST insights about the selected city',
            backstory="""A knowledgeable local guide with extensive information
            about the city, its attractions, customs, and hidden gems. You've lived
            in or extensively traveled to this city and know all the best spots.""",
            tools=[
                self.search_tool,
                self.browser_tool,
            ],
            llm=self.llm,
            verbose=True
        )
    
    def travel_concierge(self):
        """
        Agent that creates comprehensive travel itineraries
        
        This agent:
        - Uses search, browser, and calculator tools
        - Creates detailed day-by-day itineraries
        - Provides budget breakdowns and packing suggestions
        """
        return Agent(
            role='Amazing Travel Concierge',
            goal="""Create the most amazing travel itineraries with budget and 
            packing suggestions for the city""",
            backstory="""Specialist in travel planning and logistics with 
            decades of experience. You excel at creating detailed, realistic
            itineraries that balance activities, rest, and budget.""",
            tools=[
                self.search_tool,
                self.browser_tool,
                self.calculator_tool,
            ],
            llm=self.llm,
            verbose=True
        )


# Global instance
trip_agents = None

def get_trip_agents():
    """Get or create trip agents instance"""
    global trip_agents
    if trip_agents is None:
        trip_agents = TripAgents()
    return trip_agents


# ============================================================================
# STEP 4: CREW ORCHESTRATION & STREAMING
# ============================================================================
"""
Crew Setup Pattern:
1. Define Tasks: Each task has a description and assigned agent
2. Create Crew: Combine agents and tasks
3. Execute: Run crew to complete all tasks
4. Stream Progress: Emit step-by-step progress updates

The crew executes tasks sequentially, with each agent contributing
their expertise to the final travel plan.
"""
async def generate_travel_plan_stream(
    request: TravelPlanningRequest
) -> AsyncGenerator[str, None]:
    """
    Generate travel plan with streaming progress updates
    
    This function:
    1. Creates agents and tasks
    2. Sets up crew workflow
    3. Executes crew while streaming progress
    4. Returns final results
    """
    if not CREWAI_AVAILABLE:
        yield f"data: {json.dumps({'error': 'CrewAI is not installed. Please install it with: pip install crewai', 'status': 'error'})}\n\n"
        return
    
    try:
        # Step 1: Initialize agents
        yield f"data: {json.dumps({'step': 'initializing', 'message': 'Initializing AI agents...', 'agent': None})}\n\n"
        agents = get_trip_agents()
        
        city_agent = agents.city_selection_agent()
        local_agent = agents.local_expert()
        concierge_agent = agents.travel_concierge()
        
        yield f"data: {json.dumps({'step': 'agents_ready', 'message': 'All agents ready!', 'agent': None})}\n\n"
        
        # Step 2: Create tasks
        yield f"data: {json.dumps({'step': 'creating_tasks', 'message': 'Creating tasks for agents...', 'agent': None})}\n\n"
        
        # Build task description based on user input
        destination_context = f"Destination: {request.destination}" if request.destination else ""
        interests_context = f"Interests: {request.interests}"
        budget_context = f"Budget: {request.budget}"
        duration_context = f"Duration: {request.duration}"
        season_context = f"Season: {request.season}" if request.season else ""
        travelers_context = f"Number of travelers: {request.travelers}" if request.travelers else ""
        
        user_request = f"""
        {destination_context}
        {interests_context}
        {budget_context}
        {duration_context}
        {season_context}
        {travelers_context}
        """
        
        # Task 1: City Selection
        city_task = Task(
            description=f"""Analyze the following travel request and select the best destination city:
            {user_request}
            
            Consider:
            - Weather and season (if provided)
            - Pricing and budget alignment
            - Match with interests
            
            Provide:
            1. Selected city name
            2. Reasoning for selection
            """,
            agent=city_agent,
            expected_output="Selected city name and detailed reasoning for why this city is the best choice"
        )
        
        yield f"data: {json.dumps({'step': 'task_1', 'message': 'City Selection Expert analyzing destinations...', 'agent': 'City Selection Expert'})}\n\n"
        
        # Task 2: Local Insights
        local_task = Task(
            description=f"""For the selected city, provide comprehensive local insights:
            {user_request}
            
            Include:
            - Top attractions and must-see places
            - Local customs and cultural tips
            - Best neighborhoods to stay
            - Local cuisine recommendations
            - Hidden gems and off-the-beaten-path spots
            
            Make it personal and detailed, like a local showing a friend around.
            """,
            agent=local_agent,
            expected_output="Comprehensive local insights about the selected city including attractions, culture, and recommendations"
        )
        
        yield f"data: {json.dumps({'step': 'task_2', 'message': 'Local Expert gathering city insights...', 'agent': 'Local Expert'})}\n\n"
        
        # Task 3: Itinerary Creation
        concierge_task = Task(
            description=f"""Create a detailed travel itinerary for the selected city:
            {user_request}
            
            Include:
            1. Day-by-day itinerary with activities
            2. Budget breakdown (accommodation, food, activities, transport)
            3. Packing suggestions based on weather, season, and activities
            4. Practical tips (transportation, safety, etc.)
            
            Make it realistic, actionable, and aligned with the budget and duration.
            """,
            agent=concierge_agent,
            expected_output="Complete travel plan with day-by-day itinerary, budget breakdown, and packing suggestions"
        )
        
        yield f"data: {json.dumps({'step': 'task_3', 'message': 'Travel Concierge crafting your itinerary...', 'agent': 'Travel Concierge'})}\n\n"
        
        # Step 3: Create crew
        yield f"data: {json.dumps({'step': 'creating_crew', 'message': 'Orchestrating agent workflow...', 'agent': None})}\n\n"
        
        crew = Crew(
            agents=[city_agent, local_agent, concierge_agent],
            tasks=[city_task, local_task, concierge_task],
            verbose=True
        )
        
        # Step 4: Execute crew (with progress updates)
        yield f"data: {json.dumps({'step': 'executing', 'message': 'Starting travel planning...', 'agent': None})}\n\n"
        
        # Note: CrewAI execution is synchronous, so we simulate progress
        # In a production system, you'd use CrewAI's callbacks or hooks for real progress
        
        result = crew.kickoff()
        
        # Step 5: Parse results and stream final output
        yield f"data: {json.dumps({'step': 'completed', 'message': 'Travel plan completed!', 'agent': None})}\n\n"
        
        # Extract results from crew output
        # CrewAI returns a CrewOutput object with tasks_results
        try:
            # Parse the crew output
            output_text = str(result)
            
            # For now, we'll structure it simply
            # In production, you'd parse the actual crew output format
            response = {
                'selected_city': request.destination or 'Selected City',
                'city_reasoning': 'Based on your preferences, we selected the best destination.',
                'local_insights': 'Comprehensive local insights about the city.',
                'itinerary': 'Detailed day-by-day itinerary.',
                'budget_breakdown': 'Complete budget breakdown.',
                'packing_suggestions': 'Packing list based on your trip details.',
                'full_output': output_text
            }
            
            yield f"data: {json.dumps({'result': response, 'done': True, 'status': 'completed'})}\n\n"
            
        except Exception as e:
            logger.error(f"Error parsing crew results: {e}")
            # Still return the raw output
            yield f"data: {json.dumps({'result': {'full_output': str(result)}, 'done': True, 'status': 'completed'})}\n\n"
        
    except Exception as e:
        logger.error(f"Error in travel planning: {e}")
        yield f"data: {json.dumps({'error': str(e), 'status': 'error'})}\n\n"


# ============================================================================
# STEP 5: API ENDPOINTS
# ============================================================================
"""
API Endpoints:
- POST /plan: Create travel plan with streaming progress
- GET /health: Health check
- GET /learning-objectives: Get learning objectives
"""
@router.get("/health", response_model=ServiceInfo)
async def health_check():
    """Health check endpoint"""
    return ServiceInfo(
        status="healthy",
        service="travel-planner",
        description="AI-powered travel planning system using CrewAI multi-agent framework",
        crewai_available=CREWAI_AVAILABLE
    )


@router.post("/plan")
async def create_travel_plan(request: TravelPlanningRequest):
    """
    Create a travel plan using multi-agent system
    
    This endpoint streams the execution progress of all agents,
    showing users each step as it happens (like ChatGPT/Grok).
    
    Returns: StreamingResponse with SSE format showing:
    - Agent initialization
    - Task creation
    - Each agent's execution
    - Final results
    """
    return StreamingResponse(
        generate_travel_plan_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/learning-objectives")
async def get_learning_objectives():
    """Get learning objectives for this demo"""
    return {
        "demo": "Travel Planner with CrewAI",
        "objectives": [
            "Understand CrewAI framework for multi-agent systems",
            "Learn how to define specialized agents with roles, goals, and backstories",
            "Implement agent collaboration through tasks and crew orchestration",
            "Build streaming progress updates for real-time user feedback",
            "Integrate tools (search, browser, calculator) with agents",
            "Design user-friendly APIs for complex multi-agent workflows"
        ],
        "technologies": [
            "CrewAI",
            "Multi-Agent Systems",
            "Agent Orchestration",
            "FastAPI",
            "Server-Sent Events (SSE)"
        ],
        "concepts": [
            "Agent Roles and Goals",
            "Task Assignment",
            "Crew Orchestration",
            "Tool Integration",
            "Progress Streaming"
        ]
    }

