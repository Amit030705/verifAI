from __future__ import annotations


def generate_recruiter_summary(
    *,
    coding_persona: str,
    inferred_strengths: list[str],
    engineering_maturity_score: int,
    consistency_score: int,
    leetcode_depth: int,
    codeforces_strength: int,
) -> tuple[str, str]:
    strengths = ", ".join(inferred_strengths[:3]) if inferred_strengths else "general software development"
    summary = (
        f"{coding_persona} profile with strengths in {strengths}. "
        f"Engineering maturity is {engineering_maturity_score}/100 with consistency at {consistency_score}/100. "
        f"Algorithmic depth is {leetcode_depth}/100 and competitive signal is {codeforces_strength}/100."
    )

    if engineering_maturity_score >= 80 and consistency_score >= 70:
        recommendation = "Highly Recommended"
    elif engineering_maturity_score >= 68:
        recommendation = "Recommended"
    elif engineering_maturity_score >= 50:
        recommendation = "Moderate Fit"
    else:
        recommendation = "Low Fit"

    return summary, recommendation
