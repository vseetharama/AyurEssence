from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.database.session import SessionLocal
from app.main import app
from app.models.assessment import Assessment
from app.models.assessment_response import AssessmentResponse
from app.models.patient import Patient
from app.models.question import Question
from app.models.question_option import QuestionOption
from app.models.questionnaire import Questionnaire
from app.models.questionnaire_version import QuestionnaireVersion
from app.models.user import User

client = TestClient(app)
TEST_EMAIL_PREFIX = "phase4-test-"
QUESTIONNAIRE_PREFIX = "P4-"


@pytest.fixture(autouse=True)
def clean_phase4_data():
    cleanup_phase4_data()
    yield
    cleanup_phase4_data()


def cleanup_phase4_data() -> None:
    with SessionLocal() as db:
        questionnaire_ids = select(Questionnaire.id).where(
            Questionnaire.name.like(f"{QUESTIONNAIRE_PREFIX}%")
        )
        version_ids = select(QuestionnaireVersion.id).where(
            QuestionnaireVersion.questionnaire_id.in_(questionnaire_ids)
        )
        question_ids = select(Question.id).where(
            Question.questionnaire_version_id.in_(version_ids)
        )
        user_ids = select(User.id).where(User.email.like(f"{TEST_EMAIL_PREFIX}%"))
        patient_ids = select(Patient.id).where(Patient.created_by.in_(user_ids))
        db.execute(delete(AssessmentResponse).where(
            AssessmentResponse.assessment_id.in_(
                select(Assessment.id).where(Assessment.patient_id.in_(patient_ids))
            )
        ))
        db.execute(delete(Assessment).where(Assessment.patient_id.in_(patient_ids)))
        db.execute(delete(Patient).where(Patient.created_by.in_(user_ids)))
        db.execute(delete(QuestionOption).where(QuestionOption.question_id.in_(question_ids)))
        db.execute(delete(Question).where(Question.questionnaire_version_id.in_(version_ids)))
        db.execute(delete(QuestionnaireVersion).where(QuestionnaireVersion.questionnaire_id.in_(questionnaire_ids)))
        db.execute(delete(Questionnaire).where(Questionnaire.name.like(f"{QUESTIONNAIRE_PREFIX}%")))
        db.execute(delete(User).where(User.email.like(f"{TEST_EMAIL_PREFIX}%")))
        db.commit()


def user_payload(role: str) -> dict[str, str]:
    return {
        "email": f"{TEST_EMAIL_PREFIX}{uuid4().hex}@example.com",
        "full_name": f"Phase Four {role}",
        "password": "StrongPassword123!",
        "role": role,
    }


def auth_headers(role: str) -> tuple[dict[str, str], dict[str, str]]:
    payload = user_payload(role)
    registration = client.post("/api/auth/register", json=payload)
    assert registration.status_code == 201, registration.text
    login = client.post(
        "/api/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}, payload


def create_questionnaire() -> dict[str, object]:
    with SessionLocal() as db:
        questionnaire = Questionnaire(
            name=f"{QUESTIONNAIRE_PREFIX}{uuid4().hex}",
            description="Phase 4 test questionnaire",
        )
        db.add(questionnaire)
        db.flush()
        version_one = QuestionnaireVersion(
            questionnaire_id=questionnaire.id,
            version_number=1,
            title=f"{QUESTIONNAIRE_PREFIX}Version One",
        )
        version_two = QuestionnaireVersion(
            questionnaire_id=questionnaire.id,
            version_number=2,
            title=f"{QUESTIONNAIRE_PREFIX}Version Two",
        )
        db.add_all([version_one, version_two])
        db.flush()
        first = Question(
            questionnaire_version_id=version_one.id,
            question_text="Second question",
            question_type="single_choice",
            is_required=True,
            sort_order=2,
        )
        second = Question(
            questionnaire_version_id=version_one.id,
            question_text="First question",
            question_type="single_choice",
            is_required=True,
            sort_order=1,
        )
        other_version_question = Question(
            questionnaire_version_id=version_two.id,
            question_text="Other version question",
            question_type="single_choice",
            is_required=True,
            sort_order=1,
        )
        db.add_all([first, second, other_version_question])
        db.flush()
        first_option = QuestionOption(
            question_id=first.id,
            option_text="Second option",
            vata_score=1,
            sort_order=1,
        )
        first_updated_option = QuestionOption(
            question_id=first.id,
            option_text="Updated second option",
            pitta_score=1,
            sort_order=2,
        )
        second_option = QuestionOption(
            question_id=second.id,
            option_text="First option",
            pitta_score=1,
            sort_order=1,
        )
        other_option = QuestionOption(
            question_id=other_version_question.id,
            option_text="Other option",
            kapha_score=1,
            sort_order=1,
        )
        db.add_all([first_option, first_updated_option, second_option, other_option])
        db.commit()
        return {
            "id": questionnaire.id,
            "version_one": version_one.id,
            "version_two": version_two.id,
            "first_question": first.id,
            "second_question": second.id,
            "other_question": other_version_question.id,
            "first_option": first_option.id,
            "first_updated_option": first_updated_option.id,
            "second_option": second_option.id,
            "other_option": other_option.id,
        }


def create_assessment(headers: dict[str, str], version_id: str) -> dict[str, object]:
    patient = client.post(
        "/api/patients",
        headers=headers,
        json={"name": "Phase Four Patient"},
    )
    assert patient.status_code == 201, patient.text
    assessment = client.post(
        "/api/assessments",
        headers=headers,
        json={
            "patient_id": patient.json()["id"],
            "questionnaire_version_id": version_id,
        },
    )
    assert assessment.status_code == 201, assessment.text
    return assessment.json()


def test_doctor_and_student_can_retrieve_questionnaire_without_scores():
    questionnaire = create_questionnaire()
    doctor_headers, _ = auth_headers("DOCTOR")
    student_headers, _ = auth_headers("STUDENT")

    doctor_response = client.get(
        f"/api/questionnaires/{questionnaire['id']}", headers=doctor_headers
    )
    student_response = client.get(
        f"/api/questionnaires/{questionnaire['id']}", headers=student_headers
    )
    assert doctor_response.status_code == 200
    assert student_response.status_code == 200
    body = doctor_response.json()
    assert [item["version_number"] for item in body["versions"]] == [1, 2]
    assert [item["question_order"] for item in body["versions"][0]["questions"]] == [1, 2]
    assert body["versions"][0]["questions"][0]["options"][0]["option_text"] == "First option"
    assert "vata_score" not in str(body)
    assert "pitta_score" not in str(body)
    assert "kapha_score" not in str(body)


def test_questionnaire_requires_staff_authentication_and_existing_id():
    questionnaire = create_questionnaire()
    patient_headers, _ = auth_headers("PATIENT")

    assert client.get(f"/api/questionnaires/{questionnaire['id']}").status_code == 401
    assert client.get(
        f"/api/questionnaires/{questionnaire['id']}", headers=patient_headers
    ).status_code == 403
    doctor_headers, _ = auth_headers("DOCTOR")
    assert client.get(
        f"/api/questionnaires/{uuid4()}", headers=doctor_headers
    ).status_code == 404


def test_doctor_and_student_can_submit_valid_responses():
    questionnaire = create_questionnaire()
    doctor_headers, _ = auth_headers("DOCTOR")
    student_headers, _ = auth_headers("STUDENT")
    assessment = create_assessment(doctor_headers, questionnaire["version_one"])

    doctor_response = client.post(
        f"/api/assessments/{assessment['id']}/responses",
        headers=doctor_headers,
        json={"responses": [{"question_id": questionnaire["first_question"], "option_id": questionnaire["first_option"]}]},
    )
    student_response = client.post(
        f"/api/assessments/{assessment['id']}/responses",
        headers=student_headers,
        json={"responses": [{"question_id": questionnaire["second_question"], "option_id": questionnaire["second_option"]}]},
    )
    assert doctor_response.status_code == 200
    assert student_response.status_code == 200
    with SessionLocal() as db:
        assert db.query(AssessmentResponse).filter(
            AssessmentResponse.assessment_id == assessment["id"]
        ).count() == 2


def test_response_authentication_and_role_restrictions():
    questionnaire = create_questionnaire()
    doctor_headers, _ = auth_headers("DOCTOR")
    patient_headers, _ = auth_headers("PATIENT")
    assessment = create_assessment(doctor_headers, questionnaire["version_one"])
    payload = {"responses": [{"question_id": questionnaire["first_question"], "option_id": questionnaire["first_option"]}]}

    assert client.post(f"/api/assessments/{assessment['id']}/responses", json=payload).status_code == 401
    assert client.post(
        f"/api/assessments/{assessment['id']}/responses", headers=patient_headers, json=payload
    ).status_code == 403


def test_response_relationship_validation():
    questionnaire = create_questionnaire()
    doctor_headers, _ = auth_headers("DOCTOR")
    assessment = create_assessment(doctor_headers, questionnaire["version_one"])
    base = f"/api/assessments/{assessment['id']}/responses"

    cases = [
        ({"question_id": str(uuid4()), "option_id": questionnaire["first_option"]}, "Question not found."),
        ({"question_id": questionnaire["other_question"], "option_id": questionnaire["other_option"]}, "Question does not belong"),
        ({"question_id": questionnaire["first_question"], "option_id": str(uuid4())}, "Option not found."),
        ({"question_id": questionnaire["first_question"], "option_id": questionnaire["other_option"]}, "Option does not belong"),
    ]
    for response, detail in cases:
        result = client.post(base, headers=doctor_headers, json={"responses": [response]})
        assert result.status_code in {400, 404}
        assert detail in result.json()["detail"]

    assert client.post(
        f"/api/assessments/{uuid4()}/responses",
        headers=doctor_headers,
        json={"responses": [{"question_id": questionnaire["first_question"], "option_id": questionnaire["first_option"]}]},
    ).status_code == 404


def test_duplicate_response_is_updated_not_inserted():
    questionnaire = create_questionnaire()
    doctor_headers, _ = auth_headers("DOCTOR")
    assessment = create_assessment(doctor_headers, questionnaire["version_one"])
    path = f"/api/assessments/{assessment['id']}/responses"
    first = {"responses": [{"question_id": questionnaire["first_question"], "option_id": questionnaire["first_option"]}]}
    second = {"responses": [{"question_id": questionnaire["first_question"], "option_id": questionnaire["first_updated_option"]}]}

    assert client.post(path, headers=doctor_headers, json=first).status_code == 200
    updated = client.post(path, headers=doctor_headers, json=second)
    assert updated.status_code == 200
    assert updated.json()[0]["option_id"] == questionnaire["first_updated_option"]
    with SessionLocal() as db:
        rows = db.query(AssessmentResponse).filter(
            AssessmentResponse.assessment_id == assessment["id"],
            AssessmentResponse.question_id == questionnaire["first_question"],
        ).all()
        assert len(rows) == 1
        assert rows[0].option_id == questionnaire["first_updated_option"]


def test_finalized_assessment_cannot_be_modified():
    questionnaire = create_questionnaire()
    doctor_headers, _ = auth_headers("DOCTOR")
    assessment = create_assessment(doctor_headers, questionnaire["version_one"])
    with SessionLocal() as db:
        db.get(Assessment, assessment["id"]).status = "FINALIZED"
        db.commit()

    response = client.post(
        f"/api/assessments/{assessment['id']}/responses",
        headers=doctor_headers,
        json={"responses": [{"question_id": questionnaire["first_question"], "option_id": questionnaire["first_option"]}]},
    )
    assert response.status_code == 409
