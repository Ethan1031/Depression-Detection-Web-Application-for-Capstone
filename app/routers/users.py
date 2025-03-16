from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..database import get_db
from typing import List, Dict, Any

router = APIRouter()

@router.get("/me", response_model=schemas.UserOut)
def get_current_user_info(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@router.put("/me", response_model=schemas.UserOut)
def update_user(
    user_update: schemas.UserUpdate,  # Changed to UserUpdate schema
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Get the current user from database to ensure we have the latest data
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update email if provided and different
    if user_update.email and user_update.email != user.email:
        # Check if new email already exists
        user_exists = db.query(models.User).filter(models.User.email == user_update.email).first()
        if user_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        user.email = user_update.email
    
    # Update name if provided
    if user_update.name:
        user.name = user_update.name
    
    # Update phone_number if provided
    if user_update.phone_number:
        user.phone_number = user_update.phone_number
    
    # Update password if provided
    if user_update.password:
        user.hashed_password = auth.get_password_hash(user_update.password)
    
    # Commit changes
    db.commit()
    db.refresh(user)
    
    return user

@router.delete("/delete", response_model=Dict[str, Any])
def delete_user(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete the current user's account
    """
    # Get the user from database
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Delete user's assessments first to avoid foreign key constraint issues
    db.query(models.CombinedAssessment).filter(
        models.CombinedAssessment.user_id == user.id
    ).delete(synchronize_session=False)
    
    # Delete user's PHQ9 tests if the table exists
    db.query(models.PHQ9Test).filter(
        models.PHQ9Test.user_id == user.id
    ).delete(synchronize_session=False)
    
    # Delete the user
    db.query(models.User).filter(models.User.id == current_user.id).delete(synchronize_session=False)
    
    # Commit changes
    db.commit()
    
    return {"message": "User account deleted successfully"}