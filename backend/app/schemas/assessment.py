from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AssessmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: str = Field(min_length=1, max_length=36)
    questionnaire_version_id: str = Field(min_length=1, max_length=36)


class AssessmentResponse(BaseModel):
    id: str
    patient_id: str
    practitioner_id: str
    questionnaire_version_id: str
    status: str
    started_at: str
    completed_at: str | None
    created_at: str


class AssessmentFinalizeResponse(BaseModel):
    assessment_id: str
    status: str
    completed_at: str | None
    message: str


class ReportPatient(BaseModel):
    id: str
    patient_code: str | None = None
    name: str | None = None
    date_of_birth: str | None = None
    gender: str | None = None
    phone: str | None = None


class ReportAssessment(BaseModel):
    id: str
    status: str
    started_at: str | None = None
    completed_at: str | None = None
    created_at: str | None = None
    practitioner_id: str | None = None
    practitioner_name: str | None = None


class ReportQuestionnaire(BaseModel):
    id: str
    name: str
    version_id: str | None = None
    version_number: int | None = None
    title: str | None = None


class ReportResponse(BaseModel):
    question_id: str
    question_text: str
    selected_option_id: str | None = None
    selected_option_text: str | None = None
    response_text: str | None = None


class ReportObservation(BaseModel):
    id: str | None = None
    practitioner_id: str | None = None
    practitioner_name: str | None = None
    observation_text: str | None = None
    created_at: str | None = None


class ReportPrakritiResult(BaseModel):
    result_status: str
    methodology_id: str | None = None
    methodology_name: str | None = None
    methodology_version: str | None = None
    vata_percentage: float | None = None
    pitta_percentage: float | None = None
    kapha_percentage: float | None = None
    dominant_dosha: str | None = None
    references: list[dict[str, str | None]] = Field(default_factory=list)


class AssessmentReport(BaseModel):
    patient: ReportPatient
    assessment: ReportAssessment
    questionnaire: ReportQuestionnaire
    responses: list[ReportResponse]
    practitioner_observation: ReportObservation | None = None
    prakriti_result: ReportPrakritiResult


__all__ = [
    "AssessmentCreate",
    "AssessmentFinalizeResponse",
    "AssessmentReport",
    "AssessmentResponse",
    "ReportAssessment",
    "ReportObservation",
    "ReportPatient",
    "ReportPrakritiResult",
    "ReportQuestionnaire",
    "ReportResponse",
]
