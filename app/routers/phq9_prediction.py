from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..database import get_db
from ..ml.model import predict_api
from typing import List
import os

router = APIRouter()

@router.post("/submit-phq9", response_model=schemas.PHQ9Response)
async def submit_phq9(
    phq9_data: schemas.PHQ9Create,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Validate PHQ-9 answers
    if len(phq9_data.answers) != 9 or not all(0 <= answer <= 3 for answer in phq9_data.answers):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PHQ-9 answers. Must provide 9 answers, each between 0 and 3"
        )
    
    # Create PHQ9Test record
    db_phq9 = models.PHQ9Test(
        user_id=current_user.id,
        answers=phq9_data.answers,
        total_score=phq9_data.total_score,
        category=phq9_data.category
    )
    
    db.add(db_phq9)
    db.commit()
    db.refresh(db_phq9)
    
    return db_phq9

@router.post("/submit-assessment", response_model=schemas.CombinedAssessmentResponse)
async def submit_combined_assessment(
    phq9_answers: List[int],
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Validate PHQ-9 answers
    if len(phq9_answers) != 9 or not all(0 <= answer <= 3 for answer in phq9_answers):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PHQ-9 answers. Must provide 9 answers, each between 0 and 3"
        )
    
    # Calculate PHQ-9 score and category
    phq9_score = sum(phq9_answers)
    phq9_category = "Minimal Depression"
    if phq9_score >= 20:
        phq9_category = "Severe Depression"
    elif phq9_score >= 15:
        phq9_category = "Moderately Severe Depression"
    elif phq9_score >= 10:
        phq9_category = "Moderate Depression"
    elif phq9_score >= 5:
        phq9_category = "Mild Depression"
    
    # Validate file
    if not file.filename.endswith('.edf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload an EDF file"
        )
    
    try:
        # Save file temporarily
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process EEG file with model
        prediction_result = predict_api(temp_path)
        os.remove(temp_path)
        
        # Create combined assessment record
        db_assessment = models.CombinedAssessment(
            user_id=current_user.id,
            phq9_answers=phq9_answers,
            phq9_score=phq9_score,
            phq9_category=phq9_category,
            prediction=prediction_result["final_prediction"],
            confidence=prediction_result["confidence"],
            segments_analyzed=prediction_result["segments_analyzed"],
            detailed_results=prediction_result["segment_details"]
        )
        
        db.add(db_assessment)
        db.commit()
        db.refresh(db_assessment)
        
        return db_assessment
        
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/assessment-history", response_model=List[schemas.CombinedAssessmentResponse])
def get_assessment_history(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
    limit: int = 10
):
    assessments = db.query(models.CombinedAssessment)\
        .filter(models.CombinedAssessment.user_id == current_user.id)\
        .order_by(models.CombinedAssessment.created_at.desc())\
        .limit(limit)\
        .all()
    return assessments

@router.delete("/assessment/{assessment_id}")
def delete_assessment(
    assessment_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    assessment_query = db.query(models.CombinedAssessment)\
        .filter(models.CombinedAssessment.id == assessment_id, 
                models.CombinedAssessment.user_id == current_user.id)
    assessment = assessment_query.first()
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    assessment_query.delete()
    db.commit()
    return {"message": "Assessment deleted successfully"}

