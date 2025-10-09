# AI Bootcamp Demos

Interactive demos and examples from the **AI Bootcamp for Software Engineers** course by [learnwithparam](https://learnwithparam.com).

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** (recommended)
- **Node.js 18+** (for local development)
- **Python 3.8+** (for local development)
- **Git**

### 🐳 Docker Development (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-bootcamp
   ```

2. **Start development servers**
   ```bash
   make dev
   # or
   npm run dev
   ```

3. **Access the applications**
   - **API Server**: http://localhost:4010
   - **Frontend**: http://localhost:4020
   - **API Docs**: http://localhost:4010/docs

### 💻 Local Development

1. **Install all dependencies**
   ```bash
   make install
   # or
   npm run install:all
   ```

2. **Start development servers locally**
   ```bash
   make dev-local
   # or
   npm run dev:local
   ```

### 🛠️ Available Commands

```bash
# Development
make dev          # Start with Docker (recommended)
make dev-local    # Start locally without Docker
make install      # Install all dependencies

# Docker commands
make build        # Build Docker images
make start        # Start production containers
make stop         # Stop all containers
make restart      # Restart all containers
make logs         # Show container logs
make clean        # Clean up containers and images

# Individual services
make api          # Start only API server
make frontend     # Start only frontend server

# Utility
make ports        # Show running services and ports
make help         # Show all available commands
```

## 📁 Project Structure

```
ai-bootcamp/
├── api/                           # FastAPI backend
│   ├── main.py                   # Main FastAPI application
│   ├── requirements.txt          # Python dependencies
│   ├── env.example              # Environment variables template
│   ├── Dockerfile               # Production Docker image
│   ├── Dockerfile.dev           # Development Docker image
│   ├── .dockerignore            # Docker ignore file
│   └── demos/                   # Individual demo implementations
├── frontend/                     # Next.js frontend
│   ├── src/
│   │   ├── app/                 # Next.js app directory
│   │   └── components/          # React components
│   ├── package.json             # Frontend dependencies
│   ├── Dockerfile               # Production Docker image
│   ├── Dockerfile.dev           # Development Docker image
│   └── .dockerignore            # Docker ignore file
├── docker-compose.yml            # Production Docker Compose
├── docker-compose.dev.yml        # Development Docker Compose
├── Makefile                      # Development commands
├── package.json                  # Root package.json with workspace scripts
├── env.example                   # Environment variables template
├── .dockerignore                 # Root Docker ignore file
└── README.md
```

## 🎯 Available Demos

### Week 1: AI Foundation
- **Bedtime Story Generator** - Interactive story creation with streaming responses
- **Legal Document Analysis** - Extract key terms and risks from contracts
- **Web Page Q&A System** - Basic Q&A system for webpage content
- **Customer Support Knowledge Base** - 24/7 Q&A system with vector search

### Week 2: Conversational Systems
- **Lead Qualifier Chat Bot** - Qualify sales leads automatically
- **Restaurant Ordering Voice Assistant** - Voice system for food orders
- **Healthcare Triage Assistant** - Voice system for patient intake

### Week 3: AI Agents & Workflows
- **Competitor Analysis Research Agent** - Research competitors and analyze positioning
- **Web Form Filling AI Bot** - Navigate websites and fill forms automatically
- **Legal Case Intake Workflow** - Client intake with human lawyer review
- **Personal Shopping Assistant** - AI agent for product recommendations

### Week 4: Production Optimization
- **Customer Support RAG Optimization** - Optimize RAG systems for production
- **Voice Agent Performance Enhancement** - Optimize voice systems
- **Agent System Scalability** - Scale agent systems for production

### Week 5: Advanced Architecture
- **Enterprise AI Architecture Patterns** - Microservices and event-driven architecture
- **Agent-to-Agent Communication** - MCP and inter-agent protocols
- **Multi-Agent Coordination** - Communication protocols and conflict resolution
- **Computer Vision & Multi-Modal AI** - Vision processing and edge deployment
- **AI Ethics, Safety & Compliance** - Bias detection and regulatory compliance

### Week 6: Capstone Projects
- **Drive-Thru Voice Agent** - Automate fast-food ordering
- **IVR Agent** - Handle inbound support calls
- **Medical Office Triage Assistant** - Automate patient intake
- **Personal Shopper Agent** - E-commerce assistant
- **Vision AI Agent for Financial Reports** - Multimodal assistant

## 🛠️ Development

### API Development

The FastAPI backend is located in the `api/` directory. Each demo will have its own folder with:

- `main.py` - Demo-specific FastAPI routes
- `models.py` - Pydantic models for request/response
- `utils.py` - Helper functions and utilities

### Frontend Development

The Next.js frontend is in the `frontend/` directory. Each demo will have:

- A dedicated page in `src/app/demos/[demo-name]/`
- Reusable components in `src/components/`
- API integration utilities in `src/lib/`

### Adding a New Demo

1. **Create API folder**: `api/demos/[demo-name]/`
2. **Create frontend page**: `frontend/src/app/demos/[demo-name]/page.tsx`
3. **Add API routes**: Import and include in `api/main.py`
4. **Update navigation**: Add demo to the main page

## 🔧 Configuration

### Environment Variables

Copy `api/env.example` to `api/.env` and configure:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# CORS Settings
FRONTEND_URL=http://localhost:3000

# Add your API keys here as needed
# OPENAI_API_KEY=your_openai_key_here
# ANTHROPIC_API_KEY=your_anthropic_key_here
# GOOGLE_API_KEY=your_google_key_here
```

## 📚 Learning Resources

- [AI Bootcamp Course](https://learnwithparam.com) - Full 6-week program
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)

## 🤝 Contributing

This is a learning project for the AI Bootcamp course. Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 👨‍💻 Instructor

**Param Harrison** - AI Engineering Instructor & Consultant
- [LinkedIn](https://www.linkedin.com/in/paramanantham/)
- [Twitter](https://x.com/learnwithparam)
- [Website](https://learnwithparam.com)

---

Built with ❤️ for the AI Bootcamp for Software Engineers course.
