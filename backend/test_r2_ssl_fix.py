#!/usr/bin/env python3
"""
Test script to verify R2 SSL configuration is working properly
"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.r2_storage import R2StorageService

async def test_r2_ssl_connection():
    """Test SSL connection to Cloudflare R2"""
    print("Testing SSL connection to Cloudflare R2...")
    
    try:
        # Initialize R2 service
        r2_service = R2StorageService()
        
        # Test basic client creation
        print("✅ R2 client created successfully")
        
        # Test listing files (this will make an HTTPS request to R2)
        print("Testing R2 list operation...")
        files = await r2_service.list_course_files("test-course-id")
        print(f"✅ R2 list operation completed successfully (found {len(files)} files)")
        
        # Test curriculum versions (another HTTPS request)
        print("Testing R2 curriculum versions operation...")
        versions = await r2_service.get_curriculum_versions("test-course-id")
        print(f"✅ R2 curriculum versions operation completed successfully (found {len(versions)} versions)")
        
        print("\n🎉 All R2 SSL connections are working properly!")
        print("The R2 storage operations should now work without SSL certificate errors.")
        
        return True
        
    except Exception as e:
        print(f"❌ R2 SSL connection test failed: {e}")
        print("The SSL configuration may need additional adjustments.")
        return False

if __name__ == "__main__":
    print("R2 SSL Configuration Test")
    print("=" * 50)
    
    success = asyncio.run(test_r2_ssl_connection())
    
    if success:
        print("\n📝 Next steps:")
        print("1. The R2 SSL configuration is working properly")
        print("2. Course deletion should now work without SSL errors")
        print("3. Try deleting a course to verify the fix")
    else:
        print("\n⚠️  R2 SSL issues detected. You may need to:")
        print("1. Check your R2 environment variables are set correctly")
        print("2. Ensure you have proper network connectivity")
        print("3. Verify your R2 credentials are valid")
