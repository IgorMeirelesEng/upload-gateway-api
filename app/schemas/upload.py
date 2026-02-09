from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.models.upload import DataType, UploadStatus
from typing import Optional

class UploadBase(BaseModel):
    filename: str
    status: UploadStatus
    data_type: DataType
    sftp_path: str

class UploadCreate(UploadBase):
    user_id: int

class UploadResponse(UploadBase):
    id: int
    timestamp: datetime
    user_id: int

    class Config:
        from_attributes = True