# Image Generation Test Script

This directory contains test scripts to debug and verify gpt-image-1 image generation functionality.

## Files

- `test_image_generation.py` - Python script that tests image generation and saves results
- `run_image_test.sh` - Bash script to easily run the test
- `IMAGE_TEST_README.md` - This documentation file

## How to Run the Test

### Option 1: Using the Bash Script (Recommended)

```bash
cd professorAI/backend
./run_image_test.sh
```

### Option 2: Using Python Directly

```bash
cd professorAI/backend
python3 test_image_generation.py
```

## What the Test Does

1. **Loads Environment Variables**: Checks for `OPENAI_API_KEY` in `.env` file
2. **Initializes OpenAI Client**: Uses the same SSL configuration as the main application
3. **Generates Test Image**: Creates an educational UX research diagram
4. **Debug Response Structure**: Prints detailed information about the API response
5. **Downloads and Saves Image**: Saves the generated image to `test_images/` folder
6. **Reports Results**: Shows success/failure with detailed information

## Expected Output

### Success Case
```
🚀 Starting gpt-image-1 test...
==================================================
✅ OPENAI_API_KEY found: sk-proj-abc...
🖼️ Generating image with prompt: Create an educational diagram showing UX research...
🔍 Response type: <class 'openai.types.images_response.ImagesResponse'>
🔍 Response attributes: ['data', 'created', ...]
🔍 Response data type: <class 'list'>
🔍 Response data length: 1
🔍 First item type: <class 'openai.types.image.Image'>
🔍 First item attributes: ['url', 'revised_prompt', ...]
✅ Found URL via .url attribute: https://oaidalleapiprodscus.blob.core.windows.net/...
📥 Downloading image from: https://oaidalleapiprodscus.blob.core.windows.net/...
✅ Image saved successfully to: test_images/test_image_20250125_190500.png
📊 Image size: 1234567 bytes
==================================================
🎉 Test completed successfully!
📁 Check the 'test_images' folder for the generated image
🔗 Original URL: https://oaidalleapiprodscus.blob.core.windows.net/...
💾 Saved to: test_images/test_image_20250125_190500.png
📏 File size: 1234567 bytes
```

### Failure Case
```
🚀 Starting gpt-image-1 test...
==================================================
✅ OPENAI_API_KEY found: sk-proj-abc...
🖼️ Generating image with prompt: Create an educational diagram showing UX research...
🔍 Response type: <class 'openai.types.images_response.ImagesResponse'>
🔍 Response data type: <class 'list'>
🔍 Response data length: 1
🔍 First item type: <class 'NoneType'>
❌ Could not find URL. First item content: None
==================================================
💥 Test failed!
Check the error messages above for debugging information
```

## Troubleshooting

### Common Issues

1. **Missing API Key**
   ```
   ❌ OPENAI_API_KEY not found in environment variables
   ```
   **Solution**: Make sure your `.env` file contains `OPENAI_API_KEY=your_key_here`

2. **SSL Certificate Issues**
   ```
   ❌ Error during image generation: SSL: CERTIFICATE_VERIFY_FAILED
   ```
   **Solution**: The script uses the same SSL bypass configuration as the main app

3. **Permission Denied**
   ```
   bash: ./run_image_test.sh: Permission denied
   ```
   **Solution**: Run `chmod +x run_image_test.sh`

4. **Python Not Found**
   ```
   ❌ Python3 is not installed or not in PATH
   ```
   **Solution**: Install Python 3 or use `python` instead of `python3`

## Output Files

Generated images are saved in the `test_images/` directory with the format:
- `test_image_YYYYMMDD_HHMMSS.png`

Example: `test_image_20250125_190500.png`

## Debugging the gpt-image-1 Issue

The test script provides detailed debugging information to help identify why image generation might be failing:

1. **Response Structure Analysis**: Shows the exact type and attributes of the API response
2. **Data Inspection**: Examines the response.data array and its contents
3. **URL Extraction**: Tries multiple methods to extract the image URL
4. **Error Logging**: Provides full stack traces for any exceptions

This information will help us understand the exact structure of the gpt-image-1 API response and fix the `'NoneType' object is not subscriptable` error.

## Next Steps

After running this test:

1. **If Successful**: The image generation is working, and we can use the same approach in the main application
2. **If Failed**: Use the debug output to understand the API response structure and update the main application accordingly

## Integration with Main Application

Once the test is successful, the same image generation logic can be applied to the main slide generation system in `app/autogen_slide_service.py`.
