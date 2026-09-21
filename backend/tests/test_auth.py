from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.core.dependencies import require_doctor, require_doctor_or_student, require_roles
from app.core.security import create_access_token, decode_access_token
from app.database.session import SessionLocal
from app.main import app
from app.models.user import User

client = TestClient(app)
TEST_EMAIL_PREFIX = "phase2-test-"


@pytest.fixture(autouse=True)
def clean_test_users() -> None:
    with SessionLocal() as db:
        db.execute(delete(User).where(User.email.like(f"{TEST_EMAIL_PREFIX}%")))
        db.commit()
    yield
    with SessionLocal() as db:
        db.execute(delete(User).where(User.email.like(f"{TEST_EMAIL_PREFIX}%")))
        db.commit()


def user_payload(role: str = "PATIENT") -> dict[str, str]:
    return {
        "email": f"{TEST_EMAIL_PREFIX}{uuid4().hex}@example.com",
        "full_name": "Phase Two User",
        "password": "StrongPassword123!",
        "role": role,
    }


def register(payload: dict[str, str]) -> None:
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201, response.text


def login(payload: dict[str, str]):
    return client.post(
        "/api/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )


def test_successful_registration_returns_safe_user() -> None:
    payload = user_payload("PATIENT")
    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == payload["email"].lower()
    assert body["role"] == "PATIENT"
    assert "password_hash" not in body
    assert "password" not in body

    with SessionLocal() as db:
        user = db.query(User).filter(User.email == payload["email"]).one()
        assert user.password_hash != payload["password"]
        assert user.password_hash.startswith("$2b$")


def test_duplicate_email_returns_conflict() -> None:
    payload = user_payload()
    register(payload)

    duplicate = client.post("/api/auth/register", json=payload)
    assert duplicate.status_code == 409


def test_invalid_registration_data_is_rejected() -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "email": "not-an-email",
            "full_name": "A",
            "password": "short",
            "role": "ADMIN",
        },
    )
    assert response.status_code == 422


def test_successful_login_returns_bearer_token() -> None:
    payload = user_payload("DOCTOR")
    register(payload)

    response = login(payload)
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["role"] == "DOCTOR"
    assert "password_hash" not in body["user"]

    claims = decode_access_token(body["access_token"])
    assert claims["sub"] == body["user"]["id"]
    assert claims["role"] == "DOCTOR"


def test_wrong_password_and_nonexistent_user_return_unauthorized() -> None:
    payload = user_payload()
    register(payload)

    wrong_password = client.post(
        "/api/auth/login",
        json={"email": payload["email"], "password": "WrongPassword123!"},
    )
    assert wrong_password.status_code == 401

    nonexistent = client.post(
        "/api/auth/login",
        json={
            "email": f"{TEST_EMAIL_PREFIX}missing@example.com",
            "password": payload["password"],
        },
    )
    assert nonexistent.status_code == 401


def test_invalid_and_expired_jwt_are_rejected() -> None:
    invalid = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid"})
    assert invalid.status_code == 401

    expired_token = create_access_token(
        subject="missing-user",
        role="PATIENT",
        expires_delta=timedelta(seconds=-1),
    )
    expired = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert expired.status_code == 401


def test_authenticated_user_dependency_returns_current_user() -> None:
    payload = user_payload("STUDENT")
    register(payload)
    token = login(payload).json()["access_token"]

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == payload["email"].lower()
    assert response.json()["role"] == "STUDENT"


def test_role_dependencies_allow_only_expected_roles() -> None:
    doctor = User(role="DOCTOR")
    student = User(role="STUDENT")
    patient = User(role="PATIENT")

    assert require_doctor(doctor) is doctor
    assert require_doctor_or_student(student) is student
    assert require_roles("PATIENT")(patient) is patient

    with pytest.raises(HTTPException) as doctor_error:
        require_doctor(patient)
    assert doctor_error.value.status_code == 403

    with pytest.raises(HTTPException) as student_error:
        require_doctor_or_student(patient)
    assert student_error.value.status_code == 403

    with pytest.raises(HTTPException) as patient_error:
        require_roles("PATIENT")(doctor)
    assert patient_error.value.status_code == 403
