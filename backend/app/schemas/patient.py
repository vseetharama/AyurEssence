from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class PatientCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=301)
    date_of_birth: date | None = None
    gender: str | None = Field(default=None, max_length=50)
    phone: str | None = Field(default=None, max_length=30)


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_code: str
    name: str
    date_of_birth: date | None
    gender: str | None
    phone: str | None
    created_by: str
    created_at: str
    updated_at: str


__all__ = ["PatientCreate", "PatientResponse"]
