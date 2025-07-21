#!/usr/bin/env python3
"""
Test script to verify SSL configuration is working properly
"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.ssl_config import get_development_client

async def test_ssl_connection():
    """Test SSL connection to Google's OAuth endpoints"""
    print("Testing SSL connection to Google OAuth endpoints...")
    
    try:
        async with get_development_client() as client:
            # Test connection to Google's OAuth discovery endpoint
            response = await client.get('https://accounts.google.com/.well-known/openid-configuration')
            response.raise_for_status()
            print("✅ Successfully connected to Google OAuth discovery endpoint")
            
            # Test connection to Google's token endpoint
            token_response = await client.get('https://oauth2.googleapis.com/token')
            # This should return a 400 error (bad request) but not an SSL error
            print(f"✅ Token endpoint responded with status: {token_response.status_code}")
            
            # Test connection to Google's userinfo endpoint
            userinfo_response = await client.get('https://www.googleapis.com/oauth2/v2/userinfo')
            # This should return a 401 error (unauthorized) but not an SSL error
            print(f"✅ Userinfo endpoint responded with status: {userinfo_response.status_code}")
            
            print("\n🎉 All SSL connections are working properly!")
            print("The Google OAuth login should now work without SSL certificate errors.")
            
    except Exception as e:
        print(f"❌ SSL connection test failed: {e}")
        print("You may need to install certificates or use a different approach.")
        return False
    
    return True

if __name__ == "__main__":
    print("SSL Configuration Test")
    print("=" * 50)
    
    success = asyncio.run(test_ssl_connection())
    
    if success:
        print("\n📝 Next steps:")
        print("1. Make sure you have installed the updated requirements:")
        print("   pip install -r requirements.txt")
        print("2. Restart your FastAPI server")
        print("3. Try the Google OAuth login again")
    else:
        print("\n⚠️  SSL issues detected. The fix may need additional configuration.")
