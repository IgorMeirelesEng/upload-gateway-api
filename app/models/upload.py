from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class DataType(str, enum.Enum):
    VISITA1_REDCAP = "visita_01_redcap" #pdf
    VISITA2_REDCAP = "visita_02_redcap" #pdf
    RELOGIOS = "dados_relogios" #pasta
    ANEL = "dados_anel" #pasta
    REDCAP = "redcap" #pasta
    BIOIMPEDANCIA = "dados_bioimpedancia" #pasta

class UploadStatus(str, enum.Enum):
    PENDING = "pending"
    UPLOADED = "uploaded"
    FAILED = "failed"

class Upload(Base):
    __tablename__ = "upload_logs"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    data_type = Column(SAEnum(DataType, name='datatype_enum'), nullable=False)
    status = Column(SAEnum(UploadStatus, name='uploadstatus_enum'), nullable=False)
    sftp_path = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="uploads")