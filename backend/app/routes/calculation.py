from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import require_doctor_or_student
from app.database.session import get_db
from app.models.methodology import Methodology
from app.schemas.dosha_result import DoshaResultResponse
from app.services.prakriti_service import (
    CalculationValidationError,
    calculate_and_persist,
)
from app.services.response_service import get_assessment

router = APIRouter(prefix="/api/assessments", tags=["Prakriti Calculation"])
METHODOLOGY_NAME = "CCRAS PAS-Based Scoring - SDM Adapted Questionnaire"


@router.post(
    "/{assessment_id}/calculate",
    response_model=DoshaResultResponse,
    summary="Calculate and persist the configured Prakriti result",
)
def calculate_assessment(
    assessment_id: str,
    current_user=Depends(require_doctor_or_student),
    db: Session = Depends(get_db),
) -> DoshaResultResponse:
    assessment = get_assessment(db, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found.")
    if assessment.practitioner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the practitioner conducting this assessment may calculate it.",
        )
    if assessment.status.upper() == "FINALIZED":
        raise HTTPException(
            status_code=409,
            detail="Assessment is finalized and cannot be modified.",
        )

    methodology = db.scalar(
        select(Methodology).where(Methodology.name == METHODOLOGY_NAME)
    )
    if methodology is None:
        raise HTTPException(status_code=409, detail="Required methodology is not configured.")

    try:
        result = calculate_and_persist(db, assessment, methodology)
    except CalculationValidationError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from None
    return DoshaResultResponse(
        id=result.id,
        assessment_id=result.assessment_id,
        methodology_id=result.methodology_id,
        vata_percentage=result.vata_percentage,
        pitta_percentage=result.pitta_percentage,
        kapha_percentage=result.kapha_percentage,
        dominant_dosha=result.dominant_dosha,
        notes=result.notes,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )
