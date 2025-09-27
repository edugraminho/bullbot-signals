# BullBot Signals 🤖

Sistema avançado de análise técnica para trading de criptomoedas baseado em **confluência de indicadores**. Combina RSI, EMAs, MACD e Volume para gerar sinais de alta precisão, com integração à API da [MEXC](https://mexcdevelop.github.io/apidocs/spot_v3_en/) Exchange.

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

O BullBot Signals é uma aplicação de análise técnica avançada que utiliza **confluência de indicadores** para identificar oportunidades de trading em criptomoedas com alta precisão.

### 🎯 O que é Confluência?

**Confluência** é quando múltiplos indicadores técnicos concordam e apontam na mesma direção, aumentando drasticamente a probabilidade de sucesso do sinal.

**Analogia**: Em vez de confiar apenas em uma pessoa te dizendo "pode atravessar a rua", você espera que 4-5 pessoas concordem. **Maior consenso = Maior confiança!**

### 📊 Sistema de Pontuação (0-8 pontos)

| Indicador | Peso | O que Confirma |
|-----------|------|----------------|
| **RSI** | 2 pontos | Zona de sobrecompra/sobrevenda |
| **EMA** | 3 pontos | Tendência + posição do preço |
| **MACD** | 1 ponto | Momentum bullish/bearish |
| **Volume** | 2 pontos | Volume alto + OBV trending |

**Resultado**: Sinais mais confiáveis, menos falsos positivos, melhor timing de entrada.

## ✨ Funcionalidades

### ✅ Sistema de Confluência Implementado

- **🎯 Análise Confluente**: RSI + EMA + MACD + Volume = Score 0-8 pontos
- **📊 Indicadores Técnicos Completos**:
  - **RSI**: Força relativa com níveis configuráveis (padrão: 20/80)
  - **EMAs**: Médias exponenciais 9/21/50 para análise de tendência
  - **MACD**: Convergência/divergência 12/26/9 para momentum
  - **Volume**: OBV, VWAP e análise de fluxo para confirmação
- **🎚️ Sistema de Pontuação Inteligente**: Filtragem por qualidade (4+ pontos = sinal válido)
- **⚙️ Configuração Dinâmica**: Usuários podem personalizar via Telegram
- **🔗 MEXC Exchange**: Integração com MEXC para dados de mercado spot sem taxas

### ✅ Infraestrutura Robusta

- **🌐 API REST FastAPI**: Endpoints otimizados para análise em tempo real
- **📈 Monitoramento Contínuo**: Celery tasks para análise 24/7
- **🤖 Integração Telegram**: Alimenta bullbot-telegram via banco de dados
- **🚫 Anti-Spam Avançado**: Cooldowns inteligentes e limites diários
- **🏗️ Clean Architecture**: Separação clara entre domínio, infraestrutura e API
- **🐳 Containerização**: Docker-compose para desenvolvimento e produção


### 🚧 Em Desenvolvimento

- Bandas de Bollinger como indicador adicional
- Backtesting de estratégias de confluência
- Dashboard web para visualização de scores
- Machine Learning para otimização de pesos

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
git clone https://github.com/seu-usuario/bullbot-signals.git
cd bullbot-signals
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

## 🎯 Sistema de Confluência de Indicadores

O BullBot Signals utiliza um **sistema avançado de confluência** que combina múltiplos indicadores técnicos para gerar sinais de alta precisão, reduzindo drasticamente os falsos positivos.

### 📊 Indicadores Utilizados

| Indicador | Peso Máximo | Critérios de Pontuação |
|-----------|-------------|------------------------|
| **RSI** | 2 pontos | Sempre 2 se em zona extrema (≤20 ou ≥80) |
| **EMAs** | 3 pontos | +2 se tendência favorável + 1 se preço > EMA50 |
| **MACD** | 1 ponto | +1 se cruzamento favorável ao sinal |
| **Volume** | 2 pontos | +1 se volume alto + 1 se OBV favorável |

**Score Total**: 8 pontos máximos

### ⚙️ Thresholds por Timeframe

- **15 minutos**: Score mínimo **4 pontos** para gerar sinal
- **1 hora**: Score mínimo **4 pontos** para gerar sinal  
- **4 horas**: Score mínimo **5 pontos** para gerar sinal
- **1 dia**: Score mínimo **5 pontos** para gerar sinal

### 🎚️ Configuração via JSON

O sistema é totalmente configurável através do projeto **bullbot-telegram**:

```json
{
  "indicators_config": {
    "RSI": {
      "enabled": true,
      "period": 14,
      "oversold": 20,
      "overbought": 80
    },
    "EMA": {
      "enabled": true,
      "short_period": 9,
      "medium_period": 21,
      "long_period": 50
    },
    "MACD": {
      "enabled": true,
      "fast_period": 12,
      "slow_period": 26,
      "signal_period": 9
    },
    "Volume": {
      "enabled": true,
      "sma_period": 20,
      "threshold_multiplier": 1.2
    },
    "Confluence": {
      "enabled": true,
      "min_score_15m": 4,
      "min_score_4h": 5
    }
  }
}
```

### 🎯 Exemplo de Sinal Prático

**Cenário**: BTC em timeframe de 15 minutos com confluência de 6/8 pontos

```
🎯 CONFLUÊNCIA BTC/15m - Score: 6/8 (75%) 
💰 Preço: $67,530.25 | 👍 SINAL DE COMPRA STRONG

📊 Breakdown dos Indicadores:
├─ RSI: 18.4 (sobrevenda) ✅ +2/2 pontos
│  • Zona: oversold (limite: ≤20)
│  • Status: Ideal para compra
├─ EMA: Alinhamento bullish ✅ +3/3 pontos  
│  • EMA9: $67,234 > EMA21: $66,825 > EMA50: $66,210
│  • Preço acima das 3 médias ✅ (filtro de tendência)
├─ MACD: Momentum bullish ✅ +1/1 ponto
│  • Linha MACD: 234.12 > Linha Sinal: 167.89
│  • Histograma: +66.23 (divergência positiva)
└─ Volume: Abaixo do threshold ❌ +0/2 pontos
   • Volume atual: 85% da média (precisa: ≥120%)
   • OBV: Trending up ✅ (fluxo positivo)
   • VWAP: $67,230 (preço 0.44% above)

💡 Estratégia Sugerida:
   • Entry: $67,530 (preço atual)
   • Stop Loss: $66,825 (EMA21) - Risco: 1.04%  
   • Take Profit: $69,500 (próxima resistência)
   • Risk/Reward: 1:2.8

⚠️ Aviso: Volume baixo pode indicar breakout falso
```

## 📊 API Endpoints

### Análise de Confluência
```bash
GET /api/v1/confluence/{symbol}
```

**Parâmetros:**
- `symbol`: Símbolo da criptomoeda (ex: BTC, ETH, SOL)
- `interval`: Intervalo (15m, 1h, 4h, 1d)
- `source`: Fonte dos dados (mexc)

**Exemplo:**
```bash
curl "http://localhost:8000/api/v1/confluence/BTC?interval=15m"
```

**Resposta:**
```json
{
  "signal": {
    "symbol": "BTC",
    "signal_type": "BUY",
    "strength": "STRONG",
    "rsi_value": 18.4,
    "price": 67530.25,
    "timestamp": "2025-01-31T15:30:00Z",
    "timeframe": "15m",
    "message": "Sinal de COMPRA STRONG - Score: 6/8"
  },
  "confluence_score": {
    "total_score": 6,
    "max_possible_score": 8,
    "details": {
      "RSI": {
        "score": 2,
        "value": 18.4,
        "reason": "RSI 18.4 em zona de sobrevenda",
        "levels": {
          "oversold": 20,
          "overbought": 80,
          "current_zone": "oversold"
        }
      },
      "EMA": {
        "score": 3,
        "trending_up": true,
        "reason": "EMA favorável ao sinal",
        "values": {
          "ema_9": 67234.56,
          "ema_21": 66825.78,
          "ema_50": 66210.45,
          "price_above_ema_50": true
        }
      },
      "MACD": {
        "score": 1,
        "is_bullish": true,
        "reason": "MACD confirma o sinal",
        "values": {
          "macd_line": 234.12,
          "signal_line": 167.89,
          "histogram": 66.23,
          "crossover": "bullish"
        }
      },
      "Volume": {
        "score": 0,
        "is_high_volume": false,
        "obv_trending_up": true,
        "reason": "Volume não suporta o sinal",
        "values": {
          "volume_ratio": 0.85,
          "obv": 12345678.90,
          "vwap": 67230.12,
          "price_vs_vwap": "above",
          "volume_threshold": "85%"
        }
      }
    }
  },
  "recommendation": "Sinal de COMPRA STRONG - Score: 6/8",
  "risk_level": "BAIXO",
  "current_price": 67530.25
}
```



### Health Check
```bash
GET /api/v1/health
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
bullbot-signals/
├── src/
│   ├── core/                           # 🎯 Lógica central (domínio)
│   │   ├── models/                     # Entidades de negócio
│   │   │   ├── crypto.py              # RSIData, EMAData, MACDData, VolumeData
│   │   │   └── signals.py             # TradingSignal, SignalType
│   │   └── services/                   # Serviços de negócio
│   │       ├── rsi_calculator.py      # Cálculo RSI puro
│   │       ├── ema_calculator.py      # Cálculo EMAs (9, 21, 50)
│   │       ├── macd_calculator.py     # Cálculo MACD e sinais
│   │       ├── volume_analyzer.py     # Volume, OBV, VWAP
│   │       ├── confluence_analyzer.py # Sistema de confluência
│   │       ├── rsi_service.py         # Orquestração principal
│   │       └── signal_filter.py       # Filtros anti-spam
│   ├── adapters/                       # 🔌 Integrações externas
│   │   ├── binance_client.py          # Cliente Binance
│   │   ├── gate_client.py             # Cliente Gate.io
│   │   └── mexc_client.py             # Cliente MEXC
│   ├── api/                            # 🌐 Interface HTTP
│   │   ├── schemas/                    # DTOs de serialização
│   │   ├── routes/                     # Endpoints organizados
│   │   └── main.py                    # App principal
│   ├── tasks/                          # ⚡ Processamento assíncrono
│   │   ├── celery_app.py              # Configuração Celery
│   │   └── monitor_tasks.py           # Monitoramento automático
│   ├── database/                       # 💾 Persistência
│   │   ├── models.py                  # Modelos SQLAlchemy
│   │   └── connection.py              # Conexão DB
│   └── utils/                          # 🛠️ Utilitários
│       ├── config.py                  # Configurações indicadores
│       ├── logger.py                  # Logging estruturado
│       └── trading_coins.py           # Curação de moedas
├── tests/                              # 🧪 Testes
├── docker-compose.yml                  # 🐳 Configuração Docker
├── Dockerfile                          # 🐳 Imagem Docker
└── requirements.txt                    # 📦 Dependências
```

### 🔄 Integração com bullbot-telegram

O **BullBot Signals** funciona como **engine de análise** que alimenta os grupos do Telegram:

```
[bullbot-telegram] ←→ [bullbot-signals]
     ↓                        ↓
📱 Grupos Telegram    🧮 Análise Confluência
📊 Configurações     📊 Scores 0-8 pontos  
⚙️ Filtros           🎯 Sinais precisos
👥 Usuários          📈 MEXC Exchange
```

## 📝 Rate Limits

- **MEXC**: 20 requests por segundo
- **Recomendação**: Sistema gerencia rate limiting automaticamente

## 🤖 Integração com Telegram

O **BullBot Signals** é projetado para alimentar grupos do Telegram através do projeto **bullbot-telegram**. O fluxo completo funciona assim:

### 📊 Fluxo de Sinais

1. **Análise Contínua**: Sistema monitora múltiplas criptomoedas em tempo real
2. **Confluência**: Combina RSI + EMA + MACD + Volume para score 0-8
3. **Filtros**: Aplica anti-spam e cooldowns configuráveis
4. **API**: Envia sinal via API para bullbot-telegram
5. **Telegram**: Bot publica no grupo com formatação rica

### 🎯 Exemplo de Mensagem no Telegram

```
🎯 SINAL DE COMPRA STRONG - BTC/15m

📊 Score de Confluência: 6/8 ⭐⭐⭐
├─ RSI: 18.4 (sobrevenda) ✅ +2pt
├─ EMA: Tendência de alta ✅ +3pt  
│  • EMA9: $67,234 > EMA21: $66,825 > EMA50: $66,210
│  • Preço acima de todas as médias
├─ MACD: Cruzamento bullish ✅ +1pt
│  • Linha: 234.12 > Sinal: 167.89
│  • Histograma: +66.23 (positivo)
└─ Volume: Normal ❌ +0pt
   • Ratio: 85% da média (abaixo do threshold)
   • OBV: Tendência de alta ✅

💰 Preço Atual: $67,530.25
📈 Timeframe: 15 minutos
⚡ Exchange: Binance
🎚️ Força: STRONG (6/8 = 75%)
⚠️ Risco: BAIXO

💡 Recomendação: Entry com stop em EMA21 ($66,825)

🔗 TradingView | 📊 Binance
```

### ⚙️ Configuração Dinâmica

Cada grupo pode ter configurações personalizadas via **bullbot-telegram**:

- **Indicadores**: Habilitar/desabilitar RSI, EMA, MACD, Volume
- **Thresholds**: Score mínimo por timeframe (15m: 4, 4h: 5)
- **Filtros**: Cooldown personalizado por força do sinal
- **Símbolos**: Lista customizada de criptomoedas
- **Exchange**: MEXC como fonte única de dados

### 🎛️ Controles Anti-Spam Avançados

| Timeframe | STRONG | MODERATE | WEAK |
|-----------|--------|----------|------|
| **15m** | 15min | 30min | 60min |
| **1h** | 60min | 120min | 240min |
| **4h** | 120min | 240min | 360min |
| **1d** | 360min | 720min | 1440min |

**Limites Globais**:
- **3 sinais máx/símbolo/dia** 
- **2 sinais STRONG máx/símbolo/dia**
- **Diferença RSI mínima: 2.0 pontos**
- **Score mínimo**: 4+ pontos (50%+ confluência)

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Padrões de Código

- Use **type hints** em todas as funções
- Documente com docstrings em português
- Siga o padrão **Ruff** para formatação (88 chars por linha)
- Implemente testes para calculadores de indicadores
- **Clean Architecture**: Mantenha separação clara entre camadas
- **Confluência**: Novos indicadores devem seguir padrão de score 0-N
- **Configuração**: Use `config.py` para parâmetros padrão


### 🐳 Containerização Obrigatória
- **SEMPRE execute comandos Python em containers**
- Use `docker-compose exec app` para todos os comandos Python
- Nunca execute Python diretamente no ambiente local
