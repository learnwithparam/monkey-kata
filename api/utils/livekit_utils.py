"""
LiveKit Voice Agent Utilities
==============================

🎯 LEARNING OBJECTIVES:
This module provides utilities for LiveKit voice agents:

1. LLM Configuration - Get LLM instances for LiveKit voice agents
2. Provider Integration - Uses generic provider config from llm_provider

📚 USAGE:
    from utils.livekit_utils import get_livekit_llm
    
    llm = get_livekit_llm()
    agent = Agent(llm=llm, ...)
"""

import os
from typing import Optional
from utils.llm_provider import get_provider_config


def get_livekit_llm(temperature: Optional[float] = None):
    """
    Get LLM configuration for LiveKit voice agents
    
    This function:
    1. Uses get_provider_config() to detect the configured provider
    2. Returns LiveKit-compatible LLM configuration
    3. Supports Fireworks, OpenAI, and OpenRouter
    
    Args:
        temperature: Optional temperature override. If not provided, uses LLM_TEMPERATURE env var or defaults to 0.7
    
    Returns:
        LiveKit LLM instance configured for the selected provider
        
    Example:
        from utils.livekit_utils import get_livekit_llm
        
        llm = get_livekit_llm()
        agent = Agent(llm=llm, ...)
    """
    try:
        from livekit.plugins import openai as livekit_openai
    except ImportError:
        raise ImportError("LiveKit plugins not available. Install with: pip install livekit-agents[openai]")
    
    # Get temperature from parameter, env var, or default
    if temperature is None:
        temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    
    # Get provider configuration
    config = get_provider_config()
    provider_name = config["provider_name"]
    
    # Create LiveKit LLM based on provider
    if provider_name == "fireworks":
        # Use Fireworks-specific model format for LiveKit
        model = os.getenv("FIREWORKS_MODEL", "fireworks/llama-v3p1-8b-instruct")
        return livekit_openai.LLM.with_fireworks(
            model=model,
            temperature=temperature,
        )
    elif provider_name == "openrouter":
        return livekit_openai.LLM(
            model=config["model"],
            base_url=config["base_url"],
            api_key=config["api_key"],
            temperature=temperature,
        )
    elif provider_name == "openai":
        llm_kwargs = {
            "model": config["model"],
            "temperature": temperature,
        }
        if config["base_url"]:
            llm_kwargs["base_url"] = config["base_url"]
        return livekit_openai.LLM(**llm_kwargs)
    elif provider_name == "gemini":
        raise ValueError("Gemini is not supported with LiveKit. Please use Fireworks, OpenRouter, or OpenAI.")
    else:
        raise ValueError(f"Unsupported provider: {provider_name}")

