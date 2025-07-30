# API Schemas

Este diretório contém os **DTOs (Data Transfer Objects)** usados pela API REST.

## 📝 Diferença entre Models e Schemas

### 🎯 Core Models (`src/core/models/`)
- **Propósito**: Regras de negócio e entidades do domínio
- **Exemplo**: `RSIData`, `TradingSignal`, `Cryptocurrency`
- **Características**: 
  - Contêm lógica de negócio
  - Independentes de formato de API
  - Usam tipos específicos (Decimal, datetime)

### 🌐 API Schemas (`src/api/schemas/`)
- **Propósito**: Serialização/deserialização HTTP
- **Exemplo**: `RSIResponse`, `SignalResponse`
- **Características**:
  - Apenas estrutura de dados
  - Otimizados para JSON
  - Tipos compatíveis com HTTP (str, float, int)

## 📁 Organização

```
src/api/schemas/
├── common.py        # Schemas genéricos (Error, Success, Status)
├── rsi.py          # Schemas específicos do RSI
└── README.md       # Esta documentação
```

## 🔄 Fluxo de Conversão

```
Domain Model → Service → API Schema → JSON Response
RSIData → RSIService → RSIResponse → {"symbol": "BTC", "rsi_value": 65.4}
```

## ✅ Boas Práticas

1. **Separação Clara**: Models ≠ Schemas
2. **Nomenclatura**: Adicionar sufixo `Response`, `Request`
3. **Validação**: Usar Pydantic validators quando necessário
4. **Documentação**: Adicionar docstrings descritivas