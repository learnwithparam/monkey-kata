from typing import Any, Dict, AsyncGenerator
import json
import logging
import re
from datetime import datetime

from fastapi import HTTPException
from utils.llm_provider import get_provider_config
from .tools import AVAILABLE_TOOLS
from utils.thinking_streamer import ThinkingStreamer, ThinkingCategory

logger = logging.getLogger(__name__)

# AutoGen imports
try:
    from autogen_agentchat.agents import AssistantAgent
    from autogen_agentchat.teams import RoundRobinGroupChat
    from autogen_agentchat.messages import TextMessage, ToolCallRequestEvent, ToolCallExecutionEvent, ModelClientStreamingChunkEvent
    from autogen_core import CancellationToken
    from autogen_ext.models.openai import OpenAIChatCompletionClient
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

agent_sessions: Dict[str, Dict[str, Any]] = {}

def create_model_client():
    if not AUTOGEN_AVAILABLE: raise HTTPException(status_code=500, detail="AutoGen not available.")
    config = get_provider_config()
    provider_name = config["provider_name"]
    
    if provider_name == "gemini" and GEMINI_CLIENT_AVAILABLE:
        return GeminiChatCompletionClient(api_key=config["api_key"], model=config["model"])
    
    # AutoGen uses OpenRouter API directly. The model name should NOT have the "openrouter/" prefix
    # which is a LiteLLM convention. Strip it if present.
    model_name = config["model"]
    if model_name and model_name.startswith("openrouter/"):
        model_name = model_name.replace("openrouter/", "", 1)
    
    client_config = {"api_key": config["api_key"], "model": model_name}
    if config["base_url"]:
        client_config["base_url"] = config["base_url"]
        client_config["model_info"] = {"function_calling": True, "json_output": False, "vision": False, "family": "gpt-4o"}
    return OpenAIChatCompletionClient(**client_config)

def create_agent_with_tools(session_id: str) -> AssistantAgent:
    model_client = create_model_client()
    return AssistantAgent(
        name="travel_support_assistant",
        model_client=model_client,
        system_message="You are a professional travel support assistant. Write in natural prose. Use tools provided.",
        tools=AVAILABLE_TOOLS,
        model_client_stream=True,
    )

from utils.thinking_streamer import ThinkingStreamer, ThinkingCategory

async def generate_chat_stream(session_id: str, message: str) -> AsyncGenerator[str, None]:
    if session_id not in agent_sessions:
        agent_sessions[session_id] = {"session_id": session_id, "messages": [], "tool_calls": [], "created_at": datetime.now().isoformat(), "message_count": 0, "tool_call_count": 0}
    session = agent_sessions[session_id]
    
    # Create agent and wrap in a team to handle tool execution loop
    agent = create_agent_with_tools(session_id)
    team = RoundRobinGroupChat(participants=[agent], max_turns=5)
    
    session["messages"].append({"role": "user", "content": message})
    session["message_count"] += 1
    
    # Initialize thinking streamer
    streamer = ThinkingStreamer(agent_name="Assistant")
    
    # Process user message
    yield f"data: {json.dumps({'thinking': (await streamer.emit_thinking(ThinkingCategory.PLANNING, 'Analyzing request...')).to_dict()})}\n\n"
    
    # Use team.run_stream to handle the full loop (Agent -> Tool -> Agent)
    async for event in team.run_stream(task=message, cancellation_token=CancellationToken()):
        if isinstance(event, ToolCallRequestEvent):
            for tool_call in event.content:
                # Emit thinking event for tool decision
                thinking_event = await streamer.emit_tool_use(
                    tool=tool_call.name,
                    input_data=tool_call.arguments
                )
                yield f"data: {json.dumps({'thinking': thinking_event.to_dict()})}\n\n"
                
                # Emit actual tool event for frontend markers
                yield f"data: {json.dumps({'type': 'tools', 'tool_name': tool_call.name, 'arguments': tool_call.arguments})}\n\n"
                
        elif isinstance(event, ToolCallExecutionEvent):
             for result in event.content:
                # Emit observation event
                thinking_event = await streamer.emit_observation(
                    tool=result.name,
                    content=str(result.content)[:200] + "..." if len(str(result.content)) > 200 else str(result.content)
                )
                yield f"data: {json.dumps({'thinking': thinking_event.to_dict()})}\n\n"
                
                yield f"data: {json.dumps({'type': 'tool_result', 'tool_name': result.name, 'result': result.content})}\n\n"
                
        elif isinstance(event, ModelClientStreamingChunkEvent):
            # Stream tokens in real-time
            yield f"data: {json.dumps({'content': event.content})}\n\n"
            
        elif isinstance(event, TextMessage):
            # Final message content - already streamed via chunks, so we don't need to yield again
            # unless we want to send a 'final' replace event, but simple appending is safer
            # Log for debugging
            pass
    
    # Finalize
    yield f"data: {json.dumps({'thinking': (await streamer.emit_complete('Task completed')).to_dict()})}\n\n"
    yield f"data: {json.dumps({'done': True})}\n\n"
