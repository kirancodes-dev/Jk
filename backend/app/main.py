import os
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import Base, engine, SessionLocal, get_db
from backend.app.services.seed_data import seed_database, ensure_sapthagiri_seeded

# Routers
from backend.app.routers import (
    auth, challenges, ai, universities, projects,
    students, faculty, industry, admin, notifications, demo,
    organizations, verification, impact
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables if not present
    Base.metadata.create_all(bind=engine)
    
    # Auto-seed realistic demo data on initial startup
    db = SessionLocal()
    try:
        seed_database(db)
        ensure_sapthagiri_seeded(db)
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

@app.middleware("http")
async def add_security_and_correlation_headers(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response

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
app.include_router(organizations.router, prefix=settings.API_V1_STR)
app.include_router(verification.router, prefix=settings.API_V1_STR)
app.include_router(impact.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(notifications.router, prefix=settings.API_V1_STR)
app.include_router(demo.router, prefix=settings.API_V1_STR)

from fastapi.responses import FileResponse

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "FastAPI Backend", "database": "Connected"}

@app.get("/live")
def liveness_check():
    return {"status": "alive"}

@app.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database not ready")

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

