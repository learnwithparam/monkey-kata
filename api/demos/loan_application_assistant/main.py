"""
Loan Application Assistant with Human-in-the-Loop
==================================================

🎯 LEARNING OBJECTIVES:
This demo teaches you how to build a real-world loan application assistant with human-in-the-loop:

1. Human-in-the-Loop Pattern - How to integrate human oversight and approval
2. AutoGen Integration - How to build agents that request human approval
3. Approval Workflows - How to manage pending approvals and decisions
4. Production Patterns - How to structure approval systems for financial services

📚 REAL-WORLD USE CASE:
A Loan Application Assistant that helps process loan applications:
- Analyzes loan applications using AI
- Makes risk assessments and recommendations
- Requests human approval for final decisions
- Tracks approval status and history
- Provides detailed analysis for human reviewers

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Setup - Import libraries and configure the router
Step 2: Data Models - Define request structures with validation
Step 3: Analysis Tools - Create tools for loan analysis
Step 4: Agent Setup - Configure AutoGen assistant with tools
Step 5: Approval System - Human-in-the-loop approval workflow
Step 6: API Endpoints - Expose functionality via HTTP

Key Concept: This assistant demonstrates human-in-the-loop by requiring
human approval for all loan decisions, showing how AI can assist but not
replace human judgment in critical financial decisions.
"""

# ============================================================================
# STEP 1: SETUP & IMPORTS
# ============================================================================
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, AsyncGenerator
from enum import Enum
import json
import os
from datetime import datetime, timedelta
import logging
import random
import uuid

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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/loan-application", tags=["loan-application"])

# ============================================================================
# DATABASE & STATE (In-Memory Storage)
# ============================================================================
# In-memory state for demo (use database in production)
agent_sessions: Dict[str, Dict[str, Any]] = {}
pending_approvals: Dict[str, Dict[str, Any]] = {}

# Simulated loan applications database
LOAN_APPLICATIONS_DB = {}

# ============================================================================
# STEP 2: DATA MODELS
# ============================================================================
class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
    NEEDS_MORE_INFO = "needs_more_info"


class LoanApplicationRequest(BaseModel):
    """Request to analyze a loan application"""
    applicant_name: str = Field(..., min_length=1, description="Applicant's full name")
    loan_amount: float = Field(..., gt=0, description="Requested loan amount")
    annual_income: float = Field(..., gt=0, description="Annual income")
    credit_score: Optional[int] = Field(None, ge=300, le=850, description="Credit score (300-850). If not provided, will be fetched via credit bureau API")
    employment_status: str = Field(..., description="Employment status")
    loan_purpose: str = Field(..., description="Purpose of the loan")
    existing_debt: Optional[float] = Field(0, ge=0, description="Existing debt amount")
    session_id: Optional[str] = Field(None, description="Optional session ID")


class ChatRequest(BaseModel):
    """Request to chat with the loan assistant"""
    message: str = Field(..., min_length=1, description="The user's message or question")
    session_id: Optional[str] = Field(None, description="Optional session ID for conversation continuity")
    application_id: Optional[str] = Field(None, description="Optional application ID for contextual chat")


class ApprovalRequest(BaseModel):
    """Request to approve or reject a loan application"""
    approval_id: str = Field(..., description="Approval ID")
    decision: str = Field(..., description="Decision: 'approve' or 'reject'")
    reviewer_notes: Optional[str] = Field(None, description="Optional reviewer notes")


class ApprovalResponse(BaseModel):
    """Approval information"""
    approval_id: str
    application_id: str
    applicant_name: str
    loan_amount: float
    recommendation: str
    risk_score: float
    status: ApprovalStatus
    ai_analysis: str
    created_at: str
    reviewed_at: Optional[str] = None
    reviewer_notes: Optional[str] = None


class ToolCall(BaseModel):
    """Information about a tool call"""
    tool_name: str
    arguments: Dict[str, Any]
    result: str
    timestamp: str


class ChatResponse(BaseModel):
    """Loan assistant response with tool usage information"""
    response: str
    session_id: str
    tool_calls: List[ToolCall] = []
    approval_id: Optional[str] = None


# ============================================================================
# STEP 3: ANALYSIS TOOLS
# ============================================================================
def fetch_credit_score(applicant_name: str, ssn: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetches credit score from credit bureau API (mocked).
    
    In a real system, this would call an external credit bureau API (e.g., Experian, Equifax, TransUnion).
    This is a mock implementation that simulates the API call with a realistic delay.
    
    Args:
        applicant_name: Applicant's full name (required for credit lookup)
        ssn: Optional SSN for credit lookup (not required for mock, but would be used in production)
    
    Returns:
        Dictionary with credit score, credit rating, source, and report date
    """
    import random
    
    # Mock credit score lookup - simulates API delay
    import time
    time.sleep(0.5)  # Simulate API call delay
    
    # Generate a realistic credit score based on name hash (for consistency)
    name_hash = hash(applicant_name.lower()) % 550
    base_score = 300 + name_hash  # Score between 300-850
    
    # Add some randomness but keep it consistent for same name
    score_variation = random.randint(-20, 20)
    credit_score = max(300, min(850, base_score + score_variation))
    
    # Determine credit rating
    if credit_score >= 740:
        rating = "Excellent"
    elif credit_score >= 670:
        rating = "Good"
    elif credit_score >= 580:
        rating = "Fair"
    else:
        rating = "Poor"
    
    return {
        "credit_score": credit_score,
        "credit_rating": rating,
        "source": "Mock Credit Bureau API",
        "report_date": datetime.now().isoformat(),
        "message": f"Credit score retrieved for {applicant_name}: {credit_score} ({rating})"
    }


def calculate_debt_to_income_ratio(annual_income: float, existing_debt: float, loan_amount: float, loan_term_years: int = 5) -> float:
    """
    Calculates debt-to-income ratio for loan assessment.
    
    Args:
        annual_income: Annual income
        existing_debt: Existing monthly debt payments
        loan_amount: Requested loan amount
        loan_term_years: Loan term in years (default: 5)
    
    Returns:
        Debt-to-income ratio as a percentage
    """
    monthly_income = annual_income / 12
    # Estimate monthly loan payment (simplified calculation)
    monthly_loan_payment = (loan_amount * 0.05) / 12  # Simplified: 5% annual rate
    total_monthly_debt = existing_debt + monthly_loan_payment
    dti_ratio = (total_monthly_debt / monthly_income) * 100
    return round(dti_ratio, 2)


def assess_credit_risk(credit_score: int, debt_to_income: float, loan_amount: float, annual_income: float) -> Dict[str, Any]:
    """
    Assesses credit risk based on multiple factors.
    
    Args:
        credit_score: Credit score (300-850)
        debt_to_income: Debt-to-income ratio
        loan_amount: Requested loan amount
        annual_income: Annual income
    
    Returns:
        Risk assessment with score and factors
    """
    risk_factors = []
    risk_score = 0.0
    
    # Credit score risk
    if credit_score < 580:
        risk_score += 0.4
        risk_factors.append("Very poor credit score")
    elif credit_score < 670:
        risk_score += 0.25
        risk_factors.append("Fair credit score")
    elif credit_score < 740:
        risk_score += 0.1
        risk_factors.append("Good credit score")
    else:
        risk_factors.append("Excellent credit score")
    
    # Debt-to-income risk
    if debt_to_income > 43:
        risk_score += 0.3
        risk_factors.append("High debt-to-income ratio")
    elif debt_to_income > 36:
        risk_score += 0.15
        risk_factors.append("Moderate debt-to-income ratio")
    else:
        risk_factors.append("Low debt-to-income ratio")
    
    # Loan-to-income risk
    loan_to_income = (loan_amount / annual_income) * 100
    if loan_to_income > 50:
        risk_score += 0.2
        risk_factors.append("High loan-to-income ratio")
    elif loan_to_income > 30:
        risk_score += 0.1
        risk_factors.append("Moderate loan-to-income ratio")
    else:
        risk_factors.append("Reasonable loan-to-income ratio")
    
    # Normalize risk score to 0-1
    risk_score = min(1.0, risk_score)
    
    # Determine risk level
    if risk_score < 0.3:
        risk_level = "Low"
    elif risk_score < 0.6:
        risk_level = "Medium"
    else:
        risk_level = "High"
    
    return {
        "risk_score": round(risk_score, 2),
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "loan_to_income_ratio": round(loan_to_income, 2)
    }


def analyze_loan_application(
    applicant_name: str,
    loan_amount: float,
    annual_income: float,
    credit_score: int,
    employment_status: str,
    loan_purpose: str,
    existing_debt: float = 0
) -> str:
    """
    Analyzes a loan application and provides detailed assessment.
    
    This tool performs comprehensive analysis including:
    - Debt-to-income ratio calculation
    - Credit risk assessment
    - Employment status evaluation
    - Loan purpose analysis
    
    Args:
        applicant_name: Applicant's full name
        loan_amount: Requested loan amount
        annual_income: Annual income
        credit_score: Credit score (300-850)
        employment_status: Employment status
        loan_purpose: Purpose of the loan
        existing_debt: Existing debt amount
    
    Returns:
        Detailed loan analysis report
    """
    # Calculate metrics
    dti_ratio = calculate_debt_to_income_ratio(annual_income, existing_debt, loan_amount)
    risk_assessment = assess_credit_risk(credit_score, dti_ratio, loan_amount, annual_income)
    
    # Generate analysis report
    analysis = f"""Loan Application Analysis for {applicant_name}

APPLICATION DETAILS:
- Loan Amount: ${loan_amount:,.2f}
- Annual Income: ${annual_income:,.2f}
- Credit Score: {credit_score}
- Employment Status: {employment_status}
- Loan Purpose: {loan_purpose}
- Existing Debt: ${existing_debt:,.2f}

FINANCIAL METRICS:
- Debt-to-Income Ratio: {dti_ratio}%
- Loan-to-Income Ratio: {risk_assessment['loan_to_income_ratio']}%
- Risk Score: {risk_assessment['risk_score']} ({risk_assessment['risk_level']} Risk)

RISK FACTORS:
{chr(10).join(f"- {factor}" for factor in risk_assessment['risk_factors'])}

RECOMMENDATION:
Based on the analysis, this application requires human review and approval.
The AI has provided a risk assessment, but final approval must be made by a human reviewer."""
    
    return analysis


def request_human_approval(application_id: str, analysis: str, recommendation: str, risk_score: float) -> str:
    """
    Requests human approval for a loan application.
    
    This tool creates a pending approval that requires human review.
    All loan decisions require human approval as part of the human-in-the-loop pattern.
    
    Args:
        application_id: Unique application ID
        analysis: AI-generated analysis
        recommendation: AI recommendation
        risk_score: Calculated risk score (0-1)
    
    Returns:
        Approval ID for tracking
    """
    approval_id = str(uuid.uuid4())
    
    # Determine recommendation based on risk score
    if risk_score < 0.3:
        recommendation_text = "APPROVE - Low risk application"
    elif risk_score < 0.6:
        recommendation_text = "REVIEW CAREFULLY - Medium risk application"
    else:
        recommendation_text = "REJECT - High risk application"
    
    pending_approvals[approval_id] = {
        "approval_id": approval_id,
        "application_id": application_id,
        "analysis": analysis,
        "recommendation": recommendation_text,
        "risk_score": risk_score,
        "status": ApprovalStatus.PENDING,
        "created_at": datetime.now().isoformat(),
        "reviewed_at": None,
        "reviewer_notes": None
    }
    
    return f"Human approval requested. Approval ID: {approval_id}. Status: Pending review."


# List of available tools
AVAILABLE_TOOLS = [
    fetch_credit_score,
    calculate_debt_to_income_ratio,
    assess_credit_risk,
    analyze_loan_application,
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
    """Creates an AutoGen agent with loan analysis tools"""
    if not AUTOGEN_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="AutoGen not available. Install with: pip install 'autogen-agentchat[openai]'"
        )
    
    try:
        model_client = create_model_client()
        
        agent = AssistantAgent(
            name="loan_application_assistant",
            model_client=model_client,
            system_message="""You are a professional loan application analysis agent for a financial institution.
Your role is to perform comprehensive multi-step analysis of loan applications:

1. **Step 1: Fetch Credit Score** - If credit score is not provided, use fetch_credit_score() to retrieve it from credit bureau API
2. **Step 2: Calculate Financial Metrics** - Use calculate_debt_to_income_ratio() to assess debt burden
3. **Step 3: Assess Credit Risk** - Use assess_credit_risk() to evaluate creditworthiness (requires credit score from Step 1)
4. **Step 4: Comprehensive Analysis** - Use analyze_loan_application() to generate detailed assessment
5. **Step 5: Create Review Request** - Use request_human_approval() to submit for final human review

Workflow:
- Always start by checking if credit score is provided. If not, fetch it using fetch_credit_score()
- Perform analysis in a structured, step-by-step manner
- Show each step of your analysis process clearly
- After completing all analysis steps, create a review request
- Present your findings in a clear, professional format

Guidelines:
- Be professional, clear, and thorough in your analysis
- Use ALL available tools to perform comprehensive analysis
- Always fetch credit score if not provided in the application
- Show your work - explain each step you're taking
- Format your responses using proper markdown with line breaks and numbered/bulleted lists
- Always use double line breaks between paragraphs for readability
- Present findings in a structured format suitable for human review""",
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
                "tool_call_count": 0
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
# STEP 6: API ENDPOINTS
# ============================================================================
@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Chat with the loan application assistant with streaming response"""
    session_id = request.session_id or f"session_{datetime.now().timestamp()}"
    
    return StreamingResponse(
        generate_chat_stream(session_id, request.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


async def generate_analysis_stream(
    request: LoanApplicationRequest
) -> AsyncGenerator[str, None]:
    """Generate streaming analysis using agent with multi-step workflow"""
    try:
        # Create application ID
        application_id = f"APP{random.randint(100000, 999999)}"
        
        # Store application
        LOAN_APPLICATIONS_DB[application_id] = {
            "application_id": application_id,
            "applicant_name": request.applicant_name,
            "loan_amount": request.loan_amount,
            "annual_income": request.annual_income,
            "credit_score": request.credit_score,
            "employment_status": request.employment_status,
            "loan_purpose": request.loan_purpose,
            "existing_debt": request.existing_debt or 0,
            "created_at": datetime.now().isoformat()
        }
        
        # Create session for this analysis
        session_id = f"analysis_{application_id}"
        agent_sessions[session_id] = {
            "session_id": session_id,
            "messages": [],
            "tool_calls": [],
            "created_at": datetime.now().isoformat(),
            "message_count": 0,
            "tool_call_count": 0
        }
        
        # Create agent with tools
        agent = create_agent_with_tools(session_id)
        
        # Construct analysis prompt
        credit_score_info = f"Credit Score: {request.credit_score}" if request.credit_score else "Credit Score: Not provided (will be fetched from credit bureau)"
        
        analysis_prompt = f"""Analyze the following loan application:

Applicant Name: {request.applicant_name}
Loan Amount: ${request.loan_amount:,.2f}
Annual Income: ${request.annual_income:,.2f}
{credit_score_info}
Employment Status: {request.employment_status}
Loan Purpose: {request.loan_purpose}
Existing Debt: ${request.existing_debt or 0:,.2f}

Please perform a comprehensive multi-step analysis:
1. If credit score is not provided, fetch it using fetch_credit_score()
2. Calculate the debt-to-income ratio
3. Assess the credit risk (using the credit score from step 1)
4. Provide a detailed analysis
5. Create a review request for human final decision

Show each step of your analysis process clearly."""
        
        # Track tool calls and response
        tool_calls_used = []
        final_response = ""
        approval_id = None
        
        # Process through agent with streaming
        async for event in agent.on_messages_stream(
            messages=[TextMessage(content=analysis_prompt, source="user")],
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
                
                # Get approval details if created
                approval_data = {}
                if approval_id and approval_id in pending_approvals:
                    approval = pending_approvals[approval_id]
                    approval_data = {
                        "approval_id": approval_id,
                        "application_id": application_id,
                        "recommendation": approval.get("recommendation", ""),
                        "risk_score": approval.get("risk_score", 0),
                    }
                
                yield f"data: {json.dumps({'done': True, 'response': final_response, 'tool_calls': tool_calls_used, 'approval': approval_data, 'application_id': application_id, 'type': 'complete'})}\n\n"
        
    except Exception as e:
        logger.error(f"Error in analysis stream: {e}", exc_info=True)
        yield f"data: {json.dumps({'error': str(e), 'type': 'error'})}\n\n"


@router.post("/analyze/stream")
async def analyze_application_stream(request: LoanApplicationRequest):
    """Analyze a loan application using agentic workflow with streaming response"""
    return StreamingResponse(
        generate_analysis_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/approvals")
async def list_approvals():
    """List all pending approvals (including those needing more info)"""
    pending = [
        ApprovalResponse(**approval)
        for approval in pending_approvals.values()
        if approval["status"] in [ApprovalStatus.PENDING, ApprovalStatus.NEEDS_MORE_INFO]
    ]
    return {"approvals": pending, "count": len(pending)}


@router.get("/approvals/{approval_id}")
async def get_approval(approval_id: str):
    """Get approval details"""
    if approval_id not in pending_approvals:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    return ApprovalResponse(**pending_approvals[approval_id])


@router.post("/approvals/{approval_id}/review")
async def review_approval(approval_id: str, request: ApprovalRequest):
    """Review and approve/reject a loan application"""
    if approval_id not in pending_approvals:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    approval = pending_approvals[approval_id]
    
    if approval["status"] not in [ApprovalStatus.PENDING, ApprovalStatus.NEEDS_MORE_INFO]:
        raise HTTPException(status_code=400, detail=f"Approval already {approval['status']}")
    
    # Update approval status
    if request.decision.lower() == "approve":
        approval["status"] = ApprovalStatus.APPROVED
    elif request.decision.lower() == "reject":
        approval["status"] = ApprovalStatus.REJECTED
    else:
        raise HTTPException(status_code=400, detail="Decision must be 'approve' or 'reject'")
    
    approval["reviewed_at"] = datetime.now().isoformat()
    approval["reviewer_notes"] = request.reviewer_notes
    
    # Update application status
    application_id = approval["application_id"]
    if application_id in LOAN_APPLICATIONS_DB:
        LOAN_APPLICATIONS_DB[application_id]["status"] = approval["status"]
        LOAN_APPLICATIONS_DB[application_id]["reviewed_at"] = approval["reviewed_at"]
    
    return ApprovalResponse(**approval)


@router.post("/approvals/{approval_id}/request-info")
async def request_more_info(approval_id: str, request_info: Optional[str] = Body(None)):
    """Request more information for a loan application (sets status to needs_more_info)"""
    if approval_id not in pending_approvals:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    approval = pending_approvals[approval_id]
    
    if approval["status"] not in [ApprovalStatus.PENDING, ApprovalStatus.NEEDS_MORE_INFO]:
        raise HTTPException(status_code=400, detail=f"Cannot request info for approval with status {approval['status']}")
    
    approval["status"] = ApprovalStatus.NEEDS_MORE_INFO
    if request_info:
        approval["info_requested"] = request_info
        approval["info_requested_at"] = datetime.now().isoformat()
    
    return ApprovalResponse(**approval)


@router.get("/tools")
async def list_tools():
    """List all available tools"""
    tools_info = []
    for tool_func in AVAILABLE_TOOLS:
        tools_info.append({
            "name": tool_func.__name__,
            "description": tool_func.__doc__ or f"Tool: {tool_func.__name__}",
        })
    
    return {
        "tools": tools_info,
        "autogen_available": AUTOGEN_AVAILABLE
    }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "loan-application-assistant",
        "autogen_available": AUTOGEN_AVAILABLE,
        "tools_count": len(AVAILABLE_TOOLS),
        "pending_approvals": len([a for a in pending_approvals.values() if a["status"] == ApprovalStatus.PENDING])
    }

