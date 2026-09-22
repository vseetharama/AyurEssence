from __future__ import annotations

from pydantic import BaseModel


class DoshaResultResponse(BaseModel):
    id: str
    assessment_id: str
    methodology_id: str | None
    vata_percentage: float
    pitta_percentage: float
    kapha_percentage: float
    dominant_dosha: str | None
    notes: str | None
    created_at: str
    updated_at: str


__all__ = ["DoshaResultResponse"]
