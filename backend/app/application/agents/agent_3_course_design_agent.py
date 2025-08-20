import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

from ...infrastructure.ai.openai_service import OpenAIService
from ...infrastructure.database.database_service import DatabaseService
from ..services.message_service import MessageService
from ..services.context_service import ContextService
from ...infrastructure.storage.r2_storage import R2StorageService


class CourseDesignAgent:
    """Agent specialized in comprehensive course design including curriculum, pedagogy, and assessments"""
    
    def __init__(self, openai_service: OpenAIService, database_service: DatabaseService,
                 message_service: MessageService, context_service: ContextService,
                 r2_storage_service: R2StorageService):
        self.openai = openai_service
        self.db = database_service
        self.messages = message_service
        self.context = context_service
        self.storage = r2_storage_service
        self.model = "gpt-5-mini-2025-08-07"
    
    def get_function_definitions(self) -> List[Dict[str, Any]]:
        """Define functions that this agent can call"""
        return [
            {
                "name": "handle_course_design_choice",
                "description": "Handle user's course design preference choice",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {
                            "type": "string",
                            "description": "The ID of the course"
                        },
                        "choice": {
                            "type": "string",
                            "enum": ["generate", "upload"],
                            "description": "User's course design preference"
                        }
                    },
                    "required": ["course_id", "choice"]
                }
            },
            {
                "name": "generate_course_design",
                "description": "Generate a comprehensive course design including curriculum, pedagogy, and assessments",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {
                            "type": "string",
                            "description": "The ID of the course"
                        },
                        "focus": {
                            "type": "string",
                            "description": "Optional focus or modification request for the course design"
                        }
                    },
                    "required": ["course_id"]
                }
            },
            {
                "name": "modify_course_design",
                "description": "Modify existing course design based on user requirements",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {
                            "type": "string",
                            "description": "The ID of the course"
                        },
                        "modification_request": {
                            "type": "string",
                            "description": "What changes the user wants to make to the course design"
                        }
                    },
                    "required": ["course_id", "modification_request"]
                }
            },
            {
                "name": "get_course_design_info",
                "description": "Get current course design information and content",
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
                "name": "process_uploaded_materials",
                "description": "Process uploaded curriculum and pedagogy files into unified course design",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {
                            "type": "string",
                            "description": "The ID of the course"
                        },
                        "curriculum_content": {
                            "type": "string",
                            "description": "Content of the uploaded curriculum file"
                        },
                        "pedagogy_content": {
                            "type": "string",
                            "description": "Optional content of the uploaded pedagogy file"
                        }
                    },
                    "required": ["course_id", "curriculum_content"]
                }
            }
        ]
    
    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        """Generate student-centered system prompt for foundational course design"""
        course = context.get("course_state")
        workflow_step = course.get('workflow_step', 'course_naming') if course else 'course_naming'
        course_id = context.get('current_course_id', '')
        
        base_prompt = f"""You are an Expert Educational Course Designer specializing in FOUNDATIONAL, FIRST-PRINCIPLES course design for "{course['name']}" (ID: {course_id}).

🎯 CORE MISSION: Build understanding from absolute basics to practical competence:
- Start with fundamental questions: "What is this?" and "Why does it matter?"
- Build conceptual understanding before technical implementation
- Use analogies and real-world examples students can relate to
- Progress naturally: Basic Concepts → Core Principles → Simple Applications → Advanced Topics
- Prioritize student comprehension over industry buzzwords
- Focus on "learning to learn" rather than memorizing current tools

🔍 FIRST-PRINCIPLES EDUCATIONAL APPROACH:
1. FOUNDATION FIRST: What are the core concepts a complete beginner needs?
2. CONCEPTUAL UNDERSTANDING: Why do these concepts exist? What problems do they solve?
3. SIMPLE EXAMPLES: How can we demonstrate these concepts with basic, relatable examples?
4. GRADUAL COMPLEXITY: How do we build from simple to sophisticated applications?
5. PRACTICAL RELEVANCE: Where and when would students use this knowledge?

🛠️ AVAILABLE TOOLS:
- Web Search: Research educational approaches and foundational learning methods
- Function Tools: Handle course design operations

Available functions:
- handle_course_design_choice: Set user preference (generate/upload) - use course_id: {course_id}
- generate_course_design: Create comprehensive course designs - use course_id: {course_id}
- modify_course_design: Update existing designs - use course_id: {course_id}
- get_course_design_info: Get current design info - use course_id: {course_id}
- process_uploaded_materials: Process uploaded files - use course_id: {course_id}

🎯 FOUNDATIONAL LEARNING SPECIALIZATIONS:
• Beginner-friendly progression (context → basic concepts → simple examples → applications)
• Learning objectives that start with "Understand" and "Explain" before "Implement" and "Create"
• Pedagogy focused on conceptual clarity and student comprehension
• Assessments that test understanding, not just technical execution
• Building confidence through achievable, incremental learning steps"""

        if workflow_step == "course_design_method_selection":
            return base_prompt + f"""

🤖 INTELLIGENT FUNCTION CALLING:
- "Generate for me" or similar → Call both handle_course_design_choice(choice="generate") and generate_course_design
- "I have materials" or similar → Call handle_course_design_choice(choice="upload")
- Modification requests → Call modify_course_design with the request
- Info requests → Call get_course_design_info

Be intelligent about function calling - you can call multiple functions in sequence when it makes sense.
REMEMBER: Always prioritize 2025 current content and use web search for verification."""
        
        return base_prompt + """

Use your natural language understanding to help users with comprehensive course design. When users provide clear instructions, act on them immediately.

REMEMBER: Always prioritize current content and use web search for latest information."""
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools including web search and function tools"""
        tools = [
            {"type": "web_search_preview"}  # Web search tool for latest content research
        ]
        
        # Add function tools - for Responses API, function tools need name, description, and parameters directly
        for func_def in self.get_function_definitions():
            tools.append({
                "type": "function",
                "name": func_def["name"],
                "description": func_def["description"],
                "parameters": func_def["parameters"]
            })
        
        return tools

    async def process_message(self, course_id: Optional[str], user_id: str, user_message: str) -> Dict[str, Any]:
        """Process a user message for course design generation using Responses API"""
        
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
        
        # Get AI response with function calling and web search
        try:
            print(f"\n{'='*60}")
            print(f"🔄 \033[91m[CourseDesignAgent]\033[0m \033[1mSending request to Responses API...\033[0m")
            print(f"   📝 Model: \033[93m{self.model}\033[0m")
            print(f"   📝 User Message: \033[92m'{user_message}'\033[0m")
            print(f"   📝 System Instructions Preview: \033[90m{system_instructions[:150]}...\033[0m")
            print(f"   🔧 Tools available: \033[93m{len(self.get_all_tools())}\033[0m")
            print(f"   🌐 Web search enabled: \033[92mYes\033[0m")
            print(f"{'='*60}")
            
            # Use new Responses API with web search and function calling
            response = await self.openai.create_response(
                model=self.model,
                input=input_messages,
                instructions=system_instructions,
                tools=self.get_all_tools()
            )
            
            print(f"\n✅ \033[91m[CourseDesignAgent]\033[0m \033[1m\033[92mResponses API Response received\033[0m")
            print(f"   📊 Output items: \033[93m{len(response.output) if hasattr(response, 'output') else 'N/A'}\033[0m")
            
            # Process response output
            function_results = {}
            web_search_results = {}
            assistant_content = ""
            
            # Process all output items
            for item in response.output:
                if item.type == "function_call":
                    # Handle function calls
                    function_name = item.name
                    function_args = json.loads(item.arguments)
                    
                    print(f"🔧 [CourseDesignAgent] Processing function call: {function_name}")
                    
                    if function_name == "handle_course_design_choice":
                        result = await self._handle_course_design_choice(function_args["course_id"], function_args["choice"])
                        function_results["course_design_choice"] = result
                        
                        # If choice is "generate", automatically trigger course design generation
                        if result.get("success") and function_args["choice"] == "generate":
                            generation_result = await self._generate_course_design(function_args["course_id"], None)
                            function_results["course_design_generated"] = generation_result
                    elif function_name == "generate_course_design":
                        result = await self._generate_course_design(function_args["course_id"], function_args.get("focus"))
                        function_results["course_design_generated"] = result
                    elif function_name == "modify_course_design":
                        result = await self._modify_course_design(function_args["course_id"], function_args["modification_request"])
                        function_results["course_design_modified"] = result
                    elif function_name == "get_course_design_info":
                        result = await self._get_course_design_info(function_args["course_id"])
                        function_results["course_design_info"] = result
                    elif function_name == "process_uploaded_materials":
                        result = await self._process_uploaded_materials(
                            function_args["course_id"], 
                            function_args["curriculum_content"],
                            function_args.get("pedagogy_content")
                        )
                        function_results["materials_processed"] = result
                
                elif item.type == "web_search_call":
                    # Handle web search results
                    print(f"🌐 [CourseDesignAgent] Processing web search call: {item.id}")
                    # Convert web search action to serializable format
                    action_data = "search"
                    if hasattr(item, 'action') and item.action:
                        if hasattr(item.action, 'query'):
                            action_data = {
                                "type": getattr(item.action, 'type', 'search'),
                                "query": getattr(item.action, 'query', '')
                            }
                        else:
                            action_data = str(item.action)
                    
                    web_search_results[item.id] = {
                        "status": item.status,
                        "action": action_data
                    }
                
                elif item.type == "message":
                    # Handle assistant message content
                    if hasattr(item, 'content') and item.content:
                        for content_item in item.content:
                            if hasattr(content_item, 'text'):
                                assistant_content += content_item.text
                                
                                # Extract citations if available
                                if hasattr(content_item, 'annotations'):
                                    for annotation in content_item.annotations:
                                        if annotation.type == "url_citation":
                                            print(f"📎 [CourseDesignAgent] Found citation: {annotation.url}")
            
            # Generate final response based on function results and web search
            ai_response = await self._generate_response_with_context(assistant_content, function_results, web_search_results)
            
            # Store AI response
            if course_id:
                await self.messages.store_message(course_id, user_id, ai_response, "assistant", {
                    **function_results,
                    "web_search_results": web_search_results
                })
            
            return {
                "response": ai_response,
                "course_id": course_id,
                "function_results": function_results,
                "web_search_results": web_search_results
            }
            
        except Exception as e:
            import traceback
            print(f"CourseDesignAgent Responses API error: {e}")
            print(f"Full traceback: {traceback.format_exc()}")
            return {
                "response": "I apologize, but I'm experiencing some technical difficulties. Please try again in a moment.",
                "course_id": course_id,
                "function_results": {},
                "error": str(e)
            }
    
    async def _handle_course_design_choice(self, course_id: str, choice: str) -> Dict[str, Any]:
        """Handle user's course design choice"""
        # Update course workflow step based on choice
        workflow_step = "course_design_upload" if choice == "upload" else "course_design_generation"
        
        success = await self.db.update_course(course_id, {
            "workflow_step": workflow_step,
            "course_design_source": choice
        })
        
        if success:
            return {
                "success": True,
                "choice": choice,
                "workflow_step": workflow_step
            }
        else:
            return {
                "success": False,
                "error": "Failed to update course"
            }

    async def _generate_course_design(self, course_id: str, focus: Optional[str] = None) -> Dict[str, Any]:
        """Generate a comprehensive course design for the course with optional focus"""
        # This method now returns a signal to start streaming generation
        # The actual streaming happens in the route handler
        return {
            "success": True,
            "streaming": True,
            "course_id": course_id,
            "focus": focus,
            "workflow_transition": {
                "trigger_automatically": True,
                "next_step": "content_structure_generation",
                "next_agent": "course_structure"
            }
        }
    
    async def stream_course_design_generation(self, course_id: str, focus: Optional[str] = None, user_id: Optional[str] = None):
        """Stream course design generation in real-time using existing research"""
        print(f"\n🎯 [CourseDesignAgent] Starting stream_course_design_generation")
        print(f"   📋 Course ID: {course_id}")
        print(f"   👤 User ID: {user_id}")
        print(f"   🎯 Focus: {focus}")
        
        try:
            # Get course info
            print(f"🔍 [CourseDesignAgent] Fetching course info...")
            course = await self.db.find_course(course_id)
            if not course:
                print(f"❌ [CourseDesignAgent] Course not found: {course_id}")
                yield {"type": "error", "content": "Course not found"}
                return
            
            print(f"✅ [CourseDesignAgent] Course found: {course.get('name')}")
            
            # Get user_id from course if not provided
            if not user_id:
                user_id = str(course.get("user_id"))
                print(f"🔄 [CourseDesignAgent] Using user_id from course: {user_id}")
            
            # Get existing research from R2 storage
            print(f"📥 [CourseDesignAgent] Retrieving existing research...")
            research_r2_key = course.get("research_r2_key")
            research_findings = ""
            
            if research_r2_key:
                try:
                    research_findings = await self.storage.get_course_design_content(research_r2_key)
                    if research_findings:
                        print(f"✅ [CourseDesignAgent] Retrieved research ({len(research_findings)} chars)")
                    else:
                        print(f"⚠️ [CourseDesignAgent] Research file exists but content is empty")
                        research_findings = await self._generate_fallback_research(course['name'])
                except Exception as e:
                    print(f"⚠️ [CourseDesignAgent] Failed to retrieve research: {e}")
                    research_findings = await self._generate_fallback_research(course['name'])
            else:
                print(f"⚠️ [CourseDesignAgent] No research found, generating fallback research...")
                research_findings = await self._generate_fallback_research(course['name'])
            
            # Build foundational course design prompt with research findings
            base_prompt = f"""You are an expert educational designer specializing in FOUNDATIONAL, FIRST-PRINCIPLES course design. Based on the course name "{course['name']}" and the comprehensive subject matter research, generate a course design that builds understanding from absolute basics to practical competence.

Course Description: {course.get('description', '')}

🔬 COMPREHENSIVE SUBJECT MATTER RESEARCH:
{research_findings}

🎯 FOUNDATIONAL DESIGN PRINCIPLES:
- START WITH FUNDAMENTALS: What are the core concepts a complete beginner needs to understand?
- BUILD CONCEPTUAL UNDERSTANDING: Why do these concepts exist? What problems do they solve?
- USE SIMPLE, RELATABLE EXAMPLES: Demonstrate concepts with basic examples students can understand
- PROGRESS GRADUALLY: Move from simple concepts to more sophisticated applications step-by-step
- PRIORITIZE COMPREHENSION: Focus on student understanding over technical complexity
- CONNECT TO REAL WORLD: Show practical relevance without overwhelming beginners

🎓 FIRST-PRINCIPLES LEARNING PROGRESSION:
1. CONTEXT & MOTIVATION: Why does this field/topic exist? What problems does it solve?
2. BASIC CONCEPTS: What are the fundamental building blocks students need to know?
3. SIMPLE EXAMPLES: How can we demonstrate these concepts with easy-to-understand examples?
4. CORE PRINCIPLES: What are the underlying principles that govern how things work?
5. PRACTICAL APPLICATIONS: How do these principles apply in real-world scenarios?
6. CURRENT TOOLS & TECHNIQUES: What modern tools help implement these principles?
7. ADVANCED TOPICS: How do experts build on these foundations for complex applications?

🚫 AVOID COMPLEXITY TRAPS:
- Do NOT start with advanced technical jargon or complex implementations
- Do NOT assume prior knowledge of industry-specific terms or concepts
- Do NOT jump directly to current tools without explaining underlying principles
- Do NOT use "agent control loops" or "function-calling patterns" in Module 1
- Do NOT overwhelm beginners with too many technical details at once"""
            
            if focus:
                base_prompt += f"\n\nSpecial Focus/Requirements: {focus}"
            
            course_design_prompt = base_prompt + """

Your responsibilities:
1. Create foundational, student-centered course designs based on educational research findings
2. Build natural learning progression from basic concepts to advanced applications through chapters
3. Design chapters with clear titles, descriptions, and focused learning objectives
4. Provide chapter-specific pedagogy strategies for effective teaching
5. Include chapter-specific assessment ideas that test understanding
6. Ensure proper foundational progression: background → concepts → mechanisms → applications
7. Structure content to prioritize student comprehension while showcasing current industry relevance

Guidelines for chapter-based course design creation:
- Start with course overview, appropriate level for beginners, realistic duration, minimal prerequisites
- Organize modules following natural learning progression (WHY → WHAT → HOW → WHERE/WHEN)
- For each module, create multiple chapters that break down the content logically
- Each chapter should have: Title, Description, Learning Objective, Pedagogy Strategy, Assessment Idea
- Build chapters that answer natural student questions in logical sequence
- Include learning objectives that progress through Bloom's taxonomy levels appropriately
- Provide specific chapter-focused pedagogy strategies (analogies, explanations, hands-on practice)
- Include varied assessment types that test chapter-specific understanding
- Consider what students actually need to know first, building prerequisite knowledge systematically
- Add a final project that demonstrates comprehensive understanding

Output format - Follow this EXACT chapter-based structure with markdown tables:

CRITICAL TABLE FORMATTING RULES:
- Use standard markdown table syntax with pipe characters |
- Do NOT escape pipe characters with backslashes
- Each module MUST have a consistent table structure
- All tables must follow the exact same format
- Never use \| (escaped pipes) - always use | (regular pipes)

# 📚 [Course Title]

**Level:** [Beginner/Intermediate/Advanced]
**Duration:** [Time estimate]
**Prerequisites:**

* [Prerequisite 1]
* [Prerequisite 2]
* [Prerequisite 3]

**Tools & Platforms:**
[CURRENT 2025 Technologies/tools needed]

---

## **Module 1 — [Module Title]**

| **Chapter** | **Details** |
| ------- | ------- |
| **Chapter 1.1: [Chapter Title]** | **Description:** [Clear description of what will be covered in this chapter]<br><br>**Learning Objective:** [Specific learning objective for this chapter] *(Bloom Level)*<br><br>**Pedagogy Strategy:** [How to effectively teach this chapter - specific teaching methods, analogies, examples, demonstrations using LATEST tools and techniques]<br><br>**Assessment Idea:** [How to test whether the student has understood this chapter's concept - specific assessment method with current standards] |
| **Chapter 1.2: [Chapter Title]** | **Description:** [Clear description of what will be covered in this chapter]<br><br>**Learning Objective:** [Specific learning objective for this chapter] *(Bloom Level)*<br><br>**Pedagogy Strategy:** [How to effectively teach this chapter - specific teaching methods, analogies, examples, demonstrations using LATEST tools and techniques]<br><br>**Assessment Idea:** [How to test whether the student has understood this chapter's concept - specific assessment method with current standards] |
| **Chapter 1.3: [Chapter Title]** | **Description:** [Clear description of what will be covered in this chapter]<br><br>**Learning Objective:** [Specific learning objective for this chapter] *(Bloom Level)*<br><br>**Pedagogy Strategy:** [How to effectively teach this chapter - specific teaching methods, analogies, examples, demonstrations using LATEST tools and techniques]<br><br>**Assessment Idea:** [How to test whether the student has understood this chapter's concept - specific assessment method with current standards] |
| **Chapter 1.4: [Chapter Title]** | **Description:** [Clear description of what will be covered in this chapter]<br><br>**Learning Objective:** [Specific learning objective for this chapter] *(Bloom Level)*<br><br>**Pedagogy Strategy:** [How to effectively teach this chapter - specific teaching methods, analogies, examples, demonstrations using LATEST tools and techniques]<br><br>**Assessment Idea:** [How to test whether the student has understood this chapter's concept - specific assessment method with current standards] |

---

## **Module 2 — [Module Title]**

| **Chapter** | **Details** |
| ------- | ------- |
| **Chapter 2.1: [Chapter Title]** | **Description:** [Clear description of what will be covered in this chapter]<br><br>**Learning Objective:** [Specific learning objective for this chapter] *(Bloom Level)*<br><br>**Pedagogy Strategy:** [How to effectively teach this chapter - specific teaching methods, analogies, examples, demonstrations using LATEST tools and techniques]<br><br>**Assessment Idea:** [How to test whether the student has understood this chapter's concept - specific assessment method with current standards] |
| **Chapter 2.2: [Chapter Title]** | **Description:** [Clear description of what will be covered in this chapter]<br><br>**Learning Objective:** [Specific learning objective for this chapter] *(Bloom Level)*<br><br>**Pedagogy Strategy:** [How to effectively teach this chapter - specific teaching methods, analogies, examples, demonstrations using LATEST tools and techniques]<br><br>**Assessment Idea:** [How to test whether the student has understood this chapter's concept - specific assessment method with current standards] |
| **Chapter 2.3: [Chapter Title]** | **Description:** [Clear description of what will be covered in this chapter]<br><br>**Learning Objective:** [Specific learning objective for this chapter] *(Bloom Level)*<br><br>**Pedagogy Strategy:** [How to effectively teach this chapter - specific teaching methods, analogies, examples, demonstrations using LATEST tools and techniques]<br><br>**Assessment Idea:** [How to test whether the student has understood this chapter's concept - specific assessment method with current standards] |
| **Chapter 2.4: [Chapter Title]** | **Description:** [Clear description of what will be covered in this chapter]<br><br>**Learning Objective:** [Specific learning objective for this chapter] *(Bloom Level)*<br><br>**Pedagogy Strategy:** [How to effectively teach this chapter - specific teaching methods, analogies, examples, demonstrations using LATEST tools and techniques]<br><br>**Assessment Idea:** [How to test whether the student has understood this chapter's concept - specific assessment method with current standards] |

---

[Continue with additional modules and chapters...]

---

## **Final Project**

**Goal:**
[Project description reflecting CURRENT industry needs and integrating knowledge from all chapters]

**Requirements:**

1. **[Requirement 1]** — [Description using LATEST standards and techniques from the course]
2. **[Requirement 2]** — [Description using CURRENT practices covered in chapters]
3. **[Requirement 3]** — [Description using MODERN approaches taught in the course]
4. **[Requirement 4]** — [Description using 2025 methodologies from research]
5. **[Requirement 5]** — [Description using LATEST tools and frameworks]

**Rubric (100 points):**

* [Criteria 1] — **[Points]**
* [Criteria 2] — **[Points]**
* [Criteria 3] — **[Points]**
* [Criteria 4] — **[Points]**
* [Criteria 5] — **[Points]**

---

CRITICAL OUTPUT REQUIREMENTS:
- Generate ONLY the core course design content in the specified format above
- Do NOT include any additional sections like Weekly Schedule, Sample Lesson Plans, Instructor Notes, etc.
- Do NOT include any conversational elements, questions, or follow-up suggestions
- Do NOT ask "What would you like me to do next?" or similar questions
- Do NOT offer additional services or options
- End the output with the Final Project rubric - nothing more
- This is a complete, standalone course design document
- Focus on CHAPTERS as the primary learning units, not learning objectives
- Keep the content focused on the core curriculum structure only"""
            
            # Send start signal for generation
            print(f"📤 [CourseDesignAgent] Sending generation start signal...")
            yield {"type": "start", "content": f"🎯 Generating 2025-current course design for {course['name']}..."}
            
            print(f"🤖 [CourseDesignAgent] Starting enhanced course design generation...")
            print(f"   📝 Model: {self.model}")
            print(f"   📏 Max tokens: 3000")
            print(f"   🌡️ Temperature: 0.7")
            print(f"   🌐 Research findings: {len(research_findings)} characters")
            
            # Use streaming response from Responses API for generation
            response = await self.openai.create_response(
                model=self.model,
                input=[{"role": "user", "content": course_design_prompt}],
                stream=True
            )
            
            print(f"✅ [CourseDesignAgent] Enhanced streaming response created, starting to read chunks...")
            
            course_design_content = ""
            chunk_count = 0
            
            # Stream the response
            async for event in response:
                if hasattr(event, 'type'):
                    if event.type == "response.output_text.delta":
                        # This is the correct event type for Responses API streaming
                        chunk_count += 1
                        if hasattr(event, 'delta') and event.delta:
                            content_chunk = event.delta
                            course_design_content += content_chunk
                            
                            if chunk_count % 20 == 0:  # Log every 20th chunk
                                print(f"📦 [CourseDesignAgent] Processed {chunk_count} chunks, content length: {len(course_design_content)}")

                            # Send content chunk for real-time display
                            if chunk_count % 3 == 0:  # Send every 3rd chunk for optimal speed
                                yield {
                                    "type": "content",
                                    "content": content_chunk,
                                    "full_content": course_design_content
                                }
                    elif event.type == "response.output_text.done":
                        # Handle completion of text output
                        print(f"✅ [CourseDesignAgent] Text output completed")
                    elif event.type == "response.completed":
                        # Handle completion of entire response
                        print(f"✅ [CourseDesignAgent] Response completed")
            
            print(f"✅ [CourseDesignAgent] Enhanced streaming completed. Total chunks: {chunk_count}, Final content length: {len(course_design_content)}")
            
            # Post-process to fix any table formatting issues
            print(f"🔧 [CourseDesignAgent] Post-processing table formatting...")
            course_design_content = self._fix_table_formatting(course_design_content)
            print(f"✅ [CourseDesignAgent] Table formatting fixed, final length: {len(course_design_content)}")
            
            # Upload course design to R2
            print(f"💾 [CourseDesignAgent] Starting R2 upload...")
            yield {"type": "progress", "content": "💾 Saving course design..."}
            
            # Get current version and increment
            current_version = course.get("course_design_version", 0)
            new_version = current_version + 1
            
            print(f"📋 [CourseDesignAgent] Uploading version {new_version} to R2...")
            upload_result = await self.storage.upload_course_design(
                course_id=course_id,
                content=course_design_content,
                source="generated",
                version=new_version
            )
            
            print(f"📤 [CourseDesignAgent] R2 upload result: {upload_result.get('success')}")
            if not upload_result.get("success"):
                error_msg = f"Failed to upload course design: {upload_result.get('error')}"
                print(f"❌ [CourseDesignAgent] {error_msg}")
                yield {"type": "error", "content": error_msg}
                return
            
            print(f"✅ [CourseDesignAgent] R2 upload successful: {upload_result['r2_key']}")
            
            # Update course with R2 information and trigger content creation
            print(f"🔄 [CourseDesignAgent] Updating course database...")
            update_result = await self.db.update_course(course_id, {
                "course_design_r2_key": upload_result["r2_key"],
                "course_design_public_url": upload_result["public_url"],
                "course_design_source": "generated",
                "course_design_version": new_version,
                "course_design_updated_at": datetime.utcnow(),
                "workflow_step": "content_structure_generation",  # Auto-trigger content creation
                "has_pedagogy": True,
                "has_assessments": True,
                "design_components": ["curriculum", "pedagogy", "assessments"]
            })
            
            print(f"📋 [CourseDesignAgent] Course update result: {update_result}")
            
            # Store the completion message in chat history BEFORE sending completion signal
            completion_message = "✅ **Course design generated successfully!** Your course now includes curriculum structure, pedagogy strategies, and assessment frameworks."
            try:
                print(f"💬 [CourseDesignAgent] Storing completion message in chat...")
                await self.messages.store_message(course_id, user_id, completion_message, "assistant")
                print(f"✅ [CourseDesignAgent] Successfully stored completion message for course {course_id}")
            except Exception as e:
                print(f"❌ [CourseDesignAgent] Failed to store completion message: {e}")
                import traceback
                print(f"Full traceback: {traceback.format_exc()}")
                # Still send completion even if message storage fails
            
            # Send completion signal with workflow transition
            print(f"🎉 [CourseDesignAgent] Sending completion signal with auto-trigger...")
            yield {
                "type": "complete",
                "content": completion_message,
                "r2_key": upload_result["r2_key"],
                "public_url": upload_result["public_url"],
                "full_content": course_design_content,
                "workflow_transition": {
                    "trigger_automatically": True,
                    "next_step": "content_structure_generation",
                    "next_agent": "course_structure"
                }
            }
            
            print(f"🎯 [CourseDesignAgent] Stream generation completed successfully!")
            
        except Exception as e:
            error_msg = f"Failed to generate course design: {str(e)}"
            print(f"❌ [CourseDesignAgent] CRITICAL ERROR: {error_msg}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            yield {"type": "error", "content": error_msg}
    
    async def _generate_response_with_context(self, base_response: Optional[str], function_results: Dict[str, Any], web_search_results: Optional[Dict[str, Any]] = None) -> str:
        """Generate a contextual response based on function call results and web search"""
        if not function_results and not web_search_results:
            return base_response or "I'm here to help you create your comprehensive course design. What would you like to work on?"
        
        # Add web search context if available
        search_context = ""
        if web_search_results:
            search_count = len(web_search_results)
            if search_count > 0:
                search_context = f"\n\n🌐 **Latest Research:** Searched {search_count} sources for current trends and technologies."
        
        # Prioritize streaming course design generation response
        if "course_design_generated" in function_results:
            result = function_results["course_design_generated"]
            if result.get("streaming"):
                return "🎯 **Generating Course Design**\n\nCreating comprehensive package:\n\n- Curriculum structure\n- Pedagogy strategies\n- Assessment frameworks\n\n*← Content will appear in real-time*"
            else:
                return "✅ **Course Design Complete!**\n\n**Generated:**\n• Learning objectives with Bloom's taxonomy\n• Pedagogy notes & teaching strategies\n• Assessment ideas & rubrics\n\n**Next:** Review the design or request modifications"
        
        if "course_design_choice" in function_results:
            choice_result = function_results["course_design_choice"]
            if choice_result["choice"] == "generate":
                return "🎯 **AI Generation Selected**\n\nI'll create a complete instructional design package:\n• Learning objectives\n• Teaching methods\n• Evaluation strategies\n\n*Starting generation...*"
            else:
                return "📁 **Upload Materials**\n\n**Required:**\n• Curriculum file (.md) - Course structure\n\n**Optional:**\n• Pedagogy file (.md) - Teaching strategies\n\n*I'll process and enhance your content*"
        
        if "course_design_modified" in function_results:
            result = function_results["course_design_modified"]
            if result.get("streaming"):
                return "🔄 **Modifying Course Design**\n\nApplying your requested changes:\n\n- Analyzing current structure\n- Implementing modifications\n- Maintaining quality standards\n\n*← Changes will appear in real-time*"
            elif result.get("success"):
                return f"✅ **Course Design Updated**\n\n**Changes Applied:**\n• Curriculum modifications\n• Pedagogy adjustments\n• Assessment updates\n\n**Next:** Review changes or request more modifications"
            else:
                return f"❌ **Update Failed:** {result.get('error', 'Unknown error')}"
        
        if "course_design_info" in function_results:
            info = function_results["course_design_info"]
            if info.get("success"):
                components = ", ".join(info.get("design_components", ["curriculum"]))
                return f"📋 **Course Design Info**\n\n**Source:** {info['source']}\n**Version:** {info['version']}\n**Components:** {components}\n**Updated:** {info['updated_at']}\n\n*Available in course structure*"
            else:
                return f"❌ **Info Error:** {info.get('error', 'Unknown error')}"
        
        if "materials_processed" in function_results:
            result = function_results["materials_processed"]
            if result.get("success"):
                return f"✅ **Materials Processed**\n\n**Created:**\n• Enhanced curriculum structure\n• Integrated pedagogy strategies\n• Comprehensive assessments\n\n*Complete design available in outline*"
            else:
                return f"❌ **Processing Failed:** {result.get('error', 'Unknown error')}"
        
        return base_response or "I've processed your request. What would you like to work on next?"

    async def _modify_course_design(self, course_id: str, modification_request: str) -> Dict[str, Any]:
        """Modify existing course design based on user requirements - now returns streaming signal"""
        # This method now returns a signal to start streaming modification
        # The actual streaming happens in the route handler
        return {
            "success": True,
            "streaming": True,
            "course_id": course_id,
            "modification_request": modification_request
        }
    
    async def stream_course_design_modification(self, course_id: str, modification_request: str, user_id: Optional[str] = None):
        """Stream targeted course design modification in real-time"""
        print(f"\n🔄 [CourseDesignAgent] Starting TARGETED stream_course_design_modification")
        print(f"   📋 Course ID: {course_id}")
        print(f"   👤 User ID: {user_id}")
        print(f"   🔧 Modification: {modification_request}")
        
        try:
            # Get course info
            print(f"🔍 [CourseDesignAgent] Fetching course info...")
            course = await self.db.find_course(course_id)
            if not course:
                print(f"❌ [CourseDesignAgent] Course not found: {course_id}")
                yield {"type": "error", "content": "Course not found"}
                return
            
            print(f"✅ [CourseDesignAgent] Course found: {course.get('name')}")
            
            # Get user_id from course if not provided
            if not user_id:
                user_id = str(course.get("user_id"))
                print(f"🔄 [CourseDesignAgent] Using user_id from course: {user_id}")
            
            # Get current course design from R2
            print(f"📥 [CourseDesignAgent] Retrieving current course design...")
            r2_key = course.get("course_design_r2_key") or course.get("curriculum_r2_key")  # Backward compatibility
            if not r2_key:
                error_msg = "No existing course design found to modify"
                print(f"❌ [CourseDesignAgent] {error_msg}")
                yield {"type": "error", "content": error_msg}
                return
            
            current_course_design = await self.storage.get_course_design_content(r2_key)
            
            if not current_course_design:
                error_msg = "Could not retrieve current course design"
                print(f"❌ [CourseDesignAgent] {error_msg}")
                yield {"type": "error", "content": error_msg}
                return
            
            print(f"✅ [CourseDesignAgent] Retrieved current course design ({len(current_course_design)} chars)")
            
            # Send start signal
            print(f"📤 [CourseDesignAgent] Sending start signal...")
            yield {"type": "start", "content": f"🔄 Analyzing modification request: {modification_request}..."}
            
            # Step 1: Analyze what needs to be changed
            print(f"🔍 [CourseDesignAgent] Analyzing modification request...")
            yield {"type": "progress", "content": "🔍 Analyzing current structure..."}
            
            analysis_result = await self._analyze_modification_request(current_course_design, modification_request)
            
            if not analysis_result.get("success"):
                error_msg = f"Could not analyze modification request: {analysis_result.get('error')}"
                print(f"❌ [CourseDesignAgent] {error_msg}")
                yield {"type": "error", "content": error_msg}
                return
            
            print(f"✅ [CourseDesignAgent] Analysis complete: {analysis_result['change_type']}")
            print(f"🎯 [CourseDesignAgent] CRITICAL DEBUG - Change type detected: {analysis_result['change_type']}")
            print(f"🎯 [CourseDesignAgent] CRITICAL DEBUG - Target text: {analysis_result.get('target_text')}")
            print(f"🎯 [CourseDesignAgent] CRITICAL DEBUG - Replacement text: {analysis_result.get('replacement_text')}")
            yield {"type": "progress", "content": f"🎯 Identified change: {analysis_result['description']}"}
            
            # Step 2: Apply targeted modification
            print(f"🔧 [CourseDesignAgent] Applying targeted modification...")
            yield {"type": "progress", "content": "🔧 Applying targeted changes..."}
            
            if analysis_result["change_type"] == "simple_text_replacement":
                print(f"🎯🎯🎯 [CourseDesignAgent] ENTERING SIMPLE TEXT REPLACEMENT PATH!")
                # Handle simple text replacements (like module name changes)
                print(f"🎯 [CourseDesignAgent] Processing simple text replacement...")
                yield {"type": "progress", "content": "🎯 Locating target text..."}
                
                # Get LLM coordinates for the replacement
                modification_request = f"Change '{analysis_result['target_text']}' to '{analysis_result['replacement_text']}'" if analysis_result['target_text'] else f"Change to '{analysis_result['replacement_text']}'"
                coordinates = await self._get_llm_coordinates(current_course_design, modification_request)
                
                if coordinates.get("success"):
                    print(f"✅ [CourseDesignAgent] LLM coordinates obtained successfully")
                    yield {"type": "progress", "content": f"📍 Found target at line {coordinates['start_line']}"}
                    
                    # Send targeted change event with coordinates for visual highlighting
                    yield {
                        "type": "targeted_change_start",
                        "change_type": "text_replacement",
                        "target": coordinates["exact_text_to_replace"],
                        "replacement": coordinates["replacement_text"],
                        "description": analysis_result["description"],
                        "coordinates": {
                            "start_line": coordinates["start_line"],
                            "end_line": coordinates["end_line"],
                            "exact_text_to_replace": coordinates["exact_text_to_replace"],
                            "replacement_text": coordinates["replacement_text"]
                        }
                    }
                    
                    # Apply the coordinate-based replacement
                    modified_course_design = self._apply_coordinate_based_replacement(current_course_design, coordinates)
                    
                    # Send completion with the modified content - NO STREAMING OF FULL CONTENT
                    yield {
                        "type": "targeted_change_complete",
                        "change_type": "text_replacement",
                        "target": coordinates["exact_text_to_replace"],
                        "replacement": coordinates["replacement_text"],
                        "description": analysis_result["description"],
                        "full_content": modified_course_design,
                        "coordinates": {
                            "start_line": coordinates["start_line"],
                            "end_line": coordinates["end_line"],
                            "exact_text_to_replace": coordinates["exact_text_to_replace"],
                            "replacement_text": coordinates["replacement_text"]
                        }
                    }
                else:
                    print(f"❌ [CourseDesignAgent] LLM coordinate detection failed")
                    print(f"❌ [CourseDesignAgent] Coordinates error: {coordinates.get('error')}")
                    
                    # For modifications, we should NOT fall back to full AI rewrite
                    # Instead, return an error or try a simpler approach
                    error_msg = f"Could not locate target text for modification: {modification_request}"
                    print(f"❌ [CourseDesignAgent] {error_msg}")
                    yield {"type": "error", "content": error_msg}
                    return
                
            else:
                # For complex changes, use AI but with better prompting
                print(f"🤖 [CourseDesignAgent] Using AI for complex modification...")
                yield {"type": "progress", "content": "🤖 Processing complex changes..."}
                
                modified_course_design = await self._apply_ai_modification(
                    current_course_design, 
                    modification_request, 
                    analysis_result
                )
                
                # Stream the AI-generated content
                yield {
                    "type": "content",
                    "content": "",  # No incremental content for complex changes
                    "full_content": modified_course_design
                }
            
            print(f"✅ [CourseDesignAgent] Modification applied successfully")
            
            # Upload modified course design to R2
            print(f"💾 [CourseDesignAgent] Starting R2 upload...")
            yield {"type": "progress", "content": "💾 Saving changes..."}
            
            # Get current version and increment
            current_version = course.get("course_design_version", course.get("curriculum_version", 1))
            new_version = current_version + 1
            
            print(f"📋 [CourseDesignAgent] Uploading version {new_version} to R2...")
            upload_result = await self.storage.upload_course_design(
                course_id=course_id,
                content=modified_course_design,
                source="modified",
                version=new_version
            )
            
            print(f"📤 [CourseDesignAgent] R2 upload result: {upload_result.get('success')}")
            if not upload_result.get("success"):
                error_msg = f"Failed to upload modified course design: {upload_result.get('error')}"
                print(f"❌ [CourseDesignAgent] {error_msg}")
                yield {"type": "error", "content": error_msg}
                return
            
            print(f"✅ [CourseDesignAgent] R2 upload successful: {upload_result['r2_key']}")
            
            # Update course with R2 information
            print(f"🔄 [CourseDesignAgent] Updating course database...")
            update_result = await self.db.update_course(course_id, {
                "course_design_r2_key": upload_result["r2_key"],
                "course_design_public_url": upload_result["public_url"],
                "course_design_version": new_version,
                "course_design_updated_at": datetime.utcnow()
            })
            
            print(f"📋 [CourseDesignAgent] Course update result: {update_result}")
            
            # Store the completion message in chat history BEFORE sending completion signal
            completion_message = f"✅ Successfully applied targeted modification: {analysis_result['description']}"
            try:
                print(f"💬 [CourseDesignAgent] Storing completion message in chat...")
                await self.messages.store_message(course_id, user_id, completion_message, "assistant")
                print(f"✅ [CourseDesignAgent] Successfully stored completion message for course {course_id}")
            except Exception as e:
                print(f"❌ [CourseDesignAgent] Failed to store completion message: {e}")
                import traceback
                print(f"Full traceback: {traceback.format_exc()}")
                # Still send completion even if message storage fails
            
            # Send completion signal AFTER storing the message
            print(f"🎉 [CourseDesignAgent] Sending completion signal...")
            yield {
                "type": "complete",
                "content": completion_message,
                "r2_key": upload_result["r2_key"],
                "public_url": upload_result["public_url"],
                "full_content": modified_course_design,
                "change_summary": {
                    "type": analysis_result["change_type"],
                    "description": analysis_result["description"],
                    "target": analysis_result.get("target_text"),
                    "replacement": analysis_result.get("replacement_text")
                }
            }
            
            print(f"🎯 [CourseDesignAgent] TARGETED stream modification completed successfully!")
            
        except Exception as e:
            error_msg = f"Failed to modify course design: {str(e)}"
            print(f"❌ [CourseDesignAgent] CRITICAL ERROR: {error_msg}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            yield {"type": "error", "content": error_msg}

    async def _get_course_design_info(self, course_id: str) -> Dict[str, Any]:
        """Get current course design information and content"""
        try:
            # Get course info
            course = await self.db.find_course(course_id)
            if not course:
                return {"success": False, "error": "Course not found"}
            
            # Handle backward compatibility
            source = course.get("course_design_source", course.get("curriculum_source", "unknown"))
            version = course.get("course_design_version", course.get("curriculum_version", 0))
            updated_at = course.get("course_design_updated_at", course.get("curriculum_updated_at", "unknown"))
            r2_key = course.get("course_design_r2_key", course.get("curriculum_r2_key"))
            public_url = course.get("course_design_public_url", course.get("curriculum_public_url"))
            
            course_design_info = {
                "success": True,
                "source": source,
                "version": version,
                "updated_at": updated_at,
                "r2_key": r2_key,
                "public_url": public_url,
                "has_course_design": bool(r2_key),
                "has_pedagogy": course.get("has_pedagogy", False),
                "has_assessments": course.get("has_assessments", False),
                "design_components": course.get("design_components", ["curriculum"])
            }
            
            return course_design_info
            
        except Exception as e:
            return {"success": False, "error": f"Failed to get course design info: {str(e)}"}

    async def _process_uploaded_materials(self, course_id: str, curriculum_content: str, pedagogy_content: Optional[str] = None) -> Dict[str, Any]:
        """Process uploaded curriculum and pedagogy files into unified course design"""
        try:
            # Get course info
            course = await self.db.find_course(course_id)
            if not course:
                return {"success": False, "error": "Course not found"}
            
            # Build processing prompt
            processing_prompt = f"""You are an expert instructional designer. Process these uploaded materials into a comprehensive course design following the specified format.

Course Name: {course['name']}
Course Description: {course.get('description', '')}

CURRICULUM CONTENT:
{curriculum_content}

PEDAGOGY CONTENT:
{pedagogy_content or "None provided - please generate appropriate pedagogy notes based on the curriculum content"}

Your task:
1. Extract and organize the curriculum structure from the uploaded content
2. Integrate existing pedagogy notes or generate comprehensive new ones if not provided
3. Add detailed assessment ideas and rubrics aligned with learning objectives
4. Ensure proper Bloom's taxonomy tagging for all learning outcomes
5. Fill any gaps to create a complete instructional design package
6. Structure everything in the standard format

Output format - Follow this EXACT structure:
📚 [Course Title]
Level: [Beginner/Intermediate/Advanced]
Duration: [Time estimate based on content]
Prerequisites: [Required knowledge]
Tools & Platforms: [Technologies/tools needed]

Module 1: [Module Title]
Learning Outcomes (LOs)

LO1.1: [Specific learning objective] (Remember/Understand/Apply/Analyze/Evaluate/Create)

LO1.2: [Specific learning objective] (Bloom Level)

Pedagogy Notes:

[Teaching strategy with specific techniques]

[Analogies and real-world examples]

[Interactive demonstrations and hands-on activities]

Assessment Ideas:

[Assessment type]: [Description and requirements]

[Assessment type]: [Description and requirements]

[Continue for all modules...]

Final Project
Goal: [Project description]
Requirements:
[Detailed requirements list]

Rubric (out of 100 points):
[Criteria]: [Points]
[Criteria]: [Points]

Create a comprehensive, well-structured course design that integrates the uploaded materials."""
            
            client = await self.openai.get_client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": processing_prompt}],
                temperature=0.7
            )
            
            processed_course_design = response.choices[0].message.content
            
            # Upload processed course design to R2
            current_version = course.get("course_design_version", course.get("curriculum_version", 0))
            new_version = current_version + 1
            
            upload_result = await self.storage.upload_course_design(
                course_id=course_id,
                content=processed_course_design,
                source="uploaded_processed",
                version=new_version
            )
            
            if not upload_result.get("success"):
                return {"success": False, "error": f"Failed to upload processed course design: {upload_result.get('error')}"}
            
            # Update course with R2 information
            await self.db.update_course(course_id, {
                "course_design_r2_key": upload_result["r2_key"],
                "course_design_public_url": upload_result["public_url"],
                "course_design_source": "uploaded_processed",
                "course_design_version": new_version,
                "course_design_updated_at": datetime.utcnow(),
                "workflow_step": "course_design_complete",
                "has_pedagogy": True,
                "has_assessments": True,
                "design_components": ["curriculum", "pedagogy", "assessments"]
            })
            
            return {
                "success": True,
                "course_design": processed_course_design,
                "version": new_version,
                "r2_key": upload_result["r2_key"],
                "public_url": upload_result["public_url"]
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to process uploaded materials: {str(e)}"}
    
    async def _analyze_modification_request(self, current_content: str, modification_request: str) -> Dict[str, Any]:
        """Analyze the modification request to determine what type of change is needed"""
        try:
            print(f"🔍 [CourseDesignAgent] Analyzing modification request: {modification_request}")
            print(f"📄 [CourseDesignAgent] Content length: {len(current_content)} characters")
            print(f"📄 [CourseDesignAgent] Content preview (first 200 chars): {current_content[:200]}...")
            
            # Use AI to analyze the modification request
            analysis_prompt = f"""You are an expert at analyzing course design modification requests. 

Current Course Design:
{current_content}

User's Modification Request: {modification_request}

Analyze this request and determine:
1. What type of change is needed (simple_text_replacement, content_addition, content_removal, structure_change, complex_modification)
2. What specific text/content needs to be changed
3. What it should be changed to
4. A clear description of the change

For simple text replacements (like changing module names, titles, etc.), identify the exact text to find and replace.

Respond in JSON format:
{{
    "change_type": "simple_text_replacement|content_addition|content_removal|structure_change|complex_modification",
    "description": "Clear description of what will be changed",
    "target_text": "Exact text to find (for simple replacements)",
    "replacement_text": "What to replace it with (for simple replacements)",
    "complexity": "low|medium|high",
    "confidence": "high|medium|low"
}}

Examples:
- "change module 1 name to basics of RAG" → simple_text_replacement
- "add a new module about advanced topics" → content_addition  
- "remove the final project section" → content_removal
- "reorganize modules in different order" → structure_change
- "rewrite the pedagogy notes to be more interactive" → complex_modification"""

            client = await self.openai.get_client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.3  # Lower temperature for more consistent analysis
            )
            
            analysis_text = response.choices[0].message.content.strip()
            print(f"🔍 [CourseDesignAgent] Raw analysis response: {analysis_text}")
            
            # Try to parse JSON response
            try:
                # Extract JSON from response if it's wrapped in markdown
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
                
                print(f"✅ [CourseDesignAgent] Analysis successful: {analysis_result['change_type']}")
                return analysis_result
                
            except json.JSONDecodeError as e:
                print(f"❌ [CourseDesignAgent] Failed to parse JSON analysis: {e}")
                # Fallback to simple text replacement detection
                return self._fallback_analysis(modification_request)
                
        except Exception as e:
            print(f"❌ [CourseDesignAgent] Analysis error: {e}")
            return {"success": False, "error": f"Failed to analyze modification request: {str(e)}"}
    
    def _fallback_analysis(self, modification_request: str) -> Dict[str, Any]:
        """Fallback analysis using simple pattern matching"""
        request_lower = modification_request.lower()
        
        # Simple pattern matching for common requests
        if "change" in request_lower and ("name" in request_lower or "title" in request_lower):
            # Try to extract what to change and what to change it to
            if "module" in request_lower:
                # Pattern: "change module X name to Y"
                words = modification_request.split()
                try:
                    to_index = words.index("to")
                    new_name = " ".join(words[to_index + 1:])
                    
                    return {
                        "success": True,
                        "change_type": "simple_text_replacement",
                        "description": f"Change module name to '{new_name}'",
                        "target_text": None,  # Will be determined by pattern matching
                        "replacement_text": new_name,
                        "complexity": "low",
                        "confidence": "medium"
                    }
                except (ValueError, IndexError):
                    pass
        
        # Default to complex modification
        return {
            "success": True,
            "change_type": "complex_modification",
            "description": f"Apply requested changes: {modification_request}",
            "complexity": "high",
            "confidence": "low"
        }
    
    async def _apply_simple_text_replacement(self, content: str, target_text: Optional[str], replacement_text: str) -> str:
        """Apply simple text replacement using LLM-powered coordinate detection"""
        try:
            print(f"🔧 [CourseDesignAgent] Applying LLM-powered simple text replacement")
            print(f"   🎯 Target: {target_text}")
            print(f"   🔄 Replacement: {replacement_text}")
            
            # Use LLM to get precise coordinates for the replacement
            modification_request = f"Change '{target_text}' to '{replacement_text}'" if target_text else f"Change to '{replacement_text}'"
            coordinates = await self._get_llm_coordinates(content, modification_request)
            
            if coordinates.get("success"):
                print(f"✅ [CourseDesignAgent] LLM coordinates obtained successfully")
                # Apply coordinate-based replacement
                modified_content = self._apply_coordinate_based_replacement(content, coordinates)
                return modified_content
            else:
                print(f"❌ [CourseDesignAgent] LLM coordinate detection failed: {coordinates.get('error')}")
                print(f"🔄 [CourseDesignAgent] Falling back to AI modification")
                # Fallback to AI modification if coordinate detection fails
                return await self._apply_ai_modification(content, modification_request, {
                    "change_type": "simple_text_replacement",
                    "description": f"Change to '{replacement_text}'"
                })
                
        except Exception as e:
            print(f"❌ [CourseDesignAgent] Error in LLM-powered text replacement: {e}")
            # Fallback to AI modification
            return await self._apply_ai_modification(content, f"Change to: {replacement_text}", {
                "change_type": "simple_text_replacement",
                "description": f"Change to '{replacement_text}'"
            })
    
    async def _get_llm_coordinates(self, content: str, modification_request: str) -> Dict[str, Any]:
        """Use LLM to get precise coordinates for targeted modifications"""
        try:
            print(f"🤖 [CourseDesignAgent] Getting LLM coordinates for modification: {modification_request}")
            print(f"📄 [CourseDesignAgent] Content has {len(content)} characters and {len(content.split(chr(10)))} lines")
            
            # Split content into numbered lines for reference
            lines = content.split('\n')
            numbered_content = ""
            for i, line in enumerate(lines, 1):
                numbered_content += f"{i:3d}: {line}\n"
            
            print(f"📋 [CourseDesignAgent] Numbered content preview (first 500 chars):")
            print(f"📋 {numbered_content[:500]}...")
            print(f"📋 [CourseDesignAgent] Total numbered content length: {len(numbered_content)} characters")
            
            coordinate_prompt = f"""You are an expert content analyzer. Analyze this course design content and identify the EXACT location for the requested change.

NUMBERED CONTENT:
{numbered_content}

MODIFICATION REQUEST: {modification_request}

Your task:
1. Identify exactly what text needs to be changed
2. Find the precise line number(s) where this text appears
3. Determine the exact text to replace and what to replace it with
4. Provide context for verification

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
    "full_line_content": "The complete line content that contains the target text",
    "confidence": "high|medium|low",
    "modification_type": "title_change|content_addition|content_removal|structure_change"
}}

Examples:
- "change module 1 name to basics of RAG" → Find "Module 1 — [current name]" and replace the name part
- "change the title to Advanced Topics" → Find the main title and replace it
- "update learning outcome 2.1" → Find "LO2.1:" and modify its content

Be precise and only identify the minimal text that needs to change."""

            client = await self.openai.get_client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": coordinate_prompt}],
                temperature=0.1  # Very low temperature for precise analysis
            )
            
            coordinate_text = response.choices[0].message.content.strip()
            print(f"🤖 [CourseDesignAgent] Raw coordinate response: {coordinate_text}")
            
            # Parse JSON response
            try:
                # Extract JSON from response if it's wrapped in markdown
                if "```json" in coordinate_text:
                    json_start = coordinate_text.find("```json") + 7
                    json_end = coordinate_text.find("```", json_start)
                    coordinate_text = coordinate_text[json_start:json_end].strip()
                elif "```" in coordinate_text:
                    json_start = coordinate_text.find("```") + 3
                    json_end = coordinate_text.find("```", json_start)
                    coordinate_text = coordinate_text[json_start:json_end].strip()
                
                coordinates = json.loads(coordinate_text)
                
                # Validate the coordinates
                if self._validate_coordinates(coordinates, lines):
                    print(f"✅ [CourseDesignAgent] Valid coordinates received: {coordinates['target_section']}")
                    return coordinates
                else:
                    print(f"❌ [CourseDesignAgent] Invalid coordinates, falling back to AI modification")
                    return {"success": False, "error": "Invalid coordinates"}
                    
            except json.JSONDecodeError as e:
                print(f"❌ [CourseDesignAgent] Failed to parse coordinate JSON: {e}")
                return {"success": False, "error": f"JSON parsing failed: {str(e)}"}
                
        except Exception as e:
            print(f"❌ [CourseDesignAgent] Error getting LLM coordinates: {e}")
            return {"success": False, "error": f"Coordinate detection failed: {str(e)}"}
    
    def _validate_coordinates(self, coordinates: Dict[str, Any], lines: List[str]) -> bool:
        """Validate that the coordinates make sense"""
        try:
            start_line = coordinates.get("start_line", 0)
            end_line = coordinates.get("end_line", 0)
            exact_text = coordinates.get("exact_text_to_replace", "")
            
            # Check line numbers are valid
            if start_line < 1 or start_line > len(lines):
                print(f"❌ [CourseDesignAgent] Invalid start_line: {start_line}")
                return False
            
            if end_line < 1 or end_line > len(lines):
                print(f"❌ [CourseDesignAgent] Invalid end_line: {end_line}")
                return False
            
            # Check that the exact text exists in the specified line(s)
            target_lines = lines[start_line-1:end_line]  # Convert to 0-indexed
            combined_text = '\n'.join(target_lines)
            
            if exact_text and exact_text not in combined_text:
                print(f"❌ [CourseDesignAgent] Target text '{exact_text}' not found in lines {start_line}-{end_line}")
                print(f"📄 [CourseDesignAgent] Line content: '{combined_text}'")
                return False
            
            print(f"✅ [CourseDesignAgent] Coordinates validated successfully")
            return True
            
        except Exception as e:
            print(f"❌ [CourseDesignAgent] Coordinate validation error: {e}")
            return False
    
    def _apply_coordinate_based_replacement(self, content: str, coordinates: Dict[str, Any]) -> str:
        """Apply targeted replacement using LLM-provided coordinates"""
        try:
            print(f"🔧 [CourseDesignAgent] Applying coordinate-based replacement")
            print(f"   🎯 Target: {coordinates['exact_text_to_replace']}")
            print(f"   🔄 Replacement: {coordinates['replacement_text']}")
            print(f"   📍 Lines: {coordinates['start_line']}-{coordinates['end_line']}")
            
            lines = content.split('\n')
            start_line = coordinates['start_line'] - 1  # Convert to 0-indexed
            end_line = coordinates['end_line'] - 1
            
            # Apply the replacement to the specified lines
            for line_idx in range(start_line, end_line + 1):
                if line_idx < len(lines):
                    old_line = lines[line_idx]
                    new_line = old_line.replace(
                        coordinates['exact_text_to_replace'],
                        coordinates['replacement_text']
                    )
                    lines[line_idx] = new_line
                    print(f"   📝 Line {line_idx + 1}: '{old_line}' → '{new_line}'")
            
            modified_content = '\n'.join(lines)
            print(f"✅ [CourseDesignAgent] Coordinate-based replacement completed")
            return modified_content
            
        except Exception as e:
            print(f"❌ [CourseDesignAgent] Error in coordinate-based replacement: {e}")
            raise e
    
    async def _apply_ai_modification(self, content: str, modification_request: str, analysis_result: Dict[str, Any]) -> str:
        """Apply AI-based modification with improved prompting"""
        try:
            print(f"🤖 [CourseDesignAgent] Applying AI modification")
            
            # Build a more targeted prompt based on analysis
            if analysis_result.get("change_type") == "simple_text_replacement":
                modification_prompt = f"""You are an expert editor. Make a PRECISE, TARGETED change to this course design.

INSTRUCTION: {modification_request}

CURRENT CONTENT:
{content}

RULES:
1. Make ONLY the specific change requested
2. Do NOT rewrite or regenerate the entire content
3. Preserve ALL existing structure, formatting, and content
4. Change ONLY what was specifically requested
5. Maintain the exact same markdown formatting
6. Keep all tables, headers, and structure intact

Output the COMPLETE course design with ONLY the requested change applied."""

            else:
                modification_prompt = f"""You are an instructional designer. Modify this course design based on the specific request.

MODIFICATION REQUEST: {modification_request}
CHANGE TYPE: {analysis_result.get('change_type', 'modification')}

CURRENT COURSE DESIGN:
{content}

INSTRUCTIONS:
1. Apply the requested modification while preserving the overall structure
2. Maintain the markdown format and table structure
3. Keep learning outcomes with Bloom's taxonomy levels
4. Preserve pedagogy notes and assessment ideas that aren't being changed
5. Ensure the modification integrates well with existing content
6. Only change what's specifically requested

Output the complete modified course design."""

            client = await self.openai.get_client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": modification_prompt}],
                temperature=0.3  # Lower temperature for more precise modifications
            )
            
            modified_content = response.choices[0].message.content
            print(f"✅ [CourseDesignAgent] AI modification completed")
            return modified_content
            
        except Exception as e:
            print(f"❌ [CourseDesignAgent] Error in AI modification: {e}")
            raise e
    
    async def _generate_fallback_research(self, course_name: str) -> str:
        """Generate fallback research content when web search fails"""
        try:
            print(f"🔄 [CourseDesignAgent] Generating fallback research for: {course_name}")
            
            fallback_prompt = f"""You are a subject matter expert. Generate comprehensive research content about "{course_name}" using your knowledge base.

IMPORTANT: This is fallback research when web search is unavailable. Use your extensive knowledge to provide current, relevant information.

Generate a detailed research report covering:

### 1. Latest Technologies & Tools (2025)
Current tools, frameworks, and technologies in this field

### 2. Recent Breakthroughs & Innovations  
Major developments and innovations in recent years

### 3. Current Industry Trends & Practices
Leading approaches and methodologies being used

### 4. Emerging Developments & Future Directions
What's expected in the near future

### 5. Real-World Applications & Case Studies
Practical applications and successful implementations

### 6. Academic Research & New Findings
Theoretical developments and research insights

### 7. Market Adoption & Industry Impact
Business impact and industry adoption patterns

### 8. Current Best Practices & Methodologies
Established best practices and proven methodologies

### 9. Key Players & Leading Organizations
Important companies, organizations, and thought leaders

### 10. Essential Knowledge for 2025
Critical knowledge and skills needed today

Focus on providing substantial, informative content for each section. This research will inform course design, so prioritize educational value and current relevance."""

            client = await self.openai.get_client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": fallback_prompt}]
            )
            
            fallback_content = response.choices[0].message.content
            print(f"✅ [CourseDesignAgent] Fallback research generated ({len(fallback_content)} chars)")
            
            return f"""

### 🔄 Fallback Research Analysis

*Note: This research was generated using AI knowledge base due to web search limitations*

{fallback_content}

"""
            
        except Exception as e:
            print(f"❌ [CourseDesignAgent] Error generating fallback research: {e}")
            return f"""

### ⚠️ Research Generation Issue

Unable to generate comprehensive research at this time. The course design will proceed with foundational educational principles and general best practices for "{course_name}".

**Key Focus Areas:**
- Fundamental concepts and principles
- Progressive skill building
- Practical applications
- Industry-relevant examples
- Assessment strategies

"""
    
    def _fix_table_formatting(self, content: str) -> str:
        """Fix common table formatting issues in generated content"""
        try:
            print(f"🔧 [CourseDesignAgent] Fixing table formatting issues...")
            
            # Fix escaped pipe characters
            content = content.replace('\\|', '|')
            
            # Fix inconsistent table headers
            lines = content.split('\n')
            fixed_lines = []
            
            for i, line in enumerate(lines):
                # Check if this line looks like a table row
                if '|' in line and line.strip().startswith('|') and line.strip().endswith('|'):
                    # Count pipes to ensure consistent structure
                    pipe_count = line.count('|')
                    
                    # If this is a chapter table row, ensure it has exactly 3 pipes (2 columns)
                    if 'Chapter' in line and 'Details' not in line:
                        # This is a chapter row, ensure proper formatting
                        if pipe_count < 3:
                            # Add missing pipes
                            line = line.rstrip('|') + ' |'
                        elif pipe_count > 3:
                            # Remove extra pipes (keep first 2 columns)
                            parts = line.split('|')
                            if len(parts) >= 3:
                                line = f"| {parts[1].strip()} | {parts[2].strip()} |"
                    
                    # Fix table separator lines
                    elif line.strip().startswith('|') and '-' in line:
                        # This is a table separator, ensure it matches the header
                        if 'Chapter' in (lines[i-1] if i > 0 else ''):
                            line = "| ------- | ------- |"
                
                fixed_lines.append(line)
            
            fixed_content = '\n'.join(fixed_lines)
            
            # Additional cleanup for common issues
            fixed_content = fixed_content.replace('| **Chapter**           | **Details**', '| **Chapter** | **Details** |')
            fixed_content = fixed_content.replace('| --------------------- |', '| ------- |')
            
            print(f"✅ [CourseDesignAgent] Table formatting fixed")
            return fixed_content
            
        except Exception as e:
            print(f"❌ [CourseDesignAgent] Error fixing table formatting: {e}")
            # Return original content if fixing fails
            return content
