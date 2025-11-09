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
    def _is_gemini_content_blocked(candidate) -> bool:
        """
        Check if Gemini response was blocked by safety filters.
        
        Args:
            candidate: Gemini response candidate object
            
        Returns:
            True if content was blocked, False otherwise
        """
        # Finish reason 2 (SAFETY) means content was blocked
        if hasattr(candidate, 'finish_reason') and candidate.finish_reason == 2:
            return True
        return False
    
    def _extract_text_from_gemini_chunk(chunk) -> Optional[str]:
        """
        Extract text from a Gemini streaming chunk.
        
        For streaming responses, Gemini returns incremental text chunks.
        Each chunk contains the NEW text since the last chunk (not cumulative).
        
        Args:
            chunk: Gemini streaming chunk object
            
        Returns:
            Extracted text (can be empty string) or None if no text found
        """
        # Strategy 1: Try direct text attribute (works for some API versions)
        try:
            if hasattr(chunk, 'text'):
                text = chunk.text
                # Return even if empty string (empty is valid for streaming)
                if text is not None:
                    return text
        except (AttributeError, ValueError):
            pass
        
        # Strategy 2: Extract from candidates -> content -> parts (most common for streaming)
        try:
            if hasattr(chunk, 'candidates') and chunk.candidates:
                if len(chunk.candidates) > 0:
                    candidate = chunk.candidates[0]
                    
                    # Check for content with parts
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            # Iterate through all parts to find text
                            for part in candidate.content.parts:
                                # Check if part has text attribute
                                if hasattr(part, 'text'):
                                    text = part.text
                                    # Return even if empty string
                                    if text is not None:
                                        return text
                    
                    # Try direct candidate.text if available
                    if hasattr(candidate, 'text'):
                        text = candidate.text
                        if text is not None:
                            return text
        except (AttributeError, IndexError, ValueError, TypeError):
            # Log but don't fail - try next strategy
            pass
        
        # Strategy 3: Try accessing text via getattr (more defensive)
        try:
            text = getattr(chunk, 'text', None)
            if text is not None:
                return text
        except (AttributeError, ValueError):
            pass
        
        # Strategy 4: Try to access via __dict__ or dir() if available (last resort)
        try:
            if hasattr(chunk, '__dict__'):
                for key in ['text', 'content', 'delta']:
                    if hasattr(chunk, key):
                        value = getattr(chunk, key, None)
                        if isinstance(value, str):
                            return value
        except (AttributeError, ValueError):
            pass
        
        return None
    
    def _extract_text_from_gemini_response(response) -> str:
        """
        Extract text from a complete Gemini response.
        
        Args:
            response: Complete Gemini response object
            
        Returns:
            Extracted text as string
            
        Raises:
            ValueError: If no text can be extracted
        """
        # Try direct text extraction first
        try:
            return response.text
        except ValueError:
            pass
        
        # Fallback: Extract from parts manually
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                text_parts = []
                for part in candidate.content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
                if text_parts:
                    return ''.join(text_parts)
        
        raise ValueError("Failed to extract text from Gemini response")
    
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
            """
            Generate text using Gemini.
            
            Handles Gemini-specific error cases:
            - No candidates returned
            - Content blocked by safety filters
            - Text extraction failures
            
            Safety Settings:
            - Uses default Gemini safety settings
            - Can be controlled via kwargs['safety_settings'] if needed
            """
            # Default temperature: 0.3 (more deterministic, can be overridden via kwargs)
            temperature = kwargs.get('temperature', 0.3)
            
            # Use default safety settings (no custom overrides)
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=kwargs.get('max_tokens', 400),
                )
            )
            
            # Validate response has candidates
            if not response.candidates or len(response.candidates) == 0:
                raise ValueError("No candidates returned from Gemini API")
            
            candidate = response.candidates[0]
            
            # Check if content was blocked by safety filters
            if _is_gemini_content_blocked(candidate):
                raise ValueError(
                    "Content was blocked by Gemini safety filters. "
                    "Try rephrasing your prompt."
                )
            
            # Extract text from response
            return _extract_text_from_gemini_response(response)
        
        async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
            """
            Stream text using Gemini.
            
            Gemini's API is synchronous, so we use a thread executor and queue
            to bridge it to async. This handles:
            - Converting sync generator to async generator
            - Proper error handling (StopIteration is normal completion)
            - Clean shutdown
            
            Note: Gemini streaming chunks contain incremental text (new text since last chunk),
            not cumulative text. Each chunk should be yielded immediately.
            """
            chunk_queue = asyncio.Queue(maxsize=100)
            exception_holder = [None]
            
            # Get the running event loop (preferred over get_event_loop)
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.get_event_loop()
            
            def _generate_chunks():
                """
                Run synchronous Gemini generation in a thread.
                
                This function runs in a separate thread because Gemini's API
                is synchronous. It puts chunks into a queue for async consumption.
                """
                # Default temperature: 0.3 (more deterministic, can be overridden via kwargs)
                temperature = kwargs.get('temperature', 0.3)
                
                try:
                    # Generate content with streaming enabled (using default safety settings)
                    response = self.model.generate_content(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=temperature,
                            max_output_tokens=kwargs.get('max_tokens', 400),
                        ),
                        stream=True
                    )
                    
                    # Iterate over streaming chunks
                    # Gemini's stream=True returns a generator that yields chunks
                    chunk_count = 0
                    for chunk in response:
                        chunk_count += 1
                        
                        # Extract text from this chunk using multiple strategies
                        text = _extract_text_from_gemini_chunk(chunk)
                        
                        # If extraction failed, try alternative methods
                        if not text:
                            # Try accessing chunk.text directly (might work for some versions)
                            try:
                                if hasattr(chunk, 'text'):
                                    text = chunk.text
                            except (AttributeError, ValueError):
                                pass
                        
                        # If we still don't have text, try deeper extraction
                        if not text:
                            try:
                                if hasattr(chunk, 'candidates') and chunk.candidates:
                                    candidate = chunk.candidates[0]
                                    if hasattr(candidate, 'content') and candidate.content:
                                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                                            for part in candidate.content.parts:
                                                if hasattr(part, 'text') and part.text:
                                                    text = part.text
                                                    break
                            except (AttributeError, IndexError, ValueError):
                                pass
                        
                        # For Gemini streaming, chunks can be empty strings (incremental updates)
                        # We should queue them anyway, but skip completely None/empty after trimming
                        # However, empty strings are valid (they represent no new text in this chunk)
                        # So we queue any non-None value, including empty strings
                        if text is not None:
                            # Put chunk in queue from sync context
                            # Use run_coroutine_threadsafe to safely call async from sync thread
                            try:
                                future = asyncio.run_coroutine_threadsafe(
                                    chunk_queue.put(text),
                                    loop
                                )
                                # Wait for the put to complete (with timeout to avoid deadlock)
                                future.result(timeout=2.0)
                            except Exception:
                                # If queue is full or other error, continue
                                # Don't break the stream
                                pass
                    
                    # Normal completion - signal end with None
                    asyncio.run_coroutine_threadsafe(
                        chunk_queue.put(None),
                        loop
                    )
                    
                except StopIteration:
                    # StopIteration is normal completion when generator ends
                    asyncio.run_coroutine_threadsafe(
                        chunk_queue.put(None),
                        loop
                    )
                except Exception as e:
                    # Real errors - store and signal completion
                    exception_holder[0] = e
                    # Still signal completion so async loop doesn't hang
                    asyncio.run_coroutine_threadsafe(
                        chunk_queue.put(None),
                        loop
                    )
            
            # Start generation in a thread using run_in_executor
            executor_task = loop.run_in_executor(None, _generate_chunks)
            
            # Yield chunks as they arrive
            try:
                while True:
                    # Get chunk from queue (with timeout to avoid infinite wait)
                    try:
                        chunk = await asyncio.wait_for(chunk_queue.get(), timeout=60.0)
                    except asyncio.TimeoutError:
                        # Timeout waiting for chunk - likely an error
                        if exception_holder[0]:
                            raise exception_holder[0]
                        raise TimeoutError("Timeout waiting for Gemini streaming response")
                    
                    # None signals completion
                    if chunk is None:
                        # Check for errors (but StopIteration is normal)
                        if exception_holder[0]:
                            if isinstance(exception_holder[0], StopIteration):
                                # Normal completion
                                break
                            raise exception_holder[0]
                        # Normal completion - no errors
                        break
                    
                    # Yield the chunk immediately
                    yield chunk
                    
            except RuntimeError as e:
                # Some async frameworks convert StopIteration to RuntimeError
                error_str = str(e).lower()
                if "stopiteration" in error_str or "async generator" in error_str:
                    # Normal completion, not an error
                    return
                raise
            finally:
                # Clean up executor - wait for thread to finish
                try:
                    await asyncio.wait_for(executor_task, timeout=5.0)
                except (asyncio.TimeoutError, Exception):
                    # Executor cleanup failed, but that's okay
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
    # Import error classes (may vary by OpenAI SDK version)
    try:
        from openai import RateLimitError, APIError
    except ImportError:
        # Fallback: use base exception for older SDK versions
        # We'll check status codes manually if needed
        try:
            from openai import OpenAIError
            RateLimitError = OpenAIError
            APIError = OpenAIError
        except ImportError:
            # Ultimate fallback
            RateLimitError = Exception
            APIError = Exception
    
    class OpenRouterProvider(LLMProvider):
        """
        OpenRouter Provider
        
        Pros: Access to many models (Claude, GPT-4, Llama, etc.), unified API
        Cons: Requires internet connection, paid service, rate limits on free models
        
        How it works:
        - Uses OpenAI-compatible API format
        - Same code structure as OpenAI provider
        - Just change the base URL and API key
        - This demonstrates API compatibility patterns!
        
        Key Learning: OpenAI-compatible APIs let you use the same code
        to access different AI providers. This is called "API compatibility".
        
        Rate Limiting:
        - Free models have strict rate limits (429 errors)
        - This provider includes retry logic with exponential backoff
        - Consider using paid models for production workloads
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
            
            # Configure client with retry settings for rate limits
            # max_retries=3 with exponential backoff handles transient errors
            self.client = AsyncOpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
                default_headers=headers,
                max_retries=3,  # Retry up to 3 times with exponential backoff
                timeout=60.0  # 60 second timeout
            )
        
        async def _retry_with_backoff(self, operation, max_retries: int = 5, initial_delay: float = 1.0):
            """
            Retry operation with exponential backoff for rate limit errors.
            
            Args:
                operation: Async function to retry
                max_retries: Maximum number of retry attempts
                initial_delay: Initial delay in seconds before first retry
                
            Returns:
                Result of the operation
                
            Raises:
                RateLimitError: If rate limit persists after all retries
                APIError: For other API errors
            """
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await operation()
                except Exception as e:
                    # Check if this is a rate limit error (429)
                    is_rate_limit = False
                    status_code = None
                    
                    # Check if it's a RateLimitError
                    if isinstance(e, RateLimitError):
                        is_rate_limit = True
                    # Check status code if available (for 429 errors)
                    elif hasattr(e, 'status_code'):
                        status_code = e.status_code
                        is_rate_limit = (status_code == 429)
                    elif hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                        status_code = e.response.status_code
                        is_rate_limit = (status_code == 429)
                    elif hasattr(e, 'code') and e.code == 'rate_limit_exceeded':
                        is_rate_limit = True
                    # Check error message for rate limit indicators
                    elif '429' in str(e) or 'rate limit' in str(e).lower() or 'too many requests' in str(e).lower():
                        is_rate_limit = True
                    
                    if is_rate_limit:
                        last_exception = e
                        if attempt < max_retries - 1:
                            # Exponential backoff: 1s, 2s, 4s, 8s, 16s
                            delay = initial_delay * (2 ** attempt)
                            # For 429 errors, check if Retry-After header is present
                            if hasattr(e, 'response') and e.response:
                                retry_after = e.response.headers.get('Retry-After')
                                if retry_after:
                                    try:
                                        delay = float(retry_after)
                                    except (ValueError, TypeError):
                                        pass
                            
                            await asyncio.sleep(delay)
                        else:
                            # Last attempt failed
                            raise RateLimitError(
                                f"OpenRouter rate limit exceeded after {max_retries} retries. "
                                f"Free models have strict rate limits. "
                                f"Consider: 1) Using a paid model, 2) Adding delays between requests, "
                                f"3) Using a different provider (Gemini, FireworksAI), or "
                                f"4) Upgrading your OpenRouter plan. "
                                f"Model: {self.model}"
                            ) from e
                    else:
                        # For other API errors, don't retry
                        if isinstance(e, APIError):
                            raise APIError(
                                f"OpenRouter API error: {str(e)}. "
                                f"Model: {self.model}"
                            ) from e
                        # Re-raise non-rate-limit errors immediately
                        raise
            
            # Should not reach here, but just in case
            if last_exception:
                raise last_exception
        
        async def generate_text(self, prompt: str, **kwargs) -> str:
            """Generate text using OpenRouter with retry logic for rate limits"""
            async def _generate():
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=kwargs.get('temperature', 0.8),
                    max_tokens=kwargs.get('max_tokens', 1000),
                )
                return response.choices[0].message.content
            
            return await self._retry_with_backoff(_generate)
        
        async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
            """Stream text using OpenRouter with retry logic for rate limits"""
            async def _generate_stream():
                stream = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=kwargs.get('temperature', 0.8),
                    max_tokens=kwargs.get('max_tokens', 1000),
                    stream=True
                )
                return stream
            
            # Retry the initial request creation
            try:
                stream = await self._retry_with_backoff(_generate_stream)
            except RateLimitError as e:
                # Yield error message as stream chunk for user feedback
                error_msg = (
                    f"\n\n⚠️ Rate limit error: {str(e)}\n"
                    f"Please wait a moment and try again, or consider using a different provider.\n"
                )
                yield error_msg
                return
            
            # Stream chunks (no retry needed for individual chunks)
            try:
                async for chunk in stream:
                    if chunk.choices and len(chunk.choices) > 0:
                        if chunk.choices[0].delta.content:
                            yield chunk.choices[0].delta.content
            except (RateLimitError, APIError) as e:
                # Handle errors during streaming
                error_msg = (
                    f"\n\n⚠️ Error during streaming: {str(e)}\n"
                    f"Model: {self.model}\n"
                )
                yield error_msg


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
        model = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-r1-0528-qwen3-8b:free")
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
            "base_url": None,  # Gemini uses native client, not OpenAI-compatible endpoint
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
- OPENROUTER_MODEL=model-name
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