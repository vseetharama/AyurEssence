from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.models.assessment_response import AssessmentResponse
from app.models.question import Question
from app.models.question_option import QuestionOption
from app.schemas.assessment_response import AssessmentResponsesCreate


class ResponseValidationError(Exception):
    def __init__(self, detail: str, status_code: int = 400) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


def get_assessment(db: Session, assessment_id: str) -> Assessment | None:
    return db.get(Assessment, assessment_id)


def _validate_and_index(
    db: Session,
    assessment: Assessment,
    requests: Iterable,
) -> list[tuple[Question, QuestionOption]]:
    validated: list[tuple[Question, QuestionOption]] = []
    seen_questions: set[str] = set()
    for item in requests:
        if item.question_id in seen_questions:
            continue
        seen_questions.add(item.question_id)
        question = db.get(Question, item.question_id)
        if question is None:
            raise ResponseValidationError("Question not found.", 404)
        if question.questionnaire_version_id != assessment.questionnaire_version_id:
            raise ResponseValidationError(
                "Question does not belong to the assessment questionnaire version."
            )
        option = db.get(QuestionOption, item.option_id)
        if option is None:
            raise ResponseValidationError("Option not found.", 404)
        if option.question_id != question.id:
            raise ResponseValidationError("Option does not belong to the selected question.")
        validated.append((question, option))
    return validated


def save_responses(
    db: Session,
    assessment: Assessment,
    request: AssessmentResponsesCreate,
) -> list[AssessmentResponse]:
    if assessment.status.upper() == "FINALIZED":
        raise ResponseValidationError(
            "Assessment is finalized and cannot be modified.",
            409,
        )

    validated = _validate_and_index(db, assessment, request.responses)
    question_ids = [question.id for question, _ in validated]
    existing = {
        item.question_id: item
        for item in db.scalars(
            select(AssessmentResponse).where(
                AssessmentResponse.assessment_id == assessment.id,
                AssessmentResponse.question_id.in_(question_ids),
            )
        ).all()
    }
    for question, option in validated:
        response = existing.get(question.id)
        if response is None:
            response = AssessmentResponse(
                assessment_id=assessment.id,
                question_id=question.id,
            )
            db.add(response)
        response.option_id = option.id
        response.response_text = None

    db.commit()
    for response in existing.values():
        db.refresh(response)
    saved = list(
        db.scalars(
            select(AssessmentResponse)
            .where(
                AssessmentResponse.assessment_id == assessment.id,
                AssessmentResponse.question_id.in_(question_ids),
            )
            .order_by(AssessmentResponse.created_at)
        ).all()
    )
    return saved


def response_item(response: AssessmentResponse) -> dict[str, str | None]:
    return {
        "id": response.id,
        "assessment_id": response.assessment_id,
        "question_id": response.question_id,
        "option_id": response.option_id,
        "response_text": response.response_text,
    }
