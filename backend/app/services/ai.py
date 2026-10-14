from collections.abc import Callable


def generate_video_from_image(
    image_url: str,
    motion_prompt: str | None,
    progress_callback: Callable[[int], None] | None = None,
) -> tuple[bytes, str]:
    raise RuntimeError("AI provider integration not implemented yet")
