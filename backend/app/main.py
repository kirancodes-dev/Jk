import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.core.config import settings
from backend.app.core.database import Base, engine, SessionLocal
from backend.app.services.seed_data import seed_database

# Routers
from backend.app.routers import (
    auth, challenges, ai, universities, projects,
    students, faculty, industry, admin, notifications, demo
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables if not present
    Base.metadata.create_all(bind=engine)
    
    # Auto-seed realistic demo data on initial startup
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
        
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "demo"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "challenges"), exist_ok=True)
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Smart India Hackathon (SIH 2026) Problem Statement 26043 — A digital platform to crowdsource societal challenges and facilitate collaborative problem solving through universities and industry partnerships. Government of Jharkhand, Department of Higher & Technical Education.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount local uploaded files
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(challenges.router, prefix=settings.API_V1_STR)
app.include_router(ai.router, prefix=settings.API_V1_STR)
app.include_router(universities.router, prefix=settings.API_V1_STR)
app.include_router(projects.router, prefix=settings.API_V1_STR)
app.include_router(students.router, prefix=settings.API_V1_STR)
app.include_router(faculty.router, prefix=settings.API_V1_STR)
app.include_router(industry.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(notifications.router, prefix=settings.API_V1_STR)
app.include_router(demo.router, prefix=settings.API_V1_STR)

from fastapi.responses import FileResponse

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "FastAPI Backend", "database": "Connected"}

@app.get("/api-info")
def api_info():
    return {
        "platform": settings.PROJECT_NAME,
        "organization": settings.ORGANIZATION,
        "theme": "Smart Education & Societal Problem Solving",
        "api_documentation": "/docs",
        "health": "/health",
        "demo_accounts": f"{settings.API_V1_STR}/demo/accounts"
    }

# Mount Flutter Web App assets and SPA fallback
frontend_web_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend", "build", "web")
if os.path.exists(frontend_web_dir):
    for sub in ["assets", "canvaskit", "icons"]:
        subdir = os.path.join(frontend_web_dir, sub)
        if os.path.exists(subdir):
            app.mount(f"/{sub}", StaticFiles(directory=subdir), name=sub)

    @app.get("/")
    async def serve_spa():
        return FileResponse(os.path.join(frontend_web_dir, "index.html"))

    @app.get("/{filename:path}")
    async def serve_static_or_spa(filename: str):
        # Don't intercept docs or openapi
        if filename in ["docs", "redoc", "openapi.json"]:
            return None
        file_path = os.path.join(frontend_web_dir, filename)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_web_dir, "index.html"))

