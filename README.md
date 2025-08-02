# Crypto Hunter 🤖

Bot automatizado para trading de criptomoedas baseado no indicador RSI (Relative Strength Index), com integração às APIs da [Gate.io](https://www.gate.io/docs/apiv4/), [Binance](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints#klinecandlestick-data) e [MEXC](https://mexcdevelop.github.io/apidocs/spot_v3_en/) para dados OHLCV e cálculo próprio de RSI.

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

O Crypto Hunter é uma aplicação de análise técnica automatizada que utiliza o indicador RSI (Relative Strength Index) para identificar oportunidades de trading em criptomoedas. O projeto integra com as APIs da Gate.io, Binance e MEXC para obter dados de RSI em tempo real e gerar sinais de compra/venda.

## ✨ Funcionalidades

### ✅ Implementadas

- **🔗 Integração Gate.io**: Cliente para dados OHLCV e cálculo próprio de RSI
- **🔗 Integração Binance**: Cliente para dados OHLCV da maior exchange do mundo
- **🔗 Integração MEXC**: Cliente para dados OHLCV de contratos futuros
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
- **Gate.io API** - Dados de mercado spot
- **Binance API** - Dados de mercado spot
- **MEXC API** - Dados de mercado spot
- **Pytest** - Testes

## 📋 Pré-requisitos

- Docker e Docker Compose
- Conexão com internet para acessar a API da Gate.io

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

### 1. Configurar Variáveis de Ambiente

```bash
# .env
LOG_LEVEL=INFO
```

## 🔗 Integração Gate.io

O projeto inclui integração com a API da [Gate.io](https://www.gate.io/docs/apiv4/) para obtenção de dados OHLCV e cálculo próprio do RSI.

### Estrutura da Resposta da API Gate.io

A API `/spot/candlesticks` retorna dados em formato de array com **8 elementos** por item:

| Índice | Campo | Descrição |
|--------|-------|-----------|
| 0 | **Unix timestamp** | Timestamp em segundos com precisão de segundo |
| 1 | **Trading volume in quote currency** | Volume em moeda de cotação (ex: USDT) |
| 2 | **Closing price** | Preço de fechamento |
| 3 | **Highest price** | Preço mais alto |
| 4 | **Lowest price** | Preço mais baixo |
| 5 | **Opening price** | Preço de abertura |
| 6 | **Trading volume in base currency** | Volume em moeda base (ex: BTC) |
| 7 | **Whether window is closed** | Se a janela está fechada (true/false) |

### Exemplo de Resposta

```json
[
  ["1753939800", "529716.35440640", "118358.8", "118423.4", "118358.8", "118379.9", "4.47380600", "true"],
  ["1753940700", "345738.77105720", "118357.6", "118384.3", "118341.9", "118358.8", "2.92103900", "true"]
]
```

### Intervals Suportados

- `1s`, `10s`, `1m`, `5m`, `15m`, `30m`
- `1h`, `4h`, `8h`, `1d`, `7d`, `30d`

### Limites da API

- **Máximo**: 1000 pontos por consulta
- **Rate Limit**: Não especificado na documentação pública
- **Autenticação**: Não requerida para dados públicos

## 🔗 Integração Binance

O projeto também inclui integração com a API da [Binance](https://binance-docs.github.io/apidocs/spot/en/#kline-candlestick-data), a maior exchange de criptomoedas do mundo.

### Vantagens da Binance

- **📊 Maior liquidez**: Dados mais precisos e confiáveis
- **⚡ Rate limit alto**: 1200 requests/min (vs 50/min do CoinGecko)
- **🌍 Padrão da indústria**: Usada por muitas ferramentas incluindo TradingView
- **📈 Timeframes completos**: 15 opções de intervalos
- **🔒 Estabilidade**: API muito estável e bem mantida

### Intervals Suportados

- `1m`, `3m`, `5m`, `15m`, `30m`
- `1h`, `2h`, `4h`, `6h`, `8h`, `12h`
- `1d`, `3d`, `1w`, `1M`

### Limites da API

- **Máximo**: 1000 pontos por consulta
- **Rate Limit**: 1200 requests/min
- **Autenticação**: Não requerida para dados públicos

## 🎮 Como Usar

### Teste Rápido da Integração

```bash
# Testar conexão com Gate.io
docker-compose exec app python -c "from src.adapters.gate_client import GateClient; print('Gate.io client loaded successfully')"
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

**Parâmetros:**
- `symbol`: Símbolo da criptomoeda (ex: BTC, ETH, SOL)
- `interval`: Intervalo (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
- `window`: Janela do RSI (padrão: 14)
- `source`: Fonte dos dados (binance, gate ou mexc, padrão: binance)

**Exemplo:**
```bash
curl "http://localhost:8000/api/v1/rsi/single/BTC?interval=15m&window=14&source=binance"
```

**Resposta:**
```json
{
  "symbol": "BTC",
  "rsi_value": 43.48,
  "current_price": 67530.25,
  "timestamp": "2025-01-31T11:30:00",
  "timespan": "15m",
  "window": 14,
  "source": "binance_calculated",
  "data_source": "binance"
}
```

### RSI Múltiplo
```bash
GET /api/v1/rsi/multiple?symbols={symbol1},{symbol2}
```

**Exemplo:**
```bash
curl "http://localhost:8000/api/v1/rsi/multiple?symbols=BTCUSD,ETHUSD,SOLUSD"
```


### Health Check
```bash
GET /api/v1/rsi/health
```

## 🔗 Integração MEXC

O projeto inclui integração com a API da [MEXC](https://mexcdevelop.github.io/apidocs/spot_v3_en/) para obtenção de dados OHLCV de mercado spot e cálculo próprio do RSI.

### Estrutura da Resposta da API MEXC

A API `/api/v3/klines` retorna dados em formato de array com **12 elementos** por item (igual Binance):

| Índice | Campo | Descrição |
|--------|-------|-----------|
| 0 | **openTime** | Timestamp de abertura em milissegundos |
| 1 | **open** | Preço de abertura |
| 2 | **high** | Preço mais alto |
| 3 | **low** | Preço mais baixo |
| 4 | **close** | Preço de fechamento |
| 5 | **volume** | Volume negociado |
| 6 | **closeTime** | Timestamp de fechamento em milissegundos |
| 7 | **quoteAssetVolume** | Volume em moeda de cotação |
| 8 | **numberOfTrades** | Número de trades |
| 9 | **takerBuyBaseAssetVolume** | Volume comprado |
| 10 | **takerBuyQuoteAssetVolume** | Volume comprado em cotação |
| 11 | **ignore** | Campo ignorado |

### Vantagens da MEXC

- **📊 Mercado Spot**: Dados de mercado spot (mais estáveis que futuros)
- **⚡ Baixa Latência**: API otimizada para alta frequência
- **🌍 Cobertura Global**: Suporte a múltiplos mercados
- **📈 Dados Históricos**: Histórico completo de dados OHLCV
- **🔒 Confiabilidade**: API estável e bem documentada

### Intervalos Suportados

- **1m, 5m, 15m, 30m** - Análise de curto prazo
- **1h, 4h** - Análise de médio prazo  
- **1d, 1w, 1M** - Análise de longo prazo

### Limites da API

- **Rate Limit**: 20 requests por segundo
- **Dados Históricos**: Até 1000 candles por requisição
- **Símbolos**: Todos os pares spot disponíveis

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
│   │   └── gate_client.py         # Cliente Gate.io
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

- **Gate.io**: Não especificado na documentação pública
- **Recomendação**: Use com moderação e implemente rate limiting se necessário

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


# Trading Coins - Sistema de Curação de Moedas

## Visão Geral

O sistema **Trading Coins** é responsável por curar e manter uma lista atualizada das melhores moedas para trading, baseado em critérios específicos como market cap, volume de negociação e disponibilidade nas exchanges suportadas.

## Funcionalidades

- **Busca automática** de dados da CoinGecko API
- **Filtragem inteligente** baseada em critérios de trading
- **Atualização automática** via Celery a cada 7 dias
- **Suporte a múltiplas exchanges** (Binance, MEXC, Gate)
- **Armazenamento em CSV e JSON** para fácil acesso

## Critérios de Filtragem

### Market Cap
- Mínimo: $50M (configurável)
- Foco em moedas com liquidez adequada

### Volume de Negociação
- Mínimo: $3M em 24h (configurável)
- Suporte a períodos: 24h, 7d, 30d

### Exclusões Automáticas
- **Stablecoins**: USDT, USDC, BUSD, etc.
- **Meme tokens**: Tokens baseados em memes
- **Wrapped tokens**: Tokens embrulhados
- **Governance tokens**: Tokens de governança