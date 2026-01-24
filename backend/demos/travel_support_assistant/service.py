from typing import Any, Dict, AsyncGenerator
import json
import logging
import re
from datetime import datetime

from fastapi import HTTPException
from utils.llm_provider import get_provider_config
from .tools import AVAILABLE_TOOLS

logger = logging.getLogger(__name__)

# AutoGen imports
try:
    from autogen_agentchat.agents import AssistantAgent
    from autogen_agentchat.messages import TextMessage, ToolCallRequestEvent, ToolCallExecutionEvent
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
    client_config = {"api_key": config["api_key"], "model": config["model"]}
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

async def generate_chat_stream(session_id: str, message: str) -> AsyncGenerator[str, None]:
    if session_id not in agent_sessions:
        agent_sessions[session_id] = {"session_id": session_id, "messages": [], "tool_calls": [], "created_at": datetime.now().isoformat(), "message_count": 0, "tool_call_count": 0}
    session = agent_sessions[session_id]
    agent = create_agent_with_tools(session_id)
    session["messages"].append({"role": "user", "content": message})
    session["message_count"] += 1
    
    async for event in agent.on_messages_stream(messages=[TextMessage(content=message, source="user")], cancellation_token=CancellationToken()):
        if isinstance(event, ToolCallRequestEvent):
            for tool_call in event.content:
                yield f"data: {json.dumps({'type': 'tools', 'tool_name': tool_call.name})}\n\n"
        elif hasattr(event, "content") and isinstance(event.content, str):
            yield f"data: {json.dumps({'content': event.content})}\n\n"
    yield f"data: {json.dumps({'done': True})}\n\n"
