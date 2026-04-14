from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.database.models import RawUpload, Student, StudentProfile
from app.schemas.student import (
    AcademicsData,
    CodingData,
    StudentData,
    StudentProfileCreate,
    StudentProfileResponse,
    StudentProfileStoreResponse,
)
from app.services.master_service import normalize_skills

logger = logging.getLogger(__name__)


class ProfileService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def save_profile(self, payload: StudentProfileCreate) -> StudentProfileStoreResponse:
        student = self.db.query(Student).filter(Student.email == payload.student.email).one_or_none()
        if student is None:
            student = Student(
                name=payload.student.name,
                email=payload.student.email,
                phone=payload.student.phone,
                branch=payload.student.branch,
                cgpa=payload.student.cgpa,
                cgpa_verified=payload.student.cgpa_verified,
            )
            self.db.add(student)
            self.db.flush()
        else:
            student.name = payload.student.name
            student.phone = payload.student.phone
            student.branch = payload.student.branch
            student.cgpa = payload.student.cgpa
            student.cgpa_verified = payload.student.cgpa_verified

        profile = self.db.query(StudentProfile).filter(StudentProfile.student_id == student.id).one_or_none()
        skills = normalize_skills(payload.skills)
        if profile is None:
            profile = StudentProfile(
                student_id=student.id,
                skills=skills,
                skills_json=skills,
                coding_persona=payload.coding.persona,
                coding_score=payload.coding.score,
                academic_score=payload.academics.score,
                overall_score=payload.overall_score,
                github_data=payload.github_data,
                leetcode_data=payload.leetcode_data,
                resume_data=payload.resume_data,
                academic_data=payload.academic_data,
                last_analyzed_at=datetime.now(UTC),
            )
            self.db.add(profile)
            self.db.flush()
        else:
            profile.skills = skills
            profile.skills_json = skills
            profile.coding_persona = payload.coding.persona
            profile.coding_score = payload.coding.score
            profile.academic_score = payload.academics.score
            profile.overall_score = payload.overall_score
            profile.github_data = payload.github_data
            profile.leetcode_data = payload.leetcode_data
            profile.resume_data = payload.resume_data
            profile.academic_data = payload.academic_data
            profile.last_analyzed_at = datetime.now(UTC)

        if payload.resume_url or payload.marksheet_url:
            raw_upload = RawUpload(
                student_id=student.id,
                resume_url=payload.resume_url,
                marksheet_url=payload.marksheet_url,
            )
            self.db.add(raw_upload)

        self.db.commit()
        logger.info("Stored profile for student_id=%s email=%s", student.id, student.email)
        return StudentProfileStoreResponse(student_id=student.id, profile_id=profile.id)

    def get_profile(self, student_id: int) -> StudentProfileResponse:
        profile = self.db.query(StudentProfile).filter(StudentProfile.student_id == student_id).one_or_none()
        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found.")

        student = profile.student
        if student is None:
            raise HTTPException(status_code=500, detail="Profile exists without student record.")

        return StudentProfileResponse(
            id=profile.id,
            student_id=student.id,
            student=StudentData(
                name=student.name,
                email=student.email,
                phone=student.phone,
                branch=student.branch,
                cgpa=student.cgpa,
                cgpa_verified=student.cgpa_verified,
            ),
            skills=profile.skills or [],
            coding=CodingData(
                persona=profile.coding_persona,
                score=profile.coding_score,
                github=profile.github_data or {},
                leetcode=profile.leetcode_data or {},
            ),
            academics=AcademicsData(
                cgpa=student.cgpa,
                verified=student.cgpa_verified,
                score=profile.academic_score,
            ),
            overall_score=profile.overall_score,
            resume_data=profile.resume_data or {},
            academic_data=profile.academic_data or {},
            github_data=profile.github_data or {},
            leetcode_data=profile.leetcode_data or {},
            last_analyzed_at=profile.last_analyzed_at,
            created_at=student.created_at,
        )

