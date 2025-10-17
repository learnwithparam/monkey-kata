# AI Bootcamp for Software Engineers

Comprehensive 6-week AI engineering program with interactive demos, notebooks, and production-ready implementations. Master LLMs, RAG systems, conversational AI, multi-agent workflows, and enterprise architecture.

## 🎯 Course Overview

**Duration**: 6 weeks | **Format**: Live sessions + Hands-on projects  
**Instructor**: Param Harrison | **Next Cohort**: November 2025

### Learning Path
- **Week 1**: LLMs, Prompts & RAG Systems
- **Week 2**: Conversational AI & Voice Systems  
- **Week 3**: AI Agents & Workflows
- **Week 4**: Production Optimization
- **Week 5**: System Design & Architecture
- **Week 6**: Capstone Project & Demo Day

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** (for notebooks and API)
- **Node.js 18+** (for frontend development)
- **Docker & Docker Compose** (recommended for full stack)
- **Git** (for version control)
- **API Keys** (OpenAI, Gemini, or Fireworks AI)

### 🐳 Full Stack Development (Docker)

1. **Clone and setup**
   ```bash
   git clone <repository-url>
   cd ai-bootcamp
   ```

2. **Start all services**
   ```bash
   make dev
   ```

3. **Access applications**
   - **API Server**: http://localhost:4010
   - **Frontend**: http://localhost:4020  
   - **API Docs**: http://localhost:4010/docs
   - **Jupyter Lab**: http://localhost:8888

### 📓 Notebook Development (Recommended for Learning)

1. **Setup notebooks environment**
   ```bash
   make setup-notebooks
   ```

2. **Configure API keys**
   ```bash
   # Edit notebooks/.env with your API keys
   make env-check-uv
   ```

3. **Start Jupyter Lab**
   ```bash
   make notebooks-uv
   ```

4. **Access notebooks**
   - Open http://localhost:8888
   - Navigate to week folders
   - Start with `01_llm_fundamentals.ipynb`

### 💻 Local Development (No Docker)

1. **Install dependencies**
   ```bash
   make install
   ```

2. **Start services locally**
   ```bash
   make dev-local
   ```

### 🛠️ Development Commands

#### **Core Development**
```bash
# Full stack development
make dev              # Start all services with Docker
make dev-local        # Start locally without Docker
make install          # Install all dependencies

# Individual services
make api              # Start only API server
make frontend         # Start only frontend server
```

#### **Notebook Development** 
```bash
# Environment setup
make setup-notebooks      # Complete notebook setup
make install-uv          # Install uv package manager
make install-notebooks-uv # Install with uv (recommended)
make install-notebooks-venv # Install with traditional venv

# Jupyter Lab
make notebooks-uv        # Start Jupyter Lab with uv
make notebooks-venv      # Start Jupyter Lab with venv
make notebooks-classic   # Start classic Jupyter Notebook

# Environment management
make env-setup           # Setup environment files
make env-check-uv        # Check environment with uv
make notebooks-env       # Setup notebook environment
```

#### **Docker Commands**
```bash
make build              # Build Docker images
make start              # Start production containers
make stop               # Stop all containers
make restart            # Restart all containers
make logs               # Show container logs
make clean              # Clean up containers and images
```

#### **Notebook Utilities**
```bash
make notebooks-clean-uv     # Clean notebook outputs
make notebooks-convert-uv  # Convert to HTML
make notebooks-check-uv    # Check notebook syntax
```

#### **Utility Commands**
```bash
make ports            # Show running services and ports
make help             # Show all available commands
make lint             # Run linting
make test             # Run tests
```

## 📁 Project Structure

```
ai-bootcamp/
├── 📓 notebooks/                    # Jupyter notebooks (6 weeks)
│   ├── week1-llms-prompts-rag/     # Week 1: LLMs, Prompts & RAG
│   ├── week2-conversational-systems/ # Week 2: Voice & Chat Systems
│   ├── week3-ai-agents-workflows/  # Week 3: AI Agents & Workflows
│   ├── week4-production-optimization/ # Week 4: Production Systems
│   ├── week5-system-design-architecture/ # Week 5: Enterprise Architecture
│   ├── week6-capstone-project/     # Week 6: Capstone Projects
│   ├── utils/                      # Notebook utilities
│   │   ├── llm_providers.py        # Multi-provider LLM utilities
│   │   └── test_notebooks.py       # Testing utilities
│   ├── requirements.txt            # Python dependencies
│   ├── env.example                 # Environment configuration
│   └── README.md                   # Notebook documentation
├── 🔧 api/                         # FastAPI backend
│   ├── main.py                     # Main FastAPI application
│   ├── requirements.txt            # Python dependencies
│   ├── env.example                 # Environment variables
│   ├── Dockerfile                  # Production Docker image
│   └── demos/                      # Individual demo implementations
├── ⚛️ frontend/                    # Next.js frontend
│   ├── src/
│   │   ├── app/                    # Next.js app directory
│   │   └── components/             # React components
│   ├── package.json                # Frontend dependencies
│   └── Dockerfile                  # Production Docker image
├── 🐳 docker-compose.yml           # Production Docker Compose
├── 🛠️ Makefile                     # Development commands
├── 📦 package.json                 # Root package.json
└── 📚 README.md                    # This file
```

## 📚 Learning Content

### 📓 **Week 1: LLMs, Prompts & RAG Systems**
**Core Concepts**: LLM architecture, tokenization, context windows, prompt engineering, RAG fundamentals
- `01_llm_fundamentals.ipynb` - LLM architecture and multi-provider setup
- `02_prompt_engineering.ipynb` - Advanced prompting techniques
- `03_rag_fundamentals.ipynb` - RAG system components and implementation
- `04_advanced_rag.ipynb` - Hybrid search, semantic chunking, optimization
- `05_streaming_llm_apps.ipynb` - Real-time LLM applications
- **Demos**: Bedtime Story Generator, Legal Analysis, Web Q&A, Support KB

### 🗣️ **Week 2: Conversational AI & Voice Systems**
**Core Concepts**: Voice AI, conversation memory, human-in-the-loop, domain-specific flows
- `01_conversational_ai_fundamentals.ipynb` - Chat vs voice systems
- `02_voice_ai_systems.ipynb` - Speech-to-text, text-to-speech, LiveKit
- `03_conversation_memory.ipynb` - Session persistence and summarization
- `04_human_in_loop.ipynb` - HITL patterns and escalation
- `05_domain_specific_flows.ipynb` - Medical, sales, and specialized flows
- **Demos**: Lead Qualifier, Restaurant Voice Assistant, Healthcare Triage

### 🤖 **Week 3: AI Agents & Workflows**
**Core Concepts**: Autonomous agents, tool calling, multi-agent coordination, workflow orchestration
- `01_ai_agents_fundamentals.ipynb` - Agent architectures and frameworks
- `02_tool_calling_integration.ipynb` - Function calling and tool integration
- `03_multi_agent_systems.ipynb` - Agent coordination and communication
- `04_workflow_orchestration.ipynb` - State machines and complex workflows
- `05_browser_automation.ipynb` - Web automation with Selenium/Playwright
- `06_recommendation_systems.ipynb` - Collaborative filtering and personalization
- **Demos**: Competitor Analysis, Form Filling, Legal Intake, Shopping Assistant

### 🚀 **Week 4: Production Optimization**
**Core Concepts**: Performance optimization, monitoring, deployment, cost management
- `01_production_fundamentals.ipynb` - Latency, throughput, cost models
- `02_rag_optimization.ipynb` - Hybrid search, reranking, caching
- `03_voice_system_optimization.ipynb` - Latency reduction, error handling
- `04_caching_strategies.ipynb` - Redis caching, performance optimization
- `05_monitoring_metrics.ipynb` - Observability, A/B testing, alerting
- `06_deployment_patterns.ipynb` - Docker, CI/CD, cloud deployment
- **Demos**: RAG Optimization, Voice Enhancement, Agent Scalability

### 🏗️ **Week 5: System Design & Architecture**
**Core Concepts**: Enterprise architecture, multi-agent coordination, multi-modal AI, ethics
- `01_enterprise_architecture.ipynb` - Microservices, event-driven systems
- `02_multi_agent_coordination.ipynb` - A2A communication, consensus algorithms
- `03_mcp_implementation.ipynb` - Model Context Protocol
- `04_multi_modal_ai.ipynb` - Vision integration, edge deployment
- `05_computer_vision_integration.ipynb` - Object detection, OCR
- `06_ai_ethics_compliance.ipynb` - Bias detection, GDPR/HIPAA compliance
- **Demos**: Enterprise Architecture, A2A Coordination, Vision & Ethics

### 🎓 **Week 6: Capstone Project & Demo Day**
**Core Concepts**: Integration, deployment, presentation, portfolio building
- `01_capstone_planning.ipynb` - Project selection and requirements
- `02_architecture_design.ipynb` - Production-ready system design
- `03_integration_patterns.ipynb` - Combining all components
- `04_deployment_strategies.ipynb` - Final deployment and testing
- `05_testing_optimization.ipynb` - Quality assurance and performance validation
- `06_documentation_presentation.ipynb` - Documentation and demo preparation
- **Demos**: Drive-Thru Agent, Personal Shopper, Financial Reports Analysis

## 🛠️ Development Guide

### 📓 **Notebook Development**

#### **Environment Setup**
```bash
# Complete setup (recommended)
make setup-notebooks

# Manual setup
make install-uv
make notebooks-env
make env-check-uv
```

#### **Working with Notebooks**
```bash
# Start Jupyter Lab
make notebooks-uv

# Clean outputs
make notebooks-clean-uv

# Convert to HTML
make notebooks-convert-uv

# Check syntax
make notebooks-check-uv
```

#### **LLM Provider Integration**
- **Multi-provider support**: OpenAI, Gemini, Fireworks AI
- **Unified interface**: `utils/llm_providers.py`
- **Error handling**: Automatic retries and rate limiting
- **Cost tracking**: Usage monitoring and optimization
- **Environment config**: Secure API key management

### 🔧 **API Development**

The FastAPI backend (`api/`) includes:
- **Demo implementations**: Individual folders for each demo
- **LLM integration**: Multi-provider support
- **Vector databases**: ChromaDB, Qdrant, FAISS
- **Streaming responses**: Real-time LLM outputs
- **Error handling**: Comprehensive error management

### ⚛️ **Frontend Development**

The Next.js frontend (`frontend/`) provides:
- **Interactive demos**: Real-time LLM interactions
- **Streaming UI**: Live response updates
- **Component library**: Reusable UI components
- **API integration**: Seamless backend communication

### 🐳 **Docker Development**

```bash
# Full stack development
make dev              # Start all services
make build            # Build images
make logs             # View logs
make clean            # Clean up
```

### 📦 **Adding New Content**

#### **New Notebook**
1. Create in appropriate week folder
2. Follow naming convention: `##_topic_name.ipynb`
3. Include learning objectives and prerequisites
4. Add to week README

#### **New Demo**
1. **API**: Create `api/demos/[demo-name]/`
2. **Frontend**: Create `frontend/src/app/demos/[demo-name]/`
3. **Integration**: Add routes and navigation
4. **Documentation**: Update README and docs

## 🔧 Configuration

### **Environment Setup**

#### **Notebook Environment**
```bash
# Copy environment template
cp notebooks/env.example notebooks/.env

# Edit with your API keys
nano notebooks/.env

# Verify configuration
make env-check-uv
```

#### **Required API Keys**
```bash
# LLM Providers (at least one required)
OPENAI_API_KEY=sk-your-openai-key-here
GEMINI_API_KEY=your-gemini-key-here
FIREWORKS_API_KEY=your-fireworks-key-here

# Optional: Additional services
ANTHROPIC_API_KEY=your-anthropic-key-here
ELEVENLABS_API_KEY=your-elevenlabs-key-here
LIVEKIT_API_KEY=your-livekit-key-here
```

#### **Vector Database Configuration**
```bash
# Qdrant (recommended)
QDRANT_URL=http://localhost:6333

# ChromaDB (local)
CHROMA_PERSIST_DIRECTORY=./chroma_db

# Pinecone (cloud)
PINECONE_API_KEY=your-pinecone-key-here
```

### **Development Configuration**

#### **API Configuration**
```bash
# API Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# CORS Settings
FRONTEND_URL=http://localhost:4020
```

#### **Frontend Configuration**
```bash
# Next.js Settings
NEXT_PUBLIC_API_URL=http://localhost:4010
NEXT_PUBLIC_WS_URL=ws://localhost:4010/ws
```

## 📚 Learning Resources

### **Course Materials**
- [AI Bootcamp Course](https://learnwithparam.com) - Full 6-week program
- [Course Syllabus](https://learnwithparam.com/ai-engineering-bootcamp) - Detailed curriculum
- [Live Sessions](https://learnwithparam.com) - Weekly live instruction

### **Technical Documentation**
- [FastAPI Documentation](https://fastapi.tiangolo.com/) - Backend development
- [Next.js Documentation](https://nextjs.org/docs) - Frontend development
- [Jupyter Lab Documentation](https://jupyterlab.readthedocs.io/) - Notebook development
- [OpenAI API Documentation](https://platform.openai.com/docs) - LLM integration
- [Google AI Studio](https://aistudio.google.com/) - Gemini API
- [Fireworks AI Documentation](https://readme.fireworks.ai/) - Fireworks API

### **AI Engineering Resources**
- [LangChain Documentation](https://python.langchain.com/) - LLM frameworks
- [CrewAI Documentation](https://docs.crewai.com/) - Multi-agent systems
- [LiveKit Documentation](https://docs.livekit.io/) - Real-time voice AI
- [ChromaDB Documentation](https://docs.trychroma.com/) - Vector databases
- [Qdrant Documentation](https://qdrant.tech/documentation/) - Vector search

## 🎯 Learning Path

### **Week 1: Foundation**
1. Start with `01_llm_fundamentals.ipynb`
2. Complete all core concept notebooks
3. Build demo applications
4. Test with multiple LLM providers

### **Week 2: Conversational AI**
1. Review Week 1 concepts
2. Focus on voice AI and memory systems
3. Implement HITL patterns
4. Build domain-specific flows

### **Week 3: AI Agents**
1. Master agent architectures
2. Implement tool calling
3. Build multi-agent systems
4. Create workflow orchestrations

### **Week 4: Production**
1. Optimize existing systems
2. Implement monitoring
3. Deploy to cloud
4. Measure performance

### **Week 5: Architecture**
1. Design enterprise systems
2. Implement A2A communication
3. Add multi-modal capabilities
4. Apply ethics frameworks

### **Week 6: Capstone**
1. Plan your project
2. Integrate all concepts
3. Deploy and test
4. Present your work

## 🤝 Contributing

This is a learning project for the AI Bootcamp course. Contributions are welcome!

### **How to Contribute**
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Test thoroughly: `make notebooks-test-uv`
5. Submit a pull request

### **Contribution Guidelines**
- Follow the existing code style
- Add comprehensive documentation
- Include tests for new features
- Update README files as needed

## 📄 License

**Access is restricted to enrolled participants only.**

## 👨‍💻 Instructor

**Param Harrison** - AI Engineering Instructor & Consultant
- [LinkedIn](https://www.linkedin.com/in/paramanantham/)
- [Twitter](https://x.com/learnwithparam)
- [Website](https://learnwithparam.com)
- [AI Bootcamp](https://learnwithparam.com/ai-engineering-bootcamp)

---

Built with ❤️ for the AI Bootcamp for Software Engineers course.
