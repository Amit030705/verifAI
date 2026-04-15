# VeriAI

Microservices for resume parsing, coding-profile analysis, and a combined orchestrator.

## Services

| Service | Dev port (host) | Description |
|---------|-----------------|-------------|
| [coding-analyzer](coding-analyzer/) | 18080 | GitHub / LeetCode / Codeforces analysis |
| [resume-analyzer](resume-analyzer/) | 18081 | PDF/DOCX → structured resume JSON |
| [master-service](master-service/) | 18082 | Parallel calls to both; single report + UI |
| [web](web/) | 18084 | Next.js student dashboard (`/dashboard`) |

## Quick start (development)

```bash
docker compose -f docker-compose.dev.yml up -d --build
```

Production-style ports: `docker-compose.prod.yml` (28xxx), including dashboard at `28084`.

## Future work

TPO JD parsing, PostgreSQL schema, and student ranking are specified in [docs/TPO_MATCHING_AND_JD_PLAN.md](docs/TPO_MATCHING_AND_JD_PLAN.md) (not implemented yet).
