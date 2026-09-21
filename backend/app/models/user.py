from __future__ import annotations

import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="PATIENT")
    created_at: Mapped[str] = mapped_column(nullable=False, default=lambda: __import__("datetime").datetime.utcnow().isoformat())
    updated_at: Mapped[str] = mapped_column(nullable=False, default=lambda: __import__("datetime").datetime.utcnow().isoformat(), onupdate=lambda: __import__("datetime").datetime.utcnow().isoformat())

    patients: Mapped[list["Patient"]] = relationship(back_populates="created_by_user")
    assessments: Mapped[list["Assessment"]] = relationship(back_populates="practitioner", foreign_keys="Assessment.practitioner_id")
    observations: Mapped[list["PractitionerObservation"]] = relationship(back_populates="practitioner", foreign_keys="PractitionerObservation.practitioner_id")
