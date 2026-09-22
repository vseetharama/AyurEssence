from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.models.observation import PractitionerObservation


class ObservationConflictError(Exception):
    pass


def create_observation(
    db: Session,
    assessment: Assessment,
    practitioner_id: str,
    observation_text: str,
) -> PractitionerObservation:
    if assessment.status.upper() == "FINALIZED":
        raise ObservationConflictError("Assessment is finalized and cannot be modified.")
    if assessment.practitioner_id != practitioner_id:
        raise ObservationConflictError(
            "Only the practitioner conducting this assessment may add observations."
        )
    observation = PractitionerObservation(
        assessment_id=assessment.id,
        practitioner_id=practitioner_id,
        observation_text=observation_text.strip(),
    )
    db.add(observation)
    db.commit()
    db.refresh(observation)
    return observation
