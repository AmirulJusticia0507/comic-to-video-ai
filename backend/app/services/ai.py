from __future__ import annotations

import base64
from functools import lru_cache
from typing import Any

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
            model=model or settings.ai_image_model or settings.ai_provider_model,
            prompt=prompt,
            **kwargs,
        )
        b64_json = response.data[0].b64_json
        if not b64_json:
            raise ValueError("image generation response had no b64_json data")
        return base64.b64decode(b64_json)
