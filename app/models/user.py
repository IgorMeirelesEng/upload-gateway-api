import enum
from sqlalchemy import Column, Integer, Boolean, String, Enum as SAEnum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    UPLOADER_TI = "uploader_ti"
    UPLOADER_SAUDE = "uploader_saude"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SAEnum(UserRole, name='userrole_enum'), default=UserRole.UPLOADER_SAUDE, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    uploads = relationship("Upload", back_populates="owner")