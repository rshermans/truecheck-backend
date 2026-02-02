from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from routes.analysis import router as analysis_router
from routes.history import router as history_router
from routes.stats import router as stats_router
from routes.auth import router as auth_router
from routes.admin import router as admin_router
from routes.community import router as community_router
from routes.upload import router as upload_router
from routes.news import router as news_router
from routes.professor import router as professor_router
from routes.student import router as student_router
from routes.gamification import router as gamification_router
from routes.config import router as config_router
from database import create_db_and_tables

# Create FastAPI application
app = FastAPI(
    title="TrueCheck API",
    description="API for fact-checking and content verification",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth_router)
app.include_router(analysis_router)
app.include_router(upload_router)
app.include_router(admin_router)
app.include_router(history_router)
app.include_router(gamification_router)
app.include_router(stats_router)
app.include_router(config_router)
app.include_router(professor_router)
app.include_router(student_router)
app.include_router(news_router)
app.include_router(community_router)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "TrueCheck API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
