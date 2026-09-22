from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AssessmentResponseItem(BaseModel):
    id: str
    assessment_id: str
    question_id: str
    option_id: str | None
    response_text: str | None


class AssessmentResponseInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(min_length=1, max_length=36)
    option_id: str = Field(min_length=1, max_length=36)


class AssessmentResponsesCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    responses: list[AssessmentResponseInput] = Field(min_length=1)


__all__ = [
    "AssessmentResponseInput",
    "AssessmentResponseItem",
    "AssessmentResponsesCreate",
]
