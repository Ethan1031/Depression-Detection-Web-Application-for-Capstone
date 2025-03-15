import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.auth import get_current_user
import app.auth as auth_module

client = TestClient(app)

def test_login_route_exists():
    """Test that the login route exists"""
    response = client.post("/api/auth/login")
    # Even though authentication will fail, the route should exist (not 404)
    assert response.status_code != 404

def test_signup_route_exists():
    """Test that the signup route exists"""
    response = client.post("/api/auth/signup")
    # Even though it will fail due to missing data, the route should exist (not 404)
    assert response.status_code != 404

def test_profile_route_exists():
    """Test that the profile route exists"""
    response = client.get("/api/auth/profile")
    # We expect an authentication error, but not a 404
    assert response.status_code != 404

# Create a mock user for testing
def get_mock_user():
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.email = "test@example.com"
    mock_user.name = "Test User"
    mock_user.phone_number = "123-456-7890"
    mock_user.ic_number = "111122223344"
    mock_user.is_active = True
    mock_user.created_at = "2023-01-01T00:00:00"
    return mock_user

# @patch("app.routers.auth.get_db")
# @patch("app.auth.get_password_hash")
# def test_signup(mock_password_hash, mock_get_db):
#     """Test user signup"""
#     # Create a mock session
#     mock_session = MagicMock()
    
#     # Setup the mock get_db to work as a context manager
#     mock_context = MagicMock()
#     mock_context.__enter__.return_value = mock_session
#     mock_get_db.return_value = mock_context
    
#     # Mock the database query chain
#     mock_query = MagicMock()
#     mock_filter = MagicMock()
#     mock_filter.first.return_value = None  # No existing user
#     mock_query.filter.return_value = mock_filter
#     mock_session.query.return_value = mock_query
    
#     # Mock password hashing
#     mock_password_hash.return_value = "hashed_password"
    
#     # Mock db operations
#     mock_session.add = MagicMock()
#     mock_session.commit = MagicMock()
    
#     # Mock refresh to set ID and other properties
#     def mock_refresh(user_obj):
#         user_obj.id = 1
#         user_obj.created_at = "2023-01-01T00:00:00"
#         user_obj.is_active = True
    
#     mock_session.refresh = mock_refresh
    
#     # Test signup with updated data (without date_of_birth)
#     response = client.post(
#         "/api/auth/signup",
#         json={
#             "email": "new@gmail.com",
#             "name": "Darren",
#             "ic_number": "031031130555",
#             "phone_number": "012-444-5555",
#             "password": "a111111a#"
#         }
#     )
    
#     # Check results
#     assert response.status_code == 200
#     assert "email" in response.json()
#     assert response.json()["email"] == "new@gmail.com"

# Test getting profile
def test_get_profile():
    """Test getting user profile"""
    # Override the dependency
    app.dependency_overrides[get_current_user] = lambda: get_mock_user()
    
    # Test getting profile
    response = client.get("/api/auth/profile")
    
    # Check results
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
    assert response.json()["name"] == "Test User"
    
    # Reset dependency override
    app.dependency_overrides = {}