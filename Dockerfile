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
# ENV PYTHONPATH=/app
# ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# PRODUÇÃO: Usar gunicorn com múltiplos workers
# CMD ["gunicorn", "src.api.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]

# DESENVOLVIMENTO - Fast reload: "--reload"
CMD ["uvicorn", "src.api.main:app", "--host=0.0.0.0", "--port=8000"] 