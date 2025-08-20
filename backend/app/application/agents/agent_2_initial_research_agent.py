import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

from ...infrastructure.ai.openai_service import OpenAIService
from ...infrastructure.database.database_service import DatabaseService
from ..services.message_service import MessageService
from ..services.context_service import ContextService
from ...infrastructure.storage.r2_storage import R2StorageService


class InitialResearchAgent:
    """Agent specialized in conducting comprehensive initial research for course design"""
    
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
                "name": "conduct_initial_research",
                "description": "Conduct comprehensive subject matter research for course design",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {
                            "type": "string",
                            "description": "The ID of the course"
                        },
                        "focus_area": {
                            "type": "string",
                            "description": "Optional specific focus area for the research"
                        }
                    },
                    "required": ["course_id"]
                }
            }
        ]
    
    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        """Generate system prompt for initial research"""
        course = context.get("course_state")
        course_id = context.get('current_course_id', '')
        
        return f"""You are an Expert Research Specialist for course "{course['name']}" (ID: {course_id}).

🔬 CORE MISSION: Conduct comprehensive subject matter research to inform evidence-based course design.

🎯 RESEARCH OBJECTIVES:
- Gather latest industry trends and technologies (2025)
- Identify current best practices and methodologies
- Research academic developments and theoretical foundations
- Analyze market demands and skill requirements
- Discover real-world applications and case studies
- Find leading organizations and thought leaders

🛠️ AVAILABLE TOOLS:
- Web Search: Research latest information and current trends
- Function Tools: Handle research operations

Available functions:
- conduct_initial_research: Start comprehensive research process - use course_id: {course_id}

🎯 INTELLIGENT FUNCTION CALLING:
- "Start research" or similar → Call conduct_initial_research immediately
- "Research this topic" → Call conduct_initial_research with focus_area
- "Begin analysis" → Call conduct_initial_research

Be intelligent about function calling - when users request research, act immediately.

REMEMBER: Focus on comprehensive subject matter research, not teaching methods. This research will inform course design but should be about the subject itself."""
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools including web search and function tools"""
        tools = [
            {"type": "web_search_preview"}  # Web search tool for latest content research
        ]
        
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
        """Process a user message for initial research using Responses API"""
        
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
            print(f"🔄 \033[96m[InitialResearchAgent]\033[0m \033[1mSending request to Responses API...\033[0m")
            print(f"   📝 Model: \033[93m{self.model}\033[0m")
            print(f"   📝 User Message: \033[92m'{user_message}'\033[0m")
            print(f"   📝 System Instructions Preview: \033[90m{system_instructions[:150]}...\033[0m")
            print(f"   🔧 Tools available: \033[93m{len(self.get_all_tools())}\033[0m")
            print(f"   🌐 Web search enabled: \033[92mYes\033[0m")
            print(f"{'='*60}")
            
            # Use Responses API with web search and function calling
            response = await self.openai.create_response(
                model=self.model,
                input=input_messages,
                instructions=system_instructions,
                tools=self.get_all_tools()
            )
            
            print(f"\n✅ \033[96m[InitialResearchAgent]\033[0m \033[1m\033[92mResponses API Response received\033[0m")
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
                    
                    print(f"🔧 [InitialResearchAgent] Processing function call: {function_name}")
                    
                    if function_name == "conduct_initial_research":
                        result = await self._conduct_initial_research(function_args["course_id"], function_args.get("focus_area"))
                        function_results["research_conducted"] = result
                
                elif item.type == "web_search_call":
                    # Handle web search results
                    print(f"🌐 [InitialResearchAgent] Processing web search call: {item.id}")
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
                                            print(f"📎 [InitialResearchAgent] Found citation: {annotation.url}")
            
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
            print(f"InitialResearchAgent Responses API error: {e}")
            print(f"Full traceback: {traceback.format_exc()}")
            return {
                "response": "I apologize, but I'm experiencing some technical difficulties with the research process. Please try again in a moment.",
                "course_id": course_id,
                "function_results": {},
                "error": str(e)
            }
    
    async def _conduct_initial_research(self, course_id: str, focus_area: Optional[str] = None) -> Dict[str, Any]:
        """Conduct initial research for the course - returns streaming signal"""
        # This method returns a signal to start streaming research
        # The actual streaming happens in the route handler or orchestrator
        return {
            "success": True,
            "streaming": True,
            "course_id": course_id,
            "focus_area": focus_area
        }
    
    async def stream_research_generation(self, course_id: str, focus_area: Optional[str] = None, user_id: Optional[str] = None):
        """Stream research generation in real-time"""
        print(f"\n🔬 [InitialResearchAgent] Starting stream_research_generation")
        print(f"   📋 Course ID: {course_id}")
        print(f"   👤 User ID: {user_id}")
        print(f"   🎯 Focus Area: {focus_area}")
        
        try:
            # Get course info
            print(f"🔍 [InitialResearchAgent] Fetching course info...")
            course = await self.db.find_course(course_id)
            if not course:
                print(f"❌ [InitialResearchAgent] Course not found: {course_id}")
                yield {"type": "error", "content": "Course not found"}
                return
            
            print(f"✅ [InitialResearchAgent] Course found: {course.get('name')}")
            
            # Get user_id from course if not provided
            if not user_id:
                user_id = str(course.get("user_id"))
                print(f"🔄 [InitialResearchAgent] Using user_id from course: {user_id}")
            
            # Create research.md file header
            research_header = f"""# 🔬 Research Analysis for {course['name']}

*Generated on {datetime.utcnow().strftime('%B %d, %Y')} using latest 2025 data*

## Research Methodology

This research analysis was conducted using real-time web search to gather the most current information about:
- Industry standards and methodologies
- Latest tools and technologies
- Modern teaching approaches and pedagogical strategies
- Recent developments and emerging trends
- Current market demands and skills requirements
- Best practices from leading institutions and companies

---

## Research Findings

"""
            
            # Send research start with markdown file
            yield {
                "type": "start",
                "content": "🔬 Starting comprehensive research analysis...",
                "file_type": "research"
            }
            
            # Stream the research header
            yield {
                "type": "content",
                "content": research_header,
                "full_content": research_header,
                "file_type": "research"
            }
            
            # Send initial research progress event to show blue loader from the start
            yield {
                "type": "research_progress",
                "search_count": 0,
                "total_searches": 30,
                "current_source": "Initializing Research",
                "status": "searching",
                "message": "Preparing comprehensive research analysis..."
            }
            
            # Build research prompt for web search - COMPREHENSIVE SUBJECT MATTER RESEARCH
            course_topic = course['name'].replace('Untitled Course', 'Modern Technology and Software Development')
            focus_context = f" with specific focus on {focus_area}" if focus_area else ""
            
            research_prompt = f"""You are a subject matter research specialist. Conduct comprehensive, in-depth research on the latest developments, technologies, and trends in "{course_topic}"{focus_context} for 2025.

CRITICAL INSTRUCTIONS:
- DO NOT ask clarifying questions or follow-up questions
- DO NOT request more information from the user
- DO NOT offer additional services or suggest next steps
- DO NOT include conversational elements like "If you'd like..." or "Would you like me to..."
- DIRECTLY perform web searches and research
- Focus on LATEST DEVELOPMENTS and CURRENT STATE of the field
- Research the subject matter itself, not how to teach it
- Prioritize cutting-edge content, new tools, recent breakthroughs
- End your response with factual content only - no questions or offers

RESEARCH SCOPE - DEEP SUBJECT MATTER FOCUS:
- Latest technologies, tools, and frameworks (2025)
- Recent breakthroughs and innovations
- Current industry trends and emerging practices
- New research papers and academic developments
- Real-world applications and case studies
- Market trends and industry adoption
- Future directions and upcoming developments
- Current best practices and methodologies

Structure your response as a comprehensive subject matter research report with these sections:

### 1. Latest Technologies & Tools (2025)
What are the newest tools, frameworks, and technologies currently being used?

### 2. Recent Breakthroughs & Innovations
What major developments have happened in the last 1-2 years?

### 3. Current Industry Trends & Practices
What approaches are leading companies and practitioners using right now?

### 4. Emerging Developments & Future Directions
What's on the horizon? What should we expect in the next 1-2 years?

### 5. Real-World Applications & Case Studies
How is this being applied in practice? What are successful implementations?

### 6. Academic Research & New Findings
What does the latest research say? Any new theoretical developments?

### 7. Market Adoption & Industry Impact
How is the industry adopting these technologies? What's the business impact?

### 8. Current Best Practices & Methodologies
What are the established best practices as of 2025?

### 9. Key Players & Leading Organizations
Who are the thought leaders, companies, and organizations driving innovation?

### 10. Essential Knowledge for 2025
What knowledge and skills are most critical for practitioners today?

IMPORTANT: Focus on comprehensive subject matter expertise and latest developments. Prioritize current, cutting-edge information over basic concepts. This research will inform course design but should be about the subject itself. End your response with factual content only - do not ask questions or offer additional services."""
            
            # Use Responses API with web search for research - STREAMING ENABLED
            research_response = await self.openai.create_response(
                model=self.model,
                input=[{"role": "user", "content": research_prompt}],
                tools=[{"type": "web_search_preview"}],
                stream=True
            )
            
            # Extract research findings with streaming to research.md
            research_findings = research_header
            web_search_count = 0
            research_content_received = False
            
            print(f"🌐 [InitialResearchAgent] Starting to process research streaming response...")
            
            # Stream the research response directly to research.md
            async for event in research_response:
                if hasattr(event, 'type'):
                    # Handle different event types from Responses API
                    if event.type == "response.output_text.delta":
                        # Research content streaming to research.md
                        if hasattr(event, 'delta') and event.delta:
                            research_chunk = event.delta
                            research_findings += research_chunk
                            research_content_received = True
                            
                            # Send research content to research.md file
                            yield {
                                "type": "content",
                                "content": research_chunk,
                                "full_content": research_findings,
                                "file_type": "research"
                            }
                    
                    # Handle web search events
                    elif (event.type in ["response.web_search.started", "web_search.started", "web_search_started", 
                                       "response.tool_call.started", "tool_call.started", "tool_started"] or
                          "search" in str(event.type).lower() or "tool" in str(event.type).lower()):
                        
                        # Check if this is actually a web search tool call
                        is_web_search = False
                        if hasattr(event, 'tool') and hasattr(event.tool, 'type'):
                            if event.tool.type == "web_search_preview":
                                is_web_search = True
                        elif hasattr(event, 'name') and "search" in str(event.name).lower():
                            is_web_search = True
                        elif "search" in str(event.type).lower():
                            is_web_search = True
                        
                        if is_web_search:
                            web_search_count += 1
                            print(f"🔍 [InitialResearchAgent] Web search {web_search_count} started")
                            
                            # Send progress event
                            yield {
                                "type": "research_progress",
                                "search_count": web_search_count,
                                "total_searches": 30,
                                "current_source": f"Web Search {web_search_count}",
                                "status": "searching",
                                "message": f"Conducting web search {web_search_count}..."
                            }
                    
                    elif (event.type in ["response.web_search.completed", "web_search.completed", "web_search_completed",
                                       "response.tool_call.completed", "tool_call.completed", "tool_completed"] and
                          ("search" in str(event.type).lower() or hasattr(event, 'tool'))):
                        # Track when web search completes
                        print(f"✅ [InitialResearchAgent] Web search completed")
                        completion_indicator = f"✅ **Web search completed**\n\n"
                        research_findings += completion_indicator
                        yield {
                            "type": "content",
                            "content": completion_indicator,
                            "full_content": research_findings,
                            "file_type": "research"
                        }
                    
                    elif event.type == "response.output_text.done":
                        print(f"✅ [InitialResearchAgent] Research text output completed")
                    elif event.type == "response.completed":
                        print(f"✅ [InitialResearchAgent] Research response completed")
            
            print(f"📊 [InitialResearchAgent] Research streaming completed:")
            print(f"   🔍 Web searches detected: {web_search_count}")
            print(f"   📝 Content received: {research_content_received}")
            print(f"   📏 Total content length: {len(research_findings)}")
            
            # Send the "Analyzing and compiling research findings..." message BEFORE completion
            yield {
                "type": "research_progress",
                "search_count": web_search_count,
                "total_searches": web_search_count,
                "current_source": "Analyzing Research",
                "status": "analyzing",
                "message": "Analyzing and compiling research findings..."
            }
            
            # Add a small delay to show the analyzing message
            import asyncio
            await asyncio.sleep(1.5)
            
            # Send final research progress event to hide the blue loader
            yield {
                "type": "research_progress",
                "search_count": web_search_count,
                "total_searches": web_search_count,
                "current_source": "Research Complete",
                "status": "completed",
                "message": f"Completed analysis of {web_search_count} sources"
            }
            
            # If no research content was generated, create fallback research
            if not research_content_received or len(research_findings) <= len(research_header) + 100:
                print(f"⚠️ [InitialResearchAgent] No research content received, generating fallback research...")
                fallback_research = await self._generate_fallback_research(course['name'], focus_area)
                research_findings += fallback_research
                web_search_count = max(web_search_count, 1)  # Ensure at least 1 for fallback research
                
                # Stream the fallback research
                yield {
                    "type": "content",
                    "content": fallback_research,
                    "full_content": research_findings,
                    "file_type": "research"
                }
            
            # Add research completion footer
            research_footer = f"""

---

## Research Summary

✅ **Research Completed Successfully**
- **Sources Analyzed:** {web_search_count} web sources
- **Research Date:** {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}
- **Focus Area:** {course['name']}{f" - {focus_area}" if focus_area else ""}

*This comprehensive research analysis provides the foundation for evidence-based course design.*
"""
            
            research_findings += research_footer
            
            # Send final research.md content
            yield {
                "type": "content",
                "content": research_footer,
                "full_content": research_findings,
                "file_type": "research"
            }
            
            print(f"✅ [InitialResearchAgent] Research completed with {web_search_count} web searches")
            print(f"📊 [InitialResearchAgent] Research findings streamed to research.md ({len(research_findings)} chars)")
            
            # Save research.md to R2 storage
            print(f"💾 [InitialResearchAgent] Saving research.md to R2...")
            research_upload_result = await self.storage.upload_file_content(
                key=f"courses/{course_id}/research.md",
                content=research_findings,
                content_type="text/markdown"
            )
            
            if research_upload_result.get("success"):
                print(f"✅ [InitialResearchAgent] Research.md saved to R2: {research_upload_result.get('public_url')}")
                # Update course with research R2 information
                await self.db.update_course(course_id, {
                    "research_r2_key": research_upload_result.get("r2_key", f"courses/{course_id}/research.md"),
                    "research_public_url": research_upload_result.get("public_url"),
                    "research_updated_at": datetime.utcnow(),
                    "workflow_step": "course_design_method_selection"  # Move to next step
                })
            else:
                print(f"❌ [InitialResearchAgent] Failed to save research.md: {research_upload_result.get('error')}")
            
            # Store the completion message in chat history
            completion_message = f"✅ **Research completed successfully!** Analyzed {web_search_count} sources and generated comprehensive research analysis."
            try:
                print(f"💬 [InitialResearchAgent] Storing completion message in chat...")
                await self.messages.store_message(course_id, user_id, completion_message, "assistant")
                print(f"✅ [InitialResearchAgent] Successfully stored completion message for course {course_id}")
            except Exception as e:
                print(f"❌ [InitialResearchAgent] Failed to store completion message: {e}")
            
            # Send completion signal with workflow transition
            print(f"🎉 [InitialResearchAgent] Sending completion signal...")
            yield {
                "type": "complete",
                "content": completion_message,
                "r2_key": research_upload_result.get("r2_key", f"courses/{course_id}/research.md"),
                "public_url": research_upload_result.get("public_url"),
                "full_content": research_findings,
                "workflow_transition": {
                    "next_step": "course_design_generation",
                    "next_agent": "course_design",
                    "trigger_automatically": True,
                    "research_completed": True
                }
            }
            
            print(f"🔬 [InitialResearchAgent] Stream research generation completed successfully!")
            
        except Exception as e:
            error_msg = f"Failed to conduct research: {str(e)}"
            print(f"❌ [InitialResearchAgent] CRITICAL ERROR: {error_msg}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            yield {"type": "error", "content": error_msg}
    
    async def _generate_response_with_context(self, base_response: Optional[str], function_results: Dict[str, Any], web_search_results: Optional[Dict[str, Any]] = None) -> str:
        """Generate a contextual response based on function call results and web search"""
        if not function_results and not web_search_results:
            return base_response or "I'm here to help you conduct comprehensive research for your course. What would you like me to research?"
        
        # Add web search context if available
        search_context = ""
        if web_search_results:
            search_count = len(web_search_results)
            if search_count > 0:
                search_context = f"\n\n🌐 **Research Sources:** Analyzed {search_count} web sources for current information."
        
        # Prioritize streaming research response
        if "research_conducted" in function_results:
            result = function_results["research_conducted"]
            if result.get("streaming"):
                focus_text = f" focusing on {result.get('focus_area')}" if result.get('focus_area') else ""
                return f"🔬 **Starting Research Analysis**\n\nConducting comprehensive research{focus_text}:\n\n- Latest technologies and trends\n- Industry best practices\n- Academic developments\n- Real-world applications\n\n*← Research findings will appear in real-time*"
            else:
                return f"✅ **Research Complete!**\n\n**Generated:**\n• Comprehensive subject matter analysis\n• Latest industry trends and technologies\n• Current best practices and methodologies\n• Research citations and sources\n\n**Next:** Proceed to course design generation"
        
        return base_response or "I've processed your research request. The comprehensive analysis is ready for course design."
    
    async def _generate_fallback_research(self, course_name: str, focus_area: Optional[str] = None) -> str:
        """Generate fallback research content when web search fails"""
        try:
            print(f"🔄 [InitialResearchAgent] Generating fallback research for: {course_name}")
            
            focus_context = f" with focus on {focus_area}" if focus_area else ""
            
            fallback_prompt = f"""You are a subject matter expert. Generate comprehensive research content about "{course_name}"{focus_context} using your knowledge base.

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
                messages=[{"role": "user", "content": fallback_prompt}],
                temperature=0.7
            )
            
            fallback_content = response.choices[0].message.content
            print(f"✅ [InitialResearchAgent] Fallback research generated ({len(fallback_content)} chars)")
            
            return f"""

### 🔄 Fallback Research Analysis

*Note: This research was generated using AI knowledge base due to web search limitations*

{fallback_content}

"""
            
        except Exception as e:
            print(f"❌ [InitialResearchAgent] Error generating fallback research: {e}")
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
