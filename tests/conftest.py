import pytest
import sys
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Create necessary directories for tests
os.makedirs("frontend/static", exist_ok=True)
if not os.path.exists("frontend/landing-page.html"):
    with open("frontend/landing-page.html", "w") as f:
        f.write("<html><body>Test Frontend</body></html>")

# Now import your app modules
from app.database import Base, get_db
from app.main import app
from app.auth import get_current_user

# Use SQLite for testing (in-memory database)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

# Add SQLite-specific functions to handle things like DEFAULT now()
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    # Add functions that SQLite doesn't natively support but our models might use
    cursor.execute("CREATE FUNCTION IF NOT EXISTS now() RETURNS TIMESTAMP AS 'SELECT CURRENT_TIMESTAMP'")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def mock_user():
    """Create a mock user for testing"""
    user = MagicMock()
    user.id = 1
    user.email = "test@example.com"
    user.name = "Test User"
    user.phone_number = "123-456-7890"
    user.ic_number = "123456789123"
    user.password = "hashed_password"
    user.is_active = True
    user.created_at = "2023-01-01T00:00:00"
    user.date_of_birth = "2000-01-01T00:00:00"
    return user

@pytest.fixture(scope="function")
def test_client():
    """Create a test client with mocked dependencies"""
    # Create a test client
    client = TestClient(app)
    return client

@pytest.fixture(scope="function")
def authenticated_client(test_client, mock_user):
    """Create a client with mocked authentication"""
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield test_client
    app.dependency_overrides = {}

@pytest.fixture(scope="function")
def test_db():
    """Create an in-memory test database"""
    # Create tables
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Error creating tables: {e}")
        raise
        
    # Create a testing session
    session = TestingSessionLocal()
    
    # Override the get_db dependency
    app.dependency_overrides[get_db] = lambda: session
    
    yield session
    
    # Clean up
    session.close()
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides = {}

@pytest.fixture(scope="function")
def client(test_db, test_client):
    """Client with database session"""
    return test_client

@pytest.fixture
def env_vars():
    """Set environment variables needed for testing"""
    os.environ["SECRET_KEY"] = "testsecretkey"
    os.environ["ALGORITHM"] = "HS256"
    os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
    yield