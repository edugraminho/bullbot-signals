# Crypto Hunter - Bot de Trading com RSI

Bot automatizado para trading de criptomoedas baseado no indicador RSI (Relative Strength Index), com suporte a múltiplas exchanges e sistema de notificações.

## 🚀 Características

- **Múltiplas Exchanges**: Suporte a Binance, Bybit, Gate.io e outras
- **Indicadores Técnicos**: Cálculo automático de RSI e outros indicadores
- **Sistema de Sinais**: Geração inteligente de sinais de compra/venda
- **Notificações**: Integração com Discord, Telegram e outros
- **Trading Automático**: Execução automática de trades baseada em sinais
- **Monitoramento**: Dashboards em tempo real com Grafana
- **Escalabilidade**: Arquitetura modular e escalável

## 🏗️ Arquitetura

```
crypto-hunter/
├── core/                    # Lógica de negócio
│   ├── exchanges/          # Adaptadores de exchanges
│   ├── indicators/         # Cálculo de indicadores
│   ├── signals/           # Geração de sinais
│   └── trading/           # Execução de trades
├── data/                   # Camada de dados
├── services/              # Serviços externos
├── config/                # Configurações
└── monitoring/            # Monitoramento
```

## 🛠️ Tecnologias

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy
- **Banco de Dados**: PostgreSQL, Redis
- **Processamento**: Celery, Redis
- **Monitoramento**: Prometheus, Grafana
- **Qualidade**: Ruff, Black, MyPy
- **Containerização**: Docker, Docker Compose

## 📋 Pré-requisitos

- Docker e Docker Compose
- Python 3.11+
- Git

## 🚀 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/crypto-hunter.git
cd crypto-hunter
```

### 2. Configure as variáveis de ambiente

```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

### 3. Execute com Docker Compose

```bash
# Construir e iniciar todos os serviços
docker compose up -d

# Verificar status dos serviços
docker compose ps

# Ver logs
docker compose logs -f app
```

### 4. Acesse os serviços

- **Aplicação**: http://localhost:8000
- **Flower**: http://localhost:5555

## 🔧 Configuração

### Exchanges

Configure suas APIs de exchanges no arquivo `config/exchanges.yml`:

```yaml
binance:
  api_key: "sua_api_key"
  api_secret: "seu_api_secret"
  testnet: false

bybit:
  api_key: "sua_api_key"
  api_secret: "seu_api_secret"
  testnet: false
```

### Símbolos e Parâmetros

Configure os símbolos e parâmetros RSI no arquivo `config/symbols.yml`:

```yaml
BTCUSDT:
  rsi_period: 14
  overbought_level: 70
  oversold_level: 30
  position_size: 0.1
  max_loss_per_trade: 0.02
```

## 📊 Monitoramento

### Flower (Celery Monitoring)

Acesse http://localhost:5555 para monitorar:
- Tarefas em execução
- Workers ativos
- Filas de processamento
- Performance das tarefas

## 🧪 Desenvolvimento

### Ambiente Local

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar testes
pytest

# Verificar qualidade do código
ruff check .
ruff format .

# Verificar tipos
mypy .
```

### Estrutura de Testes

```bash
# Testes unitários
pytest tests/unit/

# Testes de integração
pytest tests/integration/

# Cobertura de código
pytest --cov=core --cov=data --cov=services
```

## 📈 Uso

### 1. Configurar Exchanges

1. Crie contas nas exchanges desejadas
2. Gere API keys com permissões de leitura e trading
3. Configure as credenciais no arquivo de configuração

### 2. Configurar Símbolos

1. Escolha os pares de trading
2. Configure os parâmetros RSI
3. Defina limites de risco

### 3. Iniciar Trading

1. Verifique as configurações
2. Inicie o sistema: `docker compose up -d`
3. Monitore através dos dashboards

### 4. Monitorar Performance

1. Acesse o Flower (http://localhost:5555)
2. Verifique as tarefas em execução
3. Monitore os logs da aplicação
4. Ajuste parâmetros conforme necessário

## 🔒 Segurança

- **API Keys**: Nunca commite credenciais no repositório
- **Ambiente**: Use variáveis de ambiente para configurações sensíveis
- **Testnet**: Sempre teste primeiro em ambiente de testes
- **Backup**: Faça backup regular dos dados

## 📝 Logs

Os logs são salvos em:
- **Aplicação**: `logs/app.log`
- **Celery**: `logs/celery.log`
- **Docker**: `docker compose logs [service]`

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## ⚠️ Disclaimer

Este software é fornecido "como está" sem garantias. Trading de criptomoedas envolve riscos significativos. Use por sua conta e risco.

## 📞 Suporte

- **Issues**: [GitHub Issues](https://github.com/seu-usuario/crypto-hunter/issues)
- **Documentação**: [Wiki](https://github.com/seu-usuario/crypto-hunter/wiki)
- **Email**: support@cryptohunter.com

---

**Crypto Hunter** - Trading automatizado inteligente 🚀 