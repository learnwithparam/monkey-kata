# AI Bootcamp Demos - Cross-Platform Development Makefile
.PHONY: help install dev build start stop clean logs api frontend

# Default target
help: ## Show this help message
	@echo "AI Bootcamp Demos - Cross-Platform Available Commands:"
	@echo "Detected OS: $(OS)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""

# Development commands
install: ## Install all dependencies (Python + Node.js)
	@echo "📦 Installing all dependencies for $(OS)..."
	@cd api && $(PIP) install -r requirements.txt
	@cd frontend && npm install
	@echo "✅ All dependencies installed for $(OS)!"

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

# Port management
ports: ## Show running services and ports
	@echo "🌐 Running services:"
	@echo "  API:        http://localhost:4010"
	@echo "  Frontend:   http://localhost:4020"
	@echo "  Docs:       http://localhost:4010/docs"
	@echo "  Qdrant:     http://localhost:6333"
	@echo "  Redis:      redis://localhost:6379"
	@echo ""
	@docker compose ps

# Quick setup for new developers  
setup-dev: install ## Complete setup for new developers
	@echo "🎉 Setup complete! Run 'make dev' to start development servers."
	@echo ""
	@echo "Available ports:"
	@echo "  API:      http://localhost:4010"
	@echo "  Frontend: http://localhost:4020"
	@echo "  Docs:     http://localhost:4010/docs"

# Environment management
env-setup: ## Setup environment files
	@echo "🔧 Environment files created!"
	@echo "Please edit the following files with your API keys:"
	@echo "  - api/.env (if exists)"
	@echo "  - frontend/.env (if exists)"

env-check: ## Check environment configuration
	@echo "🔍 Environment check complete!"