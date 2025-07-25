#!/bin/bash

# Image Generation Test Script
# This script runs the image generation test and shows the results

echo "🚀 Running gpt-image-1 Image Generation Test"
echo "=============================================="

# Change to the backend directory
cd "$(dirname "$0")"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed or not in PATH"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found in backend directory"
    echo "Please make sure OPENAI_API_KEY is set in .env file"
    exit 1
fi

# Run the test
echo "🔧 Running image generation test..."
python3 test_image_generation.py

# Check if test_images directory was created
if [ -d "test_images" ]; then
    echo ""
    echo "📁 Generated images:"
    ls -la test_images/
    echo ""
    echo "🖼️ You can view the generated images in the 'test_images' folder"
else
    echo ""
    echo "❌ No test_images directory found - test may have failed"
fi

echo ""
echo "✅ Test completed!"
