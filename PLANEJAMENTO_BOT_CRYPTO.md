# Planejamento: Bot de Trading Crypto com RSI

## Visão Geral do Projeto

### Objetivo
Desenvolver um bot automatizado para trading de criptomoedas baseado no indicador RSI (Relative Strength Index), com suporte a múltiplas exchanges e sistema de notificações.

### Etapas do Projeto
1. **Etapa 1**: Serviço de coleta de dados e cálculo de indicadores
2. **Etapa 2**: Sistema de notificações via mensagens
3. **Etapa 3**: Bot de execução automática de trades

---

## Análise de Viabilidade

### Múltiplas Exchanges - É Viável? ✅

**Sim, é totalmente viável!** As diferenças entre APIs podem ser abstraídas através de:

1. **Padrão Adapter/Strategy**: Cada exchange terá sua própria implementação
2. **Interface comum**: Todas as exchanges implementam a mesma interface
3. **Configuração por exchange**: Parâmetros específicos em arquivos de configuração

**Exemplo de abstração**:
```python
# Interface comum
class ExchangeInterface:
    def get_ohlcv(self, symbol, timeframe, limit)
    def get_symbols(self)
    def place_order(self, symbol, side, quantity, price)

# Implementações específicas
class BinanceAdapter(ExchangeInterface)
class BybitAdapter(ExchangeInterface)
class GateIOAdapter(ExchangeInterface)
```

---

## Arquitetura Proposta

### 1. Estrutura de Camadas

```
crypto-hunter/
├── core/                    # Lógica de negócio
│   ├── exchanges/          # Adaptadores de exchanges
│   ├── indicators/         # Cálculo de indicadores
│   ├── signals/           # Geração de sinais
│   └── trading/           # Execução de trades
├── data/                   # Camada de dados
│   ├── models/            # Modelos de dados
│   ├── repositories/      # Acesso a dados
│   └── migrations/        # Migrações do banco
├── services/              # Serviços externos
│   ├── messaging/         # WhatsApp, Discord, etc.
│   └── notifications/     # Sistema de notificações
├── config/                # Configurações
├── utils/                 # Utilitários
└── tests/                 # Testes
```

### 2. Componentes Principais

#### **Core - Exchanges**
- **ExchangeFactory**: Cria instâncias de exchanges
- **ExchangeAdapter**: Interface comum para todas as exchanges
- **RateLimiter**: Controle de rate limits por exchange
- **DataNormalizer**: Padroniza dados de diferentes exchanges

#### **Core - Indicators**
- **RSICalculator**: Cálculo do RSI
- **IndicatorManager**: Gerencia múltiplos indicadores
- **SignalGenerator**: Gera sinais baseados nos indicadores

#### **Core - Trading**
- **PortfolioManager**: Gerencia posições
- **RiskManager**: Controle de risco
- **OrderManager**: Execução de ordens

#### **Services - Messaging**
- **MessageBroker**: Interface para diferentes plataformas
- **TemplateEngine**: Templates de mensagens
- **NotificationManager**: Gerencia notificações

---

## Banco de Dados Recomendado

### **PostgreSQL** (Recomendação Principal)

**Vantagens**:
- ✅ Suporte nativo a JSON (útil para dados de exchanges)
- ✅ Transações ACID
- ✅ Índices eficientes para time-series
- ✅ Particionamento por data
- ✅ Backup e replicação robustos

**Estrutura de Tabelas**:
```sql
-- Dados de mercado
market_data (
    id, exchange, symbol, timeframe, timestamp, 
    open, high, low, close, volume, created_at
)

-- Indicadores calculados
indicators (
    id, symbol, indicator_type, timeframe, 
    timestamp, value, parameters, created_at
)

-- Sinais gerados
signals (
    id, symbol, signal_type, strength, 
    rsi_value, timestamp, status, created_at
)

-- Trades executados
trades (
    id, exchange, symbol, side, quantity, 
    price, status, signal_id, created_at
)

-- Configurações
configurations (
    id, exchange, symbol, rsi_period, 
    overbought_level, oversold_level, active
)
```

---

## Funcionalidades do Projeto

### **Etapa 1: Coleta de Dados e Indicadores**

#### **1.1 Gestão de Exchanges**
- [ ] Configuração de múltiplas exchanges
- [ ] Teste de conectividade
- [ ] Monitoramento de status das APIs
- [ ] Fallback automático entre exchanges

#### **1.2 Coleta de Dados**
- [ ] Coleta automática de OHLCV
- [ ] Mapeamento de símbolos disponíveis
- [ ] Armazenamento histórico
- [ ] Limpeza e validação de dados

#### **1.3 Cálculo de Indicadores**
- [ ] Cálculo de RSI configurável
- [ ] Suporte a múltiplos períodos
- [ ] Cache de cálculos
- [ ] Validação de dados para cálculo

#### **1.4 Geração de Sinais**
- [ ] Detecção de níveis de sobrecompra/sobrevenda
- [ ] Detecção de divergências
- [ ] Filtros de qualidade de sinal
- [ ] Histórico de sinais

### **Etapa 2: Sistema de Notificações**

#### **2.1 Plataformas de Mensagem**
- [ ] **Discord** (Recomendado - API robusta, webhooks)
- [ ] **Telegram** (Alternativa - Bot API simples)
- [ ] **WhatsApp Business API** (Mais complexo - requer aprovação)
- [ ] **Email** (Fallback)

#### **2.2 Funcionalidades de Notificação**
- [ ] Templates personalizáveis
- [ ] Filtros por tipo de sinal
- [ ] Agendamento de notificações
- [ ] Histórico de notificações
- [ ] Configuração de usuários/grupos

### **Etapa 3: Sistema de Trading**

#### **3.1 Gestão de Portfólio**
- [ ] Tracking de posições
- [ ] Cálculo de P&L
- [ ] Gestão de capital
- [ ] Histórico de trades

#### **3.2 Execução de Ordens**
- [ ] Ordens de mercado e limite
- [ ] Stop loss e take profit
- [ ] Sizing de posição
- [ ] Validação de ordens

#### **3.3 Controle de Risco**
- [ ] Limites de perda diária
- [ ] Tamanho máximo de posição
- [ ] Diversificação por símbolo
- [ ] Circuit breakers

---

## Configurações e Parâmetros

### **Por Exchange**
```yaml
binance:
  api_key: "xxx"
  api_secret: "xxx"
  rate_limit: 1200
  timeframes: ["1m", "5m", "15m", "1h", "4h", "1d"]
  symbols: ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

bybit:
  api_key: "xxx"
  api_secret: "xxx"
  rate_limit: 120
  timeframes: ["1", "5", "15", "60", "240", "D"]
```

### **Por Símbolo**
```yaml
BTCUSDT:
  rsi_period: 14
  overbought_level: 70
  oversold_level: 30
  position_size: 0.1  # 10% do capital
  max_loss_per_trade: 0.02  # 2%
```

---

## Considerações Técnicas

### **Performance**
- **Cache Redis**: Para dados de mercado e cálculos
- **Queue System**: Para processamento assíncrono (Celery + Redis)
- **Database Indexing**: Índices otimizados para consultas time-series

### **Confiabilidade**
- **Health Checks**: Monitoramento de todas as APIs
- **Circuit Breakers**: Proteção contra falhas
- **Retry Logic**: Reintentar operações falhadas
- **Logging**: Logs detalhados para debugging

### **Escalabilidade**
- **Microservices**: Separação de responsabilidades
- **Load Balancing**: Distribuição de carga
- **Horizontal Scaling**: Múltiplas instâncias

---

## Cronograma Sugerido

### **Fase 1 (2-3 semanas)**
- Estrutura base do projeto
- Implementação de 2-3 exchanges
- Cálculo de RSI
- Sistema básico de notificações (Discord)

### **Fase 2 (2-3 semanas)**
- Sistema de sinais avançado
- Gestão de portfólio
- Controle de risco básico
- Testes e otimizações

### **Fase 3 (2-4 semanas)**
- Execução automática de trades
- Sistema de notificações completo
- Dashboard de monitoramento
- Documentação e deploy

---

## Tecnologias Recomendadas

### **Backend**
- **Python 3.11+**: Linguagem principal
- **FastAPI**: API REST (se necessário)
- **SQLAlchemy**: ORM para PostgreSQL
- **Celery**: Processamento assíncrono
- **Redis**: Cache e message broker

### **Dados**
- **PostgreSQL**: Banco principal
- **Redis**: Cache e filas
- **Pandas**: Manipulação de dados
- **NumPy**: Cálculos numéricos

### **Monitoramento**
- **Prometheus**: Métricas
- **Grafana**: Dashboards
- **Sentry**: Logs de erro
- **Docker**: Containerização

---

## Próximos Passos

1. **Definir exchanges prioritárias** (sugiro: Binance, Bybit, Gate.io)
2. **Escolher plataforma de mensagem** (recomendo Discord)
3. **Configurar ambiente de desenvolvimento**
4. **Criar estrutura base do projeto**
5. **Implementar primeiro adapter de exchange**

---

## Riscos e Mitigações

### **Riscos Técnicos**
- **API Rate Limits**: Implementar rate limiting e fallbacks
- **Falhas de Conectividade**: Circuit breakers e retry logic
- **Perda de Dados**: Backup regular e replicação

### **Riscos de Trading**
- **Perdas Financeiras**: Controle rigoroso de risco
- **Execução Incorreta**: Validação múltipla de ordens
- **Slippage**: Uso de ordens limite quando possível

### **Riscos Operacionais**
- **Downtime**: Monitoramento 24/7
- **Segurança**: Criptografia e autenticação robusta
- **Compliance**: Conformidade com regulamentações

---

*Documento criado em: Janeiro 2025*
*Versão: 1.0* 