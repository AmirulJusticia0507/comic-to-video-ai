from __future__ import annotations

import time
import uuid

import httpx

from app.core.config import get_settings

TERMINAL_FAILURE_STATUSES = ("failed", "canceled", "cancelled", "rejected")
VIDEO_SUFFIX = ".mp4"


class VideoGenerationError(RuntimeError):
    pass


class VideoProviderNotConfigured(VideoGenerationError):
    pass


def _auth_headers(settings) -> dict[str, str]:
    if not settings.video_api_key_id or not settings.video_api_key_secret:
        raise VideoProviderNotConfigured(
            "video provider is not configured (set VIDEO_API_KEY_ID and VIDEO_API_KEY_SECRET)"
        )
    return {"Authorization": f"Key {settings.video_api_key_id}:{settings.video_api_key_secret}"}


def _submit(
    client: httpx.Client,
    settings,
    model: str,
    payload: dict,
) -> tuple[str, str]:
    url = f"{settings.video_api_base_url}/{model}"
    response = client.post(
        url,
        headers={**_auth_headers(settings), "Idempotency-Key": uuid.uuid4().hex},
        json=payload,
    )
    if response.status_code >= 400:
        raise VideoGenerationError(f"video submit failed ({response.status_code}): {response.text[:500]}")
    body = response.json()
    request_id = body.get("request_id")
    status_url = body.get("status_url") or f"{settings.video_api_base_url}/requests/{request_id}/status"
    if not request_id:
        raise VideoGenerationError(f"video submit response had no request_id: {response.text[:200]}")
    return request_id, status_url


def _poll(
    client: httpx.Client,
    settings,
    request_id: str,
    status_url: str,
    progress_callback: Callable[[int], None] | None,
) -> str:
    deadline = time.monotonic() + settings.video_timeout_seconds
    reported = 0
    while True:
        poll = client.get(status_url, headers=_auth_headers(settings))
        if poll.status_code >= 400:
            raise VideoGenerationError(f"video status failed ({poll.status_code}): {poll.text[:500]}")
        body = poll.json()
        status = str(body.get("status", "")).lower()

        if status in ("completed", "succeeded", "success"):
            video_url = (body.get("video") or {}).get("url") or body.get("url")
            if not video_url:
                raise VideoGenerationError("video completed but response had no url")
            if progress_callback:
                progress_callback(90)
            return video_url

        if status in TERMINAL_FAILURE_STATUSES:
            raise VideoGenerationError(f"video generation {status}: {body.get('error') or body.get('detail')}")

        if progress_callback:
            step = min(reported + 5, 85)
            reported = step
            progress_callback(step)

        if time.monotonic() > deadline:
            raise VideoGenerationError(f"video generation timed out after {settings.video_timeout_seconds}s (request {request_id})")
        time.sleep(settings.video_poll_interval_seconds)


def _download(client: httpx.Client, settings, video_url: str) -> tuple[bytes, str]:
    download = client.get(video_url)
    if download.status_code >= 400:
        raise VideoGenerationError(f"video download failed ({download.status_code})")
    content_type = download.headers.get("content-type", "video/mp4")
    return download.content, content_type.split(";")[0].strip()


def generate_video(
    image_url: str,
    motion_prompt: str | None = None,
    last_frame_url: str | None = None,
    duration_seconds: int | None = None,
    progress_callback: Callable[[int], None] | None = None,
    **_: object,
) -> tuple[bytes, str]:
    settings = get_settings()
    if settings.video_provider != "higgsfield":
        raise VideoProviderNotConfigured(f"unsupported video provider: {settings.video_provider!r}")

    payload: dict[str, object] = {
        "image_url": image_url,
        "prompt": motion_prompt or "Animate this comic panel with subtle natural motion and camera movement.",
        "duration": duration_seconds or settings.video_duration_seconds,
        "resolution": settings.video_resolution,
        "aspect_ratio": settings.video_aspect_ratio,
        "generate_audio": settings.video_generate_audio,
    }
    if last_frame_url:
        payload["end_image_url"] = last_frame_url

    timeout = settings.video_timeout_seconds + 120
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        request_id, status_url = _submit(client, settings, settings.video_model, payload)
        video_url = _poll(client, settings, request_id, status_url, progress_callback)
        data, content_type = _download(client, settings, video_url)

    if progress_callback:
        progress_callback(100)
    return data, content_type


def generate_video_from_image(
    image_url: str,
    motion_prompt: str | None,
    progress_callback: Callable[[int], None] | None = None,
) -> tuple[bytes, str]:
    return generate_video(
        image_url=image_url,
        motion_prompt=motion_prompt,
        progress_callback=progress_callback,
    )