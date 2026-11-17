from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.schemas.courses import CourseRequestInput
from app.db.session import get_db
from app.routers.dashboard import current

router = APIRouter(prefix="/api/student", tags=["student courses"])

@router.get("/courses")
def student_courses(request: Request, db: Session = Depends(get_db)):
    account = current(request, db, "student")
    sid = account["student_id"]
    student = db.execute(text('SELECT name,"class" AS class_name FROM student WHERE student_id=:id'), {"id": sid}).mappings().one()
    enrolled = db.execute(text("""
        SELECT c.course_id,c.title,c.description,c.department,c.target_class,t.name AS teacher_name,
               e.enrolled_at,0 AS progress
        FROM course_enrollment e JOIN course c ON c.course_id=e.course_id
        JOIN teacher t ON t.teacher_id=c.teacher_id
        WHERE e.student_id=:sid ORDER BY e.enrolled_at DESC
    """), {"sid": sid}).mappings().all()
    available = db.execute(text("""
        SELECT c.course_id,c.title,c.description,c.department,c.target_class,t.name AS teacher_name,
               COUNT(DISTINCT e.student_id) AS enrolled_count
        FROM course c JOIN teacher t ON t.teacher_id=c.teacher_id
        LEFT JOIN course_enrollment e ON e.course_id=c.course_id
        WHERE c.is_published=TRUE AND (c.target_class IS NULL OR c.target_class=:class_name)
          AND NOT EXISTS (SELECT 1 FROM course_enrollment mine WHERE mine.course_id=c.course_id AND mine.student_id=:sid)
        GROUP BY c.course_id,t.name ORDER BY c.title
    """), {"sid": sid, "class_name": student["class_name"]}).mappings().all()
    requests = db.execute(text("SELECT request_id,title,department,target_class,description,reason,status,created_at FROM course_request WHERE student_id=:sid ORDER BY created_at DESC"), {"sid": sid}).mappings().all()
    return {"account": {"name": student["name"], "role": "student"}, "class_name": student["class_name"], "enrolled": [dict(row) for row in enrolled], "available": [dict(row) for row in available], "requests": [dict(row) for row in requests]}

@router.post("/courses/{course_id}/enroll", status_code=201)
def enroll(course_id: int, request: Request, db: Session = Depends(get_db)):
    account = current(request, db, "student")
    sid = account["student_id"]
    row = db.execute(text("SELECT c.course_id,c.target_class,s.class AS student_class FROM course c JOIN student s ON s.student_id=:sid WHERE c.course_id=:course_id AND c.is_published=TRUE"), {"sid": sid, "course_id": course_id}).mappings().first()
    if not row:
        raise HTTPException(404, "This course is not available")
    if row["target_class"] and row["target_class"] != row["student_class"]:
        raise HTTPException(403, "This course is for a different class")
    result = db.execute(text("INSERT INTO course_enrollment(course_id,student_id) VALUES (:course_id,:sid) ON CONFLICT (course_id,student_id) DO NOTHING RETURNING enrollment_id"), {"course_id": course_id, "sid": sid}).scalar_one_or_none()
    db.commit()
    if result is None:
        raise HTTPException(409, "You are already enrolled in this course")
    return {"ok": True, "message": "You are enrolled. The course is now in My Courses."}

@router.post("/course-requests", status_code=201)
def create_course_request(data: CourseRequestInput, request: Request, db: Session = Depends(get_db)):
    account = current(request, db, "student")
    sid = account["student_id"]
    result = db.execute(text("""
        INSERT INTO course_request(student_id,title,department,target_class,description,reason)
        VALUES (:sid,:title,:department,:target_class,:description,:reason)
        RETURNING request_id,status,created_at
    """), {"sid": sid, **data.model_dump()}).mappings().one()
    db.commit()
    return {"request": dict(result)}
