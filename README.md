# AI Bootcamp

![AI Bootcamp Open Graph preview](https://www.learnwithparam.com/ai-bootcamp/opengraph-image)

Hands-on AI engineering demos, bootcamp-ready workshop material, and production-style examples for learners who want to build real apps with modern AI tools.

> Regional pricing is available for eligible learners, with discounts of up to 60% in supported regions. Start here: https://www.learnwithparam.com/ai-bootcamp

### What is inside
- **API Server**: FastAPI backend with interactive demos
- **Frontend**: Next.js application with real-time AI interactions
- **Demos**: Production-ready implementations of AI systems
- **Infrastructure**: Docker, monitoring, and deployment configurations
- **Learning Path**: Search-friendly project structure, clear docs, and copy that helps people discover the bootcamp from GitHub

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
   cd <repository-name>
   ```
1a. **.env files on Frontend and API**
   ```bash
   cp api/.env.example api/.env
   cp frontend/.env.example frontend/.env
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
make build              # Build Docker images with BuildKit cache
make build-no-cache     # Build Docker images without cache (fresh build)
make start              # Start production containers
make stop               # Stop all containers
make restart            # Restart all containers
make logs               # Show container logs
make clean              # Clean up containers and images
make clean-cache        # Clean BuildKit cache (pip/npm caches)
make clean-all          # Clean everything including BuildKit cache
make dev-no-build       # Start services without rebuilding (use existing images)
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
monkey-kata/
├── 🔧 api/                         # FastAPI backend
│   ├── main.py                     # Main FastAPI application
│   ├── requirements.txt              # Python dependencies
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

## 🐳 Docker Development

### **Optimized Build System**

The Docker setup uses **BuildKit cache mounts** for optimal development experience:

- **pip cache**: Python packages are cached between builds (only installs once)
- **npm cache**: Node.js packages are cached between builds (only installs once)
- **Layer caching**: Docker layers are cached intelligently
- **Fast rebuilds**: Only code changes trigger rebuilds, dependencies reuse cache

**First build** will take time to download dependencies. **Subsequent builds** will be much faster!

```bash
# Full stack development
make dev              # Start all services with optimized BuildKit caching
make build            # Build images with cache
make dev-no-build     # Start without rebuilding (use existing images)
make logs             # View logs
make clean-cache      # Clean BuildKit cache if needed
make clean-all        # Complete cleanup
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

#### **Browser Setup (for Amazon Product Shopping Demo)**
The Amazon Product Shopping demo requires a browser with Chrome DevTools Protocol (CDP) enabled:

```bash
# Start Chrome with CDP enabled (macOS/Linux)
google-chrome --remote-debugging-port=9222

# Or on macOS with Chrome installed via Homebrew
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222

# Or set environment variable
export BROWSER_CDP_URL=http://localhost:9222
```

**Note:** Keep the browser window open while using the demo. The AI agent will control this browser instance.

#### **Vector Database Configuration**
```bash
# Qdrant (recommended)
QDRANT_URL=http://localhost:6333

# ChromaDB (local)
CHROMA_PERSIST_DIRECTORY=./chroma_db

# Pinecone (cloud)
PINECONE_API_KEY=your-pinecone-key-here
```
## 📄 License

**Access is restricted to enrolled participants only.**

## 👨‍💻 Instructor

**Param Harrison** - AI Engineering Instructor & Consultant
- [LinkedIn](https://www.linkedin.com/in/paramanantham/)
- [Twitter](https://x.com/learnwithparam)
- [Website](https://learnwithparam.com)
- [AI Engineering](https://learnwithparam.com/ai-engineering)

---

Built with ❤️ for the [learnwithparam.com](https://learnwithparam.com) community.
