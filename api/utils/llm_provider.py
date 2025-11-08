"""
LLM Provider
============

🎯 LEARNING OBJECTIVES:
This module teaches you how to build a flexible AI provider system:

1. Abstraction Patterns - How to design interchangeable components
2. Provider Pattern - How to support multiple AI services
3. API Compatibility - How OpenAI-compatible APIs work
4. Streaming - How to implement real-time text generation
5. Factory Pattern - How to select providers based on configuration

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Abstract Base Class - Define the contract all providers must follow
Step 2: Cloud Providers - Learn how to integrate commercial AI APIs
Step 3: Factory Pattern - Automatically select the right provider

Key Concept: This uses the "Provider Pattern" - all providers implement
the same interface, so you can swap them without changing your code!
"""

import os
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional
import json
import asyncio

# ============================================================================
# STEP 1: ABSTRACT BASE CLASS
# ============================================================================
"""
What is an Abstract Base Class?
- Defines the "contract" that all providers must follow
- Ensures all providers have the same methods (generate_text, generate_stream)
- Makes code interchangeable - you can swap providers easily

Benefits:
- Type safety: Code expects specific methods
- Consistency: All providers work the same way
- Flexibility: Add new providers without breaking existing code
"""
class LLMProvider(ABC):
    """
    Abstract base class for all LLM providers
    
    This defines the interface that every provider (Gemini, OpenAI, OpenRouter, etc.)
    must implement. This is what makes the "Provider Pattern" work!
    """
    
    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate complete text from a prompt (non-streaming)
        
        Returns the full response as a single string.
        Use this when you don't need real-time streaming.
        """
        pass
    
    @abstractmethod
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        Generate streaming text from a prompt (real-time)
        
        Returns text chunk by chunk as an async generator.
        Use this for ChatGPT-like experiences.
        """
        pass


# ============================================================================
# STEP 2: CLOUD PROVIDERS (Commercial AI APIs)
# ============================================================================
"""
Commercial Cloud Providers:
These connect to paid/free APIs from major AI companies.
Each provider has different API formats, but they all implement
the same interface we defined in LLMProvider.

Key Concepts:
- API Keys: Authentication tokens for accessing services
- Rate Limits: Commercial APIs often have usage limits
- Cost: Pay per token/request (except some free tiers)
- OpenAI-Compatible: Some APIs follow OpenAI's format for easy migration
"""

# Google Gemini Provider
try:
    import google.generativeai as genai
    import asyncio
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

if GEMINI_AVAILABLE:
    class GeminiProvider(LLMProvider):
        """
        Google Gemini Provider
        
        Pros: Free tier available, good quality
        Cons: Requires internet connection, rate limits
        
        How it works:
        1. Configure with API key
        2. Create GenerativeModel instance
        3. Call generate_content() with prompt
        4. Stream chunks as they arrive
        """
        
        def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
            self.api_key = api_key
            self.model_name = model
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model)
        
        async def generate_text(self, prompt: str, **kwargs) -> str:
            """Generate text using Gemini"""
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=kwargs.get('temperature', 0.8),
                    max_output_tokens=kwargs.get('max_tokens', 1000),
                )
            )
            
            # Check if response has valid content
            if not response.candidates or len(response.candidates) == 0:
                raise ValueError("No candidates returned from Gemini API")
            
            candidate = response.candidates[0]
            
            # Check finish reason - 2 means content was blocked/filtered
            if hasattr(candidate, 'finish_reason') and candidate.finish_reason == 2:
                raise ValueError("Content was blocked by Gemini safety filters. Try rephrasing your prompt.")
            
            # Try to get text from response
            try:
                return response.text
            except ValueError as e:
                # If response.text fails, try to extract from parts manually
                if candidate.content and candidate.content.parts:
                    text_parts = []
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text:
                            text_parts.append(part.text)
                    if text_parts:
                        return ''.join(text_parts)
                
                # If we still can't get text, raise the original error
                raise ValueError(f"Failed to extract text from Gemini response: {str(e)}")
        
        async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
            """Stream text using Gemini"""
            # Use asyncio.Queue to bridge sync generator to async generator
            chunk_queue = asyncio.Queue(maxsize=100)
            exception_holder = [None]
            loop = asyncio.get_event_loop()
            
            def _generate_chunks():
                """Run the synchronous generator in a thread"""
                try:
                    response = self.model.generate_content(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=kwargs.get('temperature', 0.8),
                            max_output_tokens=kwargs.get('max_tokens', 1000),
                        ),
                        stream=True
                    )
                    # Iterate over chunks directly - for loop handles StopIteration automatically
                    chunk_count = 0
                    try:
                        for chunk in response:
                            # Try multiple ways to extract text from chunk
                            text = None
                            if hasattr(chunk, 'text') and chunk.text:
                                text = chunk.text
                            elif hasattr(chunk, 'candidates') and chunk.candidates:
                                candidate = chunk.candidates[0]
                                if hasattr(candidate, 'content') and candidate.content:
                                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                                        part = candidate.content.parts[0]
                                        if hasattr(part, 'text') and part.text:
                                            text = part.text
                            
                            if text:
                                chunk_count += 1
                                # Put chunk in queue from sync context
                                asyncio.run_coroutine_threadsafe(
                                    chunk_queue.put(text),
                                    loop
                                )
                    except StopIteration:
                        # Normal end of iteration - this is expected
                        pass
                    except Exception as e:
                        # Other errors during iteration
                        exception_holder[0] = e
                    finally:
                        # Always signal completion
                        asyncio.run_coroutine_threadsafe(
                            chunk_queue.put(None),
                            loop
                        )
                except StopIteration:
                    # StopIteration from generate_content itself - normal completion
                    # Signal completion without storing as error
                    asyncio.run_coroutine_threadsafe(
                        chunk_queue.put(None),
                        loop
                    )
                except Exception as e:
                    # Real errors - store and signal
                    exception_holder[0] = e
                    # Signal completion even on error
                    asyncio.run_coroutine_threadsafe(
                        chunk_queue.put(None),
                        loop
                    )
            
            # Start generation in a thread
            executor_task = loop.run_in_executor(None, _generate_chunks)
            
            # Yield chunks as they arrive - return normally when done (no StopIteration)
            try:
                while True:
                    try:
                        chunk = await chunk_queue.get()
                        if chunk is None:
                            # Generator finished - check for exceptions (but not StopIteration)
                            if exception_holder[0]:
                                # Don't raise StopIteration - convert to RuntimeError or handle differently
                                if isinstance(exception_holder[0], StopIteration):
                                    # StopIteration is normal completion, not an error
                                    break
                                raise exception_holder[0]
                            # Normal completion - break out of loop
                            break
                        yield chunk
                    except RuntimeError as e:
                        # Catch RuntimeError that might be caused by StopIteration
                        if "StopIteration" in str(e):
                            # This is a StopIteration converted to RuntimeError - treat as normal completion
                            break
                        raise
            finally:
                # Clean up - wait for executor
                try:
                    await asyncio.wait_for(executor_task, timeout=5.0)
                except (asyncio.TimeoutError, Exception):
                    pass


# OpenAI Provider
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None

if OPENAI_AVAILABLE:
    class OpenAIProvider(LLMProvider):
        """
        OpenAI Provider (GPT-3.5, GPT-4, etc.)
        
        Pros: Industry standard, very high quality
        Cons: Paid service, requires API key
        
        How it works:
        1. Create AsyncOpenAI client with API key
        2. Call chat.completions.create() with messages
        3. For streaming, set stream=True and iterate chunks
        """
        
        def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
            self.client = AsyncOpenAI(api_key=api_key)
            self.model = model
        
        async def generate_text(self, prompt: str, **kwargs) -> str:
            """Generate text using OpenAI"""
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get('temperature', 0.8),
                max_tokens=kwargs.get('max_tokens', 1000),
            )
            return response.choices[0].message.content
        
        async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
            """Stream text using OpenAI"""
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get('temperature', 0.8),
                max_tokens=kwargs.get('max_tokens', 1000),
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content


# OpenRouter Provider (OpenAI-Compatible API)
try:
    from openai import AsyncOpenAI
    OPENROUTER_AVAILABLE = True
except ImportError:
    OPENROUTER_AVAILABLE = False
    AsyncOpenAI = None

if OPENROUTER_AVAILABLE:
    class OpenRouterProvider(LLMProvider):
        """
        OpenRouter Provider
        
        Pros: Access to many models (Claude, GPT-4, Llama, etc.), unified API
        Cons: Requires internet connection, paid service
        
        How it works:
        - Uses OpenAI-compatible API format
        - Same code structure as OpenAI provider
        - Just change the base URL and API key
        - This demonstrates API compatibility patterns!
        
        Key Learning: OpenAI-compatible APIs let you use the same code
        to access different AI providers. This is called "API compatibility".
        """
        
        def __init__(self, api_key: str, model: str = "minimax/minimax-m2:free"):
            self.api_key = api_key
            self.model = model
            # OpenRouter uses OpenAI-compatible format with different base URL
            # Prepare custom headers for OpenRouter
            default_headers = {
                "HTTP-Referer": os.getenv("OPENROUTER_HTTP_REFERER", ""),
                "X-Title": os.getenv("OPENROUTER_APP_NAME", "AI Bootcamp for Software Engineers")
            }
            # Filter out empty values
            headers = {k: v for k, v in default_headers.items() if v}
            
            self.client = AsyncOpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
                default_headers=headers
            )
        
        async def generate_text(self, prompt: str, **kwargs) -> str:
            """Generate text using OpenRouter"""
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get('temperature', 0.8),
                max_tokens=kwargs.get('max_tokens', 1000),
            )
            return response.choices[0].message.content
        
        async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
            """Stream text using OpenRouter"""
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get('temperature', 0.8),
                max_tokens=kwargs.get('max_tokens', 1000),
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content


# FireworksAI Provider
try:
    import aiohttp
    FIREWORKS_AVAILABLE = True
except ImportError:
    FIREWORKS_AVAILABLE = False
    aiohttp = None

if FIREWORKS_AVAILABLE:
    class FireworksAIProvider(LLMProvider):
        """
        FireworksAI Provider
        
        Pros: Fast inference, good pricing
        Cons: Requires internet connection
        
        How it works:
        1. Send HTTP POST request to FireworksAI API
        2. Use OpenAI-compatible format
        3. Parse streaming response chunks
        """
        
        def __init__(self, api_key: str, model: str = "accounts/fireworks/models/qwen3-235b-a22b-instruct-2507"):
            self.api_key = api_key
            self.model = model
            self.base_url = "https://api.fireworks.ai/inference/v1/chat/completions"
        
        async def generate_text(self, prompt: str, **kwargs) -> str:
            """Generate text using FireworksAI"""
            payload = {
                "model": self.model,
                "max_tokens": kwargs.get('max_tokens', 1000),
                "temperature": kwargs.get('temperature', 0.7),
                "messages": [{"role": "user", "content": prompt}]
            }
            
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, data=json.dumps(payload)) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['choices'][0]['message']['content']
                    else:
                        error_text = await response.text()
                        raise Exception(f"FireworksAI API error {response.status}: {error_text}")
        
        async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
            """Stream text using FireworksAI"""
            payload = {
                "model": self.model,
                "max_tokens": kwargs.get('max_tokens', 1000),
                "temperature": kwargs.get('temperature', 0.7),
                "stream": True,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, data=json.dumps(payload)) as response:
                    if response.status == 200:
                        async for line in response.content:
                            line = line.decode('utf-8').strip()
                            if line.startswith('data: '):
                                data = line[6:]
                                if data == '[DONE]':
                                    break
                                try:
                                    chunk = json.loads(data)
                                    if 'choices' in chunk and len(chunk['choices']) > 0:
                                        delta = chunk['choices'][0].get('delta', {})
                                        if 'content' in delta:
                                            yield delta['content']
                                except json.JSONDecodeError:
                                    continue
                    else:
                        error_text = await response.text()
                        raise Exception(f"FireworksAI API error {response.status}: {error_text}")


# ============================================================================
# STEP 3: GENERIC PROVIDER CONFIGURATION
# ============================================================================
"""
Generic Provider Configuration:
- Returns raw provider configuration (api_key, model, base_url, provider_name)
- Can be used by any consumer (AutoGen, LiveKit, direct API calls, etc.)
- Centralizes all provider detection logic in one place

This is the core function that all other functions use internally.
"""
def get_provider_config():
    """
    Get generic provider configuration
    
    Returns:
        dict with:
        - api_key: API key for the provider
        - model: Model name
        - base_url: Base URL for API (None for standard OpenAI)
        - provider_name: Name of the provider ('fireworks', 'openrouter', 'gemini', 'openai')
        
    Example:
        from utils.llm_provider import get_provider_config
        
        config = get_provider_config()
        # Use config['api_key'], config['model'], config['base_url'] for any API client
    """
    provider_type = os.getenv("LLM_PROVIDER", "").lower()
    
    # Priority 1: FireworksAI
    fireworks_key = os.getenv("FIREWORKS_API_KEY")
    if fireworks_key and FIREWORKS_AVAILABLE and (provider_type == "fireworks" or not provider_type):
        model = os.getenv("FIREWORKS_MODEL", "accounts/fireworks/models/qwen3-235b-a22b-instruct-2507")
        return {
            "api_key": fireworks_key,
            "model": model,
            "base_url": "https://api.fireworks.ai/inference/v1",
            "provider_name": "fireworks"
        }
    
    # Priority 2: OpenRouter
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key and OPENROUTER_AVAILABLE and (provider_type == "openrouter" or not provider_type):
        model = os.getenv("OPENROUTER_MODEL", "minimax/minimax-m2:free")
        return {
            "api_key": openrouter_key,
            "model": model,
            "base_url": "https://openrouter.ai/api/v1",
            "provider_name": "openrouter"
        }
    
    # Priority 3: Gemini
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key and GEMINI_AVAILABLE and (provider_type == "gemini" or not provider_type):
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        return {
            "api_key": gemini_key,
            "model": model,
            "base_url": None,  # Gemini doesn't use OpenAI-compatible API
            "provider_name": "gemini"
        }
    
    # Priority 4: OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and OPENAI_AVAILABLE and (provider_type == "openai" or not provider_type):
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        return {
            "api_key": openai_key,
            "model": model,
            "base_url": os.getenv("OPENAI_BASE_URL"),  # None for standard OpenAI
            "provider_name": "openai"
        }
    
    # No provider available
    raise ValueError(
        "No LLM provider configured. Please set one of:\n"
        "- FIREWORKS_API_KEY\n"
        "- OPENROUTER_API_KEY\n"
        "- GEMINI_API_KEY\n"
        "- OPENAI_API_KEY"
    )


# ============================================================================
# STEP 4: FACTORY PATTERN (Automatic Provider Selection)
# ============================================================================
"""
Factory Pattern:
- Automatically selects the right provider based on environment
- Checks for API keys in priority order
- Makes configuration simple and automatic

Priority Order:
1. FireworksAI (if FIREWORKS_API_KEY set)
2. OpenRouter (if OPENROUTER_API_KEY set)
3. Gemini (if GEMINI_API_KEY set)
4. OpenAI (if OPENAI_API_KEY set)

Configuration:
Set environment variables to choose your provider:
- FIREWORKS_API_KEY=your_key
- OPENROUTER_API_KEY=your_key
- GEMINI_API_KEY=your_key
- OPENAI_API_KEY=your_key

OpenRouter also supports:
- OPENROUTER_MODEL=model-name (default: minimax/minimax-m2:free - free model)
- OPENROUTER_HTTP_REFERER=your-url (optional)
- OPENROUTER_APP_NAME=your-app-name (optional)
"""
def get_llm_provider() -> LLMProvider:
    """
    Factory function: Automatically selects and creates the right provider
    
    This is the main function you'll use in your code.
    It automatically picks the best available provider based on:
    1. Environment variables (API keys)
    2. Provider preference (LLM_PROVIDER env var)
    3. Availability of libraries
    
    Returns:
        An instance of LLMProvider (FireworksAI, OpenRouter, Gemini, or OpenAI)
    """
    # Use generic provider config
    config = get_provider_config()
    provider_name = config["provider_name"]
    
    # Create provider instance based on config
    if provider_name == "fireworks" and FIREWORKS_AVAILABLE:
        print(f"🤖 Using FireworksAI provider with model: {config['model']}")
        return FireworksAIProvider(api_key=config["api_key"], model=config["model"])
    elif provider_name == "openrouter" and OPENROUTER_AVAILABLE:
        print(f"🤖 Using OpenRouter provider with model: {config['model']}")
        return OpenRouterProvider(api_key=config["api_key"], model=config["model"])
    elif provider_name == "gemini" and GEMINI_AVAILABLE:
        print(f"🤖 Using Google Gemini provider with model: {config['model']}")
        return GeminiProvider(api_key=config["api_key"], model=config["model"])
    elif provider_name == "openai" and OPENAI_AVAILABLE:
        print(f"🤖 Using OpenAI provider with model: {config['model']}")
        return OpenAIProvider(api_key=config["api_key"], model=config["model"])
    else:
        raise ValueError(f"Provider {provider_name} is not available. Install required dependencies.")




# ============================================================================
# LEARNING CHECKLIST
# ============================================================================
"""
After reading this code, you should understand:

✓ How abstraction works (ABC base class)
✓ How to integrate cloud AI APIs (Gemini, OpenAI, FireworksAI)
✓ How OpenAI-compatible APIs work (OpenRouter example)
✓ How the Factory Pattern simplifies provider selection
✓ How streaming works across different providers
✓ The benefits of API compatibility

Next Steps:
1. Try different providers and compare results
2. Experiment with different models on OpenRouter
3. Add a new provider (e.g., Anthropic Claude directly)
4. Understand how OpenAI-compatible APIs reduce code duplication
5. Learn about API standardization benefits

Questions to Consider:
- Why is OpenAI-compatible API format useful?
- What are the advantages of using OpenRouter vs direct APIs?
- How does the Factory Pattern make code more maintainable?
- How would you add caching to reduce API costs?
- What security considerations exist for API keys?
"""