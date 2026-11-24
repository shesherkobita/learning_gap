from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import COOKIE_NAME, decode_token

router = APIRouter(prefix="/api", tags=["dashboards"])

def current(request: Request, db: Session, expected: str):
    token = request.cookies.get(COOKIE_NAME)
    if not token: raise HTTPException(401, "Sign in to continue")
    try: claims = decode_token(token); user_id = int(claims["sub"])
    except Exception: raise HTTPException(401, "Your session has expired")
    account = db.execute(text("SELECT user_id,role,teacher_id,student_id FROM user_account WHERE user_id=:id AND is_active"), {"id": user_id}).mappings().first()
    if not account: raise HTTPException(401, "Account unavailable")
    if account["role"] != expected: raise HTTPException(403, "You do not have access to this dashboard")
    return account

@router.get("/student/dashboard")
def student_dashboard(request: Request, db: Session = Depends(get_db)):
    account = current(request, db, "student")
    sid = account["student_id"]
    student = db.execute(text('SELECT name,"class" AS class_name,email FROM student WHERE student_id=:id'), {"id": sid}).mappings().first()
    stats = db.execute(text("SELECT COUNT(*) AS assessments, COALESCE(AVG(score),0) AS average FROM assessment WHERE student_id=:id"), {"id": sid}).mappings().one()
    recent = db.execute(text("SELECT type,date,score FROM assessment WHERE student_id=:id ORDER BY date DESC LIMIT 5"), {"id": sid}).mappings().all()
    gaps = db.execute(text("SELECT t.topic_name, COUNT(*) FILTER (WHERE NOT r.is_correct) AS misses, COUNT(*) AS attempts, ROUND(100.0*COUNT(*) FILTER (WHERE r.is_correct)/NULLIF(COUNT(*),0),0) AS accuracy FROM student_response r JOIN topic t ON t.topic_id=r.topic_id WHERE r.student_id=:id GROUP BY t.topic_id,t.topic_name ORDER BY accuracy ASC NULLS LAST LIMIT 4"), {"id": sid}).mappings().all()
    return {"account": {"name": student["name"], "email": student["email"], "role": "student"}, "class_name": student["class_name"], "stats": {"assessments": stats["assessments"], "average_score": float(stats["average"]), "topics_practiced": len(gaps), "learning_streak": None}, "recent_assessments": [dict(r) for r in recent], "topic_performance": [dict(g) for g in gaps]}

@router.get("/teacher/dashboard")
def teacher_dashboard(request: Request, db: Session = Depends(get_db)):
    account = current(request, db, "teacher")
    tid = account["teacher_id"]
    teacher = db.execute(text("SELECT name,email,department FROM teacher WHERE teacher_id=:id"), {"id": tid}).mappings().first()
    students = db.execute(text("SELECT COUNT(*) FROM student WHERE teacher_id=:id"), {"id": tid}).scalar_one()
    rows = db.execute(text("SELECT s.name,s.email,s.class AS class_name,COUNT(DISTINCT a.assessment_id) AS assessments,COALESCE(AVG(a.score),0) AS average FROM student s LEFT JOIN assessment a ON a.student_id=s.student_id WHERE s.teacher_id=:id GROUP BY s.student_id ORDER BY s.name LIMIT 8"), {"id": tid}).mappings().all()
    overall = db.execute(text("SELECT COUNT(DISTINCT a.assessment_id) AS assessments,COALESCE(AVG(a.score),0) AS average FROM student s LEFT JOIN assessment a ON a.student_id=s.student_id WHERE s.teacher_id=:id"), {"id": tid}).mappings().one()
    active_classes = db.execute(text("SELECT COUNT(*) FROM course WHERE teacher_id=:id AND is_published=TRUE"), {"id": tid}).scalar_one()
    pending = db.execute(text("SELECT COUNT(*) FROM teacher_submission s JOIN teacher_assessment a ON a.assessment_id=s.assessment_id JOIN course c ON c.course_id=a.course_id WHERE c.teacher_id=:id AND s.status='submitted'"), {"id": tid}).scalar_one()
    risk_rows = db.execute(text("""
      WITH scores AS (
        SELECT a.student_id,a.score FROM assessment a JOIN student s ON s.student_id=a.student_id WHERE s.teacher_id=:id
        UNION ALL SELECT q.student_id,q.score FROM quiz_attempt q JOIN student s ON s.student_id=q.student_id WHERE s.teacher_id=:id
        UNION ALL SELECT sub.student_id,100.0*sub.points_earned/NULLIF(a.total_points,0) FROM teacher_submission sub JOIN teacher_assessment a ON a.assessment_id=sub.assessment_id JOIN course c ON c.course_id=a.course_id WHERE c.teacher_id=:id AND sub.status='graded'
      )
      SELECT s.student_id,s.name,s.email,s.class,ROUND(AVG(x.score),1) AS average_score,COUNT(x.score) AS scored_attempts
      FROM student s JOIN scores x ON x.student_id=s.student_id WHERE s.teacher_id=:id
      GROUP BY s.student_id HAVING AVG(x.score)<50 ORDER BY AVG(x.score) LIMIT 8
    """), {"id": tid}).mappings().all()
    deadlines = db.execute(text("SELECT a.assessment_id,a.title,a.kind,a.due_at,c.title AS class_title FROM teacher_assessment a JOIN course c ON c.course_id=a.course_id WHERE c.teacher_id=:id AND a.is_published=TRUE AND a.due_at>=CURRENT_TIMESTAMP ORDER BY a.due_at LIMIT 6"), {"id": tid}).mappings().all()
    return {"account": {"name": teacher["name"], "email": teacher["email"], "role": "teacher"}, "department": teacher["department"], "stats": {"students": students, "assessments": overall["assessments"], "average_score": float(overall["average"]), "active_classes": active_classes, "pending_gradings": pending}, "at_risk": [dict(r, average_score=float(r["average_score"])) for r in risk_rows], "deadlines": [dict(r) for r in deadlines], "students": [dict(r, average=float(r["average"])) for r in rows]}
