# VeriAI JD Analyzer (FastAPI)

Standalone JD analyzer microservice that parses raw job descriptions into strict JSON schema using Groq.

## Features

- FastAPI microservice with dedicated parser service
- Strict JSON extraction contract for combined JD + TPO selection constraints
- Groq integration using `llama-3.3-70b-versatile`
- Built-in local frontend for manual testing (`GET /`)
- Health endpoint for orchestration checks (`GET /health`)

## Project Structure

```text
jd-analyzer/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   └── routes.py
│   ├── models/
│   │   └── response_model.py
│   ├── services/
│   │   └── jd_analyzer_service.py
│   ├── templates/
│   │   └── index.html
│   └── static/
├── requirements.txt
└── README.md
```

## Setup

1. Create and activate a Python 3.11+ virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Export required environment variable:

```bash
export GROQ_API_KEY="your_groq_api_key"
```

Optional overrides:

```bash
export GROQ_MODEL="llama-3.3-70b-versatile"
export GROQ_TIMEOUT_SECONDS="30"
```

## Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8085
```

Open:

- UI: `http://localhost:8085/`
- Health: `http://localhost:8085/health`

## API

### `POST /analyze-jd`

Request:

```json
{
  "jd_text": "Job description text..."
}
```

Response schema:

```json
{
  "job_title": "string | null",
  "role_type": "full_time | internship | contract | part_time | unknown",
  "required_skills": ["string"],
  "preferred_skills": ["string"],
  "min_experience_years": "number | null",
  "accepts_freshers": "boolean",
  "key_traits": ["string"],
  "education_requirements": ["string"],
  "location": "string | null",
  "domain": "string | null",
  "tools_and_technologies": ["string"],
  "responsibilities": ["string"],
  "duration": "string | null",
  "work_type": "string | null",
  "target_student_count": "number | null",
  "exclude_active_backlogs": "boolean",
  "placement_filter": "unplaced_only | placed_or_unplaced",
  "placement_exception_roll_nos": ["string"],
  "min_cgpa": "number | null",
  "allowed_branches": ["string"],
  "gender_filter": "women_only | men_only | all_genders | custom_text",
  "gender_filter_raw": "string | null",
  "branch_constraint_raw": "string | null",
  "branch_inference_reason": "string | null"
}
```

Normalization notes:
- Skills/tools/traits are canonicalized to lowercase for matching safety.
- Common synonyms are mapped (e.g. `ui & ux design` -> `ui/ux design`, `reactjs` -> `react`, `js` -> `javascript`).
- Roll number exceptions are uppercased and deduplicated.
- Branch constraints are normalized to canonical short codes (`cse`, `it`, `ece`, ...).
- `placement_filter` defaults to `placed_or_unplaced` when not explicitly constrained.
- `gender_filter` supports `women_only`, `men_only`, `all_genders`, `custom_text`.
- `branch_constraint_raw` + `branch_inference_reason` provide explainability for inferred branch-family mappings.

Branch-family inference examples:

| Input phrase | Inferred `allowed_branches` |
| --- | --- |
| `CSE related` | `["cse", "it", "aiml", "ds"]` |
| `computer science related` | `["cse", "it", "aiml", "ds"]` |

Gender normalization examples:

| Input phrase | `gender_filter` |
| --- | --- |
| `only girls`, `female only`, `for women` | `women_only` |
| `only boys`, `male only`, `for men` | `men_only` |
| `any gender`, `mixed` | `all_genders` |
| custom phrase | `custom_text` + `gender_filter_raw` |

## Notes

- This service is intentionally standalone for independent testing and deployment.
- Future orchestration integration can be added in `master-service` without changing this parser contract.
