import re
import json
import html
import unicodedata
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from bson import ObjectId

from ...infrastructure.ai.openai_service import OpenAIService
from ...infrastructure.database.database_service import DatabaseService
from ..services.message_service import MessageService
from ..services.context_service import ContextService
from ...infrastructure.storage.r2_storage import R2StorageService
from ...models import ContentMaterial


class MaterialContentGeneratorAgent:
    """Agent specialized in generating detailed study material content for course slides"""
    
    def __init__(self, openai_service: OpenAIService, database_service: DatabaseService,
                 message_service: MessageService, context_service: ContextService,
                 r2_storage_service: R2StorageService, image_generation_agent=None):
        self.openai = openai_service
        self.db = database_service
        self.messages = message_service
        self.context = context_service
        self.storage = r2_storage_service
        self.image_agent = image_generation_agent
        self.model = "gpt-4o-mini"
    
    def get_function_definitions(self) -> List[Dict[str, Any]]:
        """Define functions that this agent can call"""
        return [
            {
                "name": "start_content_generation",
                "description": "Start the content generation process for materials with content_status='not done'",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {
                            "type": "string",
                            "description": "The ID of the course"
                        }
                    },
                    "required": ["course_id"]
                }
            },
            {
                "name": "generate_slide_content",
                "description": "Generate detailed study material content for a specific slide using a valid MongoDB ObjectId (24-character hex string). Only use this when you have a confirmed material ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "material_id": {
                            "type": "string",
                            "description": "The MongoDB ObjectId (24-character hex string) of the content material to generate content for"
                        }
                    },
                    "required": ["material_id"]
                }
            },
            {
                "name": "generate_specific_slide_content",
                "description": "Generate content for a specific slide by natural language description. Use this when the user provides slide titles, descriptions, or natural language references (e.g., 'Generate content for material Slide 3: The Future of AI-Native Businesses', 'slide 1 of chapter 1.1', 'assessment 2 of module 2', 'AI-Native Landscape Value Assessment')",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {
                            "type": "string",
                            "description": "The ID of the course"
                        },
                        "slide_description": {
                            "type": "string",
                            "description": "Natural language description of the slide/material to target (e.g., 'Slide 3: The Future of AI-Native Businesses', 'AI-Native Landscape Value Assessment', 'slide 1 of chapter 1.1', 'assessment on management skills', 'first slide of module 2')"
                        }
                    },
                    "required": ["course_id", "slide_description"]
                }
            },
            {
                "name": "edit_specific_slide_content",
                "description": "Edit/modify content for a specific slide by natural language description",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {
                            "type": "string",
                            "description": "The ID of the course"
                        },
                        "slide_description": {
                            "type": "string",
                            "description": "Natural language description of the slide/material to edit (e.g., 'slide 1 of chapter 1.1', 'assessment on management skills')"
                        },
                        "modification_request": {
                            "type": "string",
                            "description": "What changes to make to the content"
                        }
                    },
                    "required": ["course_id", "slide_description", "modification_request"]
                }
            },
            {
                "name": "edit_slide_content_targeted",
                "description": "Make targeted edits to specific slide content via natural language with diff preview",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {
                            "type": "string",
                            "description": "The ID of the course"
                        },
                        "slide_reference": {
                            "type": "string",
                            "description": "Natural language slide reference (e.g., 'slide 1 module 1 chapter 1', 'current slide', 'first slide')"
                        },
                        "edit_instruction": {
                            "type": "string",
                            "description": "What to edit (e.g., 'change title to X', 'add paragraph about Y', 'modify section Z')"
                        },
                        "current_slide_id": {
                            "type": "string",
                            "description": "Optional: ID of currently selected slide for 'current slide' references"
                        }
                    },
                    "required": ["course_id", "slide_reference", "edit_instruction"]
                }
            },
            {
                "name": "apply_targeted_edit",
                "description": "Apply approved targeted edit changes to slide content",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "material_id": {
                            "type": "string",
                            "description": "The ID of the material to apply changes to"
                        },
                        "approved": {
                            "type": "boolean",
                            "description": "Whether the targeted edit is approved"
                        },
                        "modified_content": {
                            "type": "string",
                            "description": "The modified content to apply (if approved)"
                        }
                    },
                    "required": ["material_id", "approved"]
                }
            },
            {
                "name": "find_slide_by_description",
                "description": "Find and list slides/materials matching a natural language description",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {
                            "type": "string",
                            "description": "The ID of the course"
                        },
                        "search_description": {
                            "type": "string",
                            "description": "Natural language description to search for (e.g., 'slides about management', 'chapter 1 materials', 'assessments')"
                        }
                    },
                    "required": ["course_id", "search_description"]
                }
            },
            {
                "name": "approve_content",
                "description": "Approve the generated content and move to next slide",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "material_id": {
                            "type": "string",
                            "description": "The ID of the content material to approve"
                        },
                        "approved": {
                            "type": "boolean",
                            "description": "Whether the content is approved"
                        }
                    },
                    "required": ["material_id", "approved"]
                }
            },
            {
                "name": "modify_content",
                "description": "Modify content based on user feedback",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "material_id": {
                            "type": "string",
                            "description": "The ID of the content material to modify"
                        },
                        "modification_request": {
                            "type": "string",
                            "description": "User's modification request"
                        }
                    },
                    "required": ["material_id", "modification_request"]
                }
            }
        ]
    
    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        """Generate system prompt for content generation"""
        course = context.get("course_state")
        course_id = context.get('current_course_id', '')
        
        return f"""You are a specialized content generation assistant for educational materials.

IMPORTANT: When calling functions, always use the EXACT course_id parameter that was passed to you in the conversation context. The course_id is: {course_id}

Your primary responsibility is to generate detailed, comprehensive study material content for course slides that students can use for self-study.

CONTENT GENERATION PRINCIPLES:
1. **Comprehensive Coverage**: Create detailed content that thoroughly explains concepts
2. **Multi-level Formatting**: Use headers, subheaders, bullet points, code blocks, quotes, tables
3. **Self-Study Friendly**: Content should be complete enough for independent learning
4. **Engaging and Clear**: Use examples, analogies, and real-world applications
5. **Structured Learning**: Include key takeaways, practice questions, and summaries

CONTENT STRUCTURE REQUIREMENTS:
- Start with clear learning objectives
- Provide comprehensive explanations with examples
- Include practical applications and case studies
- Add self-check questions for understanding
- End with key takeaways and next steps
- Use proper markdown formatting throughout

IMAGE INTEGRATION:
- When content would benefit from visual explanation, request image generation
- Provide clear image descriptions and placement instructions
- Integrate images seamlessly into the content flow

QUALITY STANDARDS:
- Content should be detailed (minimum 800-1200 words for slides)
- Use professional yet accessible language
- Include relevant examples and case studies
- Provide actionable insights and practical applications
- Ensure content aligns with the slide's pedagogy strategy

🛠️ AVAILABLE FUNCTIONS:
- start_content_generation: Begin processing materials with content_status="not done"
- generate_slide_content: Create detailed content for a specific slide using a MongoDB ObjectId (24-character hex string)
- generate_specific_slide_content: Create content for a slide using natural language description (e.g., slide titles, descriptions)
- edit_slide_content_targeted: Make targeted edits to existing slide content with diff preview (e.g., "add image", "modify title", "change paragraph")
- approve_content: Mark content as approved and move to next slide
- modify_content: Revise content based on user feedback

FUNCTION SELECTION GUIDELINES:
- Use edit_slide_content_targeted for ANY modification requests to existing content (e.g., "add image", "modify title", "change paragraph", "add section", "include", "insert")
- Use generate_specific_slide_content ONLY when creating completely new content from scratch or when user explicitly says "generate" or "create"
- Use generate_slide_content only when you have a confirmed MongoDB ObjectId (24-character hex string)
- CRITICAL: If user mentions "add", "modify", "change", "edit", "update", "include", "insert", "append" to existing content, ALWAYS use edit_slide_content_targeted
- CRITICAL: Phrases like "for the same slide, can you add..." or "add an image to..." are EDIT requests, not generation requests

Focus on creating high-quality educational content that enables effective self-study and deep learning."""
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools including function tools"""
        tools = []
        
        # Add function tools
        for func_def in self.get_function_definitions():
            tools.append({
                "type": "function",
                "name": func_def["name"],
                "description": func_def["description"],
                "parameters": func_def["parameters"]
            })
        
        return tools

    async def process_message(self, course_id: Optional[str], user_id: str, user_message: str) -> Dict[str, Any]:
        """Process a user message for content generation"""
        
        # Store user message if course exists
        if course_id:
            await self.messages.store_message(course_id, user_id, user_message, "user")
        
        # Get conversation context
        context = await self.context.build_context_for_agent(course_id, user_id)
        
        # Build system instructions and input for Responses API
        system_instructions = self.get_system_prompt(context)
        messages = self.messages.build_openai_messages(context, user_message, system_instructions)
        
        # Convert messages to Responses API input format
        input_messages = self.openai.convert_messages_to_input(messages)
        
        # Get AI response with function calling
        try:
            print(f"\n{'='*60}")
            print(f"🎨 \033[95m[MaterialContentGeneratorAgent]\033[0m \033[1mSending request to Responses API...\033[0m")
            print(f"   📝 Model: \033[93m{self.model}\033[0m")
            print(f"   📝 User Message: \033[92m'{user_message}'\033[0m")
            print(f"   🔧 Tools available: \033[93m{len(self.get_all_tools())}\033[0m")
            print(f"{'='*60}")
            
            # Use Responses API with function calling
            response = await self.openai.create_response(
                model=self.model,
                input=input_messages,
                instructions=system_instructions,
                tools=self.get_all_tools()
            )
            
            print(f"\n✅ \033[95m[MaterialContentGeneratorAgent]\033[0m \033[1m\033[92mResponses API Response received\033[0m")
            
            # Process response output
            function_results = {}
            assistant_content = ""
            
            # Process all output items
            for item in response.output:
                if item.type == "function_call":
                    # Handle function calls
                    function_name = item.name
                    function_args = json.loads(item.arguments)
                    
                    print(f"🔧 [MaterialContentGeneratorAgent] Processing function call: {function_name}")
                    
                    if function_name == "start_content_generation":
                        result = await self._start_content_generation(function_args["course_id"])
                        function_results["content_generation_started"] = result
                    elif function_name == "generate_slide_content":
                        result = await self._generate_slide_content(function_args["material_id"])
                        function_results["slide_content_generated"] = result
                    elif function_name == "generate_specific_slide_content":
                        result = await self._generate_specific_slide_content(
                            function_args["course_id"],
                            function_args["slide_description"]
                        )
                        function_results["specific_slide_generated"] = result
                    elif function_name == "edit_specific_slide_content":
                        # REDIRECT to targeted editing for diff preview
                        print(f"🔄 [MaterialContentGeneratorAgent] Redirecting edit_specific_slide_content to targeted editing for diff preview")
                        result = await self._edit_slide_content_targeted(
                            function_args["course_id"],
                            function_args["slide_description"],
                            function_args["modification_request"],
                            None  # current_slide_id
                        )
                        function_results["slide_content_edited_targeted"] = result
                    elif function_name == "find_slide_by_description":
                        result = await self._find_slide_by_description(
                            function_args["course_id"],
                            function_args["search_description"]
                        )
                        function_results["slides_found"] = result
                    elif function_name == "approve_content":
                        result = await self._approve_content(
                            function_args["material_id"],
                            function_args["approved"]
                        )
                        function_results["content_approved"] = result
                    elif function_name == "modify_content":
                        result = await self._modify_content(
                            function_args["material_id"],
                            function_args["modification_request"]
                        )
                        function_results["content_modified"] = result
                    elif function_name == "edit_slide_content_targeted":
                        result = await self._edit_slide_content_targeted(
                            function_args["course_id"],
                            function_args["slide_reference"],
                            function_args["edit_instruction"],
                            function_args.get("current_slide_id")
                        )
                        function_results["slide_content_edited_targeted"] = result
                    elif function_name == "apply_targeted_edit":
                        result = await self._apply_targeted_edit(
                            function_args["material_id"],
                            function_args["approved"],
                            function_args.get("modified_content")
                        )
                        function_results["targeted_edit_applied"] = result
                
                elif item.type == "message":
                    # Handle assistant message content
                    if hasattr(item, 'content') and item.content:
                        for content_item in item.content:
                            if hasattr(content_item, 'text'):
                                assistant_content += content_item.text
            
            # Generate final response based on function results
            ai_response = await self._generate_response_with_context(assistant_content, function_results)
            
            # Store AI response
            if course_id:
                await self.messages.store_message(course_id, user_id, ai_response, "assistant", function_results)
            
            return {
                "response": ai_response,
                "course_id": course_id,
                "function_results": function_results
            }
            
        except Exception as e:
            import traceback
            print(f"MaterialContentGeneratorAgent Responses API error: {e}")
            print(f"Full traceback: {traceback.format_exc()}")
            return {
                "response": "I apologize, but I'm experiencing some technical difficulties with content generation. Please try again in a moment.",
                "course_id": course_id,
                "function_results": {},
                "error": str(e)
            }
    
    async def _start_content_generation(self, course_id: str) -> Dict[str, Any]:
        """Start the content generation process"""
        try:
            print(f"🚀 [MaterialContentGeneratorAgent] Starting content generation for course {course_id}")
            
            # Validate course_id format
            if not self._is_valid_object_id(course_id):
                return {"success": False, "error": f"Invalid course ID format: '{course_id}'"}
            
            # Get course info
            course = await self.db.find_course(course_id)
            if not course:
                return {"success": False, "error": "Course not found"}
            
            # Check if structure is approved
            if not course.get("structure_approved", False):
                return {"success": False, "error": "Course structure must be approved before content generation"}
            
            # Get next material to process
            next_material = await self._get_next_material_to_process(course_id)
            
            if not next_material:
                return {
                    "success": True,
                    "message": "All materials have been processed",
                    "completed": True
                }
            
            # Update course workflow step
            await self.db.update_document("courses", course_id, {
                "workflow_step": "content_generation",
                "content_generation_started": True,
                "content_generation_started_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
            
            # Auto-generate content for the first material immediately
            print(f"🚀 [MaterialContentGeneratorAgent] Auto-generating content for first material: {next_material['title']}")
            
            # Generate content for the first material
            generation_result = await self._generate_slide_content(str(next_material["_id"]))
            
            if generation_result["success"]:
                # Get the generated material data
                generated_material = generation_result.get("material", {})
                return {
                    "success": True,
                    "next_material": {
                        "id": str(next_material["_id"]),
                        "title": next_material["title"],
                        "module_number": next_material["module_number"],
                        "chapter_number": next_material["chapter_number"],
                        "material_type": next_material["material_type"],
                        "slide_number": next_material.get("slide_number", 1)
                    },
                    "message": "Content generation started and first slide generated",
                    "auto_generate": True,  # Signal that auto-generation occurred
                    "first_slide_generated": True,
                    "generated_material": generated_material  # Pass the full material data
                }
            else:
                # If first slide generation failed, still return success but with error info
                return {
                    "success": True,
                    "next_material": {
                        "id": str(next_material["_id"]),
                        "title": next_material["title"],
                        "module_number": next_material["module_number"],
                        "chapter_number": next_material["chapter_number"],
                        "material_type": next_material["material_type"]
                    },
                    "message": "Content generation started but first slide generation failed",
                    "auto_generate": True,
                    "first_slide_generated": False,
                    "generation_error": generation_result.get("error", "Unknown error")
                }
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error starting content generation: {e}")
            return {"success": False, "error": f"Failed to start content generation: {str(e)}"}
    
    async def _get_next_material_to_process(self, course_id: str) -> Optional[Dict[str, Any]]:
        """Get the next material that needs content generation - STRICT chapter by chapter (slides then assessments)"""
        try:
            db = await self.db.get_database()
            
            # CRITICAL FIX: Use a simple, direct query to find the next material in proper sequence
            # This ensures we get materials in the exact order they should be processed
            next_material = await db.content_materials.find_one(
                {
                    "course_id": ObjectId(course_id),
                    "content_status": "not done"
                },
            sort=[
                ("module_number", 1),
                ("chapter_number", 1),
                ("material_type", -1),  # This ensures slides come before assessments (reverse alphabetical: "slide" before "assessment")
                ("slide_number", 1)
            ]
            )
            
            if next_material:
                print(f"📝 [MaterialContentGeneratorAgent] Next material found: {next_material['title']}")
                print(f"   Type: {next_material['material_type']}")
                print(f"   Location: Module {next_material['module_number']}, Chapter {next_material['chapter_number']}")
                if next_material.get('slide_number'):
                    print(f"   Slide: {next_material['slide_number']}")
                print(f"   Status: {next_material.get('content_status', 'unknown')}")
                return next_material
            else:
                print(f"✅ [MaterialContentGeneratorAgent] No more materials to process - all complete!")
                return None
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error getting next material: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return None
    
    async def _get_current_material_to_approve(self) -> Optional[Dict[str, Any]]:
        """Auto-detect the current material that should be approved"""
        try:
            db = await self.db.get_database()
            
            # Strategy 1: Find the most recently completed material (likely the one just generated)
            recent_completed = await db.content_materials.find_one(
                {"content_status": "completed"},
                sort=[("updated_at", -1)]  # Most recently updated
            )
            
            if recent_completed:
                print(f"🔍 [MaterialContentGeneratorAgent] Found recent completed material: {recent_completed['title']}")
                return recent_completed
            
            # Strategy 2: Find any material that has content but isn't approved yet
            content_ready = await db.content_materials.find_one(
                {
                    "content_status": "completed",
                    "status": {"$ne": "approved"}  # Not yet approved
                },
                sort=[
                    ("module_number", 1),
                    ("chapter_number", 1),
                    ("slide_number", 1)
                ]
            )
            
            if content_ready:
                print(f"🔍 [MaterialContentGeneratorAgent] Found content ready for approval: {content_ready['title']}")
                return content_ready
            
            # Strategy 3: Find the most recently updated material (fallback)
            recent_material = await db.content_materials.find_one(
                {},
                sort=[("updated_at", -1)]
            )
            
            if recent_material:
                print(f"🔍 [MaterialContentGeneratorAgent] Fallback to most recent material: {recent_material['title']}")
                return recent_material
            
            print(f"⚠️ [MaterialContentGeneratorAgent] No materials found for auto-detection")
            return None
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error auto-detecting current material: {e}")
            return None
    
    async def _generate_slide_content(self, material_id: str) -> Dict[str, Any]:
        """Generate detailed content for a specific slide"""
        try:
            print(f"📝 [MaterialContentGeneratorAgent] Generating content for material {material_id}")
            
            # Validate material_id format
            if not self._is_valid_object_id(material_id):
                return {"success": False, "error": f"Invalid material ID format: '{material_id}'"}
            
            # Get material details
            db = await self.db.get_database()
            material = await db.content_materials.find_one({"_id": ObjectId(material_id)})
            
            if not material:
                return {"success": False, "error": "Material not found"}
            
            # CRITICAL FIX: Enhanced check for existing content to prevent duplicate generation
            if material.get("content_status") == "completed" and material.get("content"):
                print(f"✅ [MaterialContentGeneratorAgent] Content already exists for {material['title']}, returning existing content without regeneration")
                
                # Return existing content without regenerating
                existing_content = material["content"]
                
                # Check if it's an assessment
                is_assessment = material.get('material_type') == 'assessment' or material.get('assessment_format')
                
                # Send streaming events to maintain frontend consistency
                await self._send_streaming_event({
                    "type": "material_content_start",
                    "material_id": material_id,
                    "title": material["title"],
                    "file_path": self._get_material_file_path(material),
                    "display_path": f"Module {material['module_number']}/Chapter {material['chapter_number']}/Slide {material.get('slide_number', 1)}.md",
                    "slide_number": material.get('slide_number', 1),
                    "message": f"Content already exists for {material['title']}"
                })
                
                await self._send_streaming_event({
                    "type": "material_content_stream",
                    "material_id": material_id,
                    "file_path": self._get_material_file_path(material),
                    "display_path": f"Module {material['module_number']}/Chapter {material['chapter_number']}/Slide {material.get('slide_number', 1)}.md",
                    "content": existing_content,
                    "content_length": len(existing_content),
                    "message": f"Using existing content ({len(existing_content):,} characters)"
                })
                
                # Prepare completion event data
                completion_event = {
                    "type": "material_content_complete",
                    "material_id": material_id,
                    "title": material["title"],
                    "file_path": self._get_material_file_path(material),
                    "display_path": f"Module {material['module_number']}/Chapter {material['chapter_number']}/Slide {material.get('slide_number', 1)}.md",
                    "content": existing_content,
                    "content_length": len(existing_content),
                    "has_images": False,  # Could be enhanced to detect images in existing content
                    "message": f"Existing content loaded for {material['title']}"
                }
                
                # Only include R2 data for non-assessment materials
                if not is_assessment and material.get("public_url"):
                    completion_event["r2_key"] = material.get("r2_key")
                    completion_event["public_url"] = material.get("public_url")
                
                await self._send_streaming_event(completion_event)
                
                result_data = {
                    "success": True,
                    "material": {
                        "id": material_id,
                        "title": material["title"],
                        "content": existing_content,
                        "content_length": len(existing_content),
                        "has_images": False,  # Could be enhanced to detect images in existing content
                        "material_type": material.get('material_type', 'slide')
                    },
                    "preview_ready": True,
                    "content_already_exists": True
                }
                
                # Only include R2 data for non-assessment materials
                if not is_assessment and material.get("public_url"):
                    result_data["material"]["r2_key"] = material.get("r2_key")
                    result_data["material"]["public_url"] = material.get("public_url")
                
                return result_data
            
            # Send content generation start event with proper file path
            file_path = self._get_material_file_path(material)
            await self._send_streaming_event({
                "type": "material_content_start",
                "material_id": material_id,
                "title": material["title"],
                "material_type": material["material_type"],
                "module_number": material["module_number"],
                "chapter_number": material["chapter_number"],
                "slide_number": material.get("slide_number", 1),
                "file_path": file_path,
                "display_path": f"Module {material['module_number']}/Chapter {material['chapter_number']}/{material['title']}",
                "message": f"Starting content generation for {material['title']}"
            })
            
            # CRITICAL: Send a separate event to trigger file selection in frontend
            await self._send_streaming_event({
                "type": "select_file",
                "file_path": file_path,
                "material_id": material_id,
                "title": material["title"],
                "module_number": material["module_number"],
                "chapter_number": material["chapter_number"],
                "slide_number": material.get("slide_number", 1)
            })
            
            # Update status to generating
            await db.content_materials.update_one(
                {"_id": ObjectId(material_id)},
                {
                    "$set": {
                        "content_status": "generating",
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Get course context for content generation
            course = await self.db.find_course(str(material["course_id"]))
            if not course:
                return {"success": False, "error": "Course not found"}
            
            # Get course design content for context
            course_design_content = ""
            if course.get("course_design_r2_key"):
                course_design_content = await self.storage.get_course_design_content(course["course_design_r2_key"])
            
            # Send progress event
            await self._send_streaming_event({
                "type": "material_content_progress",
                "material_id": material_id,
                "file_path": self._get_material_file_path(material),
                "message": "Generating comprehensive study material content...",
                "stage": "ai_generation"
            })
            
            # Generate content using AI
            content_result = await self._generate_ai_content(material, course, course_design_content)
            
            if not content_result["success"]:
                # Send error event
                await self._send_streaming_event({
                    "type": "material_content_error",
                    "material_id": material_id,
                    "file_path": self._get_material_file_path(material),
                    "error_message": content_result.get("error", "Content generation failed"),
                    "message": f"Failed to generate content: {content_result.get('error', 'Unknown error')}"
                })
                
                # Update status back to not done on failure
                await db.content_materials.update_one(
                    {"_id": ObjectId(material_id)},
                    {
                        "$set": {
                            "content_status": "not done",
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                return content_result
            
            generated_content = content_result["content"]
            
            # Send content streaming event
            await self._send_streaming_event({
                "type": "material_content_stream",
                "material_id": material_id,
                "file_path": self._get_material_file_path(material),
                "content": generated_content,
                "content_length": len(generated_content),
                "message": f"Generated {len(generated_content):,} characters of content"
            })
            
            # Check if content needs images
            image_requests = self._analyze_content_for_images(generated_content, material)
            
            # Generate images if needed
            if image_requests and self.image_agent:
                await self._send_streaming_event({
                    "type": "material_content_progress",
                    "material_id": material_id,
                    "file_path": self._get_material_file_path(material),
                    "message": f"Generating {len(image_requests)} images for enhanced content...",
                    "stage": "image_generation"
                })
                
                enhanced_content = await self._generate_and_integrate_images(
                    generated_content, image_requests, material, course
                )
                generated_content = enhanced_content
            
            # Store generated content with assessment data if applicable
            update_data = {
                "content": generated_content,
                "content_status": "completed",
                "updated_at": datetime.utcnow()
            }
            
            # Check if this is an assessment - assessments should NOT be stored in R2
            is_assessment = material.get('material_type') == 'assessment' or content_result.get("assessment_format")
            
            if is_assessment:
                print(f"📊 [MaterialContentGeneratorAgent] Storing assessment data in database (no R2 storage):")
                print(f"   - Format: {content_result['assessment_format']}")
                print(f"   - Question difficulty: {content_result.get('question_difficulty', 'intermediate')}")
                print(f"   - Assessment data keys: {list(content_result['assessment_data'].keys()) if content_result.get('assessment_data') else 'None'}")
                
                update_data["assessment_format"] = content_result["assessment_format"]
                update_data["assessment_data"] = content_result["assessment_data"]
                update_data["question_difficulty"] = content_result.get("question_difficulty", "intermediate")
                
                # Extract learning objective from assessment data
                if content_result.get("assessment_data") and isinstance(content_result["assessment_data"], dict):
                    learning_objective = content_result["assessment_data"].get("learning_objective", material.get("description", material["title"]))
                else:
                    learning_objective = material.get("description", material["title"])
                
                update_data["learning_objective"] = learning_objective[:200] if learning_objective else material["title"]
                
                print(f"   - Learning objective: {update_data['learning_objective']}")
                
                # For assessments, don't store in R2 - only update database
                print(f"💾 [MaterialContentGeneratorAgent] Updating database with {len(update_data)} fields")
                result = await db.content_materials.update_one(
                    {"_id": ObjectId(material_id)},
                    {"$set": update_data}
                )
                print(f"💾 [MaterialContentGeneratorAgent] Database update result: matched={result.matched_count}, modified={result.modified_count}")
                
                # No R2 storage for assessments
                r2_result = {"success": False, "skip_r2": True}
                
            else:
                # For slides and other content, store in R2
                await self._send_streaming_event({
                    "type": "material_content_progress",
                    "material_id": material_id,
                    "file_path": self._get_material_file_path(material),
                    "message": "Storing content in cloud storage...",
                    "stage": "storage"
                })
                
                print(f"💾 [MaterialContentGeneratorAgent] Updating database with {len(update_data)} fields")
                result = await db.content_materials.update_one(
                    {"_id": ObjectId(material_id)},
                    {"$set": update_data}
                )
                print(f"💾 [MaterialContentGeneratorAgent] Database update result: matched={result.matched_count}, modified={result.modified_count}")
                
                # Store content in R2 storage as markdown file
                r2_result = await self._store_content_in_r2(material, generated_content, course)
                
                if r2_result["success"]:
                    await db.content_materials.update_one(
                        {"_id": ObjectId(material_id)},
                        {
                            "$set": {
                                "r2_key": r2_result["r2_key"],
                                "public_url": r2_result["public_url"],
                                "updated_at": datetime.utcnow()
                            }
                        }
                    )
            
            # Send completion event - different handling for assessments vs slides
            completion_event = {
                "type": "material_content_complete",
                "material_id": material_id,
                "title": material["title"],
                "file_path": self._get_material_file_path(material),
                "content": generated_content,
                "content_length": len(generated_content),
                "has_images": len(image_requests) > 0 if image_requests else False,
                "message": f"Content generation completed for {material['title']}"
            }
            
            # Only include R2 data for non-assessment materials
            if not is_assessment and r2_result.get("success"):
                completion_event["r2_key"] = r2_result["r2_key"]
                completion_event["public_url"] = r2_result["public_url"]
            
            await self._send_streaming_event(completion_event)
            
            print(f"✅ [MaterialContentGeneratorAgent] Content generated successfully for {material['title']}")
            
            # Return result - different data for assessments vs slides
            result_data = {
                "success": True,
                "material": {
                    "id": material_id,
                    "title": material["title"],
                    "content": generated_content,
                    "content_length": len(generated_content),
                    "has_images": len(image_requests) > 0 if image_requests else False,
                    "material_type": material.get('material_type', 'slide')
                },
                "preview_ready": True
            }
            
            # Only include R2 data for non-assessment materials
            if not is_assessment and r2_result.get("success"):
                result_data["material"]["r2_key"] = r2_result["r2_key"]
                result_data["material"]["public_url"] = r2_result["public_url"]
            
            return result_data
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error generating slide content: {e}")
            return {"success": False, "error": f"Failed to generate content: {str(e)}"}
    
    async def _generate_ai_content(self, material: Dict[str, Any], course: Dict[str, Any], course_design_content: str) -> Dict[str, Any]:
        """Generate content using AI based on material details and course context - supports both slides and assessments"""
        try:
            # Check material type and route to appropriate generation method
            material_type = material.get('material_type', 'slide')
            
            if material_type == 'assessment':
                return await self._generate_assessment_content(material, course, course_design_content)
            else:
                return await self._generate_slide_content_ai(material, course, course_design_content)
                
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] AI content generation error: {e}")
            return {"success": False, "error": f"AI content generation failed: {str(e)}"}
    
    async def _generate_slide_content_ai(self, material: Dict[str, Any], course: Dict[str, Any], course_design_content: str) -> Dict[str, Any]:
        """Generate slide content using the existing storytelling approach"""
        try:
            # Extract pedagogy strategy from material description or course design
            pedagogy_strategy = self._extract_pedagogy_strategy(material, course_design_content)
            
            # Use the existing master prompt for storytelling-focused content generation
            system_prompt = f"""You are an expert instructional designer and storyteller.  
Your task is to take a slide title and description and turn them into a **student-friendly article or blog-style study material in Markdown**.  

### Goals
- The output should read like a **connected article**, not disjointed notes.  
- Learners should be able to study it as a **self-contained narrative** that explains, illustrates, and reflects on the topic.  
- Use a **storytelling flow**:  
  - Hook (open with context or a relatable scenario)  
  - Build (explain concepts, compare, show examples, offer visuals if useful)  
  - Close (reflection, takeaways, or call to action)  

### Formatting & Style
- Write in a **clear, engaging, supportive tone**.  
- Keep paragraphs short for readability.  
- Use **varied formats** only where they naturally fit:  
  - **Tables** → comparisons, scenarios, pros/cons  
  - **Numbered lists** → step-by-step processes, frameworks  
  - **Bulleted lists** → key concepts, best practices, pitfalls  
  - **Blockquotes** → reflection prompts, definitions, key insights  
  - **Callout boxes/admonitions** → tips 💡, warnings ⚠️, highlights 🔑  
  - **Emojis/icons** → to lighten tone or emphasize key points (✅, 🚀, 🔍)  
  - **Code blocks / pseudo-syntax** → mnemonics, formulas, acronyms  
  - **Mini-diagrams (ASCII art)** → simple flows, pyramids, cycles  
  - **Side-by-side tables** → not just comparisons but storytelling contrasts  
  -** Seperate each section with dividers ---
  - **Inline Image** → if a visual helps, describe it **inline** with a keyword prefix:  

    ```
    #image {{Imagine a visual where two people are talking: one leans forward with open body language, while thought bubbles above capture the other's feelings being reflected back. A minimalist flat illustration would make this vivid.}}
    ```  

- Never create a separate "Visual Aid" heading. Integrate image prompts into the flow.  
- Only add image when they **directly clarify or strengthen** the content.  

### Content Elements (adapt dynamically)
Include only the elements that fit the given slide description. Possible elements include:  
- Introduction / Why this matters  
- Core explanation of the concept  
- Comparisons (tables or lists)  
- Example or story (to ground abstract ideas)  
- Practical guidance (steps, tips, or applications)  
- Reflection prompt(s) or activity  
- Inline visual suggestion (`#image {{}}` format, only if necessary)  
- Key takeaway(s) or closing message  

### Output
- Return the material in **Markdown format**.  
- Structure it like a **blog article with smooth transitions**.  
- The outcome should feel **natural, engaging, and learner-friendly**, with formatting used dynamically for emphasis and readability.

### Context for This Content
- **Slide Title**: "{material['title']}"
- **Material Type**: {material['material_type']}
- **Course Context**: {course.get('name', 'Unknown Course')} - Module {material['module_number']}, Chapter {material['chapter_number']}
- **Description**: {material.get('description', 'No specific description provided')}
- **Pedagogy Strategy**: {pedagogy_strategy}

Create engaging, story-driven study material that students will actually want to read and learn from."""

            user_prompt = f"""Create a student-friendly, blog-style study material for the slide: "{material['title']}"

**Material Details:**
- **Title:** {material['title']}
- **Description:** {material.get('description', 'No specific description provided')}
- **Material Type:** {material['material_type']}
- **Course Context:** {course.get('name', 'Unknown Course')} - Module {material['module_number']}, Chapter {material['chapter_number']}

Transform this into an engaging narrative that:
- Opens with a relatable hook or scenario
- Builds understanding through clear explanations and examples  
- Closes with meaningful takeaways or reflection

Make it feel like a connected article that students can study as a self-contained piece. Use storytelling techniques to make the content memorable and engaging.

Focus on creating content that reads naturally and keeps students interested throughout their learning journey."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await self.openai.create_chat_completion(
                model=self.model,
                messages=messages,
                max_tokens=4000  # Allow for comprehensive content
            )
            
            generated_content = response.choices[0].message.content.strip()
            
            if generated_content:
                # Clean and decode the content to fix HTML entities and encoding issues
                cleaned_content = self._clean_content(generated_content)
                print(f"✅ [MaterialContentGeneratorAgent] AI generated {len(cleaned_content)} characters of slide content")
                return {"success": True, "content": cleaned_content}
            else:
                return {"success": False, "error": "AI generated empty slide content"}
                
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Slide content generation error: {e}")
            return {"success": False, "error": f"Slide content generation failed: {str(e)}"}
    
    async def _generate_assessment_content(self, material: Dict[str, Any], course: Dict[str, Any], course_design_content: str) -> Dict[str, Any]:
        """Generate dynamic assessment content with optimal format selection"""
        try:
            print(f"🎯 [MaterialContentGeneratorAgent] Generating dynamic assessment for: {material['title']}")
            
            # Extract context for assessment generation
            pedagogy_strategy = self._extract_pedagogy_strategy(material, course_design_content)
            learning_objective = material.get('description', '')
            
            # Step 1: Determine optimal assessment format using AI
            format_result = await self._determine_assessment_format(material, pedagogy_strategy, learning_objective)
            
            if not format_result["success"]:
                return format_result
            
            assessment_format = format_result["format"]
            print(f"🎯 [MaterialContentGeneratorAgent] Selected assessment format: {assessment_format}")
            
            # Step 2: Generate question content in the selected format
            question_result = await self._generate_assessment_question(
                material, course, pedagogy_strategy, learning_objective, assessment_format
            )
            
            if not question_result["success"]:
                return question_result
            
            # Step 3: Structure the assessment data
            assessment_data = {
                "type": "assessment",
                "format": assessment_format,
                "question": question_result["question"],
                "difficulty": question_result.get("difficulty", "intermediate"),
                "learning_objective": learning_objective[:200] if learning_objective else material['title']
            }
            
            # Store structured data in the material record
            print(f"✅ [MaterialContentGeneratorAgent] Generated {assessment_format} assessment with structured data")
            
            # CRITICAL FIX: Store assessment data as JSON string for ContentMaterialResponse compatibility
            # The content field must be a string, not a dictionary
            import json
            return {
                "success": True,
                "content": json.dumps(assessment_data),  # Store as JSON string for Pydantic validation
                "assessment_format": assessment_format,
                "assessment_data": assessment_data,  # Keep structured data for database storage
                "question_difficulty": question_result.get("difficulty", "intermediate")
            }
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Assessment content generation error: {e}")
            return {"success": False, "error": f"Assessment content generation failed: {str(e)}"}
    
    async def _determine_assessment_format(self, material: Dict[str, Any], pedagogy_strategy: str, learning_objective: str) -> Dict[str, Any]:
        """Use AI to determine the optimal assessment format for the material"""
        try:
            print(f"🤖 [MaterialContentGeneratorAgent] Determining optimal assessment format for: {material['title']}")
            
            system_prompt = f"""You are an assessment design expert. Analyze the material and choose the BEST assessment format.

MATERIAL ANALYSIS:
- Title: {material['title']}
- Description: {material.get('description', 'No description provided')}
- Learning Objective: {learning_objective}
- Pedagogy Strategy: {pedagogy_strategy}
- Course Context: Module {material['module_number']}, Chapter {material['chapter_number']}

AVAILABLE ASSESSMENT FORMATS:
1. **multiple_choice** - Best for: concept understanding, definitions, best practices, factual knowledge
2. **true_false** - Best for: fact verification, principle validation, simple concept checks
3. **scenario_choice** - Best for: application of concepts, decision-making, real-world situations
4. **matching** - Best for: relationships, categories, processes, terminology connections
5. **fill_in_blank** - Best for: terminology, formulas, key phrases, specific facts
6. **ranking** - Best for: priorities, sequences, hierarchies, process steps

FORMAT SELECTION CRITERIA:
- **Conceptual content** → multiple_choice or true_false
- **Process/procedure content** → ranking or fill_in_blank  
- **Application content** → scenario_choice
- **Relationship content** → matching
- **Factual content** → true_false or fill_in_blank
- **Decision-making content** → scenario_choice
- **Sequential content** → ranking

PEDAGOGY ALIGNMENT:
- Interactive/hands-on → scenario_choice or multiple_choice
- Case study approach → scenario_choice
- Lecture-based → multiple_choice or true_false
- Problem-based → scenario_choice or ranking

RESPONSE FORMAT (JSON only):
{{
    "success": true,
    "format": "selected_format",
    "reasoning": "Brief explanation of why this format is optimal",
    "difficulty": "beginner|intermediate|advanced"
}}"""

            user_prompt = f"Analyze the material '{material['title']}' and select the optimal assessment format. Consider the learning objective: '{learning_objective}' and pedagogy: '{pedagogy_strategy}'"

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await self.openai.create_chat_completion(
                model=self.model,
                messages=messages,
                max_tokens=500,
                temperature=0.1  # Low temperature for consistent format selection
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Clean up response if it has markdown formatting
            if ai_response.startswith('```json'):
                ai_response = ai_response.replace('```json', '').replace('```', '').strip()
            elif ai_response.startswith('```'):
                ai_response = ai_response.replace('```', '').strip()
            
            # Parse AI response
            try:
                format_result = json.loads(ai_response)
                
                if format_result.get("success") and format_result.get("format"):
                    print(f"✅ [MaterialContentGeneratorAgent] AI selected format: {format_result['format']} - {format_result.get('reasoning', 'No reasoning provided')}")
                    return format_result
                else:
                    # Fallback to default format selection
                    return self._fallback_format_selection(material, pedagogy_strategy, learning_objective)
                    
            except json.JSONDecodeError:
                print(f"❌ [MaterialContentGeneratorAgent] Failed to parse AI format selection response")
                return self._fallback_format_selection(material, pedagogy_strategy, learning_objective)
                
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error determining assessment format: {e}")
            return self._fallback_format_selection(material, pedagogy_strategy, learning_objective)
    
    def _fallback_format_selection(self, material: Dict[str, Any], pedagogy_strategy: str, learning_objective: str) -> Dict[str, Any]:
        """Fallback format selection when AI fails"""
        try:
            title_lower = material['title'].lower()
            desc_lower = material.get('description', '').lower()
            objective_lower = learning_objective.lower()
            pedagogy_lower = pedagogy_strategy.lower()
            
            combined_text = f"{title_lower} {desc_lower} {objective_lower} {pedagogy_lower}"
            
            # Rule-based format selection
            if any(keyword in combined_text for keyword in ['scenario', 'situation', 'case', 'decision', 'choose', 'action']):
                return {"success": True, "format": "scenario_choice", "reasoning": "Content involves decision-making or scenarios", "difficulty": "intermediate"}
            elif any(keyword in combined_text for keyword in ['match', 'connect', 'relationship', 'pair', 'associate']):
                return {"success": True, "format": "matching", "reasoning": "Content involves relationships or connections", "difficulty": "intermediate"}
            elif any(keyword in combined_text for keyword in ['sequence', 'order', 'priority', 'rank', 'step', 'process']):
                return {"success": True, "format": "ranking", "reasoning": "Content involves sequences or priorities", "difficulty": "intermediate"}
            elif any(keyword in combined_text for keyword in ['true', 'false', 'correct', 'incorrect', 'fact', 'statement']):
                return {"success": True, "format": "true_false", "reasoning": "Content suitable for fact verification", "difficulty": "beginner"}
            elif any(keyword in combined_text for keyword in ['fill', 'complete', 'blank', 'term', 'definition']):
                return {"success": True, "format": "fill_in_blank", "reasoning": "Content involves terminology or completion", "difficulty": "intermediate"}
            else:
                # Default to multiple choice
                return {"success": True, "format": "multiple_choice", "reasoning": "Default format for concept understanding", "difficulty": "intermediate"}
                
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error in fallback format selection: {e}")
            return {"success": True, "format": "multiple_choice", "reasoning": "Fallback default format", "difficulty": "intermediate"}
    
    async def _generate_assessment_question(self, material: Dict[str, Any], course: Dict[str, Any], 
                                          pedagogy_strategy: str, learning_objective: str, assessment_format: str) -> Dict[str, Any]:
        """Generate a single assessment question in the specified format"""
        try:
            print(f"📝 [MaterialContentGeneratorAgent] Generating {assessment_format} question for: {material['title']}")
            
            # Get format-specific prompt
            format_prompt = self._get_format_specific_prompt(assessment_format)
            
            system_prompt = f"""You are an expert assessment designer creating a single high-quality question.

ASSESSMENT REQUIREMENTS:
- Format: {assessment_format}
- Material: {material['title']}
- Description: {material.get('description', 'No description provided')}
- Learning Objective: {learning_objective}
- Pedagogy Strategy: {pedagogy_strategy}
- Course Context: {course.get('name', 'Unknown Course')} - Module {material['module_number']}, Chapter {material['chapter_number']}

{format_prompt}

QUALITY STANDARDS:
- Question should directly test the learning objective
- Use clear, unambiguous language
- Avoid trick questions or overly complex wording
- Ensure one clearly correct answer (for formats that require it)
- Provide educational explanations that reinforce learning
- Make distractors plausible but clearly incorrect

RESPONSE FORMAT (JSON only):
{{
    "success": true,
    "question": {{
        "text": "Clear, specific question text",
        "options": [/* format-specific options */],
        "correct_answer": "format-specific correct answer identifier",
        "explanation": "Detailed explanation of why the answer is correct and others are wrong",
        "difficulty": "beginner|intermediate|advanced"
    }}
}}"""

            user_prompt = f"Create a single {assessment_format} question that tests understanding of '{material['title']}'. The question should align with the learning objective: '{learning_objective}'"

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await self.openai.create_chat_completion(
                model=self.model,
                messages=messages,
                max_tokens=1500,
                temperature=0.3  # Slight creativity for question variety
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Clean up response if it has markdown formatting
            if ai_response.startswith('```json'):
                ai_response = ai_response.replace('```json', '').replace('```', '').strip()
            elif ai_response.startswith('```'):
                ai_response = ai_response.replace('```', '').strip()
            
            # Parse AI response
            try:
                question_result = json.loads(ai_response)
                
                if question_result.get("success") and question_result.get("question"):
                    print(f"✅ [MaterialContentGeneratorAgent] Generated {assessment_format} question successfully")
                    return question_result
                else:
                    # Fallback to template-based question generation
                    return self._generate_fallback_question(material, assessment_format, learning_objective)
                    
            except json.JSONDecodeError:
                print(f"❌ [MaterialContentGeneratorAgent] Failed to parse AI question generation response")
                return self._generate_fallback_question(material, assessment_format, learning_objective)
                
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error generating assessment question: {e}")
            return self._generate_fallback_question(material, assessment_format, learning_objective)
    
    def _get_format_specific_prompt(self, assessment_format: str) -> str:
        """Get format-specific generation prompts"""
        format_prompts = {
            "multiple_choice": """
MULTIPLE CHOICE FORMAT:
- Create 4 options (A, B, C, D)
- Only one correct answer
- Make distractors plausible but clearly wrong
- Options should be similar in length and complexity

Example structure:
"options": [
    {"id": "A", "text": "Option A text", "correct": false},
    {"id": "B", "text": "Option B text", "correct": true},
    {"id": "C", "text": "Option C text", "correct": false},
    {"id": "D", "text": "Option D text", "correct": false}
],
"correct_answer": "B"
""",
            
            "true_false": """
TRUE/FALSE FORMAT:
- Create a clear statement that can be definitively true or false
- Avoid ambiguous or partially true statements
- Focus on key concepts from the material

Example structure:
"options": [
    {"id": "true", "text": "True", "correct": true},
    {"id": "false", "text": "False", "correct": false}
],
"correct_answer": "true"
""",
            
            "scenario_choice": """
SCENARIO CHOICE FORMAT:
- Present a realistic workplace/professional scenario
- Provide 4 possible actions/responses
- Focus on practical application of concepts
- Make the scenario relevant to the learning objective

Example structure:
"scenario": "Detailed scenario description...",
"options": [
    {"id": "A", "text": "Action A", "correct": false},
    {"id": "B", "text": "Action B", "correct": true},
    {"id": "C", "text": "Action C", "correct": false},
    {"id": "D", "text": "Action D", "correct": false}
],
"correct_answer": "B"
""",
            
            "matching": """
MATCHING FORMAT:
- Create two lists that need to be matched
- 4-5 items in each list
- Clear one-to-one relationships
- Mix up the order to avoid obvious patterns

Example structure:
"left_items": [
    {"id": "1", "text": "Item 1"},
    {"id": "2", "text": "Item 2"},
    {"id": "3", "text": "Item 3"},
    {"id": "4", "text": "Item 4"}
],
"right_items": [
    {"id": "A", "text": "Match A"},
    {"id": "B", "text": "Match B"},
    {"id": "C", "text": "Match C"},
    {"id": "D", "text": "Match D"}
],
"correct_matches": {"1": "B", "2": "A", "3": "D", "4": "C"}
""",
            
            "fill_in_blank": """
FILL IN THE BLANK FORMAT:
- Create a sentence with 1-2 key terms missing
- Focus on important terminology or concepts
- Provide the exact word(s) expected
- Make the context clear enough to determine the answer

Example structure:
"text": "A manager's primary role is to _____ performance through others.",
"blanks": [
    {"position": 1, "correct_answer": "enable", "alternatives": ["facilitate", "improve"]}
],
"correct_answer": "enable"
""",
            
            "ranking": """
RANKING FORMAT:
- Provide 4-5 items that need to be ordered
- Clear criteria for ranking (priority, sequence, importance)
- Items should have a logical, defensible order
- Focus on processes, priorities, or hierarchies

Example structure:
"items": [
    {"id": "A", "text": "Item A"},
    {"id": "B", "text": "Item B"},
    {"id": "C", "text": "Item C"},
    {"id": "D", "text": "Item D"}
],
"correct_order": ["B", "A", "D", "C"],
"ranking_criteria": "Order of priority in management process"
"""
        }
        
        return format_prompts.get(assessment_format, format_prompts["multiple_choice"])
    
    def _generate_fallback_question(self, material: Dict[str, Any], assessment_format: str, learning_objective: str) -> Dict[str, Any]:
        """Generate a basic fallback question when AI generation fails"""
        try:
            title = material['title']
            
            if assessment_format == "multiple_choice":
                return {
                    "success": True,
                    "question": {
                        "text": f"What is the key concept covered in '{title}'?",
                        "options": [
                            {"id": "A", "text": f"Understanding {title.lower()}", "correct": True},
                            {"id": "B", "text": "Unrelated concept A", "correct": False},
                            {"id": "C", "text": "Unrelated concept B", "correct": False},
                            {"id": "D", "text": "Unrelated concept C", "correct": False}
                        ],
                        "correct_answer": "A",
                        "explanation": f"The correct answer focuses on the main learning objective of {title}.",
                        "difficulty": "intermediate"
                    }
                }
            elif assessment_format == "true_false":
                return {
                    "success": True,
                    "question": {
                        "text": f"The concepts in '{title}' are important for professional development.",
                        "options": [
                            {"id": "true", "text": "True", "correct": True},
                            {"id": "false", "text": "False", "correct": False}
                        ],
                        "correct_answer": "true",
                        "explanation": f"True. The concepts covered in {title} are indeed important for professional development.",
                        "difficulty": "beginner"
                    }
                }
            else:
                # Default fallback to multiple choice
                return self._generate_fallback_question(material, "multiple_choice", learning_objective)
                
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error generating fallback question: {e}")
            return {"success": False, "error": f"Failed to generate fallback question: {str(e)}"}
    
    def _extract_pedagogy_strategy(self, material: Dict[str, Any], course_design_content: str) -> str:
        """Extract pedagogy strategy from material description or course design"""
        try:
            # First try to extract from material description
            description = material.get('description', '')
            if 'pedagogy' in description.lower() or 'strategy' in description.lower():
                # Look for pedagogy-related keywords
                pedagogy_keywords = [
                    'interactive learning', 'case study', 'hands-on', 'practical',
                    'collaborative', 'problem-based', 'experiential', 'inquiry-based'
                ]
                
                for keyword in pedagogy_keywords:
                    if keyword in description.lower():
                        return keyword.title()
            
            # Fallback to course design content analysis
            if course_design_content:
                # Look for pedagogy strategy in course design
                lines = course_design_content.split('\n')
                for line in lines:
                    if 'pedagogy strategy:' in line.lower():
                        return line.split(':', 1)[1].strip()
            
            # Default strategy
            return "Interactive learning with examples and practice"
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error extracting pedagogy strategy: {e}")
            return "Interactive learning with examples and practice"
    
    def _analyze_content_for_images(self, content: str, material: Dict[str, Any]) -> List[Dict[str, str]]:
        """Analyze content to identify where images would be helpful - ENHANCED VERSION"""
        try:
            image_requests = []
            
            # Look for explicit image requests first
            # New #image {} format
            new_image_pattern = r'#image\s*\{([^}]+)\}'
            new_matches = re.findall(new_image_pattern, content)
            
            for i, description in enumerate(new_matches):
                image_requests.append({
                    "description": description.strip(),
                    "placement": f"image_{i+1}",
                    "context": material.get('title', 'Course Material'),
                    "format": "new",
                    "type": "explicit"
                })
            
            # Legacy [IMAGE_REQUEST: ] format for backward compatibility
            legacy_image_pattern = r'\[IMAGE_REQUEST:\s*([^\]]+)\]'
            legacy_matches = re.findall(legacy_image_pattern, content)
            
            for i, description in enumerate(legacy_matches, len(image_requests)):
                image_requests.append({
                    "description": description.strip(),
                    "placement": f"image_{i+1}",
                    "context": material.get('title', 'Course Material'),
                    "format": "legacy",
                    "type": "explicit"
                })
            
            # ENHANCEMENT: Intelligent content analysis for automatic image suggestions
            if len(image_requests) == 0:  # Only suggest if no explicit requests
                auto_suggestions = self._suggest_images_from_content(content, material)
                image_requests.extend(auto_suggestions)
            
            return image_requests
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error analyzing content for images: {e}")
            return []
    
    def _suggest_images_from_content(self, content: str, material: Dict[str, Any]) -> List[Dict[str, str]]:
        """Intelligently suggest images based on content analysis"""
        try:
            suggestions = []
            content_lower = content.lower()
            
            # Define content patterns that benefit from visual aids
            visual_patterns = {
                # Process/workflow patterns
                'process': {
                    'keywords': ['process', 'workflow', 'steps', 'procedure', 'methodology', 'approach', 'framework'],
                    'description': 'A process flow diagram showing the step-by-step {topic} workflow with clear stages and connections'
                },
                # Comparison patterns
                'comparison': {
                    'keywords': ['vs', 'versus', 'compare', 'comparison', 'difference', 'contrast', 'alternative'],
                    'description': 'A comparison infographic highlighting the key differences and similarities between {topic} options'
                },
                # Architecture/system patterns
                'architecture': {
                    'keywords': ['architecture', 'system', 'structure', 'components', 'framework', 'model', 'design'],
                    'description': 'A system architecture diagram illustrating the {topic} components and their relationships'
                },
                # Data/statistics patterns
                'data': {
                    'keywords': ['data', 'statistics', 'metrics', 'analytics', 'performance', 'results', 'trends'],
                    'description': 'An infographic displaying key {topic} data and statistics in a visually appealing format'
                },
                # Concept/theory patterns
                'concept': {
                    'keywords': ['concept', 'theory', 'principle', 'idea', 'notion', 'understanding'],
                    'description': 'A conceptual illustration representing the core {topic} principles and relationships'
                },
                # Timeline/history patterns
                'timeline': {
                    'keywords': ['history', 'evolution', 'timeline', 'development', 'progression', 'chronology'],
                    'description': 'A timeline visualization showing the historical development and evolution of {topic}'
                },
                # Benefits/advantages patterns
                'benefits': {
                    'keywords': ['benefits', 'advantages', 'pros', 'value', 'impact', 'outcomes'],
                    'description': 'An infographic showcasing the key benefits and positive impacts of {topic}'
                },
                # Technology/tools patterns
                'technology': {
                    'keywords': ['technology', 'tools', 'software', 'platform', 'solution', 'implementation'],
                    'description': 'A technology stack diagram showing the {topic} tools and their integration'
                }
            }
            
            # Analyze content for patterns
            detected_patterns = []
            for pattern_name, pattern_info in visual_patterns.items():
                keyword_matches = sum(1 for keyword in pattern_info['keywords'] if keyword in content_lower)
                if keyword_matches >= 2:  # Require at least 2 keyword matches
                    detected_patterns.append((pattern_name, pattern_info, keyword_matches))
            
            # Sort by relevance (number of keyword matches)
            detected_patterns.sort(key=lambda x: x[2], reverse=True)
            
            # Generate suggestions for top patterns (max 2 to avoid overwhelming)
            for i, (pattern_name, pattern_info, matches) in enumerate(detected_patterns[:2]):
                topic = material.get('title', 'the topic').lower()
                description = pattern_info['description'].format(topic=topic)
                
                suggestions.append({
                    "description": description,
                    "placement": f"auto_image_{i+1}",
                    "context": material.get('title', 'Course Material'),
                    "format": "auto_suggestion",
                    "type": "intelligent_suggestion",
                    "pattern": pattern_name,
                    "confidence": min(matches / 5.0, 1.0)  # Normalize confidence score
                })
            
            # Special case: If no patterns detected but content is long, suggest a summary visual
            if not suggestions and len(content) > 1000:
                topic = material.get('title', 'the topic').lower()
                suggestions.append({
                    "description": f"A comprehensive visual summary of {topic} highlighting the key points and takeaways",
                    "placement": "summary_image",
                    "context": material.get('title', 'Course Material'),
                    "format": "auto_suggestion",
                    "type": "summary_visual",
                    "pattern": "summary",
                    "confidence": 0.6
                })
            
            if suggestions:
                print(f"🤖 [MaterialContentGeneratorAgent] Auto-suggested {len(suggestions)} images based on content analysis")
                for suggestion in suggestions:
                    print(f"   - {suggestion['pattern']}: {suggestion['description'][:60]}...")
            
            return suggestions
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error suggesting images from content: {e}")
            return []
    
    async def _generate_and_integrate_images(self, content: str, image_requests: List[Dict[str, str]], 
                                           material: Dict[str, Any], course: Dict[str, Any]) -> str:
        """Generate images and integrate them into content - ENHANCED VERSION"""
        try:
            if not self.image_agent:
                print("⚠️ [MaterialContentGeneratorAgent] Image agent not available")
                return content
            
            enhanced_content = content
            print(f"🔍 [MaterialContentGeneratorAgent] Starting enhanced image integration with {len(image_requests)} requests")
            print(f"🔍 [MaterialContentGeneratorAgent] Original content length: {len(content)}")
            
            # Track successful integrations for reporting
            successful_integrations = 0
            failed_integrations = 0
            
            for i, image_request in enumerate(image_requests):
                try:
                    request_type = image_request.get('type', 'explicit')
                    request_format = image_request.get('format', 'unknown')
                    confidence = image_request.get('confidence', 1.0)
                    
                    print(f"🔍 [MaterialContentGeneratorAgent] Processing image request {i+1}:")
                    print(f"   Type: {request_type}")
                    print(f"   Format: {request_format}")
                    print(f"   Confidence: {confidence}")
                    print(f"   Description: '{image_request['description'][:50]}...'")
                    
                    # Skip low-confidence auto-suggestions if we already have explicit images
                    if request_type == 'intelligent_suggestion' and confidence < 0.7 and successful_integrations > 0:
                        print(f"⏭️ [MaterialContentGeneratorAgent] Skipping low-confidence suggestion (already have {successful_integrations} images)")
                        continue
                    
                    # Extract image description for this request
                    image_description = image_request['description']
                    
                    # Enhanced context for better image generation
                    enhanced_context = {
                        "content_type": "educational_material",
                        "learning_objective": material.get('description'),
                        "material_type": material['material_type'],
                        "purpose": "content_illustration",
                        "request_type": request_type,
                        "pattern": image_request.get('pattern', 'general'),
                        "confidence": confidence,
                        "slide_context": material.get('title', 'Course Material')
                    }
                    
                    # Determine image style based on request type and pattern
                    image_style = self._determine_image_style(image_request, material)
                    
                    # Generate image using the image agent with enhanced parameters
                    image_result = await self.image_agent.generate_image_multi_size(
                        course_id=str(material["course_id"]),
                        image_name=f"{material['title']} - {image_description}",
                        image_description=image_description,
                        image_type="slide_content",
                        filename=f"slide_{material.get('slide_number', i+1)}_image_{i+1}",
                        style_preference=image_style,
                        dynamic_colors=True,
                        calling_agent="material_content_generator",
                        context=enhanced_context
                    )
                    
                    if image_result["success"]:
                        # Get medium size image URL for content integration
                        medium_image_url = image_result["images"]["medium"]["public_url"]
                        print(f"✅ [MaterialContentGeneratorAgent] Image generated successfully: {medium_image_url}")
                        
                        # Create enhanced image markdown with better formatting
                        image_markdown = self._create_enhanced_image_markdown(
                            image_request, medium_image_url, image_result
                        )
                        
                        # Handle different placeholder formats
                        replacement_successful = False
                        
                        if image_request.get('format') == 'new':
                            # New format: #image {description}
                            placeholder = f"#image {{{image_request['description']}}}"
                            if placeholder in enhanced_content:
                                enhanced_content = enhanced_content.replace(placeholder, image_markdown)
                                replacement_successful = True
                        elif image_request.get('format') == 'legacy':
                            # Legacy format: [IMAGE_REQUEST: description]
                            placeholder = f"[IMAGE_REQUEST: {image_request['description']}]"
                            if placeholder in enhanced_content:
                                enhanced_content = enhanced_content.replace(placeholder, image_markdown)
                                replacement_successful = True
                        elif image_request.get('format') == 'auto_suggestion':
                            # Auto-suggestion: Insert at strategic location
                            enhanced_content = await self._insert_auto_suggested_image(
                                enhanced_content, image_markdown, image_request, material
                            )
                            replacement_successful = True
                        
                        if replacement_successful:
                            successful_integrations += 1
                            print(f"✅ [MaterialContentGeneratorAgent] Successfully integrated image {i+1}")
                        else:
                            failed_integrations += 1
                            print(f"❌ [MaterialContentGeneratorAgent] Failed to integrate image {i+1} - placeholder not found")
                    else:
                        failed_integrations += 1
                        print(f"❌ [MaterialContentGeneratorAgent] Failed to generate image {i+1}: {image_result.get('error')}")
                        
                        # Handle failed generation gracefully
                        await self._handle_failed_image_generation(enhanced_content, image_request)
                
                except Exception as img_error:
                    failed_integrations += 1
                    print(f"❌ [MaterialContentGeneratorAgent] Error processing image {i+1}: {img_error}")
                    await self._handle_failed_image_generation(enhanced_content, image_request)
            
            # Report integration results
            total_requests = len(image_requests)
            print(f"📊 [MaterialContentGeneratorAgent] Image integration complete:")
            print(f"   Total requests: {total_requests}")
            print(f"   Successful: {successful_integrations}")
            print(f"   Failed: {failed_integrations}")
            print(f"   Success rate: {(successful_integrations/total_requests*100):.1f}%" if total_requests > 0 else "   No requests processed")
            print(f"   Final content length: {len(enhanced_content)} characters")
            
            return enhanced_content
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error in enhanced image integration: {e}")
            return content
    
    def _determine_image_style(self, image_request: Dict[str, Any], material: Dict[str, Any]) -> str:
        """Determine the best image style based on request type and content pattern"""
        try:
            request_type = image_request.get('type', 'explicit')
            pattern = image_request.get('pattern', 'general')
            material_type = material.get('material_type', 'slide')
            
            # Style mapping based on content patterns
            pattern_styles = {
                'process': 'professional_educational',  # Clean diagrams for processes
                'comparison': 'modern',  # Modern infographics for comparisons
                'architecture': 'tech_focused',  # Technical diagrams for systems
                'data': 'colorful',  # Engaging visuals for data
                'concept': 'minimalist',  # Clean illustrations for concepts
                'timeline': 'modern',  # Modern timeline visuals
                'benefits': 'colorful',  # Engaging benefit illustrations
                'technology': 'tech_focused',  # Technical style for tech content
                'summary': 'professional_educational'  # Professional summary visuals
            }
            
            # Get style based on pattern, fallback to professional_educational
            style = pattern_styles.get(pattern, 'professional_educational')
            
            # Override for assessments - always use minimalist
            if material_type == 'assessment':
                style = 'minimalist'
            
            print(f"🎨 [MaterialContentGeneratorAgent] Selected style '{style}' for pattern '{pattern}' and type '{request_type}'")
            return style
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error determining image style: {e}")
            return 'professional_educational'
    
    def _create_enhanced_image_markdown(self, image_request: Dict[str, Any], image_url: str, image_result: Dict[str, Any]) -> str:
        """Create enhanced markdown for image integration with better formatting"""
        try:
            description = image_request['description']
            request_type = image_request.get('type', 'explicit')
            pattern = image_request.get('pattern', 'general')
            
            # Create alt text (shorter version of description)
            alt_text = description[:100] + "..." if len(description) > 100 else description
            
            # Base image markdown
            image_markdown = f"![{alt_text}]({image_url})"
            
            # Add caption based on request type
            if request_type == 'intelligent_suggestion':
                # For auto-suggestions, add a more descriptive caption
                caption = f"*Figure: {description}*"
            else:
                # For explicit requests, use the description as caption
                caption = f"*{description}*"
            
            # Add spacing and formatting
            enhanced_markdown = f"\n\n{image_markdown}\n{caption}\n\n"
            
            # Add divider for better visual separation (optional)
            if pattern in ['process', 'architecture', 'timeline']:
                enhanced_markdown += "---\n\n"
            
            return enhanced_markdown
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error creating enhanced image markdown: {e}")
            # Fallback to simple markdown
            return f"\n\n![{image_request['description']}]({image_url})\n*{image_request['description']}*\n\n"
    
    async def _insert_auto_suggested_image(self, content: str, image_markdown: str, image_request: Dict[str, Any], material: Dict[str, Any]) -> str:
        """Insert auto-suggested images at strategic locations in content"""
        try:
            pattern = image_request.get('pattern', 'general')
            confidence = image_request.get('confidence', 0.5)
            
            lines = content.split('\n')
            
            # Strategy 1: Insert after relevant section headers
            if pattern in ['process', 'architecture', 'technology']:
                # Look for headers that match the pattern
                pattern_keywords = {
                    'process': ['process', 'workflow', 'steps', 'procedure', 'methodology'],
                    'architecture': ['architecture', 'system', 'structure', 'components', 'framework'],
                    'technology': ['technology', 'tools', 'software', 'platform', 'solution']
                }
                
                keywords = pattern_keywords.get(pattern, [])
                for i, line in enumerate(lines):
                    if line.startswith('#') and any(keyword in line.lower() for keyword in keywords):
                        # Insert after this header and any immediate content
                        insert_index = i + 1
                        while insert_index < len(lines) and lines[insert_index].strip() and not lines[insert_index].startswith('#'):
                            insert_index += 1
                        lines.insert(insert_index, image_markdown.strip())
                        return '\n'.join(lines)
            
            # Strategy 2: Insert in the middle of content for summary/concept images
            if pattern in ['summary', 'concept', 'benefits']:
                middle_index = len(lines) // 2
                # Find a good break point near the middle
                for i in range(middle_index - 5, min(middle_index + 5, len(lines))):
                    if i >= 0 and i < len(lines) and (not lines[i].strip() or lines[i].startswith('#')):
                        lines.insert(i, image_markdown.strip())
                        return '\n'.join(lines)
            
            # Strategy 3: Insert after introduction (for comparison, data images)
            if pattern in ['comparison', 'data', 'timeline']:
                # Look for end of introduction section
                for i, line in enumerate(lines):
                    if line.startswith('##') and i > 5:  # After some intro content
                        lines.insert(i, image_markdown.strip())
                        return '\n'.join(lines)
            
            # Fallback: Insert at 1/3 of the content
            fallback_index = len(lines) // 3
            lines.insert(fallback_index, image_markdown.strip())
            
            print(f"📍 [MaterialContentGeneratorAgent] Inserted auto-suggested image using fallback strategy at line {fallback_index}")
            return '\n'.join(lines)
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error inserting auto-suggested image: {e}")
            # Fallback: append at end
            return content + image_markdown
    
    async def _handle_failed_image_generation(self, content: str, image_request: Dict[str, Any]) -> str:
        """Handle failed image generation gracefully"""
        try:
            request_format = image_request.get('format', 'unknown')
            description = image_request['description']
            
            # Only remove placeholders for explicit requests, not auto-suggestions
            if request_format in ['new', 'legacy']:
                if request_format == 'new':
                    placeholder = f"#image {{{description}}}"
                else:
                    placeholder = f"[IMAGE_REQUEST: {description}]"
                
                # Replace with a note about the missing image
                replacement = f"*[Image placeholder: {description}]*"
                content = content.replace(placeholder, replacement)
            
            return content
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error handling failed image generation: {e}")
            return content
    
    async def _store_content_in_r2(self, material: Dict[str, Any], content: str, course: Dict[str, Any]) -> Dict[str, Any]:
        """Store generated content in R2 storage as markdown file"""
        try:
            # Create filename based on material info
            filename = f"module_{material['module_number']}_chapter_{material['chapter_number']}_{material.get('slide_number', 1)}_{self._sanitize_filename(material['title'])}.md"
            
            # Store in R2 under course content path
            r2_result = await self.storage.upload_course_content(
                course_id=str(material["course_id"]),
                content=content,
                filename=filename,
                content_type="text/markdown"
            )
            
            return r2_result
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error storing content in R2: {e}")
            return {"success": False, "error": f"Failed to store content: {str(e)}"}
    
    def _sanitize_filename(self, title: str) -> str:
        """Sanitize title for filename usage"""
        if not title:
            return 'untitled'
        
        # Convert to lowercase and remove special characters
        sanitized = re.sub(r'[^a-z0-9\s-]', '', title.lower())
        # Replace spaces with underscores
        sanitized = re.sub(r'\s+', '_', sanitized)
        # Replace multiple underscores with single underscore
        sanitized = re.sub(r'_+', '_', sanitized)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        # Limit length
        return sanitized[:30] if sanitized else 'untitled'
    
    async def _approve_content(self, material_id: str, approved: bool) -> Dict[str, Any]:
        """Approve or reject generated content"""
        try:
            print(f"✅ [MaterialContentGeneratorAgent] {'Approving' if approved else 'Rejecting'} content for material {material_id}")
            
            db = await self.db.get_database()
            
            # Try to find the material with the provided ID
            material = None
            if material_id and self._is_valid_object_id(material_id):
                material = await db.content_materials.find_one({"_id": ObjectId(material_id)})
            
            # If material not found with provided ID, try to auto-detect current material
            if not material:
                print(f"⚠️ [MaterialContentGeneratorAgent] Material {material_id} not found, attempting auto-detection...")
                material = await self._get_current_material_to_approve()
                
                if material:
                    material_id = str(material["_id"])
                    print(f"✅ [MaterialContentGeneratorAgent] Auto-detected material: {material_id} - {material['title']}")
                else:
                    return {"success": False, "error": "Material not found"}
            
            if approved:
                # Mark as approved
                await db.content_materials.update_one(
                    {"_id": ObjectId(material_id)},
                    {
                        "$set": {
                            "status": "approved",
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                
                # Get next material to process
                next_material = await self._get_next_material_to_process(str(material["course_id"]))
                
                if next_material:
                    # AUTO-GENERATE CONTENT FOR NEXT MATERIAL
                    print(f"🚀 [MaterialContentGeneratorAgent] Auto-generating content for next material: {next_material['title']}")
                    print(f"   Type: {next_material['material_type']}")
                    print(f"   Location: Module {next_material['module_number']}, Chapter {next_material['chapter_number']}, Slide {next_material.get('slide_number', 1)}")
                    
                    # Send a pre-generation event to ensure frontend knows what's coming next
                    file_path = self._get_material_file_path(next_material)
                    await self._send_streaming_event({
                        "type": "next_material_starting",
                        "material_id": str(next_material["_id"]),
                        "title": next_material["title"],
                        "material_type": next_material["material_type"],
                        "module_number": next_material["module_number"],
                        "chapter_number": next_material["chapter_number"],
                        "slide_number": next_material.get("slide_number", 1),
                        "file_path": file_path,
                        "message": f"Moving to next material: {next_material['title']}"
                    })
                    
                    # Generate content for the next material
                    generation_result = await self._generate_slide_content(str(next_material["_id"]))
                    
                    if generation_result["success"]:
                        print(f"✅ [MaterialContentGeneratorAgent] Successfully generated content for next material")
                        return {
                            "success": True,
                            "approved": True,
                            "next_material": {
                                "id": str(next_material["_id"]),
                                "title": next_material["title"],
                                "module_number": next_material["module_number"],
                                "chapter_number": next_material["chapter_number"],
                                "material_type": next_material["material_type"],
                                "slide_number": next_material.get("slide_number", 1)
                            },
                            "continue_generation": True,
                            "auto_generated": True,  # Flag to indicate auto-generation
                            "generated_material": generation_result.get("material", {})
                        }
                    else:
                        # If generation failed, still return success for approval but with error info
                        return {
                            "success": True,
                            "approved": True,
                            "next_material": {
                                "id": str(next_material["_id"]),
                                "title": next_material["title"],
                                "module_number": next_material["module_number"],
                                "chapter_number": next_material["chapter_number"],
                                "material_type": next_material["material_type"]
                            },
                            "continue_generation": True,
                            "generation_failed": True,
                            "generation_error": generation_result.get("error", "Unknown error")
                        }
                else:
                    # All materials completed
                    await self._mark_course_content_complete(str(material["course_id"]))
                    return {
                        "success": True,
                        "approved": True,
                        "all_completed": True,
                        "message": "All course materials have been generated and approved!"
                    }
            else:
                # Mark as needs revision
                await db.content_materials.update_one(
                    {"_id": ObjectId(material_id)},
                    {
                        "$set": {
                            "status": "needs_revision",
                            "content_status": "not done",  # Reset for regeneration
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                
                return {
                    "success": True,
                    "approved": False,
                    "message": "Content marked for revision. Please provide modification feedback."
                }
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error approving content: {e}")
            return {"success": False, "error": f"Failed to approve content: {str(e)}"}
    
    async def _modify_content(self, material_id: str, modification_request: str) -> Dict[str, Any]:
        """Modify content based on user feedback"""
        try:
            print(f"🔄 [MaterialContentGeneratorAgent] Modifying content for material {material_id}")
            
            # Validate material_id format
            if not self._is_valid_object_id(material_id):
                return {"success": False, "error": f"Invalid material ID format: '{material_id}'"}
            
            # Get material details
            db = await self.db.get_database()
            material = await db.content_materials.find_one({"_id": ObjectId(material_id)})
            
            if not material:
                return {"success": False, "error": "Material not found"}
            
            # Get course context
            course = await self.db.find_course(str(material["course_id"]))
            if not course:
                return {"success": False, "error": "Course not found"}
            
            # Get course design content for context
            course_design_content = ""
            if course.get("course_design_r2_key"):
                course_design_content = await self.storage.get_course_design_content(course["course_design_r2_key"])
            
            # Update status to generating
            await db.content_materials.update_one(
                {"_id": ObjectId(material_id)},
                {
                    "$set": {
                        "content_status": "generating",
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Generate modified content using AI with user feedback
            modified_content_result = await self._generate_modified_ai_content(
                material, course, course_design_content, modification_request
            )
            
            if not modified_content_result["success"]:
                # Update status back to needs revision on failure
                await db.content_materials.update_one(
                    {"_id": ObjectId(material_id)},
                    {
                        "$set": {
                            "content_status": "not done",
                            "status": "needs_revision",
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                return modified_content_result
            
            modified_content = modified_content_result["content"]
            
            # Check if modified content needs images
            image_requests = self._analyze_content_for_images(modified_content, material)
            
            # Generate images if needed
            if image_requests and self.image_agent:
                enhanced_content = await self._generate_and_integrate_images(
                    modified_content, image_requests, material, course
                )
                modified_content = enhanced_content
            
            # Store modified content
            await db.content_materials.update_one(
                {"_id": ObjectId(material_id)},
                {
                    "$set": {
                        "content": modified_content,
                        "content_status": "completed",
                        "status": "pending",  # Reset to pending for re-approval
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Update content in R2 storage
            r2_result = await self._store_content_in_r2(material, modified_content, course)
            
            if r2_result["success"]:
                await db.content_materials.update_one(
                    {"_id": ObjectId(material_id)},
                    {
                        "$set": {
                            "r2_key": r2_result["r2_key"],
                            "public_url": r2_result["public_url"],
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
            
            print(f"✅ [MaterialContentGeneratorAgent] Content modified successfully for {material['title']}")
            
            return {
                "success": True,
                "material": {
                    "id": material_id,
                    "title": material["title"],
                    "content": modified_content,
                    "content_length": len(modified_content),
                    "has_images": len(image_requests) > 0 if image_requests else False,
                    "r2_key": r2_result.get("r2_key") if r2_result["success"] else None,
                    "public_url": r2_result.get("public_url") if r2_result["success"] else None
                },
                "preview_ready": True,
                "modification_applied": True
            }
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error modifying content: {e}")
            return {"success": False, "error": f"Failed to modify content: {str(e)}"}
    
    async def _generate_modified_ai_content(self, material: Dict[str, Any], course: Dict[str, Any], 
                                          course_design_content: str, modification_request: str) -> Dict[str, Any]:
        """Generate modified content using AI based on user feedback"""
        try:
            # Extract pedagogy strategy
            pedagogy_strategy = self._extract_pedagogy_strategy(material, course_design_content)
            
            # Get current content for context
            current_content = material.get('content', '')
            
            # Create modification prompt
            system_prompt = f"""You are an expert educational content creator specializing in content modification based on user feedback.

CONTENT MODIFICATION TASK:
Modify the existing content for: "{material['title']}" based on user feedback.

MATERIAL CONTEXT:
- Type: {material['material_type']}
- Module: {material['module_number']}
- Chapter: {material['chapter_number']}
- Description: {material.get('description', 'No description provided')}
- Course: {course.get('name', 'Unknown Course')}

PEDAGOGY STRATEGY: {pedagogy_strategy}

USER FEEDBACK: {modification_request}

CURRENT CONTENT:
{current_content}

MODIFICATION REQUIREMENTS:
1. **Address User Feedback**: Specifically address all points mentioned in the user feedback
2. **Maintain Quality**: Keep the same high quality and comprehensive coverage
3. **Preserve Structure**: Maintain the overall structure unless feedback requests changes
4. **Enhance Content**: Improve based on feedback while keeping existing strengths
5. **Consistency**: Ensure modifications align with the pedagogy strategy

CONTENT STRUCTURE (maintain unless feedback requests changes):
1. **Learning Objectives** (What students will learn)
2. **Introduction** (Context and importance)
3. **Core Content** (Detailed explanations with examples)
4. **Practical Applications** (Real-world use cases)
5. **Self-Check Questions** (3-5 questions for understanding)
6. **Key Takeaways** (Summary of main points)
7. **Next Steps** (How this connects to future learning)

FORMATTING REQUIREMENTS:
- Use proper markdown formatting
- Include headers (##, ###, ####)
- Use bullet points and numbered lists
- Add code blocks where relevant
- Include blockquotes for important concepts
- Use tables for comparisons when helpful

IMAGE PLACEHOLDERS:
- When content would benefit from visual explanation, add: [IMAGE_REQUEST: Description of needed image]
- Place image requests where they would be most helpful in the content flow

Generate the modified content that addresses the user feedback while maintaining educational quality."""

            user_prompt = f"""Modify the content for "{material['title']}" based on this user feedback: "{modification_request}"

Please provide the complete modified content that addresses the feedback while maintaining the same comprehensive quality and structure."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await self.openai.create_chat_completion(
                model=self.model,
                messages=messages,
                max_tokens=4000  # Allow for comprehensive content
            )
            
            modified_content = response.choices[0].message.content.strip()
            
            if modified_content:
                print(f"✅ [MaterialContentGeneratorAgent] AI generated {len(modified_content)} characters of modified content")
                return {"success": True, "content": modified_content}
            else:
                return {"success": False, "error": "AI generated empty modified content"}
                
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] AI content modification error: {e}")
            return {"success": False, "error": f"AI content modification failed: {str(e)}"}
    
    async def _mark_course_content_complete(self, course_id: str) -> None:
        """Mark course content generation as complete"""
        try:
            await self.db.update_document("courses", course_id, {
                "workflow_step": "content_complete",
                "content_generation_completed": True,
                "content_generation_completed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
            
            print(f"✅ [MaterialContentGeneratorAgent] Marked course {course_id} content as complete")
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error marking course content complete: {e}")
    
    def _is_valid_object_id(self, object_id: str) -> bool:
        """Validate if the provided string is a valid MongoDB ObjectId format"""
        try:
            # Check if it's a valid ObjectId format (24 character hex string)
            if len(object_id) != 24:
                return False
            
            # Try to create ObjectId to validate format
            ObjectId(object_id)
            return True
            
        except Exception:
            return False
    
    async def _generate_response_with_context(self, base_response: Optional[str], function_results: Dict[str, Any]) -> str:
        """Generate contextual response based on function results - FIXED VERSION"""
        print(f"🔍 [MaterialContentGeneratorAgent] _generate_response_with_context called")
        print(f"   base_response: '{base_response}'")
        print(f"   function_results keys: {list(function_results.keys()) if function_results else 'None'}")
        
        if not function_results:
            print(f"🔍 [MaterialContentGeneratorAgent] No function results, returning base response")
            return base_response or "Ready to generate content for your course."
        
        # Handle content generation start
        if "content_generation_started" in function_results:
            result = function_results["content_generation_started"]
            print(f"🔍 [MaterialContentGeneratorAgent] Processing content_generation_started: {result}")
            if result.get("success"):
                if result.get("completed"):
                    return "✅ All Done - you can publish this course now"
                elif result.get("first_slide_generated") and result.get("generated_material"):
                    # Show the first generated material
                    material = result.get("generated_material", {})
                    return f"""✅ Content Generated Successfully!

📄 Material: {material.get('title', 'Unknown')}
📊 Content Length: {material.get('content_length', 0):,} characters
🖼️ Images: {'Yes' if material.get('has_images') else 'No'}

Preview is ready! Please review the generated content and choose:
• **Approve & Continue** to move to the next slide
• **Request Modifications** if you'd like changes"""
                else:
                    # Simply return that generation has started - no verbose details
                    return "Starting content generation..."
            else:
                return f"❌ Failed: {result.get('error', 'Unknown error')}"
        
        # Handle slide content generation - SIMPLIFIED
        if "slide_content_generated" in function_results:
            result = function_results["slide_content_generated"]
            print(f"🔍 [MaterialContentGeneratorAgent] Processing slide_content_generated: {result}")
            if result.get("success"):
                material = result.get("material", {})
                # Show the standard approval message
                return f"""✅ Content Generated Successfully!

📄 Material: {material.get('title', 'Unknown')}
📊 Content Length: {material.get('content_length', 0):,} characters
🖼️ Images: {'Yes' if material.get('has_images') else 'No'}

Preview is ready! Please review the generated content and choose:
• **Approve & Continue** to move to the next slide
• **Request Modifications** if you'd like changes"""
            else:
                return f"❌ Failed: {result.get('error', 'Unknown error')}"
        
        # Handle content approval - CRITICAL FIX FOR SEAMLESS FLOW
        if "content_approved" in function_results:
            result = function_results["content_approved"]
            print(f"🔍 [MaterialContentGeneratorAgent] Processing content_approved: {result}")
            print(f"   - success: {result.get('success')}")
            print(f"   - all_completed: {result.get('all_completed')}")
            print(f"   - auto_generated: {result.get('auto_generated')}")
            print(f"   - continue_generation: {result.get('continue_generation')}")
            print(f"   - generated_material exists: {bool(result.get('generated_material'))}")
            print(f"   - generation_failed: {result.get('generation_failed')}")
            
            if result.get("success"):
                if result.get("all_completed"):
                    print(f"🔍 [MaterialContentGeneratorAgent] All completed - returning final message")
                    return "✅ All Done - you can publish this course now"
                elif result.get("auto_generated") and result.get("generated_material"):
                    # FIXED: When auto-generating next, show the standard approval message
                    print(f"🔍 [MaterialContentGeneratorAgent] Auto-generated with material - showing approval message")
                    generated_material = result.get("generated_material", {})
                    return f"""✅ Content Generated Successfully!

📄 Material: {generated_material.get('title', 'Unknown')}
📊 Content Length: {generated_material.get('content_length', 0):,} characters
🖼️ Images: {'Yes' if generated_material.get('has_images') else 'No'}

Preview is ready! Please review the generated content and choose:
• **Approve & Continue** to move to the next slide
• **Request Modifications** if you'd like changes"""
                elif result.get("generation_failed"):
                    # Handle generation failure case
                    print(f"🔍 [MaterialContentGeneratorAgent] Generation failed - showing error")
                    next_material = result.get("next_material", {})
                    return f"❌ Failed to generate content for {next_material.get('title', 'next material')}: {result.get('generation_error', 'Unknown error')}"
                elif result.get("continue_generation"):
                    # CRITICAL FIX: Handle continue_generation cases properly
                    if result.get("generated_material"):
                        # We have generated material - show the standard approval message
                        print(f"🔍 [MaterialContentGeneratorAgent] Continue generation with material - showing approval message")
                        generated_material = result.get("generated_material", {})
                        return f"""✅ Content Generated Successfully!

📄 Material: {generated_material.get('title', 'Unknown')}
📊 Content Length: {generated_material.get('content_length', 0):,} characters
🖼️ Images: {'Yes' if generated_material.get('has_images') else 'No'}

Preview is ready! Please review the generated content and choose:
• **Approve & Continue** to move to the next slide
• **Request Modifications** if you'd like changes"""
                    else:
                        # No generated material - either generation failed or still in progress
                        print(f"🔍 [MaterialContentGeneratorAgent] Continue generation without material")
                        next_material = result.get("next_material", {})
                        if result.get("generation_failed"):
                            return f"❌ Failed to auto-generate content for {next_material.get('title', 'next material')}. Please try again."
                        else:
                            # Generation is in progress or will start
                            return f"🚀 Generating content for {next_material.get('title', 'next material')}..."
                else:
                    # CRITICAL FIX: This is the fallback case - ensure we don't get stuck here
                    print(f"🔍 [MaterialContentGeneratorAgent] Approval success but no continue_generation flag")
                    print(f"   This might indicate all materials are complete or there's an issue")
                    return "✅ Content approved successfully."
            else:
                return f"❌ Failed: {result.get('error', 'Unknown error')}"
        
        # Handle content modification - SIMPLIFIED
        if "content_modified" in function_results:
            result = function_results["content_modified"]
            if result.get("success"):
                material = result.get("material", {})
                return f"Modified content for **{material.get('title', 'Unknown')}**"
            else:
                return f"❌ Failed: {result.get('error', 'Unknown error')}"
        
        # Handle specific slide generation - SIMPLIFIED
        if "specific_slide_generated" in function_results:
            result = function_results["specific_slide_generated"]
            if result.get("success"):
                material = result.get("material", {})
                return f"Generated content for **{material.get('title', 'Unknown')}**"
            else:
                return f"❌ Failed: {result.get('error', 'Unknown error')}"
        
        # Handle specific slide editing - SIMPLIFIED
        if "specific_slide_edited" in function_results:
            result = function_results["specific_slide_edited"]
            if result.get("success"):
                material = result.get("material", {})
                return f"Edited content for **{material.get('title', 'Unknown')}**"
            else:
                return f"❌ Failed: {result.get('error', 'Unknown error')}"
        
        # Handle slide search results - KEEP DETAILED (useful for user)
        if "slides_found" in function_results:
            result = function_results["slides_found"]
            if result.get("success"):
                total_found = result.get("total_found", 0)
                materials = result.get("materials", [])
                
                if total_found == 0:
                    return "No materials found"
                
                response = f"Found {total_found} materials:\n"
                for i, material in enumerate(materials[:3], 1):
                    response += f"{i}. {material.get('title', 'Unknown')}\n"
                
                if total_found > 3:
                    response += f"...and {total_found - 3} more"
                return response
            else:
                return f"❌ Failed: {result.get('error', 'Unknown error')}"
        
        # Handle targeted edits - SIMPLIFIED
        if "slide_content_edited_targeted" in function_results:
            result = function_results["slide_content_edited_targeted"]
            if result.get("success"):
                if result.get("requires_approval"):
                    material_title = result.get("material_title", "Unknown")
                    return f"Preview changes for **{material_title}**"
                else:
                    return "✅ Changes applied"
            else:
                return f"❌ Failed: {result.get('error', 'Unknown error')}"
        
        # Handle targeted edit application - SIMPLIFIED
        if "targeted_edit_applied" in function_results:
            result = function_results["targeted_edit_applied"]
            if result.get("success"):
                if result.get("applied"):
                    return "✅ Changes saved"
                else:
                    return "Changes cancelled"
            else:
                return f"❌ Failed: {result.get('error', 'Unknown error')}"
        
        return base_response or "Operation completed"
    
    async def get_content_generation_status(self, course_id: str) -> Dict[str, Any]:
        """Get the current status of content generation for a course"""
        try:
            # Get total materials count
            db = await self.db.get_database()
            total_materials = await db.content_materials.count_documents({"course_id": ObjectId(course_id)})
            
            # Get completed materials count
            completed_materials = await db.content_materials.count_documents({
                "course_id": ObjectId(course_id),
                "content_status": "completed"
            })
            
            # Get materials by status
            status_counts = {}
            statuses = ["not done", "generating", "completed"]
            
            for status in statuses:
                count = await db.content_materials.count_documents({
                    "course_id": ObjectId(course_id),
                    "content_status": status
                })
                status_counts[status] = count
            
            # Get next material to process
            next_material = await self._get_next_material_to_process(course_id)
            
            return {
                "success": True,
                "total_materials": total_materials,
                "completed_materials": completed_materials,
                "progress_percentage": (completed_materials / total_materials * 100) if total_materials > 0 else 0,
                "status_breakdown": status_counts,
                "next_material": {
                    "id": str(next_material["_id"]),
                    "title": next_material["title"],
                    "module_number": next_material["module_number"],
                    "chapter_number": next_material["chapter_number"],
                    "material_type": next_material["material_type"]
                } if next_material else None,
                "is_complete": completed_materials == total_materials and total_materials > 0
            }
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error getting content generation status: {e}")
            return {"success": False, "error": f"Failed to get status: {str(e)}"}
    
    async def _generate_specific_slide_content(self, course_id: str, slide_description: str) -> Dict[str, Any]:
        """Generate content for a specific slide by natural language description"""
        try:
            print(f"🎯 [MaterialContentGeneratorAgent] Generating content for specific slide: '{slide_description}' in course {course_id}")
            
            # Validate course_id format
            if not self._is_valid_object_id(course_id):
                return {"success": False, "error": f"Invalid course ID format: '{course_id}'"}
            
            # Find the material matching the description
            material_result = await self._find_material_by_description(course_id, slide_description)
            
            if not material_result["success"]:
                return material_result
            
            if not material_result.get("materials"):
                return {"success": False, "error": f"No materials found matching: '{slide_description}'"}
            
            # If multiple matches, use the first one (most relevant)
            materials = material_result["materials"]
            if len(materials) > 1:
                print(f"⚠️ [MaterialContentGeneratorAgent] Multiple matches found, using first match: {materials[0]['title']}")
            
            target_material = materials[0]
            material_id = target_material["id"]
            
            # Generate content for the specific material
            result = await self._generate_slide_content(material_id)
            
            if result["success"]:
                result["targeted_slide"] = {
                    "description": slide_description,
                    "matched_title": target_material["title"],
                    "location": f"Module {target_material['module_number']}, Chapter {target_material['chapter_number']}"
                }
            
            return result
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error generating specific slide content: {e}")
            return {"success": False, "error": f"Failed to generate specific slide content: {str(e)}"}
    
    async def _edit_specific_slide_content(self, course_id: str, slide_description: str, modification_request: str) -> Dict[str, Any]:
        """Edit/modify content for a specific slide by natural language description"""
        try:
            print(f"✏️ [MaterialContentGeneratorAgent] Editing specific slide: '{slide_description}' in course {course_id}")
            
            # Validate course_id format
            if not self._is_valid_object_id(course_id):
                return {"success": False, "error": f"Invalid course ID format: '{course_id}'"}
            
            # Find the material matching the description
            material_result = await self._find_material_by_description(course_id, slide_description)
            
            if not material_result["success"]:
                return material_result
            
            if not material_result.get("materials"):
                return {"success": False, "error": f"No materials found matching: '{slide_description}'"}
            
            # If multiple matches, use the first one (most relevant)
            materials = material_result["materials"]
            if len(materials) > 1:
                print(f"⚠️ [MaterialContentGeneratorAgent] Multiple matches found, using first match: {materials[0]['title']}")
            
            target_material = materials[0]
            material_id = target_material["id"]
            
            # Check if material has existing content
            db = await self.db.get_database()
            material_doc = await db.content_materials.find_one({"_id": ObjectId(material_id)})
            
            if not material_doc:
                return {"success": False, "error": "Material not found"}
            
            if not material_doc.get("content"):
                return {"success": False, "error": f"No existing content found for '{target_material['title']}'. Please generate content first."}
            
            # Modify content for the specific material
            result = await self._modify_content(material_id, modification_request)
            
            if result["success"]:
                result["targeted_slide"] = {
                    "description": slide_description,
                    "matched_title": target_material["title"],
                    "location": f"Module {target_material['module_number']}, Chapter {target_material['chapter_number']}"
                }
            
            return result
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error editing specific slide content: {e}")
            return {"success": False, "error": f"Failed to edit specific slide content: {str(e)}"}
    
    async def _find_slide_by_description(self, course_id: str, search_description: str) -> Dict[str, Any]:
        """Find and list slides/materials matching a natural language description"""
        try:
            print(f"🔍 [MaterialContentGeneratorAgent] Searching for slides: '{search_description}' in course {course_id}")
            
            # Validate course_id format
            if not self._is_valid_object_id(course_id):
                return {"success": False, "error": f"Invalid course ID format: '{course_id}'"}
            
            # Find materials matching the description
            material_result = await self._find_material_by_description(course_id, search_description, limit=10)
            
            if not material_result["success"]:
                return material_result
            
            materials = material_result.get("materials", [])
            
            return {
                "success": True,
                "search_description": search_description,
                "total_found": len(materials),
                "materials": materials
            }
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error finding slides: {e}")
            return {"success": False, "error": f"Failed to find slides: {str(e)}"}
    
    async def _find_material_by_description(self, course_id: str, description: str, limit: int = 5) -> Dict[str, Any]:
        """Find materials matching a natural language description using AI-powered search"""
        try:
            # Get all materials for the course
            db = await self.db.get_database()
            all_materials = await db.content_materials.find(
                {"course_id": ObjectId(course_id)},
                sort=[("module_number", 1), ("chapter_number", 1), ("slide_number", 1)]
            ).to_list(None)
            
            if not all_materials:
                return {"success": False, "error": "No materials found in course"}
            
            # Use AI to match the description to materials
            matching_result = await self._ai_match_materials(description, all_materials, limit)
            
            return matching_result
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error finding material by description: {e}")
            return {"success": False, "error": f"Failed to find material: {str(e)}"}
    
    async def _ai_match_materials(self, description: str, materials: List[Dict[str, Any]], limit: int = 5) -> Dict[str, Any]:
        """Use AI to match natural language description to materials"""
        try:
            # Create materials summary for AI
            materials_summary = []
            for i, material in enumerate(materials):
                materials_summary.append({
                    "index": i,
                    "id": str(material["_id"]),
                    "title": material["title"],
                    "type": material["material_type"],
                    "module": material["module_number"],
                    "chapter": material["chapter_number"],
                    "slide": material.get("slide_number", 1),
                    "description": material.get("description", "")[:200]  # Truncate long descriptions
                })
            
            # Create AI prompt for material matching
            system_prompt = f"""You are an intelligent material matching assistant. Your task is to match a user's natural language description to the most relevant course materials.

USER DESCRIPTION: "{description}"

AVAILABLE MATERIALS:
{json.dumps(materials_summary, indent=2)}

MATCHING INSTRUCTIONS:
1. Analyze the user's description for:
   - Specific slide numbers (e.g., "slide 1", "first slide")
   - Module/chapter references (e.g., "chapter 1.1", "module 2")
   - Content keywords (e.g., "management", "assessment", "introduction")
   - Material types (e.g., "slide", "assessment", "quiz")

2. Rank materials by relevance:
   - Exact matches (slide number + chapter) = highest priority
   - Partial matches (chapter or keywords) = medium priority
   - General matches (material type or topic) = lower priority

3. Return the top {limit} most relevant matches

RESPONSE FORMAT (JSON only):
{{
    "success": true,
    "matches": [
        {{
            "index": 0,
            "relevance_score": 0.95,
            "match_reason": "Exact match: slide 1 of chapter 1.1"
        }},
        {{
            "index": 2,
            "relevance_score": 0.80,
            "match_reason": "Partial match: contains 'management' keyword"
        }}
    ]
}}

If no good matches found, return: {{"success": false, "error": "No relevant materials found"}}"""

            user_prompt = f"Find the most relevant materials for: '{description}'"

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await self.openai.create_chat_completion(
                model=self.model,
                messages=messages,
                max_tokens=1000,
                temperature=0.1  # Low temperature for consistent matching
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Clean up response if it has markdown formatting
            if ai_response.startswith('```json'):
                ai_response = ai_response.replace('```json', '').replace('```', '').strip()
            elif ai_response.startswith('```'):
                ai_response = ai_response.replace('```', '').strip()
            
            # Parse AI response
            try:
                match_result = json.loads(ai_response)
            except json.JSONDecodeError:
                # Fallback to simple text matching
                return await self._fallback_text_matching(description, materials, limit)
            
            if not match_result.get("success"):
                return {"success": False, "error": match_result.get("error", "No matches found")}
            
            # Convert AI matches to material objects
            matched_materials = []
            for match in match_result.get("matches", []):
                material_index = match["index"]
                if 0 <= material_index < len(materials):
                    material = materials[material_index]
                    matched_materials.append({
                        "id": str(material["_id"]),
                        "title": material["title"],
                        "material_type": material["material_type"],
                        "module_number": material["module_number"],
                        "chapter_number": material["chapter_number"],
                        "slide_number": material.get("slide_number", 1),
                        "description": material.get("description", ""),
                        "content_status": material.get("content_status", "not done"),
                        "relevance_score": match.get("relevance_score", 0.5),
                        "match_reason": match.get("match_reason", "AI matched")
                    })
            
            return {
                "success": True,
                "materials": matched_materials[:limit]
            }
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] AI material matching error: {e}")
            # Fallback to simple text matching
            return await self._fallback_text_matching(description, materials, limit)
    
    async def _fallback_text_matching(self, description: str, materials: List[Dict[str, Any]], limit: int = 5) -> Dict[str, Any]:
        """Fallback text-based material matching when AI fails"""
        try:
            description_lower = description.lower()
            matched_materials = []
            
            # Simple scoring based on keyword matches
            for material in materials:
                score = 0
                match_reasons = []
                
                # Check for exact slide/chapter patterns
                title_lower = material["title"].lower()
                desc_lower = material.get("description", "").lower()
                
                # Module/chapter matching
                if f"module {material['module_number']}" in description_lower:
                    score += 30
                    match_reasons.append(f"Module {material['module_number']} match")
                
                if f"chapter {material['chapter_number']}" in description_lower:
                    score += 25
                    match_reasons.append(f"Chapter {material['chapter_number']} match")
                
                # Slide number matching
                slide_num = material.get("slide_number", 1)
                if f"slide {slide_num}" in description_lower or f"slide{slide_num}" in description_lower:
                    score += 40
                    match_reasons.append(f"Slide {slide_num} match")
                
                # Material type matching
                if material["material_type"].lower() in description_lower:
                    score += 15
                    match_reasons.append(f"{material['material_type']} type match")
                
                # Title keyword matching
                title_words = title_lower.split()
                desc_words = description_lower.split()
                common_words = set(title_words) & set(desc_words)
                if common_words:
                    score += len(common_words) * 5
                    match_reasons.append(f"Title keywords: {', '.join(common_words)}")
                
                # Description keyword matching
                if desc_lower:
                    desc_title_words = desc_lower.split()
                    common_desc_words = set(desc_title_words) & set(desc_words)
                    if common_desc_words:
                        score += len(common_desc_words) * 3
                        match_reasons.append(f"Description keywords: {', '.join(list(common_desc_words)[:3])}")
                
                if score > 0:
                    matched_materials.append({
                        "id": str(material["_id"]),
                        "title": material["title"],
                        "material_type": material["material_type"],
                        "module_number": material["module_number"],
                        "chapter_number": material["chapter_number"],
                        "slide_number": material.get("slide_number", 1),
                        "description": material.get("description", ""),
                        "content_status": material.get("content_status", "not done"),
                        "relevance_score": min(score / 100.0, 1.0),  # Normalize to 0-1
                        "match_reason": "; ".join(match_reasons) if match_reasons else "Text similarity"
                    })
            
            # Sort by relevance score (descending)
            matched_materials.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            return {
                "success": True,
                "materials": matched_materials[:limit]
            }
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Fallback text matching error: {e}")
            return {"success": False, "error": f"Failed to match materials: {str(e)}"}
    
    async def _send_streaming_event(self, event_data: Dict[str, Any]) -> None:
        """Send streaming event to frontend via message service"""
        try:
            # Use the message service to send streaming events
            # This will be handled by the SSE endpoint in the routes
            await self.messages.send_streaming_event(event_data)
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error sending streaming event: {e}")
    
    def _clean_content(self, content: str) -> str:
        """Clean and decode content to fix HTML entities, encoding issues, and markdown code block wrappers"""
        try:
            # Step 1: Remove markdown code block wrappers if present
            # Check if content is wrapped in ```markdown ... ``` or ``` ... ```
            cleaned_content = content.strip()
            
            # Remove markdown code block wrapper
            if cleaned_content.startswith('```markdown'):
                # Find the closing ```
                end_marker = cleaned_content.find('```', 11)  # Start after '```markdown'
                if end_marker != -1:
                    cleaned_content = cleaned_content[11:end_marker].strip()
                    print(f"🧹 [MaterialContentGeneratorAgent] Removed markdown code block wrapper")
            elif cleaned_content.startswith('```'):
                # Generic code block wrapper
                end_marker = cleaned_content.find('```', 3)  # Start after first '```'
                if end_marker != -1:
                    cleaned_content = cleaned_content[3:end_marker].strip()
                    print(f"🧹 [MaterialContentGeneratorAgent] Removed generic code block wrapper")
            
            # Step 2: Decode HTML entities (like &quot;, &amp;, etc.)
            cleaned_content = html.unescape(cleaned_content)
            
            # Step 3: Fix common encoding issues
            # Replace common HTML entity patterns that might not be caught by html.unescape
            encoding_fixes = {
                '\u00e2\u0080\u0099': "'",  # Right single quotation mark
                '\u00e2\u0080\u009c': '"',  # Left double quotation mark
                '\u00e2\u0080\u009d': '"',  # Right double quotation mark
                '\u00e2\u0080\u0094': '—',  # Em dash
                '\u00e2\u0080\u0093': '–',  # En dash
                '\u00e2\u0080\u00a2': '•',  # Bullet point
                '\u00e2\u0080\u00a6': '…',  # Horizontal ellipsis
                '\u00c3\u00a1': 'á',       # á with acute
                '\u00c3\u00a9': 'é',       # é with acute
                '\u00c3\u00ad': 'í',       # í with acute
                '\u00c3\u00b3': 'ó',       # ó with acute
                '\u00c3\u00ba': 'ú',       # ú with acute
                '\u00c3\u00b1': 'ñ',       # ñ with tilde
                '\u00c3\u00bc': 'ü',       # ü with diaeresis
                # Common emoji encoding issues
                'â€™': "'",  # Alternative encoding for right single quote
                'â€œ': '"',  # Alternative encoding for left double quote
                'â€': '"',   # Alternative encoding for right double quote
                'â€"': '—',  # Alternative encoding for em dash
                'â€"': '–',  # Alternative encoding for en dash
                'â€¢': '•',  # Alternative encoding for bullet
                'â€¦': '…',  # Alternative encoding for ellipsis
            }
            
            for bad_encoding, correct_char in encoding_fixes.items():
                cleaned_content = cleaned_content.replace(bad_encoding, correct_char)
            
            # Step 4: Normalize Unicode characters
            cleaned_content = unicodedata.normalize('NFC', cleaned_content)
            
            # Step 5: Fix any remaining encoding issues by ensuring proper UTF-8
            try:
                # Try to encode and decode to catch any remaining issues
                cleaned_content = cleaned_content.encode('utf-8', errors='ignore').decode('utf-8')
            except UnicodeError:
                # If there are still issues, use a more aggressive approach
                cleaned_content = cleaned_content.encode('ascii', errors='ignore').decode('ascii')
            
            # Step 6: Clean up any double-encoded entities
            # Sometimes content gets double-encoded, so we run unescape again
            cleaned_content = html.unescape(cleaned_content)
            
            # Step 7: Final cleanup - remove any remaining empty code block markers
            cleaned_content = re.sub(r'^```\s*$', '', cleaned_content, flags=re.MULTILINE)
            cleaned_content = cleaned_content.strip()
            
            print(f"🧹 [MaterialContentGeneratorAgent] Content cleaned: {len(content)} -> {len(cleaned_content)} characters")
            
            return cleaned_content
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error cleaning content: {e}")
            # Return original content if cleaning fails
            return content
    
    def _get_material_file_path(self, material: Dict[str, Any]) -> str:
        """Generate file path for material based on its properties"""
        try:
            # Create a path similar to the course structure
            module_num = material.get("module_number", 1)
            chapter_num = material.get("chapter_number", 1)
            slide_num = material.get("slide_number", 1)
            
            # Sanitize title for path
            title_sanitized = self._sanitize_filename(material.get("title", "untitled"))
            
            # Create path: /content/module-X/chapter-X-Y/slide-Z-title.md
            file_path = f"/content/module-{module_num}/chapter-{module_num}-{chapter_num}/{title_sanitized}.md"
            
            return file_path
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error generating file path: {e}")
            return f"/content/material-{material.get('_id', 'unknown')}.md"
    
    async def _edit_slide_content_targeted(self, course_id: str, slide_reference: str, edit_instruction: str, current_slide_id: Optional[str] = None) -> Dict[str, Any]:
        """Make targeted edits to specific slide content via natural language with diff preview"""
        try:
            print(f"🎯 [MaterialContentGeneratorAgent] Starting targeted edit for slide: '{slide_reference}' with instruction: '{edit_instruction}'")
            
            # Validate course_id format
            if not self._is_valid_object_id(course_id):
                return {"success": False, "error": f"Invalid course ID format: '{course_id}'"}
            
            # Resolve slide reference to material
            material_result = await self._resolve_slide_reference(course_id, slide_reference, current_slide_id)
            
            if not material_result["success"]:
                return material_result
            
            material_id = material_result["material_id"]
            material_title = material_result["material_title"]
            
            # Get current content
            db = await self.db.get_database()
            material = await db.content_materials.find_one({"_id": ObjectId(material_id)})
            
            if not material:
                return {"success": False, "error": "Material not found"}
            
            if not material.get("content"):
                return {"success": False, "error": f"No existing content found for '{material_title}'. Please generate content first."}
            
            current_content = material["content"]
            
            # Analyze the edit request
            analysis_result = await self._analyze_targeted_edit_request(current_content, edit_instruction)
            
            if not analysis_result["success"]:
                return analysis_result
            
            # Apply targeted edit using coordinate detection
            if analysis_result["edit_type"] == "simple_text_replacement":
                # Use LLM coordinate detection for precise edits
                coordinates = await self._get_llm_coordinates_for_edit(current_content, edit_instruction)
                
                if coordinates["success"]:
                    modified_content = self._apply_coordinate_based_edit(current_content, coordinates)
                else:
                    # Fallback to AI-based modification
                    modified_content = await self._apply_ai_based_edit(current_content, edit_instruction, material)
            else:
                # Use AI for complex edits
                modified_content = await self._apply_ai_based_edit(current_content, edit_instruction, material)
            
            # Return diff preview for user approval
            return {
                "success": True,
                "edit_type": "targeted_modification",
                "material_id": material_id,
                "material_title": material_title,
                "slide_reference": slide_reference,
                "edit_instruction": edit_instruction,
                "original_content": current_content,
                "modified_content": modified_content,
                "changes_summary": analysis_result.get("description", "Content modified based on request"),
                "requires_approval": True,
                "edit_preview": {
                    "change_type": analysis_result["edit_type"],
                    "target_section": analysis_result.get("target_section", "Content"),
                    "description": analysis_result.get("description", "Content modified")
                }
            }
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error in targeted edit: {e}")
            return {"success": False, "error": f"Failed to perform targeted edit: {str(e)}"}
    
    async def _apply_targeted_edit(self, material_id: str, approved: bool, modified_content: Optional[str] = None) -> Dict[str, Any]:
        """Apply approved targeted edit changes to slide content"""
        try:
            print(f"🎯 [MaterialContentGeneratorAgent] Applying targeted edit for material {material_id}, approved: {approved}")
            
            if not self._is_valid_object_id(material_id):
                return {"success": False, "error": f"Invalid material ID format: '{material_id}'"}
            
            db = await self.db.get_database()
            material = await db.content_materials.find_one({"_id": ObjectId(material_id)})
            
            if not material:
                return {"success": False, "error": "Material not found"}
            
            if approved and modified_content:
                # Apply the approved changes
                await db.content_materials.update_one(
                    {"_id": ObjectId(material_id)},
                    {
                        "$set": {
                            "content": modified_content,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                
                # Update R2 storage if it's not an assessment
                is_assessment = material.get('material_type') == 'assessment'
                if not is_assessment:
                    course = await self.db.find_course(str(material["course_id"]))
                    if course:
                        r2_result = await self._store_content_in_r2(material, modified_content, course)
                        
                        if r2_result["success"]:
                            await db.content_materials.update_one(
                                {"_id": ObjectId(material_id)},
                                {
                                    "$set": {
                                        "r2_key": r2_result["r2_key"],
                                        "public_url": r2_result["public_url"],
                                        "updated_at": datetime.utcnow()
                                    }
                                }
                            )
                
                return {
                    "success": True,
                    "applied": True,
                    "material_id": material_id,
                    "material_title": material["title"],
                    "message": f"Targeted edit applied successfully to '{material['title']}'"
                }
            else:
                # Edit was rejected
                return {
                    "success": True,
                    "applied": False,
                    "material_id": material_id,
                    "material_title": material["title"],
                    "message": "Targeted edit was not applied"
                }
                
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error applying targeted edit: {e}")
            return {"success": False, "error": f"Failed to apply targeted edit: {str(e)}"}
    
    async def _resolve_slide_reference(self, course_id: str, slide_reference: str, current_slide_id: Optional[str] = None) -> Dict[str, Any]:
        """Resolve natural language slide reference to material ID"""
        try:
            # Handle "current slide" reference
            if "current slide" in slide_reference.lower() and current_slide_id:
                if self._is_valid_object_id(current_slide_id):
                    db = await self.db.get_database()
                    material = await db.content_materials.find_one({"_id": ObjectId(current_slide_id)})
                    if material:
                        return {
                            "success": True,
                            "material_id": current_slide_id,
                            "material_title": material["title"]
                        }
            
            # Use existing material finding logic
            material_result = await self._find_material_by_description(course_id, slide_reference, limit=1)
            
            if not material_result["success"]:
                return material_result
            
            materials = material_result.get("materials", [])
            if not materials:
                return {"success": False, "error": f"No materials found matching: '{slide_reference}'"}
            
            target_material = materials[0]
            return {
                "success": True,
                "material_id": target_material["id"],
                "material_title": target_material["title"]
            }
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error resolving slide reference: {e}")
            return {"success": False, "error": f"Failed to resolve slide reference: {str(e)}"}
    
    async def _analyze_targeted_edit_request(self, current_content: str, edit_instruction: str) -> Dict[str, Any]:
        """Analyze the targeted edit request to determine edit type and approach"""
        try:
            # Use AI to analyze the edit request
            analysis_prompt = f"""You are an expert content editor. Analyze this edit request and determine the best approach.

CURRENT CONTENT (first 500 chars):
{current_content[:500]}...

EDIT INSTRUCTION: {edit_instruction}

Analyze this request and determine:
1. What type of edit is needed
2. What specific content needs to be changed
3. A clear description of the change

Respond in JSON format:
{{
    "success": true,
    "edit_type": "simple_text_replacement|content_addition|content_removal|structure_change|complex_modification",
    "target_section": "Brief description of what section is being modified",
    "description": "Clear description of what will be changed",
    "complexity": "low|medium|high",
    "confidence": "high|medium|low"
}}"""

            messages = [
                {"role": "system", "content": "You are an expert content analysis assistant."},
                {"role": "user", "content": analysis_prompt}
            ]
            
            response = await self.openai.create_chat_completion(
                model=self.model,
                messages=messages,
                temperature=0.3
            )
            
            analysis_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                if "```json" in analysis_text:
                    json_start = analysis_text.find("```json") + 7
                    json_end = analysis_text.find("```", json_start)
                    analysis_text = analysis_text[json_start:json_end].strip()
                elif "```" in analysis_text:
                    json_start = analysis_text.find("```") + 3
                    json_end = analysis_text.find("```", json_start)
                    analysis_text = analysis_text[json_start:json_end].strip()
                
                analysis_result = json.loads(analysis_text)
                analysis_result["success"] = True
                return analysis_result
                
            except json.JSONDecodeError:
                # Fallback analysis
                return {
                    "success": True,
                    "edit_type": "complex_modification",
                    "target_section": "Content",
                    "description": f"Apply requested changes: {edit_instruction}",
                    "complexity": "medium",
                    "confidence": "medium"
                }
                
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error analyzing edit request: {e}")
            return {"success": False, "error": f"Failed to analyze edit request: {str(e)}"}
    
    async def _get_llm_coordinates_for_edit(self, content: str, edit_instruction: str) -> Dict[str, Any]:
        """Use LLM to get precise coordinates for targeted edits (similar to course-design agent)"""
        try:
            # Split content into numbered lines for reference
            lines = content.split('\n')
            numbered_content = ""
            for i, line in enumerate(lines, 1):
                numbered_content += f"{i:3d}: {line}\n"
            
            coordinate_prompt = f"""You are an expert content analyzer. Find the EXACT location for this edit request.

NUMBERED CONTENT:
{numbered_content}

EDIT INSTRUCTION: {edit_instruction}

Your task:
1. Identify exactly what text needs to be changed
2. Find the precise line number(s) where this text appears
3. Determine the exact text to replace and what to replace it with

Respond in JSON format:
{{
    "success": true,
    "target_section": "Brief description of what section is being modified",
    "start_line": 15,
    "end_line": 15,
    "exact_text_to_replace": "The exact text that needs to be replaced",
    "replacement_text": "What to replace it with",
    "context_before": "Text that appears before the target",
    "context_after": "Text that appears after the target",
    "confidence": "high|medium|low"
}}"""

            messages = [
                {"role": "system", "content": "You are an expert content coordinate detection assistant."},
                {"role": "user", "content": coordinate_prompt}
            ]
            
            response = await self.openai.create_chat_completion(
                model=self.model,
                messages=messages,
                temperature=0.1
            )
            
            coordinate_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                if "```json" in coordinate_text:
                    json_start = coordinate_text.find("```json") + 7
                    json_end = coordinate_text.find("```", json_start)
                    coordinate_text = coordinate_text[json_start:json_end].strip()
                elif "```" in coordinate_text:
                    json_start = coordinate_text.find("```") + 3
                    json_end = coordinate_text.find("```", json_start)
                    coordinate_text = coordinate_text[json_start:json_end].strip()
                
                coordinates = json.loads(coordinate_text)
                
                # Validate coordinates
                if self._validate_edit_coordinates(coordinates, lines):
                    return coordinates
                else:
                    return {"success": False, "error": "Invalid coordinates"}
                    
            except json.JSONDecodeError:
                return {"success": False, "error": "Failed to parse coordinates"}
                
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error getting LLM coordinates: {e}")
            return {"success": False, "error": f"Coordinate detection failed: {str(e)}"}
    
    def _validate_edit_coordinates(self, coordinates: Dict[str, Any], lines: List[str]) -> bool:
        """Validate that the edit coordinates make sense"""
        try:
            start_line = coordinates.get("start_line", 0)
            end_line = coordinates.get("end_line", 0)
            exact_text = coordinates.get("exact_text_to_replace", "")
            
            # Check line numbers are valid
            if start_line < 1 or start_line > len(lines):
                return False
            
            if end_line < 1 or end_line > len(lines):
                return False
            
            # Check that the exact text exists in the specified line(s)
            target_lines = lines[start_line-1:end_line]
            combined_text = '\n'.join(target_lines)
            
            if exact_text and exact_text not in combined_text:
                return False
            
            return True
            
        except Exception:
            return False
    
    def _apply_coordinate_based_edit(self, content: str, coordinates: Dict[str, Any]) -> str:
        """Apply targeted edit using LLM-provided coordinates with precise replacement"""
        try:
            lines = content.split('\n')
            start_line = coordinates['start_line'] - 1  # Convert to 0-indexed
            end_line = coordinates['end_line'] - 1
            exact_text = coordinates['exact_text_to_replace']
            replacement_text = coordinates['replacement_text']
            
            print(f"🎯 [MaterialContentGeneratorAgent] Applying coordinate-based edit:")
            print(f"   Lines: {start_line + 1}-{end_line + 1}")
            print(f"   Target: '{exact_text[:50]}...'")
            print(f"   Replacement: '{replacement_text[:50]}...'")
            
            # Validate line numbers
            if start_line < 0 or end_line >= len(lines) or start_line > end_line:
                print(f"❌ [MaterialContentGeneratorAgent] Invalid line numbers: {start_line + 1}-{end_line + 1}")
                raise ValueError(f"Invalid line numbers: {start_line + 1}-{end_line + 1}")
            
            # Get the target text from the specified lines
            target_lines = lines[start_line:end_line + 1]
            target_content = '\n'.join(target_lines)
            
            # Verify the exact text exists in the target lines
            if exact_text not in target_content:
                print(f"⚠️ [MaterialContentGeneratorAgent] Exact text not found in target lines")
                print(f"   Expected: '{exact_text}'")
                print(f"   Found: '{target_content}'")
                # Try partial matching
                if any(word in target_content for word in exact_text.split() if len(word) > 3):
                    print(f"   Applying partial replacement...")
                    # Replace the entire line range with the replacement text
                    lines[start_line:end_line + 1] = [replacement_text]
                else:
                    raise ValueError("Target text not found in specified lines")
            else:
                # Apply precise replacement
                modified_content = target_content.replace(exact_text, replacement_text, 1)
                modified_lines = modified_content.split('\n')
                lines[start_line:end_line + 1] = modified_lines
            
            result = '\n'.join(lines)
            print(f"✅ [MaterialContentGeneratorAgent] Coordinate-based edit applied successfully")
            return result
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error in coordinate-based edit: {e}")
            raise e
    
    async def _apply_ai_based_edit(self, current_content: str, edit_instruction: str, material: Dict[str, Any]) -> str:
        """Apply AI-based edit for complex modifications with precise targeting and image generation"""
        try:
            # Check if this is an image addition request
            if self._is_image_addition_request(edit_instruction):
                return await self._handle_image_addition_edit(current_content, edit_instruction, material)
            
            # Step 1: First identify what needs to be changed
            identification_prompt = f"""You are an expert content analyzer. Identify EXACTLY what needs to be changed in this content.

EDIT INSTRUCTION: {edit_instruction}

CURRENT CONTENT:
{current_content}

Your task:
1. Find the EXACT text that needs to be modified
2. Determine what it should be changed to
3. Provide the precise before/after text

Respond in JSON format:
{{
    "success": true,
    "target_text": "The exact text that needs to be changed",
    "replacement_text": "What it should be changed to",
    "context_before": "Text that appears before the target (for verification)",
    "context_after": "Text that appears after the target (for verification)",
    "change_type": "replacement|addition|removal",
    "confidence": "high|medium|low"
}}

If you cannot identify a specific target, respond with success: false and explain why."""

            messages = [
                {"role": "system", "content": "You are an expert content analysis assistant specializing in precise text identification."},
                {"role": "user", "content": identification_prompt}
            ]
            
            response = await self.openai.create_chat_completion(
                model=self.model,
                messages=messages,
                temperature=0.1,
                max_tokens=1000
            )
            
            identification_text = response.choices[0].message.content.strip()
            
            # Parse the identification result
            try:
                if "```json" in identification_text:
                    json_start = identification_text.find("```json") + 7
                    json_end = identification_text.find("```", json_start)
                    identification_text = identification_text[json_start:json_end].strip()
                elif "```" in identification_text:
                    json_start = identification_text.find("```") + 3
                    json_end = identification_text.find("```", json_start)
                    identification_text = identification_text[json_start:json_end].strip()
                
                identification_result = json.loads(identification_text)
                
                if identification_result.get("success") and identification_result.get("target_text"):
                    # Step 2: Apply the precise change
                    target_text = identification_result["target_text"]
                    replacement_text = identification_result["replacement_text"]
                    
                    print(f"🎯 [MaterialContentGeneratorAgent] Applying precise edit:")
                    print(f"   Target: '{target_text[:100]}...'")
                    print(f"   Replacement: '{replacement_text[:100]}...'")
                    
                    # Perform the targeted replacement
                    if target_text in current_content:
                        modified_content = current_content.replace(target_text, replacement_text, 1)  # Replace only first occurrence
                        print(f"✅ [MaterialContentGeneratorAgent] Precise replacement successful")
                        return modified_content
                    else:
                        print(f"⚠️ [MaterialContentGeneratorAgent] Target text not found, falling back to fuzzy matching")
                        # Try fuzzy matching for similar text
                        return await self._apply_fuzzy_edit(current_content, target_text, replacement_text)
                else:
                    print(f"⚠️ [MaterialContentGeneratorAgent] Could not identify precise target, using fallback method")
                    return await self._apply_fallback_edit(current_content, edit_instruction)
                    
            except json.JSONDecodeError:
                print(f"❌ [MaterialContentGeneratorAgent] Failed to parse identification result, using fallback")
                return await self._apply_fallback_edit(current_content, edit_instruction)
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error in AI-based edit: {e}")
            return await self._apply_fallback_edit(current_content, edit_instruction)
    
    async def _apply_fuzzy_edit(self, current_content: str, target_text: str, replacement_text: str) -> str:
        """Apply edit using fuzzy text matching when exact match fails"""
        try:
            # Split target text into words for fuzzy matching
            target_words = target_text.split()
            content_lines = current_content.split('\n')
            
            # Find the line that contains most of the target words
            best_match_line = -1
            best_match_score = 0
            
            for i, line in enumerate(content_lines):
                line_words = line.lower().split()
                matches = sum(1 for word in target_words if word.lower() in line_words)
                score = matches / len(target_words) if target_words else 0
                
                if score > best_match_score and score > 0.5:  # At least 50% match
                    best_match_score = score
                    best_match_line = i
            
            if best_match_line >= 0:
                # Replace the matched line
                content_lines[best_match_line] = replacement_text
                print(f"✅ [MaterialContentGeneratorAgent] Fuzzy replacement applied to line {best_match_line + 1}")
                return '\n'.join(content_lines)
            else:
                print(f"⚠️ [MaterialContentGeneratorAgent] Fuzzy matching failed, using fallback")
                return await self._apply_fallback_edit(current_content, f"Replace '{target_text}' with '{replacement_text}'")
                
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error in fuzzy edit: {e}")
            return await self._apply_fallback_edit(current_content, f"Replace '{target_text}' with '{replacement_text}'")
    
    async def _apply_fallback_edit(self, current_content: str, edit_instruction: str) -> str:
        """Fallback method that uses very strict instructions to avoid full regeneration"""
        try:
            # Use a very strict prompt that emphasizes minimal changes
            fallback_prompt = f"""You are a precise text editor. Make ONLY the minimal change requested.

CRITICAL RULES:
1. Output the COMPLETE content with ONLY the requested change
2. Do NOT rewrite, rephrase, or improve anything else
3. Keep ALL existing formatting, headers, lists, and structure EXACTLY as is
4. Change ONLY what is specifically requested
5. If you cannot make the specific change, make the closest minimal change possible

EDIT REQUEST: {edit_instruction}

CONTENT TO EDIT:
{current_content}

Make the minimal change and return the complete content."""

            messages = [
                {"role": "system", "content": "You are a minimal-change text editor. You make only the specific requested change and nothing else."},
                {"role": "user", "content": fallback_prompt}
            ]
            
            response = await self.openai.create_chat_completion(
                model=self.model,
                messages=messages,
                temperature=0.1,  # Very low temperature for consistency
                max_tokens=len(current_content.split()) + 200  # Limit tokens to prevent expansion
            )
            
            modified_content = response.choices[0].message.content.strip()
            cleaned_content = self._clean_content(modified_content)
            
            print(f"✅ [MaterialContentGeneratorAgent] Fallback edit applied")
            return cleaned_content
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error in fallback edit: {e}")
            # If all else fails, return original content
            return current_content
    
    def _is_image_addition_request(self, edit_instruction: str) -> bool:
        """Check if the edit instruction is requesting to add an image"""
        try:
            instruction_lower = edit_instruction.lower()
            image_keywords = [
                'add image', 'add an image', 'insert image', 'include image',
                'add picture', 'add visual', 'add illustration', 'add diagram',
                'image representation', 'visual representation', 'add graphic'
            ]
            
            return any(keyword in instruction_lower for keyword in image_keywords)
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error checking image addition request: {e}")
            return False
    
    async def _handle_image_addition_edit(self, current_content: str, edit_instruction: str, material: Dict[str, Any]) -> str:
        """Handle image addition requests by generating actual images and embedding them"""
        try:
            print(f"🖼️ [MaterialContentGeneratorAgent] Handling image addition request: '{edit_instruction}'")
            
            # Step 1: Analyze where to place the image and what it should show
            image_analysis = await self._analyze_image_addition_request(current_content, edit_instruction, material)
            
            if not image_analysis["success"]:
                print(f"❌ [MaterialContentGeneratorAgent] Image analysis failed: {image_analysis.get('error')}")
                return await self._apply_fallback_edit(current_content, edit_instruction)
            
            # Step 2: Generate the image using C1 agent
            if not self.image_agent:
                print(f"⚠️ [MaterialContentGeneratorAgent] Image agent not available, using placeholder")
                return await self._apply_fallback_edit(current_content, edit_instruction)
            
            image_description = image_analysis["image_description"]
            placement_location = image_analysis["placement_location"]
            
            print(f"🖼️ [MaterialContentGeneratorAgent] Generating image: '{image_description}'")
            
            # Generate image using the image agent
            image_result = await self.image_agent.generate_image_multi_size(
                course_id=str(material["course_id"]),
                image_name=f"{material['title']} - {image_description}",
                image_description=image_description,
                image_type="slide_content",
                filename=f"slide_{material.get('slide_number', 1)}_targeted_edit",
                style_preference="professional_educational",
                dynamic_colors=True
            )
            
            if not image_result["success"]:
                print(f"❌ [MaterialContentGeneratorAgent] Image generation failed: {image_result.get('error')}")
                return await self._apply_fallback_edit(current_content, edit_instruction)
            
            # Step 3: Get the image URL and create markdown
            medium_image_url = image_result["images"]["medium"]["public_url"]
            image_markdown = f"![{image_description}]({medium_image_url})\n*{image_description}*"
            
            print(f"✅ [MaterialContentGeneratorAgent] Image generated successfully: {medium_image_url}")
            
            # Step 4: Insert the image at the specified location
            modified_content = await self._insert_image_at_location(
                current_content, 
                image_markdown, 
                placement_location,
                image_analysis.get("target_text", "")
            )
            
            print(f"✅ [MaterialContentGeneratorAgent] Image inserted successfully")
            return modified_content
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error handling image addition: {e}")
            return await self._apply_fallback_edit(current_content, edit_instruction)
    
    async def _analyze_image_addition_request(self, current_content: str, edit_instruction: str, material: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the image addition request to determine what image to generate and where to place it"""
        try:
            analysis_prompt = f"""You are an expert content analyzer specializing in image placement and description generation.

MATERIAL CONTEXT:
- Title: {material['title']}
- Type: {material['material_type']}
- Course Context: Module {material['module_number']}, Chapter {material['chapter_number']}

EDIT INSTRUCTION: {edit_instruction}

CURRENT CONTENT:
{current_content}

Your task:
1. Determine what image should be generated based on the instruction
2. Create a detailed image description for AI image generation
3. Identify where in the content the image should be placed
4. Find the target text/section for placement

Respond in JSON format:
{{
    "success": true,
    "image_description": "Detailed description for AI image generation (be specific about visual elements, style, and content)",
    "placement_location": "after_paragraph|before_section|after_section|at_end",
    "target_text": "The specific text/heading after which to place the image",
    "alt_text": "Brief alt text for the image",
    "reasoning": "Why this image placement and description makes sense"
}}

Example image descriptions:
- "A professional diagram showing the RAG (Retrieval-Augmented Generation) workflow with three main components: a knowledge base, retrieval system, and language model, connected by arrows showing data flow"
- "An infographic illustrating the benefits of RAG technology with icons and text showing improved accuracy, real-time data access, and reduced hallucinations"

Make the image description detailed and specific for educational content."""

            messages = [
                {"role": "system", "content": "You are an expert educational content and image analysis assistant."},
                {"role": "user", "content": analysis_prompt}
            ]
            
            response = await self.openai.create_chat_completion(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=800
            )
            
            analysis_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                if "```json" in analysis_text:
                    json_start = analysis_text.find("```json") + 7
                    json_end = analysis_text.find("```", json_start)
                    analysis_text = analysis_text[json_start:json_end].strip()
                elif "```" in analysis_text:
                    json_start = analysis_text.find("```") + 3
                    json_end = analysis_text.find("```", json_start)
                    analysis_text = analysis_text[json_start:json_end].strip()
                
                analysis_result = json.loads(analysis_text)
                
                if analysis_result.get("success") and analysis_result.get("image_description"):
                    print(f"✅ [MaterialContentGeneratorAgent] Image analysis successful")
                    return analysis_result
                else:
                    return {"success": False, "error": "Failed to analyze image requirements"}
                    
            except json.JSONDecodeError:
                print(f"❌ [MaterialContentGeneratorAgent] Failed to parse image analysis response")
                return {"success": False, "error": "Failed to parse image analysis"}
                
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error analyzing image addition request: {e}")
            return {"success": False, "error": f"Image analysis failed: {str(e)}"}
    
    async def _insert_image_at_location(self, content: str, image_markdown: str, placement_location: str, target_text: str) -> str:
        """Insert image markdown at the specified location in the content"""
        try:
            lines = content.split('\n')
            
            if placement_location == "at_end":
                # Add image at the end of content
                lines.append("")
                lines.append(image_markdown)
                return '\n'.join(lines)
            
            # Find the target text location
            target_line_index = -1
            for i, line in enumerate(lines):
                if target_text and target_text.strip() in line.strip():
                    target_line_index = i
                    break
            
            if target_line_index == -1:
                # If target text not found, try fuzzy matching
                target_words = target_text.lower().split() if target_text else []
                best_match_index = -1
                best_match_score = 0
                
                for i, line in enumerate(lines):
                    line_words = line.lower().split()
                    matches = sum(1 for word in target_words if word in line_words)
                    score = matches / len(target_words) if target_words else 0
                    
                    if score > best_match_score and score > 0.3:  # At least 30% match
                        best_match_score = score
                        best_match_index = i
                
                target_line_index = best_match_index
            
            if target_line_index >= 0:
                # Insert image based on placement location
                if placement_location == "after_paragraph":
                    # Find the end of the current paragraph
                    insert_index = target_line_index + 1
                    while insert_index < len(lines) and lines[insert_index].strip():
                        insert_index += 1
                    lines.insert(insert_index, "")
                    lines.insert(insert_index + 1, image_markdown)
                    
                elif placement_location == "before_section":
                    lines.insert(target_line_index, image_markdown)
                    lines.insert(target_line_index + 1, "")
                    
                elif placement_location == "after_section":
                    # Find the end of the current section
                    insert_index = target_line_index + 1
                    while insert_index < len(lines) and not lines[insert_index].startswith('#'):
                        insert_index += 1
                    lines.insert(insert_index, "")
                    lines.insert(insert_index + 1, image_markdown)
                    
                else:
                    # Default: insert after the target line
                    lines.insert(target_line_index + 1, "")
                    lines.insert(target_line_index + 2, image_markdown)
            else:
                # If no target found, add at the end
                lines.append("")
                lines.append(image_markdown)
            
            return '\n'.join(lines)
            
        except Exception as e:
            print(f"❌ [MaterialContentGeneratorAgent] Error inserting image: {e}")
            # Fallback: add image at the end
            return content + f"\n\n{image_markdown}"
