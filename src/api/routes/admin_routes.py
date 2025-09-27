"""
Rotas administrativas do sistema
"""

from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.api.schemas.admin import (
    SystemStatusResponse,
    UserConfigCreate,
    UserConfigResponse,
    UserConfigUpdate,
)
from src.database.connection import get_db
from src.database.models import SignalHistory, UserMonitoringConfig
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


# ==========================================
# SYSTEM STATUS ENDPOINT
# ==========================================


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(db: Session = Depends(get_db)):
    """Obter status geral do sistema"""
    try:
        # Contar configurações
        total_configs = db.query(UserMonitoringConfig).count()
        active_configs = (
            db.query(UserMonitoringConfig)
            .filter(UserMonitoringConfig.active == True)  # noqa: E712
            .count()  # noqa: E712
        )

        # Contar sinais das últimas 24h
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        recent_signals = (
            db.query(SignalHistory)
            .filter(SignalHistory.created_at >= yesterday)
            .count()
        )

        # Contar usuários únicos ativos
        unique_users = (
            db.query(UserMonitoringConfig.user_id)
            .filter(UserMonitoringConfig.active == True)  # noqa: E712
            .distinct()
            .count()
        )

        # TODO: Verificar status do Celery
        celery_workers_active = True  # Placeholder

        return SystemStatusResponse(
            monitoring_configs=total_configs,
            active_configs=active_configs,
            unique_active_users=unique_users,
            last_signal_count_24h=recent_signals,
            celery_workers_active=celery_workers_active,
        )

    except Exception as e:
        logger.error(f"❌ Erro ao obter status do sistema: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# USER MONITORING CONFIG ENDPOINTS
# ==========================================


@router.get("/users", response_model=List[UserConfigResponse])
async def get_all_users(
    active_only: bool = Query(False, description="Filtrar apenas usuários ativos"),
    limit: int = Query(50, ge=1, le=200, description="Limite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    db: Session = Depends(get_db),
):
    """Listar todos os usuários e suas configurações"""
    try:
        query = db.query(UserMonitoringConfig)

        if active_only:
            query = query.filter(UserMonitoringConfig.active == True)  # noqa: E712

        configs = (
            query.order_by(desc(UserMonitoringConfig.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

        return configs

    except Exception as e:
        logger.error(f"❌ Erro ao listar usuários: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}", response_model=List[UserConfigResponse])
async def get_user_configs(
    user_id: int,
    db: Session = Depends(get_db),
):
    """Obter todas as configurações de um usuário específico"""
    try:
        configs = (
            db.query(UserMonitoringConfig)
            .filter(UserMonitoringConfig.user_id == user_id)
            .order_by(desc(UserMonitoringConfig.created_at))
            .all()
        )

        if not configs:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        return configs

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao obter configurações do usuário {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/search/{username}", response_model=List[UserConfigResponse])
async def search_user_by_username(
    username: str,
    db: Session = Depends(get_db),
):
    """Buscar usuário por username do Telegram"""
    try:
        configs = (
            db.query(UserMonitoringConfig)
            .filter(UserMonitoringConfig.user_username.ilike(f"%{username}%"))
            .order_by(desc(UserMonitoringConfig.created_at))
            .all()
        )

        if not configs:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        return configs

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao buscar usuário por username {username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/{user_id}/configs", response_model=UserConfigResponse)
async def create_user_config(
    user_id: int,
    config_data: UserConfigCreate,
    db: Session = Depends(get_db),
):
    """Criar nova configuração para um usuário"""
    try:
        # Verificar se já existe configuração com esse nome para o usuário
        existing = (
            db.query(UserMonitoringConfig)
            .filter(
                UserMonitoringConfig.user_id == user_id,
                UserMonitoringConfig.config_name == config_data.config_name,
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Configuração '{config_data.config_name}' já existe para este usuário",
            )

        # Criar nova configuração
        new_config = UserMonitoringConfig(
            user_id=user_id,
            user_username=config_data.user_username,
            config_name=config_data.config_name,
            config_type=config_data.config_type,
            symbols=config_data.symbols,
            timeframes=config_data.timeframes,
            indicators_config=config_data.indicators_config,
            filter_config=config_data.filter_config,
            priority=config_data.priority,
            active=config_data.active,
        )

        db.add(new_config)
        db.commit()
        db.refresh(new_config)

        logger.info(
            f"Nova configuração criada para usuário {user_id}: {config_data.config_name}"
        )
        return new_config

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro ao criar configuração para usuário {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/users/configs/{config_id}", response_model=UserConfigResponse)
async def update_user_config(
    config_id: int,
    config_data: UserConfigUpdate,
    db: Session = Depends(get_db),
):
    """Atualizar configuração existente"""
    try:
        config = (
            db.query(UserMonitoringConfig)
            .filter(UserMonitoringConfig.id == config_id)
            .first()
        )

        if not config:
            raise HTTPException(status_code=404, detail="Configuração não encontrada")

        # Atualizar campos fornecidos
        for field, value in config_data.dict(exclude_unset=True).items():
            setattr(config, field, value)

        config.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(config)

        logger.info(f"Configuração {config_id} atualizada")
        return config

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro ao atualizar configuração {config_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users/configs/{config_id}")
async def delete_user_config(
    config_id: int,
    db: Session = Depends(get_db),
):
    """Deletar configuração específica"""
    try:
        config = (
            db.query(UserMonitoringConfig)
            .filter(UserMonitoringConfig.id == config_id)
            .first()
        )

        if not config:
            raise HTTPException(status_code=404, detail="Configuração não encontrada")

        user_id = config.user_id
        config_name = config.config_name

        db.delete(config)
        db.commit()

        logger.info(
            f"✅ Configuração {config_id} deletada (usuário {user_id}, config: {config_name})"
        )
        return {"message": "Configuração deletada com sucesso", "config_id": config_id}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro ao deletar configuração {config_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/configs/{config_id}/toggle")
async def toggle_config_status(
    config_id: int,
    db: Session = Depends(get_db),
):
    """Alternar status ativo/inativo de uma configuração"""
    try:
        config = (
            db.query(UserMonitoringConfig)
            .filter(UserMonitoringConfig.id == config_id)
            .first()
        )

        if not config:
            raise HTTPException(status_code=404, detail="Configuração não encontrada")

        # Alternar status
        config.active = not config.active
        config.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(config)

        status = "ativada" if config.active else "desativada"
        logger.info(f"Configuração {config_id} {status}")

        return {
            "message": f"Configuração {status} com sucesso",
            "config_id": config_id,
            "active": config.active,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro ao alterar status da configuração {config_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/symbols")
async def get_symbols_usage_stats(db: Session = Depends(get_db)):
    """Estatísticas de uso de símbolos nas configurações ativas"""
    try:
        # Buscar todas as configurações ativas
        active_configs = (
            db.query(UserMonitoringConfig)
            .filter(UserMonitoringConfig.active == True)  # noqa: E712
            .all()
        )

        symbol_count = {}
        total_configs = len(active_configs)

        for config in active_configs:
            if config.symbols:
                for symbol in config.symbols:
                    symbol_count[symbol] = symbol_count.get(symbol, 0) + 1

        # Ordenar por popularidade
        sorted_symbols = sorted(symbol_count.items(), key=lambda x: x[1], reverse=True)

        return {
            "total_active_configs": total_configs,
            "unique_symbols": len(symbol_count),
            "symbol_usage": [
                {
                    "symbol": symbol,
                    "count": count,
                    "percentage": round((count / total_configs) * 100, 1),
                }
                for symbol, count in sorted_symbols[:20]  # Top 20
            ],
        }

    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas de símbolos: {e}")
        raise HTTPException(status_code=500, detail=str(e))
