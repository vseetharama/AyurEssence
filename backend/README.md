# AyurEssence Backend

Backend API for the AyurEssence Ayurvedic Prakriti Assessment Platform.

## Technology Stack

* FastAPI
* Python
* SQLite
* SQLAlchemy
* JWT Authentication
* Passlib
* Bcrypt
* Uvicorn

## Current APIs

### Basic APIs

* `GET /` — Backend status
* `GET /health` — Health check

### Module 1 – Authentication & User Management

* `POST /auth/register` — Register a new user
* `POST /auth/login` — Login and generate JWT token
* `GET /auth/me` — Get the currently authenticated user

## Authentication Flow

```text
Register
   ↓
Password Hashing
   ↓
User Stored in Database
   ↓
Login
   ↓
Credentials Verified
   ↓
JWT Token Generated
   ↓
Protected API Access
```

## Database

SQLite is currently used for the backend.

The User model contains:

* ID
* Username
* Password Hash
* Role

## Testing

The APIs have been tested using:

* FastAPI Swagger UI
* Postman

Authentication test cases:

* Registration — `201 Created`
* Login — `200 OK`
* Valid JWT — `200 OK`
* Invalid JWT — `401 Unauthorized`

## Running the Backend

Activate the virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
```

Start the server:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```
