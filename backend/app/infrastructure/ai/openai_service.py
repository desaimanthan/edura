from typing import Optional, List, Dict, Any, Union
from openai import AsyncOpenAI
from decouple import config
from ...ssl_config import create_httpx_client


class OpenAIService:
    """Service for OpenAI API interactions with support for both Chat Completions and Responses API"""
    
    def __init__(self):
        self.client = None
        self.api_key = config("OPENAI_API_KEY")
    
    async def get_client(self) -> AsyncOpenAI:
        """Get OpenAI client instance with SSL configuration"""
        if not self.client:
            # Create httpx client with SSL configuration
            http_client = create_httpx_client(verify=False)  # Disable SSL verification for development
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                http_client=http_client
            )
        return self.client
    
    async def close_client(self):
        """Close OpenAI client"""
        if self.client:
            await self.client.close()
            self.client = None
    
    async def create_response(self, model: str, input: Union[str, List[Dict[str, Any]]], 
                            tools: Optional[List[Dict[str, Any]]] = None, 
                            stream: bool = False, **kwargs) -> Any:
        """
        Create response using the new Responses API
        
        Args:
            model: Model name (e.g., 'gpt-5-mini-2025-08-07')
            input: Input messages or string
            tools: List of tools including web_search_preview and function tools
            stream: Whether to stream the response
            **kwargs: Additional parameters
        
        Returns:
            Response object from Responses API
        """
        client = await self.get_client()
        
        # Prepare the request parameters with correct Responses API parameter names
        request_params = {
            "model": model,
            "input": input
        }
        
        # Add tools if provided
        if tools:
            request_params["tools"] = tools
        
        # Add streaming if requested
        if stream:
            request_params["stream"] = True
        
        # Handle kwargs with parameter name mapping for Responses API
        for key, value in kwargs.items():
            if key == "max_tokens":
                # Map max_tokens to max_output_tokens for Responses API
                request_params["max_output_tokens"] = value
            elif key == "instructions":
                # Instructions parameter is supported in Responses API
                request_params["instructions"] = value
            elif key == "temperature":
                # Temperature is supported
                request_params["temperature"] = value
            elif key == "top_p":
                # top_p is supported
                request_params["top_p"] = value
            elif key in ["store", "metadata", "safety_identifier", "service_tier", "parallel_tool_calls"]:
                # These are valid Responses API parameters
                request_params[key] = value
            # Skip unsupported parameters silently
        
        return await client.responses.create(**request_params)
    
    async def create_chat_completion(self, model: str, messages: List[Dict[str, Any]], 
                                   tools: Optional[List[Dict[str, Any]]] = None, 
                                   stream: bool = False, **kwargs) -> Any:
        """
        Create chat completion using the traditional Chat Completions API
        (Kept for backward compatibility with other agents)
        
        Args:
            model: Model name
            messages: List of message objects
            tools: List of tool definitions
            stream: Whether to stream the response
            **kwargs: Additional parameters
        
        Returns:
            Response object from Chat Completions API
        """
        client = await self.get_client()
        
        # Prepare the request parameters
        request_params = {
            "model": model,
            "messages": messages,
            **kwargs
        }
        
        # Add tools if provided
        if tools:
            request_params["tools"] = tools
        
        # Add streaming if requested
        if stream:
            request_params["stream"] = True
        
        return await client.chat.completions.create(**request_params)
    
    def convert_messages_to_input(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert Chat Completions messages format to Responses API input format
        
        Args:
            messages: List of message objects in Chat Completions format
        
        Returns:
            List of input objects in Responses API format
        """
        converted_input = []
        
        for message in messages:
            role = message.get("role")
            content = message.get("content", "")
            
            if role == "system":
                # System messages become instructions in Responses API
                # We'll handle this separately in the agent
                continue
            elif role in ["user", "assistant"]:
                converted_input.append({
                    "role": role,
                    "content": content
                })
            elif role == "tool":
                # Tool messages become function_call_output in Responses API
                converted_input.append({
                    "type": "function_call_output",
                    "call_id": message.get("tool_call_id"),
                    "output": content
                })
        
        return converted_input
    
    def extract_system_instructions(self, messages: List[Dict[str, Any]]) -> Optional[str]:
        """
        Extract system instructions from messages list
        
        Args:
            messages: List of message objects
        
        Returns:
            System instructions string or None
        """
        for message in messages:
            if message.get("role") == "system":
                return message.get("content")
        return None
    
    async def generate_image(self, prompt: str, 
                           model: str = "gpt-image-1",
                           size: str = "1024x1024",
                           quality: str = "high",
                           output_format: str = "png",
                           background: str = "auto",
                           output_compression: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate image using gpt-image-1 model
        
        Args:
            prompt: Text description of the desired image
            model: Model to use (gpt-image-1, dall-e-3, dall-e-2)
            size: Size of the generated image
            quality: Quality of the image (high, medium, low for gpt-image-1)
            output_format: Format of the image (png, jpeg, webp for gpt-image-1)
            background: Background setting (auto, transparent, opaque for gpt-image-1)
            output_compression: Compression level 0-100 for gpt-image-1 (auto-set based on format if None)
        
        Returns:
            Dictionary with success status and image data
        """
        try:
            client = await self.get_client()
            
            # Prepare request parameters
            request_params = {
                "model": model,
                "prompt": prompt,
                "size": size,
                "n": 1
            }
            
            # Add response_format only for models that support it (not gpt-image-1)
            if model != "gpt-image-1":
                request_params["response_format"] = "b64_json"
            
            # Add model-specific parameters
            if model == "gpt-image-1":
                # Set appropriate compression based on format if not specified
                if output_compression is None:
                    if output_format.lower() == "png":
                        # PNG requires compression of 100 (no compression)
                        output_compression = 100
                    else:
                        # JPEG and WebP can use compression
                        output_compression = 85
                
                # Ensure PNG compression is 100
                if output_format.lower() == "png" and output_compression < 100:
                    output_compression = 100
                
                request_params.update({
                    "quality": quality,
                    "output_format": output_format,
                    "background": background,
                    "output_compression": output_compression
                })
            elif model == "dall-e-3":
                # DALL-E 3 specific parameters
                request_params.update({
                    "quality": "hd" if quality == "high" else "standard",
                    "style": "vivid"  # or "natural"
                })
            
            print(f"\n{'='*60}")
            print(f"🎨 \033[94m[OpenAI Image Generation]\033[0m \033[1mGenerating image...\033[0m")
            print(f"   📝 Model: \033[93m{model}\033[0m")
            print(f"   📏 Size: \033[93m{size}\033[0m")
            print(f"   🎯 Quality: \033[93m{quality}\033[0m")
            print(f"   📄 Format: \033[93m{output_format}\033[0m")
            print(f"   📝 Prompt Preview: \033[90m{prompt[:100]}...\033[0m")
            print(f"{'='*60}")
            
            response = await client.images.generate(**request_params)
            
            print(f"\n✅ \033[94m[OpenAI Image Generation]\033[0m \033[1m\033[92mImage generated successfully\033[0m")
            
            # Extract response data
            image_data = response.data[0]
            
            # Handle different response formats for different models
            if model == "gpt-image-1":
                # gpt-image-1 returns base64 directly in the response
                b64_data = getattr(image_data, 'b64_json', None) or getattr(image_data, 'data', None)
            else:
                # DALL-E models use b64_json field
                b64_data = getattr(image_data, 'b64_json', None)
            
            result = {
                "success": True,
                "data": [{
                    "b64_json": b64_data,
                    "revised_prompt": getattr(image_data, 'revised_prompt', None)
                }],
                "created": response.created,
                "size": size,
                "quality": quality,
                "output_format": output_format
            }
            
            # Add usage info if available (gpt-image-1)
            if hasattr(response, 'usage'):
                result["usage"] = response.usage
            
            return result
            
        except Exception as e:
            print(f"\n❌ \033[94m[OpenAI Image Generation]\033[0m \033[1m\033[91mError: {str(e)}\033[0m")
            return {
                "success": False,
                "error": str(e)
            }
