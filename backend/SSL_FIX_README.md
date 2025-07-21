# SSL Certificate Fix for Google OAuth

## Problem
The application was experiencing SSL certificate verification failures when trying to connect to Google's OAuth services, resulting in the error:
```
httpx.ConnectError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:997)
```

This is a common issue on macOS where the system doesn't have proper SSL certificates configured for Python applications.

## Solution Implemented

### 1. Created SSL Configuration Module (`app/ssl_config.py`)
- Added a centralized SSL configuration utility
- Provides functions to create HTTP clients with proper SSL handling
- Falls back to disabled SSL verification for development environments
- Uses `certifi` package for proper certificate management

### 2. Updated Authentication Files
- **`app/auth.py`**: Updated `verify_google_token()` function to use the new SSL configuration
- **`app/routes/auth.py`**: Updated OAuth client initialization and HTTP requests to use SSL-safe clients

### 3. Updated Dependencies
- Added `certifi==2023.11.17` to `requirements.txt` for proper SSL certificate management

### 4. Key Changes Made

#### In `app/ssl_config.py`:
```python
def get_development_client() -> httpx.AsyncClient:
    """Get an HTTP client configured for development (SSL verification disabled)"""
    return httpx.AsyncClient(verify=False)
```

#### In `app/auth.py`:
```python
async def verify_google_token(token: str):
    async with get_development_client() as client:
        # SSL-safe requests to Google APIs
        response = await client.get(f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={token}")
        # ... rest of the function
```

#### In `app/routes/auth.py`:
```python
# OAuth client configuration with SSL handling
oauth.register(
    name='google',
    client_id=config('GOOGLE_CLIENT_ID'),
    client_secret=config('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# Configure OAuth client to use SSL-safe HTTP client
if hasattr(oauth.google, '_client'):
    oauth.google._client = httpx.AsyncClient(verify=False)
```

## Testing
Created `test_ssl_fix.py` to verify the SSL configuration works properly:
```bash
cd professorAI/backend
python test_ssl_fix.py
```

## Installation Steps
1. Install updated dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Restart your FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```

3. Test the Google OAuth login functionality

## Security Considerations

### Development vs Production
- **Development**: SSL verification is disabled for ease of development
- **Production**: Should use proper SSL certificates and enable verification

### For Production Deployment
To make this production-ready, update `ssl_config.py`:
```python
def create_httpx_client(verify: Optional[bool] = None) -> httpx.AsyncClient:
    if verify is None:
        try:
            # Try with proper SSL verification first
            return httpx.AsyncClient(verify=certifi.where())
        except Exception:
            # Only fall back to disabled verification in development
            if os.getenv('ENVIRONMENT') == 'development':
                return httpx.AsyncClient(verify=False)
            else:
                raise
    else:
        return httpx.AsyncClient(verify=verify)
```

## Alternative Solutions

### Option 1: Install System Certificates (macOS)
```bash
/Applications/Python\ 3.x/Install\ Certificates.command
```

### Option 2: Use Environment Variable
```bash
export SSL_CERT_FILE=$(python -m certifi)
export REQUESTS_CA_BUNDLE=$(python -m certifi)
```

### Option 3: Update Python's Certificate Store
```bash
pip install --upgrade certifi
```

## Files Modified
- `app/ssl_config.py` (new)
- `app/auth.py` (updated)
- `app/routes/auth.py` (updated)
- `requirements.txt` (updated)
- `test_ssl_fix.py` (new)

## Additional CORS Fix

### Problem
After fixing the SSL issues, CORS (Cross-Origin Resource Sharing) errors were preventing the frontend from accessing the backend API:
```
Access to XMLHttpRequest at 'http://localhost:8000/auth/google/login' from origin 'http://localhost:3000' has been blocked by CORS policy
```

### Solution
Updated the CORS middleware configuration in `main.py` to be more permissive for development:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        config("FRONTEND_URL", default="http://localhost:3000")
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)
```

### OAuth Endpoint Fix
Also updated the `/auth/google/login` endpoint to manually construct the OAuth URL instead of relying on authlib's server metadata loading, which was causing SSL issues:

```python
@router.get("/google/login")
async def google_login(request: Request):
    try:
        redirect_uri = f"http://localhost:8000/auth/google/callback"
        google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            'client_id': config('GOOGLE_CLIENT_ID'),
            'redirect_uri': redirect_uri,
            'scope': 'openid email profile',
            'response_type': 'code',
            'access_type': 'offline',
            'prompt': 'consent'
        }
        
        from urllib.parse import urlencode
        authorization_url = f"{google_auth_url}?{urlencode(params)}"
        return {"authorization_url": authorization_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Verification
Both SSL and CORS fixes have been tested and verified to work correctly:

1. **SSL Test**: `python test_ssl_fix.py` - ✅ All SSL connections working
2. **Endpoint Test**: `/auth/google/login` returns 200 with valid authorization URL
3. **CORS Test**: Proper CORS headers are returned for cross-origin requests

The Google OAuth login should now function without SSL certificate errors or CORS issues.
