# AI Bootcamp Demos - Development Makefile
.PHONY: help install dev build start stop clean logs api frontend notebooks mcp-install mcp-start mcp-test mcp-configure

# Default target
help: ## Show this help message
	@echo "AI Bootcamp Demos - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""

# Development commands
install: ## Install all dependencies (Python + Node.js + Notebooks)
	@echo "📦 Installing all dependencies..."
	@cd api && pip install -r requirements.txt
	@cd frontend && npm install
	@cd notebooks && uv venv .venv && uv pip install -r requirements.txt
	@echo "✅ All dependencies installed!"

install-uv: ## Install uv package manager
	@echo "📦 Installing uv package manager..."
	@curl -LsSf https://astral.sh/uv/install.sh | sh
	@echo "✅ uv installed! Please restart your shell or run 'source ~/.bashrc'"

install-notebooks-uv: ## Install notebook dependencies using uv
	@echo "📦 Installing notebook dependencies with uv..."
	@cd notebooks && uv venv .venv
	@cd notebooks && uv pip install -r requirements.txt
	@echo "✅ Notebook dependencies installed with uv!"

install-notebooks-venv: ## Install notebook dependencies using traditional venv
	@echo "📦 Installing notebook dependencies with venv..."
	@cd notebooks && python -m venv .venv
	@cd notebooks && source .venv/bin/activate && pip install -r requirements.txt
	@echo "✅ Notebook dependencies installed with venv!"

dev: ## Start development servers (API + Frontend)
	@echo "🚀 Starting development servers..."
	@docker compose up --build

dev-local: ## Start development servers locally (without Docker)
	@echo "🚀 Starting development servers locally..."
	@concurrently "cd api && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000" "cd frontend && npm run dev"

# Docker commands
build: ## Build Docker images
	@echo "🔨 Building Docker images..."
	@docker compose build

start: ## Start containers
	@echo "🚀 Starting containers..."
	@docker compose up -d

stop: ## Stop all containers
	@echo "🛑 Stopping all containers..."
	@docker compose down

restart: stop start ## Restart all containers

# Individual services
api: ## Start only API server
	@echo "🔧 Starting API server..."
	@cd api && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

frontend: ## Start only frontend server
	@echo "⚛️ Starting frontend server..."
	@cd frontend && npm run dev

# Notebook commands
notebooks: ## Start Jupyter Lab for notebooks
	@echo "📓 Starting Jupyter Lab..."
	@cd notebooks && jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root

notebooks-uv: ## Start Jupyter Lab with uv environment
	@echo "📓 Starting Jupyter Lab with uv..."
	@cd notebooks && uv run jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root

notebooks-venv: ## Start Jupyter Lab with venv environment
	@echo "📓 Starting Jupyter Lab with venv..."
	@cd notebooks && source .venv/bin/activate && jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root

notebooks-classic: ## Start Jupyter Notebook (classic interface)
	@echo "📓 Starting Jupyter Notebook..."
	@cd notebooks && jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root

notebooks-classic-uv: ## Start Jupyter Notebook with uv
	@echo "📓 Starting Jupyter Notebook with uv..."
	@cd notebooks && uv run jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root

notebooks-install: ## Install notebook dependencies only
	@echo "📦 Installing notebook dependencies..."
	@cd notebooks && pip install -r requirements.txt
	@echo "✅ Notebook dependencies installed!"

notebooks-clean: ## Clean notebook outputs and cache
	@echo "🧹 Cleaning notebook outputs..."
	@cd notebooks && find . -name "*.ipynb" -exec jupyter nbconvert --clear-output --inplace {} \;
	@echo "✅ Notebook outputs cleaned!"

notebooks-clean-uv: ## Clean notebook outputs with uv
	@echo "🧹 Cleaning notebook outputs with uv..."
	@cd notebooks && uv run jupyter nbconvert --clear-output --inplace **/*.ipynb
	@echo "✅ Notebook outputs cleaned!"

notebooks-convert: ## Convert notebooks to HTML for easy viewing
	@echo "📄 Converting notebooks to HTML..."
	@cd notebooks && find . -name "*.ipynb" -exec jupyter nbconvert --to html {} \;
	@echo "✅ Notebooks converted to HTML!"

notebooks-convert-uv: ## Convert notebooks to HTML with uv
	@echo "📄 Converting notebooks to HTML with uv..."
	@cd notebooks && uv run jupyter nbconvert --to html **/*.ipynb
	@echo "✅ Notebooks converted to HTML!"

notebooks-check: ## Check notebook syntax and dependencies
	@echo "🔍 Checking notebook syntax..."
	@cd notebooks && python -c "import nbformat; [nbformat.read(f, as_version=4) for f in __import__('glob').glob('**/*.ipynb', recursive=True)]"
	@echo "✅ All notebooks are valid!"

notebooks-check-uv: ## Check notebook syntax with uv
	@echo "🔍 Checking notebook syntax with uv..."
	@cd notebooks && uv run python -c "import nbformat; [nbformat.read(f, as_version=4) for f in __import__('glob').glob('**/*.ipynb', recursive=True)]"
	@echo "✅ All notebooks are valid!"

notebooks-test: ## Run basic tests on notebooks
	@echo "🧪 Testing notebook functionality..."
	@cd notebooks && python utils/test_notebooks.py
	@echo "✅ Notebook tests passed!"

notebooks-test-uv: ## Run basic tests on notebooks with uv
	@echo "🧪 Testing notebook functionality with uv..."
	@cd notebooks && uv run python utils/test_notebooks.py
	@echo "✅ Notebook tests passed!"

notebooks-env: ## Setup environment file for notebooks
	@echo "🔧 Setting up environment file..."
	@cd notebooks && cp env.example .env
	@echo "✅ Environment file created! Please edit .env with your API keys"

notebooks-env-check: ## Check environment configuration
	@echo "🔍 Checking environment configuration..."
	@cd notebooks && python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('OpenAI:', '✅' if os.getenv('OPENAI_API_KEY') else '❌'); print('Gemini:', '✅' if os.getenv('GEMINI_API_KEY') else '❌'); print('Fireworks:', '✅' if os.getenv('FIREWORKS_API_KEY') else '❌')"

notebooks-env-check-uv: ## Check environment configuration with uv
	@echo "🔍 Checking environment configuration with uv..."
	@cd notebooks && uv run python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('OpenAI:', '✅' if os.getenv('OPENAI_API_KEY') else '❌'); print('Gemini:', '✅' if os.getenv('GEMINI_API_KEY') else '❌'); print('Fireworks:', '✅' if os.getenv('FIREWORKS_API_KEY') else '❌')"

# Utility commands
logs: ## Show container logs
	@docker compose logs -f

logs-api: ## Show API logs
	@docker compose logs -f api

logs-frontend: ## Show frontend logs
	@docker compose logs -f frontend

clean: ## Clean up containers, images, and volumes
	@echo "🧹 Cleaning up..."
	@docker compose down -v --remove-orphans
	@docker system prune -f
	@echo "✅ Cleanup complete!"

# Database commands (for future use)
db-up: ## Start database (if needed)
	@echo "🗄️ Starting database..."
	@docker compose up -d db

db-down: ## Stop database
	@echo "🗄️ Stopping database..."
	@docker compose stop db

# Testing commands (for future use)
test: ## Run all tests
	@echo "🧪 Running tests..."
	@cd api && python -m pytest
	@cd frontend && npm test

test-api: ## Run API tests
	@echo "🧪 Running API tests..."
	@cd api && python -m pytest

test-frontend: ## Run frontend tests
	@echo "🧪 Running frontend tests..."
	@cd frontend && npm test

# Linting commands
lint: ## Run linting for all services
	@echo "🔍 Running linting..."
	@cd api && python -m flake8 .
	@cd frontend && npm run lint

lint-fix: ## Fix linting issues
	@echo "🔧 Fixing linting issues..."
	@cd frontend && npm run lint:fix

# MCP Server commands
mcp-install: ## Install MCP server for notebook functionality
	@echo "📦 Installing MCP server..."
	@cd cursor-notebook-mcp && uv venv .venv
	@cd cursor-notebook-mcp && uv pip install -e .
	@echo "✅ MCP server installed!"

mcp-start: ## Start MCP server for notebook functionality
	@echo "🚀 Starting MCP server..."
	@cd cursor-notebook-mcp && uv run cursor-notebook-mcp --allow-root /Users/param/learn/learnwithparam/ai-bootcamp/notebooks

mcp-test: ## Test MCP server functionality
	@echo "🧪 Testing MCP server..."
	@cd cursor-notebook-mcp && uv run cursor-notebook-mcp --help

mcp-configure: ## Configure Cursor MCP settings
	@echo "⚙️ Configuring Cursor MCP settings..."
	@echo "MCP server configured in ~/.cursor/mcp.json"
	@echo "Restart Cursor to activate the MCP server"

# Port management
ports: ## Show running services and ports
	@echo "🌐 Running services:"
	@echo "  API:      http://localhost:4010"
	@echo "  Frontend: http://localhost:4020"
	@echo "  Docs:     http://localhost:4010/docs"
	@echo "  Notebooks: http://localhost:8888"
	@echo "  MCP Server: Configured in Cursor"
	@echo ""
	@docker compose ps

# Quick setup for new developers
setup: install ## Complete setup for new developers
	@echo "🎉 Setup complete! Run 'make dev' to start development servers."
	@echo ""
	@echo "Available ports:"
	@echo "  API:      http://localhost:4010"
	@echo "  Frontend: http://localhost:4020"
	@echo "  Docs:     http://localhost:4010/docs"
	@echo "  Notebooks: http://localhost:8888"

setup-notebooks: install-notebooks-uv notebooks-env ## Complete notebook setup
	@echo "🎉 Notebook setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit notebooks/.env with your API keys"
	@echo "  2. Run 'make notebooks-uv' to start Jupyter Lab"
	@echo "  3. Open http://localhost:8888 in your browser"

setup-notebooks-venv: install-notebooks-venv notebooks-env ## Complete notebook setup with venv
	@echo "🎉 Notebook setup complete with venv!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit notebooks/.env with your API keys"
	@echo "  2. Run 'make notebooks-venv' to start Jupyter Lab"
	@echo "  3. Open http://localhost:8888 in your browser"

# Environment management
env-setup: notebooks-env ## Setup environment files
	@echo "🔧 Environment files created!"
	@echo "Please edit the following files with your API keys:"
	@echo "  - notebooks/.env"
	@echo "  - api/.env (if exists)"
	@echo "  - frontend/.env (if exists)"

env-check: notebooks-env-check ## Check environment configuration
	@echo "🔍 Environment check complete!"

env-check-uv: notebooks-env-check-uv ## Check environment configuration with uv
	@echo "🔍 Environment check complete with uv!"
