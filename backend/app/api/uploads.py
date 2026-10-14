import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.auth import get_current_user
from app.models import User
from app.schemas.upload import DownloadUrlResponse, UploadUrlRequest, UploadUrlResponse
from app.services import storage

router = APIRouter(prefix="/uploads", tags=["uploads"])

_EXTENSION_BY_CONTENT_TYPE = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
}


@router.post("/presigned-url", response_model=UploadUrlResponse)
def create_presigned_upload_url(
    payload: UploadUrlRequest,
    current_user: User = Depends(get_current_user),
):
    if not storage.validate_image_content_type(payload.content_type):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"content type {payload.content_type} is not allowed",
        )
    key = f"panels/{current_user.id}/{uuid.uuid4().hex}.{_EXTENSION_BY_CONTENT_TYPE[payload.content_type]}"
    try:
        upload_url = storage.generate_presigned_upload_url(key, payload.content_type)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"failed to generate presigned url: {exc}",
        )
    return UploadUrlResponse(upload_url=upload_url, key=key)


@router.get("/download-url", response_model=DownloadUrlResponse)
def create_presigned_download_url(
    key: str = Query(min_length=1),
    current_user: User = Depends(get_current_user),
):
    try:
        url = storage.generate_presigned_download_url(key)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"failed to generate download url: {exc}",
        )
    return DownloadUrlResponse(url=url)
