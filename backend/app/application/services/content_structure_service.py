import re
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from bson import ObjectId

from ...infrastructure.database.database_service import DatabaseService
from ...infrastructure.storage.r2_storage import R2StorageService
from ...models import CourseStructureChecklist, ContentMaterial


class ContentStructureService:
    """Service for parsing course design files and managing content structure"""
    
    def __init__(self, database_service: DatabaseService, r2_storage_service: R2StorageService, openai_service=None):
        self.db = database_service
        self.storage = r2_storage_service
        self.openai = openai_service
    
    async def parse_course_design(self, course_id: str) -> Dict[str, Any]:
        """Parse course design file and extract structure using LLM analysis"""
        try:
            print(f"🔍 [ContentStructureService] Parsing course design for course {course_id}")
            
            # Get course info
            course = await self.db.find_course(course_id)
            if not course:
                return {"success": False, "error": "Course not found"}
            
            # Get course design content from R2
            r2_key = course.get("course_design_r2_key")
            if not r2_key:
                return {"success": False, "error": "No course design found"}
            
            course_design_content = await self.storage.get_course_design_content(r2_key)
            if not course_design_content:
                return {"success": False, "error": "Could not retrieve course design content"}
            
            print(f"✅ [ContentStructureService] Retrieved course design ({len(course_design_content)} chars)")
            
            # Get research content if available
            research_content = ""
            research_r2_key = course.get("research_r2_key")
            if research_r2_key:
                try:
                    research_content = await self.storage.get_course_design_content(research_r2_key)
                    print(f"✅ [ContentStructureService] Retrieved research content ({len(research_content)} chars)")
                except Exception as e:
                    print(f"⚠️ [ContentStructureService] Could not retrieve research content: {e}")
            
            # Use LLM to intelligently parse and generate structure
            if self.openai:
                parsed_structure = await self._llm_parse_course_structure(course_design_content, research_content, course.get("name", ""))
            else:
                # Fallback to basic parsing if no OpenAI service
                parsed_structure = self._parse_markdown_structure(course_design_content)
            
            if not parsed_structure["success"]:
                return parsed_structure
            
            # Generate content checklist
            checklist = self._generate_content_checklist(parsed_structure["structure"])
            
            print(f"✅ [ContentStructureService] Generated checklist with {checklist['total_items']} items")
            
            return {
                "success": True,
                "structure": parsed_structure["structure"],
                "checklist": checklist,
                "course_title": parsed_structure.get("course_title", course.get("name")),
                "total_modules": len(parsed_structure["structure"].get("modules", [])),
                "total_items": checklist["total_items"]
            }
            
        except Exception as e:
            print(f"❌ [ContentStructureService] Error parsing course design: {e}")
            return {"success": False, "error": f"Failed to parse course design: {str(e)}"}
    
    def _parse_markdown_structure(self, content: str) -> Dict[str, Any]:
        """Parse markdown content and extract course structure"""
        try:
            print(f"📄 [ContentStructureService] Parsing markdown structure")
            
            lines = content.split('\n')
            structure = {
                "course_title": "",
                "level": "",
                "duration": "",
                "prerequisites": [],
                "tools_platforms": "",
                "modules": []
            }
            
            current_module = None
            current_chapter = None
            in_prerequisites = False
            in_final_project = False
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Extract course title
                if line.startswith('# ') and not structure["course_title"]:
                    structure["course_title"] = line[2:].strip().replace('📚 ', '')
                
                # Extract level, duration, prerequisites
                elif line.startswith('**Level:**'):
                    structure["level"] = line.replace('**Level:**', '').strip()
                elif line.startswith('**Duration:**'):
                    structure["duration"] = line.replace('**Duration:**', '').strip()
                elif line.startswith('**Prerequisites:**'):
                    in_prerequisites = True
                elif in_prerequisites and line.startswith('* '):
                    structure["prerequisites"].append(line[2:].strip())
                elif in_prerequisites and line.startswith('**Tools'):
                    in_prerequisites = False
                    structure["tools_platforms"] = line.replace('**Tools & Platforms:**', '').strip()
                
                # Extract modules
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
                        current_chapter = None
                
                # Extract chapters within modules
                elif line.startswith('| **Chapter ') and current_module:
                    # Parse chapter from table row
                    chapter_match = re.match(r'\| \*\*Chapter (\d+)\.(\d+): (.*?)\*\* \|', line)
                    if chapter_match:
                        module_num = int(chapter_match.group(1))
                        chapter_num = int(chapter_match.group(2))
                        chapter_title = chapter_match.group(3)
                        
                        # Get the details from the next cell (if available)
                        details = ""
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            if next_line.startswith('|') and not next_line.startswith('| **Chapter'):
                                # Extract details from the table cell
                                details = self._extract_chapter_details(next_line)
                        
                        current_chapter = {
                            "chapter_number": chapter_num,
                            "title": chapter_title,
                            "details": details,
                            "materials": self._generate_chapter_materials(module_num, chapter_num, chapter_title)
                        }
                        
                        current_module["chapters"].append(current_chapter)
                
                # Handle final project
                elif line.startswith('## **Final Project**'):
                    in_final_project = True
                    if current_module:
                        structure["modules"].append(current_module)
                        current_module = None
                    
                    # Add final project as a special module
                    final_project_module = {
                        "module_number": len(structure["modules"]) + 1,
                        "title": "Final Project",
                        "chapters": [{
                            "chapter_number": 1,
                            "title": "Final Project",
                            "details": "Comprehensive project integrating all course concepts",
                            "materials": [
                                {"type": "slide", "title": "Final Project Overview"},
                                {"type": "slide", "title": "Project Requirements"},
                                {"type": "slide", "title": "Project Rubric"},
                                {"type": "assessment", "title": "Final Project Submission"}
                            ]
                        }]
                    }
                    structure["modules"].append(final_project_module)
            
            # Add the last module if it exists
            if current_module:
                structure["modules"].append(current_module)
            
            print(f"✅ [ContentStructureService] Parsed {len(structure['modules'])} modules")
            
            return {"success": True, "structure": structure}
            
        except Exception as e:
            print(f"❌ [ContentStructureService] Error parsing markdown: {e}")
            return {"success": False, "error": f"Failed to parse markdown structure: {str(e)}"}
    
    def _extract_chapter_details(self, table_cell: str) -> str:
        """Extract chapter details from table cell"""
        # Remove table formatting and extract meaningful content
        details = table_cell.replace('|', '').strip()
        
        # Extract description if available
        if '**Description:**' in details:
            desc_start = details.find('**Description:**') + len('**Description:**')
            desc_end = details.find('<br><br>', desc_start)
            if desc_end == -1:
                desc_end = details.find('**Learning Objective:**', desc_start)
            if desc_end != -1:
                return details[desc_start:desc_end].strip()
        
        return details[:200] + "..." if len(details) > 200 else details
    
    async def _llm_parse_course_structure(self, course_design_content: str, research_content: str, course_name: str) -> Dict[str, Any]:
        """Use LLM to intelligently parse course structure using the master prompt approach"""
        try:
            print(f"🤖 [ContentStructureService] Using master prompt approach for high-quality structure generation")
            
            # Enhanced system prompt based on the master prompt approach
            system_prompt = """You are an AI Course Architect with expertise in creating professional, industry-standard course structures.

TASK:
Using the provided course-design.md and research.md files, generate a comprehensive skeleton tree structure for the course.

REQUIREMENTS:
- Generate a hierarchical structure that follows the modules and chapters defined in course-design.md
- Create 3-6 slides per chapter based on topic complexity and depth
- Include meaningful assessments aligned with pedagogy and enriched by research.md practices
- Integrate research-driven tools, trends, and methods into slide titles and assessments
- Use subject-specific terminology and frameworks, not generic patterns
- Ensure logical progression from basic to advanced concepts

SLIDE CREATION PRINCIPLES:
- Break down each chapter into logical learning units
- Use specific, domain-relevant titles that experts would recognize
- Reflect actual learning objectives and pedagogy
- Vary content density based on topic complexity (3-6 slides per chapter)

ASSESSMENT PRINCIPLES:
- Create practical, meaningful evaluations (not just "Quiz 1", "Quiz 2")
- Align with modern pedagogical practices from research.md
- Include diverse assessment types: simulations, projects, reflections, practical exercises
- Integrate modern tools and technologies where relevant

OUTPUT FORMAT: Return a JSON object with this structure:
{
  "success": true,
  "structure": {
    "course_title": "extracted title",
    "level": "extracted level",
    "duration": "extracted duration",
    "prerequisites": ["extracted prerequisites"],
    "tools_platforms": "extracted tools",
    "modules": [
      {
        "module_number": 1,
        "title": "Module title from course design",
        "learning_objectives": ["specific objectives"],
        "chapters": [
          {
            "chapter_number": 1,
            "title": "Chapter title from course design",
            "details": "Chapter learning objectives and outcomes",
            "estimated_duration": "based on content complexity",
            "materials": [
              {"type": "slide", "title": "Specific, domain-relevant slide title", "focus": "key learning focus"},
              {"type": "slide", "title": "Another specific slide title", "focus": "key learning focus"},
              {"type": "assessment", "title": "Meaningful assessment description", "type_detail": "specific assessment format"}
            ]
          }
        ]
      }
    ]
  },
  "tree_structure": "hierarchical tree format for display",
  "analysis_summary": {
    "content_complexity": "assessment of complexity",
    "pedagogical_approach": "teaching methodology used",
    "research_integration": "how research trends were integrated",
    "assessment_strategy": "assessment approach rationale"
  }
}

CONTENT TYPES (use based on learning needs):
- "slide": Core content presentation with specific, relevant titles
- "assessment": Practical evaluations (projects, simulations, reflections, exercises)
- "interactive": Hands-on activities and labs
- "resource": Supplementary materials and references
- "discussion": Collaborative learning activities

FORBIDDEN PATTERNS:
- Generic titles like "Introduction", "Overview", "Key Concepts", "Examples"
- Fixed content formulas that could apply to any course
- Template-based assessments without subject specificity
- One-size-fits-all content density

Focus on creating professional, industry-standard structures with subject-specific content that reflects actual expertise in the domain."""

            user_prompt = f"""COURSE NAME: {course_name}

COURSE DESIGN CONTENT:
{course_design_content}

RESEARCH CONTENT:
{research_content}

Please perform a comprehensive analysis of these materials and create a fully dynamic, intelligent content structure. Every aspect should be derived from the actual course content - no generic patterns or hardcoded formulas. The structure should perfectly match the course's specific requirements and learning objectives."""

            # Use OpenAI with enhanced parameters for better analysis
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await self.openai.create_chat_completion(
                model="gpt-5-nano-2025-08-07",
                messages=messages,
                max_completion_tokens=6000   # Increased for more detailed analysis
            )
            
            # Parse the JSON response with better error handling
            response_content = response.choices[0].message.content.strip()
            
            # Extract JSON from response (handle potential markdown formatting)
            if "```json" in response_content:
                json_start = response_content.find("```json") + 7
                json_end = response_content.find("```", json_start)
                json_content = response_content[json_start:json_end].strip()
            elif "```" in response_content:
                # Handle case where JSON is in code blocks without language specification
                json_start = response_content.find("```") + 3
                json_end = response_content.find("```", json_start)
                json_content = response_content[json_start:json_end].strip()
            else:
                json_content = response_content
            
            try:
                parsed_result = json.loads(json_content)
                modules_count = len(parsed_result.get('structure', {}).get('modules', []))
                print(f"✅ [ContentStructureService] Dynamic LLM analysis complete - generated {modules_count} modules based on course content")
                
                # Log analysis summary if available
                if 'analysis_summary' in parsed_result:
                    summary = parsed_result['analysis_summary']
                    print(f"📊 [ContentStructureService] Content complexity: {summary.get('content_complexity', 'Not specified')}")
                    print(f"⏱️ [ContentStructureService] Recommended pacing: {summary.get('recommended_pacing', 'Not specified')}")
                
                # Generate hierarchical tree structure for display
                if 'structure' in parsed_result:
                    tree_structure = self._generate_tree_structure(parsed_result['structure'])
                    parsed_result['tree_structure'] = tree_structure
                
                return parsed_result
                
            except json.JSONDecodeError as e:
                print(f"❌ [ContentStructureService] Failed to parse LLM JSON response: {e}")
                print(f"Raw response preview: {response_content[:500]}...")
                
                # Instead of falling back to hardcoded parsing, retry with a simpler prompt
                return await self._retry_llm_parsing_with_simpler_prompt(course_design_content, research_content, course_name)
                
        except Exception as e:
            print(f"❌ [ContentStructureService] Error in dynamic LLM parsing: {e}")
            # Retry with simpler prompt instead of falling back to hardcoded logic
            return await self._retry_llm_parsing_with_simpler_prompt(course_design_content, research_content, course_name)

    async def _retry_llm_parsing_with_simpler_prompt(self, course_design_content: str, research_content: str, course_name: str) -> Dict[str, Any]:
        """Retry LLM parsing with a simpler, more focused prompt"""
        try:
            print(f"🔄 [ContentStructureService] Retrying with simplified dynamic analysis prompt")
            
            # Simplified but still dynamic prompt
            system_prompt = """You are an educational content analyst. Analyze the course design and create a dynamic structure based on the actual content.

REQUIREMENTS:
1. Extract the EXACT module and chapter structure from the course design
2. Generate content materials that are specific to each chapter's learning objectives
3. Vary content quantity based on chapter complexity (2-10 items per chapter)
4. Use subject-specific titles, not generic ones
5. Return valid JSON only

OUTPUT FORMAT:
{
  "success": true,
  "structure": {
    "course_title": "title from course design",
    "level": "extracted level",
    "duration": "extracted duration", 
    "prerequisites": ["extracted prerequisites"],
    "tools_platforms": "extracted tools",
    "modules": [
      {
        "module_number": 1,
        "title": "Module title from course design",
        "chapters": [
          {
            "chapter_number": 1,
            "title": "Chapter title from course design",
            "details": "Chapter learning objectives",
            "materials": [
              {"type": "slide", "title": "Specific slide title"},
              {"type": "quiz", "title": "Specific quiz title"},
              {"type": "assessment", "title": "Specific assessment title"}
            ]
          }
        ]
      }
    ]
  }
}

CONTENT TYPES: slide, quiz, assessment, interactive, resource
Create materials that match the specific subject matter and learning objectives."""

            user_prompt = f"""COURSE: {course_name}

COURSE DESIGN:
{course_design_content}

RESEARCH:
{research_content}

Analyze and create a dynamic structure with subject-specific content. Return only valid JSON."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await self.openai.create_chat_completion(
                model="gpt-5-nano-2025-08-07",
                messages=messages,
                max_completion_tokens=4000
            )
            
            response_content = response.choices[0].message.content.strip()
            
            # Extract JSON more aggressively
            if "```" in response_content:
                # Find any code block
                start_markers = ["```json", "```"]
                json_content = response_content
                for marker in start_markers:
                    if marker in response_content:
                        json_start = response_content.find(marker) + len(marker)
                        json_end = response_content.find("```", json_start)
                        if json_end != -1:
                            json_content = response_content[json_start:json_end].strip()
                            break
            else:
                json_content = response_content
            
            # Try to find JSON object even if not in code blocks
            if not json_content.strip().startswith('{'):
                # Look for JSON object in the response
                start_idx = response_content.find('{')
                end_idx = response_content.rfind('}')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_content = response_content[start_idx:end_idx + 1]
            
            try:
                parsed_result = json.loads(json_content)
                modules_count = len(parsed_result.get('structure', {}).get('modules', []))
                print(f"✅ [ContentStructureService] Simplified dynamic analysis successful - {modules_count} modules")
                return parsed_result
                
            except json.JSONDecodeError as e:
                print(f"❌ [ContentStructureService] Simplified parsing also failed: {e}")
                print(f"Attempted to parse: {json_content[:200]}...")
                
                # Last resort: return a minimal dynamic structure based on basic parsing
                return await self._create_minimal_dynamic_structure(course_design_content, course_name)
                
        except Exception as e:
            print(f"❌ [ContentStructureService] Error in simplified parsing: {e}")
            return await self._create_minimal_dynamic_structure(course_design_content, course_name)

    async def _create_minimal_dynamic_structure(self, course_design_content: str, course_name: str) -> Dict[str, Any]:
        """Create a minimal but still dynamic structure when LLM parsing fails"""
        try:
            print(f"🔧 [ContentStructureService] Creating minimal dynamic structure as last resort")
            
            # Use basic markdown parsing but enhance it to be more dynamic
            basic_result = self._parse_markdown_structure(course_design_content)
            
            if basic_result["success"]:
                structure = basic_result["structure"]
                
                # Enhance the basic structure to be more dynamic
                for module in structure.get("modules", []):
                    for chapter in module.get("chapters", []):
                        # Replace generic materials with more dynamic ones based on chapter title
                        chapter_title = chapter.get("title", "")
                        chapter["materials"] = self._create_dynamic_materials_for_chapter(chapter_title, module.get("title", ""))
                
                return basic_result
            else:
                # Create absolute minimal structure
                return {
                    "success": True,
                    "structure": {
                        "course_title": course_name,
                        "level": "Intermediate",
                        "duration": "8 weeks",
                        "prerequisites": [],
                        "tools_platforms": "",
                        "modules": [
                            {
                                "module_number": 1,
                                "title": f"{course_name} Fundamentals",
                                "chapters": [
                                    {
                                        "chapter_number": 1,
                                        "title": f"Introduction to {course_name}",
                                        "details": f"Core concepts and fundamentals of {course_name}",
                                        "materials": [
                                            {"type": "slide", "title": f"{course_name} Overview"},
                                            {"type": "slide", "title": f"Key {course_name} Concepts"},
                                            {"type": "quiz", "title": f"{course_name} Fundamentals Quiz"}
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                }
                
        except Exception as e:
            print(f"❌ [ContentStructureService] Error creating minimal structure: {e}")
            return {"success": False, "error": f"Failed to create any structure: {str(e)}"}

    def _create_dynamic_materials_for_chapter(self, chapter_title: str, module_title: str) -> List[Dict[str, str]]:
        """Create dynamic materials based on chapter and module context"""
        materials = []
        title_lower = chapter_title.lower()
        module_lower = module_title.lower()
        
        # Analyze chapter title to create relevant materials
        if any(word in title_lower for word in ["introduction", "overview", "basics", "fundamentals"]):
            materials = [
                {"type": "slide", "title": f"Understanding {chapter_title.replace('Introduction to ', '').replace('Overview of ', '')}"},
                {"type": "slide", "title": f"Core Principles of {chapter_title}"},
                {"type": "quiz", "title": f"{chapter_title} Comprehension Check"}
            ]
        elif any(word in title_lower for word in ["implementation", "building", "creating", "development"]):
            materials = [
                {"type": "slide", "title": f"{chapter_title} Planning"},
                {"type": "slide", "title": f"Step-by-Step {chapter_title}"},
                {"type": "slide", "title": f"{chapter_title} Best Practices"},
                {"type": "assessment", "title": f"{chapter_title} Practical Exercise"}
            ]
        elif any(word in title_lower for word in ["advanced", "optimization", "scaling", "performance"]):
            materials = [
                {"type": "slide", "title": f"Advanced {chapter_title} Techniques"},
                {"type": "slide", "title": f"{chapter_title} Optimization Strategies"},
                {"type": "assessment", "title": f"Advanced {chapter_title} Project"}
            ]
        elif any(word in title_lower for word in ["testing", "debugging", "troubleshooting"]):
            materials = [
                {"type": "slide", "title": f"{chapter_title} Methodologies"},
                {"type": "slide", "title": f"Common {chapter_title} Scenarios"},
                {"type": "interactive", "title": f"Hands-on {chapter_title} Lab"},
                {"type": "assessment", "title": f"{chapter_title} Skills Assessment"}
            ]
        else:
            # Default dynamic structure based on chapter context
            materials = [
                {"type": "slide", "title": f"{chapter_title} Fundamentals"},
                {"type": "slide", "title": f"Practical {chapter_title} Applications"},
                {"type": "quiz", "title": f"{chapter_title} Knowledge Check"}
            ]
        
        return materials

    def _generate_chapter_materials(self, module_number: int, chapter_number: int, chapter_title: str, chapter_details: str = "") -> List[Dict[str, str]]:
        """Generate intelligent materials for each chapter based on content analysis"""
        # This method is now only used as fallback when LLM parsing is not available
        # The LLM method above generates materials directly based on course content
        
        # Create more intelligent materials based on chapter title and details
        materials = []
        
        # Analyze chapter title to determine appropriate content types
        title_lower = chapter_title.lower()
        details_lower = chapter_details.lower()
        
        # Always start with an overview/introduction
        materials.append({"type": "slide", "title": f"{chapter_title} Overview"})
        
        # Add content based on chapter characteristics
        if any(word in title_lower for word in ["introduction", "overview", "getting started"]):
            materials.extend([
                {"type": "slide", "title": f"What is {chapter_title.replace('Introduction to ', '').replace('Overview of ', '')}?"},
                {"type": "slide", "title": f"Key Benefits and Applications"},
                {"type": "quiz", "title": f"{chapter_title} Knowledge Check"}
            ])
        elif any(word in title_lower for word in ["setup", "installation", "configuration"]):
            materials.extend([
                {"type": "slide", "title": f"Prerequisites and Requirements"},
                {"type": "slide", "title": f"Step-by-Step {chapter_title}"},
                {"type": "slide", "title": f"Troubleshooting Common Issues"},
                {"type": "assessment", "title": f"{chapter_title} Practical Exercise"}
            ])
        elif any(word in title_lower for word in ["advanced", "deep dive", "mastery"]):
            materials.extend([
                {"type": "slide", "title": f"Advanced {chapter_title} Concepts"},
                {"type": "slide", "title": f"Real-World Applications"},
                {"type": "slide", "title": f"Best Practices and Optimization"},
                {"type": "assessment", "title": f"Advanced {chapter_title} Project"}
            ])
        else:
            # Default structure for regular chapters
            materials.extend([
                {"type": "slide", "title": f"Core {chapter_title} Concepts"},
                {"type": "slide", "title": f"Practical Examples"},
                {"type": "quiz", "title": f"Chapter {module_number}.{chapter_number} Assessment"}
            ])
        
        return materials

    def _generate_tree_structure(self, structure: Dict[str, Any]) -> str:
        """Generate hierarchical tree structure in the format like the management course example"""
        try:
            tree_lines = []
            
            for module in structure.get("modules", []):
                # Module line
                module_title = f"Module {module['module_number']} — {module['title']}"
                tree_lines.append(f"∟ {module_title}")
                
                for chapter in module.get("chapters", []):
                    # Chapter line
                    chapter_title = f"Chapter {module['module_number']}.{chapter['chapter_number']}: {chapter['title']}"
                    tree_lines.append(f"      ∟ {chapter_title}")
                    
                    # Materials lines
                    slide_count = 1
                    assessment_count = 1
                    
                    for material in chapter.get("materials", []):
                        material_type = material.get("type", "slide")
                        material_title = material.get("title", "Untitled")
                        
                        if material_type == "slide":
                            tree_lines.append(f"             ∟ Slide {slide_count}: {material_title}")
                            slide_count += 1
                        elif material_type == "assessment":
                            tree_lines.append(f"             ∟ Assessment {assessment_count}: {material_title}")
                            assessment_count += 1
                        elif material_type == "quiz":
                            tree_lines.append(f"             ∟ Quiz: {material_title}")
                        elif material_type == "interactive":
                            tree_lines.append(f"             ∟ Interactive: {material_title}")
                        elif material_type == "resource":
                            tree_lines.append(f"             ∟ Resource: {material_title}")
                        elif material_type == "discussion":
                            tree_lines.append(f"             ∟ Discussion: {material_title}")
                        else:
                            tree_lines.append(f"             ∟ {material_title}")
            
            # Add final project if it exists as a separate module
            final_project_modules = [m for m in structure.get("modules", []) if "final project" in m.get("title", "").lower()]
            if final_project_modules:
                final_module = final_project_modules[0]
                tree_lines.append(f"∟ Final Project — Capstone")
                
                if final_module.get("chapters"):
                    final_chapter = final_module["chapters"][0]
                    slide_count = 1
                    for material in final_chapter.get("materials", []):
                        material_title = material.get("title", "Untitled")
                        if material.get("type") == "assessment":
                            tree_lines.append(f"      ∟ Assessment: {material_title}")
                        else:
                            tree_lines.append(f"      ∟ Slide {slide_count}: {material_title}")
                            slide_count += 1
            
            return "\n".join(tree_lines)
            
        except Exception as e:
            print(f"❌ [ContentStructureService] Error generating tree structure: {e}")
            return "Error generating tree structure"
    
    def _generate_content_checklist(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive content checklist from parsed structure"""
        checklist = {
            "modules": [],
            "total_items": 0,
            "total_slides": 0,
            "total_quizzes": 0,
            "total_assessments": 0
        }
        
        for module in structure.get("modules", []):
            module_checklist = {
                "module_number": module["module_number"],
                "title": module["title"],
                "chapters": []
                # Removed module_quiz - no more Chapter 0
            }
            
            for chapter in module.get("chapters", []):
                chapter_checklist = {
                    "chapter_number": chapter["chapter_number"],
                    "title": chapter["title"],
                    "materials": []
                }
                
                for material in chapter.get("materials", []):
                    material_item = {
                        "type": material["type"],
                        "title": material["title"],
                        "status": "pending"
                    }
                    chapter_checklist["materials"].append(material_item)
                    
                    # Count items by type
                    checklist["total_items"] += 1
                    if material["type"] == "slide":
                        checklist["total_slides"] += 1
                    elif material["type"] == "quiz":
                        checklist["total_quizzes"] += 1
                    elif material["type"] == "assessment":
                        checklist["total_assessments"] += 1
                
                module_checklist["chapters"].append(chapter_checklist)
            
            # No module quiz added - eliminates Chapter 0
            checklist["modules"].append(module_checklist)
        
        return checklist
    
    async def save_structure_checklist(self, course_id: str, structure: Dict[str, Any], checklist: Dict[str, Any]) -> Dict[str, Any]:
        """Save the parsed structure and checklist to database"""
        try:
            print(f"💾 [ContentStructureService] Saving structure checklist for course {course_id}")
            
            # Create CourseStructureChecklist document
            checklist_doc = CourseStructureChecklist(
                course_id=ObjectId(course_id),
                structure=structure,
                total_items=checklist["total_items"],
                completed_items=0,
                status="pending",
                user_approved=False
            )
            
            # Save to database using DatabaseService interface
            checklist_id = await self.db.insert_document(
                "course_structure_checklists", 
                checklist_doc.dict(by_alias=True)
            )
            
            print(f"✅ [ContentStructureService] Saved checklist with ID: {checklist_id}")
            
            return {
                "success": True,
                "checklist_id": checklist_id,
                "total_items": checklist["total_items"]
            }
            
        except Exception as e:
            print(f"❌ [ContentStructureService] Error saving checklist: {e}")
            return {"success": False, "error": f"Failed to save checklist: {str(e)}"}
    
    async def create_content_materials(self, course_id: str, checklist: Dict[str, Any]) -> Dict[str, Any]:
        """Create ContentMaterial documents for each item in the checklist"""
        try:
            print(f"📝 [ContentStructureService] Creating content materials for course {course_id}")
            
            materials = []
            
            for module in checklist.get("modules", []):
                module_number = module["module_number"]
                
                # Create materials for each chapter only - no module quizzes
                for chapter in module.get("chapters", []):
                    chapter_number = chapter["chapter_number"]
                    
                    # Track slide numbers within each chapter
                    slide_counter = 1
                    
                    for material in chapter.get("materials", []):
                        # Determine slide number for slide materials
                        slide_number = None
                        if material["type"] == "slide":
                            slide_number = slide_counter
                            slide_counter += 1
                        
                        material_doc = ContentMaterial(
                            course_id=ObjectId(course_id),
                            module_number=module_number,
                            chapter_number=chapter_number,
                            material_type=material["type"],
                            title=material["title"],
                            description=f"Generated content for {material['title']}",
                            status="pending",
                            slide_number=slide_number  # Set slide number for slides, None for other types
                        )
                        materials.append(material_doc.dict(by_alias=True))
                
                # Removed module quiz creation - no more Chapter 0
            
            # Bulk insert materials using individual inserts (DatabaseService doesn't have bulk insert)
            if materials:
                material_ids = []
                for material in materials:
                    material_id = await self.db.insert_document("content_materials", material)
                    material_ids.append(material_id)
                
                print(f"✅ [ContentStructureService] Created {len(material_ids)} content materials")
                
                return {
                    "success": True,
                    "created_count": len(material_ids),
                    "material_ids": material_ids
                }
            else:
                return {"success": True, "created_count": 0, "material_ids": []}
                
        except Exception as e:
            print(f"❌ [ContentStructureService] Error creating materials: {e}")
            return {"success": False, "error": f"Failed to create materials: {str(e)}"}
    
    async def get_course_structure_checklist(self, course_id: str) -> Optional[Dict[str, Any]]:
        """Get the course structure checklist for a course"""
        try:
            checklist = await self.db.find_document(
                "course_structure_checklists", 
                {"course_id": ObjectId(course_id)}
            )
            
            if checklist:
                checklist["_id"] = str(checklist["_id"])
                checklist["course_id"] = str(checklist["course_id"])
                return checklist
            
            return None
            
        except Exception as e:
            print(f"❌ [ContentStructureService] Error getting checklist: {e}")
            return None
    
    async def update_checklist_approval(self, course_id: str, approved: bool, modifications: Optional[str] = None) -> Dict[str, Any]:
        """Update checklist approval status"""
        try:
            # First find the checklist to get its ID
            checklist = await self.db.find_document(
                "course_structure_checklists", 
                {"course_id": ObjectId(course_id)}
            )
            
            if not checklist:
                return {"success": False, "error": "Checklist not found"}
            
            update_data = {
                "user_approved": approved,
                "status": "approved" if approved else "needs_revision",
                "updated_at": datetime.utcnow()
            }
            
            if approved:
                update_data["approved_at"] = datetime.utcnow()
                update_data["status"] = "approved"
            
            if modifications:
                update_data["modification_notes"] = modifications
            
            success = await self.db.update_document(
                "course_structure_checklists",
                str(checklist["_id"]),
                update_data
            )
            
            if success:
                return {"success": True, "approved": approved}
            else:
                return {"success": False, "error": "Failed to update checklist"}
                
        except Exception as e:
            print(f"❌ [ContentStructureService] Error updating approval: {e}")
            return {"success": False, "error": f"Failed to update approval: {str(e)}"}
    
    async def get_content_materials(self, course_id: str) -> List[Dict[str, Any]]:
        """Get all content materials for a course"""
        try:
            # Note: DatabaseService doesn't have a method to get multiple documents with sorting
            # For now, we'll return an empty list and implement this when needed
            # This method would need to be implemented in DatabaseService for full functionality
            print(f"⚠️ [ContentStructureService] get_content_materials not fully implemented - DatabaseService needs find_many method")
            return []
            
        except Exception as e:
            print(f"❌ [ContentStructureService] Error getting materials: {e}")
            return []
    
    async def update_material_status(self, material_id: str, status: str, content: Optional[str] = None) -> Dict[str, Any]:
        """Update the status and content of a material"""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow()
            }
            
            if content:
                update_data["content"] = content
            
            success = await self.db.update_document(
                "content_materials",
                material_id,
                update_data
            )
            
            if success:
                return {"success": True, "status": status}
            else:
                return {"success": False, "error": "Material not found or not updated"}
                
        except Exception as e:
            print(f"❌ [ContentStructureService] Error updating material: {e}")
            return {"success": False, "error": f"Failed to update material: {str(e)}"}
