from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.routers.dashboard import current

router = APIRouter(prefix="/api/student", tags=["personal learning"])

class SubmittedAnswer(BaseModel):
    question_id: int = Field(ge=1)
    answer: str = Field(max_length=1000)

class QuizSubmission(BaseModel):
    topic_id: int | None = Field(default=None, ge=1)
    answers: list[SubmittedAnswer] = Field(min_length=1, max_length=20)

def normalized(value: str) -> str:
    return " ".join(value.strip().lower().split()).rstrip(".!?")

def topic_summary(db: Session, student_id: int):
    rows = db.execute(text("""
        WITH all_answers AS (
          SELECT topic_id,question_id,answer,is_correct FROM student_response WHERE student_id=:sid
          UNION ALL
          SELECT q.topic_id,qa.question_id,qa.answer,qa.is_correct
          FROM quiz_answer qa JOIN quiz_attempt a ON a.attempt_id=qa.attempt_id
          JOIN question q ON q.question_id=qa.question_id WHERE a.student_id=:sid
        )
        SELECT t.topic_id,t.topic_name,COUNT(*) AS attempts,
               COUNT(*) FILTER (WHERE NOT a.is_correct) AS incorrect,
               ROUND(100.0*COUNT(*) FILTER (WHERE a.is_correct)/NULLIF(COUNT(*),0),0) AS accuracy
        FROM all_answers a JOIN topic t ON t.topic_id=a.topic_id
        GROUP BY t.topic_id,t.topic_name ORDER BY accuracy ASC,t.topic_name
    """), {"sid": student_id}).mappings().all()
    result=[]
    for row in rows:
        accuracy=int(row["accuracy"] or 0)
        severity="critical" if accuracy<50 else "needs improvement" if accuracy<70 else "moderate" if accuracy<85 else "strong"
        result.append({**dict(row),"attempts":int(row["attempts"]),"incorrect":int(row["incorrect"]),"accuracy":accuracy,"severity":severity})
    return result

@router.get("/learning-gaps")
def learning_gaps(request: Request, db: Session = Depends(get_db)):
    account=current(request,db,"student"); sid=account["student_id"]
    topics=topic_summary(db,sid)
    mistakes=db.execute(text("""
      WITH all_answers AS (
        SELECT r.topic_id,r.question_id,r.answer,r.is_correct,r.misconception_id,NULL::timestamp AS answered_at
        FROM student_response r WHERE r.student_id=:sid
        UNION ALL
        SELECT q.topic_id,qa.question_id,qa.answer,qa.is_correct,
               (SELECT sr.misconception_id FROM student_response sr WHERE sr.question_id=qa.question_id AND NOT sr.is_correct AND sr.misconception_id IS NOT NULL AND lower(trim(sr.answer))=lower(trim(qa.answer)) LIMIT 1),qa.created_at
        FROM quiz_answer qa JOIN quiz_attempt a ON a.attempt_id=qa.attempt_id
        JOIN question q ON q.question_id=qa.question_id WHERE a.student_id=:sid
      )
      SELECT x.topic_id,q.question_text,x.answer,q.correct_answer,x.is_correct,m.name AS pattern,m.description AS pattern_description
      FROM all_answers x JOIN question q ON q.question_id=x.question_id
      LEFT JOIN misconception m ON m.misconception_id=x.misconception_id
      WHERE x.is_correct=FALSE ORDER BY x.answered_at DESC NULLS LAST LIMIT 30
    """), {"sid":sid}).mappings().all()
    by_topic={}
    for row in mistakes:
        by_topic.setdefault(row["topic_id"],[]).append({k:row[k] for k in ("question_text","answer","correct_answer","pattern","pattern_description")})
    for topic in topics: topic["mistakes"]=by_topic.get(topic["topic_id"],[])[:4]
    return {"topics":topics,"summary":{"identified":sum(t["severity"]!="strong" for t in topics),"critical":sum(t["severity"]=="critical" for t in topics),"strong":sum(t["severity"]=="strong" for t in topics),"answers_reviewed":sum(t["attempts"] for t in topics)}}

@router.get("/learning-plan")
def learning_plan(request: Request, db: Session = Depends(get_db)):
    account=current(request,db,"student"); sid=account["student_id"]
    topics=topic_summary(db,sid)
    if not topics: return {"modules":[],"completed":0,"lesson_count":0}
    lessons=db.execute(text("""
       SELECT l.lesson_id,l.topic_id,t.topic_name,l.title,l.objective,l.lesson_text,l.sort_order,
              (p.completed_at IS NOT NULL) AS completed,p.completed_at
       FROM lesson l JOIN topic t ON t.topic_id=l.topic_id
       LEFT JOIN student_lesson_progress p ON p.lesson_id=l.lesson_id AND p.student_id=:sid
       ORDER BY l.sort_order
    """), {"sid":sid}).mappings().all()
    perf={t["topic_id"]:t for t in topics}
    modules=[]
    for topic_id,performance in perf.items():
        topic_lessons=[{k:r[k] for k in ("lesson_id","title","objective","lesson_text","sort_order","completed","completed_at")} for r in lessons if r["topic_id"]==topic_id]
        if topic_lessons and performance["severity"]!="strong":
            modules.append({"topic_id":topic_id,"topic_name":performance["topic_name"],"accuracy":performance["accuracy"],"severity":performance["severity"],"lessons":topic_lessons})
    return {"modules":modules,"completed":sum(l["completed"] for m in modules for l in m["lessons"]),"lesson_count":sum(len(m["lessons"]) for m in modules)}

@router.post("/learning-plan/lessons/{lesson_id}/complete")
def complete_lesson(lesson_id:int,request:Request,db:Session=Depends(get_db)):
    account=current(request,db,"student");sid=account["student_id"]
    exists=db.execute(text("SELECT 1 FROM lesson WHERE lesson_id=:id"),{"id":lesson_id}).first()
    if not exists: raise HTTPException(404,"Lesson not found")
    db.execute(text("INSERT INTO student_lesson_progress(student_id,lesson_id) VALUES (:sid,:lesson) ON CONFLICT(student_id,lesson_id) DO NOTHING"),{"sid":sid,"lesson":lesson_id});db.commit()
    return {"ok":True,"message":"Lesson marked complete"}

@router.get("/quizzes/questions")
def quiz_questions(request:Request,topic_id:int|None=None,db:Session=Depends(get_db)):
    account=current(request,db,"student")
    rows=db.execute(text("""
      SELECT MIN(q.question_id) AS question_id,q.question_text,q.difficulty,t.topic_id,t.topic_name
      FROM question q JOIN (SELECT question_id,MIN(topic_id) AS topic_id FROM student_response GROUP BY question_id) qt ON qt.question_id=q.question_id
      JOIN topic t ON t.topic_id=qt.topic_id
      WHERE (:topic_id IS NULL OR t.topic_id=:topic_id)
      GROUP BY q.question_text,q.difficulty,t.topic_id,t.topic_name
      ORDER BY t.topic_name,MIN(q.question_id)
    """),{"topic_id":topic_id}).mappings().all()
    options=db.execute(text("SELECT question_id,option_text FROM question_option WHERE question_id IN :ids ORDER BY question_id,sort_order").bindparams(bindparam("ids",expanding=True)),{"ids":[r["question_id"] for r in rows]}).mappings().all() if rows else []
    options_by_question={}
    for option in options: options_by_question.setdefault(option["question_id"],[]).append(option["option_text"])
    topics=db.execute(text("SELECT DISTINCT t.topic_id,t.topic_name FROM student_response r JOIN topic t ON t.topic_id=r.topic_id ORDER BY t.topic_name")).mappings().all()
    performance={t["topic_id"]:t for t in topic_summary(db,account["student_id"])}
    enriched=[{**dict(t),"accuracy":performance.get(t["topic_id"],{}).get("accuracy"),"severity":performance.get(t["topic_id"],{}).get("severity","not assessed")} for t in topics]
    questions=[{**dict(r),"options":options_by_question.get(r["question_id"],[])} for r in rows]
    return {"questions":questions,"topics":enriched}

@router.post("/quizzes/submit",status_code=201)
def submit_quiz(data:QuizSubmission,request:Request,db:Session=Depends(get_db)):
    account=current(request,db,"student");sid=account["student_id"]
    ids=[a.question_id for a in data.answers]
    if len(ids)!=len(set(ids)):raise HTTPException(422,"Each question can only be answered once per quiz")
    bank=db.execute(text("""
      SELECT q.question_id,q.question_text,q.correct_answer,t.topic_id,t.topic_name,m.description AS misconception
      FROM question q JOIN (SELECT question_id,MIN(topic_id) AS topic_id FROM student_response GROUP BY question_id) qt ON qt.question_id=q.question_id
      JOIN topic t ON t.topic_id=qt.topic_id
      LEFT JOIN LATERAL (SELECT mm.description FROM student_response sr JOIN misconception mm ON mm.misconception_id=sr.misconception_id WHERE sr.question_id=q.question_id AND sr.misconception_id IS NOT NULL LIMIT 1) m ON TRUE
      WHERE q.question_id IN :ids
    """).bindparams(bindparam("ids",expanding=True)),{"ids":ids}).mappings().all()
    by_id={r["question_id"]:r for r in bank}
    if len(by_id)!=len(ids):raise HTTPException(422,"One or more quiz questions are invalid")
    if data.topic_id and any(by_id[i]["topic_id"]!=data.topic_id for i in ids):raise HTTPException(422,"Questions do not match the selected topic")
    options=db.execute(text("SELECT question_id,option_text FROM question_option WHERE question_id IN :ids").bindparams(bindparam("ids",expanding=True)),{"ids":ids}).mappings().all()
    options_by_question={}
    for option in options: options_by_question.setdefault(option["question_id"],set()).add(option["option_text"])
    if any(a.question_id in options_by_question and a.answer not in options_by_question[a.question_id] for a in data.answers):
        raise HTTPException(422,"Choose one of the available answer options")
    correct=sum(normalized(a.answer)==normalized(by_id[a.question_id]["correct_answer"]) for a in data.answers)
    topic_id=data.topic_id or (bank[0]["topic_id"] if len({r["topic_id"] for r in bank})==1 else None)
    score=round(100*correct/len(ids),2)
    attempt_id=db.execute(text("INSERT INTO quiz_attempt(student_id,topic_id,score,correct_count,question_count) VALUES (:sid,:topic,:score,:correct,:total) RETURNING attempt_id"),{"sid":sid,"topic":topic_id,"score":score,"correct":correct,"total":len(ids)}).scalar_one()
    feedback=[]
    for answer in data.answers:
        q=by_id[answer.question_id];is_correct=normalized(answer.answer)==normalized(q["correct_answer"])
        db.execute(text("INSERT INTO quiz_answer(attempt_id,question_id,answer,is_correct) VALUES (:attempt,:question,:answer,:correct)"),{"attempt":attempt_id,"question":answer.question_id,"answer":answer.answer,"correct":is_correct})
        feedback.append({"question_id":answer.question_id,"question_text":q["question_text"],"your_answer":answer.answer,"correct_answer":q["correct_answer"],"is_correct":is_correct,"topic_name":q["topic_name"],"explanation":None if is_correct else (q["misconception"] or "Review the worked example and compare each step with your answer.")})
    db.commit()
    return {"attempt_id":attempt_id,"score":score,"correct_count":correct,"question_count":len(ids),"answers":feedback}
