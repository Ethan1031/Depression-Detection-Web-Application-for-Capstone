import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.auth import get_current_user

client = TestClient(app)

def test_get_current_user_route_exists():
    """Test that the current user endpoint exists"""
    response = client.get("/api/users/me")
    # We expect an authorization error, but not a 404
    assert response.status_code != 404

def test_update_user_route_exists():
    """Test that the update user endpoint exists"""
    response = client.put("/api/users/me")
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

# Test getting current user info
def test_get_current_user_info():
    """Test getting the current user info"""
    # Override the dependency
    app.dependency_overrides[get_current_user] = lambda: get_mock_user()
    
    # Test getting current user info
    response = client.get("/api/users/me")
    
    # Check results
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
    assert response.json()["name"] == "Test User"
    
    # Reset dependency override
    app.dependency_overrides = {}

# # Test updating user
# @patch("app.routers.users.get_db")
# @patch("app.auth.get_password_hash")
# def test_update_user(mock_hash_password, mock_get_db):
#     """Test updating user information"""
#     # Create a mock user that can be modified
#     mock_user = get_mock_user()
    
#     # Override the dependency
#     app.dependency_overrides[get_current_user] = lambda: mock_user
    
#     # Create a mock session
#     mock_session = MagicMock()
    
#     # Setup the mock get_db to yield our mock session
#     mock_get_db.return_value = mock_session
    
#     # Mock the database query chain
#     mock_query = MagicMock()
#     mock_filter = MagicMock()
#     mock_filter.first.return_value = None  # No existing user with the new email
#     mock_query.filter.return_value = mock_filter
#     mock_session.query.return_value = mock_query
    
#     # Mock password hashing
#     mock_hash_password.return_value = "hashed_password"
    
#     # Mock db operations
#     mock_session.commit = MagicMock()
#     mock_session.refresh = MagicMock()
    
#     # Test data for update
#     update_data = {
#         "email": "new@example.com",
#         "name": "New Name",
#         "phone_number": "987-654-3210",
#         "password": "newpassword",
#         "ic_number": "987654321123",
#         "date_of_birth": "2000-01-01T00:00:00"
#     }
    
#     # Test updating user
#     response = client.put("/api/users/me", json=update_data)
    
#     # Check results
#     assert response.status_code == 200
#     assert response.json()["email"] == "new@example.com"
#     assert response.json()["name"] == "New Name"
    
#     # Reset dependency override
#     app.dependency_overrides = {}