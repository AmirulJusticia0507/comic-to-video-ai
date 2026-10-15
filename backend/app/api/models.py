from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(prefix="/v1", tags=["models"])


@router.get("/models")
def list_models():
    settings = get_settings()
    configured_models = (
        settings.ai_provider_model,
        settings.ai_image_model,
        settings.video_model,
    )
    model_ids = list(dict.fromkeys(model_id for model_id in configured_models if model_id))
    return {
        "object": "list",
        "data": [
            {
                "id": model_id,
                "object": "model",
                "created": 0,
                "owned_by": "comic-to-video-ai",
            }
            for model_id in model_ids
        ],
    }
