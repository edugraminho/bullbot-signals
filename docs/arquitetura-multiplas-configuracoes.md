# 🎯 Arquitetura para Múltiplas Configurações Personalizadas

## 🤔 **Problema Atual**

O sistema atual usa **uma configuração global** no `config.py`:
- RSI 15m, 1h, 4h para todos
- Mesmos símbolos para todos  
- Mesmos níveis RSI (20/80) para todos

**Quando cada usuário quiser configurações diferentes:**
- Usuário A: RSI 15m + BTC,ETH,SOL + níveis 25/75
- Usuário B: RSI 4h + ADA,DOT,AVAX + níveis 30/70
- Usuário C: RSI 1h + todas as moedas + níveis 20/80

## 🏗️ **Solução Arquitetural**

### **1. Estratégia: "Detectar Tudo, Filtrar Depois"**

```
┌─────────────────────────────────────────────────────────────┐
│                    BULLBOT SIGNALS                          │
│                                                             │
│  🔍 MONITORAMENTO GLOBAL                                   │
│  • Detecta TODOS os sinais possíveis                       │
│  • Múltiplos timeframes (15m, 1h, 4h)                     │
│  • Todos os símbolos disponíveis                           │
│  • Salva no banco com metadados completos                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    TELEGRAM BOT                             │
│                                                             │
│  🎯 FILTRO PERSONALIZADO                                    │
│  • Busca sinais não processados                            │
│  • Para cada usuário: filtra por configurações             │
│  • Envia apenas sinais relevantes                          │
│  • Marca como processado                                   │
└─────────────────────────────────────────────────────────────┘
```

### **2. Vantagens desta Abordagem**

#### ✅ **Simplicidade**
- **Um único serviço** de detecção
- **Sem duplicação** de processamento
- **Sem complexidade** de múltiplos workers

#### ✅ **Escalabilidade**
- **N usuários** = **1 serviço** de detecção
- **Performance linear** com número de usuários
- **Sem overhead** de múltiplas instâncias

#### ✅ **Flexibilidade**
- **Configurações dinâmicas** sem reiniciar
- **Adicionar/remover** usuários facilmente
- **Mudar configurações** em tempo real

#### ✅ **Eficiência**
- **Rate limiting** centralizado
- **Cache compartilhado** de dados OHLCV
- **Otimização** de recursos

## 📊 **Implementação Técnica**

### **1. Monitoramento Global (BullBot Signals)**

```python
# src/tasks/monitor_tasks.py
@celery_app.task
def monitor_rsi_signals():
    """Monitora TODOS os timeframes e símbolos"""
    
    # Timeframes fixos para cobrir todas as necessidades
    timeframes = ["15m", "1h", "4h"]
    
    # Símbolos: todos disponíveis (200+)
    symbols = get_all_trading_symbols()
    
    for timeframe in timeframes:
        for symbol in symbols:
            # Calcular RSI e gerar sinal
            signal = calculate_rsi_signal(symbol, timeframe)
            
            # Salvar com metadados completos
            save_signal_to_db(signal, {
                "timeframe": timeframe,
                "rsi_value": signal.rsi_value,
                "rsi_period": 14,
                "price": signal.price,
                "volume_24h": signal.volume_24h,
                "processed": False  # Aguarda processamento pelo bot
            })
```

### **2. Filtro Personalizado (Telegram Bot)**

```python
# telegram_bot/signal_processor.py
class PersonalizedSignalProcessor:
    
    async def process_signals_for_user(self, user_id: int):
        """Processa sinais específicos para um usuário"""
        
        # 1. Buscar configuração do usuário
        user_config = await self.get_user_config(user_id)
        # {
        #     "symbols": ["BTC", "ETH", "SOL"],
        #     "timeframes": ["15m", "1h"],
        #     "rsi_oversold": 25,
        #     "rsi_overbought": 75,
        #     "min_strength": "MODERATE"
        # }
        
        # 2. Buscar sinais não processados
        unprocessed_signals = await self.get_unprocessed_signals()
        
        # 3. Filtrar para este usuário
        relevant_signals = self.filter_signals_for_user(
            unprocessed_signals, user_config
        )
        
        # 4. Enviar sinais relevantes
        for signal in relevant_signals:
            await self.send_signal_to_user(user_id, signal)
            await self.mark_signal_processed(signal.id, f"user_{user_id}")
    
    def filter_signals_for_user(self, signals, user_config):
        """Filtra sinais baseado na configuração do usuário"""
        filtered = []
        
        for signal in signals:
            # Verificar símbolo
            if signal.symbol not in user_config["symbols"]:
                continue
                
            # Verificar timeframe
            if signal.timeframe not in user_config["timeframes"]:
                continue
                
            # Verificar níveis RSI personalizados
            if user_config["rsi_oversold"] <= signal.rsi_value <= user_config["rsi_overbought"]:
                continue
                
            # Verificar força mínima
            if signal.strength < user_config["min_strength"]:
                continue
                
            filtered.append(signal)
        
        return filtered
```

## 🗄️ **Estrutura do Banco de Dados**

### **1. Tabela de Configurações de Usuário**

```sql
CREATE TABLE telegram_user_configs (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,  -- Telegram user ID
    username VARCHAR(100),
    
    -- Configurações de símbolos
    symbols JSONB NOT NULL,  -- ["BTC", "ETH", "SOL"]
    timeframes JSONB NOT NULL,  -- ["15m", "1h", "4h"]
    
    -- Configurações RSI personalizadas
    rsi_oversold INTEGER DEFAULT 20,
    rsi_overbought INTEGER DEFAULT 80,
    rsi_period INTEGER DEFAULT 14,
    
    -- Filtros adicionais
    min_strength VARCHAR(20) DEFAULT 'WEAK',  -- WEAK, MODERATE, STRONG
    max_signals_per_day INTEGER DEFAULT 10,
    cooldown_minutes INTEGER DEFAULT 120,
    
    -- Status
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### **2. Tabela de Histórico de Envios**

```sql
CREATE TABLE telegram_signal_deliveries (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    signal_id INTEGER NOT NULL,
    delivered_at TIMESTAMP DEFAULT NOW(),
    delivery_status VARCHAR(20),  -- SUCCESS, FAILED, BLOCKED
    
    FOREIGN KEY (signal_id) REFERENCES signal_history(id),
    UNIQUE(user_id, signal_id)  -- Evita duplicatas
);
```

## 🔄 **Fluxo de Funcionamento**

### **1. Monitoramento Global (5 min)**
```
BullBot Signals:
├── Buscar dados OHLCV (200+ símbolos × 3 timeframes)
├── Calcular RSI para cada combinação
├── Gerar sinais com metadados completos
└── Salvar no banco (processed = false)
```

### **2. Processamento Personalizado (30s)**
```
Telegram Bot:
├── Para cada usuário ativo:
│   ├── Buscar configuração personalizada
│   ├── Filtrar sinais não processados
│   ├── Aplicar filtros específicos
│   ├── Enviar sinais relevantes
│   └── Marcar como processado
└── Aguardar 30s e repetir
```

## 📈 **Performance e Escalabilidade**

### **Cenários de Carga**

#### **Cenário 1: 100 usuários**
- **Detecção**: 1 serviço processando 600 sinais/min (200 símbolos × 3 timeframes)
- **Filtro**: 100 filtros paralelos (muito leve)
- **Total**: ~1GB RAM, 2 vCPU

#### **Cenário 2: 1.000 usuários**
- **Detecção**: Mesmo serviço (sem mudança)
- **Filtro**: 1.000 filtros paralelos (ainda leve)
- **Total**: ~1.5GB RAM, 2 vCPU

#### **Cenário 3: 10.000 usuários**
- **Detecção**: Mesmo serviço (sem mudança)
- **Filtro**: 10.000 filtros paralelos
- **Otimização**: Batch processing, cache de configurações
- **Total**: ~2GB RAM, 4 vCPU

### **Otimizações para Escala**

#### **1. Cache de Configurações**
```python
# Redis cache para configurações de usuário
user_configs_cache = {
    "user_123": {
        "symbols": ["BTC", "ETH"],
        "timeframes": ["15m"],
        "rsi_oversold": 25,
        "rsi_overbought": 75
    }
}
```

#### **2. Batch Processing**
```python
# Processar usuários em lotes
async def process_users_batch(user_ids: List[int]):
    # Buscar configurações em lote
    configs = await get_user_configs_batch(user_ids)
    
    # Buscar sinais uma vez
    signals = await get_unprocessed_signals()
    
    # Processar cada usuário
    for user_id in user_ids:
        user_signals = filter_signals_for_config(signals, configs[user_id])
        await send_signals_to_user(user_id, user_signals)
```

#### **3. Índices Otimizados**
```sql
-- Índices para performance
CREATE INDEX idx_signal_history_unprocessed ON signal_history(processed, created_at);
CREATE INDEX idx_signal_history_symbol_timeframe ON signal_history(symbol, timeframe);
CREATE INDEX idx_telegram_deliveries_user_signal ON telegram_signal_deliveries(user_id, signal_id);
```

## 🎯 **Vantagens Finais**

### ✅ **Simplicidade Operacional**
- **Um serviço** de detecção para manter
- **Configurações** via banco de dados
- **Sem reinicializações** para mudanças

### ✅ **Custo Eficiente**
- **Recursos mínimos** para detecção
- **Escala linear** com usuários
- **Sem duplicação** de processamento

### ✅ **Flexibilidade Total**
- **Configurações únicas** por usuário
- **Mudanças em tempo real**
- **Sem limites** de personalização

### ✅ **Confiabilidade**
- **Sinais nunca perdidos**
- **Processamento idempotente**
- **Recuperação automática** de falhas

**Esta arquitetura suporta milhares de usuários com configurações únicas sem complexidade! 🚀**
