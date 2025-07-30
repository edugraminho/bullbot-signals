"""
API principal do Crypto Hunter
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.api import routes
from src.api.schemas.common import StatusResponse
from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação"""
    # Startup
    logger.info("🚀 Crypto Hunter API iniciando...")
    logger.info(f"Configurações: Debug={settings.debug}")

    yield

    # Shutdown
    logger.info("📋 Crypto Hunter API finalizando...")


# Criar aplicação FastAPI
app = FastAPI(
    title="Crypto Hunter API",
    description="API para análise de RSI em criptomoedas usando Polygon.io",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(routes.router)


@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "message": "🤖 Crypto Hunter API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/rsi/health",
    }


@app.get("/health", response_model=StatusResponse)
async def health():
    """Health check geral"""
    return StatusResponse(
        status="healthy", service="crypto-hunter-api", version="1.0.0"
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info",
    )
