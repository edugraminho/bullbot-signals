# APIs de RSI para Criptomoedas - Anotações

## Resumo da Conversa
Conversa sobre como encontrar APIs que forneçam o indicador RSI (Relative Strength Index) para criptomoedas, com foco em exchanges populares e opções gratuitas.

---

## APIs Recomendadas

### 1. Polygon.io (Recomendado Principal)
- **Endpoint**: `/v1/indicators/rsi/{cryptoTicker}`
- **Gratuito**: Sim, com limites (5 requests/min no plano gratuito)
- **Cobertura**: Múltiplas criptomoedas (BTC, ETH, SOL, etc.)
- **Parâmetros configuráveis**:
  - `window`: Tamanho da janela (padrão 14)
  - `timespan`: Período dos dados (minuto, hora, dia, etc.)
  - `series_type`: Tipo de preço usado (close, open, high, low)

**Vantagens**:
- ✅ API dedicada e bem documentada
- ✅ Dados históricos disponíveis
- ✅ Fácil integração
- ✅ Suporte a múltiplas criptomoedas

### 2. CoinMarketCap API
- **Cobertura**: 2.4 milhões+ de ativos rastreados
- **Dados históricos**: 14 anos de dados históricos
- **Endpoints**: 40+ endpoints disponíveis
- **Gratuito**: Sim, com plano básico gratuito
- **Dados incluídos**: Preços em tempo real, dados históricos OHLCV, métricas de mercado

---

## RSI Pronto vs Implementação Própria

### RSI Pronto (Ready-to-Use)
**O que é**: API fornece o valor do RSI já calculado

**Exemplo**:
```json
{
  "values": [
    {
      "timestamp": 1640995200000,
      "value": 65.4  // RSI já calculado
    }
  ]
}
```

**Vantagens**:
- ✅ Implementação rápida
- ✅ Menos código
- ✅ Menos bugs
- ✅ Performance (processamento no servidor)

**Desvantagens**:
- ❌ Dependência externa
- ❌ Rate limits
- ❌ Possível custo
- ❌ Latência de requisição

### RSI que Precisa Calcular
**O que é**: API fornece dados brutos (preços OHLCV), você implementa a fórmula

**Vantagens**:
- ✅ Independência
- ✅ Sem rate limits
- ✅ Sem custos
- ✅ Baixa latência
- ✅ Controle total

**Desvantagens**:
- ❌ Mais código
- ❌ Mais bugs
- ❌ Processamento local
- ❌ Complexidade

---

## Fórmula do RSI

Baseado na [Wikipedia](https://en.wikipedia.org/wiki/Relative_strength_index):

1. **Calcular mudanças**:
   - `U = close_now - close_previous` (se positivo, senão 0)
   - `D = close_previous - close_now` (se positivo, senão 0)

2. **Calcular médias**:
   - `SMMA(U, n)` - média suavizada dos valores U
   - `SMMA(D, n)` - média suavizada dos valores D

3. **Calcular RSI**:
   - `RS = SMMA(U, n) / SMMA(D, n)`
   - `RSI = 100 - (100 / (1 + RS))`

---

## Exchanges que Fornecem OHLCV

### 1. Binance ✅
- **Endpoint**: `/api/v3/klines`
- **Gratuito**: Sim
- **Rate limit**: 1200 requests/min
- **Timeframes**: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M

### 2. Bybit ✅
- **Endpoint**: `/v5/market/kline`
- **Gratuito**: Sim
- **Rate limit**: 120 requests/sec
- **Timeframes**: 1, 3, 5, 15, 30, 60, 120, 240, 360, 720, D, W, M

### 3. Gate.io ✅
- **Endpoint**: `/api/v4/spot/candlesticks`
- **Gratuito**: Sim
- **Rate limit**: 100 requests/sec
- **Timeframes**: 10s, 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M

### 4. MEXC ✅
- **Endpoint**: `/api/v3/klines`
- **Gratuito**: Sim
- **Rate limit**: 20 requests/sec
- **Timeframes**: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M

---

## Complexidade do Cálculo RSI

### Nível de Dificuldade: Médio-Baixo ⭐⭐⭐

**Tempo estimado**: 2-4 horas para implementar e testar corretamente.

**Implementação Python**:
```python
def calculate_rsi(prices, period=14):
    """
    Calcula RSI para uma lista de preços
    """
    if len(prices) < period + 1:
        return None
    
    # Passo 1: Calcular mudanças
    changes = []
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        changes.append(change)
    
    # Passo 2: Separar ganhos e perdas
    gains = [change if change > 0 else 0 for change in changes]
    losses = [-change if change < 0 else 0 for change in changes]
    
    # Passo 3: Calcular médias iniciais
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    # Passo 4: Calcular RSI para cada período
    rsi_values = []
    
    for i in range(period, len(changes)):
        # Atualizar médias
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        # Calcular RSI
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        rsi_values.append(rsi)
    
    return rsi_values
```

---

## Estratégia Recomendada

### Para Prototipagem Rápida:
- Use **Polygon.io** (RSI pronto)
- Foca na lógica do bot primeiro

### Para Produção/Otimização:
- Use **Binance + cálculo próprio**
- Mais confiável e escalável

### Estratégia Híbrida:
- Comece com RSI pronto para validar ideia
- Migre para cálculo próprio quando estiver funcionando

---

## Interpretação do RSI

### Níveis Clássicos:
- **RSI > 70**: Sobrevendido (possível reversão de alta)
- **RSI < 30**: Sobrevendido (possível reversão de baixa)
- **RSI = 50**: Linha neutra

### Níveis Extremos:
- **RSI > 80**: Fortemente sobrevendido
- **RSI < 20**: Fortemente sobrevendido

### Divergências:
- **Divergência de alta**: Preço faz mínima menor, RSI faz mínima maior
- **Divergência de baixa**: Preço faz máxima maior, RSI faz máxima menor

---

## Conclusões

1. **Polygon.io** é a melhor opção para RSI pronto
2. **Binance** é a melhor opção para implementação própria
3. O cálculo do RSI não é difícil de implementar
4. Recomenda-se começar com API pronta e migrar para implementação própria
5. Todas as exchanges principais oferecem dados OHLCV gratuitos

---

*Notas criadas em: Janeiro 2025*
*Fonte: Conversa sobre APIs de RSI para criptomoedas* 




trocar APIs! A arquitetura está bem estruturada com padrão de Adapter/Repository.
📋 Pontos Positivos da Arquitetura:
1. Separação de Responsabilidades:
src/adapters/ - Contém apenas clientes de APIs externas
src/core/services/ - Lógica de negócio independente da API
src/api/routes.py - Endpoints da API
2. Inversão de Dependência:
RSIService usa PolygonClient mas pode usar qualquer client
Interfaces bem definidas com RSIData model