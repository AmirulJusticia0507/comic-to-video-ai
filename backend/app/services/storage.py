import boto3

from app.core.config import get_settings

settings = get_settings()

ALLOWED_IMAGE_CONTENT_TYPES = {"image/png", "image/jpeg", "image/webp"}
MAX_IMAGE_SIZE_BYTES = 20 * 1024 * 1024
PRESIGNED_URL_EXPIRES_IN = 3600

_s3_client = boto3.client(
    "s3",
    endpoint_url=settings.storage_endpoint_url or None,
    aws_access_key_id=settings.storage_access_key or None,
    aws_secret_access_key=settings.storage_secret_key or None,
    region_name="auto",
)


def validate_image_content_type(content_type: str) -> bool:
    return content_type in ALLOWED_IMAGE_CONTENT_TYPES


def validate_image_size(content_length: int | None) -> bool:
    return content_length is None or content_length <= MAX_IMAGE_SIZE_BYTES


def generate_presigned_upload_url(key: str, content_type: str) -> str:
    if not validate_image_content_type(content_type):
        raise ValueError(f"content type {content_type} is not allowed")
    return _s3_client.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": settings.storage_bucket_name,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=PRESIGNED_URL_EXPIRES_IN,
    )


def generate_presigned_download_url(key: str) -> str:
    return _s3_client.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": settings.storage_bucket_name, "Key": key},
        ExpiresIn=PRESIGNED_URL_EXPIRES_IN,
    )


def upload_bytes(key: str, data: bytes, content_type: str) -> str:
    _s3_client.put_object(
        Bucket=settings.storage_bucket_name,
        Key=key,
        Body=data,
        ContentType=content_type,
    )
    return key
