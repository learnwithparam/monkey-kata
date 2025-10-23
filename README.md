# AI Bootcamp Demos

Production-ready API and frontend implementations for the AI Bootcamp for Software Engineers course. This repository contains interactive demos, API endpoints, and frontend applications showcasing real-world AI implementations.

## 🎯 Repository Overview

**Purpose**: API and Frontend demos for AI Bootcamp course  
**Instructor**: Param Harrison | **Next Cohort**: November 2025

### What's Included
- **API Server**: FastAPI backend with interactive demos
- **Frontend**: Next.js application with real-time AI interactions
- **Demos**: Production-ready implementations of AI systems
- **Infrastructure**: Docker, monitoring, and deployment configurations

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** (for API server)
- **Node.js 18+** (for frontend development)
- **Docker & Docker Compose** (recommended for full stack)
- **Git** (for version control)
- **API Keys** (OpenAI, Gemini, or Fireworks AI)

### 🐳 Full Stack Development (Docker)

1. **Clone and setup**
   ```bash
   git clone <repository-url>
   cd ai-bootcamp-demos
   ```

2. **Start all services**
   ```bash
   make dev
   ```

3. **Access applications**
   - **API Server**: http://localhost:4010
   - **Frontend**: http://localhost:4020  
   - **API Docs**: http://localhost:4010/docs

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

#### **Docker Commands**
```bash
make build              # Build Docker images
make start              # Start production containers
make stop               # Stop all containers
make restart            # Restart all containers
make logs               # Show container logs
make clean              # Clean up containers and images
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
ai-bootcamp-demos/
├── 🔧 api/                         # FastAPI backend
│   ├── main.py                     # Main FastAPI application
│   ├── requirements.txt           # Python dependencies
│   ├── env.example                 # Environment variables
│   ├── Dockerfile                  # Production Docker image
│   ├── demos/                      # Individual demo implementations
│   │   ├── bedtime_story_generator/ # Bedtime story generation demo
│   │   └── website_rag/            # Website RAG demo
│   └── utils/                      # Utility functions
│       ├── llm_provider.py         # Multi-provider LLM utilities
│       └── README.md               # API documentation
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

## 🔧 API Development

The FastAPI backend (`api/`) includes:

### **Demo Implementations**
- **Bedtime Story Generator**: Interactive story creation with AI
- **Website RAG**: Question-answering system for websites
- **Legal Analysis**: Document analysis and legal insights
- **Support KB**: Knowledge base search and retrieval

### **Features**
- **Multi-provider LLM support**: OpenAI, Gemini, Fireworks AI
- **Vector databases**: ChromaDB, Qdrant, FAISS integration
- **Streaming responses**: Real-time LLM outputs
- **Error handling**: Comprehensive error management
- **API documentation**: Auto-generated OpenAPI docs

### **API Endpoints**
- `GET /docs` - Interactive API documentation
- `POST /api/demos/bedtime-story` - Story generation
- `POST /api/demos/website-rag` - Website Q&A
- `POST /api/demos/legal-analysis` - Legal document analysis
- `POST /api/demos/support-kb` - Knowledge base search

## ⚛️ Frontend Development

The Next.js frontend (`frontend/`) provides:

### **Interactive Demos**
- **Real-time AI interactions**: Live response updates
- **Streaming UI**: Progressive response display
- **Component library**: Reusable UI components
- **API integration**: Seamless backend communication

### **Features**
- **Modern UI**: Clean, responsive design
- **Real-time updates**: WebSocket connections
- **Error handling**: User-friendly error messages
- **Loading states**: Smooth user experience

## 🐳 Docker Development

```bash
# Full stack development
make dev              # Start all services
make build            # Build images
make logs             # View logs
make clean            # Clean up
```

### **Services**
- **API Server**: FastAPI application (port 4010)
- **Frontend**: Next.js application (port 4020)
- **Qdrant**: Vector database (port 6333)
- **Redis**: Caching layer (port 6379)
- **Prometheus**: Monitoring (port 9090)

## 🔧 Configuration

### **Environment Setup**

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

## 📚 Learning Resources

### **Course Materials**
- [AI Bootcamp Course](https://learnwithparam.com) - Full 6-week program
- [Course Syllabus](https://learnwithparam.com/ai-engineering-bootcamp) - Detailed curriculum
- [Live Sessions](https://learnwithparam.com) - Weekly live instruction
- [Notebooks Repository](https://github.com/learnwithparam/ai-bootcamp-notebooks) - Interactive learning materials
- [Examples Repository](https://github.com/learnwithparam/ai-bootcamp-notebooks/tree/main/examples) - Additional examples and projects

### **Technical Documentation**
- [FastAPI Documentation](https://fastapi.tiangolo.com/) - Backend development
- [Next.js Documentation](https://nextjs.org/docs) - Frontend development
- [OpenAI API Documentation](https://platform.openai.com/docs) - LLM integration
- [Google AI Studio](https://aistudio.google.com/) - Gemini API
- [Fireworks AI Documentation](https://readme.fireworks.ai/) - Fireworks API

### **AI Engineering Resources**
- [LangChain Documentation](https://python.langchain.com/) - LLM frameworks
- [CrewAI Documentation](https://docs.crewai.com/) - Multi-agent systems
- [LiveKit Documentation](https://docs.livekit.io/) - Real-time voice AI
- [ChromaDB Documentation](https://docs.trychroma.com/) - Vector databases
- [Qdrant Documentation](https://qdrant.tech/documentation/) - Vector search

## 🎯 Development Guide

### **Adding New Demos**

#### **API Demo**
1. Create `api/demos/[demo-name]/`
2. Implement FastAPI routes
3. Add to main application
4. Update documentation

#### **Frontend Demo**
1. Create `frontend/src/app/demos/[demo-name]/`
2. Add React components
3. Integrate with API
4. Add navigation

#### **Full Stack Demo**
1. Implement both API and frontend
2. Add Docker configuration
3. Update documentation
4. Test end-to-end

## 🤝 Contributing

This is a learning project for the AI Bootcamp course. Contributions are welcome!

### **How to Contribute**
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Test thoroughly: `make test`
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