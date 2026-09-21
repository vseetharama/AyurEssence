from __future__ import annotations

import uuid

from sqlalchemy import String, ForeignKey, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    practitioner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    questionnaire_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("questionnaire_versions.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="IN_PROGRESS")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(nullable=False, default=lambda: __import__("datetime").datetime.utcnow().isoformat())
    updated_at: Mapped[str] = mapped_column(nullable=False, default=lambda: __import__("datetime").datetime.utcnow().isoformat(), onupdate=lambda: __import__("datetime").datetime.utcnow().isoformat())
    finalized_at: Mapped[str | None] = mapped_column(DateTime(timezone=False), nullable=True)

    patient: Mapped["Patient"] = relationship(back_populates="assessments")
    practitioner: Mapped["User"] = relationship(back_populates="assessments", foreign_keys=[practitioner_id])
    questionnaire_version: Mapped["QuestionnaireVersion"] = relationship(back_populates="assessments")
    responses: Mapped[list["AssessmentResponse"]] = relationship(back_populates="assessment")
    observations: Mapped[list["PractitionerObservation"]] = relationship(back_populates="assessment")
    dosha_results: Mapped[list["DoshaResult"]] = relationship(back_populates="assessment")
