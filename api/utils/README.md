# LLM Provider
==============

A flexible, multi-provider LLM integration system for the AI Bootcamp demos.

## 🎯 Learning Objectives

This module teaches you how to build production-grade LLM integrations:

1. **Abstraction Patterns** - Design interchangeable components
2. **Provider Pattern** - Support multiple AI services seamlessly
3. **API Compatibility** - Understand OpenAI-compatible APIs
4. **Streaming** - Implement real-time text generation
5. **Factory Pattern** - Automatic provider selection

## Quick Start

### 1. Set Environment Variables

Choose one provider and set its API key:

```bash
# Option 1: FireworksAI (recommended for performance)
FIREWORKS_API_KEY=your_fireworks_api_key_here

# Option 2: OpenRouter (access to many models)
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Option 3: Google Gemini (free tier available)
GEMINI_API_KEY=your_gemini_api_key_here

# Option 4: OpenAI
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. Use in Your Code

```python
from utils.llm_provider import get_llm_provider

# Get the configured provider automatically
provider = get_llm_provider()

# Generate complete text
response = await provider.generate_text("Explain quantum computing")

# Generate streaming text (ChatGPT-like experience)
async for chunk in provider.generate_stream("Write a story"):
    print(chunk, end="", flush=True)
```

### 3. Customize Generation Parameters

```python
# Control creativity and length
response = await provider.generate_text(
    "Write a creative story",
    temperature=0.8,  # Higher = more creative (0.0-2.0)
    max_tokens=500    # Maximum response length
)
```

## Provider Priority

The system automatically selects providers in this order:

1. **FireworksAI** (if `FIREWORKS_API_KEY` is set)
2. **OpenRouter** (if `OPENROUTER_API_KEY` is set)
3. **Google Gemini** (if `GEMINI_API_KEY` is set)
4. **OpenAI** (if `OPENAI_API_KEY` is set)

You can force a specific provider:

```bash
LLM_PROVIDER=openrouter  # Force OpenRouter
```

## Supported Providers

### FireworksAI

- **Pros**: Fast inference, competitive pricing
- **Default Model**: `accounts/fireworks/models/qwen3-235b-a22b-instruct-2507`
- **Best For**: Production applications requiring speed

```bash
FIREWORKS_API_KEY=your_key
FIREWORKS_MODEL=accounts/fireworks/models/qwen3-235b-a22b-instruct-2507
```

### OpenRouter

- **Pros**: Access to many models (Claude, GPT-4, Llama, etc.), unified API
- **Default Model**: `deepseek/deepseek-r1-0528-qwen3-8b:free` (free model)
- **Best For**: Trying different models, cost-effective options

```bash
OPENROUTER_API_KEY=your_key
OPENROUTER_MODEL=deepseek/deepseek-r1-0528-qwen3-8b:free  # or anthropic/claude-3.5-sonnet, etc.
# Optional headers
OPENROUTER_HTTP_REFERER=https://your-app-url.com
OPENROUTER_APP_NAME=Your App Name
```

**Popular OpenRouter Models:**
- `deepseek/deepseek-r1-0528-qwen3-8b:free` - Free, good quality
- `anthropic/claude-3.5-sonnet` - High quality, paid
- `google/gemini-flash-1.5` - Free, fast
- `openai/gpt-4o-mini` - Cost-effective GPT-4 variant

### Google Gemini

- **Pros**: Free tier available, excellent quality
- **Default Model**: `gemini-2.5-flash`
- **Best For**: Learning, prototyping, cost-sensitive applications

```bash
GEMINI_API_KEY=your_key
GEMINI_MODEL=gemini-2.5-flash
```

### OpenAI

- **Pros**: Industry standard, very high quality
- **Default Model**: `gpt-4o-mini`
- **Best For**: Production applications requiring highest quality

```bash
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o-mini
```

## Getting API Keys

### FireworksAI
1. Visit [FireworksAI](https://fireworks.ai)
2. Create an account and get your API key
3. Set `FIREWORKS_API_KEY=your_key`

### OpenRouter
1. Visit [OpenRouter](https://openrouter.ai)
2. Create an account and get your API key
3. Set `OPENROUTER_API_KEY=your_key`
4. Choose a model (many free options available)

### Google Gemini (Free)
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Set `GEMINI_API_KEY=your_key`

### OpenAI (Paid)
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Set `OPENAI_API_KEY=your_key`

## Advanced Usage

### Using Provider-Specific Features

```python
from utils.llm_provider import (
    FireworksAIProvider,
    OpenRouterProvider,
    GeminiProvider,
    OpenAIProvider
)

# Use specific provider directly
openrouter = OpenRouterProvider(
    api_key="your_key",
    model="anthropic/claude-3.5-sonnet"
)

# Generate with custom parameters
response = await openrouter.generate_text(
    "Explain machine learning",
    temperature=0.7,  # Override default
    max_tokens=1000   # Override default
)
```

### Understanding Parameters

```python
# Temperature: Controls randomness/creativity
# 0.0 = deterministic, factual (good for Q&A)
# 0.7-0.8 = balanced (good for most tasks)
# 1.0+ = very creative (good for creative writing)
response = await provider.generate_text(
    prompt,
    temperature=0.7
)

# Max Tokens: Limits response length
# Lower = shorter responses, faster
# Higher = longer responses, more expensive
response = await provider.generate_text(
    prompt,
    max_tokens=500
)
```

### Streaming for Real-Time Responses

```python
async def stream_response(question: str):
    """Stream response chunk by chunk for better UX"""
    async for chunk in provider.generate_stream(question):
        # Send chunk to frontend immediately
        yield chunk
```

## Provider Features Comparison

| Feature | FireworksAI | OpenRouter | Gemini | OpenAI |
|---------|-------------|------------|--------|--------|
| Text Generation | ✅ | ✅ | ✅ | ✅ |
| Streaming | ✅ | ✅ | ✅ | ✅ |
| Free Tier | ❌ | ✅ (many models) | ✅ | ❌ |
| Multiple Models | ❌ | ✅ | ❌ | ❌ |
| OpenAI Compatible | ✅ | ✅ | ❌ | ✅ |

## Key Concepts

### Abstract Base Class Pattern

All providers implement the same interface:

```python
class LLMProvider(ABC):
    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> str:
        pass
    
    @abstractmethod
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        pass
```

This allows you to swap providers without changing your code!

### Factory Pattern

The `get_llm_provider()` function automatically:
1. Checks environment variables
2. Selects the best available provider
3. Returns a configured instance

```python
provider = get_llm_provider()  # Automatically configured!
```

### API Compatibility

OpenRouter and FireworksAI use OpenAI-compatible APIs, meaning:
- Same code works across providers
- Easy migration between providers
- Standardized request/response format

## Production Considerations

### Error Handling

```python
try:
    response = await provider.generate_text("Hello")
except Exception as e:
    # Log error
    logger.error(f"LLM generation failed: {e}")
    # Handle gracefully (retry, fallback, etc.)
```

### Rate Limiting

Most providers have rate limits:
- Monitor your API usage
- Implement retry logic with exponential backoff
- Consider caching responses for repeated queries

### Cost Optimization

1. **Use appropriate models**: Free models for testing, premium for production
2. **Set max_tokens**: Limit response length to control costs
3. **Cache embeddings**: Reuse embeddings for similar queries
4. **Monitor usage**: Track API calls and costs

### Security

- **Never commit API keys**: Use environment variables only
- **Rotate keys regularly**: Update API keys periodically
- **Use least privilege**: Grant minimum permissions needed
- **Monitor usage**: Watch for unexpected API calls

## Troubleshooting

### Common Issues

**"No module named 'google.generativeai'"**
```bash
pip install google-generativeai
```

**"No module named 'openai'"**
```bash
pip install openai
```

**"No LLM provider configured"**
- Set at least one API key (FIREWORKS_API_KEY, OPENROUTER_API_KEY, GEMINI_API_KEY, or OPENAI_API_KEY)
- Restart your application after setting environment variables

**API Key Not Working**
- Verify the key is correct
- Check you have credits/quota remaining
- Verify the key has required permissions
- For OpenRouter, ensure the model name is correct

**Provider Not Selected**
- Check provider priority order
- Set `LLM_PROVIDER=provider_name` to force selection
- Verify API key is set correctly

## Next Steps

1. **Experiment with different providers**: Try each one and compare results
2. **Adjust parameters**: Experiment with temperature and max_tokens
3. **Implement caching**: Cache responses for repeated queries
4. **Add monitoring**: Track API usage and costs
5. **Handle errors gracefully**: Implement retry logic and fallbacks

## Learning Path

This module teaches:
1. ✅ How abstraction enables code reusability
2. ✅ How the Provider Pattern works
3. ✅ How to integrate multiple AI services
4. ✅ How streaming improves user experience
5. ✅ How Factory Pattern simplifies configuration

Ready to build production AI applications! 🚀