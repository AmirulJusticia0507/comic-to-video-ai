import os
import sys

import higgsfield_client
from dotenv import load_dotenv

load_dotenv(".env.local")

MODEL = "bytedance/seedance-2.5/text-to-video"
FAILED_STATUSES = ("failed", "canceled", "cancelled", "moderated", "rejected")


def check_credentials() -> str | None:
    raw = (os.environ.get("HF_KEY") or "").strip()
    if not raw:
        return "HF_KEY is not set in backend/.env.local"
    if raw == "your-api-key-id:your-api-key-secret":
        return "HF_KEY in backend/.env.local is still the placeholder"
    key_id, sep, secret = raw.partition(":")
    if not sep or not key_id.strip() or not secret.strip():
        return "HF_KEY must be in key-id:key-secret format"
    return None


def main() -> int:
    problem = check_credentials()
    if problem:
        print(f"BLOCKED: {problem}")
        print("Create credentials at https://console.higgsfield.ai and paste them into backend/.env.local")
        return 2

    try:
        result = higgsfield_client.subscribe(
            MODEL,
            arguments={
                "prompt": "A cinematic scene at sunset",
                "duration": 5,
                "resolution": "720p",
                "aspect_ratio": "16:9",
                "output_format": "mp4",
                "generate_audio": True,
            },
        )
    except higgsfield_client.exceptions.CredentialsMissedError:
        print("BLOCKED: HF_KEY is not set (or still the placeholder) in backend/.env.local")
        return 2
    except higgsfield_client.exceptions.HiggsfieldClientError as exc:
        print(f"FAILED: {type(exc).__name__}: {exc}")
        return 1

    status = str((result or {}).get("status", "")).lower()
    if status in FAILED_STATUSES:
        print(f"NOT SUCCESSFUL: request ended with status={status!r} detail={result}")
        return 1

    video_url = ((result or {}).get("video") or {}).get("url")
    if not video_url:
        print(f"FAILED: no video url in response (status={status!r}) result={result}")
        return 1

    print(f"status: {status}")
    print(f"video_url: {video_url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())