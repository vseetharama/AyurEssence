from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRole(str, Enum):
    DOCTOR = "DOCTOR"
    STUDENT = "STUDENT"
    PATIENT = "PATIENT"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    full_name: str
    role: UserRole
    created_at: datetime | str


__all__ = ["UserResponse", "UserRole"]
