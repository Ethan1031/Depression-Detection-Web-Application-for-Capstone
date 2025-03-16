from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for DATABASE_URL environment variable (Heroku provides this)
DATABASE_URL = os.environ.get("DATABASE_URL")

# If DATABASE_URL exists and starts with "postgres://", update it to "postgresql://"
# This is required because SQLAlchemy 1.4.x+ requires "postgresql://" instead of "postgres://"
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    logger.info("Updated DATABASE_URL from postgres:// to postgresql://")

# If we have DATABASE_URL, use it, otherwise use the individual connection parameters
if DATABASE_URL:
    logger.info("Using DATABASE_URL from environment")
    SQLALCHEMY_DATABASE_URL = DATABASE_URL
else:
    logger.info("Using individual database connection parameters")
    SQLALCHEMY_DATABASE_URL = f'postgresql://{settings.DATABASE_USERNAME}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOSTNAME}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}'

logger.info(f"Connecting to database...")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()