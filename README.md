# Crypto Hunter 🤖

Bot automatizado para trading de criptomoedas baseado no indicador RSI (Relative Strength Index), com integração à [Polygon.io](https://polygon.io/docs/rest/indices/technical-indicators/relative-strength-index) para RSI pronto e suporte futuro a múltiplas exchanges.

## 📋 Índice

- [Sobre o Projeto](#sobre-o-projeto)
- [Funcionalidades](#funcionalidades)
- [Tecnologias](#tecnologias)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Como Usar](#como-usar)
- [API Endpoints](#api-endpoints)
- [Arquitetura](#arquitetura)
- [Contribuição](#contribuição)
- [Licença](#licença)

## 🎯 Sobre o Projeto

O Crypto Hunter é uma aplicação de análise técnica automatizada que utiliza o indicador RSI (Relative Strength Index) para identificar oportunidades de trading em criptomoedas. O projeto integra com a API da Polygon.io para obter dados de RSI em tempo real e gerar sinais de compra/venda.

## ✨ Funcionalidades

### ✅ Implementadas

- **🔗 Integração Polygon.io**: Cliente para API de RSI pronto (5 req/min gratuito)
- **📊 Análise RSI**: Serviço para análise de RSI e geração de sinais
- **🌐 API REST**: Endpoints FastAPI para consulta de RSI e sinais
- **📈 Monitoramento Múltiplo**: Suporte a múltiplas criptomoedas simultaneamente
- **🎯 Detecção de Sinais**: Análise automática de sobrecompra/sobrevenda
- **🏗️ Arquitetura Escalável**: Estrutura preparada para múltiplas exchanges

### 🚧 Em Desenvolvimento

- Integração com múltiplas exchanges
- Backtesting de estratégias
- Dashboard web para visualização
- Alertas em tempo real

## 🛠️ Tecnologias

- **Python 3.11+**
- **FastAPI** - Framework web
- **Pydantic** - Validação de dados
- **Docker** - Containerização
- **Polygon.io API** - Dados de mercado
- **Pytest** - Testes

## 📋 Pré-requisitos

- Docker e Docker Compose
- Conta na [Polygon.io](https://polygon.io/) (gratuita)
- API Key da Polygon.io

## 🚀 Instalação

1. **Clone o repositório**
```bash
git clone https://github.com/seu-usuario/crypto-hunter.git
cd crypto-hunter
```

2. **Configure as variáveis de ambiente**
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

3. **Execute com Docker**
```bash
docker-compose up -d
```

## ⚙️ Configuração

### 1. Obter API Key da Polygon.io

1. Crie uma conta gratuita em [Polygon.io](https://polygon.io/)
2. Acesse o [Dashboard](https://polygon.io/dashboard)
3. Copie sua API Key

### 2. Configurar Variáveis de Ambiente

```bash
# .env
POLYGON_API_KEY=sua_chave_aqui
LOG_LEVEL=INFO
```

## 🎮 Como Usar

### Teste Rápido da Integração

```bash
# Testar conexão com Polygon.io
docker-compose exec app python test_polygon_integration.py
```

### Executar a Aplicação

```bash
# Iniciar serviços
docker-compose up -d

# Verificar logs
docker-compose logs -f app

# Parar serviços
docker-compose down
```

## 📊 API Endpoints

### RSI Individual
```bash
GET /api/v1/rsi/single/{symbol}
```

**Exemplo:**
```bash
curl http://localhost:8000/api/v1/rsi/single/BTCUSD
```

### RSI Múltiplo
```bash
GET /api/v1/rsi/multiple?symbols={symbol1},{symbol2}
```

**Exemplo:**
```bash
curl "http://localhost:8000/api/v1/rsi/multiple?symbols=BTCUSD,ETHUSD,SOLUSD"
```

### Sinais de Trading
```bash
GET /api/v1/rsi/signals?symbols={symbol1},{symbol2}
```

**Exemplo:**
```bash
curl "http://localhost:8000/api/v1/rsi/signals?symbols=BTCUSD,ETHUSD"
```

### Health Check
```bash
GET /api/v1/rsi/health
```

## 🏗️ Arquitetura

```
crypto-hunter/
├── src/
│   ├── core/                       # 🎯 Lógica central (domínio)
│   │   ├── models/                 # Entidades de negócio
│   │   │   ├── crypto.py          # RSIData, PolygonRSIResponse
│   │   │   └── signals.py         # TradingSignal, SignalType
│   │   └── services/               # Serviços de negócio
│   │       └── rsi_service.py     # Análise RSI e sinais
│   ├── adapters/                   # 🔌 Integrações externas
│   │   └── polygon_client.py      # Cliente Polygon.io
│   ├── api/                        # 🌐 Interface HTTP
│   │   ├── schemas/                # DTOs de serialização
│   │   │   ├── common.py          # Schemas genéricos
│   │   │   └── rsi.py             # DTOs específicos RSI
│   │   ├── routes.py              # Endpoints RSI
│   │   └── main.py                # App principal
│   └── utils/                      # 🛠️ Utilitários
│       ├── config.py              # Configurações
│       └── logger.py              # Logging
├── tests/                          # 🧪 Testes
├── docker-compose.yml              # 🐳 Configuração Docker
├── Dockerfile                      # 🐳 Imagem Docker
└── requirements.txt                # 📦 Dependências
```

## 📝 Rate Limits

- **Polygon.io Gratuito**: 5 requests/min
- **Recomendação**: Para uso intensivo, considere plano pago ou implementação própria do cálculo RSI

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Padrões de Código

- Use **type hints** em todas as funções
- Documente com docstrings em português
- Siga o padrão **Black** para formatação
- Escreva testes para novas funcionalidades


### 🐳 Containerização Obrigatória
- **SEMPRE execute comandos Python em containers**
- Use `docker-compose exec app` para todos os comandos Python
- Nunca execute Python diretamente no ambiente local

### 📝 Exemplos de Comandos Corretos
```bash
# ✅ Correto
docker-compose exec app python -c "from src.api.main import app; print('App loaded')"
docker-compose exec app pytest
docker-compose exec app ruff check .

# ❌ ERRADO
python -c "from src.api.main import app; print('App loaded')"
pytest
ruff check .
```