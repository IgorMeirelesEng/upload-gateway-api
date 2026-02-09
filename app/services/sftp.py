import paramiko
import io
import json
import os
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
        self.base_remote_dir = settings.SFTP_REMOTE_PATH.rstrip("/")

    def _create_connection(self):
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                key_filename=self.key_path,
                timeout=20
            )
            return client
        except Exception as e:
            print(f"Erro ao conectar no SFTP: {e}")
            raise HTTPException(status_code=503, detail="Falha na conexão com servidor SFTP.")

    def _ensure_directories(self, sftp, remote_path: str):

        directory = os.path.dirname(remote_path)
        if directory == "/" or directory == ".":
            return

        dirs_to_create = []
        
        while len(directory) > 1:
            try:
                sftp.stat(directory)
                break 
            except IOError:
                dirs_to_create.append(directory)
                directory = os.path.dirname(directory)
        
        while dirs_to_create:
            dir_to_create = dirs_to_create.pop()
            try:
                sftp.mkdir(dir_to_create)
            except IOError:
                pass 

    def upload_batch(self, files: List[UploadFile], data_type: str, metadata_base: dict) -> List[dict]:
       
        ssh = self._create_connection()
        sftp = ssh.open_sftp()
        results = []

        try:
            # Estrutura de pasta: /landing/uploads/dados_relogios/2026/02/
            date_folder = datetime.now().strftime("%Y/%m")
            base_path = f"{self.base_remote_dir}/{data_type}/{date_folder}"
            
            self._ensure_directories(sftp, f"{base_path}/dummy")

            for file in files:
                try:
                    
                    safe_filename = file.filename.replace(" ", "_")
                    full_path_file = f"{base_path}/{safe_filename}"
                    full_path_meta = f"{full_path_file}.json"

                    
                    content = file.file.read() 
                    file.file.seek(0) 

                    print(f"Enviando: {safe_filename}")
                    sftp.putfo(io.BytesIO(content), full_path_file)

                    # 4. Upload Metadados Específicos deste arquivo
                    meta = metadata_base.copy()
                    meta["filename"] = safe_filename
                    meta["size_bytes"] = len(content)
                    
                    meta_json = json.dumps(meta, indent=4, default=str)
                    sftp.putfo(io.BytesIO(meta_json.encode('utf-8')), full_path_meta)

                    # 5. Adiciona à lista de sucessos
                    results.append({
                        "filename": safe_filename,
                        "sftp_path": full_path_file,
                        "status": "uploaded",
                        "error": None
                    })
                
                except Exception as e:
                    print(f"Falha no arquivo {file.filename}: {e}")
                    results.append({
                        "filename": file.filename,
                        "sftp_path": "",
                        "status": "failed",
                        "error": str(e)
                    })

            return results

        except Exception as e:
            print(f"Erro Crítico no Batch: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        
        finally:
            if sftp: sftp.close()
            if ssh: ssh.close()

sftp_service = SFTPService()