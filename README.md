# Crypto Hunter 🤖

Bot automatizado para trading de criptomoedas baseado no indicador RSI (Relative Strength Index), com integração à [Polygon.io](https://polygon.io/docs/rest/indices/technical-indicators/relative-strength-index) para RSI pronto e suporte futuro a múltiplas exchanges.

## 🚀 Funcionalidades Implementadas

### ✅ Etapa 1: Integração Polygon.io (RSI Pronto)

- **✅ Polygon.io Client**: Integração com API para RSI pronto (5 req/min gratuito)
- **✅ RSI Service**: Serviço para análise de RSI e geração de sinais
- **✅ FastAPI Endpoints**: API REST para consulta de RSI e sinais
- **✅ Monitoramento Múltiplo**: Suporte a múltiplas criptomoedas simultaneamente
- **✅ Análise de Sinais**: Detecção automática de sobrecompra/sobrevenda
- **✅ Arquitetura Escalável**: Estrutura preparada para múltiplas exchanges

## 🏗️ Arquitetura Light

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
│   │   ├── v1/rsi.py              # Endpoints RSI
│   │   └── main.py                # App principal
│   └── utils/                      # 🛠️ Utilitários
│       ├── config.py              # Configurações
│       └── logger.py              # Logging
├── test_polygon_integration.py     # 🧪 Teste de integração
└── env.example                     # ⚙️ Exemplo de configuração
```

## 🚀 Como Usar

### 1. Configuração da API Key

1. Crie conta gratuita na [Polygon.io](https://polygon.io/)
2. Copie sua API key do [Dashboard](https://polygon.io/dashboard)
3. Configure o ambiente:

### 1. Teste Rápido da Integração

```bash
# Exportar API key temporariamente
export POLYGON_API_KEY="sua_chave_aqui"

# Testar conexão
python test_polygon_integration.py
```


## 📊 Endpoints Disponíveis

### RSI Individual
```bash
GET /api/v1/rsi/single/BTCUSD
```

### RSI Múltiplo
```bash
GET /api/v1/rsi/multiple?symbols=BTCUSD,ETHUSD,SOLUSD
```

### Sinais de Trading
```bash
GET /api/v1/rsi/signals?symbols=BTCUSD,ETHUSD
```

### Health Check
```bash
GET /api/v1/rsi/health
```


## 📝 Rate Limits

- **Polygon.io Gratuito**: 5 requests/min
- **Recomendação**: Para uso intensivo, considere plano pago ou implementação própria do cálculo RSI


