from __future__ import annotations

import uuid

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.schemas.patient import PatientCreate


def _split_name(name: str) -> tuple[str, str]:
    parts = name.strip().split(maxsplit=1)
    return parts[0], parts[1] if len(parts) == 2 else ""


def create_patient(db: Session, request: PatientCreate, created_by: str) -> Patient:
    first_name, last_name = _split_name(request.name)
    patient = Patient(
        patient_code=f"P-{uuid.uuid4().hex[:12].upper()}",
        first_name=first_name,
        last_name=last_name,
        date_of_birth=request.date_of_birth,
        gender=request.gender.strip() if request.gender else None,
        phone=request.phone.strip() if request.phone else None,
        created_by=created_by,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def find_patients(
    db: Session,
    *,
    name: str | None = None,
    phone: str | None = None,
    date_of_birth=None,
) -> list[Patient]:
    filters = []
    if name:
        search = f"%{name.strip()}%"
        filters.append(
            or_(
                Patient.first_name.ilike(search),
                Patient.last_name.ilike(search),
                func.concat(Patient.first_name, " ", Patient.last_name).ilike(search),
            )
        )
    if phone:
        filters.append(Patient.phone == phone.strip())
    if date_of_birth:
        filters.append(Patient.date_of_birth == date_of_birth)
    statement = select(Patient).where(and_(*filters)).order_by(Patient.created_at.desc())
    return list(db.scalars(statement).all())


def get_patient(db: Session, patient_id: str) -> Patient | None:
    return db.get(Patient, patient_id)


def patient_response(patient: Patient) -> dict[str, object]:
    name = " ".join(part for part in (patient.first_name, patient.last_name) if part).strip()
    return {
        "id": patient.id,
        "patient_code": patient.patient_code,
        "name": name,
        "date_of_birth": patient.date_of_birth,
        "gender": patient.gender,
        "phone": patient.phone,
        "created_by": patient.created_by,
        "created_at": patient.created_at,
        "updated_at": patient.updated_at,
    }
