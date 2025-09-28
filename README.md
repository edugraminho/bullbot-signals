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
- **MEXC API** - Dados de mercado spot (exchange única)
- **Pytest** - Testes

## 📋 Pré-requisitos

- Docker e Docker Compose
- Conexão com internet para acessar a API da MEXC
- PostgreSQL (via Docker Compose)

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

## 🔗 Sistema de Trading Coins

O sistema agora utiliza um **banco de dados PostgreSQL** para armazenar e gerenciar os pares de trading da MEXC, substituindo completamente o sistema anterior baseado em CSV.

### Tabela `trading_coins` (MEXCTradingPair)

```sql
CREATE TABLE trading_coins (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(30) UNIQUE NOT NULL,        -- BTCUSDT, ETHUSDT
    base_asset VARCHAR(20) NOT NULL,           -- BTC, ETH, SOL
    quote_asset VARCHAR(10) NOT NULL,          -- USDT
    current_price FLOAT,                       -- Preço atual
    volume_24h FLOAT,                          -- Volume 24h
    is_active BOOLEAN DEFAULT TRUE,            -- Par ativo
    is_spot_trading_allowed BOOLEAN DEFAULT TRUE, -- Spot trading habilitado
    raw_payload JSON,                          -- Dados completos da MEXC
    updated_at TIMESTAMP                       -- Última atualização
);
```

### Sincronização Automática

- **Frequência**: A cada 5 minutos via Celery task
- **Fonte**: API `/api/v3/ticker/24hr` + `/api/v3/exchangeInfo` da MEXC
- **Volume**: ~2.173 pares totais, ~1.705 pares USDT
- **Operação**: UPSERT (INSERT ON CONFLICT UPDATE)

## 🎮 Como Usar

### Teste Rápido da Integração

```bash
# Testar conexão com MEXC
docker-compose exec app python -c "from src.services.mexc_client import MEXCClient; print('MEXC client loaded successfully')"

# Verificar símbolos disponíveis
docker-compose exec app python -c "
from src.services.mexc_pairs_service import mexc_pairs_service
symbols = mexc_pairs_service.get_active_symbols('USDT')
print(f'Símbolos USDT ativos: {len(symbols)}')
print(f'Primeiros 10: {symbols[:10]}')
"

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
│   ├── services/                       # 🔌 Integrações e serviços
│   │   ├── mexc_client.py             # Cliente MEXC (única exchange)
│   │   └── mexc_pairs_service.py      # Gerenciamento pares MEXC
│   ├── api/                            # 🌐 Interface HTTP
│   │   ├── schemas/                    # DTOs de serialização
│   │   ├── routes/                     # Endpoints organizados
│   │   └── main.py                    # App principal
│   ├── tasks/                          # ⚡ Processamento assíncrono
│   │   ├── celery_app.py              # Configuração Celery
│   │   └── monitor_tasks.py           # Monitoramento + Sync MEXC
│   ├── database/                       # 💾 Persistência
│   │   ├── models.py                  # SQLAlchemy (MEXCTradingPair, etc.)
│   │   └── connection.py              # Conexão PostgreSQL
│   ├── utils/                          # 🛠️ Utilitários
│   │   ├── config.py                  # Configurações do sistema
│   │   └── logger.py                  # Logging estruturado
│   └── scripts/                        # 📜 Scripts SQL e utilitários
│       └── insert_test_user_monitoring_configs.sql
├── tests/                              # 🧪 Testes
├── docker-compose.yml                  # 🐳 PostgreSQL + Redis + App
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
⚡ Exchange: MEXC
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

## 🗄️ Script SQL de Teste

Para testar o sistema de monitoramento, execute o script SQL localizado em `scripts/insert_test_user_monitoring_configs.sql`:

```sql
-- Configuração para cryptos populares em timeframe 15m
INSERT INTO user_monitoring_configs (
    user_id,
    chat_id,
    chat_type,
    username,
    user_username,
    config_type,
    priority,
    config_name,
    description,
    symbols,
    timeframes,
    indicators_config,
    filter_config,
    active
) VALUES (
    123456,
    '123456',
    'private',
    'crypto_trader',
    'crypto_trader',
    'personal',
    1,
    'popular_15m',
    'Monitoramento de cryptos populares em 15 minutos',
    ARRAY['BTC', 'ETH', 'SOL', 'BNB', 'ADA', 'DOT', 'AVAX', 'LINK', 'UNI', 'ATOM'],
    ARRAY['15m'],
    '{
        "RSI": {
            "enabled": true,
            "period": 14,
            "oversold": 50,
            "overbought": 50
        },
        "EMA": {
            "enabled": true,
            "fast_period": 9,
            "medium_period": 21,
            "slow_period": 50
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
            "volume_threshold": 0.5
        }
    }'::jsonb,
    '{
        "cooldown_minutes": 5,
        "max_signals_per_day": 50,
        "min_rsi_difference": 0.1,
        "min_confluence_score": 1
    }'::jsonb,
    true
);
```

Esta configuração monitora **10 cryptos populares** (BTC, ETH, SOL, BNB, ADA, DOT, AVAX, LINK, UNI, ATOM) no timeframe de **15 minutos** com parâmetros otimizados para capturar mais sinais durante testes (RSI 50/50, volume baixo, cooldown 5min, score mínimo 1).

**Nota:** A validação de símbolos é feita diretamente contra o banco MEXC verificando se o par `base_asset/USDT` está ativo e com `is_spot_trading_allowed=true`. Símbolos como BTC e ETH podem estar indisponíveis se a MEXC desabilitou trading spot para esses pares.

## 📊 Estruturas de Dados Aprimoradas

### 🔥 SignalHistory - Dados Completos de Sinais

O modelo `SignalHistory` foi **completamente reestruturado** para capturar dados ricos de trading com análise profissional. Principais melhorias:

#### 🎯 **Correção Crítica**
- ✅ **Campo `price`**: Agora salva o **preço real da moeda** (ex: $67,530.25)
- ✅ **Campo `rsi_value`**: Valor específico do RSI em campo separado (ex: 18.4)

#### 📈 **Dados de Trading Profissionais**
```sql
-- Novos campos para análise técnica completa
rsi_value              FLOAT NOT NULL,     -- Valor do RSI no momento do sinal
entry_price            FLOAT,              -- Preço de entrada sugerido
stop_loss              FLOAT,              -- Stop loss calculado baseado em EMAs
take_profit            FLOAT,              -- Take profit baseado na força do sinal
risk_reward_ratio      FLOAT,              -- Ratio risco/retorno calculado

-- Dados de mercado reais da MEXC
volume_24h             FLOAT,              -- Volume 24h real da MEXC
quote_volume_24h       FLOAT,              -- Volume em USDT 24h
high_24h               FLOAT,              -- Máxima 24h
low_24h                FLOAT,              -- Mínima 24h
price_change_24h       FLOAT,              -- Variação % 24h real

-- Scores e qualidade melhorados
confidence_score       FLOAT,              -- % de confluência (0-100)
combined_score         FLOAT,              -- Score absoluto dos indicadores
max_possible_score     INTEGER,            -- Score máximo possível
signal_quality         VARCHAR(20),        -- EXCELLENT, GOOD, FAIR, POOR
```

#### 🗂️ **Estruturas JSON Documentadas**

##### **1. `indicator_data`** - Dados Estruturados Completos
```json
{
  "signal_info": {
    "type": "BUY",
    "strength": "STRONG",
    "message": "Sinal de compra forte detectado",
    "recommendation": "COMPRA FORTE",
    "risk_level": "MEDIUM",
    "timestamp": "2024-01-15T10:30:00Z"
  },
  "market_data": {
    "current_price": 43250.75,
    "volume_24h": 1234567.89,
    "price_change_24h_pct": 2.45,
    "high_24h": 44000.0,
    "low_24h": 42500.0,
    "spread_pct": 0.02,
    "source": "mexc"
  },
  "confluence_analysis": {
    "total_score": 6,
    "max_possible_score": 8,
    "score_percentage": 75.0,
    "signal_strength": "STRONG",
    "is_valid_signal": true,
    "breakdown_by_indicator": {
      "RSI": {"score": 2, "value": 25.5, "reason": "RSI em zona de sobrevenda"},
      "EMA": {"score": 2, "trending_up": true, "reason": "Preço acima das EMAs"},
      "MACD": {"score": 1, "is_bullish": true, "reason": "Crossover bullish"},
      "Volume": {"score": 1, "is_high_volume": true, "reason": "Volume acima da média"}
    }
  },
  "technical_indicators": {
    "rsi": {
      "value": 25.5,
      "score": 2,
      "zone": "oversold",
      "interpretation": "RSI em zona de sobrevenda forte",
      "is_contributing": true
    },
    "ema": {
      "score": 2,
      "trending_up": true,
      "values": {"ema_9": 43100.0, "ema_21": 42900.0, "ema_50": 42700.0},
      "price_position": {"above_ema_50": true, "trend_alignment": "bullish"},
      "is_contributing": true
    },
    "macd": {
      "score": 1,
      "is_bullish": true,
      "values": {"macd_line": 150.5, "signal_line": 120.3, "histogram": 30.2},
      "crossover_type": "bullish_crossover",
      "momentum_strength": "moderate",
      "is_contributing": true
    },
    "volume": {
      "score": 1,
      "is_high_volume": true,
      "obv_trending_up": true,
      "values": {"volume_ratio": 1.45, "obv": 123456.78, "vwap": 43150.0},
      "volume_quality": "good",
      "is_contributing": true
    }
  },
  "trading_recommendations": {
    "entry_price": 43250.75,
    "stop_loss": 41800.0,
    "take_profit": 45500.0,
    "risk_reward_ratio": 2.1,
    "position_size_pct": 2.5,
    "signal_quality": "GOOD",
    "timeframe": "15m",
    "strategy_notes": "Sinal de COMPRA STRONG no timeframe 15m. Confirmado por: RSI, EMA, MACD, Volume. Adequado para scalping."
  }
}
```

##### **2. `indicator_config`** - Configurações dos Indicadores
```json
{
  "rsi_window": 14,
  "timeframe": "15m",
  "exchange": "mexc",
  "confluence_enabled": true,
  "custom_rsi_levels": {
    "oversold": 30,
    "overbought": 70
  },
  "ema_periods": {
    "short": 9,
    "medium": 21,
    "long": 50
  },
  "macd_config": {
    "fast_period": 12,
    "slow_period": 26,
    "signal_period": 9
  },
  "volume_config": {
    "sma_period": 20,
    "threshold_multiplier": 1.2
  },
  "confluence_thresholds": {
    "15m": {"min_score": 4, "min_indicators": 2},
    "1h": {"min_score": 4, "min_indicators": 2},
    "4h": {"min_score": 5, "min_indicators": 3}
  }
}
```

##### **3. `market_context`** - Contexto de Mercado
```json
{
  "volatility_pct": 3.25,
  "trend_sentiment": "bullish",
  "price_momentum_pct": 1.85,
  "range_ratio": 1.15,
  "volume_ratio": 1.45,
  "is_high_volatility": false,
  "is_expanding_range": true,
  "avg_volume_10_periods": 987654.32,
  "market_phase": "trending",
  "support_resistance": {
    "nearest_support": 42500.0,
    "nearest_resistance": 44000.0,
    "support_strength": "strong",
    "resistance_strength": "moderate"
  },
  "momentum_indicators": {
    "price_velocity": 0.85,
    "acceleration": 0.15,
    "momentum_direction": "positive"
  },
  "volume_analysis": {
    "volume_trend": "increasing",
    "volume_profile": "bullish",
    "institutional_activity": "moderate"
  },
  "market_structure": {
    "trend_strength": "moderate",
    "consolidation_risk": "low",
    "breakout_potential": "high"
  }
}
```

### 🚀 **Benefícios das Melhorias**

#### 📊 **Para Análise Técnica:**
- **Dados Precisos**: Preço real separado do valor RSI
- **Contexto Rico**: Volatilidade, momentum, suporte/resistência
- **Trading Profissional**: Stop loss, take profit, risk/reward calculados
- **Qualidade Medida**: Score de qualidade EXCELLENT/GOOD/FAIR/POOR

#### 🤖 **Para Integração:**
- **JSON Estruturado**: Fácil parsing para bots e dashboards
- **Versionamento**: `data_structure_version` para compatibilidade
- **Metadados**: Timestamp, componentes incluídos, fonte dos dados
- **Flexibilidade**: Estrutura expansível para novos indicadores

#### 📈 **Para Performance:**
- **Índices Otimizados**: Campos principais indexados para queries rápidas
- **Dados Desnormalizados**: Redução de JOINs com dados estruturados em JSON
- **Configuração Persistente**: Histórico das configurações usadas em cada sinal

### 🛠️ **Novos Serviços Implementados**

- **`SignalDataBuilder`**: Constrói estrutura JSON rica e organizada
- **`TradingRecommendations`**: Calcula stop loss, take profit, position size
- **`MEXCClient.get_market_data_24h()`**: Dados de mercado reais da MEXC
- **`MEXCClient.get_market_context()`**: Análise de contexto e volatilidade

Com essas melhorias, o sistema agora captura **dados completos de trading profissional**, facilitando análises avançadas e integração com sistemas de automação! 🎯
