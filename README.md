# Crypto Hunter 🤖

Bot automatizado para trading de criptomoedas baseado no indicador RSI (Relative Strength Index), com suporte a múltiplas exchanges e sistema de notificações.

## 🚀 Funcionalidades Implementadas

### ✅ Etapa 1: Coleta de Dados e Indicadores

- **✅ Gestão de Exchanges**: Adapter para Gate.io implementado
- **✅ Coleta de Dados**: Sistema de coleta automática de OHLCV
- **✅ Mapeamento de Símbolos**: Descoberta automática de criptomoedas disponíveis
- **✅ Cálculo de RSI**: Múltiplos períodos (14, 21, 50) e timeframes
- **✅ Geração de Sinais**: Detecção de sobrecompra/sobrevenda
- **✅ Sistema de Configuração**: Arquivos YAML para configuração flexível

## 🏗️ Arquitetura

```
crypto-hunter/
├── core/                    # Lógica de negócio
│   ├── exchanges/          # Adaptadores de exchanges
│   │   ├── base.py        # Interface comum
│   │   ├── gateio.py      # Adapter da Gate.io
│   │   └── factory.py     # Factory para exchanges
│   ├── indicators/         # Cálculo de indicadores
│   │   ├── base.py        # Interface de indicadores
│   │   └── rsi.py         # Calculador de RSI
│   └── data_collector.py  # Serviço de coleta
├── config/                 # Configurações
│   └── exchanges.yaml     # Configuração de exchanges
├── utils/                  # Utilitários
│   └── config_loader.py   # Carregador de configurações
└── scripts/               # Scripts de execução
    ├── test_gateio_collection.py  # Teste da Gate.io
    └── main_collector.py          # Sistema principal
```

## 🛠️ Instalação

### 1. Clone o repositório
```bash
git clone <repository-url>
cd crypto-hunter
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Configure o ambiente
```bash
# Copie o arquivo de exemplo de variáveis de ambiente
cp env.example .env

# Edite o arquivo .env com suas credenciais da Gate.io
# Obtenha suas credenciais em: https://www.gate.com/docs/developers/apiv4/en/#generate-api-key
```

## 🚀 Como Usar

### Teste Rápido da Gate.io

Para testar a conexão e coleta de dados da Gate.io:

```bash
# Teste de integração (requer credenciais)
python tests/integration/test_gateio_connection.py

# Testes unitários (não requer credenciais)
pytest tests/unit/test_gateio_adapter.py

# Exemplo de uso
python scripts/example_gateio_usage.py
```

Os testes irão:
- ✅ Testar a conexão com a Gate.io
- 📊 Descobrir símbolos disponíveis
- 📈 Coletar dados OHLCV
- 🧮 Calcular RSI para múltiplos períodos
- 🔍 Identificar símbolos em sobrecompra/sobrevenda

### Sistema Principal

Para executar o sistema completo de monitoramento:

```bash
python scripts/main_collector.py
```

O sistema irá:
- 🔧 Carregar configurações
- 🔍 Descobrir símbolos automaticamente
- 📊 Coletar dados continuamente
- 📈 Calcular RSI em tempo real
- 🔥 Identificar oportunidades de trading

## 🧪 Testes

### Executando Testes

```bash
# Testes unitários (não requerem credenciais)
pytest tests/unit/

# Testes de integração (requerem credenciais da API)
python tests/integration/test_gateio_connection.py

# Todos os testes
pytest tests/
```

### Estrutura de Testes

```
tests/
├── unit/                    # Testes unitários
│   ├── test_gateio_adapter.py
│   └── test_rsi_calculator.py
└── integration/            # Testes de integração
    └── test_gateio_connection.py
```

## 📋 Configuração

### Variáveis de Ambiente

Copie o arquivo de exemplo e configure suas credenciais:

```bash
cp env.example .env
```

Edite o arquivo `.env` com suas credenciais da Gate.io.

### Arquivo de Configuração (`config/exchanges.yaml`)

```yaml
# Gate.io
gateio:
  name: "gateio"
  api_key: null  # Configure se necessário
  api_secret: null
  rate_limit: 100
  timeframes:
    - "1m"
    - "5m"
    - "15m"
    - "1h"
    - "4h"
    - "1d"

# Configurações globais
global:
  collection_interval: 60  # segundos
  max_data_points: 1000
  rsi_periods: [14, 21, 50]
  overbought_level: 70
  oversold_level: 30
  timeframes: ["1h", "4h", "1d"]
```

### Variáveis de Ambiente (Opcional)

```bash
# Banco de dados
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=crypto_hunter
export DB_USER=postgres
export DB_PASSWORD=your_password

# Redis
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_PASSWORD=your_password
```

## 📊 Exemplos de Uso

### 1. Descoberta de Símbolos

```python
from core.exchanges import ExchangeManager

# Configura Gate.io
exchange_manager = ExchangeManager()
exchange_manager.add_exchange("gateio", {
    "api_key": None,
    "api_secret": None,
    "rate_limit": 100
})

# Descobre símbolos
symbols = await exchange_manager.get_all_symbols()
print(f"Encontrados {len(symbols['gateio'])} símbolos na Gate.io")
```

### 2. Cálculo de RSI

```python
from core.indicators import RSICalculator

# Configura RSI
rsi_calc = RSICalculator({
    "period": 14,
    "overbought_level": 70,
    "oversold_level": 30
})

# Calcula RSI
results = rsi_calc.calculate(ohlcv_data)
latest_signal = rsi_calc.get_latest_signal(ohlcv_data)
```

### 3. Coleta Contínua de Dados

```python
from core.data_collector import DataCollector, DataCollectionConfig

# Configura coletor
config = DataCollectionConfig(
    symbols=["BTC_USDT", "ETH_USDT"],
    timeframes=["1h", "4h"],
    rsi_periods=[14, 21],
    collection_interval=60
)

collector = DataCollector(exchange_manager)
collector.configure(config)

# Inicia coleta
await collector.start_collection()
```

## 🚀 Como Usar

### Teste da Gate.io

```bash
# Testa conexão e busca símbolos
python scripts/test_gateio_collection.py
```

### Sistema Principal

```bash
# Executa coleta de dados e cálculo de RSI
python scripts/main_collector.py
```

### Execução de Testes

```bash
# Executa todos os testes
python scripts/run_tests.py

# Via Docker
./scripts/run_tests_docker.sh
```

## 🔍 Monitoramento

### Logs

Os logs são salvos em `logs/crypto_hunter.log` e também exibidos no console:

```
2025-01-XX 10:30:00 - INFO - Iniciando Crypto Hunter...
2025-01-XX 10:30:01 - INFO - Configurações carregadas com sucesso
2025-01-XX 10:30:02 - INFO - Gate.io configurada
2025-01-XX 10:30:03 - INFO - gateio: 1500 símbolos encontrados
2025-01-XX 10:30:04 - INFO - gateio - Símbolos em sobrecompra:
2025-01-XX 10:30:04 - INFO -   BTC_USDT (1h): RSI=75.23
```

### Sinais Detectados

O sistema identifica automaticamente:

- **Sobrecompra**: RSI > 70 (configurável)
- **Sobrevenda**: RSI < 30 (configurável)
- **Tendência de Alta**: RSI < 50
- **Tendência de Baixa**: RSI > 50

## 🎯 Próximos Passos

### Etapa 2: Sistema de Notificações
- [ ] Integração com Discord
- [ ] Integração com Telegram
- [ ] Templates de mensagens
- [ ] Filtros de notificação

### Etapa 3: Sistema de Trading
- [ ] Execução automática de trades
- [ ] Gestão de portfólio
- [ ] Controle de risco
- [ ] Backtesting

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## ⚠️ Disclaimer

Este software é fornecido "como está" e não constitui aconselhamento financeiro. Trading de criptomoedas envolve riscos significativos. Use por sua conta e risco.

---

**Desenvolvido com ❤️ para a comunidade crypto** 