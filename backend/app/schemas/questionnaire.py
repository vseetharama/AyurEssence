from __future__ import annotations

from pydantic import BaseModel


class QuestionOptionResponse(BaseModel):
    id: str
    option_text: str


class QuestionResponse(BaseModel):
    id: str
    question_text: str
    question_type: str
    is_required: bool
    question_order: int
    options: list[QuestionOptionResponse]


class QuestionnaireVersionResponse(BaseModel):
    id: str
    version_number: int
    title: str
    description: str | None
    questions: list[QuestionResponse]


class QuestionnaireResponse(BaseModel):
    id: str
    name: str
    description: str | None
    is_active: bool
    versions: list[QuestionnaireVersionResponse]


__all__ = [
    "QuestionOptionResponse",
    "QuestionResponse",
    "QuestionnaireResponse",
    "QuestionnaireVersionResponse",
]
