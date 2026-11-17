from typing import Literal
from pydantic import BaseModel, EmailStr, Field, field_validator

class RegisterInput(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    class_name: str | None = Field(default=None, max_length=50)
    teacher_id: int | None = Field(default=None, ge=1)
    department: str | None = Field(default=None, max_length=100)

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, value):
        value = " ".join(value.split())
        if len(value) < 2: raise ValueError("Enter your full name")
        return value

class LoginInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    remember_me: bool = False

class AccountOut(BaseModel):
    name: str
    email: str
    role: Literal["student", "teacher"]
