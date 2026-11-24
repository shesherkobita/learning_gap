import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.routers.dashboard import current
from app.schemas.teacher import (ClassInput, MaterialInput, AnnouncementInput, AssessmentInput,
    GradeEntryInput, GradeWeightsInput, StudentAssessmentSubmission, ManualGradeInput)

router = APIRouter(tags=["teacher portal"])

def teacher_account(request, db): return current(request, db, "teacher")

def owned_course(db, teacher_id, course_id):
    row=db.execute(text("SELECT course_id,title FROM course WHERE course_id=:course AND teacher_id=:teacher"),{"course":course_id,"teacher":teacher_id}).mappings().first()
    if not row: raise HTTPException(404,"Class not found")
    return row

def owned_assessment(db, teacher_id, assessment_id):
    row=db.execute(text("SELECT a.assessment_id,a.course_id,a.total_points FROM teacher_assessment a JOIN course c ON c.course_id=a.course_id WHERE a.assessment_id=:id AND c.teacher_id=:teacher"),{"id":assessment_id,"teacher":teacher_id}).mappings().first()
    if not row: raise HTTPException(404,"Assessment not found")
    return row

@router.get("/api/teacher/classes")
def list_classes(request:Request,db:Session=Depends(get_db)):
    teacher=teacher_account(request,db); tid=teacher["teacher_id"]
    rows=db.execute(text("""
      SELECT c.course_id,c.title,c.description,c.department,c.target_class,c.syllabus,c.is_published,c.created_at,
        COUNT(DISTINCT e.student_id) AS student_count,
        (SELECT COUNT(*) FROM course_material m WHERE m.course_id=c.course_id) AS material_count,
        (SELECT COUNT(*) FROM course_announcement a WHERE a.course_id=c.course_id) AS announcement_count
      FROM course c LEFT JOIN course_enrollment e ON e.course_id=c.course_id
      WHERE c.teacher_id=:tid GROUP BY c.course_id ORDER BY c.created_at DESC
    """),{"tid":tid}).mappings().all()
    return {"classes":[dict(r) for r in rows]}

@router.post("/api/teacher/classes",status_code=201)
def create_class(data:ClassInput,request:Request,db:Session=Depends(get_db)):
    teacher=teacher_account(request,db)
    course_id=db.execute(text("INSERT INTO course(teacher_id,title,description,department,target_class,syllabus,is_published) VALUES (:tid,:title,:description,:department,:target,:syllabus,FALSE) RETURNING course_id"),{"tid":teacher["teacher_id"],"title":data.title,"description":data.description,"department":data.department,"target":data.target_class,"syllabus":data.syllabus}).scalar_one()
    db.commit(); return {"course_id":course_id,"message":"Class created as a draft"}

@router.put("/api/teacher/classes/{course_id}")
def update_class(course_id:int,data:ClassInput,request:Request,db:Session=Depends(get_db)):
    teacher=teacher_account(request,db); owned_course(db,teacher["teacher_id"],course_id)
    db.execute(text("UPDATE course SET title=:title,description=:description,department=:department,target_class=:target,syllabus=:syllabus,updated_at=CURRENT_TIMESTAMP WHERE course_id=:id"),{"title":data.title,"description":data.description,"department":data.department,"target":data.target_class,"syllabus":data.syllabus,"id":course_id})
    db.commit();return {"ok":True}

@router.patch("/api/teacher/classes/{course_id}/publish")
def publish_class(course_id:int,request:Request,db:Session=Depends(get_db)):
    teacher=teacher_account(request,db); owned_course(db,teacher["teacher_id"],course_id)
    db.execute(text("UPDATE course SET is_published=NOT is_published,updated_at=CURRENT_TIMESTAMP WHERE course_id=:id"),{"id":course_id});db.commit()
    return {"ok":True}

@router.get("/api/teacher/classes/{course_id}/content")
def class_content(course_id:int,request:Request,db:Session=Depends(get_db)):
    teacher=teacher_account(request,db);owned_course(db,teacher["teacher_id"],course_id)
    materials=db.execute(text("SELECT material_id,title,material_type,resource_url,created_at FROM course_material WHERE course_id=:id ORDER BY created_at DESC"),{"id":course_id}).mappings().all()
    announcements=db.execute(text("SELECT announcement_id,title,body,created_at FROM course_announcement WHERE course_id=:id ORDER BY created_at DESC"),{"id":course_id}).mappings().all()
    students=db.execute(text("SELECT s.student_id,s.name,s.email,s.class FROM student s JOIN course_enrollment e ON e.student_id=s.student_id WHERE e.course_id=:id ORDER BY s.name"),{"id":course_id}).mappings().all()
    return {"materials":[dict(r) for r in materials],"announcements":[dict(r) for r in announcements],"students":[dict(r) for r in students]}

@router.post("/api/teacher/classes/{course_id}/materials",status_code=201)
def add_material(course_id:int,data:MaterialInput,request:Request,db:Session=Depends(get_db)):
    teacher=teacher_account(request,db);owned_course(db,teacher["teacher_id"],course_id)
    mid=db.execute(text("INSERT INTO course_material(course_id,title,material_type,resource_url) VALUES (:course,:title,:kind,:url) RETURNING material_id"),{"course":course_id,"title":data.title,"kind":data.material_type,"url":data.resource_url}).scalar_one();db.commit()
    return {"material_id":mid,"ok":True}

@router.post("/api/teacher/classes/{course_id}/announcements",status_code=201)
def add_announcement(course_id:int,data:AnnouncementInput,request:Request,db:Session=Depends(get_db)):
    teacher=teacher_account(request,db);owned_course(db,teacher["teacher_id"],course_id)
    aid=db.execute(text("INSERT INTO course_announcement(course_id,title,body) VALUES (:course,:title,:body) RETURNING announcement_id"),{"course":course_id,"title":data.title,"body":data.body}).scalar_one();db.commit()
    return {"announcement_id":aid,"ok":True}

@router.get("/api/teacher/assessments")
def list_assessments(request:Request,db:Session=Depends(get_db)):
    teacher=teacher_account(request,db)
    rows=db.execute(text("""
      SELECT a.assessment_id,a.course_id,a.title,a.description,a.kind,a.due_at,a.total_points,a.rubric,a.is_published,c.title AS class_title,
       (SELECT COUNT(*) FROM teacher_assessment_question q WHERE q.assessment_id=a.assessment_id) AS question_count,
       (SELECT COUNT(*) FROM teacher_submission s WHERE s.assessment_id=a.assessment_id AND s.status='submitted') AS pending_count,
       (SELECT COUNT(*) FROM teacher_submission s WHERE s.assessment_id=a.assessment_id) AS submission_count
      FROM teacher_assessment a JOIN course c ON c.course_id=a.course_id WHERE c.teacher_id=:tid ORDER BY a.due_at NULLS LAST,a.created_at DESC
    """),{"tid":teacher["teacher_id"]}).mappings().all()
    classes=db.execute(text("SELECT course_id,title FROM course WHERE teacher_id=:tid ORDER BY title"),{"tid":teacher["teacher_id"]}).mappings().all()
    return {"assessments":[dict(r) for r in rows],"classes":[dict(r) for r in classes]}

@router.post("/api/teacher/assessments",status_code=201)
def create_assessment(data:AssessmentInput,request:Request,db:Session=Depends(get_db)):
    teacher=teacher_account(request,db);owned_course(db,teacher["teacher_id"],data.course_id)
    if not data.questions: raise HTTPException(422,"Add at least one question or assignment prompt")
    assessment_id=db.execute(text("INSERT INTO teacher_assessment(course_id,title,description,kind,due_at,total_points,rubric) VALUES (:course,:title,:description,:kind,:due,:points,:rubric) RETURNING assessment_id"),{"course":data.course_id,"title":data.title,"description":data.description,"kind":data.kind,"due":data.due_at,"points":data.total_points,"rubric":data.rubric}).scalar_one()
    for q in data.questions:
        db.execute(text("INSERT INTO teacher_assessment_question(assessment_id,question_text,answer_type,choices,correct_answer,points) VALUES (:assessment,:text,:type,:choices,:answer,:points)"),{"assessment":assessment_id,"text":q.question_text,"type":q.answer_type,"choices":json.dumps(q.choices) if q.choices else None,"answer":q.correct_answer,"points":q.points})
    db.commit();return {"assessment_id":assessment_id,"is_published":False,"message":"Assessment saved as a draft"}

@router.patch("/api/teacher/assessments/{assessment_id}/publish")
def publish_assessment(assessment_id:int,request:Request,db:Session=Depends(get_db)):
    teacher=teacher_account(request,db);owned_assessment(db,teacher["teacher_id"],assessment_id)
    db.execute(text("UPDATE teacher_assessment SET is_published=NOT is_published WHERE assessment_id=:id"),{"id":assessment_id});db.commit();return {"ok":True}

@router.get("/api/teacher/assessments/{assessment_id}/submissions")
def assessment_submissions(assessment_id:int,request:Request,db:Session=Depends(get_db)):
    teacher=teacher_account(request,db);owned_assessment(db,teacher["teacher_id"],assessment_id)
    rows=db.execute(text("SELECT s.submission_id,s.student_id,st.name,st.email,st.class,s.answers,s.points_earned,s.status,s.feedback,s.submitted_at,a.total_points FROM teacher_submission s JOIN student st ON st.student_id=s.student_id JOIN teacher_assessment a ON a.assessment_id=s.assessment_id WHERE s.assessment_id=:id ORDER BY s.submitted_at DESC"),{"id":assessment_id}).mappings().all()
    return {"submissions":[dict(r) for r in rows]}

@router.patch("/api/teacher/submissions/{submission_id}/grade")
def grade_submission(submission_id:int,data:ManualGradeInput,request:Request,db:Session=Depends(get_db)):
    teacher=teacher_account(request,db)
    row=db.execute(text("SELECT s.submission_id,a.total_points FROM teacher_submission s JOIN teacher_assessment a ON a.assessment_id=s.assessment_id JOIN course c ON c.course_id=a.course_id WHERE s.submission_id=:id AND c.teacher_id=:tid"),{"id":submission_id,"tid":teacher["teacher_id"]}).mappings().first()
    if not row:raise HTTPException(404,"Submission not found")
    points=data.points_earned;feedback=data.feedback
    if points<0 or points>float(row["total_points"]):raise HTTPException(422,"Score must be between zero and the assessment total")
    db.execute(text("UPDATE teacher_submission SET points_earned=:points,status='graded',feedback=:feedback,graded_at=CURRENT_TIMESTAMP WHERE submission_id=:id"),{"points":points,"feedback":feedback,"id":submission_id});db.commit()
    return {"ok":True}

@router.get("/api/teacher/gradebook")
def gradebook(request:Request,course_id:int|None=None,db:Session=Depends(get_db)):
    teacher=teacher_account(request,db);tid=teacher["teacher_id"]
    classes=db.execute(text("SELECT course_id,title FROM course WHERE teacher_id=:tid ORDER BY title"),{"tid":tid}).mappings().all()
    course_id=course_id or (classes[0]["course_id"] if classes else None)
    if course_id is None:return {"classes":[],"students":[],"weights":[],"entries":[]}
    owned_course(db,tid,course_id)
    students=db.execute(text("SELECT s.student_id,s.name,s.email,s.class FROM student s JOIN course_enrollment e ON e.student_id=s.student_id WHERE e.course_id=:course ORDER BY s.name"),{"course":course_id}).mappings().all()
    weights=db.execute(text("SELECT category,weight_percent FROM gradebook_weight WHERE course_id=:course ORDER BY category"),{"course":course_id}).mappings().all()
    entries=db.execute(text("""
      SELECT entry_id,student_id,category,item_name,score,max_score,updated_at FROM gradebook_entry WHERE course_id=:course
      UNION ALL
      SELECT NULL AS entry_id,s.student_id,CASE WHEN a.kind='quiz' THEN 'Quizzes' ELSE 'Assignments' END AS category,
        a.title AS item_name,sub.points_earned AS score,a.total_points AS max_score,sub.graded_at AS updated_at
      FROM teacher_submission sub JOIN teacher_assessment a ON a.assessment_id=sub.assessment_id JOIN student s ON s.student_id=sub.student_id
      WHERE a.course_id=:course AND sub.status='graded'
      ORDER BY category,item_name,student_id
    """),{"course":course_id}).mappings().all()
    return {"classes":[dict(r) for r in classes],"selected_course_id":course_id,"students":[dict(r) for r in students],"weights":[dict(r) for r in weights],"entries":[dict(r) for r in entries]}

@router.put("/api/teacher/gradebook/weights/{course_id}")
def save_weights(course_id:int,data:GradeWeightsInput,request:Request,db:Session=Depends(get_db)):
    teacher=teacher_account(request,db);owned_course(db,teacher["teacher_id"],course_id)
    db.execute(text("DELETE FROM gradebook_weight WHERE course_id=:course"),{"course":course_id})
    for item in data.weights: db.execute(text("INSERT INTO gradebook_weight(course_id,category,weight_percent) VALUES (:course,:category,:weight)"),{"course":course_id,"category":item.category,"weight":item.weight_percent})
    db.commit();return {"ok":True}

@router.put("/api/teacher/gradebook/entries/{course_id}/{student_id}")
def save_grade(course_id:int,student_id:int,data:GradeEntryInput,request:Request,db:Session=Depends(get_db)):
    teacher=teacher_account(request,db);owned_course(db,teacher["teacher_id"],course_id)
    if data.score>data.max_score:raise HTTPException(422,"Score cannot exceed the maximum score")
    enrolled=db.execute(text("SELECT 1 FROM course_enrollment WHERE course_id=:course AND student_id=:student"),{"course":course_id,"student":student_id}).first()
    if not enrolled:raise HTTPException(404,"Student is not enrolled in this class")
    db.execute(text("INSERT INTO gradebook_entry(course_id,student_id,category,item_name,score,max_score) VALUES (:course,:student,:category,:item,:score,:max) ON CONFLICT(course_id,student_id,category,item_name) DO UPDATE SET score=EXCLUDED.score,max_score=EXCLUDED.max_score,updated_at=CURRENT_TIMESTAMP"),{"course":course_id,"student":student_id,"category":data.category,"item":data.item_name,"score":data.score,"max":data.max_score});db.commit()
    return {"ok":True}

@router.get("/api/teacher/reports")
def teacher_reports(request:Request,course_id:int|None=None,db:Session=Depends(get_db)):
    teacher=teacher_account(request,db);tid=teacher["teacher_id"]
    classes=db.execute(text("SELECT course_id,title FROM course WHERE teacher_id=:tid ORDER BY title"),{"tid":tid}).mappings().all()
    if course_id:owned_course(db,tid,course_id)
    params={"tid":tid,"course":course_id}
    scores=db.execute(text("""
      WITH course_students AS (SELECT DISTINCT s.student_id FROM student s LEFT JOIN course_enrollment e ON e.student_id=s.student_id LEFT JOIN course c ON c.course_id=e.course_id WHERE s.teacher_id=:tid AND (:course IS NULL OR c.course_id=:course)),
      all_scores AS (
       SELECT a.student_id,a.score,a.date::date AS score_date FROM assessment a JOIN course_students cs ON cs.student_id=a.student_id
       UNION ALL SELECT q.student_id,q.score,q.created_at::date FROM quiz_attempt q JOIN course_students cs ON cs.student_id=q.student_id
       UNION ALL SELECT s.student_id,100.0*sub.points_earned/NULLIF(a.total_points,0),sub.submitted_at::date FROM teacher_submission sub JOIN teacher_assessment a ON a.assessment_id=sub.assessment_id JOIN course c ON c.course_id=a.course_id JOIN course_students s ON s.student_id=sub.student_id WHERE sub.status='graded' AND (:course IS NULL OR c.course_id=:course)
      )
      SELECT to_char(date_trunc('month',score_date),'YYYY-MM') AS month,ROUND(AVG(score),1) AS average_score,COUNT(*) AS attempts FROM all_scores GROUP BY date_trunc('month',score_date) ORDER BY date_trunc('month',score_date)
    """),params).mappings().all()
    at_risk=db.execute(text("""
      WITH course_students AS (SELECT DISTINCT s.student_id,s.name,s.email,s.class FROM student s LEFT JOIN course_enrollment e ON e.student_id=s.student_id LEFT JOIN course c ON c.course_id=e.course_id WHERE s.teacher_id=:tid AND (:course IS NULL OR c.course_id=:course)),
      all_scores AS (
       SELECT a.student_id,a.score FROM assessment a JOIN course_students s ON s.student_id=a.student_id
       UNION ALL SELECT q.student_id,q.score FROM quiz_attempt q JOIN course_students s ON s.student_id=q.student_id
       UNION ALL SELECT sub.student_id,100.0*sub.points_earned/NULLIF(a.total_points,0) FROM teacher_submission sub JOIN teacher_assessment a ON a.assessment_id=sub.assessment_id JOIN course c ON c.course_id=a.course_id JOIN course_students s ON s.student_id=sub.student_id WHERE sub.status='graded' AND (:course IS NULL OR c.course_id=:course)
      )
      SELECT s.student_id,s.name,s.email,s.class,ROUND(AVG(a.score),1) AS average_score,COUNT(a.score) AS scored_attempts FROM course_students s JOIN all_scores a ON a.student_id=s.student_id GROUP BY s.student_id,s.name,s.email,s.class HAVING AVG(a.score)<50 ORDER BY AVG(a.score)
    """),params).mappings().all()
    return {"classes":[dict(r) for r in classes],"trend":[dict(r) for r in scores],"at_risk":[dict(r) for r in at_risk]}

@router.get("/api/student/assessments")
def student_assessments(request:Request,db:Session=Depends(get_db)):
    student=current(request,db,"student");sid=student["student_id"]
    rows=db.execute(text("SELECT a.assessment_id,a.title,a.description,a.kind,a.due_at,a.total_points,c.title AS class_title,s.status,s.points_earned FROM teacher_assessment a JOIN course c ON c.course_id=a.course_id JOIN course_enrollment e ON e.course_id=c.course_id AND e.student_id=:sid LEFT JOIN teacher_submission s ON s.assessment_id=a.assessment_id AND s.student_id=:sid WHERE a.is_published=TRUE ORDER BY a.due_at NULLS LAST"),{"sid":sid}).mappings().all()
    return {"assessments":[dict(r) for r in rows]}

@router.get("/api/student/assessments/{assessment_id}")
def get_student_assessment(assessment_id:int,request:Request,db:Session=Depends(get_db)):
    student=current(request,db,"student");sid=student["student_id"]
    allowed=db.execute(text("SELECT a.assessment_id,a.title,a.description,a.kind,a.due_at,a.total_points FROM teacher_assessment a JOIN course_enrollment e ON e.course_id=a.course_id WHERE a.assessment_id=:id AND e.student_id=:sid AND a.is_published=TRUE"),{"id":assessment_id,"sid":sid}).mappings().first()
    if not allowed:raise HTTPException(404,"Assessment not found")
    questions=db.execute(text("SELECT question_id,question_text,answer_type,choices,points FROM teacher_assessment_question WHERE assessment_id=:id ORDER BY question_id"),{"id":assessment_id}).mappings().all()
    return {"assessment":dict(allowed),"questions":[{**dict(q),"choices":json.loads(q["choices"]) if q["choices"] else []} for q in questions]}

@router.post("/api/student/assessments/{assessment_id}/submit",status_code=201)
def submit_student_assessment(assessment_id:int,data:StudentAssessmentSubmission,request:Request,db:Session=Depends(get_db)):
    student=current(request,db,"student");sid=student["student_id"]
    assessment=db.execute(text("SELECT a.assessment_id,a.kind,a.total_points,a.due_at FROM teacher_assessment a JOIN course_enrollment e ON e.course_id=a.course_id WHERE a.assessment_id=:id AND e.student_id=:sid AND a.is_published=TRUE"),{"id":assessment_id,"sid":sid}).mappings().first()
    if not assessment:raise HTTPException(404,"Assessment not found")
    if assessment["due_at"] and assessment["due_at"]<datetime.now(timezone.utc):raise HTTPException(409,"The due date has passed")
    if db.execute(text("SELECT 1 FROM teacher_submission WHERE assessment_id=:a AND student_id=:s"),{"a":assessment_id,"s":sid}).first():raise HTTPException(409,"You already submitted this assessment")
    questions=db.execute(text("SELECT question_id,answer_type,choices,correct_answer,points FROM teacher_assessment_question WHERE assessment_id=:id ORDER BY question_id"),{"id":assessment_id}).mappings().all()
    by_id={q["question_id"]:q for q in questions};answers={a.question_id:a.answer for a in data.answers}
    if set(answers)-set(by_id):raise HTTPException(422,"An answer refers to a question outside this assessment")
    if not questions or set(answers)!=set(by_id):raise HTTPException(422,"Answer every assessment prompt")
    if any(not answers[qid].strip() for qid in by_id):raise HTTPException(422,"Answers cannot be blank")
    auto=assessment["kind"]=="quiz" and all(q["correct_answer"] is not None for q in questions)
    earned=None
    if auto:
        raw=sum(float(q["points"]) for q in questions)
        earned=round(float(assessment["total_points"])*sum(float(q["points"]) for q in questions if answers.get(q["question_id"],"").strip().casefold()==q["correct_answer"].strip().casefold())/raw,2)
    submission_id=db.execute(text("INSERT INTO teacher_submission(assessment_id,student_id,answers,points_earned,status,graded_at) VALUES (:a,:s,:answers,:points,:status,:graded) RETURNING submission_id"),{"a":assessment_id,"s":sid,"answers":json.dumps(answers),"points":earned,"status":"graded" if auto else "submitted","graded":datetime.now(timezone.utc) if auto else None}).scalar_one();db.commit()
    return {"submission_id":submission_id,"points_earned":earned,"total_points":float(assessment["total_points"]),"status":"graded" if auto else "submitted"}
