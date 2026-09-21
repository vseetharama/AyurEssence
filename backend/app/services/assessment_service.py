from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.models.patient import Patient
from app.models.questionnaire_version import QuestionnaireVersion
from app.schemas.assessment import AssessmentCreate


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
