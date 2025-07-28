# Sistema de Cache Redis

O Crypto Hunter implementa um sistema de cache Redis com estratégia **cache-aside híbrido** e **TTL configurável** para otimizar performance e reduzir chamadas às APIs das exchanges.

## Características

- **Cache-aside**: Dados são buscados primeiro no cache, depois na fonte original
- **TTL configurável**: Diferentes tipos de dados têm TTLs específicos
- **Compressão automática**: Dados grandes são comprimidos automaticamente
- **Serialização híbrida**: JSON para dados simples, pickle para objetos complexos
- **Invalidação inteligente**: Suporte a invalidação por padrão

## Configuração

```python
from core.cache import CacheConfig, CacheManager

# Configuração padrão
config = CacheConfig()

# Configuração customizada
config = CacheConfig(
    ohlcv_ttl=300,      # 5 minutos
    rsi_ttl=120,        # 2 minutos
    symbols_ttl=3600,   # 1 hora
    redis_host="redis",
    redis_port=6379
)

cache_manager = CacheManager(config)
```

## TTLs Padrão

| Tipo de Dado | TTL | Justificativa |
|--------------|-----|---------------|
| OHLCV | 5 min | Dados de mercado mudam rapidamente |
| RSI | 2 min | Indicadores técnicos precisam ser atualizados |
| Symbols | 1 hora | Lista de símbolos muda pouco |
| Ticker | 1 min | Preços em tempo real |

## Uso Básico

### Dados OHLCV

```python
# Armazenar dados
ohlcv_data = [{"timestamp": "2024-01-01", "close": 50000}]
cache_manager.set_ohlcv("gateio", "BTC_USDT", "1h", ohlcv_data)

# Recuperar dados
cached_data = cache_manager.get_ohlcv("gateio", "BTC_USDT", "1h")
```

### Dados RSI

```python
# Armazenar RSI
rsi_data = {"rsi_14": {"value": 65.5, "signal": "neutral"}}
cache_manager.set_rsi("gateio", "BTC_USDT", rsi_data)

# Recuperar RSI
cached_rsi = cache_manager.get_rsi("gateio", "BTC_USDT")
```

### Lista de Símbolos

```python
# Armazenar símbolos
symbols = ["BTC_USDT", "ETH_USDT", "ADA_USDT"]
cache_manager.set_symbols("gateio", symbols)

# Recuperar símbolos
cached_symbols = cache_manager.get_symbols("gateio")
```

## Invalidação

```python
# Invalidar todos os dados de uma exchange
deleted_count = cache_manager.invalidate_exchange("gateio")

# Limpar todo o cache
cache_manager.cache.clear()
```

## Monitoramento

### Health Check

```python
# Verificar saúde do cache
is_healthy = cache_manager.health_check()
```

### Estatísticas

```python
# Obter estatísticas
stats = cache_manager.cache.get_stats()
print(f"Hit rate: {stats['hit_rate']}%")
print(f"Memory usage: {stats['used_memory_human']}")
```

## Integração com DataCollector

O `DataCollector` já está integrado com o cache:

```python
# O DataCollector verifica cache automaticamente
data_collector = DataCollector(exchange_manager)

# Ao buscar dados OHLCV
ohlcv_data = await exchange.get_ohlcv(symbol, timeframe)
# Se não estiver no cache, busca da exchange e armazena
```

## API Endpoints

### Estatísticas do Cache

```bash
GET /cache/stats
```

### Limpar Cache

```bash
POST /cache/clear
```

## Testes

### Teste Manual

```bash
python scripts/test_cache.py
```

### Testes Unitários

```bash
pytest tests/unit/test_cache.py -v
```

## Performance

O cache Redis oferece:

- **Latência**: < 1ms para operações locais
- **Throughput**: > 100k ops/s
- **Compressão**: Redução de 60-80% no uso de memória
- **TTL**: Expiração automática evita dados obsoletos

## Troubleshooting

### Cache não conecta

1. Verifique se o Redis está rodando:
   ```bash
   docker compose ps redis
   ```

2. Teste conexão:
   ```bash
   python scripts/test_cache.py
   ```

### Dados não aparecem

1. Verifique TTL:
   ```python
   ttl = cache_manager.cache.get_ttl("chave")
   ```

2. Verifique se dados foram armazenados:
   ```python
   exists = cache_manager.cache.exists("chave")
   ```

### Performance ruim

1. Monitore estatísticas:
   ```python
   stats = cache_manager.cache.get_stats()
   ```

2. Ajuste TTLs conforme necessário
3. Considere aumentar memória do Redis 