# 🤖 Comandos do Telegram - BullBot Signals

## 📋 **Comandos de Configuração Básica**

### `/start`
Inicia o bot e cria configuração padrão para o usuário.

### `/settings`
Exibe a configuração atual do usuário:
```
⚙️ Suas Configurações:
📊 Config: crypto_principais
🪙 Símbolos: BTC, ETH, SOL (5 total)
⏰ Timeframes: 15m, 1h
📈 RSI: 25-75 (sobrevenda-sobrecompra)
🛡️ Filtros: cooldown=120min, max_signals=3/dia
✅ Status: Ativo
```

### `/config create <nome>`
Cria nova configuração personalizada:
```
/config create trading_btc
✅ Configuração "trading_btc" criada!
```

### `/config list`
Lista todas as configurações do usuário:
```
📋 Suas Configurações:
1. crypto_principais (ativa)
2. trading_btc (inativa)
3. scalping_15m (ativa)
```

### `/config activate <nome>`
Ativa uma configuração específica:
```
/config activate trading_btc
✅ Configuração "trading_btc" ativada!
```

## 🪙 **Comandos de Símbolos**

### `/symbols <lista>`
Define símbolos para monitorar:
```
/symbols BTC,ETH,SOL,ADA,DOT
✅ 5 símbolos configurados: BTC, ETH, SOL, ADA, DOT
```

### `/symbols add <lista>`
Adiciona símbolos à configuração atual:
```
/symbols add AVAX,LINK
✅ Símbolos adicionados: AVAX, LINK
📊 Total: 7 símbolos
```

### `/symbols remove <lista>`
Remove símbolos da configuração:
```
/symbols remove ADA,DOT
✅ Símbolos removidos: ADA, DOT
📊 Total: 5 símbolos
```

### `/symbols clear`
Remove todos os símbolos:
```
⚠️ Todos os símbolos removidos!
💡 Use /symbols <lista> para adicionar novos
```

## ⏰ **Comandos de Timeframes**

### `/timeframes <lista>`
Define timeframes para análise:
```
/timeframes 15m,1h,4h
✅ Timeframes configurados: 15m, 1h, 4h
```

### `/timeframes add <lista>`
Adiciona timeframes:
```
/timeframes add 1d
✅ Timeframe adicionado: 1d
📊 Total: 15m, 1h, 4h, 1d
```

## 📈 **Comandos de RSI**

### `/rsi <oversold>,<overbought>`
Define níveis de RSI:
```
/rsi 25,75
✅ RSI configurado:
📉 Sobrevenda: ≤ 25 (sinais de compra)
📈 Sobrecompra: ≥ 75 (sinais de venda)
```

### `/rsi_period <periodo>`
Define período do RSI (padrão: 14):
```
/rsi_period 21
✅ Período RSI alterado para 21
```

## 🛡️ **Comandos de Filtros Anti-Spam**

### `/cooldown <minutos>`
Define cooldown global em minutos:
```
/cooldown 120
✅ Cooldown configurado: 2 horas
🔄 Aplicado a todos os timeframes e forças de sinal
```

### `/cooldown_advanced`
Configura cooldown detalhado por timeframe e força:
```
/cooldown_advanced
📝 Configure cooldown por timeframe:

15m - Quantos minutos entre sinais?
STRONG: 15min | MODERATE: 30min | WEAK: 60min

1h - Quantos minutos entre sinais?  
STRONG: 60min | MODERATE: 120min | WEAK: 240min

4h - Quantos minutos entre sinais?
STRONG: 120min | MODERATE: 240min | WEAK: 360min

✅ Use /cooldown_save para confirmar
```

### `/max_signals <numero>`
Define máximo de sinais por símbolo por dia:
```
/max_signals 3
✅ Máximo configurado: 3 sinais/símbolo/dia
🛡️ Sinais STRONG limitados à metade: 1/dia
```

### `/min_rsi_diff <valor>`
Define diferença mínima de RSI para novos sinais:
```
/min_rsi_diff 2.0
✅ Diferença mínima RSI: 2.0 pontos
📊 Evita sinais repetitivos com RSI similar
```

### `/filters_reset`
Reseta filtros para configuração padrão:
```
⚠️ Filtros resetados para padrão:
🔄 Cooldown: 2h (moderate)
📊 Max sinais: 3/dia
📈 Diferença RSI: 2.0
```

## 📊 **Comandos de Monitoramento**

### `/stats`
Exibe estatísticas de sinais do dia:
```
📊 Estatísticas de Hoje:
🎯 Sinais enviados: 8
💪 Sinais STRONG: 3
📈 Taxa de acerto: 75%
⏰ Último sinal: BTC há 15min
```

### `/stats <simbolo>`
Estatísticas de um símbolo específico:
```
/stats BTC
📊 BTC - Estatísticas de Hoje:
🎯 Sinais enviados: 2/3
💪 Sinais STRONG: 1/1
⏰ Último sinal: há 45min (STRONG BUY)
🔄 Próximo sinal: em 75min
```

### `/cooldowns`
Status de cooldown dos símbolos:
```
🔄 Status de Cooldown:
✅ BTC: livre
⏰ ETH: 25min restantes
⏰ SOL: 1h 15min restantes
✅ ADA: livre
```

### `/test_filters <simbolo>`
Testa filtros para um símbolo específico:
```
/test_filters BTCUSDT
🧪 Teste de Filtros - BTCUSDT:
✅ Cooldown: OK (livre)
✅ Limites diários: 1/3 sinais usados
✅ RSI último: 28.5 (aceitável)
🎯 Próximo sinal será aceito!
```

## 🔧 **Comandos Avançados**

### `/priority <numero>`
Define prioridade da configuração (1-10):
```
/priority 5
✅ Prioridade definida: 5
📊 Configurações com maior prioridade são preferidas
```

### `/export`
Exporta configuração atual:
```
📤 Sua configuração:
{
  "symbols": ["BTC", "ETH", "SOL"],
  "timeframes": ["15m", "1h"],
  "rsi": {"oversold": 25, "overbought": 75},
  "filters": {"cooldown_minutes": 120, "max_signals_per_day": 3}
}
```

### `/import <json>`
Importa configuração a partir de JSON:
```
/import {"symbols": ["BTC"], "timeframes": ["1h"]}
✅ Configuração importada com sucesso!
```

### `/help <comando>`
Ajuda detalhada sobre comandos:
```
/help cooldown
🛡️ Comando: /cooldown

Define tempo mínimo entre sinais do mesmo símbolo.
Uso: /cooldown <minutos>
Exemplo: /cooldown 120 (2 horas)

🔄 Tipos de cooldown:
- Global: mesmo tempo para tudo
- Avançado: por timeframe e força (/cooldown_advanced)
```

## 🚨 **Comandos de Emergência**

### `/pause`
Pausa temporariamente os sinais:
```
⏸️ Sinais pausados!
💡 Use /resume para reativar
```

### `/resume`
Retoma o envio de sinais:
```
▶️ Sinais reativados!
🎯 Monitoramento ativo para 5 símbolos
```

### `/reset_all`
Reseta completamente a configuração:
```
⚠️ ATENÇÃO: Isso apagará TODA sua configuração!
Digite "CONFIRMAR" para prosseguir ou "CANCELAR"
```

---

## 📝 **Exemplos de Uso Completo**

### **Setup Inicial Rápido:**
```
/start
/symbols BTC,ETH,SOL
/timeframes 15m,1h
/rsi 25,75
/cooldown 120
/max_signals 3
```

### **Configuração Avançada de Scalping:**
```
/config create scalping_15m
/symbols BTC,ETH,SOL,ADA,AVAX
/timeframes 15m
/rsi 20,80
/cooldown_advanced
/max_signals 5
/min_rsi_diff 1.5
```

### **Monitoramento de Longo Prazo:**
```
/config create hodl_signals  
/symbols BTC,ETH
/timeframes 4h,1d
/rsi 30,70
/cooldown 360
/max_signals 1
```

**🎯 Sistema 100% personalizável para cada usuário!**