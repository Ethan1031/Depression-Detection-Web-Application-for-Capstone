from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .routers import auth, users, phq9_prediction
from .database import engine
from . import models

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Depression Detection API",
    description="API for depression detection using EEG data and PHQ-9 assessment",
    version="1.0.0",
    docs_url="/docs",   
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(phq9_prediction.router, prefix="/api/assessment", tags=["Combined Assessment"])

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint returning API information
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Welcome to Depression Detection API",
            "documentation": "/docs",
            "alternative_documentation": "/redoc",
            "available_endpoints": {
                "authentication": "/api/auth",
                "users": "/api/users",
                "assessment": "/api/assessment"
            }
        }
    )

@app.get("/health", tags=["Health Check"])
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}

# run by using uvicorn app.main:app --reload
