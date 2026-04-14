from __future__ import annotations

import asyncio
from typing import Any

import cloudinary
import cloudinary.uploader

from app.config import Settings


def _configure_cloudinary(settings: Settings) -> None:
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )


def _upload_resume_sync(*, settings: Settings, resume_bytes: bytes, filename: str) -> str:
    _configure_cloudinary(settings)
    result: dict[str, Any] = cloudinary.uploader.upload(
        resume_bytes,
        resource_type="raw",
        folder=settings.cloudinary_resume_folder,
        public_id=filename.rsplit(".", 1)[0],
        overwrite=False,
        use_filename=True,
        unique_filename=True,
    )
    secure_url = result.get("secure_url")
    if not isinstance(secure_url, str) or not secure_url.strip():
        raise ValueError("Cloudinary upload succeeded but no secure_url returned.")
    return secure_url


async def upload_resume_to_cloudinary(*, settings: Settings, resume_bytes: bytes, filename: str) -> str:
    if not settings.cloudinary_cloud_name or not settings.cloudinary_api_key or not settings.cloudinary_api_secret:
        raise ValueError("Cloudinary is not configured. Set CLOUDINARY_CLOUD_NAME/API_KEY/API_SECRET.")
    return await asyncio.to_thread(
        _upload_resume_sync,
        settings=settings,
        resume_bytes=resume_bytes,
        filename=filename,
    )

