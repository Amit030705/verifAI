from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"
    request_timeout_seconds: float = 30.0


def get_settings() -> Settings:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured.")

    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip() or "llama-3.3-70b-versatile"

    timeout_raw = os.getenv("GROQ_TIMEOUT_SECONDS", "30").strip()
    try:
        timeout = float(timeout_raw)
    except ValueError:
        timeout = 30.0

    return Settings(
        groq_api_key=api_key,
        groq_model=model,
        request_timeout_seconds=max(5.0, timeout),
    )
