"""
API principal do BullBot Signals
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import rsi_routes
from src.database.connection import create_tables
from src.utils.logger import get_logger
from src.api.routes.admin_routes import router as admin_router
from src.api.routes.debug_routes import router as debug_router

logger = get_logger(__name__)


# Criar aplicação FastAPI
app = FastAPI(
    title="BullBot Signals API",
    description="API para análise de RSI em criptomoedas usando múltiplas exchanges",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(rsi_routes.router)
app.include_router(admin_router)
app.include_router(debug_router)


@app.on_event("startup")
def startup_event():
    """Initialize database tables on startup."""
    try:
        create_tables()
    except Exception as e:
        logger.error(f"❌ Erro ao criar tabelas: {e}")
        raise


@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "message": "🤖 BullBot Signals API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/rsi/health",
        "admin": "/admin/status",
        "debug": "/debug/system-health",
    }
