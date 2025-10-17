"""
LLM Provider Utilities for AI Bootcamp Notebooks

This module provides unified interfaces for different LLM providers including
OpenAI, Google Gemini, and Fireworks AI. It includes proper error handling,
rate limiting, and cost tracking.
"""

import os
import time
import json
import requests
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LLMConfig:
    """Configuration for LLM providers"""
    provider: str
    model: str
    api_key: str
    base_url: Optional[str] = None
    max_tokens: int = None
    temperature: float = None
    top_p: float = None
    embedding_model: str = None
    timeout: int = 30
    max_retries: int = 3
    rate_limit_delay: float = 0.5
    
    def __post_init__(self):
        """Set default values from environment variables"""
        if self.max_tokens is None:
            self.max_tokens = int(os.getenv('DEFAULT_MAX_TOKENS', '1000'))
        if self.temperature is None:
            self.temperature = float(os.getenv('DEFAULT_TEMPERATURE', '0.7'))
        if self.top_p is None:
            self.top_p = float(os.getenv('DEFAULT_TOP_P', '0.9'))
        
        # Set embedding model based on provider
        if self.embedding_model is None:
            if self.provider == 'openai':
                self.embedding_model = os.getenv('DEFAULT_OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
            elif self.provider == 'gemini':
                self.embedding_model = os.getenv('DEFAULT_GEMINI_EMBEDDING_MODEL', 'embedding-001')
            elif self.provider == 'ollama':
                self.embedding_model = os.getenv('DEFAULT_OLLAMA_EMBEDDING_MODEL', 'nomic-embed-text:latest')

@dataclass
class UsageStats:
    """Track usage statistics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    average_latency: float = 0.0
    last_request_time: Optional[datetime] = None

class BaseLLMProvider:
    """Base class for LLM providers"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.session = requests.Session()
        self.stats = UsageStats()
        self._setup_session()
    
    def _setup_session(self):
        """Setup HTTP session with proper headers"""
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.config.api_key}'
        })
    
    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate text from prompt - to be implemented by subclasses"""
        raise NotImplementedError
    
    def _make_request(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request with error handling and retries"""
        start_time = time.time()
        
        for attempt in range(self.config.max_retries):
            try:
                # Rate limiting
                if self.stats.total_requests > 0:
                    time.sleep(self.config.rate_limit_delay)
                
                response = self.session.post(
                    url, 
                    json=payload, 
                    timeout=self.config.timeout
                )
                response.raise_for_status()
                
                # Update stats
                self.stats.total_requests += 1
                self.stats.successful_requests += 1
                self.stats.last_request_time = datetime.now()
                
                latency = time.time() - start_time
                self.stats.average_latency = (
                    (self.stats.average_latency * (self.stats.successful_requests - 1) + latency) 
                    / self.stats.successful_requests
                )
                
                return response.json()
                
            except requests.exceptions.RequestException as e:
                self.stats.total_requests += 1
                self.stats.failed_requests += 1
                
                if attempt < self.config.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {wait_time}s: {str(e)}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Max retries exceeded: {str(e)}")
                    return {"error": f"API request failed: {str(e)}"}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            'total_requests': self.stats.total_requests,
            'successful_requests': self.stats.successful_requests,
            'failed_requests': self.stats.failed_requests,
            'success_rate': (self.stats.successful_requests / self.stats.total_requests * 100) if self.stats.total_requests > 0 else 0,
            'total_tokens': self.stats.total_tokens,
            'total_cost': self.stats.total_cost,
            'average_latency': self.stats.average_latency,
            'last_request_time': self.stats.last_request_time.isoformat() if self.stats.last_request_time else None
        }

class OpenAIProvider(BaseLLMProvider):
    """OpenAI API implementation"""
    
    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate text using OpenAI API"""
        url = f"{self.config.base_url}/chat/completions"
        
        payload = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get('max_tokens', self.config.max_tokens),
            "temperature": kwargs.get('temperature', self.config.temperature),
            "top_p": kwargs.get('top_p', self.config.top_p)
        }
        
        result = self._make_request(url, payload)
        
        # Track usage if successful
        if 'usage' in result and 'error' not in result:
            self.stats.total_tokens += result['usage'].get('total_tokens', 0)
            # Approximate cost calculation (varies by model)
            self.stats.total_cost += result['usage'].get('total_tokens', 0) * 0.000002  # Rough estimate
        
        return result

class GeminiProvider(BaseLLMProvider):
    """Google Gemini API implementation"""
    
    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate text using Gemini API"""
        url = f"{self.config.base_url}/models/{self.config.model}:generateContent"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": kwargs.get('max_tokens', self.config.max_tokens),
                "temperature": kwargs.get('temperature', self.config.temperature),
                "topP": kwargs.get('top_p', self.config.top_p)
            }
        }
        
        result = self._make_request(url, payload)
        
        # Track usage if successful
        if 'usageMetadata' in result and 'error' not in result:
            self.stats.total_tokens += result['usageMetadata'].get('totalTokenCount', 0)
            # Approximate cost calculation
            self.stats.total_cost += result['usageMetadata'].get('totalTokenCount', 0) * 0.000001  # Rough estimate
        
        return result
    
    def embed_text(self, text: str, **kwargs) -> Dict[str, Any]:
        """Generate embeddings using Gemini API"""
        url = f"{self.config.base_url}/models/embedding-001:embedContent"
        
        payload = {
            "content": {"parts": [{"text": text}]}
        }
        
        result = self._make_request(url, payload)
        
        # Track usage if successful
        if 'usageMetadata' in result and 'error' not in result:
            self.stats.total_tokens += result['usageMetadata'].get('totalTokenCount', 0)
            # Embedding cost is typically lower
            self.stats.total_cost += result['usageMetadata'].get('totalTokenCount', 0) * 0.0000005
        
        return result

class FireworksProvider(BaseLLMProvider):
    """Fireworks AI API implementation"""
    
    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate text using Fireworks AI API"""
        url = f"{self.config.base_url}/chat/completions"
        
        payload = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get('max_tokens', self.config.max_tokens),
            "temperature": kwargs.get('temperature', self.config.temperature),
            "top_p": kwargs.get('top_p', self.config.top_p)
        }
        
        result = self._make_request(url, payload)
        
        # Track usage if successful
        if 'usage' in result and 'error' not in result:
            self.stats.total_tokens += result['usage'].get('total_tokens', 0)
            # Approximate cost calculation
            self.stats.total_cost += result['usage'].get('total_tokens', 0) * 0.000001  # Rough estimate
        
        return result

class OllamaProvider(BaseLLMProvider):
    """Ollama local API implementation"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        # Ollama doesn't need API key, but we'll use it for model identification
        self.session.headers.pop('Authorization', None)
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
    
    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate text using Ollama local API"""
        url = f"{self.config.base_url}/api/generate"
        
        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get('temperature', self.config.temperature),
                "top_p": kwargs.get('top_p', self.config.top_p),
                "num_predict": kwargs.get('max_tokens', self.config.max_tokens)
            }
        }
        
        result = self._make_request(url, payload)
        
        # Convert Ollama response to standard format
        if 'error' not in result and 'response' in result:
            # Estimate tokens (rough approximation)
            estimated_tokens = len(result['response'].split()) * 1.33
            self.stats.total_tokens += int(estimated_tokens)
            # Ollama is free, so no cost
            self.stats.total_cost += 0.0
            
            # Convert to standard format
            return {
                "choices": [{
                    "message": {
                        "content": result['response']
                    }
                }],
                "usage": {
                    "total_tokens": int(estimated_tokens)
                }
            }
        
        return result
    
    def embed_text(self, text: str, **kwargs) -> Dict[str, Any]:
        """Generate embeddings using Ollama API"""
        url = f"{self.config.base_url}/api/embeddings"
        
        # Use configured embedding model or fallback to nomic-embed-text
        embedding_model = kwargs.get('embedding_model', self.config.embedding_model or 'nomic-embed-text:latest')
        
        payload = {
            "model": embedding_model,
            "prompt": text
        }
        
        result = self._make_request(url, payload)
        
        # Track usage if successful
        if 'embedding' in result and 'error' not in result:
            # Estimate tokens for embedding
            estimated_tokens = len(text.split())
            self.stats.total_tokens += estimated_tokens
            # Ollama is free, so no cost
            self.stats.total_cost += 0.0
        
        return result

class LLMProviderFactory:
    """Factory for creating LLM providers"""
    
    @staticmethod
    def create_provider(provider_name: str, config: LLMConfig) -> BaseLLMProvider:
        """Create a provider instance"""
        providers = {
            'openai': OpenAIProvider,
            'gemini': GeminiProvider,
            'fireworks': FireworksProvider,
            'ollama': OllamaProvider
        }
        
        if provider_name not in providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        return providers[provider_name](config)
    
    @staticmethod
    def create_from_env(provider_name: str) -> Optional[BaseLLMProvider]:
        """Create provider from environment variables"""
        api_key = None
        base_url = None
        
        if provider_name == 'openai':
            api_key = os.getenv('OPENAI_API_KEY')
            base_url = 'https://api.openai.com/v1'
        elif provider_name == 'gemini':
            api_key = os.getenv('GEMINI_API_KEY')
            base_url = 'https://generativelanguage.googleapis.com/v1'
        elif provider_name == 'fireworks':
            api_key = os.getenv('FIREWORKS_API_KEY')
            base_url = 'https://api.fireworks.ai/inference/v1'
        elif provider_name == 'ollama':
            # Ollama doesn't need API key, check if service is running
            base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
            api_key = 'ollama'  # Placeholder for consistency
        
        if not api_key:
            return None
        
        # Get models from environment variables with fallbacks
        default_models = {
            'openai': os.getenv('DEFAULT_OPENAI_MODEL', 'gpt-4o-mini'),
            'gemini': os.getenv('DEFAULT_GEMINI_MODEL', 'gemini-2.5-flash'),
            'fireworks': os.getenv('DEFAULT_FIREWORKS_MODEL', 'accounts/fireworks/models/llama-v3p1-8b-instruct'),
            'ollama': os.getenv('DEFAULT_OLLAMA_MODEL', 'llama3.2:latest')
        }
        
        config = LLMConfig(
            provider=provider_name,
            model=default_models[provider_name],
            api_key=api_key,
            base_url=base_url
        )
        
        return LLMProviderFactory.create_provider(provider_name, config)

def get_available_providers() -> Dict[str, BaseLLMProvider]:
    """Get all available providers from environment"""
    providers = {}
    
    # Check cloud providers first (preferred)
    for provider_name in ['openai', 'gemini', 'fireworks']:
        provider = LLMProviderFactory.create_from_env(provider_name)
        if provider:
            providers[provider_name] = provider
    
    # Check Ollama as fallback (local)
    ollama_provider = LLMProviderFactory.create_from_env('ollama')
    if ollama_provider:
        # Test if Ollama is actually running
        try:
            test_result = ollama_provider.generate("test", max_tokens=1)
            if 'error' not in test_result:
                providers['ollama'] = ollama_provider
        except:
            pass  # Ollama not running, skip it
    
    return providers

def test_provider(provider: BaseLLMProvider, test_prompt: str = "Hello, how are you?") -> Dict[str, Any]:
    """Test a provider with a simple prompt"""
    try:
        result = provider.generate(test_prompt, max_tokens=50)
        return {
            'success': 'error' not in result,
            'response': result,
            'stats': provider.get_stats()
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'stats': provider.get_stats()
        }

# Example usage
if __name__ == "__main__":
    # Test all available providers
    providers = get_available_providers()
    
    print(f"🔧 Available providers: {list(providers.keys())}")
    
    for name, provider in providers.items():
        print(f"\n🧪 Testing {name.upper()}...")
        test_result = test_provider(provider)
        
        if test_result['success']:
            print(f"   ✅ Success!")
            print(f"   📊 Stats: {test_result['stats']}")
        else:
            print(f"   ❌ Failed: {test_result.get('error', 'Unknown error')}")
