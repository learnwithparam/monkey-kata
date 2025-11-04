from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
import glob
from pathlib import Path

# Import demo routers
from demos.bedtime_story_generator.main import router as bedtime_story_router
from demos.website_rag.main import router as website_rag_router
from demos.document_qa_chatbot.main import router as document_qa_chatbot_router
from demos.cv_analyzer.main import router as cv_analyzer_router
from demos.restaurant_booking.main import router as restaurant_booking_router

# Load environment variables
load_dotenv()

# Global app state
app_state = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 AI Bootcamp API starting up...")
    app_state["started"] = True
    app_state["demos"] = ["bedtime-story-generator", "website-rag", "document-qa-chatbot", "cv-analyzer", "restaurant-booking"]
    yield
    # Shutdown
    print("🛑 AI Bootcamp API shutting down...")

# Create FastAPI app
app = FastAPI(
    title="AI Bootcamp Demo API",
    description="API for AI Bootcamp demos and examples",
    version="1.0.0",
    lifespan=lifespan
)

# Include demo routers
app.include_router(bedtime_story_router)
app.include_router(website_rag_router)
app.include_router(document_qa_chatbot_router)
app.include_router(cv_analyzer_router)
app.include_router(restaurant_booking_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:4020", 
        "http://127.0.0.1:4020"
    ],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/")
async def root():
    return {"message": "AI Bootcamp Demo API is running!", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "app_state": app_state,
        "timestamp": "2025-01-27T00:00:00Z",
        "version": "1.0.0"
    }

@app.get("/challenges/{demo_name}")
async def get_challenge(demo_name: str):
    """Get README content for a specific demo"""
    try:
        # Get the base directory (parent of api directory)
        base_dir = Path(__file__).parent
        readme_path = base_dir / "demos" / demo_name / "README.md"
        
        if not readme_path.exists():
            raise HTTPException(status_code=404, detail=f"Challenge not found for demo: {demo_name}")
        
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "demo_name": demo_name,
            "content": content
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading challenge: {str(e)}")

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found", "detail": str(exc)}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": "Something went wrong"}
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
