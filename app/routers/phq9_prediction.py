from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Response
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..database import get_db
from ..ml.model import predict_api
from typing import List
import os
import io
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
    """
    Generate and download a PDF report for a specific assessment
    """
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
    
    # Create PDF report
    buffer = io.BytesIO()
    
    # Create the PDF document using ReportLab
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=72, 
        leftMargin=72,
        topMargin=72, 
        bottomMargin=72
    )
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=1,  # Center alignment
        spaceAfter=20,
        textColor=colors.navy
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=16,
        alignment=1,  # Center alignment
        spaceAfter=10,
        textColor=colors.teal
    )
    
    label_style = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontSize=12,
        alignment=1,  # Center alignment
        fontName='Helvetica-Bold',
        textColor=colors.gray
    )
    
    value_style = ParagraphStyle(
        'Value',
        parent=styles['Normal'],
        fontSize=14,
        alignment=1,  # Center alignment
        spaceAfter=20,
        textColor=colors.black
    )
    
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=12,
        fontName='Helvetica-Bold',
        textColor=colors.white
    )
    
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.gray,
        alignment=1  # Center alignment
    )
    
    content = []
    
    # Report header and date
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content.append(Paragraph("MINDLOOM ASSESSMENT REPORT", title_style))
    content.append(Paragraph(f"Date: {current_date}", label_style))
    content.append(Paragraph(f"User: {user.name}", label_style))
    content.append(Spacer(1, 20))
    
    # PHQ-9 Results Section
    content.append(Paragraph("PHQ-9 Test Result", section_title_style))
    content.append(Paragraph("Total Score:", label_style))
    content.append(Paragraph(f"{assessment.phq9_score}/27", value_style))
    content.append(Paragraph("Severity:", label_style))
    content.append(Paragraph(f"{assessment.phq9_category}", value_style))
    content.append(Spacer(1, 20))
    
    # CNN-LSTM Model Result Section
    content.append(Paragraph("CNN-LSTM Model Result", section_title_style))
    content.append(Paragraph(f"{assessment.prediction}", value_style))
    
    # Add confidence bar (as text representation since we can't easily do graphical bars)
    content.append(Paragraph("Confidence:", label_style))
    confidence_percentage = assessment.confidence
    if confidence_percentage > 1:  # If confidence is stored as percentage (e.g., 90 instead of 0.9)
        confidence_text = f"{confidence_percentage:.2f}%"
    else:
        confidence_text = f"{confidence_percentage * 100:.2f}%"
    content.append(Paragraph(confidence_text, value_style))
    content.append(Spacer(1, 20))
    
    # PHQ-9 Depression Scale Table
    content.append(Paragraph("PHQ-9 Depression Scale", section_title_style))
    
    # Create table data
    table_data = [
        [Paragraph("Score Range", table_header_style), Paragraph("Depression Severity", table_header_style)],
        ["0-4", "Minimal"],
        ["5-9", "Mild"],
        ["10-14", "Moderate"],
        ["15-19", "Moderately Severe"],
        ["20-27", "Severe"]
    ]
    
    # Create table
    table = Table(table_data, colWidths=[200, 200])
    
    # Style the table
    table.setStyle(TableStyle([
        # Headers
        ('BACKGROUND', (0, 0), (1, 0), colors.teal),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
        ('ALIGN', (0, 0), (1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (1, 0), 12),
        # Cells
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        # Grid
        ('GRID', (0, 0), (-1, -1), 1, colors.gray),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    content.append(table)
    content.append(Spacer(1, 30))
    
    # Disclaimer
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

@router.get("/latest-assessment-id")
async def get_latest_assessment_id(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the ID of the user's latest assessment
    """
    latest_assessment = db.query(models.CombinedAssessment)\
        .filter(models.CombinedAssessment.user_id == current_user.id)\
        .order_by(models.CombinedAssessment.created_at.desc())\
        .first()
    
    if not latest_assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assessment found"
        )
    
    return {"assessment_id": latest_assessment.id}

