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

## 🔄 Execução Contínua

O **Crypto Hunter** opera em modo contínuo para fornecer dados e sinais em tempo real. Aqui está como funciona o fluxo de execução:

### Como o Sistema Funciona

O sistema opera como um **relógio inteligente** que nunca para, monitorando constantemente o mercado de criptomoedas. Imagine-o como um **observador atento** que:

1. **Observa** as exchanges continuamente
2. **Coleta** dados de preços em tempo real
3. **Analisa** os movimentos do mercado
4. **Calcula** indicadores técnicos
5. **Identifica** oportunidades de trading
6. **Notifica** quando encontra algo interessante

### Arquitetura de Execução

O sistema possui **duas formas** de operar:

#### **Modo Síncrono (FastAPI)**
- **Funciona como um relógio** que executa tarefas em sequência
- **Coleta dados** a cada intervalo configurado (ex: 60 segundos)
- **Processa tudo** de forma ordenada e controlada
- **Ideal para** sistemas menores ou testes

#### **Modo Assíncrono (Celery)**
- **Funciona como uma fábrica** com várias linhas de produção
- **Executa tarefas** em paralelo e independentemente
- **Agenda trabalhos** para horários específicos
- **Ideal para** sistemas em produção com alta demanda

### Fluxo Detalhado de Execução

#### **Fase 1: Inicialização (Preparação)**
Quando o sistema inicia, ele faz uma **preparação completa**:

1. **Conecta** com as exchanges (Gate.io, etc.)
2. **Configura** o sistema de cache para armazenar dados
3. **Prepara** os calculadores de indicadores
4. **Descobre** quais criptomoedas estão disponíveis
5. **Faz uma coleta inicial** para "aquecer" o sistema

É como **ligar um carro** - você precisa verificar se tudo está funcionando antes de sair.

#### **Fase 2: Loop Principal (Operação Contínua)**
Depois da inicialização, o sistema entra em um **ciclo infinito** que:

1. **Coleta dados** de todas as exchanges configuradas
2. **Processa** os dados coletados
3. **Calcula** indicadores técnicos (RSI, etc.)
4. **Identifica** sinais de trading
5. **Armazena** resultados no cache
6. **Aguarda** o próximo ciclo

É como um **coração batendo** - cada batida representa um ciclo completo de coleta e análise.

### Processo de Coleta de Dados

#### **Passo 1: Descoberta de Símbolos**
O sistema primeiro **mapeia** o que está disponível:

- **Conecta** com cada exchange
- **Lista** todas as criptomoedas disponíveis
- **Filtra** apenas as que atendem aos critérios (volume, liquidez)
- **Armazena** a lista no cache para não precisar buscar novamente

É como **fazer um inventário** de uma loja - você precisa saber o que tem antes de começar a trabalhar.

#### **Passo 2: Coleta de Dados OHLCV**
Para cada criptomoeda, o sistema coleta dados de preços:

- **Verifica** se já tem dados recentes no cache
- **Se tem**: usa os dados do cache (mais rápido)
- **Se não tem**: busca novos dados da exchange
- **Armazena** os dados coletados para uso futuro

Os dados OHLCV incluem:
- **Open**: Preço de abertura
- **High**: Preço mais alto do período
- **Low**: Preço mais baixo do período
- **Close**: Preço de fechamento
- **Volume**: Quantidade negociada

#### **Passo 3: Cálculo de Indicadores**
Com os dados coletados, o sistema calcula indicadores técnicos:

- **RSI (14 períodos)**: Para análise de curto prazo
- **RSI (21 períodos)**: Para análise de médio prazo
- **RSI (50 períodos)**: Para análise de longo prazo

Cada cálculo gera:
- **Valor numérico** do indicador
- **Tipo de sinal** (sobrecompra, sobrevenda, neutro)
- **Força do sinal** (quão forte é o indicador)
- **Timestamp** (quando foi calculado)

### Sistema de Cache Inteligente

O sistema usa uma **estratégia de cache inteligente** para otimizar performance:

#### **Como Funciona**
1. **Primeiro verifica** se já tem os dados no cache
2. **Se tem e está atualizado**: usa os dados do cache
3. **Se não tem ou está desatualizado**: busca novos dados
4. **Armazena** os novos dados no cache para uso futuro

#### **Benefícios**
- **Reduz requisições** às APIs das exchanges
- **Aumenta velocidade** de resposta
- **Diminui custos** de API
- **Melhora confiabilidade** do sistema

### Controle de Intervalos

#### **Configuração de Tempos**
O sistema permite configurar **diferentes intervalos**:

- **Coleta de dados**: A cada 60 segundos (configurável)
- **Cálculo de RSI**: A cada 1 minuto
- **Verificação de sinais**: A cada 2 minutos
- **Limpeza de cache**: A cada 1 hora

#### **Loop de Execução**
O sistema funciona em um **loop contínuo**:

1. **Executa** todas as tarefas programadas
2. **Aguarda** o tempo configurado
3. **Repete** o processo infinitamente
4. **Trata erros** automaticamente se algo falhar

### Tratamento de Erros Robusto

#### **Recuperação Automática**
O sistema é **resistente a falhas**:

- **Se uma exchange falha**: tenta outras exchanges
- **Se a API está lenta**: aguarda e tenta novamente
- **Se o cache falha**: usa dados diretos da exchange
- **Se o cálculo falha**: registra o erro e continua

#### **Logs Detalhados**
O sistema registra **tudo que acontece**:

- **Logs de inicialização**: quando o sistema inicia
- **Status das exchanges**: se estão funcionando
- **Dados coletados**: quantos símbolos foram processados
- **Sinais detectados**: quais oportunidades foram encontradas
- **Erros e exceções**: para debugging e correção

### Paralelismo e Performance

#### **Processamento Simultâneo**
O sistema processa **múltiplas coisas ao mesmo tempo**:

- **Várias exchanges**: conecta com Gate.io, Binance, etc. simultaneamente
- **Múltiplos símbolos**: analisa BTC, ETH, SOL ao mesmo tempo
- **Diferentes timeframes**: processa 1h, 4h, 1d em paralelo
- **Cálculos independentes**: RSI 14, 21, 50 simultaneamente

#### **Otimizações Inteligentes**
- **Cache-first**: sempre verifica cache antes de buscar dados
- **TTL configurável**: dados expiram em tempos diferentes
- **Rate limiting**: respeita limites das APIs das exchanges
- **Compressão**: dados são comprimidos para economizar espaço

### Monitoramento em Tempo Real

#### **Health Checks**
O sistema **monitora sua própria saúde**:

- **Verifica conexões** com exchanges
- **Testa acesso** ao cache
- **Valida cálculos** de indicadores
- **Reporta status** via API REST

#### **Métricas de Performance**
- **Tempo de resposta** das APIs
- **Taxa de sucesso** das coletas
- **Uso de memória** e cache
- **Número de sinais** detectados

### Configuração Flexível

#### **Intervalos Personalizáveis**
Você pode configurar **diferentes intervalos**:

- **Coleta de dados**: 30 segundos a 5 minutos
- **Cálculo de indicadores**: 1 minuto a 10 minutos
- **Verificação de sinais**: 2 minutos a 15 minutos
- **Limpeza de cache**: 1 hora a 24 horas

#### **Parâmetros Ajustáveis**
- **Número de símbolos** para monitorar
- **Timeframes** de análise (1m, 5m, 15m, 1h, 4h, 1d)
- **Períodos RSI** (14, 21, 50)
- **Limites** de sobrecompra/sobrevenda

### Resumo do Fluxo Contínuo

#### **Ciclo Completo de Operação**

1. **🔄 Inicialização**
   - Conecta com exchanges
   - Configura cache e indicadores
   - Descobre símbolos disponíveis
   - Faz coleta inicial

2. **📊 Coleta de Dados**
   - Busca dados OHLCV das exchanges
   - Verifica cache primeiro
   - Armazena dados coletados
   - Processa múltiplos símbolos

3. **🧮 Cálculo de Indicadores**
   - Calcula RSI para diferentes períodos
   - Identifica sinais de trading
   - Determina força dos sinais
   - Armazena resultados

4. **💾 Armazenamento**
   - Salva dados no cache
   - Configura TTL apropriado
   - Organiza por exchange/símbolo/timeframe
   - Otimiza para consultas rápidas

5. **⏱️ Aguarda Próximo Ciclo**
   - Espera intervalo configurado
   - Prepara para próxima execução
   - Mantém sistema ativo

6. **🛡️ Tratamento de Erros**
   - Recupera de falhas automaticamente
   - Registra logs detalhados
   - Continua operação mesmo com problemas

#### **Características do Sistema**

- **🔄 Contínuo**: Nunca para de operar
- **⚡ Rápido**: Cache inteligente para performance
- **🛡️ Robusto**: Recupera de falhas automaticamente
- **📈 Escalável**: Suporta múltiplas exchanges
- **⚙️ Configurável**: Intervalos e parâmetros ajustáveis
- **📊 Monitorado**: Health checks e logs detalhados

O sistema funciona como um **observador atento e inteligente** que nunca dorme, sempre monitorando o mercado de criptomoedas para identificar as melhores oportunidades de trading.

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