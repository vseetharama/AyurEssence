from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_doctor_or_student
from app.database.session import get_db
from app.schemas.assessment import AssessmentCreate, AssessmentResponse
from app.services.assessment_service import (
    assessment_response,
    create_assessment,
    get_patient,
    get_questionnaire_version,
)

router = APIRouter(prefix="/api/assessments", tags=["Assessments"])


@router.post(
    "",
    response_model=AssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an assessment",
)
def create_assessment_record(
    request: AssessmentCreate,
    current_user=Depends(require_doctor_or_student),
    db: Session = Depends(get_db),
) -> AssessmentResponse:
    if get_patient(db, request.patient_id) is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    if get_questionnaire_version(db, request.questionnaire_version_id) is None:
        raise HTTPException(status_code=404, detail="Questionnaire version not found")

    assessment = create_assessment(db, request, current_user.id)
    return AssessmentResponse.model_validate(assessment_response(assessment))
