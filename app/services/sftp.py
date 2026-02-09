import paramiko
import json
import os
import stat
from datetime import datetime
from fastapi import UploadFile, HTTPException
from app.core.config import settings
from typing import List

class SFTPService:
    def __init__(self):
        self.host = settings.SFTP_HOST
        self.port = settings.SFTP_PORT
        self.username = settings.SFTP_USERNAME
        self.key_path = settings.SFTP_KEY_PATH
        # Remove barra final para evitar caminhos duplicados (//)
        self.base_remote_dir = settings.SFTP_REMOTE_PATH.rstrip("/")

    def _create_connection(self):
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Carrega a chave explicitamente para evitar erros de formato
            pkey = paramiko.RSAKey.from_private_key_file(self.key_path)
            
            client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                pkey=pkey, # Passando o objeto da chave
                look_for_keys=False,
                timeout=20
            )
            return client
        except Exception as e:
            print(f"Erro ao conectar no SFTP ({self.host}): {e}")
            raise HTTPException(status_code=503, detail=f"Falha na conexão SFTP: {str(e)}")

    def _ensure_directories(self, sftp, remote_path: str):
        """
        Cria diretórios recursivamente no servidor remoto se não existirem.
        """
        dirs = remote_path.split("/")
        current_path = ""
        
        for dir_name in dirs:
            if not dir_name: continue # Pula strings vazias causadas por //
            
            current_path += f"/{dir_name}"
            
            try:
                sftp.stat(current_path)
            except IOError:
                try:
                    sftp.mkdir(current_path)
                    print(f"Diretório criado: {current_path}")
                except Exception as e:
                    # Se falhar ao criar, pode ser que outro processo criou ao mesmo tempo
                    print(f"Aviso ao criar diretório {current_path}: {e}")

    def upload_batch(self, files: List[UploadFile], data_type: str, metadata_base: dict) -> List[dict]:
        ssh = None
        sftp = None
        results = []

        try:
            ssh = self._create_connection()
            sftp = ssh.open_sftp()
            
            # Define caminho base: /remote/path/tipo/ano/mes
            date_folder = datetime.now().strftime("%Y/%m")
            # Garante que não temos barras duplas
            target_dir = f"{self.base_remote_dir}/{data_type}/{date_folder}".replace("//", "/")
            
            # Cria a estrutura de pastas uma única vez
            self._ensure_directories(sftp, target_dir)

            for file in files:
                try:
                    # Higieniza o nome do arquivo
                    safe_filename = file.filename.replace(" ", "_").replace("/", "_")
                    full_path_file = f"{target_dir}/{safe_filename}"
                    full_path_meta = f"{full_path_file}.json"

                    print(f"Iniciando upload (stream): {safe_filename} -> {full_path_file}")
                    
                    # --- CORREÇÃO DE PERFORMANCE (STREAMING) ---
                    # Reset o ponteiro do arquivo para garantir leitura do início
                    file.file.seek(0)
                    
                    # Usa putfo diretamente com o file-like object do FastAPI/SpooledTemporaryFile
                    # Isso evita carregar o arquivo na RAM. O Paramiko lê em chunks.
                    sftp.putfo(file.file, full_path_file)
                    
                    # Pega o tamanho real após upload (ou usa file.size se disponível)
                    file_size = file.size if hasattr(file, 'size') else 0

                    # Upload de Metadados (JSON leve, pode ir para RAM)
                    meta = metadata_base.copy()
                    meta["filename"] = safe_filename
                    meta["uploaded_at"] = datetime.now().isoformat()
                    meta["size_bytes"] = file_size
                    
                    # Escreve JSON direto no pipe
                    import io
                    meta_json = json.dumps(meta, indent=4, default=str)
                    sftp.putfo(io.BytesIO(meta_json.encode('utf-8')), full_path_meta)

                    results.append({
                        "filename": safe_filename,
                        "sftp_path": full_path_file,
                        "status": "uploaded",
                        "error": None,
                        "size": file_size
                    })
                
                except Exception as e:
                    print(f"FALHA no arquivo {file.filename}: {e}")
                    results.append({
                        "filename": file.filename,
                        "sftp_path": "",
                        "status": "failed",
                        "error": str(e),
                        "size": 0
                    })
            
            return results

        except Exception as e:
            print(f"Erro Crítico no Batch: {e}")
            # Não paramos a API, mas retornamos erro para o controller tratar
            raise HTTPException(status_code=500, detail=str(e))
        
        finally:
            if sftp: sftp.close()
            if ssh: ssh.close()

# Instância Singleton
sftp_service = SFTPService()