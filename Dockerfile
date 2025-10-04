FROM python:3.10-slim

WORKDIR /app

# Instalar apenas dependências essenciais
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Variáveis de ambiente
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Este Dockerfile é usado apenas para build dos containers Celery
# Não há API/servidor web - apenas workers Celery 