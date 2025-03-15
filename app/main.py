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

# API endpoints
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

# Mount static files - do this separately for each type
# Mount CSS files
app.mount("/styles.css", StaticFiles(directory="frontend"), name="css")

# Mount JavaScript files
app.mount("/auth-check.js", StaticFiles(directory="frontend"), name="js")

# Mount images directory
if os.path.exists(os.path.join("frontend", "images")):
    app.mount("/images", StaticFiles(directory="frontend/images"), name="images")

# Mount specific HTML files
app.mount("/profile-settings.html", StaticFiles(directory="frontend"), name="profile_settings")
app.mount("/contact-us.html", StaticFiles(directory="frontend"), name="contact_us")

# Root endpoint to serve frontend landing-page.html
@app.get("/")
async def root():
    # Try to find the landing page
    frontend_path = "frontend/landing-page.html"
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    else:
        # Fallback if the file isn't found
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Welcome to Depression Detection API",
                "documentation": "/api/docs",
                "note": "Frontend files not found."
            }
        )

# Catch-all route for other pages
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    # Skip API routes
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    
    # Try to serve the specific file
    file_path = os.path.join("frontend", full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # Default to landing page for SPA-style navigation
    landing_page = "frontend/landing-page.html"
    if os.path.exists(landing_page):
        return FileResponse(landing_page)
    else:
        raise HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)

# run by using uvicorn app.main:app --reload locally
# In production, the app will be run using the __main__ block
