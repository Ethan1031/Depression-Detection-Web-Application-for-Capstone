from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..database import get_db
from typing import List

router = APIRouter()

@router.post("/submit", response_model=schemas.PHQ9Response)
def submit_phq9(
    test: schemas.PHQ9Submit,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    if len(test.answers) != 9 or not all(0 <= answer <= 3 for answer in test.answers):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PHQ-9 answers. Must provide 9 answers, each between 0 and 3"
        )
    
    score = sum(test.answers)
    category = "Minimal Depression"
    if score >= 20:
        category = "Severe Depression"
    elif score >= 15:
        category = "Moderately Severe Depression"
    elif score >= 10:
        category = "Moderate Depression"
    elif score >= 5:
        category = "Mild Depression"
    
    phq9_test = models.PHQ9Test(
        user_id=current_user.id,
        answers=test.answers,
        score=score,
        category=category
    )
    
    db.add(phq9_test)
    db.commit()
    db.refresh(phq9_test)
    return phq9_test

@router.get("/history", response_model=List[schemas.PHQ9Response])
def get_phq9_history(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
    limit: int = 10
):
    tests = db.query(models.PHQ9Test)\
        .filter(models.PHQ9Test.user_id == current_user.id)\
        .order_by(models.PHQ9Test.created_at.desc())\
        .limit(limit)\
        .all()
    return tests

@router.delete("/history")
def delete_phq9_history(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    db.query(models.PHQ9Test)\
        .filter(models.PHQ9Test.user_id == current_user.id)\
        .delete()
    db.commit()
    return {"message": "PHQ-9 history deleted successfully"}