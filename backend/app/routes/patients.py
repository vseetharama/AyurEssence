from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import CurrentUser, require_doctor_or_student
from app.database.session import get_db
from app.schemas.assessment import AssessmentResponse
from app.schemas.patient import PatientCreate, PatientResponse
from app.services.assessment_service import find_patient_assessments
from app.services.patient_service import (
    create_patient,
    find_patients,
    get_patient,
    patient_response,
)
from app.services.assessment_service import assessment_response

router = APIRouter(prefix="/api/patients", tags=["Patients"])


def _patient_or_404(db: Session, patient_id: str):
    patient = get_patient(db, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.post(
    "",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a patient profile",
)
def create_patient_profile(
    request: PatientCreate,
    current_user=Depends(require_doctor_or_student),
    db: Session = Depends(get_db),
) -> PatientResponse:
    patient = create_patient(db, request, current_user.id)
    return PatientResponse.model_validate(patient_response(patient))


@router.get(
    "",
    response_model=list[PatientResponse],
    summary="Search patient profiles",
)
def list_patient_profiles(
    name: str | None = Query(default=None, max_length=301),
    phone: str | None = Query(default=None, max_length=30),
    date_of_birth: date | None = None,
    current_user=Depends(require_doctor_or_student),
    db: Session = Depends(get_db),
) -> list[PatientResponse]:
    patients = find_patients(
        db,
        name=name,
        phone=phone,
        date_of_birth=date_of_birth,
    )
    return [PatientResponse.model_validate(patient_response(patient)) for patient in patients]


@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Get a patient profile",
)
def get_patient_profile(
    patient_id: str,
    current_user=Depends(require_doctor_or_student),
    db: Session = Depends(get_db),
) -> PatientResponse:
    patient = _patient_or_404(db, patient_id)
    return PatientResponse.model_validate(patient_response(patient))


@router.get(
    "/{patient_id}/assessments",
    response_model=list[AssessmentResponse],
    summary="Get a patient's assessment history",
)
def get_patient_assessments(
    patient_id: str,
    current_user=Depends(require_doctor_or_student),
    db: Session = Depends(get_db),
) -> list[AssessmentResponse]:
    _patient_or_404(db, patient_id)
    assessments = find_patient_assessments(db, patient_id)
    return [AssessmentResponse.model_validate(assessment_response(item)) for item in assessments]
