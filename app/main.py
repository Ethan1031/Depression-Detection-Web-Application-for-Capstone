from fastapi import FastAPI, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
from .routers import auth, users, phq9_prediction
from .database import engine
from . import models

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Depression Detection API",
    description="API for depression detection using EEG data and PHQ-9 assessment",
    version="1.0.0",
    docs_url="/api/docs",   
    redoc_url="/api/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(phq9_prediction.router, prefix="/api/assessment", tags=["Combined Assessment"])

# Mount frontend static files only if the directory exists
static_dir = "frontend/static"
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
else:
    # Create the directory in development mode
    if os.environ.get("ENVIRONMENT") != "production":
        os.makedirs(static_dir, exist_ok=True)
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/api", tags=["Root"])
async def api_root():
    """
    API root endpoint returning API information
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Welcome to Depression Detection API",
            "documentation": "/api/docs",
            "alternative_documentation": "/api/redoc",
            "available_endpoints": {
                "authentication": "/api/auth",
                "users": "/api/users",
                "assessment": "/api/assessment"
            }
        }
    )

@app.get("/api/health", tags=["Health Check"])
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}

# Serve frontend for all non-API routes
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    # If the path already starts with /api, raise a 404 error
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    
    # For all other paths, serve the landing-page.html file from the frontend directory
    frontend_path = "frontend/landing-page.html"
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    else:
        raise HTTPException(status_code=404, detail="Frontend not found")

# Root endpoint to serve frontend landing-page.html
@app.get("/")
async def root():
    frontend_path = "frontend/landing-page.html"
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    else:
        # Fallback to API info if frontend is not available
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Welcome to Depression Detection API",
                "documentation": "/api/docs",
                "note": "Frontend files not found. Please place your frontend files in the 'frontend' directory."
            }
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)

# run by using uvicorn app.main:app --reload locally
# In production, the app will be run using the __main__ block
