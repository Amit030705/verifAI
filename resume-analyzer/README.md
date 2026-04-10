# VeriAI Resume Analyzer (FastAPI)

Production-structured Resume Analyzer microservice for VeriAI's multi-agent placement intelligence platform.

## Features

- FastAPI service with modular architecture
- Supports PDF and DOCX resume uploads
- Automatic PDF parser strategy selection (PyMuPDF + pdfplumber quality scoring)
- Regex + NLP hybrid extraction pipeline
- Skill extraction via ontology + spaCy phrase matching
- Consistent downstream JSON schema
- Minimal upload UI for manual QA/testing
- Graceful error handling and health check endpoint

## Project Structure

```text
resume-analyzer/
├── app/
│   ├── main.py
│   ├── api/
│   │   └── routes.py
│   ├── services/
│   │   ├── parser.py
│   │   ├── extractor.py
│   │   ├── skill_matcher.py
│   │   └── summarizer.py
│   ├── models/
│   │   └── response_model.py
│   ├── templates/
│   │   └── index.html
│   ├── static/
│   └── utils/
├── uploads/
├── requirements.txt
└── README.md
```

## Setup

1. Create and activate a Python 3.11+ virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Install at least one English spaCy model (service auto-selects best available):

```bash
python -m spacy download en_core_web_sm
```

Optional higher-accuracy models:

```bash
python -m spacy download en_core_web_md
python -m spacy download en_core_web_lg
```

## Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

Open UI:

- `http://localhost:8080/`

## API

### `POST /analyze-resume`

Accepts `multipart/form-data` with field `file` (`.pdf` or `.docx`).

Response schema:

```json
{
  "name": "",
  "email": "",
  "phone": "",
  "education": [],
  "cgpa": "",
  "skills": [],
  "projects": [],
  "experience": [],
  "certifications": [],
  "summary": ""
}
```

### `GET /`

Serves manual upload/test UI.

### `GET /health`

Simple service liveness endpoint.

## Notes

- The parser chooses the better PDF extraction output automatically using a text quality score.
- Section classification and completeness scoring are implemented internally to support future multi-agent orchestration.
- Uploaded files are removed after processing.
