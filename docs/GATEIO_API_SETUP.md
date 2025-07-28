# Configuração da API Gate.io

Este documento explica como configurar e conectar com a API do Gate.io para o Crypto Hunter.

## 1. Obter Credenciais da API

### Passo 1: Criar Conta na Gate.io
1. Acesse [Gate.io](https://www.gate.io)
2. Crie uma conta ou faça login
3. Complete a verificação de identidade (KYC) se necessário

### Passo 2: Gerar Chaves da API
1. Acesse: https://www.gate.com/docs/developers/apiv4/en/#generate-api-key
2. Faça login na sua conta Gate.io
3. Vá para **API Management** no painel de controle
4. Clique em **Create API Key**
5. Configure as permissões:
   - **Read**: Para leitura de dados de mercado
   - **Trade**: Para operações de trading (opcional)
   - **Withdraw**: Para saques (opcional - use com cuidado)

### Passo 3: Configurar Permissões
Para o Crypto Hunter, você precisa das seguintes permissões:
- ✅ **Read**: Para buscar dados de mercado, OHLCV, tickers
- ❌ **Trade**: Não necessário para coleta de dados
- ❌ **Withdraw**: Não necessário

## 2. Configuração no Projeto

### Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```bash
# Configurações da API Gate.io
GATEIO_API_KEY=sua_api_key_aqui
GATEIO_API_SECRET=sua_api_secret_aqui

# Configurações de Rate Limit
EXCHANGE_RATE_LIMIT=100

# Configurações de Coleta de Dados
COLLECTION_INTERVAL=60
MAX_DATA_POINTS=1000
MIN_VOLUME_24H=1000000
MAX_SYMBOLS_PER_EXCHANGE=100

# Configurações do RSI
RSI_PERIODS=14,21,50
OVERBOUGHT_LEVEL=70.0
OVERSOLD_LEVEL=30.0

# Configurações de Timeframes
TIMEFRAMES=1h,4h,1d

# Configurações de Notificação
NOTIFICATIONS_ENABLED=true
NOTIFICATION_PLATFORMS=discord,telegram
MIN_SIGNAL_STRENGTH=0.7
NOTIFICATION_CHECK_INTERVAL=300

# Configurações de Banco de Dados
DATABASE_URL=postgresql://crypto_user:crypto_password_2024@db:5432/crypto_hunter
REDIS_URL=redis://redis:6380/0
```

## 3. Testando a Conexão

### Script de Teste
Execute o script de teste para verificar se a conexão está funcionando:

```bash
python scripts/test_gateio_collection.py
```

### Verificação Manual
Você pode testar a conexão manualmente:

```python
from core.exchanges.gateio import GateIOAdapter
from config.config import config

# Configuração da exchange
exchange_config = config.exchanges["gateio"]

# Criar adapter
adapter = GateIOAdapter(exchange_config.__dict__)

# Testar conexão
import asyncio
result = asyncio.run(adapter.test_connection())
print(f"Conexão: {'OK' if result else 'FALHOU'}")
```

## 4. Endpoints da API Utilizados

O Crypto Hunter utiliza os seguintes endpoints da API Gate.io:

### Dados Públicos (não requerem API key)
- `GET /spot/currency_pairs` - Lista de pares de moedas
- `GET /spot/candlesticks` - Dados OHLCV
- `GET /spot/tickers` - Informações de ticker

### Dados Privados (requerem API key)
- `GET /spot/accounts` - Saldo da conta (se necessário)
- `GET /spot/orders` - Histórico de ordens (se necessário)

## 5. Rate Limits

A Gate.io possui os seguintes limites de taxa:

- **Público**: 100 requests por 10 segundos
- **Privado**: 300 requests por 10 segundos

O Crypto Hunter implementa controle automático de rate limiting.

## 6. Símbolos Suportados

Por padrão, o sistema monitora os seguintes símbolos:
- `BTC_USDT`
- `ETH_USDT`
- `SOL_USDT`
- `ADA_USDT`
- `DOT_USDT`

Você pode modificar a lista em `config/config.py`.

## 7. Troubleshooting

### Erro: "Invalid API key"
- Verifique se as credenciais estão corretas
- Certifique-se de que a API key está ativa
- Verifique se as permissões estão configuradas corretamente

### Erro: "Rate limit exceeded"
- O sistema implementa controle automático
- Aguarde alguns segundos e tente novamente
- Considere aumentar o intervalo de coleta

### Erro: "Connection timeout"
- Verifique sua conexão com a internet
- A Gate.io pode estar temporariamente indisponível
- Tente novamente em alguns minutos

## 8. Segurança

### Boas Práticas
1. **Nunca compartilhe suas credenciais**
2. **Use apenas permissões necessárias**
3. **Monitore o uso da API**
4. **Rotacione as chaves periodicamente**
5. **Use IP whitelist se disponível**

### Configuração de IP Whitelist
1. No painel da Gate.io, vá para API Management
2. Configure IP whitelist para seu servidor
3. Isso adiciona uma camada extra de segurança

## 9. Monitoramento

### Logs
O sistema gera logs detalhados em:
- `logs/crypto_hunter.log`
- Console (durante desenvolvimento)

### Métricas
- Número de requests por minuto
- Taxa de sucesso das requisições
- Tempo de resposta médio
- Erros de rate limiting

## 10. Suporte

Se você encontrar problemas:
1. Verifique os logs do sistema
2. Teste a conexão manualmente
3. Consulte a documentação oficial da Gate.io
4. Abra uma issue no repositório do projeto 