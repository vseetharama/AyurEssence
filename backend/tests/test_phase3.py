from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.database.session import SessionLocal
from app.main import app
from app.models.assessment import Assessment
from app.models.patient import Patient
from app.models.questionnaire import Questionnaire
from app.models.questionnaire_version import QuestionnaireVersion
from app.models.user import User

client = TestClient(app)
TEST_EMAIL_PREFIX = "phase3-test-"


@pytest.fixture(autouse=True)
def clean_phase3_data():
    with SessionLocal() as db:
        user_ids = select(User.id).where(User.email.like(f"{TEST_EMAIL_PREFIX}%"))
        patient_ids = select(Patient.id).where(Patient.created_by.in_(user_ids))
        db.execute(delete(Assessment).where(Assessment.patient_id.in_(patient_ids)))
        db.execute(delete(Patient).where(Patient.created_by.in_(user_ids)))
        db.execute(delete(QuestionnaireVersion).where(QuestionnaireVersion.title.like("P3-%")))
        db.execute(delete(Questionnaire).where(Questionnaire.name.like("P3-%")))
        db.execute(delete(User).where(User.email.like(f"{TEST_EMAIL_PREFIX}%")))
        db.commit()
    yield
    with SessionLocal() as db:
        user_ids = select(User.id).where(User.email.like(f"{TEST_EMAIL_PREFIX}%"))
        patient_ids = select(Patient.id).where(Patient.created_by.in_(user_ids))
        db.execute(delete(Assessment).where(Assessment.patient_id.in_(patient_ids)))
        db.execute(delete(Patient).where(Patient.created_by.in_(user_ids)))
        db.execute(delete(QuestionnaireVersion).where(QuestionnaireVersion.title.like("P3-%")))
        db.execute(delete(Questionnaire).where(Questionnaire.name.like("P3-%")))
        db.execute(delete(User).where(User.email.like(f"{TEST_EMAIL_PREFIX}%")))
        db.commit()


def user_payload(role: str) -> dict[str, str]:
    return {
        "email": f"{TEST_EMAIL_PREFIX}{uuid4().hex}@example.com",
        "full_name": f"Phase Three {role}",
        "password": "StrongPassword123!",
        "role": role,
    }


def auth_headers(role: str) -> tuple[dict[str, str], dict[str, str]]:
    payload = user_payload(role)
    assert client.post("/api/auth/register", json=payload).status_code == 201
    response = client.post(
        "/api/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}, payload


def create_questionnaire_version() -> str:
    with SessionLocal() as db:
        questionnaire = Questionnaire(name=f"P3-{uuid4().hex}")
        db.add(questionnaire)
        db.flush()
        version = QuestionnaireVersion(
            questionnaire_id=questionnaire.id,
            version_number=1,
            title=f"P3-{uuid4().hex}",
        )
        db.add(version)
        db.commit()
        return version.id


def create_patient(headers: dict[str, str], name: str = "Anil Kumar"):
    response = client.post(
        "/api/patients",
        headers=headers,
        json={
            "name": name,
            "date_of_birth": "2001-05-15",
            "gender": "Male",
            "phone": "9876543210",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_doctor_and_student_can_create_patients_and_created_by_is_jwt_user():
    doctor_headers, doctor = auth_headers("DOCTOR")
    student_headers, student = auth_headers("STUDENT")

    doctor_patient = create_patient(doctor_headers, "Doctor Patient")
    student_patient = create_patient(student_headers, "Student Patient")

    with SessionLocal() as db:
        doctor_user = db.query(User).filter(User.email == doctor["email"]).one()
        student_user = db.query(User).filter(User.email == student["email"]).one()
        assert db.get(Patient, doctor_patient["id"]).created_by == doctor_user.id
        assert db.get(Patient, student_patient["id"]).created_by == student_user.id


def test_patient_and_unauthenticated_users_cannot_create_patient():
    patient_headers, _ = auth_headers("PATIENT")
    denied = client.post(
        "/api/patients",
        headers=patient_headers,
        json={"name": "Denied Patient"},
    )
    assert denied.status_code == 403

    unauthenticated = client.post("/api/patients", json={"name": "Denied Patient"})
    assert unauthenticated.status_code == 401


def test_get_patient_search_filters_and_missing_patient():
    headers, _ = auth_headers("DOCTOR")
    patient = create_patient(headers)

    assert client.get(f"/api/patients/{patient['id']}", headers=headers).status_code == 200
    assert client.get("/api/patients?name=Anil", headers=headers).json()[0]["id"] == patient["id"]
    assert client.get("/api/patients?phone=9876543210", headers=headers).json()[0]["id"] == patient["id"]
    assert client.get("/api/patients?date_of_birth=2001-05-15", headers=headers).json()[0]["id"] == patient["id"]
    combined = client.get(
        "/api/patients?name=Anil&phone=9876543210&date_of_birth=2001-05-15",
        headers=headers,
    )
    assert combined.status_code == 200
    assert combined.json()[0]["id"] == patient["id"]

    missing = client.get(f"/api/patients/{uuid4()}", headers=headers)
    assert missing.status_code == 404


def test_invalid_patient_input_is_rejected():
    headers, _ = auth_headers("DOCTOR")
    response = client.post(
        "/api/patients",
        headers=headers,
        json={"name": "", "created_by": "attacker"},
    )
    assert response.status_code == 422


def test_doctor_and_student_can_create_assessment_for_existing_patient():
    doctor_headers, doctor = auth_headers("DOCTOR")
    student_headers, student = auth_headers("STUDENT")
    patient = create_patient(doctor_headers)
    version_id = create_questionnaire_version()

    doctor_assessment = client.post(
        "/api/assessments",
        headers=doctor_headers,
        json={"patient_id": patient["id"], "questionnaire_version_id": version_id},
    )
    student_assessment = client.post(
        "/api/assessments",
        headers=student_headers,
        json={"patient_id": patient["id"], "questionnaire_version_id": version_id},
    )
    assert doctor_assessment.status_code == 201
    assert student_assessment.status_code == 201
    assert doctor_assessment.json()["status"] == "IN_PROGRESS"
    assert doctor_assessment.json()["practitioner_id"] != student_assessment.json()["practitioner_id"]

    with SessionLocal() as db:
        doctor_user = db.query(User).filter(User.email == doctor["email"]).one()
        student_user = db.query(User).filter(User.email == student["email"]).one()
        assert doctor_assessment.json()["practitioner_id"] == doctor_user.id
        assert student_assessment.json()["practitioner_id"] == student_user.id


def test_patient_unauthenticated_and_client_practitioner_are_rejected():
    doctor_headers, _ = auth_headers("DOCTOR")
    patient_headers, _ = auth_headers("PATIENT")
    patient = create_patient(doctor_headers)
    version_id = create_questionnaire_version()

    patient_response = client.post(
        "/api/assessments",
        headers=patient_headers,
        json={"patient_id": patient["id"], "questionnaire_version_id": version_id},
    )
    assert patient_response.status_code == 403
    assert client.post(
        "/api/assessments",
        json={"patient_id": patient["id"], "questionnaire_version_id": version_id},
    ).status_code == 401

    forged = client.post(
        "/api/assessments",
        headers=doctor_headers,
        json={
            "patient_id": patient["id"],
            "questionnaire_version_id": version_id,
            "practitioner_id": str(uuid4()),
        },
    )
    assert forged.status_code == 422


def test_assessment_foreign_keys_and_history():
    headers, _ = auth_headers("DOCTOR")
    patient = create_patient(headers)
    version_id = create_questionnaire_version()

    missing_patient = client.post(
        "/api/assessments",
        headers=headers,
        json={"patient_id": str(uuid4()), "questionnaire_version_id": version_id},
    )
    assert missing_patient.status_code == 404

    missing_version = client.post(
        "/api/assessments",
        headers=headers,
        json={"patient_id": patient["id"], "questionnaire_version_id": str(uuid4())},
    )
    assert missing_version.status_code == 404

    created = client.post(
        "/api/assessments",
        headers=headers,
        json={"patient_id": patient["id"], "questionnaire_version_id": version_id},
    )
    assert created.status_code == 201
    history = client.get(f"/api/patients/{patient['id']}/assessments", headers=headers)
    assert history.status_code == 200
    assert history.json()[0]["id"] == created.json()["id"]


def test_patient_cannot_view_unrestricted_patient_or_assessment_data():
    doctor_headers, _ = auth_headers("DOCTOR")
    patient_headers, _ = auth_headers("PATIENT")
    patient = create_patient(doctor_headers)

    assert client.get(f"/api/patients/{patient['id']}", headers=patient_headers).status_code == 403
    assert client.get(f"/api/patients/{patient['id']}/assessments", headers=patient_headers).status_code == 403
