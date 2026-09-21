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


__all__ = ["AssessmentCreate", "AssessmentResponse"]
