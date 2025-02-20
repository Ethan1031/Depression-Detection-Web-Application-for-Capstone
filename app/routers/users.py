from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..database import get_db
from typing import List

router = APIRouter()

@router.get("/me", response_model=schemas.UserOut)
def get_current_user_info(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@router.put("/me", response_model=schemas.UserOut)
def update_user(
    user_update: schemas.UserCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Check if new email already exists
    if user_update.email != current_user.email:
        user_exists = db.query(models.User).filter(models.User.email == user_update.email).first()
        if user_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        current_user.email = user_update.email
    
    # Update password
    current_user.password = auth.get_password_hash(user_update.password)
    
    # Commit changes
    db.commit()
    db.refresh(current_user)
    
    return current_user