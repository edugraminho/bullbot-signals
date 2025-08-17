# ⚙️ Configurações Globais - config.py

## 📝 **Visão Geral**

O sistema usa configurações em **3 níveis de prioridade**:

1. **🎯 Configurações de Usuário** (Prioridade ALTA) - `user_monitoring_configs.filter_config`
2. **🌐 Configurações Globais** (Prioridade MÉDIA) - `config.py` 
3. **⚙️ Configurações Hardcoded** (Prioridade BAIXA) - Valores padrão no código

## 🛡️ **Filtros Anti-Spam - config.py**

### **Cooldown por Timeframe e Força (em minutos):**

```python
# 15 minutos
signal_filter_cooldown_15m_strong: int = 15       # 15 min
signal_filter_cooldown_15m_moderate: int = 30     # 30 min  
signal_filter_cooldown_15m_weak: int = 60         # 1 hora

# 1 hora
signal_filter_cooldown_1h_strong: int = 60        # 1 hora
signal_filter_cooldown_1h_moderate: int = 120     # 2 horas
signal_filter_cooldown_1h_weak: int = 240         # 4 horas

# 4 horas  
signal_filter_cooldown_4h_strong: int = 120       # 2 horas
signal_filter_cooldown_4h_moderate: int = 240     # 4 horas
signal_filter_cooldown_4h_weak: int = 360         # 6 horas

# 1 dia
signal_filter_cooldown_1d_strong: int = 360       # 6 horas
signal_filter_cooldown_1d_moderate: int = 720     # 12 horas
signal_filter_cooldown_1d_weak: int = 1440        # 24 horas
```

### **Limites Diários:**

```python
signal_filter_max_signals_per_symbol: int = 3     # Max sinais/símbolo/dia
signal_filter_max_strong_signals: int = 2         # Max sinais STRONG/símbolo/dia
signal_filter_min_rsi_difference: float = 2.0     # Diferença mínima RSI
```

## 🔄 **Como o Sistema Decide:**

### **1. Prioridade de Configurações:**

```python
# 1º - Verifica se usuário tem filter_config personalizado
if user_config.filter_config:
    use_user_config()  # 🎯 USAR CONFIGURAÇÃO DO USUÁRIO

# 2º - Se não há config de usuário, usa config.py  
elif settings.signal_filter_cooldown_15m_strong:
    use_global_config()  # 🌐 USAR CONFIGURAÇÃO GLOBAL

# 3º - Se config.py falha, usa hardcoded
else:
    use_hardcoded_defaults()  # ⚙️ USAR PADRÃO HARDCODED
```

### **2. Agregação de Múltiplos Usuários:**

Quando múltiplos usuários têm configurações diferentes, o sistema usa a **mais restritiva**:

```python
# Exemplo: 3 usuários ativos
User A: cooldown=60min, max_signals=5
User B: cooldown=120min, max_signals=3  
User C: cooldown=30min, max_signals=10

# Sistema usa:
Final: cooldown=30min (menor), max_signals=3 (menor)
```

## 📊 **Variáveis Disponíveis no config.py:**

### **RSI:**
```python
rsi_calculation_window: int = 14
rsi_analysis_timeframe: str = "15m"  
rsi_oversold: int = 20
rsi_overbought: int = 80
```

### **Filtros Anti-Spam:**
```python
# Cooldown 15m
signal_filter_cooldown_15m_strong: int = 15
signal_filter_cooldown_15m_moderate: int = 30
signal_filter_cooldown_15m_weak: int = 60

# Cooldown 1h
signal_filter_cooldown_1h_strong: int = 60
signal_filter_cooldown_1h_moderate: int = 120
signal_filter_cooldown_1h_weak: int = 240

# Cooldown 4h
signal_filter_cooldown_4h_strong: int = 120
signal_filter_cooldown_4h_moderate: int = 240
signal_filter_cooldown_4h_weak: int = 360

# Cooldown 1d
signal_filter_cooldown_1d_strong: int = 360
signal_filter_cooldown_1d_moderate: int = 720
signal_filter_cooldown_1d_weak: int = 1440

# Limites diários
signal_filter_max_signals_per_symbol: int = 3
signal_filter_max_strong_signals: int = 2
signal_filter_min_rsi_difference: float = 2.0
```

### **Trading Coins:**
```python
trading_coins_max_limit: int = 500
trading_coins_min_market_cap: int = 50_000_000
trading_coins_min_volume: int = 3_000_000
```

### **Celery:**
```python
celery_worker_count: int = 1
celery_tasks_per_worker: int = 1
celery_task_warning_timeout: int = 600
celery_max_memory_per_child: int = 200000
```

## 🔧 **Como Alterar Configurações:**

### **1. Via Arquivo .env:**
```bash
# Sobrescrever config.py via variáveis de ambiente
SIGNAL_FILTER_COOLDOWN_15M_STRONG=30
SIGNAL_FILTER_MAX_SIGNALS_PER_SYMBOL=5
RSI_OVERSOLD=25
RSI_OVERBOUGHT=75
```

### **2. Via config.py direto:**
```python
# src/utils/config.py
class Settings(BaseSettings):
    signal_filter_cooldown_15m_strong: int = 30  # Mudança aqui
    signal_filter_max_signals_per_symbol: int = 5  # Mudança aqui
```

### **3. Via docker-compose.yml:**
```yaml
services:
  app:
    environment:
      - SIGNAL_FILTER_COOLDOWN_15M_STRONG=30
      - SIGNAL_FILTER_MAX_SIGNALS_PER_SYMBOL=5
```

## 📈 **Exemplos de Configuração:**

### **Configuração Conservadora (Menos Sinais):**
```python
signal_filter_cooldown_15m_strong: int = 60      # 1 hora
signal_filter_cooldown_1h_strong: int = 240      # 4 horas  
signal_filter_max_signals_per_symbol: int = 1    # 1 sinal/dia
signal_filter_min_rsi_difference: float = 5.0    # 5 pontos RSI
```

### **Configuração Agressiva (Mais Sinais):**
```python
signal_filter_cooldown_15m_strong: int = 5       # 5 min
signal_filter_cooldown_1h_strong: int = 15       # 15 min
signal_filter_max_signals_per_symbol: int = 10   # 10 sinais/dia
signal_filter_min_rsi_difference: float = 0.5    # 0.5 pontos RSI
```

### **Configuração Balanceada (Padrão):**
```python
signal_filter_cooldown_15m_strong: int = 15      # 15 min
signal_filter_cooldown_1h_strong: int = 60       # 1 hora
signal_filter_max_signals_per_symbol: int = 3    # 3 sinais/dia
signal_filter_min_rsi_difference: float = 2.0    # 2 pontos RSI
```

## 🔍 **Debug e Monitoramento:**

### **Ver Configurações Ativas:**
```bash
docker compose exec app python3 -c "
from src.utils.config import settings
print('Cooldown 15m STRONG:', settings.signal_filter_cooldown_15m_strong)
print('Max signals per symbol:', settings.signal_filter_max_signals_per_symbol)
"
```

### **Testar SignalFilter:**
```bash
docker compose exec app python3 -c "
from src.core.services.signal_filter import SignalFilter
sf = SignalFilter()
print('Configurações carregadas:')
print('15m STRONG:', sf.default_cooldown_rules['15m']['STRONG']/60, 'min')
print('Daily limits:', sf.default_daily_limits)
"
```

## 🎯 **Resultado Final:**

- ✅ **Usuários**: Configurações personalizadas via Telegram
- ✅ **Admins**: Configurações globais via config.py
- ✅ **Sistema**: Fallback automático para valores padrão
- ✅ **Flexibilidade**: 3 níveis de configuração
- ✅ **Robustez**: Sistema nunca falha por falta de configuração

**Sistema configurável em todos os níveis! 🚀**