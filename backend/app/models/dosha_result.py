from __future__ import annotations

import uuid

from sqlalchemy import String, ForeignKey, Float, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class DoshaResult(Base):
    __tablename__ = "dosha_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id: Mapped[str] = mapped_column(String(36), ForeignKey("assessments.id"), nullable=False, index=True)
    methodology_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("methodologies.id"), nullable=True)
    vata_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    pitta_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    kapha_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    dominant_dosha: Mapped[str | None] = mapped_column(String(30), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(nullable=False, default=lambda: __import__("datetime").datetime.utcnow().isoformat())
    updated_at: Mapped[str] = mapped_column(nullable=False, default=lambda: __import__("datetime").datetime.utcnow().isoformat(), onupdate=lambda: __import__("datetime").datetime.utcnow().isoformat())

    assessment: Mapped["Assessment"] = relationship(back_populates="dosha_results")
    methodology: Mapped["Methodology"] = relationship(back_populates="dosha_results")
