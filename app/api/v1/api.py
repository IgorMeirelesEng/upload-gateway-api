from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, upload

api_router = APIRouter()

# 1. Rota de Login (Gera o Token)
# URL final: /api/v1/login/access-token
api_router.include_router(auth.router, tags=["login"])

# 2. Rotas de Usuários (Criar, Listar, Ver Perfil)
# URL final: /api/v1/users/
api_router.include_router(users.router, prefix="/users", tags=["users"])

# 3. Rotas de Upload (Enviar Arquivo, Exportar CSV)
# URL final: /api/v1/upload/
api_router.include_router(upload.router, prefix="/upload", tags=["upload"])