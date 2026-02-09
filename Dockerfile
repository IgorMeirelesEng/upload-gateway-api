FROM python:3.11-slim

# Evita arquivos .pyc e logs presos no buffer
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Instala dependências do SO (necessárias para psycopg2 e criptografia)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    openssh-client \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copia e instala requirements primeiro (para cache do Docker ser rápido)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY . .

# Expõe a porta (informativo)
EXPOSE 8000

# Comando de inicialização
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]