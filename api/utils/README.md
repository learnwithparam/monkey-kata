# LLM Provider

A flexible, multi-provider LLM integration system for the AI Bootcamp demos.

## Features

- **Multiple Provider Support**: Google Gemini, OpenAI, and Mock provider
- **Automatic Fallback**: Falls back to Mock provider if no API keys are set
- **Streaming Support**: Real-time text generation for better UX
- **Easy Configuration**: Set API keys via environment variables
- **Cost-Effective**: Prioritizes free Gemini API over paid OpenAI

## Quick Start

### 1. Set Environment Variables

```bash
# For Google Gemini (recommended - free tier available)
GEMINI_API_KEY=your_gemini_api_key_here

# For OpenAI (optional)
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. Use in Your Code

```python
from utils.llm_provider import get_llm_provider

# Get the configured provider
provider = get_llm_provider()

# Generate text
response = await provider.generate_text("Tell me a story about a robot")

# Generate streaming text
async for chunk in provider.generate_stream("What is AI?"):
    print(chunk, end="", flush=True)
```

## Provider Priority

The system automatically selects providers in this order:

1. **Google Gemini** (if `GEMINI_API_KEY` is set)
2. **OpenAI** (if `OPENAI_API_KEY` is set)
3. **Mock Provider** (fallback for demos)

## Getting API Keys

### Google Gemini (Free)
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Set `GEMINI_API_KEY=your_key_here`

### OpenAI (Paid)
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Set `OPENAI_API_KEY=your_key_here`

## Provider Features

| Feature | Gemini | OpenAI | Mock |
|---------|--------|--------|------|
| Text Generation | ✅ | ✅ | ✅ |
| Streaming | ✅ (simulated) | ✅ | ✅ |
| Free Tier | ✅ | ❌ | ✅ |
| Real AI | ✅ | ✅ | ❌ |

## Advanced Usage

### Custom Configuration

```python
from utils.llm_provider import GeminiProvider, OpenAIProvider

# Use specific provider
gemini = GeminiProvider(api_key="your_key", model="gemini-1.5-pro")
openai = OpenAIProvider(api_key="your_key", model="gpt-4")

# Generate with custom parameters
response = await gemini.generate_text(
    "Write a story",
    temperature=0.9,
    max_tokens=2000
)
```

### Error Handling

```python
try:
    response = await provider.generate_text("Hello")
except Exception as e:
    print(f"LLM Error: {e}")
```

## Learning Objectives

This LLM provider teaches:

- **Factory Pattern**: How to create objects based on configuration
- **Abstract Base Classes**: Defining common interfaces
- **Async Programming**: Handling asynchronous operations
- **Error Handling**: Graceful fallbacks and error management
- **Environment Configuration**: Managing API keys securely
- **Streaming**: Real-time data processing

## Contributing

To add a new provider:

1. Create a new class inheriting from `LLMProvider`
2. Implement `generate_text()` and `generate_stream()` methods
3. Add the provider to `LLMProviderFactory`
4. Update this README

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

**API Key Not Working**
- Check your API key is correct
- Ensure you have credits/quota remaining
- Verify the key has the right permissions

**Mock Provider Always Used**
- Check environment variables are set correctly
- Restart your application after setting new env vars
- Verify the API key format is correct
