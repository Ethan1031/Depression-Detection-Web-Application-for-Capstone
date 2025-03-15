import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, mock_open
from app.main import app
import json
import os
from app.auth import get_current_user

client = TestClient(app)

def test_submit_phq9_route_exists():
    """Test that the PHQ-9 submission endpoint exists"""
    response = client.post("/api/assessment/submit-phq9")
    # We expect an authorization error, but not a 404
    assert response.status_code != 404

def test_submit_assessment_route_exists():
    """Test that the combined assessment submission endpoint exists"""
    response = client.post("/api/assessment/submit-assessment")
    # We expect an authorization error, but not a 404
    assert response.status_code != 404

def test_assessment_history_route_exists():
    """Test that the assessment history endpoint exists"""
    response = client.get("/api/assessment/assessment-history")
    # We expect an authorization error, but not a 404
    assert response.status_code != 404

def test_delete_assessment_route_exists():
    """Test that the delete assessment endpoint exists"""
    response = client.delete("/api/assessment/assessment/1")
    # We expect an authorization error, but not a 404
    assert response.status_code != 404

# Create a mock user for testing
def get_mock_user():
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.email = "test@example.com"
    mock_user.name = "Test User"
    mock_user.phone_number = "123-456-7890"
    mock_user.ic_number = "123456789"
    mock_user.is_active = True
    mock_user.created_at = "2023-01-01T00:00:00"
    return mock_user

# Test submitting PHQ-9 assessment
# @patch("app.routers.phq9_prediction.get_db")
# def test_submit_phq9(mock_get_db):
#     """Test submitting PHQ-9 assessment"""
#     # Override the dependency
#     app.dependency_overrides[get_current_user] = lambda: get_mock_user()
    
#     # Create a mock session
#     mock_session = MagicMock()
    
#     # Setup the mock get_db to yield our mock session
#     mock_get_db.return_value = mock_session
    
#     # Mock db operations
#     mock_session.add = MagicMock()
#     mock_session.commit = MagicMock()
    
#     # Mock refresh to set ID
#     def mock_refresh(obj):
#         obj.id = 1
#         obj.created_at = "2023-01-01T00:00:00"
    
#     mock_session.refresh = mock_refresh
    
#     # Test submitting PHQ-9
#     response = client.post(
#         "/api/assessment/submit-phq9",
#         json={
#             "answers": [1, 2, 1, 0, 1, 0, 2, 1, 0],
#             "total_score": 8,
#             "category": "Mild Depression"
#         }
#     )
    
#     # Check results
#     assert response.status_code == 200
#     assert response.json()["total_score"] == 8
#     assert response.json()["category"] == "Mild Depression"
#     assert response.json()["user_id"] == 1
    
#     # Reset dependency override
#     app.dependency_overrides = {}

# # Test getting assessment history
# @patch("app.routers.phq9_prediction.get_db")
# def test_get_assessment_history(mock_get_db):
#     """Test getting assessment history"""
#     # Override the dependency
#     app.dependency_overrides[get_current_user] = lambda: get_mock_user()
    
#     # Create a mock session
#     mock_session = MagicMock()
    
#     # Setup the mock get_db to yield our mock session
#     mock_get_db.return_value = mock_session
    
#     # Create a mock assessment
#     mock_assessment = MagicMock()
#     mock_assessment.id = 1
#     mock_assessment.user_id = 1
#     mock_assessment.created_at = "2023-01-01T00:00:00"
#     mock_assessment.phq9_score = 8
#     mock_assessment.phq9_category = "Mild Depression"
#     mock_assessment.phq9_answers = [1, 2, 1, 0, 1, 0, 2, 1, 0]
#     mock_assessment.prediction = "Healthy"
#     mock_assessment.confidence = 85.5
    
#     # Setup the query chain
#     mock_query = MagicMock()
#     mock_filter = MagicMock()
#     mock_order_by = MagicMock()
#     mock_limit = MagicMock()
    
#     mock_limit.all.return_value = [mock_assessment]
#     mock_order_by.limit.return_value = mock_limit
#     mock_filter.order_by.return_value = mock_order_by
#     mock_query.filter.return_value = mock_filter
#     mock_session.query.return_value = mock_query
    
#     # Test getting assessment history
#     response = client.get("/api/assessment/assessment-history")
    
#     # Check results
#     assert response.status_code == 200
#     assert len(response.json()) == 1
#     assert response.json()[0]["phq9_score"] == 8
#     assert response.json()[0]["prediction"] == "Healthy"
    
#     # Reset dependency override
#     app.dependency_overrides = {}

# # Test deleting assessment
# @patch("app.routers.phq9_prediction.get_db")
# def test_delete_assessment(mock_get_db):
#     """Test deleting an assessment"""
#     # Override the dependency
#     app.dependency_overrides[get_current_user] = lambda: get_mock_user()
    
#     # Create a mock session
#     mock_session = MagicMock()
    
#     # Setup the mock get_db to yield our mock session
#     mock_get_db.return_value = mock_session
    
#     # Create a mock assessment
#     mock_assessment = MagicMock()
#     mock_assessment.id = 1
#     mock_assessment.user_id = 1
    
#     # Setup the query chain
#     mock_query = MagicMock()
#     mock_filter = MagicMock()
    
#     mock_filter.first.return_value = mock_assessment
#     mock_filter.delete = MagicMock()
#     mock_query.filter.return_value = mock_filter
#     mock_session.query.return_value = mock_query
    
#     # Test deleting assessment
#     response = client.delete("/api/assessment/assessment/1")
    
#     # Check results
#     assert response.status_code == 200
#     assert response.json()["message"] == "Assessment deleted successfully"
    
#     # Reset dependency override
#     app.dependency_overrides = {}