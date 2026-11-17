from pydantic import BaseModel, Field

class CourseRequestInput(BaseModel):
    title: str = Field(min_length=2, max_length=150)
    department: str = Field(min_length=2, max_length=100)
    target_class: str = Field(min_length=1, max_length=50)
    description: str = Field(min_length=10, max_length=2000)
    reason: str | None = Field(default=None, max_length=1000)
