from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import require_doctor_or_student
from app.database.session import get_db
from app.schemas.questionnaire import QuestionnaireResponse
from app.services.questionnaire_service import get_questionnaire, questionnaire_response

router = APIRouter(prefix="/api/questionnaires", tags=["Questionnaires"])


@router.get(
    "/{questionnaire_id}",
    response_model=QuestionnaireResponse,
    summary="Get a questionnaire with versions, questions, and answer options",
)
def get_questionnaire_structure(
    questionnaire_id: str,
    current_user=Depends(require_doctor_or_student),
    db: Session = Depends(get_db),
) -> QuestionnaireResponse:
    questionnaire = get_questionnaire(db, questionnaire_id)
    if questionnaire is None:
        raise HTTPException(status_code=404, detail="Questionnaire not found.")
    return QuestionnaireResponse.model_validate(questionnaire_response(questionnaire))
