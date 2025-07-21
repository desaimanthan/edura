from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import RedirectResponse
from datetime import datetime, timedelta
from pymongo.errors import DuplicateKeyError
from authlib.integrations.starlette_client import OAuth
from decouple import config
import secrets
from bson import ObjectId
import ssl
import httpx

from ..ssl_config import get_development_client

from ..models import (
    UserCreate, UserLogin, UserResponse, Token, 
    PasswordResetRequest, PasswordReset, UserInDB
)
from ..auth import (
    authenticate_user, create_access_token, get_password_hash,
    verify_google_token, generate_reset_token, get_current_active_user
)
from ..database import get_users_collection, get_password_reset_collection, get_roles_collection

router = APIRouter()

# Create SSL context that doesn't verify certificates (for development)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Initialize OAuth with custom HTTP client that handles SSL
oauth = OAuth()
oauth.register(
    name='google',
    client_id=config('GOOGLE_CLIENT_ID'),
    client_secret=config('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Configure the OAuth client to use our SSL context
if hasattr(oauth.google, '_client'):
    oauth.google._client = httpx.AsyncClient(verify=False)

# Store for OAuth state (in production, use Redis or database)
oauth_states = {}

async def get_default_role_id():
    """Get the default Student role ObjectId"""
    roles_collection = await get_roles_collection()
    student_role = await roles_collection.find_one({"name": "Student"})
    return student_role["_id"] if student_role else None

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate):
    """Register a new user with email and password"""
    users_collection = await get_users_collection()
    
    # Check if user already exists
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Get default role
    default_role_id = await get_default_role_id()
    
    # Create new user
    user_dict = {
        "email": user.email,
        "name": user.name,
        "password_hash": get_password_hash(user.password),
        "role_id": default_role_id,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    try:
        result = await users_collection.insert_one(user_dict)
        return {
            "message": "User created successfully",
            "user_id": str(result.inserted_id)
        }
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

@router.post("/login", response_model=dict)
async def login_user(user_credentials: UserLogin):
    """Login user with email and password"""
    user = await authenticate_user(user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/google", response_model=dict)
async def google_auth(token_data: dict):
    """Authenticate user with Google OAuth token"""
    google_token = token_data.get("token")
    if not google_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google token is required"
        )
    
    # Verify Google token
    google_user_info = await verify_google_token(google_token)
    
    users_collection = await get_users_collection()
    
    # Check if user exists
    user = await users_collection.find_one({"email": google_user_info["email"]})
    
    if user:
        # Update existing user with Google info if not already set
        update_data = {"updated_at": datetime.utcnow()}
        if not user.get("google_id"):
            update_data["google_id"] = google_user_info["id"]
        if not user.get("avatar") and google_user_info.get("picture"):
            update_data["avatar"] = google_user_info["picture"]
        
        await users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": update_data}
        )
        
        user_obj = UserInDB(**user)
    else:
        # Get default role
        default_role_id = await get_default_role_id()
        
        # Create new user from Google info
        user_dict = {
            "email": google_user_info["email"],
            "name": google_user_info["name"],
            "google_id": google_user_info["id"],
            "avatar": google_user_info.get("picture"),
            "role_id": default_role_id,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await users_collection.insert_one(user_dict)
        user_dict["_id"] = result.inserted_id
        user_obj = UserInDB(**user_dict)
    
    # Create access token
    access_token = create_access_token(data={"sub": user_obj.email})
    
    return {
        "id": str(user_obj.id),
        "email": user_obj.email,
        "name": user_obj.name,
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserInDB = Depends(get_current_active_user)):
    """Get current user information"""
    return UserResponse(
        _id=str(current_user.id),
        email=current_user.email,
        name=current_user.name,
        is_active=current_user.is_active,
        google_id=current_user.google_id,
        avatar=current_user.avatar,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )

@router.post("/request-password-reset")
async def request_password_reset(request: PasswordResetRequest):
    """Request password reset"""
    users_collection = await get_users_collection()
    password_reset_collection = await get_password_reset_collection()
    
    # Check if user exists
    user = await users_collection.find_one({"email": request.email})
    if not user:
        # Don't reveal if email exists or not for security
        return {"message": "If the email exists, a password reset link has been sent"}
    
    # Generate reset token
    reset_token = generate_reset_token()
    expires_at = datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
    
    # Store reset token
    reset_data = {
        "email": request.email,
        "token": reset_token,
        "created_at": datetime.utcnow(),
        "expires_at": expires_at,
        "used": False
    }
    
    await password_reset_collection.insert_one(reset_data)
    
    # In a real application, you would send an email here
    # For now, we'll just return the token (remove this in production)
    return {
        "message": "If the email exists, a password reset link has been sent",
        "reset_token": reset_token  # Remove this in production
    }

@router.post("/reset-password")
async def reset_password(reset_data: PasswordReset):
    """Reset password using token"""
    users_collection = await get_users_collection()
    password_reset_collection = await get_password_reset_collection()
    
    # Find and validate reset token
    reset_record = await password_reset_collection.find_one({
        "token": reset_data.token,
        "used": False,
        "expires_at": {"$gt": datetime.utcnow()}
    })
    
    if not reset_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Update user password
    new_password_hash = get_password_hash(reset_data.new_password)
    await users_collection.update_one(
        {"email": reset_record["email"]},
        {
            "$set": {
                "password_hash": new_password_hash,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Mark token as used
    await password_reset_collection.update_one(
        {"_id": reset_record["_id"]},
        {"$set": {"used": True}}
    )
    
    return {"message": "Password reset successfully"}

@router.get("/google/login")
async def google_login(request: Request):
    """Initiate Google OAuth login"""
    try:
        # Create redirect URI
        redirect_uri = f"http://localhost:8000/auth/google/callback"
        
        # Manual OAuth URL construction to avoid SSL issues during server metadata loading
        google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            'client_id': config('GOOGLE_CLIENT_ID'),
            'redirect_uri': redirect_uri,
            'scope': 'openid email profile',
            'response_type': 'code',
            'access_type': 'offline',
            'prompt': 'consent'
        }
        
        # Build the authorization URL manually
        from urllib.parse import urlencode
        authorization_url = f"{google_auth_url}?{urlencode(params)}"
        
        return {"authorization_url": authorization_url}
        
    except Exception as e:
        print(f"Google login error: {e}")  # Debug logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create Google authorization URL: {str(e)}"
        )

@router.get("/google/callback")
async def google_callback(request: Request):
    """Handle Google OAuth callback"""
    try:
        # Bypass state verification for development - manually handle the OAuth flow
        code = request.query_params.get('code')
        if not code:
            raise Exception("No authorization code received")
        
        # Exchange code for token using development client with SSL configuration
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            'client_id': config('GOOGLE_CLIENT_ID'),
            'client_secret': config('GOOGLE_CLIENT_SECRET'),
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': 'http://localhost:8000/auth/google/callback'
        }
        
        async with get_development_client() as client:
            token_response = await client.post(token_url, data=token_data)
            token_response.raise_for_status()
            token = token_response.json()
        
        # Get user info using development client with SSL configuration
        userinfo_url = f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={token['access_token']}"
        async with get_development_client() as client:
            userinfo_response = await client.get(userinfo_url)
            userinfo_response.raise_for_status()
            user_info = userinfo_response.json()
        
        users_collection = await get_users_collection()
        
        # Check if user exists
        user = await users_collection.find_one({"email": user_info["email"]})
        
        if user:
            # Update existing user with Google info if not already set
            update_data = {"updated_at": datetime.utcnow()}
            if not user.get("google_id"):
                update_data["google_id"] = user_info["id"]
            if not user.get("avatar") and user_info.get("picture"):
                update_data["avatar"] = user_info["picture"]
            
            await users_collection.update_one(
                {"_id": user["_id"]},
                {"$set": update_data}
            )
            
            user_obj = UserInDB(**user)
        else:
            # Get default role
            default_role_id = await get_default_role_id()
            
            # Create new user from Google info
            user_dict = {
                "email": user_info["email"],
                "name": user_info["name"],
                "google_id": user_info["id"],
                "avatar": user_info.get("picture"),
                "role_id": default_role_id,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await users_collection.insert_one(user_dict)
            user_dict["_id"] = result.inserted_id
            user_obj = UserInDB(**user_dict)
        
        # Create access token
        access_token = create_access_token(data={"sub": user_obj.email})
        
        # Redirect to frontend with token
        frontend_url = config('FRONTEND_URL', 'http://localhost:3000')
        return RedirectResponse(
            url=f"{frontend_url}/auth/callback?token={access_token}&user_id={str(user_obj.id)}"
        )
        
    except Exception as e:
        print(f"OAuth callback error: {e}")  # Debug logging
        # Redirect to frontend with error
        frontend_url = config('FRONTEND_URL', 'http://localhost:3000')
        return RedirectResponse(
            url=f"{frontend_url}/auth/signin?error=oauth_error"
        )

@router.post("/logout")
async def logout(current_user: UserInDB = Depends(get_current_active_user)):
    """Logout user (in a real app, you might want to blacklist the token)"""
    return {"message": "Successfully logged out"}
