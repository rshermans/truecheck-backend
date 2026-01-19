from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
import os

from models.database import User
from models.auth_schemas import UserRegister, UserLogin, Token, UserResponse
from database import get_session

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "truecheck-secret-key-change-in-production-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

security = HTTPBearer()

def create_access_token(user_id: int, username: str, role: str):
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode = {"sub": str(user_id), "username": username, "role": role, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return user data"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"user_id": int(payload["sub"]), "username": payload["username"], "role": payload.get("role", "user")}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

@router.post("/register", response_model=Token)
async def register(user_data: UserRegister, session: Session = Depends(get_session)):
    """Register a new user"""
    # Check if username exists
    existing = session.exec(select(User).where(User.username == user_data.username)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username já existe")
    
    # Create user
    hashed_password = pwd_context.hash(user_data.password)
    user = User(
        username=user_data.username,
        password_hash=hashed_password,
        email=user_data.email
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Generate token
    token = create_access_token(user.id, user.username, user.role)
    return Token(
        access_token=token,
        user={"id": user.id, "username": user.username, "role": user.role}
    )

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, session: Session = Depends(get_session)):
    """Login with username and password"""
    # Find user
    user = session.exec(select(User).where(User.username == credentials.username)).first()
    if not user or not pwd_context.verify(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Conta desativada")
    
    # Generate token
    token = create_access_token(user.id, user.username, user.role)
    return Token(
        access_token=token,
        user={"id": user.id, "username": user.username, "role": user.role}
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    token_data: dict = Depends(verify_token),
    session: Session = Depends(get_session)
):
    """Get current authenticated user"""
    user = session.get(User, token_data["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        created_at=user.created_at.isoformat()
    )

# Password Reset Schemas
from pydantic import BaseModel

class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

# Import email service
from services.email_service import (
    generate_reset_token, 
    verify_reset_token, 
    invalidate_reset_token,
    send_password_reset_email
)
from config import settings

@router.post("/request-reset")
async def request_password_reset(
    data: PasswordResetRequest,
    session: Session = Depends(get_session)
):
    """Request a password reset email"""
    # Find user by email
    user = session.exec(select(User).where(User.email == data.email)).first()
    
    if not user:
        # Don't reveal if email exists (security)
        return {"message": "Se o email existir, receberá instruções de recuperação."}
    
    # Generate reset token
    token = generate_reset_token(user.id, user.email)
    
    # Build reset link
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    
    # Send email
    send_password_reset_email(user.email, reset_link)
    
    return {"message": "Se o email existir, receberá instruções de recuperação."}

@router.post("/reset-password")
async def reset_password(
    data: PasswordResetConfirm,
    session: Session = Depends(get_session)
):
    """Reset password using token from email"""
    # Verify token
    token_data = verify_reset_token(data.token)
    
    if not token_data:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado")
    
    # Find user
    user = session.get(User, token_data["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    
    # Update password
    user.password_hash = pwd_context.hash(data.new_password)
    session.add(user)
    session.commit()
    
    # Invalidate token
    invalidate_reset_token(data.token)
    
    return {"message": "Senha alterada com sucesso"}
