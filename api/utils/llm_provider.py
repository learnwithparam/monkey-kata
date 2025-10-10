"""
LLM Provider
============

A flexible provider that supports multiple LLM APIs:
- Google Gemini (free tier available)
- OpenAI GPT models
- Easy to extend for other providers

Usage:
    from utils.llm_provider import LLMProvider
    
    provider = LLMProvider()
    response = await provider.generate_text("Hello, world!")
    async for chunk in provider.generate_stream("Tell me a story"):
        print(chunk)
"""

import os
import asyncio
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, Optional
from enum import Enum
import json

# OpenAI imports
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Google Gemini imports
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class LLMProviderType(Enum):
    """Supported LLM providers"""
    GEMINI = "gemini"
    OPENAI = "openai"
    FIREWORKS = "fireworks"
    MOCK = "mock"

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt"""
        pass
    
    @abstractmethod
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Generate streaming text from a prompt"""
        pass

class GeminiProvider(LLMProvider):
    """Google Gemini provider"""
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-lite"):
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai package not installed")
        
        self.api_key = api_key
        self.model_name = model
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using Gemini"""
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=kwargs.get('temperature', 0.8),
                    max_output_tokens=kwargs.get('max_tokens', 1000),
                )
            )
            # Check if response is blocked or empty
            if not response.text:
                print(f"Gemini response blocked or empty. Finish reason: {getattr(response, 'candidates', [{}])[0].get('finish_reason', 'unknown')}")
                # Return a simple fallback story
                return """{
    "title": "A Gentle Adventure",
    "story": "Once upon a time, there was a kind character who learned about friendship and kindness. They had a wonderful day and went to sleep happy.",
    "moral": "Being kind and friendly makes everyone happy"
}"""
            
            return response.text
        except Exception as e:
            print(f"Gemini API error details: {str(e)}")
            print(f"Using model: {self.model_name}")
            # Return a fallback instead of raising an error
            return """{
    "title": "A Gentle Adventure", 
    "story": "Once upon a time, there was a kind character who learned about friendship and kindness. They had a wonderful day and went to sleep happy.",
    "moral": "Being kind and friendly makes everyone happy"
}"""
    
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Generate streaming text using Gemini"""
        try:
            # Use Gemini's streaming API
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=kwargs.get('temperature', 0.3),
                    max_output_tokens=kwargs.get('max_tokens', 1000),
                ),
                stream=True
            )
            
            # Stream the response chunks
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    # Small delay to make streaming visible but not too slow
                    await asyncio.sleep(0.01)
                    
        except Exception as e:
            yield f"Error: {str(e)}"

class FireworksAIProvider(LLMProvider):
    """FireworksAI provider"""
    
    def __init__(self, api_key: str, model: str = "accounts/fireworks/models/qwen3-235b-a22b-instruct-2507"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.fireworks.ai/inference/v1/chat/completions"
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using FireworksAI API"""
        import aiohttp
        import json
        
        payload = {
            "model": self.model,
            "max_tokens": kwargs.get('max_tokens', 1000),
            "top_p": 1,
            "top_k": 40,
            "presence_penalty": 0,
            "frequency_penalty": 0,
            "temperature": kwargs.get('temperature', 0.7),
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
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
        """Generate streaming text using FireworksAI API"""
        import aiohttp
        import json
        
        payload = {
            "model": self.model,
            "max_tokens": kwargs.get('max_tokens', 1000),
            "top_p": 1,
            "top_k": 40,
            "presence_penalty": 0,
            "frequency_penalty": 0,
            "temperature": kwargs.get('temperature', 0.7),
            "stream": True,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
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
                            data = line[6:]  # Remove 'data: ' prefix
                            if data == '[DONE]':
                                break
                            try:
                                chunk = json.loads(data)
                                if 'choices' in chunk and len(chunk['choices']) > 0:
                                    delta = chunk['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        yield delta['content']
                                        await asyncio.sleep(0.01)  # Small delay for visual effect
                            except json.JSONDecodeError:
                                continue
                else:
                    error_text = await response.text()
                    raise Exception(f"FireworksAI API error {response.status}: {error_text}")

class OpenAIProvider(LLMProvider):
    """OpenAI provider"""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package not installed")
        
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using OpenAI"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get('temperature', 0.8),
                max_tokens=kwargs.get('max_tokens', 1000),
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Generate streaming text using OpenAI"""
        try:
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
        except Exception as e:
            yield f"Error: {str(e)}"

class MockProvider(LLMProvider):
    """Mock provider for demos and testing"""
    
    def __init__(self):
        self.mock_responses = {
            "story": "Once upon a time, there was a brave little character who went on amazing adventures. They learned about courage, kindness, and the importance of believing in themselves. The end.",
            "analysis": "This is a mock analysis. In a real implementation, this would contain detailed insights and recommendations.",
            "qa": "This is a mock answer. The actual response would be generated based on the provided context and question.",
            "default": "This is a mock response. Set up your API keys to get real AI-generated content!"
        }
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate mock text"""
        # Simple keyword matching for different types of responses
        prompt_lower = prompt.lower()
        
        if any(word in prompt_lower for word in ["story", "tale", "adventure", "bedtime"]):
            return self.mock_responses["story"]
        elif any(word in prompt_lower for word in ["analyze", "analysis", "document", "contract"]):
            return self.mock_responses["analysis"]
        elif any(word in prompt_lower for word in ["question", "answer", "what", "how", "why"]):
            return self.mock_responses["qa"]
        else:
            return self.mock_responses["default"]
    
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Generate mock streaming text"""
        response = await self.generate_text(prompt, **kwargs)
        
        # Split into words and stream them
        words = response.split()
        for word in words:
            await asyncio.sleep(0.05)  # Simulate streaming delay
            yield word + " "

class LLMProviderFactory:
    """Factory for creating LLM providers based on environment configuration"""
    
    @staticmethod
    def create_provider() -> LLMProvider:
        """Create LLM provider based on environment variables"""
        
        # Check for provider preference
        provider_type = os.getenv("LLM_PROVIDER", "").lower()
        
        # Check for FireworksAI
        fireworks_key = os.getenv("FIREWORKS_API_KEY")
        if fireworks_key and (provider_type == "fireworks" or not provider_type):
            model = os.getenv("FIREWORKS_MODEL", "accounts/fireworks/models/qwen3-235b-a22b-instruct-2507")
            print(f"🤖 Using FireworksAI provider with model: {model}")
            return FireworksAIProvider(api_key=fireworks_key, model=model)
        
        # Check for Gemini (free tier)
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key and (provider_type == "gemini" or not provider_type):
            model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")
            print(f"🤖 Using Google Gemini provider with model: {model}")
            return GeminiProvider(api_key=gemini_key, model=model)
        
        # Check for OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and (provider_type == "openai" or not provider_type):
            model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
            print(f"🤖 Using OpenAI provider with model: {model}")
            return OpenAIProvider(api_key=openai_key, model=model)
        
        # Fall back to mock provider
        print("🤖 Using Mock provider (set FIREWORKS_API_KEY, GEMINI_API_KEY, or OPENAI_API_KEY for real AI)")
        return MockProvider()
    
    @staticmethod
    def get_available_providers() -> Dict[str, bool]:
        """Get information about available providers"""
        return {
            "fireworks": True,  # FireworksAI uses aiohttp which is always available
            "gemini": GEMINI_AVAILABLE,
            "openai": OPENAI_AVAILABLE,
            "mock": True
        }

# Convenience function for easy usage
def get_llm_provider() -> LLMProvider:
    """Get the configured LLM provider"""
    return LLMProviderFactory.create_provider()

# Example usage
if __name__ == "__main__":
    async def main():
        provider = get_llm_provider()
        
        # Test text generation
        response = await provider.generate_text("Tell me a short story about a robot")
        print("Text response:", response)
        
        # Test streaming
        print("\nStreaming response:")
        async for chunk in provider.generate_stream("What is artificial intelligence?"):
            print(chunk, end="", flush=True)
        print()
    
    asyncio.run(main())
