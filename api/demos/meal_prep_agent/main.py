"""
30-Day Meal Prep Agent with Human-in-the-Loop
==============================================

🎯 LEARNING OBJECTIVES:
This demo teaches you how to build a real-world meal prep assistant with human-in-the-loop:

1. Human-in-the-Loop Pattern - How to integrate human oversight and approval at each step
2. AutoGen Integration - How to build agents that request human approval
3. Step-by-Step Workflows - How to manage multi-step processes with interruption capability
4. PDF Generation - How to export final meal plans as downloadable PDFs
5. Production Patterns - How to structure approval systems for meal planning applications

📚 REAL-WORLD USE CASE:
A 30-Day Meal Prep Agent that helps users create personalized meal plans:
- Collects dietary preferences, restrictions, and goals
- Generates meal suggestions step-by-step
- Requests human approval at each step (preferences, meal selection, final plan)
- Allows users to interrupt, modify, or redo any step
- Exports final approved meal plan as PDF

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Setup - Import libraries and configure the router
Step 2: Data Models - Define request structures with validation
Step 3: Meal Planning Tools - Create tools for meal generation and nutrition calculation
Step 4: Agent Setup - Configure AutoGen assistant with tools
Step 5: Approval System - Human-in-the-loop approval workflow
Step 6: PDF Generation - Export meal plans as PDFs
Step 7: API Endpoints - Expose functionality via HTTP

Key Concept: This assistant demonstrates human-in-the-loop by requiring
human approval at each step, showing how AI can assist but not replace
human judgment in meal planning decisions.
"""

# ============================================================================
# STEP 1: SETUP & IMPORTS
# ============================================================================
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, AsyncGenerator
from enum import Enum
import json
import os
from datetime import datetime, timedelta
import logging
import random
import uuid
from io import BytesIO

from utils.llm_provider import get_provider_config

# AutoGen imports
try:
    from autogen_agentchat.agents import AssistantAgent
    from autogen_agentchat.messages import (
        TextMessage,
        ModelClientStreamingChunkEvent,
        ToolCallRequestEvent,
        ToolCallExecutionEvent,
    )
    from autogen_agentchat.base import Response
    from autogen_core import CancellationToken
    from autogen_ext.models.openai import OpenAIChatCompletionClient
    # Try to import Gemini client if available
    try:
        from autogen_ext.models.gemini import GeminiChatCompletionClient
        GEMINI_CLIENT_AVAILABLE = True
    except ImportError:
        GEMINI_CLIENT_AVAILABLE = False
        GeminiChatCompletionClient = None
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    AssistantAgent = None
    TextMessage = None
    ModelClientStreamingChunkEvent = None
    ToolCallRequestEvent = None
    ToolCallExecutionEvent = None
    Response = None
    CancellationToken = None
    OpenAIChatCompletionClient = None
    GEMINI_CLIENT_AVAILABLE = False
    GeminiChatCompletionClient = None

# PDF generation
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/meal-prep", tags=["meal-prep"])

# ============================================================================
# DATABASE & STATE (In-Memory Storage)
# ============================================================================
# In-memory state for demo (use database in production)
agent_sessions: Dict[str, Dict[str, Any]] = {}
pending_approvals: Dict[str, Dict[str, Any]] = {}
meal_plans: Dict[str, Dict[str, Any]] = {}

# Sample meal database (in production, this would be a real database)
MEAL_DATABASE = {
    "breakfast": [
        {"name": "Overnight Oats", "calories": 350, "protein": 12, "carbs": 55, "fat": 8, "prep_time": 5, "ingredients": ["oats", "milk", "berries", "honey"]},
        {"name": "Greek Yogurt Bowl", "calories": 280, "protein": 20, "carbs": 30, "fat": 6, "prep_time": 5, "ingredients": ["greek yogurt", "granola", "berries", "honey"]},
        {"name": "Avocado Toast", "calories": 320, "protein": 10, "carbs": 35, "fat": 15, "prep_time": 10, "ingredients": ["bread", "avocado", "eggs", "salt"]},
        {"name": "Scrambled Eggs", "calories": 250, "protein": 18, "carbs": 2, "fat": 18, "prep_time": 10, "ingredients": ["eggs", "butter", "salt", "pepper"]},
        {"name": "Smoothie Bowl", "calories": 300, "protein": 15, "carbs": 45, "fat": 8, "prep_time": 10, "ingredients": ["banana", "berries", "yogurt", "granola"]},
    ],
    "lunch": [
        {"name": "Grilled Chicken Salad", "calories": 400, "protein": 35, "carbs": 20, "fat": 18, "prep_time": 20, "ingredients": ["chicken", "lettuce", "tomatoes", "dressing"]},
        {"name": "Quinoa Bowl", "calories": 450, "protein": 18, "carbs": 65, "fat": 12, "prep_time": 25, "ingredients": ["quinoa", "vegetables", "chickpeas", "tahini"]},
        {"name": "Turkey Wrap", "calories": 380, "protein": 25, "carbs": 40, "fat": 12, "prep_time": 10, "ingredients": ["tortilla", "turkey", "lettuce", "mayo"]},
        {"name": "Lentil Soup", "calories": 320, "protein": 18, "carbs": 45, "fat": 8, "prep_time": 30, "ingredients": ["lentils", "vegetables", "spices", "broth"]},
        {"name": "Salmon Bowl", "calories": 500, "protein": 35, "carbs": 50, "fat": 18, "prep_time": 25, "ingredients": ["salmon", "rice", "vegetables", "sauce"]},
    ],
    "dinner": [
        {"name": "Baked Salmon", "calories": 450, "protein": 40, "carbs": 15, "fat": 25, "prep_time": 30, "ingredients": ["salmon", "vegetables", "olive oil", "lemon"]},
        {"name": "Chicken Stir Fry", "calories": 420, "protein": 35, "carbs": 35, "fat": 15, "prep_time": 25, "ingredients": ["chicken", "vegetables", "soy sauce", "rice"]},
        {"name": "Vegetarian Pasta", "calories": 480, "protein": 18, "carbs": 70, "fat": 12, "prep_time": 20, "ingredients": ["pasta", "vegetables", "tomato sauce", "cheese"]},
        {"name": "Beef and Broccoli", "calories": 500, "protein": 38, "carbs": 40, "fat": 18, "prep_time": 25, "ingredients": ["beef", "broccoli", "soy sauce", "rice"]},
        {"name": "Turkey Meatballs", "calories": 400, "protein": 32, "carbs": 30, "fat": 16, "prep_time": 35, "ingredients": ["turkey", "breadcrumbs", "pasta", "sauce"]},
    ],
    "snack": [
        {"name": "Apple with Almonds", "calories": 200, "protein": 6, "carbs": 25, "fat": 10, "prep_time": 2, "ingredients": ["apple", "almonds"]},
        {"name": "Protein Shake", "calories": 180, "protein": 25, "carbs": 8, "fat": 4, "prep_time": 3, "ingredients": ["protein powder", "milk", "banana"]},
        {"name": "Hummus and Veggies", "calories": 150, "protein": 6, "carbs": 15, "fat": 8, "prep_time": 5, "ingredients": ["hummus", "carrots", "celery"]},
        {"name": "Greek Yogurt", "calories": 120, "protein": 15, "carbs": 10, "fat": 3, "prep_time": 1, "ingredients": ["greek yogurt", "berries"]},
    ],
}

# ============================================================================
# STEP 2: DATA MODELS
# ============================================================================
class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class StepStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"


class MealPrepRequest(BaseModel):
    """Request to start meal prep planning"""
    dietary_preferences: List[str] = Field(default=[], description="Dietary preferences (e.g., vegetarian, vegan, keto)")
    dietary_restrictions: List[str] = Field(default=[], description="Dietary restrictions (e.g., gluten-free, dairy-free, nut-free)")
    calorie_goal: Optional[int] = Field(None, ge=1200, le=4000, description="Daily calorie goal")
    protein_goal: Optional[int] = Field(None, ge=0, le=300, description="Daily protein goal (grams)")
    budget_per_week: Optional[float] = Field(None, gt=0, description="Budget per week in dollars")
    cooking_skill_level: str = Field("intermediate", description="Cooking skill level: beginner, intermediate, advanced")
    meal_prep_days: int = Field(2, ge=1, le=7, description="Number of days to meal prep at once")
    session_id: Optional[str] = Field(None, description="Optional session ID")


class ChatRequest(BaseModel):
    """Request to chat with the meal prep assistant"""
    message: str = Field(..., min_length=1, description="The user's message or question")
    session_id: Optional[str] = Field(None, description="Optional session ID for conversation continuity")
    plan_id: Optional[str] = Field(None, description="Optional plan ID for contextual chat")


class ApprovalRequest(BaseModel):
    """Request to approve or reject a step"""
    approval_id: str = Field(..., description="Approval ID")
    decision: str = Field(..., description="Decision: 'approve' or 'reject'")
    feedback: Optional[str] = Field(None, description="Optional feedback or modification request")


class ApprovalResponse(BaseModel):
    """Approval information"""
    approval_id: str
    step_name: str
    step_number: int
    content: Dict[str, Any]
    status: ApprovalStatus
    created_at: str
    reviewed_at: Optional[str] = None
    feedback: Optional[str] = None


class MealPlan(BaseModel):
    """Final meal plan"""
    plan_id: str
    session_id: str
    preferences: Dict[str, Any]
    meals: List[Dict[str, Any]]
    shopping_list: List[Dict[str, Any]]
    nutrition_summary: Dict[str, Any]
    created_at: str
    approved_at: Optional[str] = None


# ============================================================================
# STEP 3: MEAL PLANNING TOOLS
# ============================================================================
def get_dietary_meal_suggestions(
    meal_type: str,
    dietary_preferences: List[str],
    dietary_restrictions: List[str],
    calorie_range: Optional[tuple] = None
) -> List[Dict[str, Any]]:
    """
    Gets meal suggestions based on dietary preferences and restrictions.
    
    Args:
        meal_type: Type of meal (breakfast, lunch, dinner, snack)
        dietary_preferences: List of dietary preferences
        dietary_restrictions: List of dietary restrictions
        calorie_range: Optional tuple of (min, max) calories
    
    Returns:
        List of meal suggestions matching criteria
    """
    meals = MEAL_DATABASE.get(meal_type, [])
    
    # Filter by restrictions
    filtered_meals = []
    for meal in meals:
        skip = False
        ingredients_lower = [ing.lower() for ing in meal.get("ingredients", [])]
        
        # Check restrictions
        if "dairy-free" in dietary_restrictions:
            dairy_items = ["milk", "yogurt", "cheese", "butter"]
            if any(item in ingredients_lower for item in dairy_items):
                skip = True
        
        if "gluten-free" in dietary_restrictions:
            gluten_items = ["bread", "pasta", "oats", "tortilla"]
            if any(item in ingredients_lower for item in gluten_items):
                skip = True
        
        if "nut-free" in dietary_restrictions:
            nut_items = ["almonds", "nuts"]
            if any(item in ingredients_lower for item in nut_items):
                skip = True
        
        if "vegetarian" in dietary_preferences or "vegan" in dietary_preferences:
            meat_items = ["chicken", "turkey", "beef", "salmon"]
            if any(item in ingredients_lower for item in meat_items):
                skip = True
        
        if "vegan" in dietary_preferences:
            animal_items = ["eggs", "milk", "yogurt", "cheese", "butter"]
            if any(item in ingredients_lower for item in animal_items):
                skip = True
        
        if not skip:
            # Filter by calorie range if provided
            if calorie_range:
                min_cal, max_cal = calorie_range
                if min_cal <= meal["calories"] <= max_cal:
                    filtered_meals.append(meal)
            else:
                filtered_meals.append(meal)
    
    return filtered_meals[:5]  # Return top 5 suggestions


def calculate_daily_nutrition(meals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculates total daily nutrition from selected meals.
    
    Args:
        meals: List of meal dictionaries
    
    Returns:
        Dictionary with total calories, protein, carbs, fat
    """
    total_calories = sum(meal.get("calories", 0) for meal in meals)
    total_protein = sum(meal.get("protein", 0) for meal in meals)
    total_carbs = sum(meal.get("carbs", 0) for meal in meals)
    total_fat = sum(meal.get("fat", 0) for meal in meals)
    
    return {
        "calories": total_calories,
        "protein": total_protein,
        "carbs": total_carbs,
        "fat": total_fat,
        "protein_percentage": round((total_protein * 4 / total_calories * 100) if total_calories > 0 else 0, 1),
        "carbs_percentage": round((total_carbs * 4 / total_calories * 100) if total_calories > 0 else 0, 1),
        "fat_percentage": round((total_fat * 9 / total_calories * 100) if total_calories > 0 else 0, 1),
    }


def generate_shopping_list(meals: List[Dict[str, Any]], days: int = 7) -> List[Dict[str, Any]]:
    """
    Generates a shopping list from selected meals.
    
    Args:
        meals: List of meal dictionaries
        days: Number of days to plan for
    
    Returns:
        List of shopping items with quantities
    """
    ingredient_counts: Dict[str, int] = {}
    
    for meal in meals:
        for ingredient in meal.get("ingredients", []):
            ingredient_counts[ingredient] = ingredient_counts.get(ingredient, 0) + days
    
    shopping_list = []
    for ingredient, quantity in ingredient_counts.items():
        shopping_list.append({
            "ingredient": ingredient,
            "quantity": quantity,
            "unit": "servings"  # Simplified for demo
        })
    
    return sorted(shopping_list, key=lambda x: x["ingredient"])


def request_human_approval(
    step_name: str,
    step_number: int,
    content: Dict[str, Any],
    session_id: str
) -> str:
    """
    Requests human approval for a meal prep step.
    
    Args:
        step_name: Name of the step (e.g., "preferences", "meal_selection", "final_plan")
        step_number: Step number in the workflow
        content: Content to be approved
        session_id: Session ID
    
    Returns:
        Approval ID for tracking
    """
    approval_id = str(uuid.uuid4())
    
    pending_approvals[approval_id] = {
        "approval_id": approval_id,
        "step_name": step_name,
        "step_number": step_number,
        "content": content,
        "status": ApprovalStatus.PENDING,
        "session_id": session_id,
        "created_at": datetime.now().isoformat(),
        "reviewed_at": None,
        "feedback": None
    }
    
    return f"Human approval requested for {step_name}. Approval ID: {approval_id}. Status: Pending review."


# List of available tools
AVAILABLE_TOOLS = [
    get_dietary_meal_suggestions,
    calculate_daily_nutrition,
    generate_shopping_list,
    request_human_approval
]


# ============================================================================
# STEP 4: AGENT SETUP (AutoGen)
# ============================================================================
def create_model_client():
    """Creates a model client for the AutoGen agent"""
    if not AUTOGEN_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="AutoGen not available. Install with: pip install 'autogen-agentchat[openai]'"
        )
    
    try:
        config = get_provider_config()
        provider_name = config["provider_name"]
        
        # Use Gemini's native client if available
        if provider_name == "gemini" and GEMINI_CLIENT_AVAILABLE:
            return GeminiChatCompletionClient(
                api_key=config["api_key"],
                model=config["model"],
            )
        
        # Build AutoGen client config for OpenAI-compatible providers
        client_config = {
            "api_key": config["api_key"],
            "model": config["model"],
        }
        
        # Add base_url if provided
        if config["base_url"]:
            client_config["base_url"] = config["base_url"]
            if provider_name == "fireworks":
                family = "llama"
            elif provider_name == "openrouter":
                family = "gpt-4o"
            else:
                family = "gpt-4o"
            
            client_config["model_info"] = {
                "function_calling": True,
                "json_output": False,
                "vision": False,
                "family": family,
            }
        
        return OpenAIChatCompletionClient(**client_config)
    except Exception as e:
        logger.error(f"Error creating model client: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create model client: {str(e)}"
        )


def create_agent_with_tools(session_id: str) -> AssistantAgent:
    """Creates an AutoGen agent with meal planning tools"""
    if not AUTOGEN_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="AutoGen not available. Install with: pip install 'autogen-agentchat[openai]'"
        )
    
    try:
        model_client = create_model_client()
        
        agent = AssistantAgent(
            name="meal_prep_assistant",
            model_client=model_client,
            system_message="""You are a professional meal prep planning assistant.
Your role is to help users create personalized 30-day meal plans through a step-by-step conversational process.

WORKFLOW STEPS:
1. **Step 1: Collect Preferences** - Ask about dietary preferences, restrictions, goals, and constraints
2. **Step 2: Generate Meal Suggestions** - Use get_dietary_meal_suggestions() to suggest meals for each meal type
3. **Step 3: Calculate Nutrition** - Use calculate_daily_nutrition() to verify nutrition goals are met
4. **Step 4: Generate Shopping List** - Use generate_shopping_list() to create shopping list
5. **Step 5: Request Approval** - Use request_human_approval() at each step to get user approval

IMPORTANT GUIDELINES:
- Always work step-by-step and clearly communicate what step you're on
- After each step, request human approval using request_human_approval()
- Wait for user approval before proceeding to the next step
- If user rejects or requests changes, modify accordingly and re-request approval
- Be conversational and friendly, like ChatGPT
- Format your responses with clear sections and line breaks
- Use the available tools to generate meal suggestions and calculate nutrition
- Always explain what you're doing and why
- Make sure to get approval for: preferences, meal selections, and final plan

RESPONSE FORMAT:
- Clearly indicate which step you're on (e.g., "Step 1: Collecting Your Preferences")
- Explain what you're doing
- Show the results or ask questions
- Request approval before moving to the next step""",
            tools=AVAILABLE_TOOLS,
            model_client_stream=True,
            reflect_on_tool_use=True,
        )
        
        return agent
        
    except Exception as e:
        logger.error(f"Error setting up AutoGen agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize AutoGen agent: {str(e)}"
        )


# ============================================================================
# STEP 5: AGENTIC WORKFLOW SYSTEM
# ============================================================================
async def generate_chat_stream(
    session_id: str,
    message: str
) -> AsyncGenerator[str, None]:
    """Generate streaming chat response with tool usage using AutoGen"""
    try:
        # Initialize session if needed
        if session_id not in agent_sessions:
            agent_sessions[session_id] = {
                "session_id": session_id,
                "messages": [],
                "tool_calls": [],
                "created_at": datetime.now().isoformat(),
                "message_count": 0,
                "tool_call_count": 0,
                "current_step": 1,
                "step_status": {}
            }
        
        session = agent_sessions[session_id]
        
        # Create agent with tools
        agent = create_agent_with_tools(session_id)
        
        # Add current user message to session
        session["messages"].append({"role": "user", "content": message})
        session["message_count"] += 1
        
        # Track tool calls and response
        tool_calls_used = []
        final_response = ""
        approval_id = None
        
        # Process message through agent with streaming
        async for event in agent.on_messages_stream(
            messages=[TextMessage(content=message, source="user")],
            cancellation_token=CancellationToken(),
        ):
            # Handle tool call requests
            if isinstance(event, ToolCallRequestEvent):
                for tool_call in event.content:
                    tool_name = getattr(tool_call, 'name', 'unknown')
                    tool_args = {}
                    if hasattr(tool_call, 'arguments'):
                        tool_args = tool_call.arguments
                    elif hasattr(tool_call, 'args'):
                        tool_args = tool_call.args
                    
                    tool_calls_used.append({
                        "tool_name": tool_name,
                        "arguments": tool_args if isinstance(tool_args, dict) else {},
                        "result": "",
                        "timestamp": datetime.now().isoformat()
                    })
                    yield f"data: {json.dumps({'tool_calls': [tool_calls_used[-1]], 'type': 'tools'})}\n\n"
            
            # Handle tool call execution results
            elif isinstance(event, ToolCallExecutionEvent):
                for result in event.content:
                    result_name = getattr(result, 'name', None)
                    result_content = ""
                    if hasattr(result, 'content'):
                        result_content = result.content
                    elif hasattr(result, 'result'):
                        result_content = str(result.result)
                    else:
                        result_content = str(result)
                    
                    # Extract approval ID if request_human_approval was called
                    if result_name == "request_human_approval" and "Approval ID:" in result_content:
                        try:
                            approval_id = result_content.split("Approval ID:")[1].split(".")[0].strip()
                        except:
                            pass
                    
                    # Find matching tool call and update result
                    if result_name:
                        for tool_call in tool_calls_used:
                            if tool_call["tool_name"] == result_name:
                                tool_call["result"] = result_content
                                break
                    yield f"data: {json.dumps({'tool_calls': tool_calls_used, 'type': 'tools'})}\n\n"
            
            # Handle streaming text chunks
            elif isinstance(event, ModelClientStreamingChunkEvent):
                chunk = event.content
                final_response += chunk
                yield f"data: {json.dumps({'content': chunk, 'type': 'text'})}\n\n"
            
            # Handle final response
            elif isinstance(event, Response):
                if hasattr(event, 'chat_message') and isinstance(event.chat_message, TextMessage):
                    final_response = event.chat_message.content
                
                yield f"data: {json.dumps({'done': True, 'response': final_response, 'tool_calls': tool_calls_used, 'approval_id': approval_id, 'type': 'complete'})}\n\n"
        
        # Update session
        session["messages"].append({"role": "assistant", "content": final_response})
        if tool_calls_used:
            session["tool_calls"].extend(tool_calls_used)
            session["tool_call_count"] += len(tool_calls_used)
            
    except Exception as e:
        logger.error(f"Error in chat stream: {e}", exc_info=True)
        yield f"data: {json.dumps({'error': str(e), 'type': 'error'})}\n\n"


# ============================================================================
# STEP 6: PDF GENERATION
# ============================================================================
def generate_meal_plan_pdf(plan: Dict[str, Any]) -> BytesIO:
    """
    Generates a PDF document for the meal plan.
    
    Args:
        plan: Meal plan dictionary
    
    Returns:
        BytesIO buffer containing PDF
    """
    if not REPORTLAB_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="PDF generation not available. Install with: pip install reportlab"
        )
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    story.append(Paragraph("30-Day Meal Prep Plan", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Date
    date_style = ParagraphStyle(
        'CustomDate',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#6b7280'),
        alignment=TA_CENTER
    )
    story.append(Paragraph(f"Created: {plan.get('created_at', datetime.now().strftime('%Y-%m-%d'))}", date_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Preferences
    story.append(Paragraph("Dietary Preferences & Goals", styles['Heading2']))
    prefs = plan.get('preferences', {})
    prefs_text = f"""
    <b>Dietary Preferences:</b> {', '.join(prefs.get('dietary_preferences', ['None']))}<br/>
    <b>Dietary Restrictions:</b> {', '.join(prefs.get('dietary_restrictions', ['None']))}<br/>
    <b>Calorie Goal:</b> {prefs.get('calorie_goal', 'Not specified')} calories/day<br/>
    <b>Protein Goal:</b> {prefs.get('protein_goal', 'Not specified')} grams/day<br/>
    <b>Cooking Skill:</b> {prefs.get('cooking_skill_level', 'Not specified')}
    """
    story.append(Paragraph(prefs_text, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Nutrition Summary
    story.append(Paragraph("Daily Nutrition Summary", styles['Heading2']))
    nutrition = plan.get('nutrition_summary', {})
    nutrition_text = f"""
    <b>Total Calories:</b> {nutrition.get('calories', 0)}<br/>
    <b>Protein:</b> {nutrition.get('protein', 0)}g ({nutrition.get('protein_percentage', 0)}%)<br/>
    <b>Carbohydrates:</b> {nutrition.get('carbs', 0)}g ({nutrition.get('carbs_percentage', 0)}%)<br/>
    <b>Fat:</b> {nutrition.get('fat', 0)}g ({nutrition.get('fat_percentage', 0)}%)
    """
    story.append(Paragraph(nutrition_text, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Meals
    story.append(Paragraph("Meal Plan", styles['Heading2']))
    meals = plan.get('meals', [])
    for i, meal in enumerate(meals, 1):
        meal_text = f"""
        <b>{meal.get('meal_type', 'Meal').title()} - {meal.get('name', 'Unknown')}</b><br/>
        Calories: {meal.get('calories', 0)} | Protein: {meal.get('protein', 0)}g | 
        Carbs: {meal.get('carbs', 0)}g | Fat: {meal.get('fat', 0)}g<br/>
        Prep Time: {meal.get('prep_time', 0)} minutes<br/>
        Ingredients: {', '.join(meal.get('ingredients', []))}
        """
        story.append(Paragraph(meal_text, styles['Normal']))
        story.append(Spacer(1, 0.15*inch))
    
    story.append(PageBreak())
    
    # Shopping List
    story.append(Paragraph("Shopping List", styles['Heading2']))
    shopping_list = plan.get('shopping_list', [])
    if shopping_list:
        table_data = [['Ingredient', 'Quantity', 'Unit']]
        for item in shopping_list:
            table_data.append([
                item.get('ingredient', ''),
                str(item.get('quantity', '')),
                item.get('unit', '')
            ])
        
        table = Table(table_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        story.append(table)
    
    doc.build(story)
    buffer.seek(0)
    return buffer


# ============================================================================
# STEP 7: API ENDPOINTS
# ============================================================================
@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Chat with the meal prep assistant with streaming response"""
    session_id = request.session_id or f"session_{datetime.now().timestamp()}"
    
    return StreamingResponse(
        generate_chat_stream(session_id, request.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/approvals")
async def list_approvals():
    """List all pending approvals"""
    pending = [
        ApprovalResponse(**approval).model_dump()
        for approval in pending_approvals.values()
        if approval["status"] == ApprovalStatus.PENDING
    ]
    return {"approvals": pending, "count": len(pending)}


@router.get("/approvals/{approval_id}")
async def get_approval(approval_id: str):
    """Get approval details"""
    if approval_id not in pending_approvals:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    return ApprovalResponse(**pending_approvals[approval_id]).model_dump()


@router.post("/approvals/{approval_id}/review")
async def review_approval(approval_id: str, request: ApprovalRequest):
    """Review and approve/reject a step"""
    if approval_id not in pending_approvals:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    approval = pending_approvals[approval_id]
    
    if approval["status"] != ApprovalStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Approval already {approval['status']}")
    
    # Update approval status
    if request.decision.lower() == "approve":
        approval["status"] = ApprovalStatus.APPROVED
    elif request.decision.lower() == "reject":
        approval["status"] = ApprovalStatus.REJECTED
    else:
        raise HTTPException(status_code=400, detail="Decision must be 'approve' or 'reject'")
    
    approval["reviewed_at"] = datetime.now().isoformat()
    approval["feedback"] = request.feedback
    
    # If this is the final plan approval, create the meal plan
    if approval["step_name"] == "final_plan" and approval["status"] == ApprovalStatus.APPROVED:
        plan_id = str(uuid.uuid4())
        meal_plans[plan_id] = {
            "plan_id": plan_id,
            "session_id": approval["session_id"],
            "preferences": approval["content"].get("preferences", {}),
            "meals": approval["content"].get("meals", []),
            "shopping_list": approval["content"].get("shopping_list", []),
            "nutrition_summary": approval["content"].get("nutrition_summary", {}),
            "created_at": datetime.now().isoformat(),
            "approved_at": datetime.now().isoformat()
        }
        # Add plan_id to content for response
        approval["content"] = approval["content"].copy()
        approval["content"]["plan_id"] = plan_id
    
    return ApprovalResponse(**approval)


@router.get("/plans/{plan_id}/pdf")
async def download_plan_pdf(plan_id: str):
    """Download meal plan as PDF"""
    if plan_id not in meal_plans:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    
    plan = meal_plans[plan_id]
    pdf_buffer = generate_meal_plan_pdf(plan)
    
    return Response(
        content=pdf_buffer.read(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=meal-plan-{plan_id[:8]}.pdf"
        }
    )


@router.get("/plans/{plan_id}")
async def get_plan(plan_id: str):
    """Get meal plan details"""
    if plan_id not in meal_plans:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    
    return MealPlan(**meal_plans[plan_id])


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "meal-prep-agent",
        "autogen_available": AUTOGEN_AVAILABLE,
        "pdf_available": REPORTLAB_AVAILABLE,
        "tools_count": len(AVAILABLE_TOOLS),
        "pending_approvals": len([a for a in pending_approvals.values() if a["status"] == ApprovalStatus.PENDING])
    }

