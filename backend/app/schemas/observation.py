from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ObservationCreate(BaseModel):
    observation_text: str = Field(min_length=1, max_length=10000)

    @field_validator("observation_text")
    @classmethod
    def validate_observation_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Observation text must not be empty.")
        return value.strip()


class ObservationResponse(BaseModel):
    id: str
    assessment_id: str
    practitioner_id: str
    observation_text: str
    created_at: str


__all__ = ["ObservationCreate", "ObservationResponse"]
