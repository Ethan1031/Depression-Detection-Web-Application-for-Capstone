from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    name: str
    phone_number: str
    
class UserCreate(UserBase):
    password: str
    ic_number: str
    date_of_birth: datetime = datetime.now()  # Add default value

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserProfile(BaseModel):
    name: str
    phone_number: str
    email: EmailStr

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: EmailStr
    name: str
    phone_number: str

class UserCreate(UserBase):
    password: str
    ic_number: str
    date_of_birth: datetime

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserProfile(BaseModel):
    name: str
    phone_number: str
    email: EmailStr

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

class CombinedAssessmentSubmit(BaseModel):
    phq9_answers: List[int]

class CombinedAssessmentResponse(BaseModel):
    id: int
    created_at: datetime
    phq9_score: int
    phq9_category: str
    phq9_answers: List[int]
    prediction: str
    confidence: float
    segments_analyzed: int
    detailed_results: Dict
    user_id: int

    class Config:
        from_attributes = True

class PHQ9Create(BaseModel):
    answers: List[int]
    total_score: int
    category: str

class PHQ9Response(BaseModel):
    id: int
    user_id: int
    answers: List[int]
    total_score: int
    category: str
    created_at: datetime

    class Config:
        orm_mode = True