from pydantic import BaseModel, Field, validator
from typing import Optional

class UserRegister(BaseModel):
    """Schema for user registration"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    email: Optional[str] = None
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username deve conter apenas letras, números, _ e -')
        return v.lower()

class UserLogin(BaseModel):
    """Schema for user login"""
    username: str
    password: str

class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user: dict  # {id, username}

class UserResponse(BaseModel):
    """User data response"""
    id: int
    username: str
    email: Optional[str]
    role: str
    created_at: str
