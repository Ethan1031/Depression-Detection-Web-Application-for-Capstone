from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    ic_number = Column(String, nullable=False, unique=True)
    phone_number = Column(String, nullable=False)
    password = Column(String, nullable=False)
    is_active = Column(Boolean, server_default='TRUE', nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    
    phq9_tests = relationship("PHQ9Test", back_populates="user")
    combined_assessments = relationship("CombinedAssessment", back_populates="user")

class PHQ9Test(Base):
    __tablename__ = "phq9_tests"
    
    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    
    # Store the answers to the 9 questions
    answers = Column(JSON, nullable=False)
    
    # Store the total score
    total_score = Column(Integer, nullable=False)
    
    # Store the depression severity category
    category = Column(String, nullable=False)
    
    # Relationship back to user
    user = relationship("User", back_populates="phq9_tests")

class CombinedAssessment(Base):
    __tablename__ = "combined_assessments"

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    
    # PHQ-9 related fields
    phq9_answers = Column(JSON, nullable=False)
    phq9_score = Column(Integer, nullable=False)
    phq9_category = Column(String, nullable=False)
    
    # EEG prediction related fields
    prediction = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    segments_analyzed = Column(Integer, nullable=False)
    detailed_results = Column(JSON)
    
    user = relationship("User", back_populates="combined_assessments")