from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.models.upload import DataType, UploadStatus
from typing import Optional

class UploadBase(BaseModel):
    filename: str
    status: str
    data_type: DataType
    error_message: Optional[str] = None

class UploadCreate(UploadBase):
    sftp_path: str
    user_id: int
    status: UploadStatus = UploadStatus.PENDING

class UploadResponse(UploadBase):
    id: int
    sftp_path: str
    status: UploadStatus
    timestamp: datetime
    user_id: int

    model_config = ConfigDict(from_attributes=True)