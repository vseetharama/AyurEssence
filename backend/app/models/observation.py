from __future__ import annotations

import uuid

from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class PractitionerObservation(Base):
    __tablename__ = "practitioner_observations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id: Mapped[str] = mapped_column(String(36), ForeignKey("assessments.id"), nullable=False, index=True)
    practitioner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    observation_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(nullable=False, default=lambda: __import__("datetime").datetime.utcnow().isoformat())
    updated_at: Mapped[str] = mapped_column(nullable=False, default=lambda: __import__("datetime").datetime.utcnow().isoformat(), onupdate=lambda: __import__("datetime").datetime.utcnow().isoformat())

    assessment: Mapped["Assessment"] = relationship(back_populates="observations")
    practitioner: Mapped["User"] = relationship(back_populates="observations", foreign_keys=[practitioner_id])
