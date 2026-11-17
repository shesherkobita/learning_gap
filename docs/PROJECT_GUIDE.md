# Learning Gap Project Guide

This note maps the project to the job each folder performs. Start at the project root for setup and run commands; start at `app/main.py` to follow the backend.

## Folder map

```text
learning-gap/
├── app/                         Python web application
│   ├── main.py                  Creates FastAPI and connects pages/API routes
│   ├── core/                    Shared configuration and security helpers
│   ├── db/                      PostgreSQL connection and session
│   ├── routers/                 API routes grouped by feature
│   └── schemas/                 Input validation for API requests
├── alembic/                     Database migrations and migration history
├── database/                    Starting PostgreSQL SQL and sample data
├── frontend/                    Pages the student or teacher sees
│   ├── *.html                   Page layouts
│   └── assets/
│       ├── css/                 Visual styling
│       └── js/                  Browser interactions and API calls
├── docs/                        Project notes and this guide
├── .env                         Your local database URL and secret (private)
├── .env.example                 Safe settings template
├── alembic.ini                  Alembic migration configuration
└── requirements.txt             Python packages used by the app
```

The local `.venv/` folder holds installed Python packages and is not part of the application source. Keep `.env` private and do not submit it with reports or upload it to a public repository.

## Backend files

| File | Purpose |
|---|---|
| `app/main.py` | Starts the FastAPI app, registers feature routers, and serves HTML/static files. |
| `app/core/config.py` | Reads settings such as `DATABASE_URL` and `JWT_SECRET` from `.env`. |
| `app/core/security.py` | Hashes and checks passwords; creates and verifies signed login tokens. |
| `app/db/session.py` | Creates the PostgreSQL connection and supplies database sessions to API routes. |
| `app/routers/auth.py` | Registration, login, logout, current account, and teacher list endpoints. |
| `app/routers/dashboard.py` | Student and teacher dashboard data; checks signed-in role. |
| `app/routers/courses.py` | Course browsing, student enrollment, and course requests. |
| `app/routers/learning.py` | Learning gap calculations, guided lesson progress, and quiz questions/results. |
| `app/schemas/auth.py` | Validates registration and login request fields. |
| `app/schemas/courses.py` | Validates course request form fields. |

Database queries currently live beside the API routes that use them. They use SQLAlchemy with bound SQL parameters to communicate safely with PostgreSQL.

## Frontend files

- `frontend/index.html`: sign-in and account creation.
- `frontend/student.html` and `frontend/teacher.html`: role-specific dashboards.
- `frontend/courses.html`, `frontend/learning-gaps.html`, `frontend/learning-plan.html`, `frontend/quizzes.html`: student feature pages.
- `frontend/assets/css/app.css`: shared layout, colors, components, and responsive styling.
- `frontend/assets/js/auth.js`: sign-in, registration, and redirects.
- `frontend/assets/js/dashboard.js`: dashboard data loading and sign-out.
- `frontend/assets/js/courses.js`: course search, enrollment, and requests.
- `frontend/assets/js/learning.js`: learning gap and lesson plan page behavior.
- `frontend/assets/js/quizzes.js`: quiz question flow and result feedback.

The browser calls the `/api/...` endpoints in the backend. It does not connect directly to PostgreSQL.

## Database files

- `database/learning_gap_pg.sql`: creates the original learning tables and sample records.
- `alembic/versions/`: adds application tables and changes in order. `alembic upgrade head` applies the migrations to the database named in `.env`.

## Run the project

From the project root in PowerShell:

```powershell
.\.venv\Scripts\uvicorn.exe app.main:app --reload
```

Then open `http://127.0.0.1:8000`. For database setup and first-time migration steps, see the root `README.md`.
