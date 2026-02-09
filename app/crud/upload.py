from sqlalchemy.orm import Session
from app.models.upload import Upload, DataType
from app.schemas.upload import UploadCreate
from datetime import datetime
from typing import Optional, List

def create_upload_log(db: Session, upload: UploadCreate):
    
    db_upload = Upload(
        filename=upload.filename,
        data_type=upload.data_type,
        sftp_path=upload.sftp_path,
        user_id=upload.user_id,
        status=upload.status
    )
    
    db.add(db_upload)
    db.commit()
    db.refresh(db_upload)
    return db_upload

def get_uploads_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(Upload).filter(Upload.user_id == user_id).offset(skip).limit(limit).all()

def get_all_uploads(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Upload).offset(skip).limit(limit).all()

def get_uploads_filtered(
    db: Session, 
    user_id: Optional[int] = None, 
    data_type: Optional[DataType] = None, 
    start_date: Optional[datetime] = None, 
    end_date: Optional[datetime] = None
) -> List[Upload]:
    query = db.query(Upload)

    if user_id:
        query = query.filter(Upload.user_id == user_id)
    
    if data_type:
        query = query.filter(Upload.data_type == data_type)
    
    if start_date:
        query = query.filter(Upload.timestamp >= start_date)
        
    if end_date:
        query = query.filter(Upload.timestamp <= end_date)
        
    # Ordena do mais recente para o mais antigo
    return query.order_by(Upload.timestamp.desc()).all()