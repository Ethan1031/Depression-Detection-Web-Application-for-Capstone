import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import os
from app.main import app

client = TestClient(app)

def test_api_root():
    """Test the API root endpoint"""
    response = client.get("/api")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "Welcome to Depression Detection API" in response.json()["message"]

def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_api_docs_endpoint():
    """Test that the API docs endpoint exists"""
    response = client.get("/api/docs")
    assert response.status_code == 200

def test_root_endpoint():
    """Test the root endpoint (serves frontend)"""
    # Mock os.path.exists to always return True for frontend/index.html
    with patch("os.path.exists") as mock_exists:
        mock_exists.return_value = True
        
        # Mock FileResponse to avoid actual file system access
        with patch("fastapi.responses.FileResponse") as mock_file_response:
            mock_file_response.return_value = {"mock": "response"}
            
            # Test the root endpoint
            response = client.get("/")
    
    # The endpoint should be called without an error
    assert response.status_code != 404

def test_serve_frontend():
    """Test serving frontend files for non-API routes"""
    # Mock os.path.exists to always return True for frontend/index.html
    with patch("os.path.exists") as mock_exists:
        mock_exists.return_value = True
        
        # Mock FileResponse to avoid actual file system access
        with patch("fastapi.responses.FileResponse") as mock_file_response:
            mock_file_response.return_value = {"mock": "response"}
            
            # Test a non-API route
            response = client.get("/dashboard")
    
    # The endpoint should be called without an error
    assert response.status_code != 404