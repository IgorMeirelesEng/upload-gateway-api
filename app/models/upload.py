from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.core.database import Base
import enum

class DataType(str, enum.Enum):
    VISITA1_REDCAP = "visita_01_redcap"
    VISITA2_REDCAP = "visita_02_redcap"
    RELOGIOS = "dados_relogios"
    ANEL = "dados_anel"
    BIOIMPEDANCIA = "dados_bioimpedancia"

class UploadStatus(str, enum.Enum):
    PENDING = "pending"
    UPLOADED = "uploaded"
    FAILED = "failed"

class Upload(Base):
    __tablename__ = "upload_logs"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    data_type = Column(Enum(DataType), nullable=False)
    sftp_path = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="uploads")