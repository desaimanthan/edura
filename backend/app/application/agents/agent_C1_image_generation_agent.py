import base64
import random
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from io import BytesIO
from PIL import Image

from ...infrastructure.ai.openai_service import OpenAIService
from ...infrastructure.storage.r2_storage import R2StorageService


class ImageGenerationAgent:
    """Agent specialized in generating and storing course images (covers, slides, etc.) using gpt-image-1"""
    
    def __init__(self, openai_service: OpenAIService, r2_storage: R2StorageService):
        self.openai = openai_service
        self.r2_storage = r2_storage
        self.model = "gpt-image-1"
    
    async def generate_course_cover_image(self, course_id: str, course_name: str, 
                                         course_description: str = "", 
                                         style_preference: str = "professional_educational",
                                         dynamic_colors: bool = True) -> Dict[str, Any]:
        """
        Generate and store course cover image
        
        Args:
            course_id: Database course ID
            course_name: Course title (e.g., "Machine Learning Fundamentals")
            course_description: Optional course description for context
            style_preference: Style hint (professional_educational, modern, colorful, etc.)
        
        Returns:
            {
                "success": bool,
                "r2_key": str,
                "public_url": str,
                "image_metadata": dict,
                "error": str (if failed)
            }
        """
        
        try:
            print(f"\n🎨 \033[94m[ImageGenerationAgent]\033[0m \033[1mGenerating cover image for: {course_name}\033[0m")
            
            # Step 1: Generate dynamic color palette if enabled
            color_palette = None
            if dynamic_colors:
                color_palette = self._generate_dynamic_color_palette(course_name, course_description, style_preference)
            
            # Step 2: Create detailed prompt based on course context
            prompt = await self._create_course_image_prompt(course_name, course_description, style_preference, color_palette, "cover")
            
            # Step 3: Generate image using OpenAI gpt-image-1
            openai_response = await self.openai.generate_image(
                prompt=prompt,
                model=self.model,
                size="1536x1024",  # 3:2 aspect ratio (closest to 16:9 available)
                quality="medium",
                output_format="png",
                background="auto"
            )
            
            if not openai_response["success"]:
                return {
                    "success": False,
                    "error": f"Image generation failed: {openai_response.get('error', 'Unknown error')}"
                }
            
            # Step 4: Extract and decode base64 data
            base64_data = openai_response["data"][0]["b64_json"]
            image_bytes = base64.b64decode(base64_data)
            
            print(f"📏 \033[94m[ImageGenerationAgent]\033[0m Image generated: {len(image_bytes)} bytes")
            
            # Step 5: Upload to R2 storage
            filename = f"cover_image.{openai_response['output_format']}"
            content_type = f"image/{openai_response['output_format']}"
            
            r2_result = await self.r2_storage.upload_course_cover_image(
                course_id=course_id,
                image_data=image_bytes,
                filename=filename,
                content_type=content_type
            )
            
            if r2_result["success"]:
                print(f"✅ \033[94m[ImageGenerationAgent]\033[0m \033[1m\033[92mCover image generated and stored successfully\033[0m")
                
                return {
                    "success": True,
                    "r2_key": r2_result["r2_key"],
                    "public_url": r2_result["public_url"],
                    "image_metadata": {
                        "size": openai_response["size"],
                        "quality": openai_response["quality"],
                        "format": openai_response["output_format"],
                        "file_size": len(image_bytes),
                        "generated_with": self.model,
                        "created_at": datetime.utcnow().isoformat(),
                        "style_preference": style_preference,
                        "color_palette": color_palette if color_palette else "default"
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"R2 storage failed: {r2_result.get('error', 'Unknown error')}"
                }
                
        except Exception as e:
            print(f"❌ \033[94m[ImageGenerationAgent]\033[0m \033[1m\033[91mError: {str(e)}\033[0m")
            return {
                "success": False,
                "error": f"Image generation process failed: {str(e)}"
            }
    
    def _generate_dynamic_color_palette(self, course_name: str, course_description: str, style: str) -> Dict[str, Any]:
        """Generate dynamic color palette based on course content and style - LLM will determine colors"""
        
        # Detect course subject from name and description for context
        text_to_analyze = f"{course_name} {course_description}".lower()
        detected_subject = self._detect_course_subject(text_to_analyze)
        
        # Return palette structure that will be filled by LLM
        return {
            'subject_theme': detected_subject,
            'color_temperature': self._determine_color_temperature(style),
            'contrast_level': self._determine_contrast_level(style),
            'llm_determined': True  # Flag to indicate LLM should choose colors
        }
    
    def _detect_course_subject(self, text_to_analyze: str) -> str:
        """Detect course subject from text for context (no hardcoded colors)"""
        
        # Define subject keywords for detection only
        subject_keywords = {
            'technology': ['technology', 'tech', 'software', 'computer', 'digital', 'cyber', 'system'],
            'programming': ['programming', 'coding', 'development', 'python', 'javascript', 'java', 'code'],
            'ai_ml': ['artificial intelligence', 'machine learning', 'ai', 'ml', 'neural', 'deep learning'],
            'data_science': ['data', 'analytics', 'statistics', 'database', 'big data', 'analysis'],
            'business': ['business', 'management', 'strategy', 'leadership', 'entrepreneurship'],
            'finance': ['finance', 'accounting', 'investment', 'money', 'economics', 'trading'],
            'marketing': ['marketing', 'advertising', 'branding', 'social media', 'promotion'],
            'design': ['design', 'graphic', 'ui', 'ux', 'visual', 'creative'],
            'art': ['art', 'drawing', 'painting', 'creative', 'artistic', 'illustration'],
            'photography': ['photography', 'photo', 'camera', 'visual', 'image'],
            'health': ['health', 'fitness', 'wellness', 'nutrition', 'medical'],
            'science': ['science', 'physics', 'chemistry', 'biology', 'research'],
            'medicine': ['medicine', 'medical', 'healthcare', 'clinical', 'therapy'],
            'education': ['education', 'teaching', 'learning', 'academic', 'school'],
            'language': ['language', 'english', 'spanish', 'communication', 'linguistics'],
            'literature': ['literature', 'writing', 'books', 'poetry', 'reading']
        }
        
        # Detect subject based on keywords
        for subject, keywords in subject_keywords.items():
            if any(keyword in text_to_analyze for keyword in keywords):
                return subject
        
        return 'general'
    
    def _determine_color_temperature(self, style: str) -> str:
        """Determine color temperature based on style"""
        temperature_map = {
            'professional_educational': 'balanced',
            'modern': 'cool',
            'colorful': 'warm',
            'minimalist': 'neutral',
            'tech_focused': 'cool'
        }
        return temperature_map.get(style, 'balanced')
    
    def _determine_contrast_level(self, style: str) -> str:
        """Determine contrast level based on style"""
        contrast_map = {
            'professional_educational': 'medium',
            'modern': 'high',
            'colorful': 'high',
            'minimalist': 'low',
            'tech_focused': 'high'
        }
        return contrast_map.get(style, 'medium')

    async def _create_course_image_prompt(self, image_name: str, image_description: str, style: str, color_palette: Optional[Dict[str, Any]] = None, image_type: str = "cover", calling_agent: str = None, context: Dict[str, Any] = None) -> str:
        """Create detailed prompt for course image generation (covers, slides, etc.)"""
        
        # HYBRID LOGIC: Preserve existing behavior for Course Creation Agent, dynamic for others
        if calling_agent == "course_creation_agent":
            # PRESERVE EXISTING HARDCODED BEHAVIOR for Course Creation Agent
            return await self._create_legacy_course_image_prompt(image_name, image_description, style, color_palette, image_type)
        else:
            # DYNAMIC BEHAVIOR for all other agents
            return await self._create_dynamic_course_image_prompt(image_name, image_description, style, color_palette, image_type, context)
    
    async def _create_legacy_course_image_prompt(self, image_name: str, image_description: str, style: str, color_palette: Optional[Dict[str, Any]] = None, image_type: str = "cover") -> str:
        """Create legacy hardcoded prompt for course creation agent (preserves existing behavior)"""
        
        # Dynamic prompt based on image type
        if image_type == "slide":
            base_prompt = f"""Create a professional, educational slide image for: "{image_name}"

SLIDE-SPECIFIC DESIGN REQUIREMENTS:
- Clean, presentation-ready design optimized for educational content delivery
- Clear visual hierarchy that supports learning objectives
- 3:2 widescreen format (1536x1024) optimized for presentations and digital displays
- High contrast elements for excellent readability in various lighting conditions
- Focused composition that doesn't distract from content overlay
- Suitable for both standalone viewing and as part of a presentation sequence

SLIDE VISUAL COMPOSITION:
- Generous white space for text and content overlay
- Clear focal areas that guide attention
- Professional background that enhances rather than competes with content
- Consistent visual language suitable for educational presentations
- Avoid overly decorative elements that might distract from learning content

EDUCATIONAL SLIDE REQUIREMENTS:
- Support for text overlay and content placement
- Visual elements that reinforce learning concepts
- Professional appearance suitable for academic or corporate training
- Scalable design that works in presentation software and online platforms"""
        
        elif image_type == "thumbnail":
            base_prompt = f"""Create a compelling thumbnail image for: "{image_name}"

THUMBNAIL-SPECIFIC DESIGN REQUIREMENTS:
- Eye-catching design optimized for small display sizes
- Bold, clear visual elements that remain recognizable when scaled down
- 3:2 widescreen format (1536x1024) that works well as thumbnails
- High contrast and strong visual impact for course discovery
- Instantly recognizable subject matter representation
- Optimized for course catalogs, search results, and grid layouts

THUMBNAIL VISUAL COMPOSITION:
- Strong focal point that draws immediate attention
- Simplified design elements that scale well
- Bold typography consideration for title overlay
- Clear subject matter representation
- Avoid fine details that disappear at small sizes"""
        
        else:  # Default to cover image
            base_prompt = f"""Create a professional, modern course cover image for: "{image_name}"

COVER IMAGE DESIGN REQUIREMENTS:
- Professional educational aesthetic suitable for online learning platforms
- Clean, modern design with high visual impact
- 3:2 widescreen format (1536x1024) optimized for modern course banners and hero images
- High contrast elements for excellent readability across devices
- Engaging and inspiring visual composition that attracts learners
- Scalable design that works at different sizes (thumbnail to full display)

COVER VISUAL COMPOSITION:
- Balanced layout with clear focal points
- Strategic use of white space for clean appearance
- Professional typography consideration (space for course title overlay)
- Modern flat design or subtle gradients
- Avoid cluttered or overly complex designs"""

        # Add common specifications for all image types
        base_prompt += f"""

STYLE PREFERENCE: {style}

TECHNICAL SPECIFICATIONS:
- High resolution (1536x1024) with crisp, clean details in 3:2 widescreen format
- Professional lighting and smooth gradients
- Clean edges and polished finish
- Optimized for digital display across platforms and modern layouts
- Consistent with modern educational design trends and widescreen presentation formats

VISUAL ELEMENTS TO INCLUDE:
- Relevant icons, symbols, or illustrations related to the topic
- Abstract or geometric elements that complement the subject matter
- Subtle textures or patterns if they enhance the design
- Modern, contemporary visual language"""

        # Add dynamic color specifications if palette is provided
        if color_palette and color_palette.get('llm_determined'):
            base_prompt += f"""

INTELLIGENT COLOR SELECTION:
- Subject Theme: {color_palette['subject_theme']} (choose colors that best represent this subject area)
- Color Temperature: {color_palette['color_temperature']} (overall warmth/coolness of the design)
- Contrast Level: {color_palette['contrast_level']} (how bold the color contrasts should be)

COLOR SELECTION GUIDELINES:
- Analyze the course name and description to determine the most appropriate colors
- Choose a primary color that best represents the subject matter and evokes the right emotions
- Select a complementary secondary color that works harmoniously with the primary
- Add 2-3 accent colors that enhance the overall design without overwhelming it
- Consider color psychology: what colors would make learners feel engaged and motivated for this topic?
- Ensure colors work well together and maintain professional appearance
- Use colors that would appeal to the target audience for this course
- Maintain accessibility with proper contrast ratios
- Create visual hierarchy through strategic color placement

SUBJECT-SPECIFIC COLOR CONSIDERATIONS:
- For technology/programming: Consider modern, innovative colors that suggest precision and growth
- For business/finance: Use professional, trustworthy colors that convey stability and success
- For creative/design: Choose inspiring, artistic colors that spark creativity
- For health/wellness: Select calming, natural colors that promote well-being
- For science/research: Use colors that suggest discovery, analysis, and knowledge
- For education/teaching: Pick colors that are engaging yet professional for learning environments"""
        else:
            base_prompt += """

INTELLIGENT COLOR SELECTION:
- Analyze the course name and description to determine the most appropriate colors
- Choose colors that best represent the subject matter and evoke the right emotions
- Use a harmonious color palette with 2-4 complementary colors
- Consider color psychology: what colors would make learners feel engaged and motivated for this topic?
- Professional color scheme appropriate for educational content
- Ensure colors work well together and maintain accessibility standards"""

        # Add image-specific context if description provided
        if image_description:
            base_prompt += f"""

CONTENT CONTEXT AND FOCUS:
{image_description}

CONTENT-SPECIFIC VISUAL ELEMENTS:
- Incorporate visual metaphors and symbols that directly relate to the content
- Use imagery that reflects the key concepts and objectives
- Include visual elements that would resonate with the target audience
- Ensure the design communicates the content's value proposition visually
- Create visual hierarchy that emphasizes the most important aspects"""
        
        # Add style-specific instructions
        style_instructions = {
            "professional_educational": """
PROFESSIONAL EDUCATIONAL STYLE:
- Use academic and professional color schemes (greens, blues, grays, yellows, oranges, purples)
- Incorporate clean lines and structured layouts
- Include educational iconography (books, graduation caps, lightbulbs, etc.)
- Maintain formal yet approachable aesthetic
- Use typography-friendly layouts with clear hierarchy""",
            
            "modern": """
MODERN CONTEMPORARY STYLE:
- Use contemporary design elements and current design trends
- Incorporate dynamic gradients and modern color palettes
- Include geometric shapes and abstract elements
- Use bold, confident visual language
- Emphasize innovation and forward-thinking concepts""",
            
            "colorful": """
VIBRANT COLORFUL STYLE:
- Use bright, energetic color combinations
- Incorporate dynamic visual elements and patterns
- Create engaging, eye-catching compositions
- Maintain professional quality while being visually exciting
- Use color psychology to convey enthusiasm and engagement""",
            
            "minimalist": """
MINIMALIST CLEAN STYLE:
- Use simple, clean design with lots of white space
- Employ minimal color palette (2-3 colors maximum)
- Focus on essential elements only
- Use subtle, elegant visual elements
- Emphasize clarity and simplicity in all design choices""",
            
            "tech_focused": """
TECHNOLOGY-FOCUSED STYLE:
- Use modern tech-inspired color schemes (dark themes, neon accents)
- Incorporate digital elements, circuits, code snippets, or tech icons
- Use futuristic design elements and clean geometric shapes
- Emphasize innovation and cutting-edge technology
- Include subtle tech patterns or grid systems"""
        }
        
        if style in style_instructions:
            base_prompt += style_instructions[style]
        
        # Add final quality assurance instructions
        base_prompt += """

QUALITY ASSURANCE:
- Ensure all elements are properly aligned and balanced
- Verify color contrast meets accessibility standards
- Confirm the design works effectively at thumbnail size
- Check that the overall composition is visually appealing and professional
- Ensure the design accurately represents the course content and target audience"""
        
        return base_prompt
    
    async def _create_dynamic_course_image_prompt(self, image_name: str, image_description: str, style: str, color_palette: Optional[Dict[str, Any]] = None, image_type: str = "cover", context: Dict[str, Any] = None) -> str:
        """Create dynamic AI-powered prompt for non-course-creation agents"""
        
        try:
            print(f"🤖 \033[94m[ImageGenerationAgent]\033[0m \033[1mGenerating dynamic prompt for: {image_name}\033[0m")
            
            # Use AI to analyze the image request and generate optimal prompt prefix
            analysis_prompt = f"""You are an expert image generation prompt creator. Analyze this image request and create the optimal prompt prefix for AI image generation.

IMAGE REQUEST ANALYSIS:
- Image Name: {image_name}
- Image Description: {image_description}
- Image Type: {image_type}
- Style Preference: {style}
- Context: {context if context else 'No additional context'}

Your task is to determine what type of visual would be most effective and create the appropriate prompt prefix.

AVAILABLE VISUAL TYPES:
- Technical diagram: For explaining processes, systems, architectures
- Infographic: For presenting data, comparisons, key points
- Illustration: For concepts, ideas, abstract topics  
- Process flow: For step-by-step procedures, workflows
- Concept visualization: For abstract ideas, theories
- Educational diagram: For learning materials, explanations
- System architecture: For technical systems, frameworks
- Comparison chart: For comparing options, features
- Timeline: For historical progression, roadmaps
- Mind map: For interconnected concepts

PROMPT PREFIX EXAMPLES:
- "Create a technical diagram illustrating"
- "Create an educational infographic showing"
- "Create a process flow diagram depicting"
- "Create a concept visualization of"
- "Create a system architecture diagram for"
- "Create an illustration representing"
- "Create a comparison infographic between"

ANALYSIS GUIDELINES:
1. Consider the image name and description to understand the content
2. Determine what visual format would best serve the educational purpose
3. Choose a prompt prefix that will generate the most effective visual aid
4. Consider the target audience and learning objectives

Respond with ONLY the optimal prompt prefix (ending with the image name in quotes):
Example: Create a technical diagram illustrating: "{image_name}"
"""

            # Use AI to generate the optimal prompt prefix
            messages = [
                {"role": "system", "content": "You are an expert visual communication and prompt engineering specialist."},
                {"role": "user", "content": analysis_prompt}
            ]
            
            response = await self.openai.create_chat_completion(
                model="gpt-4o-mini",  # Use a fast model for prompt generation
                messages=messages,
                max_tokens=100,
                temperature=0.3
            )
            
            dynamic_prefix = response.choices[0].message.content.strip()
            
            # Clean up the response to ensure it's just the prefix
            if dynamic_prefix.startswith('"') and dynamic_prefix.endswith('"'):
                dynamic_prefix = dynamic_prefix[1:-1]
            
            print(f"🤖 \033[94m[ImageGenerationAgent]\033[0m AI generated prefix: '{dynamic_prefix}'")
            
            # Build the complete dynamic prompt
            base_prompt = f"""{dynamic_prefix}

DYNAMIC IMAGE DESIGN REQUIREMENTS:
- Professional educational aesthetic optimized for learning and comprehension
- Clear, modern design with high visual impact and educational value
- 3:2 widescreen format (1536x1024) optimized for digital learning platforms
- High contrast elements for excellent readability across devices and contexts
- Engaging and informative visual composition that enhances understanding
- Scalable design that works at different sizes and viewing contexts

EDUCATIONAL VISUAL COMPOSITION:
- Clear visual hierarchy that guides attention to key information
- Strategic use of white space for clean, uncluttered appearance
- Professional design language appropriate for educational content
- Visual elements that directly support learning objectives
- Avoid decorative elements that distract from educational content

CONTENT-SPECIFIC DESIGN ELEMENTS:
- Incorporate visual metaphors and symbols that directly relate to the subject matter
- Use imagery and graphics that clarify and reinforce key concepts
- Include visual elements that would resonate with learners
- Ensure the design communicates information clearly and effectively
- Create visual hierarchy that emphasizes the most important educational points"""

            # Add style preference
            base_prompt += f"""

STYLE PREFERENCE: {style}

TECHNICAL SPECIFICATIONS:
- High resolution (1536x1024) with crisp, clean details in 3:2 widescreen format
- Professional lighting and smooth gradients optimized for educational content
- Clean edges and polished finish suitable for learning materials
- Optimized for digital display across educational platforms and devices
- Consistent with modern educational design trends and accessibility standards"""

            # Add dynamic color specifications if palette is provided
            if color_palette and color_palette.get('llm_determined'):
                base_prompt += f"""

INTELLIGENT COLOR SELECTION:
- Subject Theme: {color_palette['subject_theme']} (choose colors that best represent this subject area)
- Color Temperature: {color_palette['color_temperature']} (overall warmth/coolness of the design)
- Contrast Level: {color_palette['contrast_level']} (how bold the color contrasts should be)

DYNAMIC COLOR GUIDELINES:
- Analyze the content to determine the most appropriate and effective colors
- Choose colors that enhance comprehension and engagement with the material
- Use color psychology to support learning objectives and content retention
- Ensure colors work harmoniously and maintain professional educational appearance
- Maintain accessibility with proper contrast ratios for all learners
- Create visual hierarchy through strategic and purposeful color placement"""
            else:
                base_prompt += """

INTELLIGENT COLOR SELECTION:
- Analyze the content and context to determine the most appropriate colors
- Choose colors that enhance learning and comprehension of the material
- Use a harmonious color palette that supports educational objectives
- Consider color psychology to improve engagement and information retention
- Professional color scheme appropriate for educational and learning content
- Ensure colors work well together and maintain accessibility standards"""

            # Add content-specific context if description provided
            if image_description:
                base_prompt += f"""

CONTENT CONTEXT AND EDUCATIONAL FOCUS:
{image_description}

CONTENT-SPECIFIC VISUAL ELEMENTS:
- Incorporate visual metaphors and symbols that directly relate to the educational content
- Use imagery that reflects the key learning concepts and objectives
- Include visual elements that would enhance understanding for the target audience
- Ensure the design communicates the educational value proposition clearly
- Create visual hierarchy that emphasizes the most important learning points
- Support comprehension through clear, purposeful visual design choices"""

            # Add style-specific instructions (same as legacy but adapted for dynamic content)
            style_instructions = {
                "professional_educational": """

PROFESSIONAL EDUCATIONAL STYLE:
- Use academic and professional color schemes that support learning
- Incorporate clean lines and structured layouts that enhance comprehension
- Include educational iconography and symbols that clarify concepts
- Maintain formal yet approachable aesthetic suitable for diverse learners
- Use typography-friendly layouts with clear hierarchy for information processing""",
                
                "modern": """

MODERN CONTEMPORARY STYLE:
- Use contemporary design elements and current visual trends
- Incorporate dynamic gradients and modern color palettes that engage learners
- Include geometric shapes and abstract elements that support content
- Use bold, confident visual language that inspires learning
- Emphasize innovation and forward-thinking educational approaches""",
                
                "colorful": """

VIBRANT COLORFUL STYLE:
- Use bright, energetic color combinations that motivate learning
- Incorporate dynamic visual elements and patterns that enhance engagement
- Create engaging, eye-catching compositions that capture attention
- Maintain educational quality while being visually stimulating
- Use color psychology to convey enthusiasm and learning excitement""",
                
                "minimalist": """

MINIMALIST CLEAN STYLE:
- Use simple, clean design with lots of white space for focus
- Employ minimal color palette (2-3 colors maximum) for clarity
- Focus on essential educational elements only
- Use subtle, elegant visual elements that don't distract from learning
- Emphasize clarity and simplicity in all educational design choices""",
                
                "tech_focused": """

TECHNOLOGY-FOCUSED STYLE:
- Use modern tech-inspired color schemes appropriate for technical content
- Incorporate digital elements, diagrams, or tech-related visual metaphors
- Use futuristic design elements and clean geometric shapes
- Emphasize innovation and cutting-edge technological concepts
- Include subtle tech patterns or grid systems that support technical learning"""
            }
            
            if style in style_instructions:
                base_prompt += style_instructions[style]
            
            # Add final quality assurance instructions
            base_prompt += """

EDUCATIONAL QUALITY ASSURANCE:
- Ensure all visual elements support learning objectives and comprehension
- Verify color contrast meets accessibility standards for all learners
- Confirm the design effectively communicates educational content
- Check that the overall composition enhances rather than hinders learning
- Ensure the design accurately represents and supports the educational content"""
            
            return base_prompt
            
        except Exception as e:
            print(f"❌ \033[94m[ImageGenerationAgent]\033[0m Error generating dynamic prompt: {e}")
            # Fallback to a generic educational prompt
            return f"""Create an educational visual for: "{image_name}"

EDUCATIONAL DESIGN REQUIREMENTS:
- Professional educational aesthetic suitable for learning platforms
- Clear, modern design with high visual impact
- 3:2 widescreen format (1536x1024) optimized for educational content
- High contrast elements for excellent readability
- Engaging visual composition that supports learning

{f"CONTENT CONTEXT: {image_description}" if image_description else ""}

STYLE PREFERENCE: {style}

Create a visual that enhances understanding and supports educational objectives."""

    async def generate_image(self, course_id: str, image_name: str,
                           image_description: str = "", 
                           image_type: str = "cover",
                           filename: str = None,
                           style_preference: str = "professional_educational",
                           dynamic_colors: bool = True,
                           calling_agent: str = None,
                           context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate and store any type of course image (cover, slide, thumbnail, etc.)
        
        Args:
            course_id: Database course ID
            image_name: Image title/name (e.g., "Machine Learning Fundamentals" or "Slide 1: Introduction")
            image_description: Optional image description for context
            image_type: Type of image (cover, slide, thumbnail, etc.)
            filename: Base filename (without extension) - auto-generated if not provided
            style_preference: Style hint (professional_educational, modern, colorful, etc.)
            dynamic_colors: Whether to use dynamic color palette generation
        
        Returns:
            {
                "success": bool,
                "images": dict,
                "image_type": str,
                "image_metadata": dict,
                "error": str (if failed)
            }
        """
        
        try:
            print(f"\n🎨 \033[94m[ImageGenerationAgent]\033[0m \033[1mGenerating {image_type} image for: {image_name}\033[0m")
            
            # Auto-generate filename if not provided
            if not filename:
                filename = f"{image_type}_image"
            
            # Step 1: Generate dynamic color palette if enabled
            color_palette = None
            if dynamic_colors:
                color_palette = self._generate_dynamic_color_palette(image_name, image_description, style_preference)
            
            # Step 2: Create detailed prompt based on image context and type
            prompt = await self._create_course_image_prompt(image_name, image_description, style_preference, color_palette, image_type, calling_agent, context)
            
            # Step 3: Generate image using OpenAI gpt-image-1
            openai_response = await self.openai.generate_image(
                prompt=prompt,
                model=self.model,
                size="1536x1024",  # 3:2 aspect ratio (closest to 16:9 available)
                quality="medium",
                output_format="png",
                background="auto"
            )
            
            if not openai_response["success"]:
                return {
                    "success": False,
                    "error": f"Image generation failed: {openai_response.get('error', 'Unknown error')}"
                }
            
            # Step 4: Extract and decode base64 data
            base64_data = openai_response["data"][0]["b64_json"]
            image_bytes = base64.b64decode(base64_data)
            
            print(f"📏 \033[94m[ImageGenerationAgent]\033[0m Image generated: {len(image_bytes)} bytes")
            
            # Step 5: Upload to R2 storage using the generic multi-size method
            full_filename = f"{filename}.{openai_response['output_format']}"
            content_type = f"image/{openai_response['output_format']}"
            
            # Generate multiple sizes
            image_sizes = self._generate_multiple_sizes(image_bytes)
            
            r2_result = await self.r2_storage.upload_images_multi_size(
                course_id=course_id,
                large_image=image_sizes['large'],
                medium_image=image_sizes.get('medium', image_sizes['large']),
                small_image=image_sizes.get('small', image_sizes['large']),
                filename=full_filename,
                image_type=image_type,
                content_type=content_type
            )
            
            if r2_result["success"]:
                print(f"✅ \033[94m[ImageGenerationAgent]\033[0m \033[1m\033[92m{image_type.title()} image generated and stored successfully\033[0m")
                
                return {
                    "success": True,
                    "images": r2_result["images"],
                    "image_type": image_type,
                    "image_metadata": {
                        "size": openai_response["size"],
                        "quality": openai_response["quality"],
                        "format": openai_response["output_format"],
                        "generated_with": self.model,
                        "created_at": datetime.utcnow().isoformat(),
                        "style_preference": style_preference,
                        "color_palette": color_palette if color_palette else "default",
                        "image_type": image_type
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"R2 storage failed: {r2_result.get('error', 'Unknown error')}"
                }
                
        except Exception as e:
            print(f"❌ \033[94m[ImageGenerationAgent]\033[0m \033[1m\033[91mError: {str(e)}\033[0m")
            return {
                "success": False,
                "error": f"{image_type.title()} image generation process failed: {str(e)}"
            }

    async def regenerate_course_cover_image(self, course_id: str, course_name: str, 
                                           course_description: str = "", 
                                           style_preference: str = "professional_educational",
                                           dynamic_colors: bool = True,
                                           delete_previous: bool = True) -> Dict[str, Any]:
        """
        Regenerate course cover image with potentially different style
        
        Args:
            course_id: Database course ID
            course_name: Course title
            course_description: Optional course description
            style_preference: New style preference
            delete_previous: Whether to delete the previous image
        
        Returns:
            Same format as generate_course_cover_image
        """
        
        # Delete previous image if requested
        if delete_previous:
            try:
                await self.r2_storage.delete_course_cover_image(course_id, "cover_image.png")
                await self.r2_storage.delete_course_cover_image(course_id, "cover_image.jpeg")
                await self.r2_storage.delete_course_cover_image(course_id, "cover_image.webp")
            except Exception as e:
                print(f"Warning: Could not delete previous cover image: {e}")
        
        # Generate new image
        return await self.generate_course_cover_image(
            course_id, course_name, course_description, style_preference, dynamic_colors
        )
    
    async def get_supported_styles(self) -> Dict[str, str]:
        """Get list of supported style preferences with descriptions"""
        return {
            "professional_educational": "Clean, academic design with professional colors and educational iconography",
            "modern": "Contemporary design with current trends, gradients, and geometric elements",
            "colorful": "Vibrant, energetic design with bright colors while maintaining professionalism",
            "minimalist": "Simple, clean design with lots of white space and minimal color palette",
            "tech_focused": "Technology-inspired design with modern tech elements and futuristic aesthetics"
        }

    async def get_supported_image_types(self) -> Dict[str, str]:
        """Get list of supported image types with descriptions"""
        return {
            "cover": "Course cover images for banners, hero sections, and main course representation",
            "slide": "Presentation slide backgrounds optimized for content overlay and educational delivery",
            "thumbnail": "Small preview images optimized for course catalogs and grid layouts",
            "banner": "Wide banner images for promotional and header use",
            "icon": "Icon-style images for compact representation and navigation"
        }
    
    async def preview_color_palette(self, course_name: str, course_description: str = "", style: str = "professional_educational") -> Dict[str, Any]:
        """Preview the color palette context that would be provided to the LLM"""
        color_palette = self._generate_dynamic_color_palette(course_name, course_description, style)
        
        return {
            "course_name": course_name,
            "detected_subject": color_palette['subject_theme'],
            "style": style,
            "llm_color_guidance": {
                "subject_theme": color_palette['subject_theme'],
                "color_temperature": color_palette['color_temperature'],
                "contrast_level": color_palette['contrast_level'],
                "llm_determined": color_palette['llm_determined']
            },
            "color_selection_approach": "LLM will analyze course content and choose appropriate colors based on subject matter, style preferences, and color psychology"
        }
    
    # Multi-Size Image Generation Methods
    def _resize_image(self, image_bytes: bytes, target_size: Tuple[int, int], quality: int = 85) -> bytes:
        """
        Resize image to target size while maintaining quality
        
        Args:
            image_bytes: Original image bytes
            target_size: Target (width, height) tuple
            quality: JPEG quality (1-100), ignored for PNG
            
        Returns:
            Resized image bytes
        """
        try:
            # Open image from bytes
            image = Image.open(BytesIO(image_bytes))
            
            # Resize with high-quality resampling
            resized_image = image.resize(target_size, Image.Resampling.LANCZOS)
            
            # Save to bytes
            output_buffer = BytesIO()
            
            # Determine format from original image
            original_format = image.format or 'PNG'
            
            if original_format.upper() == 'PNG':
                # For PNG, maintain transparency and use optimization
                resized_image.save(output_buffer, format='PNG', optimize=True)
            else:
                # For JPEG and other formats
                resized_image.save(output_buffer, format=original_format, quality=quality, optimize=True)
            
            return output_buffer.getvalue()
            
        except Exception as e:
            print(f"❌ Error resizing image to {target_size}: {str(e)}")
            raise e
    
    def _generate_multiple_sizes(self, original_image_bytes: bytes) -> Dict[str, bytes]:
        """
        Generate multiple sizes from original image
        
        Args:
            original_image_bytes: Original large image bytes
            
        Returns:
            Dictionary with size names as keys and image bytes as values
        """
        try:
            print(f"🔄 \033[94m[ImageGenerationAgent]\033[0m \033[1mGenerating multiple image sizes...\033[0m")
            
            # Define size configurations
            size_configs = {
                'large': (1536, 1024),   # Original size (L)
                'medium': (768, 512),    # 50% scale (M)
                'small': (384, 256)      # 25% scale (S)
            }
            
            sizes = {}
            
            # Large size is the original
            sizes['large'] = original_image_bytes
            print(f"   📏 LARGE: \033[93m1536x1024 ({len(original_image_bytes)} bytes)\033[0m")
            
            # Generate medium and small sizes
            for size_name, (width, height) in size_configs.items():
                if size_name == 'large':
                    continue  # Already handled
                
                try:
                    resized_bytes = self._resize_image(original_image_bytes, (width, height), quality=90)
                    sizes[size_name] = resized_bytes
                    print(f"   📏 {size_name.upper()}: \033[93m{width}x{height} ({len(resized_bytes)} bytes)\033[0m")
                    
                except Exception as e:
                    print(f"❌ Failed to generate {size_name} size: {str(e)}")
                    # Continue with other sizes even if one fails
            
            print(f"✅ \033[94m[ImageGenerationAgent]\033[0m \033[1m\033[92mGenerated {len(sizes)} image sizes\033[0m")
            return sizes
            
        except Exception as e:
            print(f"❌ \033[94m[ImageGenerationAgent]\033[0m \033[1m\033[91mError generating multiple sizes: {str(e)}\033[0m")
            raise e
    
    async def generate_course_cover_image_multi_size(self, course_id: str, course_name: str, 
                                                   course_description: str = "", 
                                                   style_preference: str = "professional_educational",
                                                   dynamic_colors: bool = True) -> Dict[str, Any]:
        """
        Generate and store course cover image in multiple sizes (L, M, S)
        
        Args:
            course_id: Database course ID
            course_name: Course title (e.g., "Machine Learning Fundamentals")
            course_description: Optional course description for context
            style_preference: Style hint (professional_educational, modern, colorful, etc.)
            dynamic_colors: Whether to use dynamic color palette generation
        
        Returns:
            {
                "success": bool,
                "images": {
                    "large": {"r2_key": str, "public_url": str, "size": str, "file_size": int},
                    "medium": {"r2_key": str, "public_url": str, "size": str, "file_size": int},
                    "small": {"r2_key": str, "public_url": str, "size": str, "file_size": int}
                },
                "image_metadata": dict,
                "error": str (if failed)
            }
        """
        return await self.generate_image_multi_size(
            course_id=course_id,
            image_name=course_name,
            image_description=course_description,
            image_type="cover",
            filename="cover_image",
            style_preference=style_preference,
            dynamic_colors=dynamic_colors
        )
    
    async def generate_image_multi_size(self, course_id: str, image_name: str, 
                                      image_description: str = "", 
                                      image_type: str = "cover",
                                      filename: str = "image",
                                      style_preference: str = "professional_educational",
                                      dynamic_colors: bool = True) -> Dict[str, Any]:
        """
        Generate and store course image in multiple sizes (L, M, S) with configurable type
        
        Args:
            course_id: Database course ID
            image_name: Image title/name (e.g., "Machine Learning Fundamentals" or "Slide 1: Introduction")
            image_description: Optional image description for context
            image_type: Type of image (cover, slide, etc.) - affects storage path
            filename: Base filename (without extension)
            style_preference: Style hint (professional_educational, modern, colorful, etc.)
            dynamic_colors: Whether to use dynamic color palette generation
        
        Returns:
            {
                "success": bool,
                "images": {
                    "large": {"r2_key": str, "public_url": str, "size": str, "file_size": int},
                    "medium": {"r2_key": str, "public_url": str, "size": str, "file_size": int},
                    "small": {"r2_key": str, "public_url": str, "size": str, "file_size": int}
                },
                "image_metadata": dict,
                "error": str (if failed)
            }
        """
        
        try:
            print(f"\n🎨 \033[94m[ImageGenerationAgent]\033[0m \033[1mGenerating {image_type} image (multi-size) for: {image_name}\033[0m")
            
            # Step 1: Generate dynamic color palette if enabled
            color_palette = None
            if dynamic_colors:
                color_palette = self._generate_dynamic_color_palette(image_name, image_description, style_preference)
            
            # Step 2: Create detailed prompt based on image context and type
            prompt = await self._create_course_image_prompt(image_name, image_description, style_preference, color_palette, image_type)
            
            # Step 3: Generate image using OpenAI gpt-image-1
            openai_response = await self.openai.generate_image(
                prompt=prompt,
                model=self.model,
                size="1536x1024",  # 3:2 aspect ratio (closest to 16:9 available)
                quality="medium",
                output_format="png",
                background="auto"
            )
            
            if not openai_response["success"]:
                return {
                    "success": False,
                    "error": f"Image generation failed: {openai_response.get('error', 'Unknown error')}"
                }
            
            # Step 4: Extract and decode base64 data
            base64_data = openai_response["data"][0]["b64_json"]
            image_bytes = base64.b64decode(base64_data)
            
            print(f"📏 \033[94m[ImageGenerationAgent]\033[0m Image generated: {len(image_bytes)} bytes")
            
            # Step 5: Generate multiple sizes
            image_sizes = self._generate_multiple_sizes(image_bytes)
            
            # Step 6: Upload to R2 storage using multi-size method
            full_filename = f"{filename}.{openai_response['output_format']}"
            content_type = f"image/{openai_response['output_format']}"
            
            r2_result = await self.r2_storage.upload_images_multi_size(
                course_id=course_id,
                large_image=image_sizes['large'],
                medium_image=image_sizes.get('medium', image_sizes['large']),
                small_image=image_sizes.get('small', image_sizes['large']),
                filename=full_filename,
                image_type=image_type,
                content_type=content_type
            )
            
            if r2_result["success"]:
                print(f"✅ \033[94m[ImageGenerationAgent]\033[0m \033[1m\033[92m{image_type.title()} image (multi-size) generated and stored successfully\033[0m")
                
                return {
                    "success": True,
                    "images": r2_result["images"],
                    "image_metadata": {
                        "size": openai_response["size"],
                        "quality": openai_response["quality"],
                        "format": openai_response["output_format"],
                        "generated_with": self.model,
                        "created_at": datetime.utcnow().isoformat(),
                        "style_preference": style_preference,
                        "color_palette": color_palette if color_palette else "default",
                        "image_type": image_type
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"R2 storage failed: {r2_result.get('error', 'Unknown error')}"
                }
                
        except Exception as e:
            print(f"❌ \033[94m[ImageGenerationAgent]\033[0m \033[1m\033[91mError: {str(e)}\033[0m")
            return {
                "success": False,
                "error": f"{image_type.title()} image (multi-size) generation process failed: {str(e)}"
            }
    
    async def get_image_size_info(self) -> Dict[str, Any]:
        """Get information about available image sizes"""
        return {
            "available_sizes": {
                "large": {
                    "dimensions": "1536x1024",
                    "description": "Original high-resolution image for detailed viewing and printing",
                    "use_cases": ["Hero banners", "Full-screen displays", "Print materials"]
                },
                "medium": {
                    "dimensions": "768x512", 
                    "description": "Medium resolution for web display and thumbnails",
                    "use_cases": ["Course cards", "Grid layouts", "Mobile displays"]
                },
                "small": {
                    "dimensions": "384x256",
                    "description": "Small resolution for icons and compact displays", 
                    "use_cases": ["Navigation icons", "List items", "Quick previews"]
                }
            },
            "aspect_ratio": "3:2 (widescreen)",
            "format": "PNG with optimization",
            "quality": "High-quality with LANCZOS resampling"
        }
