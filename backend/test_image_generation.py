#!/usr/bin/env python3
"""
Test script for gpt-image-1 image generation
This script tests image generation and saves the result to the project folder
"""

import os
import sys
import asyncio
import requests
import base64
from datetime import datetime
from pathlib import Path

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Import our modules
from app.ssl_config import get_sync_development_client
from openai import OpenAI

async def test_image_generation():
    """Test image generation with gpt-image-1 and save to project folder"""
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        return False
    
    print(f"✅ OPENAI_API_KEY found: {api_key[:10]}...")
    
    try:
        # Create HTTP client with SSL configuration
        http_client = get_sync_development_client()
        
        # Initialize OpenAI client
        client = OpenAI(
            api_key=api_key,
            http_client=http_client
        )
        
        # Test prompt
        prompt = "Create an educational diagram showing UX research methods including interviews, surveys, usability testing, and analytics. Clean, professional, academic style suitable for learning materials."
        
        print(f"🖼️ Generating image with prompt: {prompt[:50]}...")
        
        # Generate image
        response = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024",
            quality="high",
            n=1
        )
        
        # Debug response structure
        print(f"🔍 Response type: {type(response)}")
        print(f"🔍 Response attributes: {dir(response)}")
        
        if hasattr(response, 'data'):
            print(f"🔍 Response data type: {type(response.data)}")
            print(f"🔍 Response data length: {len(response.data) if response.data else 'No data'}")
            
            if response.data and len(response.data) > 0:
                first_item = response.data[0]
                print(f"🔍 First item type: {type(first_item)}")
                print(f"🔍 First item attributes: {dir(first_item)}")
                
                # Debug all available fields
                print(f"🔍 First item fields and values:")
                for attr in ['url', 'b64_json', 'revised_prompt']:
                    if hasattr(first_item, attr):
                        value = getattr(first_item, attr)
                        if attr == 'b64_json' and value:
                            print(f"  - {attr}: [Base64 data - length: {len(value)}]")
                        else:
                            print(f"  - {attr}: {value[:50] + '...' if isinstance(value, str) and len(value) > 50 else value}")
                
                # Try to get URL or base64 data
                image_url = None
                image_data = None
                
                if hasattr(first_item, 'url') and first_item.url:
                    image_url = first_item.url
                    print(f"✅ Found URL via .url attribute: {image_url}")
                elif hasattr(first_item, 'b64_json') and first_item.b64_json:
                    image_data = first_item.b64_json
                    print(f"✅ Found base64 data via .b64_json attribute (length: {len(image_data)})")
                elif hasattr(first_item, 'image_url') and first_item.image_url:
                    image_url = first_item.image_url
                    print(f"✅ Found URL via .image_url attribute: {image_url}")
                elif isinstance(first_item, dict):
                    image_url = first_item.get('url') or first_item.get('image_url')
                    image_data = first_item.get('b64_json')
                    print(f"✅ Found via dict access - URL: {image_url}, B64: {bool(image_data)}")
                else:
                    print(f"❌ Could not find URL or base64 data. First item content: {first_item}")
                    return False
                
                # Create images directory if it doesn't exist
                images_dir = Path("test_images")
                images_dir.mkdir(exist_ok=True)
                
                # Generate filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"test_image_{timestamp}.png"
                filepath = images_dir / filename
                
                if image_url:
                    # Download and save the image from URL
                    print(f"📥 Downloading image from: {image_url}")
                    
                    img_response = requests.get(image_url)
                    if img_response.status_code == 200:
                        with open(filepath, 'wb') as f:
                            f.write(img_response.content)
                        
                        print(f"✅ Image saved successfully to: {filepath}")
                        print(f"📊 Image size: {len(img_response.content)} bytes")
                        
                        return {
                            "success": True,
                            "image_url": image_url,
                            "saved_path": str(filepath),
                            "file_size": len(img_response.content),
                            "prompt": prompt,
                            "source": "url"
                        }
                    else:
                        print(f"❌ Failed to download image. Status code: {img_response.status_code}")
                        return False
                        
                elif image_data:
                    # Save base64 image data
                    print(f"💾 Saving base64 image data to: {filepath}")
                    
                    try:
                        # Decode base64 data
                        image_bytes = base64.b64decode(image_data)
                        
                        # Save to file
                        with open(filepath, 'wb') as f:
                            f.write(image_bytes)
                        
                        print(f"✅ Image saved successfully to: {filepath}")
                        print(f"📊 Image size: {len(image_bytes)} bytes")
                        
                        return {
                            "success": True,
                            "image_data_length": len(image_data),
                            "saved_path": str(filepath),
                            "file_size": len(image_bytes),
                            "prompt": prompt,
                            "source": "base64"
                        }
                        
                    except Exception as e:
                        print(f"❌ Failed to decode/save base64 image: {str(e)}")
                        return False
                        
                else:
                    print("❌ No image URL or base64 data found in response")
                    return False
                    
            else:
                print("❌ No data in response or empty data array")
                return False
        else:
            print("❌ Response has no 'data' attribute")
            return False
            
    except Exception as e:
        print(f"❌ Error during image generation: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to run the test"""
    print("🚀 Starting gpt-image-1 test...")
    print("=" * 50)
    
    # Run the async test
    result = asyncio.run(test_image_generation())
    
    print("=" * 50)
    if result:
        print("🎉 Test completed successfully!")
        print(f"📁 Check the 'test_images' folder for the generated image")
        if isinstance(result, dict):
            if result.get("source") == "url":
                print(f"🔗 Original URL: {result['image_url']}")
            elif result.get("source") == "base64":
                print(f"📊 Base64 data length: {result['image_data_length']} characters")
            print(f"💾 Saved to: {result['saved_path']}")
            print(f"📏 File size: {result['file_size']} bytes")
            print(f"🎯 Source: {result['source']}")
    else:
        print("💥 Test failed!")
        print("Check the error messages above for debugging information")

if __name__ == "__main__":
    main()
