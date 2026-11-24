from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, model_validator

class ClassInput(BaseModel):
    title: str = Field(min_length=2, max_length=150)
    description: str = Field(min_length=1, max_length=4000)
    department: str = Field(min_length=2, max_length=100)
    target_class: str = Field(min_length=1, max_length=50)
    syllabus: str = Field(default="", max_length=12000)

class MaterialInput(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    material_type: str = Field(default="link", max_length=40)
    resource_url: str = Field(min_length=8, max_length=1000)

class AnnouncementInput(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    body: str = Field(min_length=2, max_length=5000)

class AssessmentQuestionInput(BaseModel):
    question_text: str = Field(min_length=2, max_length=2000)
    answer_type: Literal["multiple_choice", "short_answer"]
    choices: list[str] = Field(default_factory=list, max_length=10)
    correct_answer: str | None = Field(default=None, max_length=1000)
    points: float = Field(default=1, gt=0, le=1000)

    @model_validator(mode="after")
    def validate_choices(self):
        if self.answer_type == "multiple_choice":
            if len(self.choices) < 2 or not self.correct_answer or self.correct_answer not in self.choices:
                raise ValueError("Multiple-choice questions need at least two choices and a correct choice")
        return self

class AssessmentInput(BaseModel):
    course_id: int = Field(ge=1)
    title: str = Field(min_length=2, max_length=160)
    description: str = Field(default="", max_length=4000)
    kind: Literal["quiz", "assignment"]
    due_at: datetime | None = None
    total_points: float = Field(default=100, gt=0, le=100000)
    rubric: str = Field(default="", max_length=12000)
    questions: list[AssessmentQuestionInput] = Field(default_factory=list, max_length=100)

class GradeEntryInput(BaseModel):
    category: str = Field(min_length=2, max_length=80)
    item_name: str = Field(min_length=2, max_length=160)
    score: float = Field(ge=0)
    max_score: float = Field(gt=0)

class GradeWeight(BaseModel):
    category: str = Field(min_length=2, max_length=80)
    weight_percent: float = Field(ge=0, le=100)

class GradeWeightsInput(BaseModel):
    weights: list[GradeWeight] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def total_is_one_hundred(self):
        if abs(sum(w.weight_percent for w in self.weights) - 100) > 0.01:
            raise ValueError("Grade weights must add up to 100 percent")
        return self

class StudentAssessmentAnswer(BaseModel):
    question_id: int = Field(ge=1)
    answer: str = Field(max_length=4000)

class StudentAssessmentSubmission(BaseModel):
    answers: list[StudentAssessmentAnswer] = Field(default_factory=list, max_length=100)

class ManualGradeInput(BaseModel):
    points_earned: float = Field(ge=0)
    feedback: str = Field(default="", max_length=4000)
