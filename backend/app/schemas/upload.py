from pydantic import BaseModel, Field


class UploadUrlRequest(BaseModel):
    filename: str = Field(min_length=1)
    content_type: str = Field(min_length=1)


class UploadUrlResponse(BaseModel):
    upload_url: str
    key: str


class DownloadUrlResponse(BaseModel):
    url: str
