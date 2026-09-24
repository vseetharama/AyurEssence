from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.database.session import SessionLocal
from app.main import app
from app.models.assessment import Assessment
from app.models.assessment_response import AssessmentResponse
from app.models.dosha_result import DoshaResult
from app.models.observation import PractitionerObservation
from app.models.patient import Patient
from app.models.question import Question
from app.models.question_option import QuestionOption
from app.models.questionnaire import Questionnaire
from app.models.questionnaire_version import QuestionnaireVersion
from app.models.user import User

client = TestClient(app)
EMAIL_PREFIX = "phase6-test-"
NAME_PREFIX = "P6-"


@pytest.fixture(autouse=True)
def clean_phase6_data():
    cleanup_phase6_data()
    yield
    cleanup_phase6_data()


def cleanup_phase6_data() -> None:
    with SessionLocal() as db:
        user_ids = select(User.id).where(User.email.like(f"{EMAIL_PREFIX}%"))
        patient_ids = select(Patient.id).where(Patient.created_by.in_(user_ids))
        assessment_ids = select(Assessment.id).where(Assessment.patient_id.in_(patient_ids))
        db.execute(delete(DoshaResult).where(DoshaResult.assessment_id.in_(assessment_ids)))
        db.execute(delete(PractitionerObservation).where(PractitionerObservation.assessment_id.in_(assessment_ids)))
        db.execute(delete(AssessmentResponse).where(AssessmentResponse.assessment_id.in_(assessment_ids)))
        db.execute(delete(Assessment).where(Assessment.id.in_(assessment_ids)))
        db.execute(delete(Patient).where(Patient.id.in_(patient_ids)))
        question_ids = select(Question.id).where(Question.questionnaire_version_id.in_(select(QuestionnaireVersion.id).where(QuestionnaireVersion.title.like(f"{NAME_PREFIX}%"))))
        db.execute(delete(QuestionOption).where(QuestionOption.question_id.in_(question_ids)))
        db.execute(delete(Question).where(Question.id.in_(question_ids)))
        db.execute(delete(QuestionnaireVersion).where(QuestionnaireVersion.title.like(f"{NAME_PREFIX}%")))
        db.execute(delete(Questionnaire).where(Questionnaire.name.like(f"{NAME_PREFIX}%")))
        db.execute(delete(User).where(User.email.like(f"{EMAIL_PREFIX}%")))
        db.commit()


def auth_headers(role: str) -> tuple[dict[str, str], str]:
    payload = {
        "email": f"{EMAIL_PREFIX}{uuid4().hex}@example.com",
        "full_name": f"Phase Six {role}",
        "password": "StrongPassword123!",
        "role": role,
    }
    assert client.post("/api/auth/register", json=payload).status_code == 201
    login = client.post("/api/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}, login.json()["user"]["id"]


def create_questionnaire_version(title: str | None = None) -> dict[str, str]:
    with SessionLocal() as db:
        questionnaire = Questionnaire(name=f"{NAME_PREFIX}{uuid4().hex}")
        db.add(questionnaire)
        db.flush()
        version = QuestionnaireVersion(questionnaire_id=questionnaire.id, version_number=1, title=title or f"{NAME_PREFIX}{uuid4().hex}")
        db.add(version)
        db.flush()
        required_question = Question(questionnaire_version_id=version.id, question_text="Required trait", is_required=True, sort_order=1)
        db.add(required_question)
        db.flush()
        required_option = QuestionOption(question_id=required_question.id, option_text="Required answer", sort_order=1)
        db.add(required_option)
        db.commit()
    return {"question_id": required_question.id, "option_id": required_option.id, "version_id": version.id}


def create_patient(headers: dict[str, str], name: str = "Phase Six Patient") -> dict[str, str]:
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


def build_assessment(headers: dict[str, str], patient_id: str, version_id: str) -> str:
    response = client.post(
        "/api/assessments",
        headers=headers,
        json={"patient_id": patient_id, "questionnaire_version_id": version_id},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def add_observation(headers: dict[str, str], assessment_id: str) -> None:
    response = client.post(
        f"/api/assessments/{assessment_id}/observations",
        headers=headers,
        json={"observation_text": "Practitioner observation for Phase 6."},
    )
    assert response.status_code == 201, response.text


def test_unauthenticated_finalization_and_report_require_authentication():
    doctor_headers, _ = auth_headers("DOCTOR")
    patient = create_patient(doctor_headers)
    questionnaire = create_questionnaire_version()
    assessment_id = build_assessment(doctor_headers, patient["id"], questionnaire["version_id"])

    assert client.post(f"/api/assessments/{assessment_id}/finalize").status_code == 401
    assert client.get(f"/api/assessments/{assessment_id}/report").status_code == 401


def test_doctor_can_finalize_when_required_conditions_are_met():
    doctor_headers, _ = auth_headers("DOCTOR")
    patient = create_patient(doctor_headers)
    questionnaire = create_questionnaire_version()
    assessment_id = build_assessment(doctor_headers, patient["id"], questionnaire["version_id"])

    response = client.post(
        f"/api/assessments/{assessment_id}/responses",
        headers=doctor_headers,
        json={"responses": [{"question_id": questionnaire["question_id"], "option_id": questionnaire["option_id"]}]},
    )
    assert response.status_code == 200

    add_observation(doctor_headers, assessment_id)

    finalize = client.post(f"/api/assessments/{assessment_id}/finalize", headers=doctor_headers)
    assert finalize.status_code == 200, finalize.text
    payload = finalize.json()
    assert payload["status"] == "FINALIZED"
    assert payload["completed_at"] is not None

    with SessionLocal() as db:
        assessment = db.get(Assessment, assessment_id)
        assert assessment is not None
        assert assessment.status == "FINALIZED"
        assert assessment.finalized_at is not None


def test_student_patient_and_unrelated_doctor_cannot_finalize():
    doctor_headers, _ = auth_headers("DOCTOR")
    student_headers, _ = auth_headers("STUDENT")
    patient_headers, _ = auth_headers("PATIENT")
    other_doctor_headers, _ = auth_headers("DOCTOR")

    patient = create_patient(doctor_headers)
    questionnaire = create_questionnaire_version()
    assessment_id = build_assessment(doctor_headers, patient["id"], questionnaire["version_id"])

    client.post(
        f"/api/assessments/{assessment_id}/responses",
        headers=doctor_headers,
        json={"responses": [{"question_id": questionnaire["question_id"], "option_id": questionnaire["option_id"]}]},
    )

    assert client.post(f"/api/assessments/{assessment_id}/finalize", headers=student_headers).status_code == 403
    assert client.post(f"/api/assessments/{assessment_id}/finalize", headers=patient_headers).status_code == 403
    assert client.post(f"/api/assessments/{assessment_id}/finalize", headers=other_doctor_headers).status_code == 403


def test_finalize_validates_missing_assessment_state_and_response_requirements():
    doctor_headers, _ = auth_headers("DOCTOR")
    patient = create_patient(doctor_headers)
    questionnaire = create_questionnaire_version()
    assessment_id = build_assessment(doctor_headers, patient["id"], questionnaire["version_id"])

    missing = client.post(f"/api/assessments/{uuid4()}/finalize", headers=doctor_headers)
    assert missing.status_code == 404

    missing_required = client.post(f"/api/assessments/{assessment_id}/finalize", headers=doctor_headers)
    assert missing_required.status_code == 409

    client.post(
        f"/api/assessments/{assessment_id}/responses",
        headers=doctor_headers,
        json={"responses": [{"question_id": questionnaire["question_id"], "option_id": questionnaire["option_id"]}]},
    )
    missing_observation = client.post(f"/api/assessments/{assessment_id}/finalize", headers=doctor_headers)
    assert missing_observation.status_code == 409
    assert missing_observation.json()["detail"] == "Practitioner observation is required before finalizing the assessment."

    add_observation(doctor_headers, assessment_id)
    first = client.post(f"/api/assessments/{assessment_id}/finalize", headers=doctor_headers)
    assert first.status_code == 200

    second = client.post(f"/api/assessments/{assessment_id}/finalize", headers=doctor_headers)
    assert second.status_code == 409

    with SessionLocal() as db:
        db.get(Assessment, assessment_id).status = "IN_PROGRESS"
        db.commit()

    duplicate = client.post(f"/api/assessments/{assessment_id}/finalize", headers=doctor_headers)
    assert duplicate.status_code == 409


def test_finalized_assessment_is_immutable_and_report_is_safe():
    doctor_headers, _ = auth_headers("DOCTOR")
    patient = create_patient(doctor_headers)
    questionnaire = create_questionnaire_version()
    assessment_id = build_assessment(doctor_headers, patient["id"], questionnaire["version_id"])
    client.post(
        f"/api/assessments/{assessment_id}/responses",
        headers=doctor_headers,
        json={"responses": [{"question_id": questionnaire["question_id"], "option_id": questionnaire["option_id"]}]},
    )
    add_observation(doctor_headers, assessment_id)
    finalize = client.post(f"/api/assessments/{assessment_id}/finalize", headers=doctor_headers)
    assert finalize.status_code == 200

    response_result = client.post(
        f"/api/assessments/{assessment_id}/responses",
        headers=doctor_headers,
        json={"responses": [{"question_id": questionnaire["question_id"], "option_id": questionnaire["option_id"]}]},
    )
    assert response_result.status_code == 409

    observation_result = client.post(
        f"/api/assessments/{assessment_id}/observations",
        headers=doctor_headers,
        json={"observation_text": "Should not be allowed after finalization."},
    )
    assert observation_result.status_code == 409

    report = client.get(f"/api/assessments/{assessment_id}/report", headers=doctor_headers)
    assert report.status_code == 200
    body = report.json()
    assert body["patient"]["id"] == patient["id"]
    assert body["assessment"]["status"] == "FINALIZED"
    assert body["questionnaire"]["name"]
    assert body["responses"][0]["question_text"]
    assert body["responses"][0]["selected_option_text"]
    assert body["prakriti_result"]["result_status"] == "UNAVAILABLE"
    assert "diagnosis" not in str(body).lower()
    assert "treatment" not in str(body).lower()


def test_report_rejects_unauthorized_and_nonexistent_assessment():
    doctor_headers, _ = auth_headers("DOCTOR")
    patient_headers, _ = auth_headers("PATIENT")
    patient = create_patient(doctor_headers)
    questionnaire = create_questionnaire_version()
    assessment_id = build_assessment(doctor_headers, patient["id"], questionnaire["version_id"])

    assert client.get(f"/api/assessments/{assessment_id}/report", headers=patient_headers).status_code == 403
    assert client.get(f"/api/assessments/{uuid4()}/report", headers=doctor_headers).status_code == 404


def test_finalized_assessment_history_and_status_are_returned():
    doctor_headers, _ = auth_headers("DOCTOR")
    patient = create_patient(doctor_headers)
    questionnaire = create_questionnaire_version()
    first = build_assessment(doctor_headers, patient["id"], questionnaire["version_id"])
    second = build_assessment(doctor_headers, patient["id"], questionnaire["version_id"])

    client.post(
        f"/api/assessments/{first}/responses",
        headers=doctor_headers,
        json={"responses": [{"question_id": questionnaire["question_id"], "option_id": questionnaire["option_id"]}]},
    )
    add_observation(doctor_headers, first)
    first_finalize = client.post(f"/api/assessments/{first}/finalize", headers=doctor_headers)
    assert first_finalize.status_code == 200

    history = client.get(f"/api/patients/{patient['id']}/assessments", headers=doctor_headers)
    assert history.status_code == 200
    ids = [item["id"] for item in history.json()]
    assert first in ids and second in ids
    statuses = {item["id"]: item["status"] for item in history.json()}
    assert statuses[first] == "FINALIZED"
    assert statuses[second] == "IN_PROGRESS"
    assert len(ids) == len(set(ids))
