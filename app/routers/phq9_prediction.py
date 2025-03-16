from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..database import get_db
from ..ml.model import predict_api
from typing import List
import os

from datetime import datetime 
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

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


@router.get("/download-report/{assessment_id}")
async def download_assessment_report(
    assessment_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Get the assessment with the given ID
    assessment = db.query(models.CombinedAssessment)\
        .filter(models.CombinedAssessment.id == assessment_id, 
                models.CombinedAssessment.user_id == current_user.id)\
        .first()
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    # Get user information
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    
    # Create report content
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create a file-like object to receive PDF data
    buffer = io.BytesIO()
    
    # Create the PDF document using ReportLab
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        spaceAfter=12
    )
    
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        spaceAfter=10,
        spaceBefore=10
    )
    
    normal_style = styles["Normal"]
    
    # Build the document content
    content = []
    
    # Title
    content.append(Paragraph("MINDLOOM ASSESSMENT REPORT", title_style))
    content.append(Spacer(1, 12))
    
    # User info and date
    content.append(Paragraph(f"Date: {current_date}", normal_style))
    content.append(Paragraph(f"User: {user.name}", normal_style))
    content.append(Spacer(1, 12))
    
    # PHQ-9 Section
    content.append(Paragraph("PHQ-9 DEPRESSION SCREENING RESULTS", heading_style))
    content.append(Paragraph(f"Total Score: {assessment.phq9_score}/27", normal_style))
    content.append(Paragraph(f"Severity: {assessment.phq9_category}", normal_style))
    content.append(Spacer(1, 6))
    
    # PHQ-9 Answers Table
    phq9_questions = [
        "Little interest or pleasure in doing things",
        "Feeling down, depressed, or hopeless",
        "Trouble falling/staying asleep, sleeping too much",
        "Feeling tired or having little energy",
        "Poor appetite or overeating",
        "Feeling bad about yourself",
        "Trouble concentrating",
        "Moving or speaking slowly/being fidgety or restless",
        "Thoughts of hurting yourself"
    ]
    
    phq9_data = [["Question", "Score"]]
    for i, question in enumerate(phq9_questions):
        phq9_data.append([f"{i+1}. {question}", str(assessment.phq9_answers[i])])
    
    phq9_table = Table(phq9_data, colWidths=[350, 60])
    phq9_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
        ('ALIGN', (0, 0), (1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    content.append(phq9_table)
    content.append(Spacer(1, 12))
    
    # EEG Analysis Section
    content.append(Paragraph("EEG ANALYSIS RESULTS", heading_style))
    content.append(Paragraph(f"Prediction: {assessment.prediction}", normal_style))
    content.append(Paragraph(f"Confidence: {assessment.confidence:.2f}%", normal_style))
    content.append(Paragraph(f"Segments Analyzed: {assessment.segments_analyzed}", normal_style))
    content.append(Spacer(1, 12))
    
    # Disclaimer
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey
    )
    
    disclaimer_text = """
    DISCLAIMER: This report is intended for use by healthcare professionals. 
    These assessments should be interpreted in the context of a clinician's medical care 
    and are not intended to be used alone to diagnose or treat any condition.
    """
    
    content.append(Paragraph(disclaimer_text, disclaimer_style))
    
    # Build the PDF
    doc.build(content)
    
    # Move buffer position to the beginning
    buffer.seek(0)
    
    # Generate filename
    filename = f"mindloom_assessment_{assessment_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    # Return as downloadable PDF file
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

