from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models.database import SystemConfig, User
from routes.auth import verify_token
from datetime import datetime
import json

router = APIRouter(prefix="/api/config", tags=["config"])

# Initialize default configs data
DEFAULT_CONFIGS = [
    {
        "key": "enable_downloads",
        "value": "true",
        "description": "Ativar/Desativar download de materiais",
        "is_active": True
    },
    {
        "key": "enable_quiz",
        "value": "true", 
        "description": "Ativar/Desativar acesso aos quizzes",
        "is_active": True
    },
    {
        "key": "maintenance_mode",
        "value": "false",
        "description": "Modo de manutenção (bloqueia acesso geral)",
        "is_active": False
    }
]


def verify_admin_token(token_data: dict = Depends(verify_token)):
    """Verify that the user is an admin"""
    if token_data.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas administradores.")
    return token_data


@router.get("")
@router.get("/")
async def get_configs(session: Session = Depends(get_session)):
    """Get all system configurations"""
    try:
        configs = session.exec(select(SystemConfig)).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # If no configs exist, initialize defaults
    if not configs:
        for default in DEFAULT_CONFIGS:
            config = SystemConfig(**default)
            session.add(config)
        session.commit()
        configs = session.exec(select(SystemConfig)).all()
        
    return configs

@router.get("/{key}")
async def get_config(key: str, session: Session = Depends(get_session)):
    """Get a specific configuration"""
    config = session.get(SystemConfig, key)
    if not config:
        # Check defaults
        default = next((c for c in DEFAULT_CONFIGS if c["key"] == key), None)
        if default:
            return default
        raise HTTPException(status_code=404, detail="Config definition not found")
    return config

@router.put("/{key}")
async def update_config(
    key: str, 
    value: dict, 
    token_data: dict = Depends(verify_admin_token),
    session: Session = Depends(get_session)
):
    """Update a configuration (Admin only)"""
    config = session.get(SystemConfig, key)
    if not config:
        # Create if doesn't exist (from defaults or new)
        config = SystemConfig(
            key=key, 
            value=json.dumps(value.get("value")) if not isinstance(value.get("value"), str) else value.get("value", ""),
            description=value.get("description", ""), 
            is_active=value.get("is_active", True)
        )
        session.add(config)
    else:
        if "value" in value:
            config.value = json.dumps(value["value"]) if not isinstance(value["value"], str) else value["value"]
        if "is_active" in value:
            config.is_active = value["is_active"]
        config.updated_at = datetime.utcnow()
        session.add(config)
        
    session.commit()
    session.refresh(config)
    return config
