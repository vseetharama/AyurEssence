from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import require_doctor_or_student
from app.database.session import get_db
from app.schemas.assessment_response import (
    AssessmentResponseItem,
    AssessmentResponsesCreate,
)
from app.services.response_service import (
    ResponseValidationError,
    get_assessment,
    response_item,
    save_responses,
)

router = APIRouter(prefix="/api/assessments", tags=["Assessment Responses"])


@router.post(
    "/{assessment_id}/responses",
    response_model=list[AssessmentResponseItem],
    summary="Submit or update assessment responses",
)
def submit_assessment_responses(
    assessment_id: str,
    request: AssessmentResponsesCreate,
    current_user=Depends(require_doctor_or_student),
    db: Session = Depends(get_db),
) -> list[AssessmentResponseItem]:
    assessment = get_assessment(db, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found.")

    try:
        responses = save_responses(db, assessment, request)
    except ResponseValidationError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from None
    return [AssessmentResponseItem.model_validate(response_item(item)) for item in responses]
