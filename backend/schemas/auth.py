"""
Pydantic schemas for authentication endpoints
"""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

class UserLogin(BaseModel):
    """User login request schema"""
    username: str
    password: str

    @validator('username')
    def username_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Username cannot be empty')
        return v.strip()

class UserRegister(BaseModel):
    """User registration request schema"""
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None

    @validator('username')
    def validate_username(cls, v):
        if not v.strip():
            raise ValueError('Username cannot be empty')
        if len(v.strip()) < 3:
            raise ValueError('Username must be at least 3 characters')
        if len(v.strip()) > 50:
            raise ValueError('Username must be less than 50 characters')
        return v.strip()

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v) > 128:
            raise ValueError('Password must be less than 128 characters')
        return v

class Token(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

class UserResponse(BaseModel):
    """User response schema"""
    id: uuid.UUID
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    preferences: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    """User update request schema"""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    preferences: Optional[Dict[str, Any]] = None

class PasswordChange(BaseModel):
    """Password change request schema"""
    current_password: str
    new_password: str

    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v) > 128:
            raise ValueError('Password must be less than 128 characters')
        return v