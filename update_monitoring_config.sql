-- Script para atualizar configuração de monitoramento com todas as moedas solicitadas
-- e criar indicadores sensíveis para facilitar testes

-- 1. Atualizar a configuração existente com as moedas
UPDATE user_monitoring_configs
SET
    symbols = ARRAY[
        'BTC', 'ETH', 'XRP', 'SOL', 'ADA', 'XLM', 'LINK', 'HBAR', 'BCH', 'AVAX',
        'LTC', 'DOT', 'UNI', 'AAVE', 'NEAR', 'ETC', 'ALGO', 'ATOM', 'POL', 'ARB',
        'QNT', 'TIA', 'OP', 'IMX', 'GRT', 'LDO', 'XTZ', 'AERO', 'AGI', 'ANKR',
        'BLOCK', 'AI16Z', 'CELR', 'DAO', 'GHX', 'ASTR', 'ENJ', 'MUBI', 'ATH',
        'HOT', 'XRD', 'AXL', 'KSM', 'BLUR', 'MANTA', 'CHZ', 'PRCL', 'DRIFT',
        'RLB', 'DYDX', 'SAND', 'ENA', 'SFUND', 'ETHFI', 'SNX', 'GALA', 'SPEC',
        'JUP', 'TAI', 'LPT', 'PAAL', 'PRIME', 'RAY', 'RON', 'SCRT', 'UMA',
        'USUAL', 'FET', 'HNT', 'INJ', 'PENDLE', 'SEI', 'SUPER', 'VET', 'VIRTUAL',
        'RNDR', 'STX', 'SUI', 'TON', 'MATIC', 'MKR'
    ],
    timeframes = ARRAY['15m', '1h', '4h'],
    description = 'Monitoramento completo de todas as cryptos principais e altcoins em múltiplos timeframes',
    indicators_config = '{
        "RSI": {
            "enabled": true,
            "period": 14,
            "oversold": 50,
            "overbought": 50
        },
        "EMA": {
            "enabled": true,
            "fast_period": 9,
            "medium_period": 21,
            "slow_period": 50
        },
        "MACD": {
            "enabled": true,
            "fast_period": 12,
            "slow_period": 26,
            "signal_period": 9
        },
        "Volume": {
            "enabled": true,
            "sma_period": 20,
            "volume_threshold": 0.3
        },
        "Confluence": {
            "enabled": true,
            "min_score_15m": 1,
            "min_score_1h": 1,
            "min_score_4h": 1,
            "min_score_1d": 1
        }
    }'::jsonb,
    filter_config = '{
        "cooldown_minutes": 5,
        "min_confluence_score": 1,
        "max_signals_per_day": 100,
        "min_rsi_difference": 0.1
    }'::jsonb,
    active = true,
    updated_at = NOW()
WHERE id = 1;

-- 2. Criar uma segunda configuração ultra-sensível apenas para BTC e ETH
INSERT INTO user_monitoring_configs (
    user_id,
    chat_id,
    chat_type,
    username,
    user_username,
    config_type,
    priority,
    config_name,
    description,
    symbols,
    timeframes,
    indicators_config,
    filter_config,
    active
) VALUES (
    123456,
    '123457',  -- Chat ID diferente
    'private',
    'crypto_trader',
    'crypto_trader',
    'personal',
    2,
    'btc_eth_ultra_sensitive',
    'Configuração ULTRA SENSÍVEL para BTC e ETH - captura qualquer movimento',
    ARRAY['BTC', 'ETH'],
    ARRAY['15m', '1h'],
    '{
        "RSI": {
            "enabled": true,
            "period": 14,
            "oversold": 60,
            "overbought": 40
        },
        "EMA": {
            "enabled": true,
            "fast_period": 9,
            "medium_period": 21,
            "slow_period": 50
        },
        "MACD": {
            "enabled": true,
            "fast_period": 12,
            "slow_period": 26,
            "signal_period": 9
        },
        "Volume": {
            "enabled": true,
            "sma_period": 20,
            "volume_threshold": 0.1
        },
        "Confluence": {
            "enabled": true,
            "min_score_15m": 0,
            "min_score_1h": 0,
            "min_score_4h": 0,
            "min_score_1d": 0
        }
    }'::jsonb,
    '{
        "cooldown_minutes": 2,
        "min_confluence_score": 0,
        "max_signals_per_day": 200,
        "min_rsi_difference": 0.01
    }'::jsonb,
    true
) ON CONFLICT (chat_id) DO UPDATE SET
    symbols = EXCLUDED.symbols,
    timeframes = EXCLUDED.timeframes,
    indicators_config = EXCLUDED.indicators_config,
    filter_config = EXCLUDED.filter_config,
    description = EXCLUDED.description,
    updated_at = NOW();

-- Verificar as configurações atualizadas
SELECT
    id,
    config_name,
    description,
    array_length(symbols, 1) as total_symbols,
    timeframes,
    indicators_config->'RSI' as rsi_config,
    indicators_config->'Confluence' as confluence_config,
    filter_config->'cooldown_minutes' as cooldown,
    filter_config->'min_confluence_score' as min_score,
    active
FROM user_monitoring_configs
ORDER BY id;
