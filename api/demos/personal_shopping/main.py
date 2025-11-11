"""
Personal Shopping Assistant API
================================

🎯 LEARNING OBJECTIVES:
This demo teaches you how to build a shopping assistant with agent memory:

1. Agent memory - Storing and retrieving user preferences
2. Recommendation systems - Generating personalized recommendations
3. Multi-agent coordination - Search, comparison, and recommendation agents
4. Context building - Using memory to build agent context

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Setup - Import libraries and configure the router
Step 2: Data Models - Define request structures with validation
Step 3: API Endpoints - Expose functionality via HTTP
Step 4: Agent Execution - Run shopping workflow with memory

Key Concept: This demo shows how agent memory enables personalized
recommendations that improve over time based on user preferences and history.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import uuid
import logging

from .shopping_agents import get_product_recommendations
from .memory import get_memory

logger = logging.getLogger(__name__)

# Create a router - groups all endpoints under /personal-shopping
router = APIRouter(prefix="/personal-shopping", tags=["personal-shopping"])

# In-memory storage for shopping sessions
shopping_sessions: Dict[str, Dict[str, Any]] = {}


# ============================================================================
# STEP 2: DATA MODELS
# ============================================================================
class ShoppingRequest(BaseModel):
    """Request for product recommendations"""
    user_query: str = Field(..., min_length=1, description="Product search query")
    user_id: Optional[str] = Field("default", description="User identifier for memory")
    budget: Optional[str] = Field(None, description="Budget constraint (e.g., 'under $100')")
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences to update")


class ShoppingResponse(BaseModel):
    """Response with shopping session status"""
    session_id: str
    status: str
    message: str
    user_query: str


class ShoppingResult(BaseModel):
    """Final shopping recommendations"""
    session_id: str
    status: str
    user_query: str
    search_results: Optional[str] = None
    comparison: Optional[str] = None
    recommendations: Optional[str] = None
    user_preferences: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class PreferenceUpdate(BaseModel):
    """Request to update user preferences"""
    user_id: str = Field("default", description="User identifier")
    preferences: Dict[str, Any] = Field(..., description="Preferences to update")


class ServiceInfo(BaseModel):
    """Health check response"""
    status: str
    service: str
    description: str


# ============================================================================
# STEP 3: BACKGROUND PROCESSING
# ============================================================================
async def process_shopping_request(
    session_id: str,
    user_query: str,
    user_id: str,
    budget: Optional[str],
    preferences: Optional[Dict[str, Any]]
):
    """Background task to get product recommendations"""
    try:
        session = shopping_sessions[session_id]
        session["status"] = "searching"
        session["message"] = "Product Search Agent: Searching for products..."
        
        # Get recommendations using multi-agent system
        result = await get_product_recommendations(
            user_query=user_query,
            user_id=user_id,
            budget=budget,
            preferences=preferences
        )
        
        # Update session with results
        session["status"] = "completed"
        session["message"] = "Recommendations generated successfully!"
        session.update(result)
        
        logger.info(f"Completed shopping request for session: {session_id}")
        
    except Exception as e:
        logger.error(f"Error processing shopping request for session {session_id}: {e}")
        if session_id in shopping_sessions:
            shopping_sessions[session_id]["status"] = "error"
            shopping_sessions[session_id]["message"] = f"Error: {str(e)}"
            shopping_sessions[session_id]["error"] = str(e)


# ============================================================================
# STEP 4: API ENDPOINTS
# ============================================================================
@router.get("/health", response_model=ServiceInfo)
async def health_check():
    """Health check endpoint"""
    return ServiceInfo(
        status="healthy",
        service="personal-shopping",
        description="AI-powered personal shopping assistant with agent memory and recommendations"
    )


@router.post("/get-recommendations", response_model=ShoppingResponse)
async def get_recommendations(
    request: ShoppingRequest,
    background_tasks: BackgroundTasks
):
    """
    Get personalized product recommendations
    
    This endpoint:
    1. Creates a new shopping session
    2. Starts background processing with multiple agents
    3. Returns session ID for status checking
    
    The workflow uses three agents:
    - Product Search Agent: Searches for products
    - Comparison Agent: Compares products
    - Recommendation Agent: Generates personalized recommendations
    
    Agent memory is used to personalize recommendations based on
    user preferences and shopping history.
    """
    try:
        session_id = str(uuid.uuid4())
        
        # Initialize session
        shopping_sessions[session_id] = {
            "session_id": session_id,
            "status": "processing",
            "message": "Initializing shopping assistant...",
            "user_query": request.user_query,
            "user_id": request.user_id,
            "budget": request.budget,
            "preferences": request.preferences
        }
        
        # Start background processing
        background_tasks.add_task(
            process_shopping_request,
            session_id,
            request.user_query,
            request.user_id,
            request.budget,
            request.preferences
        )
        
        logger.info(f"Started shopping request for session: {session_id}")
        
        return ShoppingResponse(
            session_id=session_id,
            status="processing",
            message="Shopping assistant started. Use the session_id to check status.",
            user_query=request.user_query
        )
        
    except Exception as e:
        logger.error(f"Error starting shopping request: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting shopping request: {str(e)}")


@router.get("/status/{session_id}", response_model=ShoppingResponse)
async def get_status(session_id: str):
    """Get shopping request status"""
    if session_id not in shopping_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = shopping_sessions[session_id]
    return ShoppingResponse(
        session_id=session_id,
        status=session["status"],
        message=session["message"],
        user_query=session["user_query"]
    )


@router.get("/result/{session_id}", response_model=ShoppingResult)
async def get_result(session_id: str):
    """Get final shopping recommendations"""
    if session_id not in shopping_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = shopping_sessions[session_id]
    
    if session["status"] == "processing" or session["status"] == "searching":
        raise HTTPException(
            status_code=400,
            detail="Recommendations still being generated. Please check status endpoint."
        )
    
    return ShoppingResult(
        session_id=session_id,
        status=session["status"],
        user_query=session["user_query"],
        search_results=session.get("search_results"),
        comparison=session.get("comparison"),
        recommendations=session.get("recommendations"),
        user_preferences=session.get("user_preferences"),
        error=session.get("error")
    )


@router.post("/update-preferences")
async def update_preferences(request: PreferenceUpdate):
    """
    Update user preferences for personalized recommendations
    
    This endpoint allows updating user preferences that will be used
    in future recommendations. Preferences are stored in agent memory.
    """
    try:
        memory = get_memory(request.user_id)
        
        for key, value in request.preferences.items():
            memory.update_preference(key, value)
        
        return {
            "status": "success",
            "message": "Preferences updated successfully",
            "user_id": request.user_id,
            "preferences": memory.get_preferences()
        }
        
    except Exception as e:
        logger.error(f"Error updating preferences: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating preferences: {str(e)}")


@router.get("/preferences/{user_id}")
async def get_preferences(user_id: str = "default"):
    """Get user preferences"""
    try:
        memory = get_memory(user_id)
        return {
            "user_id": user_id,
            "preferences": memory.get_preferences(),
            "recent_history": memory.get_recent_history(5),
            "interests": memory.get_interests()
        }
    except Exception as e:
        logger.error(f"Error getting preferences: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting preferences: {str(e)}")


@router.get("/learning-objectives")
async def get_learning_objectives():
    """Get learning objectives for this demo"""
    return {
        "demo": "Personal Shopping Assistant",
        "objectives": [
            "Understand agent memory and preference storage",
            "Learn recommendation systems with AI agents",
            "Implement multi-agent coordination for shopping",
            "Build personalized systems using memory",
            "Create context-aware recommendations"
        ],
        "technologies": [
            "Agent Memory",
            "DuckDuckGo Search",
            "Multi-Agent Systems",
            "Recommendation Systems",
            "FastAPI"
        ],
        "concepts": [
            "Agent Memory",
            "Recommendation Systems",
            "Multi-Agent Coordination",
            "Personalization",
            "Context Building"
        ]
    }

