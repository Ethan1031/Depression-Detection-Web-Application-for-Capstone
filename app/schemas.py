from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class PHQ9Submit(BaseModel):
    answers: List[int]

class PHQ9Response(BaseModel):
    id: int
    score: int
    category: str
    answers: List[int]
    created_at: datetime
    user_id: int

    class Config:
        from_attributes = True

class PHQ9History(BaseModel):
    tests: List[PHQ9Response]
    count: int

class PredictionCreate(BaseModel):
    prediction: str
    confidence: float
    segments_analyzed: int
    detailed_results: Dict

class PredictionResponse(BaseModel):
    id: int
    prediction: str
    confidence: float
    segments_analyzed: int
    detailed_results: Dict
    created_at: datetime

    class Config:
        from_attributes = True