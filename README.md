# Learning Gap

Learning Gap is a student learning app that uses assessment and quiz answers to highlight topics to review. Students can browse courses, practice with quizzes, review their learning gaps, and follow a guided learning plan. The project includes student and teacher registration, login, and role-specific dashboards.

## Features in this version

- **Accounts:** student and teacher registration, login, logout, and protected dashboards.
- **My Courses:** browse courses for the student's class, search and filter by department or teacher, enroll, and submit or view course requests.
- **Learning Gaps:** view topic accuracy, severity, actual incorrect answers, and known misconception patterns based on recorded data.
- **Learning Plan:** follow curated lessons prioritized using topic performance and save lesson completion.
- **Quizzes:** take topic-focused or mixed quizzes, submit answers, review feedback, and save results that update Learning Gaps and the Learning Plan.
- **Teacher Dashboard:** see published classes, student totals, pending grading, students below the at-risk score threshold, and upcoming assessment deadlines.
- **Classes:** create and publish class sections, maintain a syllabus, link study materials, post announcements, and view enrolled students.
- **Assessments:** create quizzes or assignments with questions, rubrics, due dates, and points; quizzes with answer keys are auto-graded, while written work can be graded by the teacher.
- **Gradebook & Students:** review enrolled students and scores, add grade entries, set category weights that total 100%, and view a weighted class matrix.
- **Reports:** filter monthly score trends by class, review Learning Gap alerts, and download a CSV report.
- **Student Assessments:** students can open and submit published assessments from classes they are enrolled in.

## Technology

- **Backend:** Python, FastAPI, SQLAlchemy, Alembic
- **Frontend:** HTML, CSS, vanilla JavaScript, Fetch API
- **Database:** PostgreSQL
- **Authentication:** Argon2 password hashing, signed session tokens in HttpOnly cookies

## Run locally on Windows

### 1. Prepare PostgreSQL

Create a PostgreSQL database (the example name is `learning_app`). In pgAdmin, open the Query Tool for that database, open [`database/learning_gap_pg.sql`](database/learning_gap_pg.sql), and run it to create the starting schema and sample learning data.

### 2. Install the application

From this project folder in PowerShell:

```powershell
py -m venv .venv
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Edit `.env` and set `DATABASE_URL` to your PostgreSQL username, password, host, port, and database name. Set `JWT_SECRET` to a long, random value. Keep `.env` private; it is excluded from Git.

### 3. Create/update tables and start the app

```powershell
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\uvicorn.exe app.main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). FastAPI's interactive API documentation is at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

For macOS or Linux, create and activate a virtual environment with `python3 -m venv .venv` and `source .venv/bin/activate`, install with `pip install -r requirements.txt`, copy `.env.example` to `.env`, then run `alembic upgrade head` and `uvicorn app.main:app --reload`.

## Project layout

```text
app/                 FastAPI application
  core/              Settings and security helpers
  db/                PostgreSQL connection/session
  routers/           Authentication, dashboard, courses, learning, and teacher APIs
  schemas/           API input validation
alembic/             Database migration history
database/            Starting schema and sample data
docs/                Project documentation
frontend/             HTML pages and browser assets
  assets/css/         Styles
  assets/js/          Browser behavior and API calls
.env.example          Template for local configuration
requirements.txt      Python dependencies
```

See [docs/PROJECT_GUIDE.md](docs/PROJECT_GUIDE.md) for descriptions of the main files.

## Data and scope notes

Learning gap scores are calculated from stored assessment and quiz answers. New student accounts will show no topic scores until they have answer data. The guided lesson content is curated starter material, not AI-generated content. The supplied database file contains development sample records.

Teacher materials are stored as resource links; direct file uploads are not included. The teacher gradebook can also store manual grade entries independently of assessment submissions. Course requests remain part of the student course workflow.

## GitHub and secrets

`.gitignore` excludes `.env`, virtual environments, Python cache files, editor settings, and common build output. Commit `.env.example`, but do not commit `.env` or any real database credentials. Before publishing the sample SQL publicly, check that its demo names and data are appropriate to share.
