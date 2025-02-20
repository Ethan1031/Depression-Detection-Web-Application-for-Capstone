from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    is_active = Column(Boolean, server_default='TRUE', nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    
    predictions = relationship("Prediction", back_populates="user")
    phq9_tests = relationship("PHQ9Test", back_populates="user")

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    prediction = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    segments_analyzed = Column(Integer, nullable=False)
    detailed_results = Column(JSON)
    
    user = relationship("User", back_populates="predictions")

class PHQ9Test(Base):
    __tablename__ = "phq9_tests"

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    answers = Column(JSON, nullable=False)
    score = Column(Integer, nullable=False)
    category = Column(String, nullable=False)
    
    user = relationship("User", back_populates="phq9_tests")