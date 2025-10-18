# AI Bootcamp Notebooks - Setup Guide

## Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp env.example .env

# Edit .env with your API keys
nano .env
```

### 2. Using Docker (Recommended)

```bash
# Start all services
make dev

# Or start specific services
make start
```

### 3. Using Local Environment

```bash
# Install dependencies
make install-notebooks-uv

# Start Jupyter Lab
make notebooks-uv
```

## Services Overview

| Service | Port | Description |
|---------|------|-------------|
| Jupyter Lab | 8888 | Main notebook environment |
| Qdrant | 6333 | Vector database |
| Redis | 6379 | Caching layer |
| Prometheus | 9090 | Monitoring (optional) |

## Environment Variables

### Required API Keys

```bash
# At least one LLM provider is required
OPENAI_API_KEY=sk-your-key-here
GEMINI_API_KEY=your-gemini-key-here
FIREWORKS_API_KEY=your-fireworks-key-here

# Optional: Local Ollama
OLLAMA_BASE_URL=http://localhost:11434
```

### Vector Database

```bash
# Qdrant (recommended)
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-qdrant-key-here

# Alternative: ChromaDB
CHROMA_PERSIST_DIRECTORY=./chroma_db
```

### Caching

```bash
# Redis (recommended)
REDIS_URL=redis://localhost:6379
```

## Notebook Structure

### Core RAG Notebooks
- `03_rag_fundamentals.ipynb` - Basic RAG implementation
- `03a_splitting_techniques.ipynb` - Document splitting strategies
- `03b_rag_optimization.ipynb` - Performance optimization
- `04_advanced_rag.ipynb` - Advanced RAG techniques
- `04a_agentic_rag.ipynb` - Multi-agent RAG systems
- `04b_rag_production.ipynb` - Production deployment patterns

### Advanced Topics
- `05_fine_tuning_custom_models.ipynb` - Fine-tuning techniques
- `06_advanced_applications.ipynb` - Real-world applications

### Framework Demos
- `demos/langchain_rag_demo.ipynb` - LangChain implementation
- `demos/llamaindex_rag_demo.ipynb` - LlamaIndex implementation

## Troubleshooting

### Common Issues

1. **No LLM providers available**
   - Check your `.env` file has valid API keys
   - Ensure at least one provider is configured

2. **Qdrant connection failed**
   - Check if Qdrant is running: `docker ps`
   - Verify `QDRANT_URL` in `.env`

3. **Redis connection failed**
   - Check if Redis is running: `docker ps`
   - Verify `REDIS_URL` in `.env`

4. **Import errors**
   - Run `make install-notebooks-uv` to install dependencies
   - Restart Jupyter kernel

### Performance Tips

1. **Use GPU for fine-tuning**
   - Ensure CUDA is available
   - Use smaller models for testing

2. **Optimize memory usage**
   - Use smaller chunk sizes
   - Enable caching for repeated queries

3. **Scale with Docker**
   - Use Docker Compose for production
   - Configure resource limits

## Development

### Adding New Notebooks

1. Create notebook in appropriate directory
2. Use LLM provider abstraction
3. Include proper error handling
4. Add to this documentation

### Testing

```bash
# Test all notebooks
make notebooks-test-uv

# Check syntax
make notebooks-check-uv
```

## Support

For issues and questions:
1. Check this documentation
2. Review notebook comments
3. Check environment configuration
4. Open an issue on GitHub
