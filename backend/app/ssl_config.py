"""
SSL Configuration utilities for handling certificate verification issues on macOS
"""
import ssl
import certifi
import httpx
from typing import Optional

def create_ssl_context() -> ssl.SSLContext:
    """
    Create an SSL context with proper certificate verification.
    This handles the common macOS SSL certificate issue.
    """
    try:
        # Try to create a context with proper certificates
        context = ssl.create_default_context(cafile=certifi.where())
        return context
    except Exception:
        # Fallback: create context without verification for development
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context

def create_httpx_client(verify: Optional[bool] = None) -> httpx.AsyncClient:
    """
    Create an httpx client with proper SSL configuration.
    
    Args:
        verify: If None, will try to use proper SSL verification first,
                then fall back to disabled verification if needed.
                If True, forces SSL verification.
                If False, disables SSL verification.
    """
    if verify is None:
        try:
            # Try with proper SSL verification first
            return httpx.AsyncClient(verify=certifi.where())
        except Exception:
            # Fall back to disabled verification for development
            return httpx.AsyncClient(verify=False)
    else:
        return httpx.AsyncClient(verify=verify)

# For development, we'll disable SSL verification
# In production, you should use proper SSL certificates
def get_development_client() -> httpx.AsyncClient:
    """Get an HTTP client configured for development (SSL verification disabled)"""
    return httpx.AsyncClient(verify=False)
