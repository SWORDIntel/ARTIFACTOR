"""
Authentication router for ARTIFACTOR v3.0
JWT-based authentication with refresh tokens
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from typing import Optional
import jwt
import bcrypt
import uuid

from ..database import get_database
from ..models import User, UserSession
from ..config import settings
from ..schemas.auth import (
    UserLogin, UserRegister, Token, UserResponse,
    PasswordChange, UserUpdate
)

router = APIRouter()
security = HTTPBearer()

class AuthService:
    """Authentication service with JWT and session management"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    def create_refresh_token() -> str:
        """Create refresh token"""
        return str(uuid.uuid4())

    @staticmethod
    async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_database)
    ) -> User:
        """Get current user from JWT token"""
        try:
            payload = jwt.decode(
                credentials.credentials,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            user_id: str = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication token"
                )
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )

        # Get user from database
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Update last activity
        user.last_login = datetime.utcnow()
        await db.commit()

        return user

auth_service = AuthService()

@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_database)
):
    """Register a new user"""

    # Check if user already exists
    result = await db.execute(
        select(User).where(
            (User.username == user_data.username) | (User.email == user_data.email)
        )
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )

    # Create new user
    hashed_password = auth_service.hash_password(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return UserResponse.from_orm(user)

@router.post("/login", response_model=Token)
async def login_user(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_database)
):
    """Authenticate user and return tokens"""

    # Find user by username or email
    result = await db.execute(
        select(User).where(
            (User.username == user_data.username) | (User.email == user_data.username)
        )
    )
    user = result.scalar_one_or_none()

    if not user or not auth_service.verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    # Create tokens
    access_token = auth_service.create_access_token(data={"sub": str(user.id)})
    refresh_token = auth_service.create_refresh_token()

    # Create session
    session = UserSession(
        user_id=user.id,
        session_token=access_token[:50],  # Store partial token for security
        refresh_token=refresh_token,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )

    db.add(session)
    user.last_login = datetime.utcnow()
    await db.commit()

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_database)
):
    """Refresh access token using refresh token"""

    # Find session by refresh token
    result = await db.execute(
        select(UserSession).where(
            (UserSession.refresh_token == refresh_token) &
            (UserSession.is_active == True) &
            (UserSession.expires_at > datetime.utcnow())
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    # Get user
    result = await db.execute(select(User).where(User.id == session.user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Create new tokens
    access_token = auth_service.create_access_token(data={"sub": str(user.id)})
    new_refresh_token = auth_service.create_refresh_token()

    # Update session
    session.session_token = access_token[:50]
    session.refresh_token = new_refresh_token
    session.last_activity = datetime.utcnow()
    user.last_login = datetime.utcnow()

    await db.commit()

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/logout")
async def logout_user(
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_database)
):
    """Logout user and invalidate session"""

    # Deactivate all user sessions
    result = await db.execute(
        select(UserSession).where(
            (UserSession.user_id == current_user.id) &
            (UserSession.is_active == True)
        )
    )
    sessions = result.scalars().all()

    for session in sessions:
        session.is_active = False

    await db.commit()

    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(auth_service.get_current_user)
):
    """Get current user information"""
    return UserResponse.from_orm(current_user)

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_database)
):
    """Update current user information"""

    # Update user fields
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    if user_update.email is not None:
        # Check if email is already taken
        result = await db.execute(
            select(User).where(
                (User.email == user_update.email) & (User.id != current_user.id)
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        current_user.email = user_update.email

    if user_update.preferences is not None:
        current_user.preferences = user_update.preferences

    current_user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(current_user)

    return UserResponse.from_orm(current_user)

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_database)
):
    """Change user password"""

    # Verify current password
    if not auth_service.verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Update password
    current_user.hashed_password = auth_service.hash_password(password_data.new_password)
    current_user.updated_at = datetime.utcnow()

    # Invalidate all sessions
    result = await db.execute(
        select(UserSession).where(
            (UserSession.user_id == current_user.id) &
            (UserSession.is_active == True)
        )
    )
    sessions = result.scalars().all()

    for session in sessions:
        session.is_active = False

    await db.commit()

    return {"message": "Password changed successfully. Please log in again."}

# Export auth service for use in other modules
get_current_user = auth_service.get_current_user