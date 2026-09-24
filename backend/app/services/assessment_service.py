from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.models.assessment_response import AssessmentResponse
from app.models.patient import Patient
from app.models.question import Question
from app.models.question_option import QuestionOption
from app.models.questionnaire_version import QuestionnaireVersion
from app.models.observation import PractitionerObservation
from app.schemas.assessment import AssessmentCreate


class AssessmentConflictError(Exception):
    def __init__(self, detail: str, status_code: int = 409) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


class AssessmentValidationError(Exception):
    def __init__(self, detail: str, status_code: int = 409) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


def get_patient(db: Session, patient_id: str) -> Patient | None:
    return db.get(Patient, patient_id)


def get_questionnaire_version(db: Session, version_id: str) -> QuestionnaireVersion | None:
    return db.get(QuestionnaireVersion, version_id)


def create_assessment(
    db: Session,
    request: AssessmentCreate,
    practitioner_id: str,
) -> Assessment:
    assessment = Assessment(
        patient_id=request.patient_id,
        questionnaire_version_id=request.questionnaire_version_id,
        practitioner_id=practitioner_id,
        status="IN_PROGRESS",
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


def find_patient_assessments(db: Session, patient_id: str) -> list[Assessment]:
    statement = (
        select(Assessment)
        .where(Assessment.patient_id == patient_id)
        .order_by(Assessment.created_at.desc())
    )
    return list(db.scalars(statement).all())


def assessment_response(assessment: Assessment) -> dict[str, str | None]:
    return {
        "id": assessment.id,
        "patient_id": assessment.patient_id,
        "practitioner_id": assessment.practitioner_id,
        "questionnaire_version_id": assessment.questionnaire_version_id,
        "status": assessment.status,
        "started_at": assessment.created_at,
        "completed_at": assessment.finalized_at.isoformat() if assessment.finalized_at else None,
        "created_at": assessment.created_at,
    }


def get_required_question_ids(db: Session, assessment: Assessment) -> set[str]:
    questions = list(
        db.scalars(
            select(Question).where(
                Question.questionnaire_version_id == assessment.questionnaire_version_id,
                Question.is_required.is_(True),
            )
        ).all()
    )
    return {question.id for question in questions}


def validate_finalization_inputs(db: Session, assessment: Assessment) -> None:
    if assessment.status.upper() == "FINALIZED" or assessment.finalized_at is not None:
        raise AssessmentConflictError("Assessment has already been finalized.", 409)
    if assessment.status.upper() != "IN_PROGRESS":
        raise AssessmentConflictError("Assessment is not in progress and cannot be finalized.", 409)

    observation_exists = db.scalar(
        select(PractitionerObservation.id).where(
            PractitionerObservation.assessment_id == assessment.id,
        )
    )
    if observation_exists is None:
        raise AssessmentValidationError(
            "Practitioner observation is required before finalizing the assessment.",
            409,
        )

    required_question_ids = get_required_question_ids(db, assessment)
    responses = list(
        db.scalars(
            select(AssessmentResponse).where(
                AssessmentResponse.assessment_id == assessment.id,
            )
        ).all()
    )
    response_by_question = {response.question_id: response for response in responses}
    if not required_question_ids.issubset(response_by_question):
        missing = sorted(required_question_ids.difference(response_by_question))
        raise AssessmentValidationError(
            f"Required questionnaire responses are missing: {', '.join(missing)}",
            409,
        )

    for response in responses:
        question = db.get(Question, response.question_id)
        if question is None:
            raise AssessmentValidationError("Assessment contains a response for a missing question.", 409)
        if question.questionnaire_version_id != assessment.questionnaire_version_id:
            raise AssessmentValidationError(
                "Assessment contains a response from another questionnaire version.",
                409,
            )
        if response.option_id is not None:
            option = db.get(QuestionOption, response.option_id)
            if option is None or option.question_id != response.question_id:
                raise AssessmentValidationError(
                    "Assessment response contains an invalid question/option relationship.",
                    409,
                )


def finalize_assessment(db: Session, assessment: Assessment, practitioner_id: str) -> Assessment:
    if assessment.practitioner_id != practitioner_id:
        raise AssessmentConflictError(
            "Only the practitioner conducting this assessment may finalize it.",
            403,
        )
    validate_finalization_inputs(db, assessment)
    assessment.status = "FINALIZED"
    assessment.finalized_at = datetime.utcnow()
    assessment.updated_at = datetime.utcnow().isoformat()
    db.commit()
    db.refresh(assessment)
    return assessment
