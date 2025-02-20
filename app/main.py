from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .routers import auth, users, predictions, phq9
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["Predictions"])
app.include_router(phq9.router, prefix="/api/phq9", tags=["PHQ-9"])

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
                "predictions": "/api/predictions",
                "phq9": "/api/phq9"
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
