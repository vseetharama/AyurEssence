from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import CurrentUser, require_doctor, require_doctor_or_student
from app.database.session import get_db
from app.models.assessment import Assessment
from app.models.assessment_response import AssessmentResponse as AssessmentResponseModel
from app.models.dosha_result import DoshaResult
from app.models.methodology import Methodology
from app.models.observation import PractitionerObservation
from app.models.question import Question
from app.models.question_option import QuestionOption
from app.models.reference import Reference
from app.schemas.assessment import (
    AssessmentCreate,
    AssessmentFinalizeResponse,
    AssessmentReport,
    AssessmentResponse as AssessmentResponseSchema,
    ReportAssessment,
    ReportObservation,
    ReportPatient,
    ReportPrakritiResult,
    ReportQuestionnaire,
    ReportResponse,
)
from app.services.assessment_service import (
    AssessmentConflictError,
    AssessmentValidationError,
    assessment_response,
    create_assessment,
    finalize_assessment,
    get_patient,
    get_questionnaire_version,
)
from app.services.patient_service import patient_response

router = APIRouter(prefix="/api/assessments", tags=["Assessments"])


@router.post(
    "",
    response_model=AssessmentResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create an assessment",
)
def create_assessment_record(
    request: AssessmentCreate,
    current_user=Depends(require_doctor_or_student),
    db: Session = Depends(get_db),
) -> AssessmentResponseSchema:
    if get_patient(db, request.patient_id) is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    if get_questionnaire_version(db, request.questionnaire_version_id) is None:
        raise HTTPException(status_code=404, detail="Questionnaire version not found")

    assessment = create_assessment(db, request, current_user.id)
    return AssessmentResponseSchema.model_validate(assessment_response(assessment))


@router.post(
    "/{assessment_id}/finalize",
    response_model=AssessmentFinalizeResponse,
    summary="Finalize an in-progress assessment",
)
def finalize_assessment_record(
    assessment_id: str,
    current_user=Depends(require_doctor),
    db: Session = Depends(get_db),
) -> AssessmentFinalizeResponse:
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found.")

    try:
        finalized = finalize_assessment(db, assessment, current_user.id)
    except (AssessmentConflictError, AssessmentValidationError) as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from None

    return AssessmentFinalizeResponse(
        assessment_id=finalized.id,
        status=finalized.status,
        completed_at=finalized.finalized_at.isoformat() if finalized.finalized_at else None,
        message="Assessment finalized successfully.",
    )


@router.get(
    "/{assessment_id}/report",
    response_model=AssessmentReport,
    summary="Get an assessment report",
)
def get_assessment_report(
    assessment_id: str,
    current_user=Depends(require_doctor_or_student),
    db: Session = Depends(get_db),
) -> AssessmentReport:
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found.")
    if current_user.role.upper() == "PATIENT":
        raise HTTPException(status_code=403, detail="Patient access to assessment reports is not permitted.")
    if current_user.role.upper() == "STUDENT" and assessment.practitioner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owning practitioner may view this assessment report.")

    patient = assessment.patient
    questionnaire_version = assessment.questionnaire_version
    questionnaire = questionnaire_version.questionnaire
    responses = list(
        db.scalars(
            select(Question).where(Question.questionnaire_version_id == questionnaire_version.id)
        ).all()
    )
    question_by_id = {question.id: question for question in responses}
    response_rows = list(
        db.scalars(
            select(AssessmentResponseModel).where(AssessmentResponseModel.assessment_id == assessment.id)
        ).all()
    )
    response_payload = []
    for response in response_rows:
        question = question_by_id.get(response.question_id)
        option = db.get(QuestionOption, response.option_id) if response.option_id else None
        response_payload.append(
            ReportResponse(
                question_id=response.question_id,
                question_text=question.question_text if question else "Unknown question",
                selected_option_id=response.option_id,
                selected_option_text=option.option_text if option else None,
                response_text=response.response_text,
            )
        )

    observation = db.scalar(
        select(PractitionerObservation).where(
            PractitionerObservation.assessment_id == assessment.id,
        ).order_by(PractitionerObservation.created_at.desc())
    )
    observation_payload = None
    if observation is not None:
        observation_payload = ReportObservation(
            id=observation.id,
            practitioner_id=observation.practitioner_id,
            practitioner_name=observation.practitioner.full_name if observation.practitioner else None,
            observation_text=observation.observation_text,
            created_at=observation.created_at,
        )

    result = db.scalar(
        select(DoshaResult).where(DoshaResult.assessment_id == assessment.id)
    )
    prakriti_result = ReportPrakritiResult(result_status="UNAVAILABLE")
    if result is not None and result.methodology_id is not None:
        methodology = db.get(Methodology, result.methodology_id)
        references = list(
            db.scalars(
                select(Reference).where(Reference.methodology_id == result.methodology_id)
            ).all()
        )
        if (
            result.vata_percentage is not None
            and result.pitta_percentage is not None
            and result.kapha_percentage is not None
        ):
            prakriti_result = ReportPrakritiResult(
                result_status="AVAILABLE",
                methodology_id=result.methodology_id,
                methodology_name=methodology.name if methodology else None,
                methodology_version=methodology.version if methodology else None,
                vata_percentage=result.vata_percentage,
                pitta_percentage=result.pitta_percentage,
                kapha_percentage=result.kapha_percentage,
                dominant_dosha=result.dominant_dosha,
                references=[
                    {
                        "id": reference.id,
                        "title": reference.title,
                        "author": reference.author,
                        "source": reference.source,
                        "citation": reference.citation,
                    }
                    for reference in references
                ],
            )
        else:
            prakriti_result = ReportPrakritiResult(
                result_status="UNAVAILABLE",
                methodology_id=result.methodology_id,
                methodology_name=methodology.name if methodology else None,
                methodology_version=methodology.version if methodology else None,
                references=[
                    {
                        "id": reference.id,
                        "title": reference.title,
                        "author": reference.author,
                        "source": reference.source,
                        "citation": reference.citation,
                    }
                    for reference in references
                ],
            )

    return AssessmentReport(
        patient=ReportPatient(
            id=patient.id,
            patient_code=patient.patient_code,
            name=" ".join(part for part in (patient.first_name, patient.last_name) if part).strip() or None,
            date_of_birth=patient.date_of_birth.isoformat() if patient.date_of_birth else None,
            gender=patient.gender,
            phone=patient.phone,
        ),
        assessment=ReportAssessment(
            id=assessment.id,
            status=assessment.status,
            started_at=assessment.created_at,
            completed_at=assessment.finalized_at.isoformat() if assessment.finalized_at else None,
            created_at=assessment.created_at,
            practitioner_id=assessment.practitioner_id,
            practitioner_name=assessment.practitioner.full_name if assessment.practitioner else None,
        ),
        questionnaire=ReportQuestionnaire(
            id=questionnaire.id,
            name=questionnaire.name,
            version_id=questionnaire_version.id,
            version_number=questionnaire_version.version_number,
            title=questionnaire_version.title,
        ),
        responses=response_payload,
        practitioner_observation=observation_payload,
        prakriti_result=prakriti_result,
    )
