# 🤖 Integração com Bot do Telegram

## Fluxo de Controle de Sinais

O projeto do bot do Telegram irá consumir os sinais através das seguintes APIs:

### 📥 **1. Buscar Sinais Não Processados**

```bash
GET /api/v1/admin/signals/unprocessed?limit=50
```

**Resposta:**
```json
[
  {
    "id": 123,
    "symbol": "BTC",
    "signal_type": "BUY",
    "strength": "STRONG",
    "price": 67530.25,
    "timeframe": "1h",
    "source": "binance",
    "indicator_type": ["RSI"],
    "indicator_data": {
      "RSI": {
        "value": 18.5,
        "oversold": true
      }
    },
    "confidence_score": 85.0,
    "combined_score": 85.0,
    "processed": false,
    "processed_at": null,
    "processed_by": null,
    "created_at": "2025-01-31T15:30:00Z"
  }
]
```

### ✅ **2. Marcar Sinal como Processado**

```bash
POST /api/v1/admin/signals/123/mark-processed?processed_by=telegram-bot
```

**Resposta:**
```json
{
  "message": "Sinal marcado como processado",
  "signal_id": 123
}
```

## 🔄 **Fluxo Recomendado para o Bot**

### **Loop Principal:**

```python
import asyncio
import httpx
from datetime import datetime

class TelegramBotSignalProcessor:
    def __init__(self):
        self.api_base = "http://bullbot-signals:8000/api/v1"
        self.bot_id = "telegram-bot"
    
    async def process_signals_loop(self):
        """Loop principal para processar sinais"""
        while True:
            try:
                # 1. Buscar sinais não processados
                unprocessed_signals = await self.get_unprocessed_signals()
                
                if not unprocessed_signals:
                    await asyncio.sleep(30)  # Aguardar 30s se não há sinais
                    continue
                
                # 2. Processar cada sinal
                for signal in unprocessed_signals:
                    try:
                        # Aplicar filtros de usuário
                        eligible_users = await self.filter_users_for_signal(signal)
                        
                        # Enviar para usuários elegíveis
                        if eligible_users:
                            await self.send_signal_to_users(signal, eligible_users)
                        
                        # Marcar como processado
                        await self.mark_signal_processed(signal["id"])
                        
                    except Exception as e:
                        print(f"Erro ao processar sinal {signal['id']}: {e}")
                        # Opcional: marcar como processado mesmo com erro
                        # await self.mark_signal_processed(signal["id"])
                
                # Pequena pausa entre ciclos
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"Erro no loop principal: {e}")
                await asyncio.sleep(60)  # Aguardar 1min em caso de erro
    
    async def get_unprocessed_signals(self):
        """Buscar sinais não processados"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_base}/admin/signals/unprocessed?limit=50"
            )
            if response.status_code == 200:
                return response.json()
            return []
    
    async def mark_signal_processed(self, signal_id: int):
        """Marcar sinal como processado"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/admin/signals/{signal_id}/mark-processed",
                params={"processed_by": self.bot_id}
            )
            return response.status_code == 200
    
    async def filter_users_for_signal(self, signal):
        """Filtrar usuários que devem receber o sinal"""
        # Implementar lógica baseada nas configurações do usuário
        # Exemplo: verificar símbolos, timeframes, força mínima, etc.
        pass
    
    async def send_signal_to_users(self, signal, users):
        """Enviar sinal para lista de usuários"""
        # Implementar envio via Telegram
        pass
```

## 🎯 **Vantagens desta Abordagem**

### ✅ **Controle Preciso:**
- Evita sinais duplicados
- Rastreia quais sinais foram processados
- Permite reprocessamento se necessário

### ✅ **Escalabilidade:**
- Múltiplas instâncias do bot podem rodar
- Sinais são processados em ordem (FIFO)
- Sem conflitos entre instâncias

### ✅ **Auditoria:**
- Log completo de processamento
- Identificação de qual serviço processou
- Timestamp de processamento

### ✅ **Recuperação:**
- Sinais não processados ficam na fila
- Bot pode reprocessar após reinicialização
- Sem perda de sinais

## 📊 **Monitoramento**

### **Verificar Sinais Pendentes:**
```bash
GET /api/v1/admin/signals/unprocessed?limit=1
```

### **Estatísticas de Processamento:**
```bash
GET /api/v1/admin/status
```

### **Últimos Sinais Processados:**
```bash
GET /api/v1/admin/signals/recent?limit=10
```

## ⚙️ **Configuração Recomendada**

### **Frequência de Verificação:**
- **Normal**: 30 segundos quando não há sinais
- **Ativo**: 5 segundos quando há sinais pendentes
- **Erro**: 60 segundos em caso de falha

### **Limites:**
- **Batch size**: 50 sinais por consulta
- **Timeout**: 30 segundos por requisição
- **Retry**: 3 tentativas com backoff

### **Logs Importantes:**
```python
logger.info(f"📥 Processando {len(signals)} sinais pendentes")
logger.info(f"✅ Sinal {signal_id} enviado para {len(users)} usuários")
logger.info(f"🔄 Sinal {signal_id} marcado como processado")
```

Esta arquitetura garante que **nenhum sinal seja perdido** e **todos sejam processados exatamente uma vez**! 🎯
