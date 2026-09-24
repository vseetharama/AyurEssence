from __future__ import annotations

import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.database.session import SessionLocal
from app.main import app
from app.models.assessment import Assessment
from app.models.assessment_response import AssessmentResponse
from app.models.dosha_result import DoshaResult
from app.models.methodology import Methodology
from app.models.observation import PractitionerObservation
from app.models.patient import Patient
from app.models.question import Question
from app.models.question_option import QuestionOption
from app.models.questionnaire import Questionnaire
from app.models.questionnaire_version import QuestionnaireVersion
from app.models.reference import Reference
from app.models.user import User
from app.services.prakriti_service import CalculationValidationError, _classify

client = TestClient(app)
EMAIL_PREFIX = "phase5-test-"
NAME_PREFIX = "P5-"


@pytest.fixture(autouse=True)
def clean_phase5_data():
    cleanup_phase5_data()
    yield
    cleanup_phase5_data()


def cleanup_phase5_data() -> None:
    with SessionLocal() as db:
        user_ids = select(User.id).where(User.email.like(f"{EMAIL_PREFIX}%"))
        patient_ids = select(Patient.id).where(Patient.created_by.in_(user_ids))
        assessment_ids = select(Assessment.id).where(Assessment.patient_id.in_(patient_ids))
        questionnaire_ids = select(Questionnaire.id).where(Questionnaire.name.like(f"{NAME_PREFIX}%"))
        version_ids = select(QuestionnaireVersion.id).where(QuestionnaireVersion.questionnaire_id.in_(questionnaire_ids))
        question_ids = select(Question.id).where(Question.questionnaire_version_id.in_(version_ids))
        db.execute(delete(DoshaResult).where(DoshaResult.assessment_id.in_(assessment_ids)))
        db.execute(delete(PractitionerObservation).where(PractitionerObservation.assessment_id.in_(assessment_ids)))
        db.execute(delete(AssessmentResponse).where(AssessmentResponse.assessment_id.in_(assessment_ids)))
        db.execute(delete(Assessment).where(Assessment.id.in_(assessment_ids)))
        db.execute(delete(Patient).where(Patient.id.in_(patient_ids)))
        db.execute(delete(QuestionOption).where(QuestionOption.question_id.in_(question_ids)))
        db.execute(delete(Question).where(Question.id.in_(question_ids)))
        db.execute(delete(QuestionnaireVersion).where(QuestionnaireVersion.id.in_(version_ids)))
        db.execute(delete(Questionnaire).where(Questionnaire.id.in_(questionnaire_ids)))
        db.execute(delete(Reference).where(Reference.title.like(f"{NAME_PREFIX}%")))
        db.execute(delete(Methodology).where(Methodology.name.like(f"{NAME_PREFIX}%")))
        db.execute(delete(User).where(User.id.in_(user_ids)))
        db.commit()


def auth_headers(role: str) -> tuple[dict[str, str], str]:
    payload = {
        "email": f"{EMAIL_PREFIX}{uuid4().hex}@example.com",
        "full_name": f"Phase Five {role}",
        "password": "StrongPassword123!",
        "role": role,
    }
    assert client.post("/api/auth/register", json=payload).status_code == 201
    login = client.post("/api/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}, login.json()["user"]["id"]


def create_assessment(headers: dict[str, str]) -> tuple[str, dict[str, str]]:
    with SessionLocal() as db:
        questionnaire = Questionnaire(name=f"{NAME_PREFIX}{uuid4().hex}")
        db.add(questionnaire)
        db.flush()
        version = QuestionnaireVersion(questionnaire_id=questionnaire.id, version_number=1, title=f"{NAME_PREFIX}Version")
        db.add(version)
        db.flush()
        question = Question(questionnaire_version_id=version.id, question_text="Trait", is_required=True, sort_order=1)
        db.add(question)
        db.flush()
        option = QuestionOption(question_id=question.id, option_text="Configured answer", sort_order=1)
        db.add(option)
        db.commit()
        version_id, question_id, option_id = version.id, question.id, option.id

    patient = client.post("/api/patients", headers=headers, json={"name": "Phase Five Patient"})
    assert patient.status_code == 201, patient.text
    assessment = client.post(
        "/api/assessments",
        headers=headers,
        json={"patient_id": patient.json()["id"], "questionnaire_version_id": version_id},
    )
    assert assessment.status_code == 201, assessment.text
    return assessment.json()["id"], {"question_id": question_id, "option_id": option_id}


def seed_configured_methodology(option_id: str) -> str:
    configuration = {
        "calculation_enabled": True,
        "vata_predictors": 31,
        "pitta_predictors": 29,
        "kapha_predictors": 32,
        "question_option_mappings": {
            option_id: {"vata": 2, "pitta": 1, "kapha": 0},
        },
        "classification_rules": {
            "method": "ccras_pas_based",
            "samadoshaja": {"minimum_percentage": 30, "maximum_percentage": 34, "inclusive": True},
            "ekadoshaja": {"dominant_percentage_greater_than": 50, "margin_over_second_greater_than": 25},
            "dwandaja": {"dominant_first": True, "equal_percentage_tie_breaker": "raw_score"},
            "classification_source_status": "verified",
        },
    }
    with SessionLocal() as db:
        methodology = Methodology(
            name=f"{NAME_PREFIX}Configured Methodology",
            version="test",
            scoring_rules=json.dumps(configuration),
        )
        db.add(methodology)
        db.commit()
        return methodology.id


def test_doctor_can_add_observation_and_patient_cannot():
    doctor_headers, doctor_id = auth_headers("DOCTOR")
    assessment_id, _ = create_assessment(doctor_headers)
    response = client.post(
        f"/api/assessments/{assessment_id}/observations",
        headers=doctor_headers,
        json={"observation_text": "Observed during assessment."},
    )
    assert response.status_code == 201
    assert response.json()["practitioner_id"] == doctor_id
    with SessionLocal() as db:
        assert db.query(PractitionerObservation).filter_by(assessment_id=assessment_id).count() == 1

    patient_headers, _ = auth_headers("PATIENT")
    denied = client.post(
        f"/api/assessments/{assessment_id}/observations",
        headers=patient_headers,
        json={"observation_text": "Not allowed."},
    )
    assert denied.status_code == 403


def test_observation_requires_authentication_and_nonempty_text():
    doctor_headers, _ = auth_headers("DOCTOR")
    assessment_id, _ = create_assessment(doctor_headers)
    assert client.post(
        f"/api/assessments/{assessment_id}/observations",
        json={"observation_text": "Observation"},
    ).status_code == 401
    assert client.post(
        f"/api/assessments/{assessment_id}/observations",
        headers=doctor_headers,
        json={"observation_text": "   "},
    ).status_code == 422


def test_calculation_rejects_missing_required_response():
    doctor_headers, _ = auth_headers("DOCTOR")
    assessment_id, _ = create_assessment(doctor_headers)
    with SessionLocal() as db:
        methodology = Methodology(name=f"{NAME_PREFIX}Missing Response", version="test", scoring_rules="{}")
        db.add(methodology)
        db.commit()
    response = client.post(f"/api/assessments/{assessment_id}/calculate", headers=doctor_headers)
    assert response.status_code == 409


def test_configured_calculation_persists_and_recalculation_updates_one_result(monkeypatch):
    doctor_headers, _ = auth_headers("DOCTOR")
    assessment_id, answer = create_assessment(doctor_headers)
    methodology_id = seed_configured_methodology(answer["option_id"])
    monkeypatch.setattr(
        "app.routes.calculation.METHODOLOGY_NAME",
        f"{NAME_PREFIX}Configured Methodology",
    )
    response_path = f"/api/assessments/{assessment_id}/responses"
    assert client.post(
        response_path,
        headers=doctor_headers,
        json={"responses": [answer]},
    ).status_code == 200

    first = client.post(f"/api/assessments/{assessment_id}/calculate", headers=doctor_headers)
    second = client.post(f"/api/assessments/{assessment_id}/calculate", headers=doctor_headers)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["methodology_id"] == methodology_id
    assert 0 <= first.json()["vata_percentage"] <= 100
    assert 0 <= first.json()["pitta_percentage"] <= 100
    assert 0 <= first.json()["kapha_percentage"] <= 100
    assert second.json()["id"] == first.json()["id"]
    with SessionLocal() as db:
        assert db.query(DoshaResult).filter_by(assessment_id=assessment_id).count() == 1


def test_calculation_requires_assessment_owner_and_finalized_is_blocked(monkeypatch):
    doctor_headers, _ = auth_headers("DOCTOR")
    other_doctor_headers, _ = auth_headers("DOCTOR")
    assessment_id, answer = create_assessment(doctor_headers)
    seed_configured_methodology(answer["option_id"])
    monkeypatch.setattr(
        "app.routes.calculation.METHODOLOGY_NAME",
        f"{NAME_PREFIX}Configured Methodology",
    )
    assert client.post(
        f"/api/assessments/{assessment_id}/calculate", headers=other_doctor_headers
    ).status_code == 403
    with SessionLocal() as db:
        db.get(Assessment, assessment_id).status = "FINALIZED"
        db.commit()
    assert client.post(
        f"/api/assessments/{assessment_id}/calculate", headers=doctor_headers
    ).status_code == 409


CLASSIFICATION_RULES = {
    "method": "ccras_pas_based",
    "samadoshaja": {"minimum_percentage": 30, "maximum_percentage": 34, "inclusive": True},
    "ekadoshaja": {"dominant_percentage_greater_than": 50, "margin_over_second_greater_than": 25},
    "dwandaja": {"dominant_first": True, "equal_percentage_tie_breaker": "raw_score"},
    "classification_source_status": "verified",
}


def test_classification_boundaries_and_raw_score_tie_breaker():
    assert _classify({"vata": 60.01, "pitta": 20, "kapha": 19.99}, {"vata": 5, "pitta": 2, "kapha": 3}, CLASSIFICATION_RULES) == "EKA-DOSHAJA:VATA"
    assert _classify({"vata": 30, "pitta": 34, "kapha": 33}, {"vata": 3, "pitta": 4, "kapha": 3}, CLASSIFICATION_RULES) == "SAMADOSHAJA"
    assert _classify({"vata": 45, "pitta": 45, "kapha": 10}, {"vata": 4, "pitta": 5, "kapha": 1}, CLASSIFICATION_RULES) == "SANSARGAJA:PITTA+VATA"


def test_classification_rejects_unverified_source_status():
    rules = {**CLASSIFICATION_RULES, "classification_source_status": "published boundary table requires verification"}
    with pytest.raises(CalculationValidationError):
        from app.services.prakriti_service import _validate_configuration

        _validate_configuration({
            "calculation_enabled": True,
            "vata_predictors": 27,
            "pitta_predictors": 25,
            "kapha_predictors": 27,
            "question_option_mappings": {"option": {"vata": 1, "pitta": 0, "kapha": 0}},
            "classification_rules": rules,
        })
