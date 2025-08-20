import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

from ...infrastructure.ai.openai_service import OpenAIService
from ...infrastructure.database.database_service import DatabaseService
from ..services.message_service import MessageService
from ..services.context_service import ContextService


class CourseCreationAgent:
    """Agent specialized in course creation and initial setup"""
    
    def __init__(self, openai_service: OpenAIService, database_service: DatabaseService,
                 message_service: MessageService, context_service: ContextService,
                 image_generation_agent=None):
        self.openai = openai_service
        self.db = database_service
        self.messages = message_service
        self.context = context_service
        self.image_generation_agent = image_generation_agent
        self.model = "gpt-5-nano-2025-08-07"
    
    def get_function_definitions(self) -> List[Dict[str, Any]]:
        """Define functions that this agent can call"""
        return [
            {
                "name": "create_course",
                "description": "Create a new course with the given name and description",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the course"
                        },
                        "description": {
                            "type": "string",
                            "description": "A brief description of the course"
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "update_course_name",
                "description": "Update the name of an existing course",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {
                            "type": "string",
                            "description": "The ID of the course to update"
                        },
                        "new_name": {
                            "type": "string",
                            "description": "The new name for the course"
                        }
                    },
                    "required": ["course_id", "new_name"]
                }
            },
            {
                "name": "update_course_description",
                "description": "Update the description of an existing course",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {
                            "type": "string",
                            "description": "The ID of the course to update"
                        },
                        "new_description": {
                            "type": "string",
                            "description": "The new description for the course"
                        }
                    },
                    "required": ["course_id", "new_description"]
                }
            },
            {
                "name": "get_course_info",
                "description": "Get current information about the course",
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
            }
        ]
    
    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        """Generate system prompt for course creation"""
        course = context.get("course_state")
        course_id = context.get('current_course_id', '')
        intent_info = context.get('intent_info', {})
        
        # Check if intent indicates course naming/creation
        intent_suggests_creation = (
            intent_info.get('category') == 'workflow_request' and
            intent_info.get('target_step') == 'course_naming'
        )
        
        # Check if we need to create/update a course (draft with "Untitled Course" or no course)
        needs_course_creation = (
            not course or 
            (course and course.get("status") == "draft" and course.get("name") == "Untitled Course") or
            intent_suggests_creation
        )
        
        if needs_course_creation:
            return """You are a Course Creation Copilot. Your PRIMARY GOAL is to create courses from user input.

INTELLIGENT COURSE NAME DETECTION:
- If the user provides ANY text that could be a course name, immediately call create_course
- Examples: "Introduction to RAG", "Python Basics", "Machine Learning 101", "Web Development"
- Don't ask for confirmation - act immediately when you detect a course name
- Generate a compelling description based on the course name

BEHAVIOR RULES:
1. Single words or phrases that sound educational → create_course immediately
2. Questions about capabilities → provide helpful guidance
3. Unclear input → ask for clarification

Available functions:
- create_course: Create new courses with name and description (USE THIS IMMEDIATELY when you detect a course name)

Examples of correct behavior:
- User: "Introduction to RAG" → Call create_course with name="Introduction to RAG" and generate description
- User: "Python Programming" → Call create_course with name="Python Programming" and generate description
- User: "What can you do?" → Explain capabilities without calling functions

Be proactive and intelligent - don't wait for explicit instructions when the intent is clear."""
        
        return f"""You are a Course Creation Assistant for course "{course['name']}" (ID: {course_id}).

Use your natural language understanding to help users with course management. When users provide clear instructions with all necessary information, act on them immediately.

Available functions:
- update_course_name: Change course names (requires course_id: {course_id} and new_name)
- update_course_description: Update descriptions (requires course_id: {course_id} and new_description)  
- get_course_info: Get course details (requires course_id: {course_id})

Examples of intelligent behavior:
- "change the name to RAG" → Extract "RAG" as new_name and call update_course_name
- "rename it to Python Basics" → Extract "Python Basics" and update the name
- "what's the current course info?" → Call get_course_info

Be conversational, helpful, and act on clear requests immediately."""
    
    async def process_message(self, course_id: Optional[str], user_id: str, user_message: str, intent_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a user message for course creation"""
        
        # Note: User message storage is handled by the conversation orchestrator
        if course_id:
            await self.messages.store_message(course_id, user_id, user_message, "user")
        
        # Get conversation context
        context = await self.context.build_context_for_agent(course_id, user_id)
        
        # Add intent information to context if provided
        if intent_info:
            context['intent_info'] = intent_info
        
        # Build OpenAI messages
        system_prompt = self.get_system_prompt(context)
        messages = self.messages.build_openai_messages(context, user_message, system_prompt)
        
        # Get AI response with function calling
        try:
            print(f"\n{'='*60}")
            print(f"🔄 \033[94m[CourseCreationAgent]\033[0m \033[1mSending request to OpenAI...\033[0m")
            print(f"   📝 Model: \033[93m{self.model}\033[0m")
            print(f"   📝 User Message: \033[92m'{user_message}'\033[0m")
            print(f"   📝 System Prompt Preview: \033[90m{system_prompt[:150]}...\033[0m")
            print(f"   🔧 Functions available: \033[93m{len(self.get_function_definitions())}\033[0m")
            print(f"{'='*60}")
            
            client = await self.openai.get_client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=[{"type": "function", "function": func} for func in self.get_function_definitions()],
                tool_choice="auto",
                max_completion_tokens=1000
            )
            
            print(f"\n✅ \033[94m[CourseCreationAgent]\033[0m \033[1m\033[92mOpenAI Response received\033[0m")
            print(f"   💰 Tokens used: \033[93m{response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}\033[0m")
            
            message = response.choices[0].message
            
            # Handle tool calls
            function_results = {}
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    if tool_call.type == "function":
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)
                        
                        if function_name == "create_course":
                            result = await self._create_course(user_id, function_args)
                            function_results["course_created"] = result
                            course_id = result["course_id"]
                        elif function_name == "update_course_name":
                            result = await self._update_course_name(function_args["course_id"], function_args["new_name"])
                            function_results["course_name_updated"] = result
                        elif function_name == "update_course_description":
                            result = await self._update_course_description(function_args["course_id"], function_args["new_description"])
                            function_results["course_description_updated"] = result
                        elif function_name == "get_course_info":
                            result = await self._get_course_info(function_args["course_id"])
                            function_results["course_info"] = result
            
            # Generate final response based on function results
            ai_response = await self._generate_response_with_context(message.content, function_results)
            
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
            print(f"CourseCreationAgent OpenAI API error: {e}")
            print(f"Full traceback: {traceback.format_exc()}")
            return {
                "response": "I apologize, but I'm experiencing some technical difficulties. Please try again in a moment.",
                "course_id": course_id,
                "function_results": {},
                "error": str(e)
            }
    
    async def _create_course(self, user_id: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new course or update existing draft course with enhanced content generation"""
        
        course_name = args["name"]
        course_description = args.get("description", "")
        
        # Check if there's an existing draft course for this user
        existing_draft = await self.db.find_document("courses", {
            "user_id": ObjectId(user_id),
            "status": "draft",
            "name": "Untitled Course"
        })
        
        if existing_draft:
            # Update the existing draft course
            course_id = str(existing_draft["_id"])
            update_data = {
                "name": course_name,
                "description": course_description,
                "status": "creating",
                "workflow_step": "course_design_planning",
                "updated_at": datetime.utcnow()
            }
            
            await self.db.update_course(course_id, update_data)
        else:
            # Create a new course if no draft exists
            course_data = {
                "name": course_name,
                "description": course_description,
                "user_id": ObjectId(user_id),
                "structure": {},
                "status": "creating",
                "workflow_step": "course_design_planning"
            }
            
            course_id = await self.db.create_course(course_data)
            
            # Create chat session
            session_data = {
                "course_id": ObjectId(course_id),
                "user_id": ObjectId(user_id),
                "context_summary": "",
                "last_activity": datetime.utcnow(),
                "total_messages": 0,
                "context_window_start": 0
            }
            
            await self.db.create_chat_session(session_data)
        
        # Generate enhanced course content
        try:
            print(f"\n🚀 \033[94m[CourseCreationAgent]\033[0m \033[1mGenerating enhanced course content...\033[0m")
            
            # Generate learning outcomes and prerequisites
            content_result = await self._generate_course_content(course_name, course_description)
            
            # Generate multi-size cover image if image generation agent is available
            image_result = {"success": False}
            if self.image_generation_agent:
                image_result = await self.image_generation_agent.generate_course_cover_image_multi_size(
                    course_id=course_id,
                    course_name=course_name,
                    course_description=course_description,
                    style_preference="professional_educational",
                    dynamic_colors=True
                )
            
            # Update course with generated content
            update_data = {
                "learning_outcomes": content_result.get("learning_outcomes", []),
                "prerequisites": content_result.get("prerequisites", []),
                "content_generated_at": datetime.utcnow(),
                "auto_generated_fields": ["learning_outcomes", "prerequisites"]
            }
            
            # Add cover image data if generation was successful
            if image_result["success"]:
                images = image_result["images"]
                # Store multi-size image data in separate fields
                update_data.update({
                    # Multi-size image fields
                    "cover_image_large_r2_key": images.get("large", {}).get("r2_key"),
                    "cover_image_large_public_url": images.get("large", {}).get("public_url"),
                    "cover_image_medium_r2_key": images.get("medium", {}).get("r2_key"),
                    "cover_image_medium_public_url": images.get("medium", {}).get("public_url"),
                    "cover_image_small_r2_key": images.get("small", {}).get("r2_key"),
                    "cover_image_small_public_url": images.get("small", {}).get("public_url"),
                    # Legacy fields for backward compatibility (use large image)
                    "cover_image_r2_key": images.get("large", {}).get("r2_key"),
                    "cover_image_public_url": images.get("large", {}).get("public_url"),
                    # Metadata
                    "cover_image_metadata": image_result["image_metadata"],
                    "cover_image_updated_at": datetime.utcnow()
                })
                update_data["auto_generated_fields"].append("cover_image")
            
            await self.db.update_course(course_id, update_data)
            
            print(f"✅ \033[94m[CourseCreationAgent]\033[0m \033[1m\033[92mEnhanced course content generated successfully\033[0m")
            
            return {
                "course_id": course_id,
                "name": course_name,
                "description": course_description,
                "learning_outcomes": content_result.get("learning_outcomes", []),
                "prerequisites": content_result.get("prerequisites", []),
                "cover_image_url": image_result.get("images", {}).get("large", {}).get("public_url"),
                "cover_image_large_url": image_result.get("images", {}).get("large", {}).get("public_url"),
                "cover_image_medium_url": image_result.get("images", {}).get("medium", {}).get("public_url"),
                "cover_image_small_url": image_result.get("images", {}).get("small", {}).get("public_url"),
                "image_generated": image_result["success"],
                "content_generated": True
            }
            
        except Exception as e:
            print(f"⚠️ \033[94m[CourseCreationAgent]\033[0m \033[1m\033[93mContent generation failed: {str(e)}\033[0m")
            # If content generation fails, course still exists with basic info
            return {
                "course_id": course_id,
                "name": course_name,
                "description": course_description,
                "content_generated": False,
                "error": f"Content generation failed: {str(e)}"
            }
    
    async def _generate_course_content(self, course_name: str, course_description: str) -> Dict[str, Any]:
        """Generate learning outcomes and prerequisites using LLM"""
        
        try:
            # Create prompt for generating course content
            prompt = f"""Based on the course "{course_name}" with description: "{course_description}"

Generate comprehensive course content in the following format:

WHAT YOU'LL LEARN (4-6 short topics, 2-3 words each):
- [Topic 1]
- [Topic 2]
- [Topic 3]
- [Topic 4]
- [Topic 5]
- [Topic 6]

PREREQUISITES (2-4 short requirements, 2-3 words each):
- [Requirement 1]
- [Requirement 2]
- [Requirement 3]
- [Requirement 4]

Guidelines:
- "What you'll learn" items should be short topics/skills (2-3 words max)
- Examples: "Python Basics", "Data Analysis", "Model Training", "API Integration"
- Prerequisites should be short requirements (2-3 words max)
- Examples: "Basic Python", "High School Math", "Computer Literacy"
- Focus on key topics and essential skills
- Keep items concise and scannable"""

            client = await self.openai.get_client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert course designer. Generate high-quality learning outcomes and prerequisites for educational courses."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=800
            )
            
            content = response.choices[0].message.content
            
            # Parse the response to extract learning outcomes and prerequisites
            learning_outcomes = []
            prerequisites = []
            
            lines = content.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if 'WHAT YOU\'LL LEARN' in line.upper() or 'LEARNING OUTCOMES' in line.upper():
                    current_section = 'outcomes'
                elif 'PREREQUISITES' in line.upper():
                    current_section = 'prerequisites'
                elif line.startswith('- ') and current_section:
                    item = line[2:].strip()
                    if current_section == 'outcomes':
                        learning_outcomes.append(item)
                    elif current_section == 'prerequisites':
                        prerequisites.append(item)
            
            # Fallback parsing if structured format wasn't followed
            if not learning_outcomes or not prerequisites:
                # Try alternative parsing methods
                content_upper = content.upper()
                if ('WHAT YOU\'LL LEARN' in content_upper or 'LEARNING OUTCOMES' in content_upper) and 'PREREQUISITES' in content_upper:
                    # Find the outcomes section
                    if 'WHAT YOU\'LL LEARN' in content_upper:
                        outcomes_section = content.split('WHAT YOU\'LL LEARN')[1].split('PREREQUISITES')[0]
                    else:
                        outcomes_section = content.split('LEARNING OUTCOMES')[1].split('PREREQUISITES')[0]
                    
                    prereq_section = content.split('PREREQUISITES')[1]
                    
                    # Extract items from each section
                    for line in outcomes_section.split('\n'):
                        if line.strip().startswith('-'):
                            learning_outcomes.append(line.strip()[1:].strip())
                    
                    for line in prereq_section.split('\n'):
                        if line.strip().startswith('-'):
                            prerequisites.append(line.strip()[1:].strip())
            
            # Ensure we have reasonable defaults if parsing failed
            if not learning_outcomes:
                # Extract key words from course name for short topics
                course_words = course_name.split()
                if len(course_words) >= 2:
                    main_topic = " ".join(course_words[:2])
                else:
                    main_topic = course_words[0] if course_words else "Course Topic"
                
                learning_outcomes = [
                    f"{main_topic} Basics",
                    "Core Concepts",
                    "Practical Skills",
                    "Real Applications"
                ]
            
            if not prerequisites:
                prerequisites = [
                    "Basic Knowledge",
                    "Computer Access"
                ]
            
            return {
                "learning_outcomes": learning_outcomes[:6],  # Limit to 6 outcomes
                "prerequisites": prerequisites[:4]  # Limit to 4 prerequisites
            }
            
        except Exception as e:
            print(f"Error generating course content: {e}")
            # Return default content if generation fails
            course_words = course_name.split()
            if len(course_words) >= 2:
                main_topic = " ".join(course_words[:2])
            else:
                main_topic = course_words[0] if course_words else "Course Topic"
            
            return {
                "learning_outcomes": [
                    f"{main_topic} Basics",
                    "Core Concepts", 
                    "Practical Skills",
                    "Real Applications"
                ],
                "prerequisites": [
                    "Basic Knowledge",
                    "Computer Access"
                ]
            }
    
    async def _generate_response_with_context(self, base_response: Optional[str], function_results: Dict[str, Any]) -> str:
        """Generate a contextual response based on function call results"""
        if not function_results:
            return base_response or "I'm here to help you create your course. What would you like to work on?"
        
        if "course_created" in function_results:
            course_info = function_results["course_created"]
            
            # Build enhanced response with generated content
            response = f"✅ **Course created successfully:** '{course_info['name']}'\n\n"
            
            # Add learning outcomes if generated
            if course_info.get("learning_outcomes"):
                response += "📚 **What You'll Learn:**\n"
                for outcome in course_info["learning_outcomes"]:
                    response += f"• {outcome}\n"
                response += "\n"
            
            # Add prerequisites if generated
            if course_info.get("prerequisites"):
                response += "📋 **Prerequisites:**\n"
                for prereq in course_info["prerequisites"]:
                    response += f"• {prereq}\n"
                response += "\n"
            
            # Add cover image status
            if course_info.get("image_generated"):
                response += "🎨 **Cover Image:** Generated and ready!\n\n"
            elif course_info.get("cover_image_url"):
                response += f"🎨 **Cover Image:** [View Image]({course_info['cover_image_url']})\n\n"
            
            # Add next steps
            response += "**Next Step:** Course Design\n\nI can help you create:\n\n- Curriculum design\n- Pedagogy strategies\n- Assessment frameworks\n\nWould you like me to generate everything for you? I can create all your course materials automatically!"
            
            return response
        
        if "course_name_updated" in function_results:
            result = function_results["course_name_updated"]
            if result["success"]:
                return f"Great! I've updated the course name to '{result['new_name']}'. Is there anything else you'd like to modify about your course?"
            else:
                return f"I encountered an issue updating the course name: {result.get('error', 'Unknown error')}"
        
        if "course_description_updated" in function_results:
            result = function_results["course_description_updated"]
            if result["success"]:
                return f"Perfect! I've updated the course description. The new description is: '{result['new_description']}'"
            else:
                return f"I encountered an issue updating the course description: {result.get('error', 'Unknown error')}"
        
        if "course_info" in function_results:
            info = function_results["course_info"]
            if info["success"]:
                course = info["course"]
                return f"Here's the current information about your course:\n\n**Name:** {course['name']}\n**Description:** {course.get('description', 'No description provided')}\n**Status:** {course.get('status', 'Unknown')}\n**Created:** {course.get('created_at', 'Unknown')}\n\nWhat would you like to do with your course?"
            else:
                return f"I couldn't retrieve the course information: {info.get('error', 'Unknown error')}"
        
        return base_response or "I've processed your request. What would you like to work on next?"

    async def _update_course_name(self, course_id: str, new_name: str) -> Dict[str, Any]:
        """Update the name of an existing course"""
        try:
            # Update the course name
            success = await self.db.update_course(course_id, {"name": new_name})
            
            if success:
                return {
                    "success": True,
                    "new_name": new_name,
                    "course_id": course_id
                }
            else:
                return {
                    "success": False,
                    "error": "Course not found or no changes made"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def _update_course_description(self, course_id: str, new_description: str) -> Dict[str, Any]:
        """Update the description of an existing course"""
        try:
            # Update the course description
            success = await self.db.update_course(course_id, {"description": new_description})
            
            if success:
                return {
                    "success": True,
                    "new_description": new_description,
                    "course_id": course_id
                }
            else:
                return {
                    "success": False,
                    "error": "Course not found or no changes made"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def _get_course_info(self, course_id: str) -> Dict[str, Any]:
        """Get current information about the course"""
        try:
            # Get course information
            course = await self.db.find_course(course_id)
            
            if course:
                # Convert ObjectIds to strings for JSON serialization
                course["_id"] = str(course["_id"])
                course["user_id"] = str(course["user_id"])
                
                return {
                    "success": True,
                    "course": course
                }
            else:
                return {
                    "success": False,
                    "error": "Course not found"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
