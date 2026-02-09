from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, SessionLocal, Base
from app.api.v1.api import api_router
from app.crud import user as crud_user
from app.schemas.user import UserCreate
from app.models.user import UserRole

# ==========================================
# 1. Função para criar o Admin Inicial
# ==========================================
def init_db():
    
    db = SessionLocal()
    try:
        user = crud_user.get_user_by_username(db, username=settings.FIRST_SUPERUSER)
        
        if not user:
            print(f"Usuário Admin não encontrado. Criando: {settings.FIRST_SUPERUSER}")
            
            user_in = UserCreate(
                username=settings.FIRST_SUPERUSER,
                password=settings.FIRST_SUPERUSER_PASSWORD,
                role=UserRole.ADMIN,
                is_active=True
            )
            crud_user.create_user(db, user_in)
            print("Usuário Admin criado com sucesso!")
        else:
            print("Usuário Admin já existe.")
            
    except Exception as e:
        print(f"Erro ao inicializar DB: {e}")
    finally:
        db.close()

# ==========================================
# 2. Ciclo de Vida (Lifespan)
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):

    print("Criando tabelas no Banco de Dados...")
    Base.metadata.create_all(bind=engine) 
    
    print("Verificando usuário Admin...")
    init_db() 
    
    yield 
    
    print("Servidor desligando...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan # Conecta o ciclo de vida
)

# Permite que o Frontend (React/Vue/Angular) acesse essa API
# Se estiver em produção, altere allow_origins=["*"] para o domínio real
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {"message": "API de Uploads SFTP está rodando! 🚀", "docs": "/docs"}