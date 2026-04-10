from pydantic import BaseModel, Field


class EducationEntry(BaseModel):
    institution: str = ""
    duration: str = ""
    degree: str = ""


class ExperienceEntry(BaseModel):
    company: str = ""
    duration: str = ""
    role: str = ""
    description: list[str] = Field(default_factory=list)


class ProjectEntry(BaseModel):
    title: str = ""
    tech_stack: list[str] = Field(default_factory=list)
    description: list[str] = Field(default_factory=list)


class ResumeAnalysisResponse(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    education: list[EducationEntry] = Field(default_factory=list)
    cgpa: str = ""
    skills: list[str] = Field(default_factory=list)
    projects: list[ProjectEntry] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    summary: str = ""
