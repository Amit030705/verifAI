# VeriAI Coding Profile Analyzer (FastAPI)

Second AI agent for VeriAI: collects, normalizes, and scores candidate coding performance from GitHub, LeetCode, and optional Codeforces.

## What This Service Does

- Accepts usernames or profile links
- Fetches platform stats asynchronously
- Handles unstable endpoints with retry logic
- Normalizes all profiles into one schema
- Computes platform scores + overall coding strength score (out of 100)
- Serves a lightweight web UI for manual testing

## Project Structure

```text
coding-analyzer/
├── app/
│   ├── main.py
│   ├── api/
│   │   └── routes.py
│   ├── services/
│   │   ├── github_service.py
│   │   ├── leetcode_service.py
│   │   ├── codeforces_service.py
│   │   ├── scoring_engine.py
│   │   └── normalizer.py
│   ├── models/
│   │   └── response_model.py
│   ├── templates/
│   │   └── index.html
│   └── utils/
├── requirements.txt
└── README.md
```

## API

### `POST /analyze-coding-profile`

Input JSON:

```json
{
  "github_username": "anshbhatt",
  "leetcode_username": "anshbhatt",
  "codeforces_username": "optional"
}
```

All fields can be either a username or a full profile URL.

### `GET /`

Simple testing dashboard.

### `GET /health`

Liveness check.

## Output Shape

The response contains:

- `github`: normalized GitHub profile intelligence
- `leetcode`: normalized LeetCode profile intelligence
- `codeforces`: normalized Codeforces profile intelligence (nullable fields when unavailable)
- `scores`: `github_score`, `leetcode_score`, `codeforces_score`, `overall_score`
- `coding_level`: `Beginner | Intermediate | Strong | Excellent`
- `errors`: per-platform fetch/validation errors (if any)
- `metadata`: request context and generation timestamp

## Scoring Weights

Default weights:

- GitHub: 40%
- LeetCode: 40%
- Codeforces: 20%

If one platform is unavailable, weights are proportionally re-normalized across available platforms.

## Setup

```bash
cd coding-analyzer
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

Open:

- `http://localhost:8080/`

## Notes

- GitHub integration uses the public API and profile-page parsing for pinned repos fallback.
- LeetCode integration uses GraphQL queries.
- Codeforces integration uses official Codeforces API.
- Existing scraper patterns from `/Users/anshbhatt/Developer/verifAI/Coding-Profile-Scrapper` were reused conceptually and restructured into isolated replaceable services.
