from __future__ import annotations

from spacy.language import Language
from spacy.matcher import PhraseMatcher

from app.utils.text import dedupe_preserve_order

SKILL_ONTOLOGY: dict[str, list[str]] = {
    "programming_languages": [
        "python",
        "java",
        "javascript",
        "typescript",
        "c++",
        "c#",
        "go",
        "rust",
        "kotlin",
        "swift",
        "sql",
        "c language",
        "r language",
        "matlab",
    ],
    "frameworks": [
        "fastapi",
        "django",
        "flask",
        "react",
        "next.js",
        "node.js",
        "spring boot",
        "tensorflow",
        "pytorch",
        "scikit-learn",
        "langchain",
        "streamlit",
    ],
    "databases": [
        "postgresql",
        "mysql",
        "mongodb",
        "sqlite",
        "redis",
        "elasticsearch",
        "dynamodb",
    ],
    "tools": [
        "docker",
        "kubernetes",
        "aws",
        "azure",
        "gcp",
        "git",
        "linux",
        "terraform",
        "jenkins",
        "github actions",
        "power bi",
        "tableau",
    ],
}

ALIASES: dict[str, str] = {
    "js": "JavaScript",
    "ts": "TypeScript",
    "c": "C Language",
    "r": "R Language",
    "node": "Node.js",
    "postgres": "PostgreSQL",
    "k8s": "Kubernetes",
    "scikit learn": "Scikit-learn",
    "sklearn": "Scikit-learn",
}


class SkillMatcher:
    def __init__(self, nlp: Language) -> None:
        self._nlp = nlp
        self._matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
        self._canonical_lookup: dict[str, str] = {}

        all_terms: set[str] = set()
        for category in SKILL_ONTOLOGY.values():
            all_terms.update(category)

        all_terms.update(ALIASES.keys())

        patterns = [nlp.make_doc(term) for term in sorted(all_terms)]
        self._matcher.add("SKILLS", patterns)

        for term in all_terms:
            canonical = ALIASES.get(term.lower(), term)
            self._canonical_lookup[term.lower()] = self._format_skill(canonical)

    def _format_skill(self, skill: str) -> str:
        exceptions = {
            "aws": "AWS",
            "gcp": "GCP",
            "c++": "C++",
            "c#": "C#",
            "c language": "C",
            "sql": "SQL",
            "r language": "R",
            "power bi": "Power BI",
            "github actions": "GitHub Actions",
            "next.js": "Next.js",
            "node.js": "Node.js",
        }
        key = skill.lower()
        if key in exceptions:
            return exceptions[key]
        return " ".join(token.capitalize() for token in skill.split())

    def extract(self, doc_text: str, section_text: str = "") -> list[str]:
        combined = f"{doc_text}\n{section_text}".strip()
        if not combined:
            return []

        doc = self._nlp.make_doc(combined)
        matches = self._matcher(doc)

        skills: list[str] = []
        for _, start, end in matches:
            raw = doc[start:end].text.strip().lower()
            canonical = self._canonical_lookup.get(raw)
            if canonical:
                skills.append(canonical)

        return dedupe_preserve_order(skills)
