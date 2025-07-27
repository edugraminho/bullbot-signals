.PHONY: help install test lint format clean docker-build docker-up docker-down docker-logs

# Variáveis
PYTHON = python3
PIP = pip3
DOCKER_COMPOSE = docker compose

# Cores para output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
NC = \033[0m # No Color

help: ## Mostra esta ajuda
	@echo "$(BLUE)Crypto Hunter - Comandos disponíveis:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# =============================================================================
# DESENVOLVIMENTO LOCAL
# =============================================================================

install: ## Instala dependências Python
	@echo "$(YELLOW)Instalando dependências...$(NC)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)Dependências instaladas!$(NC)"

install-dev: ## Instala dependências de desenvolvimento
	@echo "$(YELLOW)Instalando dependências de desenvolvimento...$(NC)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)Dependências de desenvolvimento instaladas!$(NC)"

test: ## Executa testes
	@echo "$(YELLOW)Executando testes...$(NC)"
	pytest tests/ -v --cov=core --cov=data --cov=services --cov-report=html
	@echo "$(GREEN)Testes concluídos!$(NC)"

test-unit: ## Executa apenas testes unitários
	@echo "$(YELLOW)Executando testes unitários...$(NC)"
	pytest tests/unit/ -v
	@echo "$(GREEN)Testes unitários concluídos!$(NC)"

test-integration: ## Executa apenas testes de integração
	@echo "$(YELLOW)Executando testes de integração...$(NC)"
	pytest tests/integration/ -v
	@echo "$(GREEN)Testes de integração concluídos!$(NC)"

lint: ## Verifica qualidade do código com Ruff
	@echo "$(YELLOW)Verificando qualidade do código...$(NC)"
	ruff check .
	@echo "$(GREEN)Verificação concluída!$(NC)"

format: ## Formata código com Ruff
	@echo "$(YELLOW)Formatando código...$(NC)"
	ruff format .
	@echo "$(GREEN)Código formatado!$(NC)"

type-check: ## Verifica tipos com MyPy
	@echo "$(YELLOW)Verificando tipos...$(NC)"
	mypy core/ data/ services/
	@echo "$(GREEN)Verificação de tipos concluída!$(NC)"

quality: lint format type-check ## Executa todas as verificações de qualidade
	@echo "$(GREEN)Todas as verificações de qualidade concluídas!$(NC)"

# =============================================================================
# DOCKER
# =============================================================================

docker-build: ## Constrói imagens Docker
	@echo "$(YELLOW)Construindo imagens Docker...$(NC)"
	$(DOCKER_COMPOSE) build
	@echo "$(GREEN)Imagens construídas!$(NC)"

docker-up: ## Inicia todos os serviços Docker
	@echo "$(YELLOW)Iniciando serviços Docker...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)Serviços iniciados!$(NC)"
	@echo "$(BLUE)Acesse:$(NC)"
	@echo "  - App: http://localhost:8000"
	@echo "  - Flower: http://localhost:5555"

docker-down: ## Para todos os serviços Docker
	@echo "$(YELLOW)Parando serviços Docker...$(NC)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)Serviços parados!$(NC)"

docker-logs: ## Mostra logs dos serviços Docker
	@echo "$(YELLOW)Mostrando logs...$(NC)"
	$(DOCKER_COMPOSE) logs -f

docker-logs-app: ## Mostra logs da aplicação
	@echo "$(YELLOW)Mostrando logs da aplicação...$(NC)"
	$(DOCKER_COMPOSE) logs -f app

docker-restart: ## Reinicia todos os serviços Docker
	@echo "$(YELLOW)Reiniciando serviços Docker...$(NC)"
	$(DOCKER_COMPOSE) restart
	@echo "$(GREEN)Serviços reiniciados!$(NC)"

# =============================================================================
# BANCO DE DADOS
# =============================================================================

db-migrate: ## Executa migrações do banco de dados
	@echo "$(YELLOW)Executando migrações...$(NC)"
	alembic upgrade head
	@echo "$(GREEN)Migrações executadas!$(NC)"

db-reset: ## Reseta o banco de dados (CUIDADO!)
	@echo "$(RED)ATENÇÃO: Isso irá apagar todos os dados!$(NC)"
	@read -p "Tem certeza? (y/N): " confirm && [ "$$confirm" = "y" ]
	$(DOCKER_COMPOSE) down -v
	$(DOCKER_COMPOSE) up -d postgres redis
	@echo "$(GREEN)Banco de dados resetado!$(NC)"

# =============================================================================
# LIMPEZA
# =============================================================================

clean: ## Remove arquivos temporários e cache
	@echo "$(YELLOW)Limpando arquivos temporários...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage
	@echo "$(GREEN)Limpeza concluída!$(NC)"

clean-docker: ## Remove containers e volumes Docker
	@echo "$(YELLOW)Removendo containers e volumes Docker...$(NC)"
	$(DOCKER_COMPOSE) down -v --remove-orphans
	docker system prune -f
	@echo "$(GREEN)Limpeza Docker concluída!$(NC)"

# =============================================================================
# DESENVOLVIMENTO
# =============================================================================

dev-setup: install-dev docker-build ## Configura ambiente de desenvolvimento completo
	@echo "$(GREEN)Ambiente de desenvolvimento configurado!$(NC)"

dev-start: docker-up ## Inicia ambiente de desenvolvimento
	@echo "$(GREEN)Ambiente de desenvolvimento iniciado!$(NC)"

dev-stop: docker-down ## Para ambiente de desenvolvimento
	@echo "$(GREEN)Ambiente de desenvolvimento parado!$(NC)"

# =============================================================================
# PRODUÇÃO
# =============================================================================

prod-build: ## Constrói imagens para produção
	@echo "$(YELLOW)Construindo imagens para produção...$(NC)"
	docker build -t crypto-hunter:prod .
	@echo "$(GREEN)Imagens de produção construídas!$(NC)"

prod-deploy: ## Deploy em produção (exemplo)
	@echo "$(YELLOW)Fazendo deploy em produção...$(NC)"
	@echo "$(RED)Implemente sua lógica de deploy aqui$(NC)"
	@echo "$(GREEN)Deploy concluído!$(NC)" 