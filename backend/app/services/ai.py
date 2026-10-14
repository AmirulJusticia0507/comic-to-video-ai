from __future__ import annotations

import base64
import time
from collections.abc import Callable
from functools import lru_cache
from typing import Any

import httpx
from openai import OpenAI

from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_ai_client() -> OpenAI:
    settings = get_settings()
    return OpenAI(
        api_key=settings.ai_provider_api_key,
        base_url=settings.ai_provider_base_url,
    )


class AIService:
    def __init__(self, client: OpenAI | None = None) -> None:
        self.client = client or get_ai_client()

    def create_client(self) -> OpenAI:
        return get_ai_client()

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        **kwargs: Any,
    ) -> str:
        settings = get_settings()
        response = self.client.chat.completions.create(
            model=model or settings.ai_provider_model,
            messages=messages,
            **kwargs,
        )
        choice = response.choices[0]
        return choice.message.content or ""

    def generate_image(
        self,
        prompt: str,
        model: str | None = None,
        **kwargs: Any,
    ) -> bytes:
        settings = get_settings()
        response = self.client.images.generate(
            model=model or settings.ai_provider_model,
            prompt=prompt,
            **kwargs,
        )
        b64_json = response.data[0].b64_json
        if not b64_json:
            raise ValueError("image generation response had no b64_json data")
        return base64.b64decode(b64_json)

    def generate_video(
        self,
        image_url: str,
        motion_prompt: str | None = None,
        model: str | None = None,
        progress_callback: Callable[[int], None] | None = None,
        poll_interval_seconds: int = 5,
        timeout_seconds: int = 600,
        **kwargs: Any,
    ) -> tuple[bytes, str]:
        settings = get_settings()
        model = model or settings.ai_video_model
        if not model:
            raise ValueError("AI video model is not configured (set AI_VIDEO_MODEL)")

        payload: dict[str, Any] = {"model": model, "image": image_url}
        if motion_prompt:
            payload["prompt"] = motion_prompt

        headers = {"Authorization": f"Bearer {settings.ai_provider_api_key}"}
        with httpx.Client(timeout=timeout_seconds) as client:
            response = client.post(
                f"{settings.ai_provider_base_url}/videos",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            job_id = response.json().get("id")
            if not job_id:
                raise ValueError("video generation response had no job id")

            deadline = time.monotonic() + timeout_seconds
            while True:
                if progress_callback:
                    progress_callback(50)
                poll = client.get(
                    f"{settings.ai_provider_base_url}/videos/{job_id}",
                    headers=headers,
                )
                poll.raise_for_status()
                result = poll.json()
                status = result.get("status")
                if status == "succeeded":
                    video_url = (
                        result.get("video", {}).get("url")
                        or result.get("url")
                        or result.get("output")
                    )
                    if not video_url:
                        raise ValueError("video generation succeeded but returned no url")
                    if progress_callback:
                        progress_callback(100)
                    video = client.get(video_url)
                    video.raise_for_status()
                    return video.content, video.headers.get("content-type", "video/mp4")
                if status in ("failed", "canceled"):
                    raise ValueError(f"video generation {status}: {result.get('error')}")
                if time.monotonic() > deadline:
                    raise ValueError("video generation timed out")
                time.sleep(poll_interval_seconds)


def generate_video_from_image(
    image_url: str,
    motion_prompt: str | None,
    progress_callback: Callable[[int], None] | None = None,
) -> tuple[bytes, str]:
    return AIService().generate_video(
        image_url=image_url,
        motion_prompt=motion_prompt,
        progress_callback=progress_callback,
    )
