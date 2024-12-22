from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import List
import time

from app.routes import (
    food_routes,
    social_routes,
    streak_routes,
    user_routes,
    auth_routes
)
from app.config import settings
from app.utils.appwrite_client import get_client
from app.utils.scheduler import init_scheduler
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize services, database connections, etc.
    client = get_client()
    logger.info("Starting up CalMate API...")
    
    # Initialize and start the scheduler
    scheduler = init_scheduler()
    # Store scheduler in app state
    app.state.scheduler = scheduler
    
    yield
    
    # Shutdown: Clean up resources
    logger.info("Shutting down CalMate API...")
    # Shut down scheduler gracefully
    if hasattr(app.state, "scheduler"):
        logger.info("Shutting down scheduler...")
        app.state.scheduler.shutdown()

app = FastAPI(
    title="CalMate API",
    description="AI-powered fitness tracking with social features",
    version="1.0.0",
    lifespan=lifespan
)

# Remove the @app.on_event("startup") since we're using lifespan context manager
# The scheduler is now initialized in the lifespan context manager

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Global error handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "path": request.url.path
        }
    )

# Include all routers
app.include_router(auth_routes.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(user_routes.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(food_routes.router, prefix="/api/v1/food", tags=["Food"])
app.include_router(social_routes.router, prefix="/api/v1/social", tags=["Social"])
app.include_router(streak_routes.router, prefix="/api/v1/streaks", tags=["Streaks"])

# Health check endpoint
@app.get("/health")
async def health_check():
    scheduler_status = "running" if hasattr(app.state, "scheduler") and app.state.scheduler.running else "stopped"
    return {
        "status": "healthy",
        "version": app.version,
        "environment": settings.ENVIRONMENT,
        "scheduler_status": scheduler_status
    }

# API documentation customization
app.docs_url = "/docs"  # Swagger UI
app.redoc_url = "/redoc"  # ReDoc

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False,
        log_level="info"
    )