"""
Rotas de administração para configuração do sistema
"""

from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from src.database.connection import get_db
from src.database.models import MonitoringConfig, TelegramSubscription, SignalHistory
from src.api.schemas.admin import (
    MonitoringConfigCreate,
    MonitoringConfigUpdate,
    MonitoringConfigResponse,
    TelegramSubscriptionCreate,
    TelegramSubscriptionUpdate,
    TelegramSubscriptionResponse,
    SystemStatusResponse,
)
from src.utils.logger import get_logger
from datetime import datetime, timedelta, timezone

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


# ==========================================
# MONITORING CONFIG ENDPOINTS
# ==========================================


@router.get("/monitoring/configs", response_model=List[MonitoringConfigResponse])
async def list_monitoring_configs(db: Session = Depends(get_db)):
    """Listar todas as configurações de monitoramento"""
    try:
        configs = db.query(MonitoringConfig).all()
        return configs
    except Exception as e:
        logger.error(f"❌ Erro ao listar configs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/configs", response_model=MonitoringConfigResponse)
async def create_monitoring_config(
    config: MonitoringConfigCreate, db: Session = Depends(get_db)
):
    """Criar nova configuração de monitoramento"""
    try:
        # Verificar se nome já existe
        existing = (
            db.query(MonitoringConfig)
            .filter(MonitoringConfig.name == config.name)
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Configuração com nome '{config.name}' já existe",
            )

        # Se ativa=True, desativar outras configurações
        if config.active:
            db.query(MonitoringConfig).update({"active": False})

        # Criar nova configuração
        db_config = MonitoringConfig(**config.dict())
        db.add(db_config)
        db.commit()
        db.refresh(db_config)

        logger.info(f"Config '{config.name}' criada com {len(config.symbols)} símbolos")
        return db_config

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro ao criar config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/configs/{config_id}", response_model=MonitoringConfigResponse)
async def get_monitoring_config(config_id: int, db: Session = Depends(get_db)):
    """Obter configuração específica"""
    config = db.query(MonitoringConfig).filter(MonitoringConfig.id == config_id).first()

    if not config:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")

    return config


@router.put("/monitoring/configs/{config_id}", response_model=MonitoringConfigResponse)
async def update_monitoring_config(
    config_id: int, config_update: MonitoringConfigUpdate, db: Session = Depends(get_db)
):
    """Atualizar configuração existente"""
    try:
        db_config = (
            db.query(MonitoringConfig).filter(MonitoringConfig.id == config_id).first()
        )

        if not db_config:
            raise HTTPException(status_code=404, detail="Configuração não encontrada")

        # Se tornando ativa, desativar outras
        if config_update.active is True:
            db.query(MonitoringConfig).filter(MonitoringConfig.id != config_id).update(
                {"active": False}
            )

        # Atualizar campos fornecidos
        update_data = config_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_config, field, value)

        db_config.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(db_config)

        logger.info(f"Config ID {config_id} atualizada")
        return db_config

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro ao atualizar config {config_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/monitoring/configs/{config_id}")
async def delete_monitoring_config(config_id: int, db: Session = Depends(get_db)):
    """Deletar configuração"""
    try:
        db_config = (
            db.query(MonitoringConfig).filter(MonitoringConfig.id == config_id).first()
        )

        if not db_config:
            raise HTTPException(status_code=404, detail="Configuração não encontrada")

        db.delete(db_config)
        db.commit()

        logger.info(f"Config ID {config_id} deletada")
        return {"message": "Configuração deletada com sucesso"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro ao deletar config {config_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# TELEGRAM SUBSCRIPTION ENDPOINTS
# ==========================================


@router.get(
    "/telegram/subscriptions", response_model=List[TelegramSubscriptionResponse]
)
async def list_telegram_subscriptions(db: Session = Depends(get_db)):
    """Listar todas as assinaturas do Telegram"""
    try:
        subscriptions = db.query(TelegramSubscription).all()
        return subscriptions
    except Exception as e:
        logger.error(f"❌ Erro ao listar assinaturas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/telegram/subscriptions", response_model=TelegramSubscriptionResponse)
async def create_telegram_subscription(
    subscription: TelegramSubscriptionCreate, db: Session = Depends(get_db)
):
    """Criar nova assinatura do Telegram"""
    try:
        # Verificar se chat_id já existe
        existing = (
            db.query(TelegramSubscription)
            .filter(TelegramSubscription.chat_id == subscription.chat_id)
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Chat ID '{subscription.chat_id}' já está cadastrado",
            )

        # Criar nova assinatura
        db_subscription = TelegramSubscription(**subscription.dict())
        db.add(db_subscription)
        db.commit()
        db.refresh(db_subscription)

        logger.info(f"Assinatura criada para chat {subscription.chat_id}")
        return db_subscription

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro ao criar assinatura: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/telegram/subscriptions/{chat_id}", response_model=TelegramSubscriptionResponse
)
async def get_telegram_subscription(chat_id: str, db: Session = Depends(get_db)):
    """Obter assinatura específica"""
    subscription = (
        db.query(TelegramSubscription)
        .filter(TelegramSubscription.chat_id == chat_id)
        .first()
    )

    if not subscription:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada")

    return subscription


@router.put(
    "/telegram/subscriptions/{chat_id}", response_model=TelegramSubscriptionResponse
)
async def update_telegram_subscription(
    chat_id: str,
    subscription_update: TelegramSubscriptionUpdate,
    db: Session = Depends(get_db),
):
    """Atualizar assinatura existente"""
    try:
        db_subscription = (
            db.query(TelegramSubscription)
            .filter(TelegramSubscription.chat_id == chat_id)
            .first()
        )

        if not db_subscription:
            raise HTTPException(status_code=404, detail="Assinatura não encontrada")

        # Atualizar campos fornecidos
        update_data = subscription_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_subscription, field, value)

        db.commit()
        db.refresh(db_subscription)

        logger.info(f"Assinatura {chat_id} atualizada")
        return db_subscription

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro ao atualizar assinatura {chat_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/telegram/subscriptions/{chat_id}")
async def delete_telegram_subscription(chat_id: str, db: Session = Depends(get_db)):
    """Deletar assinatura"""
    try:
        db_subscription = (
            db.query(TelegramSubscription)
            .filter(TelegramSubscription.chat_id == chat_id)
            .first()
        )

        if not db_subscription:
            raise HTTPException(status_code=404, detail="Assinatura não encontrada")

        db.delete(db_subscription)
        db.commit()

        logger.info(f"Assinatura {chat_id} deletada")
        return {"message": "Assinatura deletada com sucesso"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro ao deletar assinatura {chat_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# SYSTEM STATUS ENDPOINT
# ==========================================


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(db: Session = Depends(get_db)):
    """Obter status geral do sistema"""
    try:
        # Contar configurações
        total_configs = db.query(MonitoringConfig).count()
        active_configs = (
            db.query(MonitoringConfig).filter(MonitoringConfig.active == True).count()
        )

        # Contar assinaturas
        total_subs = db.query(TelegramSubscription).count()
        active_subs = (
            db.query(TelegramSubscription)
            .filter(TelegramSubscription.active == True)
            .count()
        )

        # Contar sinais das últimas 24h
        last_24h = datetime.now(timezone.utc) - timedelta(hours=24)
        signals_24h = (
            db.query(SignalHistory).filter(SignalHistory.created_at >= last_24h).count()
        )

        # TODO: Verificar status do Celery e Telegram
        celery_active = True  # Placeholder
        telegram_connected = True  # Placeholder

        return SystemStatusResponse(
            monitoring_configs=total_configs,
            active_configs=active_configs,
            telegram_subscriptions=total_subs,
            active_subscriptions=active_subs,
            last_signal_count_24h=signals_24h,
            celery_workers_active=celery_active,
            telegram_bot_connected=telegram_connected,
        )

    except Exception as e:
        logger.error(f"❌ Erro ao obter status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
