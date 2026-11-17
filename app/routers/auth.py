from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.schemas.auth import RegisterInput, LoginInput
from app.core.security import hash_password, verify_password, create_token, decode_token, COOKIE_NAME

router = APIRouter(prefix="/api/auth", tags=["authentication"])

def serialize_account(row):
    return {"name": row["name"], "email": row["email"], "role": row["role"]}

def set_session(response: Response, token: str, remember: bool = False):
    response.set_cookie(COOKIE_NAME, token, httponly=True, secure=settings.cookie_secure, samesite="lax", max_age=(60*60*24*14 if remember else 60*60*12), path="/")

@router.get("/teachers")
def list_teachers(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT t.teacher_id,t.name,t.department FROM teacher t JOIN user_account u ON u.teacher_id=t.teacher_id WHERE u.role='teacher' AND u.is_active=TRUE ORDER BY t.name")).mappings().all()
    return {"teachers": [dict(row) for row in rows]}

@router.post("/register/{role}", status_code=201)
def register(role: str, data: RegisterInput, response: Response, db: Session = Depends(get_db)):
    if role not in ("student", "teacher"):
        raise HTTPException(404, "Choose student or teacher registration")
    if role == "student" and not (data.class_name and data.class_name.strip()):
        raise HTTPException(422, "Class or grade is required")
    if role == "student" and not data.teacher_id:
        raise HTTPException(422, "Choose a teacher")
    if role == "teacher" and not (data.department and data.department.strip()):
        raise HTTPException(422, "Department is required")
    email = str(data.email).lower().strip()
    if db.execute(text("SELECT 1 FROM user_account WHERE lower(email)=:email"), {"email": email}).first():
        raise HTTPException(409, "An account with this email already exists")
    try:
        if role == "student":
            teacher_exists = db.execute(text("SELECT 1 FROM teacher t JOIN user_account u ON u.teacher_id=t.teacher_id WHERE t.teacher_id=:id AND u.role='teacher' AND u.is_active=TRUE"), {"id": data.teacher_id}).first()
            if not teacher_exists:
                raise HTTPException(422, "Choose an available teacher")
            linked_id = db.execute(
            text('INSERT INTO student (teacher_id,name,"class",email) VALUES (:teacher_id,:name,:klass,:email) RETURNING student_id'),
            {"teacher_id": data.teacher_id, "name": data.full_name, "klass": data.class_name.strip(), "email": email}).scalar_one()
            link_column = "student_id"
        else:
            linked_id = db.execute(text("INSERT INTO teacher (name,email,department) VALUES (:name,:email,:dept) RETURNING teacher_id"), {"name": data.full_name, "email": email, "dept": data.department.strip()}).scalar_one()
            link_column = "teacher_id"
        user_id = db.execute(text(f"INSERT INTO user_account (email,password_hash,role,{link_column}) VALUES (:email,:password,CAST(:role AS user_role),:linked) RETURNING user_id"), {"email": email, "password": hash_password(data.password), "role": role, "linked": linked_id}).scalar_one()
        db.commit()
    except Exception:
        db.rollback()
        raise
    token = create_token(user_id, role)
    set_session(response, token)
    return {"account": {"name": data.full_name, "email": email, "role": role}, "redirect": f"/{role}/dashboard"}

@router.post("/login")
def login(data: LoginInput, response: Response, db: Session = Depends(get_db)):
    email = str(data.email).lower().strip()
    row = db.execute(text("SELECT u.user_id,u.email,u.password_hash,u.role,u.is_active,COALESCE(s.name,t.name) AS name FROM user_account u LEFT JOIN student s ON s.student_id=u.student_id LEFT JOIN teacher t ON t.teacher_id=u.teacher_id WHERE lower(u.email)=:email"), {"email": email}).mappings().first()
    if not row or not verify_password(data.password, row["password_hash"]):
        if row:
            db.execute(text("UPDATE user_account SET failed_logins=failed_logins+1 WHERE user_id=:id"), {"id": row["user_id"]}); db.commit()
        raise HTTPException(401, "Email or password is incorrect")
    if not row["is_active"]: raise HTTPException(403, "This account is inactive. Contact your school administrator.")
    db.execute(text("UPDATE user_account SET failed_logins=0,last_login_at=:now WHERE user_id=:id"), {"id": row["user_id"], "now": datetime.now(timezone.utc)}); db.commit()
    set_session(response, create_token(row["user_id"], row["role"]), data.remember_me)
    return {"account": serialize_account(row), "redirect": f"/{row['role']}/dashboard"}

@router.get("/me")
def me(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get(COOKIE_NAME)
    if not token: raise HTTPException(401, "Sign in to continue")
    try: claims = decode_token(token); user_id = int(claims["sub"])
    except Exception: raise HTTPException(401, "Your session has expired. Sign in again.")
    row = db.execute(text("SELECT u.user_id,u.email,u.role,u.is_active,COALESCE(s.name,t.name) AS name FROM user_account u LEFT JOIN student s ON s.student_id=u.student_id LEFT JOIN teacher t ON t.teacher_id=u.teacher_id WHERE u.user_id=:id"), {"id": user_id}).mappings().first()
    if not row or not row["is_active"]: raise HTTPException(401, "Your account is unavailable")
    return {"account": serialize_account(row)}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/", httponly=True, secure=settings.cookie_secure, samesite="lax")
    return {"ok": True}
