from __future__ import annotations

import uuid

from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class QuestionnaireVersion(Base):
    __tablename__ = "questionnaire_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    questionnaire_id: Mapped[str] = mapped_column(String(36), ForeignKey("questionnaires.id"), nullable=False)
    version_number: Mapped[int] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(nullable=False, default=lambda: __import__("datetime").datetime.utcnow().isoformat())
    updated_at: Mapped[str] = mapped_column(nullable=False, default=lambda: __import__("datetime").datetime.utcnow().isoformat(), onupdate=lambda: __import__("datetime").datetime.utcnow().isoformat())

    questionnaire: Mapped["Questionnaire"] = relationship(back_populates="versions")
    questions: Mapped[list["Question"]] = relationship(back_populates="questionnaire_version")
    assessments: Mapped[list["Assessment"]] = relationship(back_populates="questionnaire_version")
