from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StudentData(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=3, max_length=255)
    roll_no: str | None = Field(default=None, min_length=1, max_length=64)
    phone: str = Field(min_length=7, max_length=32)
    branch: str = Field(min_length=1, max_length=128)
    cgpa: float | None = Field(default=None, ge=0, le=10)
    cgpa_verified: bool = False

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        v = value.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("invalid email format")
        return v

    @field_validator("name", "phone", "branch")
    @classmethod
    def trim_required(cls, value: str) -> str:
        v = value.strip()
        if not v:
            raise ValueError("field cannot be blank")
        return v

    @field_validator("roll_no")
    @classmethod
    def normalize_roll_no(cls, value: str | None) -> str | None:
        if value is None:
            return None
        v = value.strip().upper()
        if not v:
            raise ValueError("roll_no cannot be blank")
        return v


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        v = value.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("invalid email format")
        return v

class LoginRequest(BaseModel):
    identifier: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("identifier")
    @classmethod
    def normalize_identifier(cls, value: str) -> str:
        return value.strip()


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    student_id: int
    email: str
    roll_no: str | None = None


class RegisterResponse(BaseModel):
    success: bool = True
    student_id: int
    message: str = "Registration successful."


class CodingData(BaseModel):
    persona: str = ""
    score: float = Field(default=0.0, ge=0, le=100)
    github: dict[str, Any] = Field(default_factory=dict)
    leetcode: dict[str, Any] = Field(default_factory=dict)


class AcademicsData(BaseModel):
    cgpa: float | None = Field(default=None, ge=0, le=10)
    verified: bool = False
    score: float = Field(default=0.0, ge=0, le=100)


class StudentAnalyzeResponse(BaseModel):
    student: StudentData
    skills: list[str] = Field(default_factory=list)
    coding: CodingData = Field(default_factory=CodingData)
    academics: AcademicsData = Field(default_factory=AcademicsData)
    overall_score: float = Field(default=0.0, ge=0, le=100)
    resume_url: str | None = None


class StudentProfileCreate(StudentAnalyzeResponse):
    resume_data: dict[str, Any] = Field(default_factory=dict)
    academic_data: dict[str, Any] = Field(default_factory=dict)
    github_data: dict[str, Any] = Field(default_factory=dict)
    leetcode_data: dict[str, Any] = Field(default_factory=dict)
    resume_url: str | None = None
    marksheet_url: str | None = None

    @field_validator("skills")
    @classmethod
    def normalize_skills(cls, value: list[str]) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for skill in value:
            s = skill.strip().lower()
            if not s or s in seen:
                continue
            seen.add(s)
            out.append(s)
        return out


class StudentProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    student: StudentData
    skills: list[str] = Field(default_factory=list)
    coding: CodingData
    academics: AcademicsData
    overall_score: float
    resume_url: str | None = None
    resume_data: dict[str, Any] = Field(default_factory=dict)
    academic_data: dict[str, Any] = Field(default_factory=dict)
    github_data: dict[str, Any] = Field(default_factory=dict)
    leetcode_data: dict[str, Any] = Field(default_factory=dict)
    last_analyzed_at: datetime
    created_at: datetime


class StudentProfileStoreResponse(BaseModel):
    success: bool = True
    student_id: int
    profile_id: int
    message: str = "Profile stored successfully."

