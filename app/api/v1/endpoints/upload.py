from typing import Any, List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import csv
import io
from datetime import datetime

from app.core.database import get_db
from app.api import deps
from app.models.user import User, UserRole # Importe o UserRole
from app.models.upload import DataType, UploadStatus
from app.schemas import upload as upload_schema
from app.services.sftp import sftp_service
from app.crud import upload as crud_upload

router = APIRouter()

# --- NOTA: Removi o 'async' para evitar bloquear o servidor durante o upload SFTP ---
@router.post("/", response_model=List[upload_schema.UploadResponse])
def upload_files(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
    files: List[UploadFile] = File(...),
    data_type: DataType = Form(...)
) -> Any:
    """
    Realiza o upload de arquivos para o servidor SFTP e registra no banco.
    """
    if not files:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado.")

    # Metadados para o arquivo .json auxiliar no servidor
    metadata_base = {
        "uploaded_by": current_user.username,
        "user_role": current_user.role.value if hasattr(current_user.role, 'value') else current_user.role,
        "data_type": data_type.value,
        "batch_id": datetime.utcnow().timestamp(), # Útil para agrupar uploads
        "timestamp_utc": str(datetime.utcnow())
    }

    # Chama o serviço (síncrono/bloqueante, por isso estamos numa rota 'def')
    upload_results = sftp_service.upload_batch(files, data_type.value, metadata_base)

    response_list = []

    for result in upload_results:
        # Define status baseado no retorno do serviço
        status_enum = UploadStatus.UPLOADED if result["status"] == "uploaded" else UploadStatus.FAILED
        
        # Cria o objeto Pydantic para passar ao CRUD
        upload_in = upload_schema.UploadCreate(
            filename=result["filename"],
            data_type=data_type,
            sftp_path=result.get("sftp_path", ""),
            user_id=current_user.id,
            status=status_enum
        )

        # Salva no banco
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
    Gera CSV de logs.
    - Admin: Vê tudo.
    - User: Vê apenas os seus.
    """
    
    # Lógica de permissão corrigida usando o Enum
    is_admin = current_user.role == UserRole.ADMIN
    target_user_id = None if is_admin else current_user.id

    logs = crud_upload.get_uploads_filtered(
        db=db,
        user_id=target_user_id,
        data_type=data_type,
        start_date=start_date,
        end_date=end_date
    )

    # Criação do CSV na memória
    stream = io.StringIO()
    csv_writer = csv.writer(stream)

    # Cabeçalhos
    csv_writer.writerow(["ID", "Arquivo", "Tipo", "Status", "Caminho SFTP", "Usuário", "Data Upload (UTC)"])

    for log in logs:
        # Prevenção de erro caso usuário tenha sido deletado
        owner_name = log.owner.username if log.owner else f"User ID {log.user_id}"
        
        csv_writer.writerow([
            log.id,
            log.filename,
            log.data_type.value,
            log.status.value,
            log.sftp_path,
            owner_name,
            log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        ])

    stream.seek(0)
    
    filename = f"relatorio_uploads_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    
    # Retorna o stream como arquivo para download
    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )