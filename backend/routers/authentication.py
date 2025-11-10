"""
Authentication router - JWT token management and user authentication
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
from passlib.context import CryptContext
from core.config import settings
from core.logger import get_logger

logger = get_logger("auth")
router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class LoginRequest(BaseModel):
    """Login request schema"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserCreate(BaseModel):
    """User creation schema"""
    username: str
    password: str
    email: EmailStr


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning(f"Invalid token: {str(e)}")
        return None


@router.post("/login", response_model=TokenResponse, tags=["Authentication"])
async def login(request: LoginRequest):
    """
    User login endpoint
    Returns JWT access token for authenticated users
    """
    # TODO: Replace with actual database lookup
    # This is a demo implementation
    
    if request.username != "admin" or request.password != "admin123":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    expires_delta = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    access_token = create_access_token(
        data={"sub": request.username},
        expires_delta=expires_delta
    )
    
    logger.info(f"User logged in: {request.username}")
    
    return TokenResponse(
        access_token=access_token,
        expires_in=int(expires_delta.total_seconds())
    )


@router.post("/register", tags=["Authentication"])
async def register(user: UserCreate):
    """
    User registration endpoint
    Creates new user account
    """
    # TODO: Implement actual user registration with database
    logger.info(f"User registered: {user.username}")
    
    return {
        "message": "User registered successfully",
        "username": user.username
    }


@router.get("/me", tags=["Authentication"])
async def get_current_user(token: str = Depends(lambda: None)):
    """Get current authenticated user"""
    return {"message": "Current user endpoint"}
