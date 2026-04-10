from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import router


app = FastAPI(
    title="VeriAI Coding Profile Analyzer",
    version="1.0.0",
    description="Coding profile intelligence microservice for GitHub, LeetCode, and Codeforces.",
)

app.include_router(router)
