#!/bin/bash
# Script simples para executar testes via Docker

set -e

echo "Executando testes via Docker..."

# Verifica se o docker-compose.yml existe
if [ ! -f "docker-compose.yml" ]; then
    echo "docker-compose.yml não encontrado"
    exit 1
fi

# Executa testes
docker compose run --rm app python scripts/run_tests.py

echo "Testes concluídos!" 