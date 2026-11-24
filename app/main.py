from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers.auth import router as auth_router
from app.routers.dashboard import router as dashboard_router
from app.routers.courses import router as courses_router
from app.routers.learning import router as personal_learning_router
from app.routers.teacher import router as teacher_portal_router

BASE = Path(__file__).resolve().parent.parent
app = FastAPI(title="Learning Gap", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.frontend_origins.split(",")], allow_credentials=True, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(courses_router)
app.include_router(personal_learning_router)
app.include_router(teacher_portal_router)
app.mount("/assets", StaticFiles(directory=BASE / "frontend" / "assets"), name="assets")

@app.get("/health")
def health(): return {"status": "ok"}

@app.get("/{role}/dashboard")
def dashboard_page(role: str):
    if role not in ("student", "teacher"): return FileResponse(BASE / "frontend" / "index.html")
    return FileResponse(BASE / "frontend" / f"{role}.html")

@app.get("/student/courses")
def student_courses_page(): return FileResponse(BASE / "frontend" / "courses.html")

@app.get("/student/learning-gaps")
def student_gaps_page(): return FileResponse(BASE / "frontend" / "learning-gaps.html")

@app.get("/student/learning-plan")
def student_plan_page(): return FileResponse(BASE / "frontend" / "learning-plan.html")

@app.get("/student/quizzes")
def student_quizzes_page(): return FileResponse(BASE / "frontend" / "quizzes.html")

@app.get("/student/assessments")
def student_assessments_page(): return FileResponse(BASE / "frontend" / "student-assessments.html")

@app.get("/teacher/classes")
def teacher_classes_page(): return FileResponse(BASE / "frontend" / "teacher-classes.html")

@app.get("/teacher/assessments")
def teacher_assessments_page(): return FileResponse(BASE / "frontend" / "teacher-assessments.html")

@app.get("/teacher/gradebook")
def teacher_gradebook_page(): return FileResponse(BASE / "frontend" / "teacher-gradebook.html")

@app.get("/teacher/reports")
def teacher_reports_page(): return FileResponse(BASE / "frontend" / "teacher-reports.html")

@app.get("/{path:path}")
def frontend(path: str): return FileResponse(BASE / "frontend" / "index.html")
