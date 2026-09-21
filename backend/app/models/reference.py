from __future__ import annotations

import uuid

from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Reference(Base):
    __tablename__ = "references"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    methodology_id: Mapped[str] = mapped_column(String(36), ForeignKey("methodologies.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    citation: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(nullable=False, default=lambda: __import__("datetime").datetime.utcnow().isoformat())
    updated_at: Mapped[str] = mapped_column(nullable=False, default=lambda: __import__("datetime").datetime.utcnow().isoformat(), onupdate=lambda: __import__("datetime").datetime.utcnow().isoformat())

    methodology: Mapped["Methodology"] = relationship(back_populates="references")
