import re
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from bson import ObjectId

from ...infrastructure.ai.openai_service import OpenAIService
from ...infrastructure.database.database_service import DatabaseService
from ..services.message_service import MessageService
from ..services.context_service import ContextService
from ...infrastructure.storage.r2_storage import R2StorageService
from ...models import ContentMaterial


class CourseStructureAgent:
    """CourseStructureAgent with chapter-scoped content generation and no material limits"""
    
    # No material limits - generate content based on course design requirements
    # Focus on chapter-scoped content generation to prevent cross-chapter mixing
    
    def __init__(self, openai_service: OpenAIService, database_service: DatabaseService,
                 message_service: MessageService, context_service: ContextService,
                 r2_storage_service: R2StorageService):
        self.openai = openai_service
        self.db = database_service
        self.messages = message_service
        self.context = context_service
        self.storage = r2_storage_service
        self.model = "gpt-4o-mini"
    
    def get_function_definitions(self) -> List[Dict[str, Any]]:
        """Define functions that this agent can call"""
        return [
            {
                "name": "generate_content_structure",
                "description": "Generate constrained content structure based on course design",
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
                "name": "approve_structure",
                "description": "Approve the generated structure for content creation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {
                            "type": "string",
                            "description": "The ID of the course"
                        },
                        "approved": {
                            "type": "boolean",
                            "description": "Whether the structure is approved"
                        }
                    },
                    "required": ["course_id", "approved"]
                }
            },
            {
                "name": "start_content_creation",
                "description": "Start the content creation process after structure approval",
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
        """Generate system prompt using the master instructional design approach"""
        course = context.get("course_state")
        course_id = context.get('current_course_id', '')
        
        return f"""You are an instructional design assistant.

IMPORTANT: When calling functions, always use the EXACT course_id parameter that was passed to you in the conversation context. The course_id is: {course_id}
DO NOT use the course name or any other value as the course_id parameter.

CRITICAL: APPROVAL MESSAGE HANDLING
If the user message contains "approve", "approve and proceed", "start content creation", or similar approval language:
1. First call approve_structure with approved=true
2. Then call start_content_creation to begin content generation
3. This will update the database and trigger the content generation workflow

You will always be given two inputs:
1. `course_design.md` → contains course structure (modules, chapters, descriptions, learning objectives with Bloom's taxonomy levels, pedagogy strategies, assessments, and learner type such as Beginner, Intermediate, or Expert).
2. `research.md` → contains domain-specific research (tools, trends, case studies, industry practices, skills, academic findings, etc.).

Your task:
Generate a **sequential slide deck outline** for the course.

---

### Rules for Output:
1. For each **chapter** inside a module:
   - Expand into **multiple slides** (minimum 3, usually 4–6 depending on depth).
   - Each slide must have:
     - **Slide {{n}}: {{Title}}**
     - **Description:** A detailed paragraph (3–6 sentences) explaining EXACTLY what the learner will see, learn, or practice on that slide. 
       - Use clear teaching tone, like instructor notes.  
       - Include research examples, case studies, analogies, or tools wherever possible.
       - Tie back to Bloom's taxonomy level and learner type (Beginner, Intermediate, Expert).  
   - Keep all content **chapter-scoped only** (don't mix across chapters).

2. After finishing **content slides for a chapter**, generate **assessment slides for that chapter**:
   - Assessments must directly test what was just taught.  
   - Formats: Multiple-choice (MCQ), True/False, Matching, or Quick Scenario Choice.  
   - Keep them **quick and fast** (no long essays).  
   - Number of assessments:
     - Short chapter (2–3 slides) → 1 assessment  
     - Medium chapter (4–5 slides) → 2 assessments  
     - Long/dense chapter (6+ slides) → 3–4 assessments  

3. Sequential flow:
   - Module → Chapter → Content Slides → Assessments → Next Chapter.  
   - Do NOT generate all content first and assessments later — assessments always follow the chapter's slides.

---

### Output Format Example (STRICTLY FOLLOW):

## Chapter 1.1: What Managers Do — Purpose & Outcomes

**Slide 1: The Role of a Manager**  
*Description:* This slide introduces the essential distinction between an individual contributor (IC) and a manager. Learners explore how a manager's impact is multiplied through others, shifting from personal execution to enabling team performance. It clarifies why organizations invest in managers — because their decisions and behaviors influence team engagement, retention, and productivity at scale.

**Slide 2: Core Responsibilities of Managers**  
*Description:* Breaks down the three universal responsibilities of managers: (1) people leadership (hiring, coaching, development), (2) delivery ownership (meeting targets, ensuring quality), and (3) stakeholder alignment (communicating priorities and trade-offs). Each responsibility is illustrated with practical workplace examples, so learners can connect abstract responsibilities to everyday actions.

**Slide 3: Measurable Outcomes Managers Influence**  
*Description:* Demonstrates how a manager's work connects to measurable business outcomes. Using Gallup's 2025 research, the slide highlights that disengaged managers drive costs in billions, while strong managers directly improve retention, performance, and time-to-promotion. Learners see how outcomes are tracked via analytics dashboards and why their behaviors matter beyond day-to-day operations.

**Slide 4: Manager as Conductor vs. Soloist**  
*Description:* Uses an analogy: an IC is like a soloist who excels individually, while a manager is like a conductor ensuring harmony across multiple performers. This visual comparison helps learners reframe leadership as orchestration rather than execution. The slide also prompts reflection on how their current style leans more toward "soloist" or "conductor."

### Assessments for Chapter 1.1
**Assessment Slide 1: Manager's Core Role**  
*Question:* Which of the following best describes the difference between an IC and a Manager?  
*Options:*  
A) ICs multiply outcomes through others, Managers focus only on their own tasks  
B) ICs deliver individually, Managers enable performance through teams ✅  
C) Both ICs and Managers are evaluated only on their personal output  
D) Managers avoid alignment with stakeholders  

**Assessment Slide 2: Responsibilities Check**  
*Question:* Match each responsibility with its example.  
- People Leadership → [A. Hiring & Coaching, B. Delivering a report, C. Negotiating with executives]  
- Delivery Ownership → [ ]  
- Stakeholder Alignment → [ ]  

---

### Remember:
- Every chapter MUST follow this **content → assessment** flow.  
- Every slide description MUST be a full teaching note (not a phrase).  
- Adapt **depth and complexity** based on learner type (Beginner, Intermediate, Expert).

---

🎯 CHAPTER-SCOPED CONTENT GENERATION:
- Generate content ONLY for the specific chapter being processed
- Do NOT mix content from different chapters or modules
- Each chapter should be self-contained and focused
- Ensure all slides and assessments relate directly to the current chapter's learning objectives
- Avoid referencing concepts from other chapters unless explicitly building upon them

🛠️ AVAILABLE FUNCTIONS:
- generate_content_structure: Generate sequential slide deck outline based on course design and research
- approve_structure: Mark structure as approved for content creation
- start_content_creation: Begin content creation after approval

Focus on creating **instructor-quality slide descriptions** that provide clear guidance for content creation while maintaining strict chapter scope."""
    
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
        """Process a user message for constrained course structure generation"""
        
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
            print(f"🔄 \033[95m[CourseStructureAgent]\033[0m \033[1mSending request to Responses API...\033[0m")
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
            
            print(f"\n✅ \033[95m[CourseStructureAgent]\033[0m \033[1m\033[92mResponses API Response received\033[0m")
            
            # Process response output
            function_results = {}
            assistant_content = ""
            
            # Process all output items
            for item in response.output:
                if item.type == "function_call":
                    # Handle function calls
                    function_name = item.name
                    function_args = json.loads(item.arguments)
                    
                    print(f"🔧 [CourseStructureAgent] Processing function call: {function_name}")
                    
                    if function_name == "generate_content_structure":
                        # Check if this should be a streaming operation
                        course_id = function_args["course_id"]
                        
                        # For structure generation, we want to use streaming to provide real-time file updates
                        # Return a streaming signal instead of blocking execution
                        result = {
                            "success": True,
                            "streaming": True,
                            "course_id": course_id,
                            "message": "Content structure generation will stream in real-time"
                        }
                        function_results["structure_generated"] = result
                    elif function_name == "approve_structure":
                        result = await self._approve_structure(
                            function_args["course_id"],
                            function_args["approved"]
                        )
                        function_results["structure_approved"] = result
                    elif function_name == "start_content_creation":
                        result = await self._start_content_creation(function_args["course_id"])
                        function_results["content_creation_started"] = result
                
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
            print(f"CourseStructureAgent Responses API error: {e}")
            print(f"Full traceback: {traceback.format_exc()}")
            return {
                "response": "I apologize, but I'm experiencing some technical difficulties with structure generation. Please try again in a moment.",
                "course_id": course_id,
                "function_results": {},
                "error": str(e)
            }
    
    async def _generate_content_structure(self, course_id: str, streaming_callback=None) -> Dict[str, Any]:
        """Generate constrained content structure directly to ContentMaterial collection"""
        try:
            print(f"🎯 [CourseStructureAgent] Generating constrained structure for {course_id}")
            
            # Validate course_id format - check if it's a valid ObjectId
            if not self._is_valid_object_id(course_id):
                print(f"❌ [CourseStructureAgent] Invalid course_id format: {course_id}")
                return {"success": False, "error": f"Invalid course ID format: '{course_id}' is not a valid ObjectId"}
            
            # Get course info and check if generation is already in progress
            course = await self.db.find_course(course_id)
            if not course:
                return {"success": False, "error": "Course not found"}
            
            # Check if structure generation is already in progress for this course
            if course.get("structure_generation_in_progress", False):
                print(f"⚠️ [CourseStructureAgent] Structure generation already in progress for course {course_id}")
                return {"success": False, "error": "Structure generation is already in progress for this course. Please wait for it to complete."}
            
            # Set generation in progress flag
            await self.db.update_document("courses", course_id, {
                "structure_generation_in_progress": True,
                "structure_generation_started_at": datetime.utcnow()
            })
            
            try:
                # Continue with the actual generation process
                # Get course design content
                course_design_content = ""
                r2_key = course.get("course_design_r2_key")
                if r2_key:
                    course_design_content = await self.storage.get_course_design_content(r2_key)
                
                if not course_design_content:
                    return {"success": False, "error": "No course design found"}
                
                # Parse structure with strict constraints and incremental saving
                parse_result = await self._parse_course_design_constrained(course_design_content, course.get("name", ""), course_id, streaming_callback)
                
                if not parse_result["success"]:
                    return parse_result
                
                # No constraint validation needed - generate content based on course design requirements
                
                # Create ContentMaterial records directly
                materials_result = await self._create_content_materials_constrained(course_id, parse_result["structure"])
                
                if not materials_result["success"]:
                    return materials_result
            
                # Update course record with structure metadata
                await self._update_course_structure_metadata(
                    course_id, 
                    parse_result["structure"], 
                    materials_result["total_materials"]
                )
                
                print(f"✅ [CourseStructureAgent] Generated {materials_result['total_materials']} materials across {len(parse_result['structure']['modules'])} modules")
                
                return {
                    "success": True,
                    "structure": parse_result["structure"],
                    "total_materials": materials_result["total_materials"],
                    "total_modules": len(parse_result["structure"]["modules"]),
                    "constraints_applied": True
                }
                
            finally:
                # Always clear the generation in progress flag
                await self.db.update_document("courses", course_id, {
                    "structure_generation_in_progress": False,
                    "structure_generation_completed_at": datetime.utcnow()
                })
                print(f"🔓 [CourseStructureAgent] Released generation lock for course {course_id}")
            
        except Exception as e:
            print(f"❌ [CourseStructureAgent] Error generating structure: {e}")
            # Try to clear the flag in case of error
            try:
                await self.db.update_document("courses", course_id, {
                    "structure_generation_in_progress": False,
                    "structure_generation_error": str(e),
                    "structure_generation_error_at": datetime.utcnow()
                })
            except:
                pass  # Ignore errors when clearing flag
            return {"success": False, "error": f"Failed to generate structure: {str(e)}"}
    
    async def _parse_course_design_constrained(self, course_design_content: str, course_name: str, course_id: str = None, streaming_callback=None) -> Dict[str, Any]:
        """Parse course design with strict constraints and incremental saving"""
        try:
            print(f"📋 [CourseStructureAgent] Parsing course design with constraints and incremental saving")
            
            # First try exact markdown parsing with dynamic material generation and incremental saving
            basic_result = await self._parse_markdown_structure_constrained(course_design_content, course_name, course_id, streaming_callback)
            
            if basic_result["success"]:
                structure = basic_result["structure"]
                structure["course_title"] = course_name
                
                print(f"✅ [CourseStructureAgent] Parsed {len(structure['modules'])} modules from course design with incremental saving")
                return {"success": True, "structure": structure}
            
            # Fallback to constrained OpenAI parsing (without incremental saving)
            print(f"⚠️ [CourseStructureAgent] Markdown parsing failed, using constrained OpenAI parsing")
            return await self._openai_parse_constrained(course_design_content, course_name)
            
        except Exception as e:
            print(f"❌ [CourseStructureAgent] Error parsing course design: {e}")
            return {"success": False, "error": f"Failed to parse course design: {str(e)}"}
    
    async def _parse_markdown_structure_constrained(self, content: str, course_name: str, course_id: str = None, streaming_callback=None) -> Dict[str, Any]:
        """Parse markdown content with detailed chapter extraction and incremental material generation and saving"""
        try:
            print(f"📄 [CourseStructureAgent] Parsing markdown with incremental material generation and saving")
            
            lines = content.split('\n')
            structure = {
                "course_title": "",
                "modules": []
            }
            
            current_module = None
            total_materials_count = 0  # Track materials early to prevent constraint violations
            processed_chapters = set()  # Track processed chapters to prevent duplicates
            
            # Get research content for dynamic generation (once for all chapters)
            research_content = await self._get_research_content(course_name)
            
            # Clear existing materials if any to prevent duplicates - with course-specific isolation
            if course_id:
                existing_count = await self.db.count_documents("content_materials", {"course_id": ObjectId(course_id)})
                if existing_count > 0:
                    print(f"⚠️ [CourseStructureAgent] Found {existing_count} existing materials for course {course_id} - clearing to prevent duplicates")
                    db = await self.db.get_database()
                    # Use course_id in the delete query to ensure we only delete materials for THIS course
                    delete_result = await db.content_materials.delete_many({"course_id": ObjectId(course_id)})
                    print(f"🗑️ [CourseStructureAgent] Deleted {delete_result.deleted_count} materials for course {course_id}")
            
            # Single pass: collect chapter information, generate materials, and save immediately
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Extract course title
                if line.startswith('# ') and not structure["course_title"]:
                    structure["course_title"] = line[2:].strip().replace('📚 ', '')
                
                # Extract modules - no constraint on count
                elif line.startswith('## **Module '):
                    # Save previous module
                    if current_module:
                        structure["modules"].append(current_module)
                    
                    # Parse module title
                    module_match = re.match(r'## \*\*Module (\d+) — (.*?)\*\*', line)
                    if module_match:
                        module_number = int(module_match.group(1))
                        module_title = module_match.group(2)
                        
                        current_module = {
                            "module_number": module_number,
                            "title": module_title,
                            "chapters": []
                        }
                
                # Extract chapters, generate materials, and save immediately
                elif line.startswith('| **Chapter ') and current_module:
                    # Parse chapter from table row
                    chapter_match = re.match(r'\| \*\*Chapter (\d+)\.(\d+): (.*?)\*\* \|', line)
                    if chapter_match:
                        module_num = int(chapter_match.group(1))
                        chapter_num = int(chapter_match.group(2))
                        chapter_title = chapter_match.group(3)
                        
                        # Create unique chapter identifier to prevent duplicates
                        chapter_id = f"{module_num}.{chapter_num}"
                        
                        # Check if this chapter has already been processed
                        if chapter_id in processed_chapters:
                            print(f"⚠️ [CourseStructureAgent] Chapter {chapter_id}: {chapter_title} already processed, skipping duplicate")
                            continue
                        
                        # Mark chapter as processed
                        processed_chapters.add(chapter_id)
                        print(f"🔄 [CourseStructureAgent] Processing Chapter {chapter_id}: {chapter_title}")
                        
                        # No material limits - generate content based on course design requirements
                        
                        # Extract detailed chapter information from the next lines
                        chapter_details = await self._extract_chapter_details(lines, i, chapter_title)
                        
                        # Generate dynamic materials for this chapter
                        materials = await self._generate_dynamic_chapter_materials(
                            chapter_details, 
                            research_content, 
                            course_name
                        )
                        
                        # Save materials to database immediately if course_id is provided
                        if course_id and materials:
                            # Use chapter-scoped numbering (no global counters needed)
                            await self._save_chapter_materials_immediately(
                                course_id, module_num, chapter_num, materials, streaming_callback
                            )
                            print(f"💾 [CourseStructureAgent] Saved {len(materials)} materials for Chapter {module_num}.{chapter_num}: {chapter_title}")
                        
                        # Update actual count
                        total_materials_count += len(materials)
                        
                        # Create chapter object and add to current module immediately
                        chapter = {
                            "chapter_number": chapter_num,
                            "title": chapter_title,
                            "description": chapter_details.get("description", ""),
                            "learning_objective": chapter_details.get("learning_objective", ""),
                            "pedagogy_strategy": chapter_details.get("pedagogy_strategy", ""),
                            "assessment_idea": chapter_details.get("assessment_idea", ""),
                            "materials": materials
                        }
                        
                        current_module["chapters"].append(chapter)
                        
                        # No material limits - continue processing all chapters
            
            # Add the last module if it exists
            if current_module:
                structure["modules"].append(current_module)
            
            # Handle final project - add to last module as chapter
            if structure["modules"] and len(structure["modules"]) > 0:
                last_module = structure["modules"][-1]
                # Check if we need to add final project based on course design content
                if "## **Final Project**" in content:
                    final_project_materials = [
                        {
                            "type": "slide",
                            "title": "Final Project Overview",
                            "description": "Introduction to the capstone project, its objectives, and how it integrates course concepts"
                        },
                        {
                            "type": "slide", 
                            "title": "Project Requirements and Deliverables",
                            "description": "Detailed breakdown of project requirements, deliverables, timeline, and evaluation criteria"
                        },
                        {
                            "type": "assessment",
                            "title": "Final Project Submission and Evaluation",
                            "description": "Comprehensive assessment of the final project including presentation, documentation, and implementation"
                        }
                    ]
                    
                    # Save final project materials immediately if course_id is provided
                    if course_id:
                        final_chapter_num = len(last_module["chapters"]) + 1
                        await self._save_chapter_materials_immediately(
                            course_id, last_module["module_number"], final_chapter_num, final_project_materials, streaming_callback
                        )
                        print(f"💾 [CourseStructureAgent] Saved {len(final_project_materials)} materials for Final Project")
                    
                    final_chapter = {
                        "chapter_number": len(last_module["chapters"]) + 1,
                        "title": "Final Project",
                        "description": "Capstone project integrating all course concepts",
                        "materials": final_project_materials
                    }
                    last_module["chapters"].append(final_chapter)
                    total_materials_count += len(final_project_materials)
            
            print(f"✅ [CourseStructureAgent] Incremental parsing complete: {len(structure['modules'])} modules with {total_materials_count} materials saved incrementally")
            
            return {"success": True, "structure": structure, "total_materials_saved": total_materials_count}
            
        except Exception as e:
            print(f"❌ [CourseStructureAgent] Error in incremental markdown parsing: {e}")
            return {"success": False, "error": f"Failed to parse markdown: {str(e)}"}
    
    async def _extract_chapter_details(self, lines: List[str], start_index: int, chapter_title: str) -> Dict[str, str]:
        """Extract detailed chapter information from course design markdown"""
        try:
            details = {
                "title": chapter_title,
                "description": "",
                "learning_objective": "",
                "pedagogy_strategy": "",
                "assessment_idea": ""
            }
            
            # Look for the details in the next few lines after the chapter header
            for i in range(start_index + 1, min(start_index + 10, len(lines))):
                line = lines[i].strip()
                
                if line.startswith('**Description:**'):
                    # Extract description
                    desc_text = line.replace('**Description:**', '').strip()
                    # Continue reading until we hit the next field
                    j = i + 1
                    while j < len(lines) and not lines[j].strip().startswith('**') and lines[j].strip():
                        desc_text += " " + lines[j].strip()
                        j += 1
                    details["description"] = desc_text
                
                elif line.startswith('**Learning Objective:**'):
                    # Extract learning objective
                    obj_text = line.replace('**Learning Objective:**', '').strip()
                    # Continue reading until we hit the next field
                    j = i + 1
                    while j < len(lines) and not lines[j].strip().startswith('**') and lines[j].strip():
                        obj_text += " " + lines[j].strip()
                        j += 1
                    details["learning_objective"] = obj_text
                
                elif line.startswith('**Pedagogy Strategy:**'):
                    # Extract pedagogy strategy
                    ped_text = line.replace('**Pedagogy Strategy:**', '').strip()
                    # Continue reading until we hit the next field
                    j = i + 1
                    while j < len(lines) and not lines[j].strip().startswith('**') and lines[j].strip():
                        ped_text += " " + lines[j].strip()
                        j += 1
                    details["pedagogy_strategy"] = ped_text
                
                elif line.startswith('**Assessment Idea:**'):
                    # Extract assessment idea
                    assess_text = line.replace('**Assessment Idea:**', '').strip()
                    # Continue reading until we hit the next field
                    j = i + 1
                    while j < len(lines) and not lines[j].strip().startswith('**') and lines[j].strip():
                        assess_text += " " + lines[j].strip()
                        j += 1
                    details["assessment_idea"] = assess_text
                
                # Stop if we hit another chapter or module
                elif line.startswith('| **Chapter ') or line.startswith('## **Module '):
                    break
            
            print(f"📋 [CourseStructureAgent] Extracted details for chapter: {chapter_title}")
            return details
            
        except Exception as e:
            print(f"❌ [CourseStructureAgent] Error extracting chapter details: {e}")
            return {
                "title": chapter_title,
                "description": f"Content covering {chapter_title}",
                "learning_objective": f"Understand key concepts in {chapter_title}",
                "pedagogy_strategy": "Interactive learning with examples and practice",
                "assessment_idea": "Knowledge check and practical application"
            }
    
    async def _get_research_content(self, course_name: str) -> str:
        """Get research content for the course to inform dynamic material generation"""
        try:
            print(f"📚 [CourseStructureAgent] Fetching research content for: {course_name}")
            
            # Try to get research content from the course's research R2 key
            # This implementation attempts to fetch actual research content
            research_content = ""
            
            # In a full implementation, this would:
            # 1. Get the course record from the current context
            # 2. Check for research_r2_key in the course record
            # 3. Fetch research content from R2 storage using the key
            # 4. Parse and return relevant research findings
            
            # For now, we'll create contextual research content based on course name
            # This can be enhanced to fetch actual research when available
            
            # Generate contextual research based on course subject area
            subject_keywords = self._extract_subject_keywords(course_name)
            
            research_content = f"""
# Research Findings for {course_name}

## Subject Area Analysis
Based on course title analysis, key subject areas identified: {', '.join(subject_keywords)}

## Current Industry Trends (2025)
- Latest developments in {subject_keywords[0] if subject_keywords else 'the field'}
- Industry adoption rates and market dynamics
- Key players and thought leaders driving innovation
- Regulatory changes and compliance requirements
- Emerging best practices and methodologies

## Technologies and Tools
- Current state-of-the-art tools and frameworks in {subject_keywords[0] if subject_keywords else 'the domain'}
- Emerging technologies gaining traction
- Integration patterns and industry standards
- Performance benchmarks and comparisons
- Popular platforms and software solutions

## Real-World Applications
- Case studies from leading organizations
- Success stories and implementation examples
- Common use cases and business applications
- ROI metrics and business impact data
- Industry-specific applications and scenarios

## Challenges and Solutions
- Common implementation challenges in {subject_keywords[0] if subject_keywords else 'the field'}
- Proven solutions and workarounds
- Risk mitigation strategies
- Scalability considerations
- Cost-benefit analysis approaches

## Future Directions
- Predicted trends for the next 2-3 years
- Research and development focus areas
- Potential disruptions and innovations
- Skills and knowledge that will be in demand
- Career pathways and opportunities

## Learning Implications
- Key concepts students need to understand
- Practical skills that are most valuable
- Industry certifications and standards
- Hands-on experience requirements
- Project-based learning opportunities

## Pedagogical Considerations
- Most effective teaching methods for {subject_keywords[0] if subject_keywords else 'this subject'}
- Common student misconceptions and how to address them
- Assessment strategies that work well
- Real-world project ideas and case studies
- Industry connections and guest speaker opportunities
"""
            
            print(f"✅ [CourseStructureAgent] Contextual research content prepared ({len(research_content)} chars)")
            return research_content
            
        except Exception as e:
            print(f"❌ [CourseStructureAgent] Error getting research content: {e}")
            return f"""
# Research Context for {course_name}

## Basic Course Context
- Fundamental concepts and principles
- Core skills and knowledge areas
- Practical applications and examples
- Assessment and evaluation methods

## Subject-Specific Considerations
- Industry-relevant skills and knowledge
- Current trends and developments
- Practical applications and use cases
- Career pathways and opportunities

This content will be enhanced with specific research findings when available.
"""
    
    def _extract_subject_keywords(self, course_name: str) -> List[str]:
        """Extract subject keywords from course name for contextual research"""
        try:
            # Convert to lowercase and split into words
            words = course_name.lower().split()
            
            # Common subject area keywords to look for
            subject_areas = {
                'management': ['management', 'leadership', 'business', 'strategy', 'operations'],
                'technology': ['technology', 'software', 'programming', 'development', 'engineering', 'data', 'ai', 'machine learning'],
                'marketing': ['marketing', 'advertising', 'branding', 'digital', 'social media'],
                'finance': ['finance', 'accounting', 'economics', 'investment', 'banking'],
                'healthcare': ['healthcare', 'medical', 'nursing', 'health', 'clinical'],
                'education': ['education', 'teaching', 'learning', 'pedagogy', 'curriculum'],
                'design': ['design', 'creative', 'art', 'visual', 'ux', 'ui'],
                'science': ['science', 'research', 'analysis', 'laboratory', 'experiment']
            }
            
            identified_areas = []
            for area, keywords in subject_areas.items():
                if any(keyword in words for keyword in keywords):
                    identified_areas.append(area)
            
            # If no specific areas identified, use generic terms
            if not identified_areas:
                identified_areas = ['professional development', 'skill building']
            
            return identified_areas[:3]  # Return top 3 areas
            
        except Exception as e:
            print(f"❌ [CourseStructureAgent] Error extracting subject keywords: {e}")
            return ['professional development']
    
    async def _generate_ai_slide_deck(self, chapter_title: str, description: str, learning_objective: str, 
                                    pedagogy_strategy: str, assessment_idea: str, research_content: str, course_name: str) -> List[Dict[str, Any]]:
        """Generate sequential slide deck using AI with enhanced pedagogy-informed descriptions"""
        try:
            print(f"🤖 [CourseStructureAgent] Using AI to generate pedagogy-informed sequential slide deck for: {chapter_title}")
            
            # Determine audience level from learning objective and pedagogy strategy
            audience_level = self._determine_audience_level(learning_objective, pedagogy_strategy)
            
            # Get pedagogy-specific guidance
            pedagogy_guidance = self._get_pedagogy_specific_guidance(pedagogy_strategy)
            
            # Create the enhanced master prompt for AI with pedagogy integration
            system_prompt = f"""You are an expert instructional designer creating a PEDAGOGY-INFORMED sequential slide deck outline for ONE SPECIFIC CHAPTER.

🎯 CRITICAL CHAPTER SCOPE CONSTRAINT:
- You are generating content ONLY for: "{chapter_title}"
- Do NOT reference other chapters, modules, or course sections
- Keep all content strictly within this chapter's boundaries
- Do NOT create comprehensive overviews that span multiple topics

CHAPTER INFORMATION:
- Title: {chapter_title}
- Description: {description}
- Learning Objective: {learning_objective}
- Pedagogy Strategy: {pedagogy_strategy}
- Assessment Idea: {assessment_idea}
- Audience Level: {audience_level}

PEDAGOGY-SPECIFIC GUIDANCE:
{pedagogy_guidance}

RESEARCH CONTEXT:
{research_content[:500]}...

TASK: Generate a PEDAGOGY-INFORMED sequential slide deck outline for THIS CHAPTER ONLY following these rules:

### STRICT CONTENT LIMITS:
- Generate EXACTLY 3-4 content slides (NO MORE)
- Generate EXACTLY 1-2 assessment slides (NO MORE)
- Total materials should be 4-6 items maximum
- Focus on the CORE concepts of this specific chapter only

### ENHANCED RULES for Content Slides with PEDAGOGY INTEGRATION:
- Create 3-4 focused slides that cover ONLY this chapter's content
- Each slide must be specific to "{chapter_title}" - no generic content
- Slide titles must be contextual and specific (NOT generic like "Overview" or "Introduction")
- **DETAILED PEDAGOGY-INFORMED DESCRIPTIONS**: Each description must be 4-6 sentences that include:
  * **Content Overview**: What learners will see and learn on this slide
  * **Pedagogical Approach**: HOW the content should be presented based on "{pedagogy_strategy}"
  * **Teaching Methods**: Specific techniques to use (examples, interactions, demonstrations, etc.)
  * **Learning Activities**: Suggested activities that align with the pedagogy strategy
  * **Research Integration**: Include relevant examples from research context when applicable
- Stay strictly within the chapter's learning objective scope

### Rules for Assessment Slides (MANDATORY):
- Generate 1-2 assessment slides that test ONLY this chapter's content
- Assessments must directly relate to "{chapter_title}" concepts
- Format: Quick MCQ or True/False only
- Each assessment must include clear question and options
- Assessment descriptions should include pedagogy-aligned evaluation methods

### FORBIDDEN CONTENT:
- Do NOT create slides about other chapters or modules
- Do NOT create comprehensive course overviews
- Do NOT reference concepts from other parts of the course
- Do NOT create generic introductory content

OUTPUT FORMAT (JSON only):
{{
  "materials": [
    {{
      "type": "slide",
      "title": "Specific title about {chapter_title}",
      "description": "DETAILED 4-6 sentence pedagogy-informed description that includes: content overview, pedagogical approach based on '{pedagogy_strategy}', specific teaching methods, suggested learning activities, and research examples when relevant."
    }},
    {{
      "type": "assessment", 
      "title": "Assessment about {chapter_title}",
      "description": "Question: [Clear question about {chapter_title}] Options: A) Option 1 B) Option 2 C) Option 3 D) Option 4. Format: Multiple choice. Evaluation approach: [pedagogy-aligned assessment method]."
    }}
  ]
}}

REMEMBER: 
- Maximum 4-6 total materials
- Focus ONLY on "{chapter_title}"
- Create DETAILED pedagogy-informed descriptions (4-6 sentences each)
- Integrate "{pedagogy_strategy}" throughout all descriptions
- No cross-chapter references"""

            user_prompt = f"Generate sequential slide deck outline for chapter: {chapter_title}. MUST include assessments. Return JSON only."

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await self.openai.create_chat_completion(
                model=self.model,
                messages=messages
            )
            
            response_content = response.choices[0].message.content.strip()
            
            # Extract JSON
            if "```" in response_content:
                json_start = response_content.find("```json")
                if json_start == -1:
                    json_start = response_content.find("```")
                json_start = response_content.find("{", json_start)
                json_end = response_content.rfind("}")
                if json_start != -1 and json_end != -1:
                    json_content = response_content[json_start:json_end + 1]
                else:
                    json_content = response_content
            else:
                # Find JSON object
                json_start = response_content.find("{")
                json_end = response_content.rfind("}")
                if json_start != -1 and json_end != -1:
                    json_content = response_content[json_start:json_end + 1]
                else:
                    json_content = response_content
            
            try:
                parsed_result = json.loads(json_content)
                materials = parsed_result.get("materials", [])
                
                if materials:
                    # Validate that assessments are included
                    materials = self._ensure_assessments_included(materials, chapter_title)
                    print(f"✅ [CourseStructureAgent] AI generated {len(materials)} sequential slide deck materials with assessments")
                    return materials
                else:
                    print(f"⚠️ [CourseStructureAgent] AI returned empty materials, using fallback")
                    return self._generate_fallback_materials({"title": chapter_title})
                    
            except json.JSONDecodeError as e:
                print(f"❌ [CourseStructureAgent] JSON parsing failed: {e}")
                return self._generate_fallback_materials({"title": chapter_title})
                
        except Exception as e:
            print(f"❌ [CourseStructureAgent] AI slide deck generation error: {e}")
            return self._generate_fallback_materials({"title": chapter_title})
    
    def _determine_audience_level(self, learning_objective: str, pedagogy_strategy: str) -> str:
        """Determine audience level from learning objective and pedagogy strategy"""
        text = f"{learning_objective} {pedagogy_strategy}".lower()
        
        # Check for advanced indicators
        advanced_keywords = ['advanced', 'expert', 'complex', 'sophisticated', 'analyze', 'evaluate', 'synthesize', 'create']
        if any(keyword in text for keyword in advanced_keywords):
            return "Expert"
        
        # Check for intermediate indicators
        intermediate_keywords = ['apply', 'implement', 'demonstrate', 'compare', 'contrast', 'intermediate']
        if any(keyword in text for keyword in intermediate_keywords):
            return "Intermediate"
        
        # Default to beginner
        return "Beginner"
    
    def _get_pedagogy_specific_guidance(self, pedagogy_strategy: str) -> str:
        """Generate detailed pedagogy-specific guidance for slide descriptions"""
        try:
            strategy_lower = pedagogy_strategy.lower()
            
            # Interactive Learning Strategy
            if any(keyword in strategy_lower for keyword in ['interactive', 'engagement', 'participation', 'discussion']):
                return """
INTERACTIVE LEARNING PEDAGOGY GUIDANCE:
- **Content Presentation**: Use engaging, conversational tone with frequent learner interaction points
- **Teaching Methods**: Include polls, Q&A sessions, breakout discussions, and real-time feedback
- **Learning Activities**: Design activities that require active participation (think-pair-share, live polls, interactive demos)
- **Slide Structure**: Break content into digestible chunks with interaction opportunities every 2-3 minutes
- **Assessment Approach**: Use formative assessments with immediate feedback and peer discussion
- **Engagement Techniques**: Include rhetorical questions, scenario-based discussions, and collaborative problem-solving
"""
            
            # Case Study Approach
            elif any(keyword in strategy_lower for keyword in ['case study', 'case-based', 'scenario', 'real-world']):
                return """
CASE STUDY PEDAGOGY GUIDANCE:
- **Content Presentation**: Structure content around real-world scenarios and authentic business cases
- **Teaching Methods**: Use problem-based learning with detailed case analysis and group discussions
- **Learning Activities**: Include case study analysis, role-playing, and decision-making simulations
- **Slide Structure**: Present cases progressively - context, challenge, analysis, solution, lessons learned
- **Assessment Approach**: Use scenario-based questions that test application of concepts to new situations
- **Research Integration**: Include actual company examples, industry data, and documented outcomes
"""
            
            # Hands-on/Practical Learning
            elif any(keyword in strategy_lower for keyword in ['hands-on', 'practical', 'experiential', 'learning by doing']):
                return """
HANDS-ON LEARNING PEDAGOGY GUIDANCE:
- **Content Presentation**: Focus on step-by-step processes and practical demonstrations
- **Teaching Methods**: Use guided practice, simulations, and immediate application exercises
- **Learning Activities**: Include skill-building exercises, practice sessions, and real-world applications
- **Slide Structure**: Show-do-practice format with clear action steps and practice opportunities
- **Assessment Approach**: Use performance-based assessments and practical skill demonstrations
- **Engagement Techniques**: Include interactive tools, simulations, and immediate feedback on practice attempts
"""
            
            # Lecture-based/Traditional
            elif any(keyword in strategy_lower for keyword in ['lecture', 'presentation', 'instructional', 'didactic']):
                return """
LECTURE-BASED PEDAGOGY GUIDANCE:
- **Content Presentation**: Use clear, structured explanations with logical flow and strong visual support
- **Teaching Methods**: Employ storytelling, analogies, and systematic knowledge building
- **Learning Activities**: Include note-taking guides, concept mapping, and structured reflection
- **Slide Structure**: Follow clear hierarchy - overview, main points, examples, summary
- **Assessment Approach**: Use knowledge-based questions that test understanding and recall
- **Visual Support**: Include diagrams, charts, and visual aids to support verbal explanations
"""
            
            # Collaborative Learning
            elif any(keyword in strategy_lower for keyword in ['collaborative', 'team', 'group', 'peer']):
                return """
COLLABORATIVE LEARNING PEDAGOGY GUIDANCE:
- **Content Presentation**: Design content that facilitates group work and peer learning
- **Teaching Methods**: Use team-based activities, peer teaching, and collaborative problem-solving
- **Learning Activities**: Include group projects, peer reviews, and collaborative discussions
- **Slide Structure**: Provide frameworks for group work with clear roles and expectations
- **Assessment Approach**: Use peer assessments and group-based evaluation methods
- **Social Learning**: Encourage knowledge sharing, peer feedback, and collective knowledge building
"""
            
            # Problem-based Learning
            elif any(keyword in strategy_lower for keyword in ['problem-based', 'inquiry', 'discovery', 'constructivist']):
                return """
PROBLEM-BASED LEARNING PEDAGOGY GUIDANCE:
- **Content Presentation**: Present content through authentic problems and inquiry-based challenges
- **Teaching Methods**: Use guided discovery, Socratic questioning, and scaffolded problem-solving
- **Learning Activities**: Include research tasks, hypothesis formation, and solution development
- **Slide Structure**: Problem → Investigation → Analysis → Solution → Reflection
- **Assessment Approach**: Use open-ended problems that require critical thinking and justification
- **Inquiry Support**: Provide resources and guidance for independent investigation and discovery
"""
            
            # Blended/Mixed Methods
            elif any(keyword in strategy_lower for keyword in ['blended', 'mixed', 'varied', 'multi-modal']):
                return """
BLENDED LEARNING PEDAGOGY GUIDANCE:
- **Content Presentation**: Combine multiple teaching methods and vary presentation styles
- **Teaching Methods**: Mix lectures, discussions, hands-on activities, and digital interactions
- **Learning Activities**: Include diverse activities catering to different learning preferences
- **Slide Structure**: Vary slide formats - some text-heavy, some visual, some interactive
- **Assessment Approach**: Use multiple assessment types - quizzes, projects, discussions, presentations
- **Flexibility**: Adapt teaching methods based on content complexity and learner needs
"""
            
            # Default/Generic Strategy
            else:
                return f"""
GENERAL PEDAGOGY GUIDANCE FOR "{pedagogy_strategy}":
- **Content Presentation**: Adapt presentation style to match the specified pedagogy strategy
- **Teaching Methods**: Use methods that align with "{pedagogy_strategy}" principles
- **Learning Activities**: Design activities that support the chosen pedagogical approach
- **Slide Structure**: Organize content in a way that facilitates the intended teaching method
- **Assessment Approach**: Use evaluation methods that complement the pedagogy strategy
- **Strategy Integration**: Ensure all slide elements reflect and support "{pedagogy_strategy}"
"""
                
        except Exception as e:
            print(f"❌ [CourseStructureAgent] Error generating pedagogy guidance: {e}")
            return """
DEFAULT PEDAGOGY GUIDANCE:
- **Content Presentation**: Use clear, engaging explanations with relevant examples
- **Teaching Methods**: Employ active learning techniques and interactive elements
- **Learning Activities**: Include practice opportunities and knowledge application
- **Slide Structure**: Follow logical progression with clear learning objectives
- **Assessment Approach**: Use formative and summative assessments aligned with objectives
"""
    
    async def _generate_dynamic_chapter_materials(self, chapter_info: Dict[str, Any], research_content: str, course_name: str) -> List[Dict[str, Any]]:
        """Generate sequential slide deck materials using master prompt approach with AI"""
        try:
            print(f"🎯 [CourseStructureAgent] Generating sequential slide deck for: {chapter_info.get('title', 'Unknown Chapter')}")
            
            chapter_title = chapter_info.get('title', 'Chapter Content')
            description = chapter_info.get('description', '')
            learning_objective = chapter_info.get('learning_objective', '')
            pedagogy_strategy = chapter_info.get('pedagogy_strategy', '')
            assessment_idea = chapter_info.get('assessment_idea', '')
            
            # Use AI to generate sequential slide deck following master prompt approach
            materials = await self._generate_ai_slide_deck(
                chapter_title, description, learning_objective, 
                pedagogy_strategy, assessment_idea, research_content, course_name
            )
            
            # No material limits - generate content based on course design requirements
            print(f"✅ [CourseStructureAgent] Generated {len(materials)} sequential slide deck materials")
            return materials
                
        except Exception as e:
            print(f"❌ [CourseStructureAgent] Error generating slide deck materials: {e}")
            # Fallback to basic materials
            return self._generate_fallback_materials(chapter_info)
    
    def _generate_contextual_slide_titles(self, chapter_title: str, description: str, learning_objective: str, slide_count: int) -> List[str]:
        """Generate contextual slide titles based on chapter content"""
        titles = []
        
        # Extract key concepts from chapter title and description
        key_concepts = self._extract_key_concepts(chapter_title, description)
        
        if slide_count == 3:
            titles = [
                f"Understanding {key_concepts[0] if key_concepts else chapter_title}",
                f"Key Principles of {chapter_title}",
                f"Applying {chapter_title} in Practice"
            ]
        elif slide_count == 4:
            titles = [
                f"Introduction to {chapter_title}",
                f"Core Concepts: {key_concepts[0] if key_concepts else 'Fundamentals'}",
                f"Implementation Strategies for {chapter_title}",
                f"Best Practices and Real-World Applications"
            ]
        elif slide_count == 5:
            titles = [
                f"Foundations of {chapter_title}",
                f"Key Components: {key_concepts[0] if key_concepts else 'Essential Elements'}",
                f"Advanced Techniques in {chapter_title}",
                f"Case Studies and Examples",
                f"Integration and Next Steps"
            ]
        
        return titles
    
    def _extract_key_concepts(self, chapter_title: str, description: str) -> List[str]:
        """Extract key concepts from chapter title and description"""
        # Simple keyword extraction - can be enhanced with NLP
        text = f"{chapter_title} {description}".lower()
        
        # Common management/business concepts
        concepts = []
        concept_keywords = {
            'leadership': ['leadership', 'leading', 'leader'],
            'communication': ['communication', 'communicating', 'feedback'],
            'strategy': ['strategy', 'strategic', 'planning'],
            'performance': ['performance', 'evaluation', 'assessment'],
            'team building': ['team', 'collaboration', 'teamwork'],
            'decision making': ['decision', 'decisions', 'choosing'],
            'problem solving': ['problem', 'solution', 'solving'],
            'project management': ['project', 'management', 'planning'],
            'change management': ['change', 'transition', 'transformation'],
            'conflict resolution': ['conflict', 'resolution', 'disputes']
        }
        
        for concept, keywords in concept_keywords.items():
            if any(keyword in text for keyword in keywords):
                concepts.append(concept.title())
        
        return concepts[:2]  # Return top 2 concepts
    
    def _generate_slide_description(self, slide_title: str, chapter_title: str, description: str, learning_objective: str, pedagogy_strategy: str, slide_number: int, total_slides: int) -> str:
        """Generate detailed slide description"""
        base_description = f"This slide covers {slide_title.lower()} as part of {chapter_title}. "
        
        if slide_number == 1:
            # Introduction slide
            base_description += f"It provides an overview of the key concepts and sets the foundation for understanding {chapter_title}. "
            base_description += f"Content should include definitions, importance, and relevance to the learning objective: {learning_objective[:100]}..."
        elif slide_number == total_slides - 1 and 'assessment' not in slide_title.lower():
            # Second to last slide (usually practical application)
            base_description += f"This slide focuses on practical applications and real-world examples of {chapter_title}. "
            base_description += f"Include case studies, scenarios, and actionable insights that students can apply immediately."
        elif slide_number == total_slides and 'assessment' not in slide_title.lower():
            # Last content slide
            base_description += f"This concluding slide summarizes key takeaways and provides next steps for {chapter_title}. "
            base_description += f"Include integration points with other concepts and resources for further learning."
        else:
            # Middle slides
            base_description += f"This slide delves into specific aspects of {chapter_title}, building on previous concepts. "
            base_description += f"Content should be detailed and include examples, frameworks, or methodologies relevant to the topic."
        
        # Add pedagogy strategy context
        if pedagogy_strategy:
            base_description += f" Teaching approach: {pedagogy_strategy[:100]}..."
        
        return base_description
    
    def _generate_assessment_title(self, chapter_title: str, learning_objective: str) -> str:
        """Generate contextual assessment title"""
        # Extract action words from learning objective
        action_words = ['evaluate', 'analyze', 'apply', 'understand', 'demonstrate', 'assess']
        
        for word in action_words:
            if word in learning_objective.lower():
                return f"{word.title()} Your Understanding of {chapter_title}"
        
        return f"{chapter_title} Knowledge Assessment"
    
    def _generate_assessment_description(self, chapter_title: str, learning_objective: str, pedagogy_strategy: str) -> str:
        """Generate detailed assessment description"""
        description = f"This assessment evaluates student understanding of {chapter_title} concepts. "
        
        # Determine assessment type based on pedagogy strategy
        if 'interactive' in pedagogy_strategy.lower() or 'hands-on' in pedagogy_strategy.lower():
            description += "Format: Interactive scenario-based questions with practical applications. "
        elif 'case study' in pedagogy_strategy.lower():
            description += "Format: Case study analysis with multiple-choice and short answer questions. "
        else:
            description += "Format: Mixed question types including multiple-choice, true/false, and short answer. "
        
        description += f"Assessment aligns with learning objective: {learning_objective[:150]}... "
        description += "Includes immediate feedback and explanations for incorrect answers to reinforce learning."
        
        return description
    
    def _ensure_assessments_included(self, materials: List[Dict[str, Any]], chapter_title: str) -> List[Dict[str, Any]]:
        """Ensure that every chapter has at least one assessment slide"""
        try:
            # Count content slides and assessments
            content_slides = [m for m in materials if m.get("type") == "slide"]
            assessments = [m for m in materials if m.get("type") == "assessment"]
            
            content_count = len(content_slides)
            assessment_count = len(assessments)
            
            # Determine required number of assessments based on master prompt rules
            if content_count <= 3:
                required_assessments = 1  # Short chapter
            elif content_count <= 5:
                required_assessments = 2  # Medium chapter
            else:
                required_assessments = 3  # Long chapter
            
            # If we don't have enough assessments, add them
            if assessment_count < required_assessments:
                missing_assessments = required_assessments - assessment_count
                print(f"⚠️ [CourseStructureAgent] Chapter '{chapter_title}' missing {missing_assessments} assessments, adding them")
                
                for i in range(missing_assessments):
                    assessment_number = assessment_count + i + 1
                    new_assessment = {
                        "type": "assessment",
                        "title": f"{chapter_title} Knowledge Check {assessment_number}",
                        "description": f"Assessment {assessment_number} to evaluate understanding of {chapter_title} concepts. Format: Multiple choice with immediate feedback."
                    }
                    materials.append(new_assessment)
            
            # No material limits - generate content based on course design requirements
            return materials
            
        except Exception as e:
            print(f"❌ [CourseStructureAgent] Error ensuring assessments: {e}")
            return materials
    
    def _generate_fallback_materials(self, chapter_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate enhanced fallback materials with detailed pedagogy-informed descriptions"""
        chapter_title = chapter_info.get('title', 'Chapter Content')
        pedagogy_strategy = chapter_info.get('pedagogy_strategy', 'Interactive learning with examples and practice')
        learning_objective = chapter_info.get('learning_objective', f'Understand key concepts in {chapter_title}')
        
        # Get pedagogy-specific guidance for fallback materials
        pedagogy_guidance = self._get_pedagogy_specific_guidance(pedagogy_strategy)
        
        # Generate enhanced materials with detailed pedagogy-informed descriptions
        materials = [
            {
                "type": "slide",
                "title": f"Foundations of {chapter_title}",
                "description": f"This slide establishes the foundational understanding of {chapter_title} concepts and their significance in the broader context. Learners will explore key terminology, core principles, and the fundamental importance of mastering these concepts. The pedagogical approach follows {pedagogy_strategy} by incorporating interactive elements, real-world connections, and engaging presentation techniques. Content includes clear definitions, contextual examples, and connections to learners' prior knowledge. The slide sets clear expectations for learning outcomes and provides a roadmap for the chapter journey, ensuring learners understand both what they will learn and why it matters for their professional development."
            },
            {
                "type": "slide", 
                "title": f"Core Principles and Frameworks in {chapter_title}",
                "description": f"This slide delves deep into the essential principles, methodologies, and frameworks that define {chapter_title}. Using the {pedagogy_strategy} approach, content is presented through structured analysis, practical examples, and systematic knowledge building. Learners will examine the underlying theories, explore proven frameworks, and understand how these principles interconnect to form a comprehensive understanding. The slide incorporates research-based examples, industry best practices, and comparative analysis to help learners grasp complex concepts. Interactive elements and guided discovery techniques ensure active engagement while building upon the foundational knowledge from the previous slide."
            },
            {
                "type": "slide",
                "title": f"Real-World Applications and Case Studies in {chapter_title}",
                "description": f"This slide bridges theory with practice by demonstrating how {chapter_title} concepts are applied in real-world professional scenarios. Following {pedagogy_strategy} methodology, learners engage with authentic case studies, industry examples, and practical implementation strategies. Content includes detailed analysis of successful applications, common challenges and solutions, and step-by-step implementation guidance. The slide encourages critical thinking through scenario-based learning, problem-solving exercises, and reflective analysis. Learners will connect theoretical knowledge to practical skills, understand the impact of proper implementation, and develop confidence in applying these concepts in their own professional contexts."
            },
            {
                "type": "assessment",
                "title": f"{chapter_title} Conceptual Understanding Check",
                "description": f"This comprehensive assessment evaluates learners' grasp of fundamental {chapter_title} concepts, principles, and their interconnections. Aligned with the learning objective '{learning_objective}' and designed using {pedagogy_strategy} assessment principles, the evaluation includes multiple-choice questions that test conceptual understanding, definitional knowledge, and principle application. Questions are scaffolded from basic recall to analytical thinking, incorporating real-world scenarios that require learners to demonstrate their understanding. Immediate feedback is provided for each response, including detailed explanations for correct answers and guidance for addressing misconceptions, ensuring the assessment serves as a learning tool rather than just evaluation."
            },
            {
                "type": "assessment",
                "title": f"{chapter_title} Application and Analysis Assessment",
                "description": f"This advanced assessment challenges learners to apply {chapter_title} concepts to complex, realistic scenarios that mirror professional challenges. Using {pedagogy_strategy} evaluation methods, the assessment presents multi-layered problems requiring analysis, synthesis, and practical application of learned principles. Questions include case study analysis, decision-making scenarios, and problem-solving challenges that test higher-order thinking skills. The assessment format encourages critical thinking, justification of choices, and demonstration of practical competency. Comprehensive feedback includes not only correct answers but also alternative approaches, common pitfalls to avoid, and connections to real-world applications, reinforcing learning while building confidence in practical application."
            }
        ]
        
        print(f"✅ [CourseStructureAgent] Generated enhanced fallback materials with pedagogy-informed descriptions for: {chapter_title}")
        return materials
    
    async def _openai_parse_constrained(self, course_design_content: str, course_name: str) -> Dict[str, Any]:
        """Fallback OpenAI parsing with strict constraints"""
        try:
            print(f"🤖 [CourseStructureAgent] Using constrained OpenAI parsing")
            
            system_prompt = f"""You are a dynamic course structure parser. Extract EXACTLY what's in the course design with NO limits on modules, chapters, or materials.

CHAPTER-SCOPED CONTENT GENERATION:
- Generate content ONLY for the specific chapter being processed
- Do NOT mix content from different chapters or modules
- Each chapter should be self-contained and focused
- NO LIMITS on number of modules, chapters, or materials - follow course design exactly
- Extract ALL modules and chapters from course-design.md
- Generate dynamic, contextual slide titles (NOT generic like "Overview")
- If Final Project exists, add it as a chapter to the LAST module

OUTPUT FORMAT (JSON only):
{{
  "success": true,
  "structure": {{
    "course_title": "title",
    "modules": [
      {{
        "module_number": 1,
        "title": "EXACT module title from design",
        "chapters": [
          {{
            "chapter_number": 1,
            "title": "EXACT chapter title from design",
            "materials": [
              {{"type": "slide", "title": "specific contextual title"}},
              {{"type": "assessment", "title": "specific assessment title"}}
            ]
          }}
        ]
      }}
    ]
  }}
}}"""

            user_prompt = f"COURSE: {course_name}\n\nCOURSE DESIGN:\n{course_design_content}\n\nExtract structure with constraints. Return JSON only."

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await self.openai.create_chat_completion(
                model=self.model,
                messages=messages
            )
            
            response_content = response.choices[0].message.content.strip()
            
            # Extract JSON
            if "```" in response_content:
                json_start = response_content.find("```json")
                if json_start == -1:
                    json_start = response_content.find("```")
                json_start = response_content.find("{", json_start)
                json_end = response_content.rfind("}")
                if json_start != -1 and json_end != -1:
                    json_content = response_content[json_start:json_end + 1]
                else:
                    json_content = response_content
            else:
                # Find JSON object
                json_start = response_content.find("{")
                json_end = response_content.rfind("}")
                if json_start != -1 and json_end != -1:
                    json_content = response_content[json_start:json_end + 1]
                else:
                    json_content = response_content
            
            try:
                parsed_result = json.loads(json_content)
                if parsed_result.get("success") and "structure" in parsed_result:
                    print(f"✅ [CourseStructureAgent] OpenAI constrained parsing successful")
                    return parsed_result
                else:
                    return {"success": False, "error": "Invalid OpenAI response format"}
                    
            except json.JSONDecodeError as e:
                print(f"❌ [CourseStructureAgent] JSON parsing failed: {e}")
                return {"success": False, "error": f"Failed to parse OpenAI response: {str(e)}"}
                
        except Exception as e:
            print(f"❌ [CourseStructureAgent] OpenAI parsing error: {e}")
            return {"success": False, "error": f"OpenAI parsing failed: {str(e)}"}
    
    def _validate_structure_constraints(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Validate structure - no material limits, focus on chapter-scoped content"""
        try:
            modules = structure.get("modules", [])
            total_materials = 0
            
            for module in modules:
                chapters = module.get("chapters", [])
                
                for chapter in chapters:
                    materials = chapter.get("materials", [])
                    total_materials += len(materials)
            
            # No material limits - generate content based on course design requirements
            print(f"✅ [CourseStructureAgent] Structure validation passed: {total_materials} total materials (no limits)")
            return {"valid": True, "total_materials": total_materials}
            
        except Exception as e:
            return {"valid": False, "error": f"Validation error: {str(e)}"}
    
    async def _save_chapter_materials_immediately(self, course_id: str, module_number: int, chapter_number: int, materials: List[Dict[str, Any]], streaming_callback=None):
        """Save materials for a single chapter immediately to database with chapter-scoped numbering and real-time streaming events"""
        try:
            if not materials:
                return
            
            # Check if materials for this chapter already exist to prevent duplicates
            db = await self.db.get_database()
            existing_materials = await db.content_materials.find_one({
                "course_id": ObjectId(course_id),
                "module_number": module_number,
                "chapter_number": chapter_number
            })
            
            if existing_materials:
                print(f"⚠️ [CourseStructureAgent] Materials for Chapter {module_number}.{chapter_number} already exist, skipping to prevent duplicates")
                return
            
            # Use chapter-scoped counters (restart numbering for each chapter)
            chapter_slide_counter = 1
            chapter_assessment_counter = 1
            
            # Emit folder creation events first
            module_path = f"/content/module-{module_number}"
            chapter_path = f"{module_path}/chapter-{module_number}.{chapter_number}"
            
            if streaming_callback:
                # Emit content folder creation event
                streaming_callback({
                    "type": "folder_created",
                    "file_path": "/content",
                    "folder_name": "content",
                    "status": "created"
                })
                
                # Emit module folder creation event
                streaming_callback({
                    "type": "folder_created", 
                    "file_path": module_path,
                    "folder_name": f"Module {module_number}",
                    "module_number": module_number,
                    "status": "created"
                })
                
                # Emit chapter folder creation event
                streaming_callback({
                    "type": "folder_created",
                    "file_path": chapter_path,
                    "folder_name": f"Chapter {module_number}.{chapter_number}",
                    "module_number": module_number,
                    "chapter_number": chapter_number,
                    "status": "created"
                })
            
            chapter_materials = []
            for material in materials:
                # Determine slide number for sequencing using chapter-scoped counters
                slide_number = None
                if material["type"] == "slide":
                    slide_number = chapter_slide_counter
                    chapter_slide_counter += 1
                elif material["type"] == "assessment":
                    slide_number = chapter_assessment_counter
                    chapter_assessment_counter += 1
                
                material_doc = ContentMaterial(
                    course_id=ObjectId(course_id),
                    module_number=module_number,
                    chapter_number=chapter_number,
                    material_type=material["type"],
                    title=material["title"],
                    description=material.get("description", f"Generated content for {material['title']}"),
                    status="pending",
                    content_status="not done",  # Set content status for next agent
                    slide_number=slide_number
                )
                chapter_materials.append(material_doc.dict(by_alias=True))
                
                # Emit material creation event for real-time file appearance
                if streaming_callback:
                    # Create display name with chapter-scoped number for slides and assessments
                    display_name = material["title"]
                    if slide_number is not None:
                        if material["type"] == "slide":
                            display_name = f"Slide {slide_number}: {material['title']}"
                        elif material["type"] == "assessment":
                            display_name = f"Assessment {slide_number}: {material['title']}"
                    
                    # Sanitize filename
                    filename = self._sanitize_filename(display_name)
                    file_path = f"{chapter_path}/{filename}.md"
                    
                    streaming_callback({
                        "type": "material_created",
                        "file_path": file_path,
                        "material_type": material["type"],
                        "title": display_name,
                        "status": "saved",
                        "module_number": module_number,
                        "chapter_number": chapter_number,
                        "slide_number": slide_number,
                        "description": material.get("description", "")
                    })
            
            # Insert chapter materials immediately
            if chapter_materials:
                try:
                    # Try batch insert for the chapter
                    db = await self.db.get_database()
                    result = await db.content_materials.insert_many(chapter_materials)
                    print(f"✅ [CourseStructureAgent] Immediately saved {len(result.inserted_ids)} materials for Chapter {module_number}.{chapter_number} (chapter-scoped numbering)")
                except Exception as batch_error:
                    print(f"⚠️ [CourseStructureAgent] Chapter batch insert failed, falling back to individual inserts: {batch_error}")
                    # Fallback to individual inserts
                    for material in chapter_materials:
                        await self.db.insert_document("content_materials", material)
                    print(f"✅ [CourseStructureAgent] Individually saved {len(chapter_materials)} materials for Chapter {module_number}.{chapter_number} (chapter-scoped numbering)")
                    
        except Exception as e:
            print(f"❌ [CourseStructureAgent] Error saving chapter materials immediately: {e}")
    
    def _sanitize_filename(self, title: str) -> str:
        """Sanitize file names for safe file system usage"""
        if not title:
            return 'untitled'
        
        # Convert to lowercase and remove special characters
        sanitized = re.sub(r'[^a-z0-9\s-]', '', title.lower())
        # Replace multiple spaces with single hyphens
        sanitized = re.sub(r'\s+', '-', sanitized)
        # Replace multiple hyphens with single hyphen
        sanitized = re.sub(r'-+', '-', sanitized)
        # Remove leading/trailing hyphens
        sanitized = sanitized.strip('-')
        # Limit length
        return sanitized[:50] if sanitized else 'untitled'

    async def _create_content_materials_constrained(self, course_id: str, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Create ContentMaterial records with constraints - now used as fallback when incremental saving wasn't used"""
        try:
            print(f"📝 [CourseStructureAgent] Creating constrained content materials (fallback method)")
            
            # Check if materials were already saved incrementally
            existing_count = await self.db.count_documents("content_materials", {"course_id": ObjectId(course_id)})
            if existing_count > 0:
                print(f"✅ [CourseStructureAgent] Found {existing_count} materials already saved incrementally")
                return {
                    "success": True,
                    "total_materials": existing_count,
                    "material_ids": []  # IDs not needed since materials already exist
                }
            
            # If no materials exist, fall back to batch creation
            print(f"⚠️ [CourseStructureAgent] No incremental materials found, falling back to batch creation")
            
            materials = []
            total_materials = 0
            
            for module in structure.get("modules", []):
                module_number = module["module_number"]
                
                for chapter in module.get("chapters", []):
                    chapter_number = chapter["chapter_number"]
                    
                    # Use chapter-scoped counters (restart numbering for each chapter)
                    chapter_slide_counter = 1
                    chapter_assessment_counter = 1
                    
                    for material in chapter.get("materials", []):
                        # No material limits - generate content based on course design requirements
                        
                        # Determine slide number for sequencing using chapter-scoped counters
                        slide_number = None
                        if material["type"] == "slide":
                            slide_number = chapter_slide_counter
                            chapter_slide_counter += 1
                        elif material["type"] == "assessment":
                            slide_number = chapter_assessment_counter
                            chapter_assessment_counter += 1
                        
                        material_doc = ContentMaterial(
                            course_id=ObjectId(course_id),
                            module_number=module_number,
                            chapter_number=chapter_number,
                            material_type=material["type"],
                            title=material["title"],
                            description=material.get("description", f"Generated content for {material['title']}"),
                            status="pending",
                            content_status="not done",  # Set content status for next agent
                            slide_number=slide_number
                        )
                        materials.append(material_doc.dict(by_alias=True))
                        total_materials += 1
            
            # Insert materials in batch for better performance
            if materials:
                # Use batch insert if available, otherwise insert individually
                try:
                    # Try batch insert first
                    db = await self.db.get_database()
                    result = await db.content_materials.insert_many(materials)
                    material_ids = [str(id) for id in result.inserted_ids]
                    print(f"✅ [CourseStructureAgent] Batch created {len(material_ids)} constrained materials")
                except Exception as batch_error:
                    print(f"⚠️ [CourseStructureAgent] Batch insert failed, falling back to individual inserts: {batch_error}")
                    # Fallback to individual inserts
                    material_ids = []
                    for material in materials:
                        material_id = await self.db.insert_document("content_materials", material)
                        material_ids.append(material_id)
                    print(f"✅ [CourseStructureAgent] Individual created {len(material_ids)} constrained materials")
                
                return {
                    "success": True,
                    "total_materials": len(material_ids),
                    "material_ids": material_ids
                }
            else:
                return {"success": True, "total_materials": 0, "material_ids": []}
                
        except Exception as e:
            print(f"❌ [CourseStructureAgent] Error creating materials: {e}")
            return {"success": False, "error": f"Failed to create materials: {str(e)}"}
    
    async def _update_course_structure_metadata(self, course_id: str, structure: Dict[str, Any], total_materials: int) -> None:
        """Update course record with structure metadata (replaces CourseStructureChecklist)"""
        try:
            update_data = {
                "content_structure": structure,
                "total_content_items": total_materials,
                "completed_content_items": 0,
                "structure_generated_at": datetime.utcnow(),
                "structure_approved": False,
                "updated_at": datetime.utcnow()
            }
            
            await self.db.update_document("courses", course_id, update_data)
            print(f"✅ [CourseStructureAgent] Updated course metadata")
            
        except Exception as e:
            print(f"❌ [CourseStructureAgent] Error updating course metadata: {e}")
    
    async def _approve_structure(self, course_id: str, approved: bool) -> Dict[str, Any]:
        """Approve or reject the generated structure"""
        try:
            update_data = {
                "structure_approved": approved,
                "updated_at": datetime.utcnow()
            }
            
            if approved:
                update_data["structure_approved_at"] = datetime.utcnow()
            
            success = await self.db.update_document("courses", course_id, update_data)
            
            if success:
                return {"success": True, "approved": approved}
            else:
                return {"success": False, "error": "Failed to update approval status"}
                
        except Exception as e:
            print(f"❌ [CourseStructureAgent] Error updating approval: {e}")
            return {"success": False, "error": f"Failed to update approval: {str(e)}"}
    
    async def stream_structure_generation(self, course_id: str, preferences: Dict[str, Any] = None, user_id: Optional[str] = None):
        """Stream constrained structure generation in real-time with proper async streaming"""
        print(f"\n🎯 [CourseStructureAgent] Starting constrained structure generation")
        print(f"   📋 Course ID: {course_id}")
        print(f"   👤 User ID: {user_id}")
        
        try:
            # Send start signal
            yield {"type": "start", "content": "🎯 Analyzing course content with constrained AI to generate structure..."}
            
            # Generate structure with constraints
            print(f"🤖 [CourseStructureAgent] Using constrained parsing...")
            yield {"type": "progress", "content": "🤖 Using AI to analyze course design with strict constraints..."}
            
            # Create an async queue for real-time streaming events
            import asyncio
            streaming_queue = asyncio.Queue()
            
            # Create async streaming callback that puts events in queue
            def streaming_callback(event_data):
                """Callback to queue streaming events during material creation"""
                print(f"📡 [CourseStructureAgent] Queuing streaming event: {event_data.get('type', 'unknown')} - {event_data.get('file_path', 'no path')}")
                # Put event in queue for async processing
                try:
                    streaming_queue.put_nowait(event_data)
                except asyncio.QueueFull:
                    print(f"⚠️ [CourseStructureAgent] Streaming queue full, dropping event")
                return event_data
            
            # Start structure generation in background task
            print(f"🚀 [CourseStructureAgent] Starting generation task...")
            generation_task = asyncio.create_task(
                self._generate_content_structure(course_id, streaming_callback)
            )
            
            # Process streaming events in real-time while generation happens
            structure_result = None
            event_count = 0
            
            while True:
                try:
                    # Check if generation is complete first
                    if generation_task.done():
                        print(f"✅ [CourseStructureAgent] Generation task completed")
                        structure_result = await generation_task
                        
                        # Process any remaining events in queue
                        remaining_events = 0
                        while not streaming_queue.empty():
                            try:
                                event = streaming_queue.get_nowait()
                                yield event
                                remaining_events += 1
                            except asyncio.QueueEmpty:
                                break
                        
                        if remaining_events > 0:
                            print(f"📤 [CourseStructureAgent] Processed {remaining_events} remaining events")
                        break
                    
                    # Try to get an event from the queue with a short timeout
                    try:
                        event = await asyncio.wait_for(streaming_queue.get(), timeout=0.5)
                        event_count += 1
                        print(f"📤 [CourseStructureAgent] Yielding event #{event_count}: {event.get('type', 'unknown')}")
                        yield event
                    except asyncio.TimeoutError:
                        # No events available, continue checking if generation is done
                        print(f"⏳ [CourseStructureAgent] No events in queue, checking generation status...")
                        continue
                        
                except Exception as loop_error:
                    print(f"❌ [CourseStructureAgent] Error in streaming loop: {loop_error}")
                    # Don't break the loop for minor errors, just continue
                    continue
            
            if not structure_result or not structure_result.get("success"):
                error_msg = f"Failed to generate constrained structure: {structure_result.get('error', 'Unknown error') if structure_result else 'Generation task failed'}"
                print(f"❌ [CourseStructureAgent] {error_msg}")
                yield {"type": "error", "content": error_msg}
                return
            
            print(f"✅ [CourseStructureAgent] Generated constrained structure with {structure_result['total_materials']} materials across {structure_result['total_modules']} modules")
            yield {"type": "progress", "content": f"✅ Generated {structure_result['total_materials']} constrained content items across {structure_result['total_modules']} modules"}
            
            # Generate structure summary
            structure_summary = self._generate_structure_summary(structure_result["structure"], structure_result["total_materials"])
            
            # Store completion message
            if user_id:
                completion_message = f"✅ Constrained content structure generated! Created {structure_result['total_materials']} items across {structure_result['total_modules']} modules with enforced limits."
                await self.messages.store_message(course_id, user_id, completion_message, "assistant")
            
            # Send completion with structure data
            yield {
                "type": "complete",
                "content": f"✅ Constrained content structure generated successfully!",
                "structure_data": {
                    "course_title": structure_result["structure"].get("course_title", "Course"),
                    "total_modules": structure_result["total_modules"],
                    "total_items": structure_result["total_materials"],
                    "structure_summary": structure_summary,
                    "breakdown": self._calculate_breakdown(structure_result["structure"]),
                    "constraints_applied": True,
                    "subject_specific": True
                }
            }
            
        except Exception as e:
            error_msg = f"Failed to generate constrained structure: {str(e)}"
            print(f"❌ [CourseStructureAgent] CRITICAL ERROR: {error_msg}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            yield {"type": "error", "content": error_msg}
    
    def _generate_structure_summary(self, structure: Dict[str, Any], total_materials: int) -> str:
        """Generate a human-readable summary of the constrained structure"""
        summary_lines = []
        summary_lines.append(f"# {structure.get('course_title', 'Constrained Course Content Structure')}")
        summary_lines.append("")
        summary_lines.append("## 🎯 Constrained Structure Generation")
        summary_lines.append(f"**Total Materials:** {total_materials} (within limits)")
        summary_lines.append(f"**Modules:** {len(structure.get('modules', []))}")
        summary_lines.append("")
        summary_lines.append("## 📊 Content Breakdown")
        
        breakdown = self._calculate_breakdown(structure)
        summary_lines.append(f"- **Slides:** {breakdown['slides']} (constrained)")
        summary_lines.append(f"- **Assessments:** {breakdown['assessments']} (constrained)")
        summary_lines.append(f"- **Quizzes:** {breakdown['quizzes']} (constrained)")
        summary_lines.append("")
        summary_lines.append("## 🎯 Module Structure (Constraint-Applied)")
        
        for module in structure.get("modules", []):
            summary_lines.append(f"### Module {module['module_number']}: {module['title']}")
            for chapter in module.get("chapters", []):
                materials_count = len(chapter.get("materials", []))
                summary_lines.append(f"- Chapter {module['module_number']}.{chapter['chapter_number']}: {chapter['title']} ({materials_count} items)")
        
        summary_lines.append("")
        summary_lines.append("*✨ This structure was generated with strict constraints to prevent excessive content generation and follows the course design specifications.*")
        
        return "\n".join(summary_lines)
    
    def _calculate_breakdown(self, structure: Dict[str, Any]) -> Dict[str, int]:
        """Calculate breakdown of material types"""
        breakdown = {"slides": 0, "assessments": 0, "quizzes": 0, "others": 0}
        
        for module in structure.get("modules", []):
            for chapter in module.get("chapters", []):
                for material in chapter.get("materials", []):
                    material_type = material.get("type", "other")
                    if material_type == "slide":
                        breakdown["slides"] += 1
                    elif material_type == "assessment":
                        breakdown["assessments"] += 1
                    elif material_type == "quiz":
                        breakdown["quizzes"] += 1
                    else:
                        breakdown["others"] += 1
        
        return breakdown
    
    def _is_valid_object_id(self, course_id: str) -> bool:
        """Validate if the provided string is a valid MongoDB ObjectId format"""
        try:
            # Check if it's a valid ObjectId format (24 character hex string)
            if len(course_id) != 24:
                return False
            
            # Try to create ObjectId to validate format
            ObjectId(course_id)
            return True
            
        except Exception:
            return False
    
    async def _start_content_creation(self, course_id: str) -> Dict[str, Any]:
        """Start the content creation process after structure approval"""
        try:
            print(f"🚀 [CourseStructureAgent] Starting content creation for course {course_id}")
            
            # First, mark the structure as approved if not already
            course = await self.db.find_course(course_id)
            if not course:
                return {"success": False, "error": "Course not found"}
            
            # Update course to mark structure as approved and start content creation
            update_data = {
                "structure_approved": True,
                "structure_approved_at": datetime.utcnow(),
                "workflow_step": "content_generation",
                "content_creation_started": True,
                "content_creation_started_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            success = await self.db.update_document("courses", course_id, update_data)
            
            if success:
                print(f"✅ [CourseStructureAgent] Content creation started for course {course_id}")
                
                # Get the first material that needs content generation
                first_material = await self._get_next_material_for_generation(course_id)
                
                if first_material:
                    print(f"🎯 [CourseStructureAgent] Found first material for generation: {first_material.get('title', 'Unknown')}")
                    return {
                        "success": True,
                        "workflow_step": "content_generation",
                        "message": "Content creation process has been initiated",
                        "next_agent": "material_content_generator",
                        "auto_trigger": True,
                        "streaming": True,  # Enable streaming for content generation
                        "course_id": course_id,
                        "material_id": str(first_material.get("_id")),
                        "material_title": first_material.get("title"),
                        "material_type": first_material.get("material_type"),
                        "workflow_transition": {
                            "automatic": True,
                            "next_agent": "material_content_generator",
                            "trigger_immediately": True
                        }
                    }
                else:
                    print(f"⚠️ [CourseStructureAgent] No materials found for content generation")
                    return {
                        "success": True,
                        "workflow_step": "content_generation",
                        "message": "Content creation ready, but no materials found to generate",
                        "course_id": course_id
                    }
            else:
                return {"success": False, "error": "Failed to update course for content creation"}
                
        except Exception as e:
            print(f"❌ [CourseStructureAgent] Error starting content creation: {e}")
            return {"success": False, "error": f"Failed to start content creation: {str(e)}"}
    
    async def _get_next_material_for_generation(self, course_id: str) -> Optional[Dict[str, Any]]:
        """Get the next material that needs content generation"""
        try:
            # Find the first material with content_status "not done"
            db = await self.db.get_database()
            material = await db.content_materials.find_one(
                {
                    "course_id": ObjectId(course_id),
                    "content_status": "not done"
                },
                sort=[("module_number", 1), ("chapter_number", 1), ("slide_number", 1)]
            )
            
            if material:
                print(f"🎯 [CourseStructureAgent] Next material for generation: {material.get('title', 'Unknown')} (Module {material.get('module_number')}, Chapter {material.get('chapter_number')})")
                return material
            else:
                print(f"⚠️ [CourseStructureAgent] No materials found with content_status 'not done'")
                return None
                
        except Exception as e:
            print(f"❌ [CourseStructureAgent] Error getting next material: {e}")
            return None
    
    async def _generate_response_with_context(self, base_response: Optional[str], function_results: Dict[str, Any]) -> str:
        """Generate contextual response based on function results"""
        if not function_results:
            return base_response or "I'm ready to help you create a constrained course structure. What would you like to work on?"
        
        # Handle structure generation
        if "structure_generated" in function_results:
            result = function_results["structure_generated"]
            if result.get("success"):
                if result.get("streaming"):
                    # For streaming responses, provide a different message
                    return f"🎯 **Content Structure Generation Started!**\n\nGenerating course structure in real-time:\n\n- 📁 Creating content folders and materials\n- 📝 Processing course design and research\n- 🎯 Building sequential slide deck structure\n\n*← Files will appear in the Course Files tree as they are generated*"
                else:
                    # For non-streaming responses, use the detailed summary
                    return f"✅ **Constrained Structure Generated Successfully!**\n\n📊 **Structure Summary:**\n- **Modules:** {result.get('total_modules', 'N/A')}\n- **Total Materials:** {result.get('total_materials', 'N/A')}\n- **Constraints Applied:** ✅ All limits enforced\n\n🎯 **Next Step:** Review the structure and approve it to proceed with content creation."
            else:
                return f"❌ **Structure Generation Failed:** {result.get('error', 'Unknown error')}"
        
        # Handle structure approval
        if "structure_approved" in function_results:
            result = function_results["structure_approved"]
            if result.get("success"):
                if result.get("approved"):
                    return "✅ **Structure Approved!** You can now proceed with content creation."
                else:
                    return "📝 **Structure Needs Revision** - Please provide feedback for improvements."
            else:
                return f"❌ **Approval Failed:** {result.get('error', 'Unknown error')}"
        
        # Handle content creation start
        if "content_creation_started" in function_results:
            result = function_results["content_creation_started"]
            if result.get("success"):
                return "🚀 **Content Creation Started!** The system is now generating course materials based on your approved structure."
            else:
                return f"❌ **Content Creation Failed to Start:** {result.get('error', 'Unknown error')}"
        
        return base_response or "Structure operation completed. What would you like to work on next?"
    
    async def update_checklist_approval(self, course_id: str, approved: bool, modifications: Optional[str] = None) -> Dict[str, Any]:
        """Update structure approval status (compatibility method for frontend)"""
        try:
            print(f"🔄 [CourseStructureAgent] Updating approval status for course {course_id}: {approved}")
            
            update_data = {
                "structure_approved": approved,
                "updated_at": datetime.utcnow()
            }
            
            if approved:
                update_data["structure_approved_at"] = datetime.utcnow()
                print(f"✅ [CourseStructureAgent] Structure approved for course {course_id}")
            else:
                print(f"❌ [CourseStructureAgent] Structure rejected for course {course_id}")
            
            if modifications:
                # Store modification notes in course metadata
                update_data["structure_modification_notes"] = modifications
                print(f"📝 [CourseStructureAgent] Added modification notes: {modifications}")
            
            success = await self.db.update_document("courses", course_id, update_data)
            
            if success:
                return {"success": True, "approved": approved}
            else:
                return {"success": False, "error": "Failed to update approval status"}
                
        except Exception as e:
            print(f"❌ [CourseStructureAgent] Error updating approval: {e}")
            return {"success": False, "error": f"Failed to update approval: {str(e)}"}
    
    async def get_course_structure_checklist(self, course_id: str) -> Optional[Dict[str, Any]]:
        """Get course structure data (compatibility method for frontend)"""
        try:
            print(f"🔍 [CourseStructureAgent] Getting structure data for course {course_id}")
            
            # Get course with structure metadata
            course = await self.db.find_course(course_id)
            if not course:
                return None
            
            # Convert course structure data to checklist format for frontend compatibility
            structure_data = {
                "_id": course_id,  # Use course_id as identifier
                "course_id": course_id,
                "structure": course.get("content_structure", {}),
                "total_items": course.get("total_content_items", 0),
                "completed_items": course.get("completed_content_items", 0),
                "status": "approved" if course.get("structure_approved", False) else "pending",
                "user_approved": course.get("structure_approved", False),
                "created_at": course.get("structure_generated_at", course.get("created_at")),
                "approved_at": course.get("structure_approved_at")
            }
            
            print(f"✅ [CourseStructureAgent] Retrieved structure data: {structure_data['total_items']} items, approved: {structure_data['user_approved']}")
            return structure_data
            
        except Exception as e:
            print(f"❌ [CourseStructureAgent] Error getting structure data: {e}")
            return None
