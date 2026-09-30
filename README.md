# AyurEssence

**Intelligent Ayurvedic Prakriti Assessment Platform**

A comprehensive full-stack web application for conducting digital Ayurvedic assessments to determine a patient's Prakriti (constitutional type) based on Vata, Pitta, and Kapha doshas. Built with modern web technologies and designed for healthcare practitioners to streamline patient consultations and assessment workflows.

---

## 📋 Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Database Migrations](#database-migrations)
- [API Documentation](#api-documentation)
- [Architecture](#architecture)
- [Workflow](#workflow)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

---

## ✨ Features

### Core Assessment System
- **Digital Questionnaires**: Customizable, versioned questionnaires for Prakriti assessment
- **Response Tracking**: Comprehensive recording of patient responses with option scoring
- **Prakriti Calculation**: Automated dosha scoring using CCRAS PAS-Based methodology
- **Classification**: Three-tier classification system (SAMADOSHAJA, EKA-DOSHAJA, SANSARGAJA)
- **Assessment Reports**: Detailed reports with dosha percentages, observations, and references

### Patient Management
- **Patient Profiles**: Complete patient information management (name, DOB, contact, etc.)
- **Unique Patient Codes**: Auto-generated unique identifiers for patient tracking
- **Assessment History**: Full audit trail of all assessments per patient
- **Search & Filter**: Find patients by name, phone, or date of birth

### Practitioner Features
- **Role-Based Access**: Doctor, Student, and Patient roles with distinct permissions
- **Clinical Observations**: Practitioners can add contextual observations
- **Assessment Workflow**: Guided step-by-step assessment process
- **Finalization Controls**: Validation checks before assessment completion

### Authentication & Security
- **JWT Authentication**: Secure token-based authentication
- **Password Security**: bcrypt-hashed passwords with salt
- **Session Persistence**: Automatic session restoration on page reload
- **Role-Based Access Control**: Endpoint protection based on user roles
- **CORS Configuration**: Secure cross-origin requests

---

## 📁 Project Structure

```
AyurEssence/
├── backend/                          # FastAPI backend application
│   ├── app/
│   │   ├── main.py                  # FastAPI application entry point
│   │   ├── core/
│   │   │   ├── config.py            # Configuration management (Settings class)
│   │   │   ├── security.py          # JWT and password utilities
│   │   │   └── dependencies.py      # Dependency injection utilities
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   │   ├── user.py              # User model (DOCTOR, STUDENT, PATIENT)
│   │   │   ├── patient.py           # Patient profile model
│   │   │   ├── assessment.py        # Assessment session model
│   │   │   ├── questionnaire.py     # Questionnaire template model
│   │   │   ├── question.py          # Individual questions
│   │   │   ├── question_option.py   # Question response options with dosha scores
│   │   │   ├── assessment_response.py # Patient responses to questions
│   │   │   ├── dosha_result.py      # Calculated prakriti results
│   │   │   ├── observation.py       # Practitioner clinical observations
│   │   │   └── ...                  # Additional models
│   │   ├── schemas/                 # Pydantic validation schemas
│   │   │   ├── auth.py              # Authentication request/response schemas
│   │   │   ├── patient.py           # Patient schemas
│   │   │   ├── assessment.py        # Assessment schemas
│   │   │   └── ...                  # Additional schemas
│   │   ├── routes/                  # API endpoint handlers
│   │   │   ├── auth.py              # Authentication endpoints
│   │   │   ├── patients.py          # Patient management endpoints
│   │   │   ├── assessments.py       # Assessment endpoints
│   │   │   ├── questionnaires.py    # Questionnaire endpoints
│   │   │   ├── responses.py         # Response submission endpoints
│   │   │   ├── observations.py      # Observation endpoints
│   │   │   ├── calculation.py       # Dosha calculation endpoints
│   │   │   └── __init__.py
│   │   ├── services/                # Business logic layer
│   │   │   ├── auth_service.py      # Authentication logic
│   │   │   ├── patient_service.py   # Patient management logic
│   │   │   ├── assessment_service.py# Assessment orchestration
│   │   │   ├── prakriti_service.py  # Dosha calculation logic
│   │   │   └── ...                  # Additional services
│   │   ├── database/                # Database initialization & management
│   │   │   ├── session.py           # SQLAlchemy session factory
│   │   │   ├── base.py              # Base model class
│   │   │   ├── init_db.py           # Database initialization
│   │   │   ├── seed_questionnaire.py# Sample data seeding
│   │   │   └── seed_methodology.py  # Scoring methodology seeding
│   │   └── auth/                    # Authentication handlers
│   ├── alembic/                     # Database migrations
│   │   ├── versions/                # Migration scripts
│   │   └── env.py                   # Alembic configuration
│   ├── requirements.txt             # Python dependencies
│   ├── .env.example                 # Environment variables template
│   └── alembic.ini                  # Alembic migration config
│
├── frontend/                         # React Vite frontend application
│   ├── src/
│   │   ├── pages/                   # Page components (route-based)
│   │   │   ├── Login.jsx            # Authentication page
│   │   │   ├── Dashboard.jsx        # Main dashboard
│   │   │   ├── Patients.jsx         # Patient list & search
│   │   │   ├── PatientProfile.jsx   # Patient details page
│   │   │   ├── NewAssessment.jsx    # Assessment initialization
│   │   │   ├── Questionnaire.jsx    # Questionnaire form
│   │   │   ├── Observation.jsx      # Clinical observations form
│   │   │   ├── FinalizeAssessment.jsx # Assessment completion
│   │   │   ├── AssessmentReport.jsx # Final report display
│   │   │   └── NotFound.jsx         # 404 page
│   │   ├── components/              # Reusable UI components
│   │   │   ├── Layout.jsx           # Main page wrapper
│   │   │   ├── QuestionCard.jsx     # Question display component
│   │   │   ├── StatusBadge.jsx      # Status indicator
│   │   │   ├── ProgressBar.jsx      # Assessment progress
│   │   │   └── ...                  # Additional components
│   │   ├── services/                # API client services
│   │   │   └── api.js               # Axios instance with interceptors
│   │   ├── context/                 # React Context
│   │   │   └── AuthContext.jsx      # Authentication state management
│   │   ├── routes/                  # Route components
│   │   │   └── ProtectedRoute.jsx   # Route protection wrapper
│   │   ├── styles/                  # CSS files
│   │   ├── App.jsx                  # Main app component & routing
│   │   ├── App.css                  # Global styles
│   │   └── main.jsx                 # React entry point
│   ├── public/                      # Static assets
│   ├── package.json                 # Node.js dependencies
│   ├── vite.config.js               # Vite build configuration
│   ├── eslint.config.js             # ESLint configuration
│   └── .env.example                 # Environment variables template
│
├── .gitignore                       # Git ignore rules
└── README.md                        # This file
```

---

## 🛠️ Tech Stack

### Backend
| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | FastAPI | Latest |
| ASGI Server | Uvicorn | Standard |
| ORM | SQLAlchemy | 2.0+ |
| Database | PostgreSQL | 12+ |
| Authentication | JWT + python-jose | Latest |
| Password Hashing | bcrypt | <4.1 |
| Data Validation | Pydantic | Latest |
| Migrations | Alembic | Latest |
| Testing | pytest | Latest |

### Frontend
| Component | Technology | Version |
|-----------|-----------|---------|
| Library | React | 19.2.8 |
| Build Tool | Vite | 8.3.0 |
| Routing | React Router | 7.18.4 |
| HTTP Client | Axios | 1.20.0 |
| CSS Framework | Bootstrap | 5.3.8 |
| Linter | ESLint | 10.10.0 |

### Infrastructure
- **Database**: PostgreSQL with Alembic version control
- **API Documentation**: FastAPI auto-generated Swagger/OpenAPI
- **CORS**: Configured for local and network development

---

## 📦 Prerequisites

### Required
- **Python**: 3.9+
- **Node.js**: 16+ (with npm or yarn)
- **PostgreSQL**: 12+
- **Git**

### Optional
- **Docker**: For containerized deployment
- **Postman**: For API testing

---

## 🚀 Installation & Setup

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/AyurEssence.git
   cd AyurEssence/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   ```

3. **Activate virtual environment**
   - On Windows (cmd):
     ```bash
     .venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and update:
   - `DATABASE_URL`: PostgreSQL connection string
   - `JWT_SECRET_KEY`: Generate a secure secret key
   - `CORS_ORIGINS`: Your frontend URL (default: http://localhost:5173)

   Example `.env`:
   ```env
   APP_NAME=AyurEssence
   APP_VERSION=1.0.0
   DATABASE_URL=postgresql+psycopg://ayur_user:ayur_pass@localhost:5432/ayur_essence
   JWT_SECRET_KEY=your-secret-key-here-change-in-production
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   CORS_ORIGINS=["http://localhost:5173"]
   ```

6. **Create PostgreSQL database**
   ```bash
   createdb ayur_essence
   ```
   
   Or using psql:
   ```sql
   CREATE DATABASE ayur_essence;
   ```

7. **Run migrations**
   ```bash
   alembic upgrade head
   ```

8. **Seed initial data (optional)**
   ```bash
   python -c "from app.database.init_db import init_db; from app.database.session import SessionLocal; init_db(SessionLocal())"
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd ../frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env`:
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   ```

---

## ⚙️ Configuration

### Backend Configuration (`app/core/config.py`)

```python
class Settings(BaseSettings):
    app_name: str = "AyurEssence"
    app_version: str = "1.0.0"
    database_url: str  # PostgreSQL URL from .env
    jwt_secret_key: str  # Secret key for JWT tokens
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: list[str]  # Allowed origins
```

### Frontend Configuration (`vite.config.js`)

The frontend automatically reads `VITE_API_BASE_URL` from `.env` for API communication.

### Database Connection

PostgreSQL connection in `.env`:
```
DATABASE_URL=postgresql+psycopg://username:password@host:port/database_name
```

---

## ▶️ Running the Application

### Start Backend Server

```bash
cd backend
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`

**API Documentation**:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Start Frontend Development Server

```bash
cd frontend
npm run dev
```

Frontend will be available at: `http://localhost:5173`

### Production Build (Frontend)

```bash
npm run build
npm run preview
```

---

## 🗄️ Database Migrations

### Create a new migration
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations
```bash
alembic upgrade head
```

### Rollback migrations
```bash
alembic downgrade -1  # Rollback one revision
alembic downgrade base  # Rollback to initial state
```

### View migration history
```bash
alembic history
```

---

## 📚 API Documentation

### Authentication Endpoints

**Register User** (Doctor only)
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "doctor@example.com",
  "full_name": "Dr. Rajesh",
  "password": "secure_password",
  "role": "DOCTOR"
}
```

**Login**
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "doctor@example.com",
  "password": "secure_password"
}

Response: { "access_token": "jwt_token", "user": {...} }
```

**Get Current User**
```http
GET /api/auth/me
Authorization: Bearer <token>
```

### Patient Endpoints

**Create Patient**
```http
POST /api/patients
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "John Doe",
  "date_of_birth": "1990-01-15",
  "gender": "MALE",
  "phone": "+1234567890"
}
```

**Search Patients**
```http
GET /api/patients?name=John&phone=1234567890&date_of_birth=1990-01-15
Authorization: Bearer <token>
```

**Get Patient Profile**
```http
GET /api/patients/{patient_id}
Authorization: Bearer <token>
```

**Get Patient Assessment History**
```http
GET /api/patients/{patient_id}/assessments
Authorization: Bearer <token>
```

### Assessment Endpoints

**Create Assessment**
```http
POST /api/assessments
Authorization: Bearer <token>
Content-Type: application/json

{
  "patient_id": "uuid",
  "questionnaire_version_id": "uuid"
}
```

**Submit Responses**
```http
POST /api/assessments/{assessment_id}/responses
Authorization: Bearer <token>
Content-Type: application/json

{
  "responses": [
    {
      "question_id": "uuid",
      "option_id": "uuid"
    }
  ]
}
```

**Add Observation**
```http
POST /api/assessments/{assessment_id}/observations
Authorization: Bearer <token>
Content-Type: application/json

{
  "observation_text": "Patient shows signs of Vata imbalance..."
}
```

**Calculate Assessment**
```http
POST /api/assessments/{assessment_id}/calculate
Authorization: Bearer <token>
```

**Get Assessment Report**
```http
GET /api/assessments/{assessment_id}/report
Authorization: Bearer <token>
```

**Finalize Assessment**
```http
POST /api/assessments/{assessment_id}/finalize
Authorization: Bearer <token>
```

---

## 🏗️ Architecture

### Layered Architecture

```
┌─────────────────────────────────────┐
│         FastAPI Routers             │ (API Endpoints)
├─────────────────────────────────────┤
│       Pydantic Schemas              │ (Request/Response Validation)
├─────────────────────────────────────┤
│      Business Logic Services        │ (Core Logic)
├─────────────────────────────────────┤
│     SQLAlchemy ORM Models           │ (Data Access)
├─────────────────────────────────────┤
│      PostgreSQL Database            │ (Data Storage)
└─────────────────────────────────────┘
```

### Database Relationships

```
User (1) ──> (*) Patient (created_by)
User (1) ──> (*) Assessment (practitioner)
Patient (1) ──> (*) Assessment
Assessment (1) ──> (*) AssessmentResponse
Assessment (1) ──> (*) DoshaResult
Assessment (1) ──> (*) PractitionerObservation
QuestionnaireVersion (1) ──> (*) Question
Question (1) ──> (*) QuestionOption
AssessmentResponse (n) --> QuestionOption
```

### Frontend Components

```
App
├── AuthProvider (Context)
├── Router
│   ├── Login
│   ├── Dashboard
│   ├── Patients
│   ├── PatientProfile
│   ├── NewAssessment
│   ├── Questionnaire
│   ├── Observation
│   ├── FinalizeAssessment
│   └── AssessmentReport
└── Global Styles
```

---

## 📋 Assessment Workflow

### Step-by-Step Flow

1. **User Login**
   - Doctor/Student logs in with credentials
   - JWT token stored in localStorage
   - Session persists on page reload

2. **Patient Selection/Creation**
   - Search existing patients or create new patient profile
   - Unique patient code auto-generated
   - Patient details recorded (name, DOB, gender, contact)

3. **Assessment Initialization**
   - Select questionnaire version
   - Assessment created in `IN_PROGRESS` status
   - Unique assessment ID generated

4. **Questionnaire Completion**
   - Questions displayed one by one
   - Patient selects options (each option has dosha scoring)
   - Responses saved to database
   - Progress tracked

5. **Clinical Observations**
   - Practitioner adds contextual clinical observations
   - Free-text notes recorded
   - Timestamp tracked

6. **Finalization**
   - System validates all required responses
   - Practitioner observation required
   - Assessment marked as `FINALIZED`
   - Completion timestamp set

7. **Prakriti Calculation**
   - Dosha scores aggregated from responses
   - CCRAS PAS-Based methodology applied
   - Percentages calculated
   - Classification determined (SAMADOSHAJA/EKA-DOSHAJA/SANSARGAJA)

8. **Report Generation**
   - Comprehensive assessment report generated
   - Dosha percentages displayed
   - Patient details included
   - Clinical observations noted
   - References provided

---

## 🔒 Security

### Authentication & Authorization
- **JWT Tokens**: Secure stateless authentication
- **Password Hashing**: bcrypt with salt
- **Role-Based Access Control**: Endpoints protected by user role
- **Token Expiry**: Configurable token lifetime (default: 60 minutes)

### Data Protection
- **Input Validation**: Pydantic schemas validate all inputs
- **SQL Injection Prevention**: SQLAlchemy parameterized queries
- **CORS Security**: Restricted origins configuration
- **HTTPS Ready**: Application supports HTTPS in production

### Best Practices Implemented
- Environment variables for sensitive config
- UUID for primary keys (non-sequential IDs)
- Audit timestamps on all records (created_at, updated_at)
- User-specific data access (can't view other practitioner's assessments)

---

## 🧪 Testing

### Run Backend Tests
```bash
cd backend
pytest
```

### Run Frontend Linting
```bash
cd frontend
npm run lint
```

---

## 📝 API Response Examples

### Successful Assessment Report
```json
{
  "patient": {
    "id": "uuid",
    "patient_code": "PAT-001",
    "name": "John Doe",
    "date_of_birth": "1990-01-15",
    "gender": "MALE",
    "phone": "+1234567890"
  },
  "assessment": {
    "id": "assessment-uuid",
    "status": "FINALIZED",
    "started_at": "2024-01-20T10:30:00",
    "completed_at": "2024-01-20T11:15:00",
    "practitioner_name": "Dr. Rajesh"
  },
  "questionnaire": {
    "id": "q-uuid",
    "name": "Prakriti Assessment",
    "version_id": "qv-uuid",
    "version_number": 1
  },
  "responses": [
    {
      "question_id": "q1-uuid",
      "question_text": "What is your body type?",
      "selected_option_text": "Lean and lightweight"
    }
  ],
  "practitioner_observation": {
    "id": "obs-uuid",
    "observation_text": "Patient shows typical Vata characteristics..."
  },
  "prakriti_result": {
    "result_status": "AVAILABLE",
    "vata_percentage": 45.5,
    "pitta_percentage": 35.2,
    "kapha_percentage": 19.3,
    "dominant_dosha": "EKA-DOSHAJA:VATA"
  }
}
```

---

## 🚀 Deployment

### Backend Deployment

**Using Gunicorn** (Production)
```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

**Using Docker**
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Deployment

**Build for Production**
```bash
cd frontend
npm run build
```

Output: `dist/` directory ready for deployment

**Deploy to Vercel/Netlify**
- Connect git repository
- Set build command: `npm run build`
- Set output directory: `dist`

---

## 📞 Support & Documentation

### Additional Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

### Troubleshooting

**Database Connection Failed**
```
Error: could not translate host name "localhost" to address
→ Ensure PostgreSQL is running
→ Check DATABASE_URL in .env
```

**CORS Error in Frontend**
```
Access to XMLHttpRequest denied
→ Check VITE_API_BASE_URL in frontend .env
→ Verify CORS_ORIGINS in backend .env
```

**JWT Token Expired**
```
401 Unauthorized
→ Login again to get new token
→ Check ACCESS_TOKEN_EXPIRE_MINUTES setting
```

---

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

---

## 👥 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Code Style
- **Backend**: Follow PEP 8 with black formatter
- **Frontend**: Follow ESLint configuration

---

## 📧 Contact

For questions or support, reach out to:
- **Email**: support@ayuressence.com
- **GitHub Issues**: Report bugs and feature requests

---

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) and [React](https://react.dev/)
- Powered by [PostgreSQL](https://www.postgresql.org/) and [SQLAlchemy](https://www.sqlalchemy.org/)
- Styled with [Bootstrap](https://getbootstrap.com/)
- Ayurvedic methodology: CCRAS PAS-Based Assessment

---

**Last Updated**: September 2026  
**Version**: 1.0.0
