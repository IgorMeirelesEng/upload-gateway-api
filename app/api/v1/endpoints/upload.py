from typing import Any, List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from sqlalchemy.orm import Session

import csv
import io
from datetime import datetime
from typing import Optional
from fastapi.responses import StreamingResponse


from app.core.database import get_db
from app.api import deps
from app.models.user import User
from app.models.upload import DataType, UploadStatus
from app.schemas import upload as upload_schema
from app.services.sftp import sftp_service
from app.crud import upload as crud_upload
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=List[upload_schema.UploadResponse])
async def upload_files(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
    files: List[UploadFile] = File(...), # Agora aceita Lista!
    data_type: DataType = Form(...)
) -> Any:
    """
    Recebe um ou múltiplos arquivos.
    - Se for Visita Redcap: Geralmente 1 arquivo.
    - Se for Relógio/Anel: Pode selecionar vários arquivos de uma vez.
    """
    
    if not files:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado.")

    
    metadata_base = {
        "uploaded_by": current_user.username,
        "user_role": current_user.role,
        "data_type": data_type.value,
        "batch_size": len(files),
        "timestamp_utc": str(datetime.utcnow())
    }

    upload_results = sftp_service.upload_batch(files, data_type.value, metadata_base)

    response_list = []

    for result in upload_results:

        status_enum = UploadStatus.UPLOADED if result["status"] == "uploaded" else UploadStatus.FAILED
        
        upload_in = upload_schema.UploadCreate(
            filename=result["filename"],
            data_type=data_type,
            sftp_path=result["sftp_path"],
            user_id=current_user.id,
            status=status_enum
        )
 
        db_log = crud_upload.create_upload_log(db, upload=upload_in)
        
        response_list.append(db_log)

    return response_list

@router.get("/export/csv")
def export_upload_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
    data_type: Optional[DataType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    """
    Gera um CSV com histórico de uploads.
    - Admin: Pode ver logs de todos (ou filtrar).
    - Usuário Comum: Só vê os seus próprios logs.
    """
    
    # 1. Regra de Permissão
    # Se for ADMIN, user_id = None (traz tudo).
    # Se for USER, user_id = current_user.id (traz só os dele).
    target_user_id = current_user.id if current_user.role != "admin" else None

    # 2. Busca no Banco
    logs = crud_upload.get_uploads_filtered(
        db=db,
        user_id=target_user_id,
        data_type=data_type,
        start_date=start_date,
        end_date=end_date
    )

    # 3. Cria o Arquivo CSV na Memória
    stream = io.StringIO()
    csv_writer = csv.writer(stream)

    # Cabeçalho do CSV
    csv_writer.writerow(["ID", "Arquivo", "Tipo", "Caminho SFTP", "Status", "Usuário", "Data (UTC)"])

    # Linhas de dados
    for log in logs:
        # log.owner.username acessa o nome do usuário via relacionamento
        username = log.owner.username if log.owner else "Desconhecido"
        
        csv_writer.writerow([
            log.id,
            log.filename,
            log.data_type.value,
            log.sftp_path,
            log.status.value,
            username,
            log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        ])

    # Prepara para leitura do início
    stream.seek(0)

    # 4. Retorna como Download de Arquivo
    filename = f"export_uploads_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    
    response = StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv"
    )
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    
    return response