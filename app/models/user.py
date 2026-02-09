import enum
from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class UserRole(enum.Enum):
    ADMIN = "admin"
    UPLOADER_TI = "uploader_ti"
    UPLOADER_SAUDE = "uploader_saude"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.UPLOADER_SAUDE, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    uploads = relationship("Upload", back_populates="owner")