from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_doctor_or_student
from app.database.session import get_db
from app.schemas.observation import ObservationCreate, ObservationResponse
from app.services.observation_service import (
    ObservationConflictError,
    create_observation,
)
from app.services.response_service import get_assessment

router = APIRouter(prefix="/api/assessments", tags=["Practitioner Observations"])


@router.post(
    "/{assessment_id}/observations",
    response_model=ObservationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a practitioner observation",
)
def add_observation(
    assessment_id: str,
    request: ObservationCreate,
    current_user=Depends(require_doctor_or_student),
    db: Session = Depends(get_db),
) -> ObservationResponse:
    assessment = get_assessment(db, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found.")
    try:
        observation = create_observation(
            db,
            assessment,
            current_user.id,
            request.observation_text,
        )
    except ObservationConflictError as error:
        status_code = 409 if assessment.status.upper() == "FINALIZED" else 403
        raise HTTPException(status_code=status_code, detail=str(error)) from None
    return ObservationResponse(
        id=observation.id,
        assessment_id=observation.assessment_id,
        practitioner_id=observation.practitioner_id,
        observation_text=observation.observation_text,
        created_at=observation.created_at,
    )
