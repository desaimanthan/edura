from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from decouple import config
from google.auth.transport import requests
from google.oauth2 import id_token
import ssl
import httpx

from .ssl_config import get_development_client

from .models import TokenData, UserInDB
from .database import get_users_collection

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = config("JWT_SECRET_KEY")
ALGORITHM = config("JWT_ALGORITHM", default="HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = config("ACCESS_TOKEN_EXPIRE_MINUTES", default=30, cast=int)

# Google OAuth settings
GOOGLE_CLIENT_ID = config("GOOGLE_CLIENT_ID")

# Security scheme
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return user email"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    return token_data

async def get_current_user(token_data: TokenData = Depends(verify_token)):
    """Get current user from token"""
    users_collection = await get_users_collection()
    user = await users_collection.find_one({"email": token_data.email})
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return UserInDB(**user)

async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)):
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def authenticate_user(email: str, password: str):
    """Authenticate user with email and password"""
    users_collection = await get_users_collection()
    user = await users_collection.find_one({"email": email})
    
    if not user:
        return False
    
    if not user.get("password_hash"):
        return False
    
    if not verify_password(password, user["password_hash"]):
        return False
    
    return UserInDB(**user)

async def verify_google_token(token: str):
    """Verify Google OAuth token"""
    try:
        # Use the development client with SSL configuration
        async with get_development_client() as client:
            response = await client.get(
                f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={token}"
            )
            response.raise_for_status()
            token_info = response.json()
            
            # Verify the audience (client_id)
            if token_info.get('audience') != GOOGLE_CLIENT_ID:
                raise ValueError('Invalid audience.')
            
            # Get user info
            userinfo_response = await client.get(
                f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={token}"
            )
            userinfo_response.raise_for_status()
            user_info = userinfo_response.json()
            
            return {
                "id": user_info["id"],
                "email": user_info["email"],
                "name": user_info["name"],
                "picture": user_info.get("picture"),
                "verified_email": user_info.get("verified_email", False)
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Google token: {str(e)}"
        )

def generate_reset_token() -> str:
    """Generate a password reset token"""
    import secrets
    return secrets.token_urlsafe(32)
