"""
Endpoints para operações com RSI
"""

from typing import List
from fastapi import APIRouter, HTTPException, Query

from src.api.schemas.rsi import (
    RSIResponse,
    SignalResponse,
    MultipleRSIResponse,
    HealthResponse,
)
from src.core.services.rsi_service import RSIService
from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/rsi", tags=["RSI"])


@router.get("/single/{symbol}", response_model=RSIResponse)
async def get_rsi(
    symbol: str,
    timespan: str = Query("day", description="Timeframe: minute, hour, day"),
    window: int = Query(14, description="RSI calculation window"),
):
    """
    Busca RSI para uma criptomoeda específica

    Exemplos de símbolos: BTCUSD, ETHUSD, SOLUSD
    """
    try:
        rsi_service = RSIService(settings.polygon_api_key)
        rsi_data = await rsi_service.get_rsi_from_polygon(symbol, timespan, window)

        if not rsi_data:
            raise HTTPException(
                status_code=404, detail=f"RSI não encontrado para {symbol}"
            )

        return RSIResponse(
            symbol=rsi_data.symbol,
            rsi_value=float(rsi_data.value),
            timestamp=rsi_data.timestamp.isoformat(),
            timespan=rsi_data.timespan,
            window=rsi_data.window,
            source=rsi_data.source,
        )

    except Exception as e:
        logger.error(f"Erro ao buscar RSI para {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/multiple", response_model=MultipleRSIResponse)
async def get_multiple_rsi(
    symbols: str = Query(
        ..., description="Símbolos separados por vírgula (ex: BTCUSD,ETHUSD)"
    ),
    timespan: str = Query("day", description="Timeframe: minute, hour, day"),
    window: int = Query(14, description="RSI calculation window"),
):
    """
    Busca RSI para múltiplas criptomoedas

    Exemplo: /rsi/multiple?symbols=BTCUSD,ETHUSD,SOLUSD
    """
    try:
        # Processar símbolos
        symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]

        if not symbol_list:
            raise HTTPException(
                status_code=400, detail="Pelo menos um símbolo deve ser fornecido"
            )

        if len(symbol_list) > 10:
            raise HTTPException(
                status_code=400, detail="Máximo 10 símbolos por consulta"
            )

        rsi_service = RSIService(settings.polygon_api_key)
        rsi_results = await rsi_service.get_multiple_rsi(symbol_list, timespan, window)

        # Processar resultados
        results = {}
        successful_count = 0

        for symbol, rsi_data in rsi_results.items():
            if rsi_data:
                results[symbol] = RSIResponse(
                    symbol=rsi_data.symbol,
                    rsi_value=float(rsi_data.value),
                    timestamp=rsi_data.timestamp.isoformat(),
                    timespan=rsi_data.timespan,
                    window=rsi_data.window,
                    source=rsi_data.source,
                )
                successful_count += 1
            else:
                results[symbol] = None

        return MultipleRSIResponse(
            results=results,
            successful_count=successful_count,
            total_count=len(symbol_list),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar RSI múltiplo: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/signals", response_model=List[SignalResponse])
async def get_trading_signals(
    symbols: str = Query(
        "BTCUSD,ETHUSD,SOLUSD,ADAUSD", description="Símbolos separados por vírgula"
    ),
    timespan: str = Query("day", description="Timeframe: minute, hour, day"),
    window: int = Query(14, description="RSI calculation window"),
):
    """
    Gera sinais de trading baseados em RSI para múltiplas cryptos

    Retorna lista ordenada por força do sinal (mais forte primeiro)
    """
    try:
        # Processar símbolos
        symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]

        if not symbol_list:
            # Usar símbolos padrão se nenhum fornecido
            symbol_list = settings.default_symbols

        if len(symbol_list) > 20:
            raise HTTPException(
                status_code=400, detail="Máximo 20 símbolos para análise de sinais"
            )

        rsi_service = RSIService(settings.polygon_api_key)
        analyses = await rsi_service.get_trading_signals(symbol_list, timespan, window)

        # Converter para response model
        signals = []
        for analysis in analyses:
            signal_response = SignalResponse(
                symbol=analysis.signal.symbol,
                signal_type=analysis.signal.signal_type.value,
                strength=analysis.signal.strength.value,
                rsi_value=float(analysis.signal.rsi_value),
                timestamp=analysis.signal.timestamp.isoformat(),
                timeframe=analysis.signal.timeframe,
                message=analysis.signal.message,
                interpretation=analysis.interpretation,
                risk_level=analysis.risk_level,
            )
            signals.append(signal_response)

        return signals

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar sinais de trading: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Verifica se a integração com Polygon.io está funcionando"""
    try:
        rsi_service = RSIService(settings.polygon_api_key)
        # Testar com Bitcoin
        rsi_data = await rsi_service.get_rsi_from_polygon("BTCUSD", "day", 14)

        return HealthResponse(
            status="healthy" if rsi_data else "degraded",
            polygon_api="connected" if rsi_data else "error",
            message="RSI service operational"
            if rsi_data
            else "Unable to fetch RSI data",
        )

    except Exception as e:
        logger.error(f"Health check falhou: {e}")
        return HealthResponse(status="unhealthy", polygon_api="error", message=str(e))
