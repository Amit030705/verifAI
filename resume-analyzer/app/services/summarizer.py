from __future__ import annotations


def generate_summary(
    education: list[str],
    skills: list[str],
    experience: list[str],
    projects: list[str],
) -> str:
    profile = "Candidate"

    edu_blob = " ".join(education).lower()
    if any(token in edu_blob for token in ["student", "b.tech", "b.e", "bachelor", "undergraduate", "final year"]):
        profile = "Computer Science student" if "computer" in edu_blob else "Engineering student"
    elif experience:
        profile = "Professional"

    top_skills = ", ".join(skills[:4]) if skills else "technical skill set"

    if experience and projects:
        context = "hands-on experience across industry and project work"
    elif experience:
        context = "practical industry experience"
    elif projects:
        context = "strong project-based implementation exposure"
    else:
        context = "a growing technical foundation"

    return f"{profile} with strengths in {top_skills} and {context}."
