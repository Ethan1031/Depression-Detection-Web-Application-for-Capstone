from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..database import get_db
from ..ml.model import predict_api 
from typing import List
import os

router = APIRouter()

@router.post("/upload", response_model=schemas.PredictionResponse)
async def create_prediction(
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith('.edf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload an EDF file"
        )
    
    try:
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        prediction_result = predict_api(temp_path)
        os.remove(temp_path)
        
        # Save prediction to database
        db_prediction = models.Prediction(
            user_id=current_user.id,
            prediction=prediction_result["final_prediction"],
            confidence=prediction_result["confidence"],
            segments_analyzed=prediction_result["segments_analyzed"],
            detailed_results=prediction_result["segment_details"]
        )
        db.add(db_prediction)
        db.commit()
        db.refresh(db_prediction)
        
        return db_prediction
        
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/history", response_model=List[schemas.PredictionResponse])
def get_predictions(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
    limit: int = 10
):
    predictions = db.query(models.Prediction)\
        .filter(models.Prediction.user_id == current_user.id)\
        .order_by(models.Prediction.created_at.desc())\
        .limit(limit)\
        .all()
    return predictions

@router.delete("/{prediction_id}")
def delete_prediction(
    prediction_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    prediction_query = db.query(models.Prediction)\
        .filter(models.Prediction.id == prediction_id, models.Prediction.user_id == current_user.id)
    prediction = prediction_query.first()
    
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found"
        )
    
    prediction_query.delete()
    db.commit()
    return {"message": "Prediction deleted successfully"}