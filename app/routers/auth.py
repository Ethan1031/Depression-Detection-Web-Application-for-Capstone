from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .. import database, models, schemas, auth
from ..database import get_db

router = APIRouter()

@router.post("/login", response_model=schemas.Token)
async def login(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_credentials.email).first()
    if not user or not auth.verify_password(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/signup", response_model=schemas.UserOut)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if user exists by email
    existing_user_email = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if user exists by IC number
    existing_user_ic = db.query(models.User).filter(models.User.ic_number == user.ic_number).first()
    if existing_user_ic:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="IC number already registered"
        )
    
    # Create new user with all required fields
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(
        email=user.email,
        name=user.name,
        ic_number=user.ic_number,
        phone_number=user.phone_number,
        password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# Add a new endpoint to get user profile information
@router.get("/profile", response_model=schemas.UserProfile)
def get_user_profile(current_user: models.User = Depends(auth.get_current_user)):
    return {
        "name": current_user.name,
        "phone_number": current_user.phone_number,
        "email": current_user.email
    }