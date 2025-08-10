# 🎯 API Simplificada - Foco em Sinais

## 🧹 **Mudanças Realizadas**

### ❌ **Removido (Over-engineering)**
- ❌ CRUD de configurações de monitoramento (`/monitoring/configs`)
- ❌ Schemas complexos de configuração
- ❌ Gerenciamento via API REST
- ❌ Múltiplos schemas desnecessários

### ✅ **Mantido (Essencial)**
- ✅ Buscar sinais não processados
- ✅ Marcar sinais como processados  
- ✅ Status do sistema
- ✅ Histórico recente para debug

## 🌐 **APIs Disponíveis**

### **1. Buscar Sinais Não Processados**
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
    "message": "🚀 Sobrevenda forte detectada. RSI em 18.5.",
    "indicator_type": ["RSI"],
    "indicator_data": {
      "RSI": {
        "value": 18.5,
        "oversold": true,
        "period": 14
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

### **2. Marcar Sinal como Processado**
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

### **3. Status do Sistema**
```bash
GET /api/v1/admin/status
```

**Resposta:**
```json
{
  "monitoring_configs": 1,
  "active_configs": 1,
  "last_signal_count_24h": 15,
  "unprocessed_signals": 3,
  "celery_workers_active": true
}
```

### **4. Histórico Recente (Debug)**
```bash
GET /api/v1/admin/signals/recent?limit=10
```

### **5. Sinais das Últimas X Horas (Debug)**
```bash
GET /api/v1/admin/signals/last?limit=50&hours=24
```

## 🤖 **Exemplo de Uso pelo Bot do Telegram**

```python
import asyncio
import httpx
from datetime import datetime

class TelegramSignalBot:
    def __init__(self):
        self.api_base = "http://bullbot-signals:8000/api/v1/admin"
        self.bot_id = "telegram-bot"
    
    async def run(self):
        """Loop principal simplificado"""
        while True:
            try:
                # 1. Buscar sinais pendentes
                signals = await self.get_unprocessed_signals()
                
                if not signals:
                    await asyncio.sleep(30)  # Aguardar se não há sinais
                    continue
                
                print(f"📥 {len(signals)} sinais pendentes")
                
                # 2. Processar cada sinal
                for signal in signals:
                    try:
                        # Filtrar usuários que devem receber
                        eligible_users = await self.filter_users(signal)
                        
                        if eligible_users:
                            # Enviar para usuários elegíveis
                            await self.send_to_users(signal, eligible_users)
                            print(f"✅ Sinal {signal['id']} enviado para {len(eligible_users)} usuários")
                        
                        # Marcar como processado
                        await self.mark_processed(signal["id"])
                        
                    except Exception as e:
                        print(f"❌ Erro no sinal {signal['id']}: {e}")
                
                await asyncio.sleep(5)  # Pausa pequena entre ciclos
                
            except Exception as e:
                print(f"❌ Erro no loop: {e}")
                await asyncio.sleep(60)
    
    async def get_unprocessed_signals(self):
        """Buscar sinais não processados"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_base}/signals/unprocessed?limit=50")
            return response.json() if response.status_code == 200 else []
    
    async def mark_processed(self, signal_id: int):
        """Marcar sinal como processado"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/signals/{signal_id}/mark-processed",
                params={"processed_by": self.bot_id}
            )
            return response.status_code == 200
    
    async def filter_users(self, signal):
        """Filtrar usuários baseado em suas configurações"""
        # Implementar lógica de filtro baseada no banco do Telegram
        # Ex: verificar símbolos de interesse, força mínima, etc.
        return await self.get_interested_users(signal)
    
    async def send_to_users(self, signal, users):
        """Enviar sinal para usuários via Telegram"""
        # Implementar envio via bot do Telegram
        pass
    
    async def get_interested_users(self, signal):
        """Buscar usuários interessados no sinal"""
        # Consultar banco do Telegram para usuários que:
        # - Têm o símbolo na lista de interesse
        # - Aceitam sinais deste timeframe  
        # - Têm força mínima compatível
        pass

# Executar bot
if __name__ == "__main__":
    bot = TelegramSignalBot()
    asyncio.run(bot.run())
```

## 🎯 **Vantagens da Simplificação**

### ✅ **Foco Total**
- API 100% focada em consumo de sinais
- Sem complexidade desnecessária
- Zero configuração via API

### ✅ **Arquitetura Limpa** 
- **BullBot Signals**: Detecta e armazena sinais
- **Telegram Bot**: Consome e distribui sinais
- **Separação clara** de responsabilidades

### ✅ **Performance**
- APIs leves e rápidas
- Menos overhead desnecessário
- Foco no essencial

### ✅ **Manutenibilidade**
- Código mais simples
- Menos pontos de falha
- Fácil de debugar

## 📊 **Monitoramento**

### **Verificar Status:**
```bash
curl http://localhost:8000/api/v1/admin/status
```

### **Verificar Sinais Pendentes:**
```bash
curl http://localhost:8000/api/v1/admin/signals/unprocessed?limit=1
```

### **Debug de Sinais Recentes:**
```bash
curl http://localhost:8000/api/v1/admin/signals/recent?limit=5
```

### **Debug de Sinais das Últimas Horas:**
```bash
curl http://localhost:8000/api/v1/admin/signals/last?limit=20&hours=6
```

**Resultado: API enxuta, focada e eficiente! 🚀**
