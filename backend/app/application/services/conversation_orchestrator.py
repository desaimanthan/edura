from typing import Dict, Any, Optional

from .intent_service import IntentService
from .agent_coordinator import AgentCoordinator
from .context_service import ContextService
from .message_service import MessageService
from ...infrastructure.ai.openai_service import OpenAIService


class ConversationOrchestrator:
    """Main orchestrator for conversational AI interactions"""
    
    def __init__(self, intent_service: IntentService, agent_coordinator: AgentCoordinator, 
                 context_service: ContextService, message_service: MessageService, 
                 openai_service: OpenAIService):
        self.intent_service = intent_service
        self.agent_coordinator = agent_coordinator
        self.context_service = context_service
        self.message_service = message_service
        self.openai_service = openai_service
        self.model = "gpt-5-nano-2025-08-07"
    
    async def process_message(self, course_id: Optional[str], user_id: str, user_message: str, context_hints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Main entry point for processing user messages"""
        
        try:
            # Check if this is a welcome trigger message
            if user_message == '__WELCOME_TRIGGER__':
                # Send welcome message without storing the trigger message
                welcome_response = await self._send_welcome_message(course_id, user_id)
                if welcome_response:
                    return welcome_response
            
            # Check if this is the very first message in a new conversation
            should_send_welcome = await self._should_send_welcome_message(course_id, user_id)
            
            if should_send_welcome:
                # Send welcome message first, then process the user's message
                welcome_response = await self._send_welcome_message(course_id, user_id)
                if welcome_response:
                    return welcome_response
            
            # Get conversation context
            context = await self.context_service.build_context_for_agent(course_id, user_id)
            
            # Enhance context with hints from frontend if available
            if context_hints:
                print(f"📋 [ConversationOrchestrator] Enhancing context with frontend hints: {context_hints}")
                
                # Add workflow context hints to the context
                if context_hints.get('current_step'):
                    context['current_step'] = context_hints['current_step']
                
                if context_hints.get('available_files'):
                    # Merge available files info into course state
                    if 'course_state' not in context:
                        context['course_state'] = {}
                    
                    available_files = context_hints['available_files']
                    if available_files.get('research'):
                        context['course_state']['research_public_url'] = available_files['research'].get('url')
                        context['course_state']['research_r2_key'] = available_files['research'].get('r2_key')
                    
                    if available_files.get('course_design'):
                        context['course_state']['course_design_public_url'] = available_files['course_design'].get('url')
                        context['course_state']['course_design_r2_key'] = available_files['course_design'].get('r2_key')
                    
                    if available_files.get('cover_image'):
                        context['course_state']['cover_image_public_url'] = available_files['cover_image'].get('url')
                        context['course_state']['cover_image_r2_key'] = available_files['cover_image'].get('r2_key')
                
                if context_hints.get('suggested_message'):
                    context['suggested_message'] = context_hints['suggested_message']
            
            # Analyze user intent
            print(f"\n{'='*60}")
            print(f"🎯 \033[95m[ConversationOrchestrator]\033[0m \033[1mAnalyzing user intent...\033[0m")
            print(f"   📝 User Message: \033[92m'{user_message}'\033[0m")
            if context_hints:
                print(f"   📋 Context Hints: \033[94m{context_hints}\033[0m")
            print(f"{'='*60}")
            
            intent_result = await self.intent_service.analyze_request(user_message, context)
            
            print(f"\n🎯 \033[95m[ConversationOrchestrator]\033[0m \033[1m\033[92mIntent Analysis Complete\033[0m")
            print(f"   📋 Category: \033[93m{intent_result.get('category')}\033[0m")
            print(f"   🎬 Action: \033[93m{intent_result.get('workflow_action')}\033[0m")
            print(f"   🎯 Target Agent: \033[93m{intent_result.get('target_agent')}\033[0m")
            print(f"   🔍 Confidence: \033[93m{intent_result.get('confidence')}\033[0m")
            print(f"   💭 Reasoning:")
            print(f"      \033[90m{intent_result.get('reasoning', 'No reasoning provided')}\033[0m")
            print(f"   \033[90m{'-'*50}\033[0m")
            
            # Route based on intent category - agents will handle message storage
            if intent_result['category'] == 'workflow_request':
                # Handle workflow-related requests
                agent_result = await self.agent_coordinator.execute_with_agent(
                    intent_result, course_id, user_id, user_message
                )
            elif intent_result['category'] == 'agent_request':
                # Handle direct agent requests
                agent_name = self.intent_service.determine_agent_from_intent(intent_result)
                agent_result = await self.agent_coordinator.route_to_agent(
                    agent_name, course_id, user_id, user_message
                )
            else:
                # Handle general conversation - store message here since no agent will handle it
                if course_id:
                    await self.message_service.store_message(course_id, user_id, user_message, "user")
                agent_result = await self._handle_general_conversation(
                    user_message, context, course_id, user_id
                )
            
            # Update course_id if agent created a new course
            final_course_id = agent_result.get('course_id', course_id)
            
            # CRITICAL FIX: Check if MaterialContentGeneratorAgent was called and handle streaming
            target_agent = intent_result.get('target_agent')
            if target_agent == 'material_content_generator':
                print(f"🎨 [ConversationOrchestrator] MaterialContentGeneratorAgent was called - checking for streaming events")
                
                # Check if the agent result contains material content generation
                function_results = agent_result.get('function_results', {})
                
                # Handle specific slide generation with streaming
                if 'specific_slide_generated' in function_results:
                    specific_result = function_results['specific_slide_generated']
                    if specific_result.get('success') and specific_result.get('material'):
                        print(f"🎨 [ConversationOrchestrator] Specific slide generated - triggering streaming events")
                        
                        # Get material info
                        material = specific_result['material']
                        targeted_slide = specific_result.get('targeted_slide', {})
                        
                        # Create streaming events that match what the frontend expects
                        streaming_events = []
                        
                        # 1. Material content start event
                        file_path = self._get_material_file_path_from_material(material, targeted_slide)
                        # CRITICAL FIX: Generate the actual storage path that matches course file store structure
                        storage_path = self._get_storage_path_from_material(material, targeted_slide)
                        
                        streaming_events.append({
                            "type": "material_content_start",
                            "material_id": material['id'],
                            "title": material['title'],
                            "file_path": storage_path,  # Use storage path for file operations
                            "display_path": file_path,  # Keep display path for UI
                            "slide_number": targeted_slide.get('slide_number', 1),
                            "message": f"Starting content generation for {material['title']}"
                        })
                        
                        # 2. Material content stream event
                        streaming_events.append({
                            "type": "material_content_stream",
                            "material_id": material['id'],
                            "file_path": storage_path,  # Use storage path for file operations
                            "display_path": file_path,  # Keep display path for UI
                            "content": material['content'],
                            "content_length": material['content_length'],
                            "message": f"Generated {material['content_length']:,} characters of content"
                        })
                        
                        # 3. Material content complete event
                        streaming_events.append({
                            "type": "material_content_complete",
                            "material_id": material['id'],
                            "title": material['title'],
                            "file_path": storage_path,  # Use storage path for file operations
                            "display_path": file_path,  # Keep display path for UI
                            "content": material['content'],
                            "content_length": material['content_length'],
                            "has_images": material.get('has_images', False),
                            "r2_key": material.get('r2_key'),
                            "public_url": material.get('public_url'),
                            "message": f"Content generation completed for {material['title']}"
                        })
                        
                        # Return with streaming events for the frontend to handle
                        return {
                            "response": agent_result.get('response', ''),
                            "course_id": final_course_id,
                            "function_results": function_results,
                            "streaming_events": streaming_events,
                            "material_content_streaming": True
                        }
                
                # Handle regular slide content generation with streaming (from auto-trigger)
                elif 'slide_content_generated' in function_results:
                    slide_result = function_results['slide_content_generated']
                    if slide_result.get('success') and slide_result.get('material'):
                        print(f"🎨 [ConversationOrchestrator] Regular slide generated - triggering streaming events")
                        
                        # Get material info
                        material = slide_result['material']
                        
                        # Create streaming events that match what the frontend expects
                        streaming_events = []
                        
                        # 1. Material content start event
                        file_path = self._get_material_file_path_from_material(material, {})
                        streaming_events.append({
                            "type": "material_content_start",
                            "material_id": material['id'],
                            "title": material['title'],
                            "file_path": file_path,
                            "slide_number": 1,  # Default for auto-generated first slide
                            "message": f"Starting content generation for {material['title']}"
                        })
                        
                        # 2. Material content stream event
                        streaming_events.append({
                            "type": "material_content_stream",
                            "material_id": material['id'],
                            "file_path": file_path,
                            "content": material['content'],
                            "content_length": material['content_length'],
                            "message": f"Generated {material['content_length']:,} characters of content"
                        })
                        
                        # 3. Material content complete event
                        streaming_events.append({
                            "type": "material_content_complete",
                            "material_id": material['id'],
                            "title": material['title'],
                            "file_path": file_path,
                            "content": material['content'],
                            "content_length": material['content_length'],
                            "has_images": material.get('has_images', False),
                            "r2_key": material.get('r2_key'),
                            "public_url": material.get('public_url'),
                            "message": f"Content generation completed for {material['title']}"
                        })
                        
                        # Return with streaming events for the frontend to handle
                        return {
                            "response": agent_result.get('response', ''),
                            "course_id": final_course_id,
                            "function_results": function_results,
                            "streaming_events": streaming_events,
                            "material_content_streaming": True
                        }
                
                # Handle content generation started with auto-generated first slide
                elif 'content_generation_started' in function_results:
                    start_result = function_results['content_generation_started']
                    if (start_result.get('success') and start_result.get('auto_generate') and 
                        start_result.get('first_slide_generated') and start_result.get('generated_material')):
                        print(f"🎨 [ConversationOrchestrator] Content generation started with auto-generated first slide - triggering streaming events")
                        
                        # Get material info from the auto-generated first slide
                        material = start_result['generated_material']
                        
                        # Create streaming events that match what the frontend expects
                        streaming_events = []
                        
                        # 1. Material content start event
                        file_path = self._get_material_file_path_from_material(material, {})
                        streaming_events.append({
                            "type": "material_content_start",
                            "material_id": material['id'],
                            "title": material['title'],
                            "file_path": file_path,
                            "slide_number": 1,  # First slide
                            "message": f"Starting content generation for {material['title']}"
                        })
                        
                        # 2. Material content stream event
                        streaming_events.append({
                            "type": "material_content_stream",
                            "material_id": material['id'],
                            "file_path": file_path,
                            "content": material['content'],
                            "content_length": material['content_length'],
                            "message": f"Generated {material['content_length']:,} characters of content"
                        })
                        
                        # 3. Material content complete event
                        streaming_events.append({
                            "type": "material_content_complete",
                            "material_id": material['id'],
                            "title": material['title'],
                            "file_path": file_path,
                            "content": material['content'],
                            "content_length": material['content_length'],
                            "has_images": material.get('has_images', False),
                            "r2_key": material.get('r2_key'),
                            "public_url": material.get('public_url'),
                            "message": f"Content generation completed for {material['title']}"
                        })
                        
                        # Return with streaming events for the frontend to handle
                        return {
                            "response": agent_result.get('response', ''),
                            "course_id": final_course_id,
                            "function_results": function_results,
                            "streaming_events": streaming_events,
                            "material_content_streaming": True
                        }
            
            # Check if agent returned a streaming signal
            function_results = agent_result.get('function_results', {})
            
            # Handle streaming signals for research generation
            if 'research_conducted' in function_results:
                research_result = function_results['research_conducted']
                if research_result.get('streaming'):
                    # Return streaming signal with metadata for frontend to handle
                    return {
                        "response": agent_result.get('response', ''),
                        "course_id": final_course_id,
                        "function_results": function_results,
                        "streaming": {
                            "type": "research_generation",
                            "course_id": research_result.get('course_id'),
                            "focus_area": research_result.get('focus_area')
                        }
                    }
            
            # Handle streaming signals for course design generation
            if 'course_design_generated' in function_results:
                design_result = function_results['course_design_generated']
                if design_result.get('streaming'):
                    # Return streaming signal with metadata for frontend to handle
                    return {
                        "response": agent_result.get('response', ''),
                        "course_id": final_course_id,
                        "function_results": function_results,
                        "streaming": {
                            "type": "course_design_generation",
                            "course_id": design_result.get('course_id'),
                            "focus": design_result.get('focus')
                        }
                    }
            
            # Handle streaming signals for course design modification
            if 'course_design_modified' in function_results:
                modify_result = function_results['course_design_modified']
                if modify_result.get('streaming'):
                    # Return streaming signal with metadata for frontend to handle
                    return {
                        "response": agent_result.get('response', ''),
                        "course_id": final_course_id,
                        "function_results": function_results,
                        "streaming": {
                            "type": "course_design_modification",
                            "course_id": modify_result.get('course_id'),
                            "modification_request": modify_result.get('modification_request')
                        }
                    }
            
            # Handle streaming signals for content structure generation
            if 'content_structure_generated' in function_results:
                content_result = function_results['content_structure_generated']
                if content_result.get('streaming'):
                    # Return streaming signal with metadata for frontend to handle
                    return {
                        "response": agent_result.get('response', ''),
                        "course_id": final_course_id,
                        "function_results": function_results,
                        "streaming": {
                            "type": "content_structure_generation",
                            "course_id": content_result.get('course_id'),
                            "focus": content_result.get('focus')
                        }
                    }
            
            # Handle streaming signals for content structure generation (from CourseStructureAgent)
            if 'structure_generated' in function_results:
                structure_result = function_results['structure_generated']
                if structure_result.get('streaming'):
                    # Auto-trigger the streaming endpoint for content structure generation
                    print(f"🎯 [ConversationOrchestrator] Auto-triggering content structure streaming for course: {structure_result.get('course_id')}")
                    
                    try:
                        # Get the CourseStructureAgent and call its streaming method directly
                        course_structure_agent = self.agent_coordinator.get_agent('course_structure')
                        if course_structure_agent:
                            # Create a streaming callback to emit events
                            async def streaming_callback(event_data):
                                # This would be handled by the streaming endpoint in a real implementation
                                # For now, we'll let the frontend handle the streaming call
                                pass
                            
                            # Return streaming signal with metadata for frontend to handle
                            return {
                                "response": agent_result.get('response', ''),
                                "course_id": final_course_id,
                                "function_results": function_results,
                                "streaming": {
                                    "type": "content_structure_generation",
                                    "course_id": structure_result.get('course_id'),
                                    "focus": None
                                }
                            }
                        else:
                            print(f"❌ [ConversationOrchestrator] CourseStructureAgent not found")
                            return {
                                "response": agent_result.get('response', ''),
                                "course_id": final_course_id,
                                "function_results": function_results
                            }
                    except Exception as e:
                        print(f"❌ [ConversationOrchestrator] Error in content structure streaming: {e}")
                        return {
                            "response": agent_result.get('response', ''),
                            "course_id": final_course_id,
                            "function_results": function_results
                        }
            
            # Handle streaming signals for content creation start
            if 'content_creation_started' in function_results:
                creation_result = function_results['content_creation_started']
                if creation_result.get('streaming'):
                    # Return streaming signal with metadata for frontend to handle
                    return {
                        "response": agent_result.get('response', ''),
                        "course_id": final_course_id,
                        "function_results": function_results,
                        "streaming": {
                            "type": "content_creation",
                            "course_id": creation_result.get('course_id'),
                            "batch_mode": creation_result.get('batch_mode', False)
                        }
                    }
                elif creation_result.get('auto_trigger') or creation_result.get('workflow_transition', {}).get('trigger_immediately'):
                    # CRITICAL FIX: Check if content generation has already been started to prevent duplicate generation
                    print(f"🚀 [ConversationOrchestrator] Auto-trigger detected for content creation!")
                    print(f"   📋 Next agent: {creation_result.get('next_agent', 'material_content_generator')}")
                    print(f"   🎬 Streaming: {creation_result.get('streaming', False)}")
                    print(f"   🆔 Material ID: {creation_result.get('material_id', 'None')}")
                    print(f"   📝 Material Title: {creation_result.get('material_title', 'None')}")
                    
                    # Check if the MaterialContentGeneratorAgent already generated content in this request
                    if 'content_generation_started' in function_results:
                        content_gen_result = function_results['content_generation_started']
                        if (content_gen_result.get('success') and 
                            content_gen_result.get('first_slide_generated') and 
                            content_gen_result.get('generated_material')):
                            print(f"✅ [ConversationOrchestrator] Content already generated in this request, skipping auto-trigger to prevent duplication")
                            
                            # Return the existing result without triggering again
                            return {
                                "response": agent_result.get('response', ''),
                                "course_id": final_course_id,
                                "function_results": function_results,
                                "auto_trigger": {
                                    "type": "content_creation",
                                    "course_id": final_course_id,
                                    "next_agent": creation_result.get('next_agent', 'material_content_generator'),
                                    "workflow_step": creation_result.get('workflow_step', 'content_generation'),
                                    "completed": True,
                                    "skipped_duplicate": True,
                                    "reason": "Content already generated in this request"
                                }
                            }
                    
                    # Actually trigger the MaterialContentGeneratorAgent only if content wasn't already generated
                    next_agent = creation_result.get('next_agent', 'material_content_generator')
                    
                    try:
                        print(f"🚀 [ConversationOrchestrator] Auto-triggering {next_agent}...")
                        
                        # Create a more specific message for the MaterialContentGeneratorAgent
                        material_id = creation_result.get('material_id')
                        material_title = creation_result.get('material_title', 'first material')
                        
                        if material_id:
                            trigger_message = f"Generate content for material {material_id}: {material_title}"
                        else:
                            trigger_message = "Start content generation for the first material"
                        
                        # Trigger content generation automatically with specific material info
                        content_generation_result = await self.agent_coordinator.route_to_agent(
                            next_agent, final_course_id, user_id, trigger_message
                        )
                        
                        print(f"✅ [ConversationOrchestrator] {next_agent} triggered successfully")
                        
                        # Check if content generation agent returned function results
                        content_function_results = content_generation_result.get('function_results', {})
                        
                        # Merge function results from both agents
                        merged_function_results = {**function_results, **content_function_results}
                        
                        # Return the content generation result with merged function results
                        return {
                            "response": content_generation_result.get('response', agent_result.get('response', '')),
                            "course_id": final_course_id,
                            "function_results": merged_function_results,
                            "auto_trigger": {
                                "type": "content_creation",
                                "course_id": final_course_id,
                                "next_agent": next_agent,
                                "workflow_step": creation_result.get('workflow_step', 'content_generation'),
                                "completed": True,
                                "triggered_agent_response": content_generation_result.get('response', ''),
                                "material_id": material_id,
                                "material_title": material_title
                            }
                        }
                        
                    except Exception as e:
                        print(f"❌ [ConversationOrchestrator] Failed to auto-trigger {next_agent}: {e}")
                        import traceback
                        print(f"Full traceback: {traceback.format_exc()}")
                        
                        # Return original result with error info
                        return {
                            "response": agent_result.get('response', ''),
                            "course_id": final_course_id,
                            "function_results": function_results,
                            "auto_trigger": {
                                "type": "content_creation",
                                "course_id": final_course_id,
                                "next_agent": next_agent,
                                "workflow_step": creation_result.get('workflow_step', 'content_generation'),
                                "error": str(e),
                                "completed": False
                            }
                        }
            
            # Handle automatic workflow transitions
            print(f"🔍 [ConversationOrchestrator] Checking for workflow transitions...")
            print(f"   📋 Agent result keys: {list(agent_result.keys())}")
            print(f"   🔄 Workflow transition: {agent_result.get('workflow_transition', 'None')}")
            
            if agent_result.get('workflow_transition', {}).get('trigger_automatically'):
                print(f"🎯 [ConversationOrchestrator] Automatic workflow transition detected!")
                workflow_transition = agent_result['workflow_transition']
                next_agent = workflow_transition.get('next_agent')
                next_step = workflow_transition.get('next_step')
                
                print(f"   🔄 Next step: {next_step}")
                print(f"   🤖 Next agent: {next_agent}")
                print(f"   📋 Registered agents: {list(self.agent_coordinator.get_registered_agents().keys())}")
                
                # Check if we should automatically trigger the next agent
                if next_agent == 'course_structure' and next_step == 'content_structure_generation':
                    print(f"🚀 [ConversationOrchestrator] Auto-triggering CourseStructureAgent...")
                    
                    # Trigger content structure generation automatically
                    try:
                        course_structure_result = await self.agent_coordinator.route_to_agent(
                            'course_structure', final_course_id, user_id, 'start content structure generation'
                        )
                        
                        print(f"✅ [ConversationOrchestrator] CourseStructureAgent triggered successfully")
                        
                        # Check if course structure agent returned streaming signal
                        content_function_results = course_structure_result.get('function_results', {})
                        if 'structure_generated' in content_function_results:
                            content_result = content_function_results['structure_generated']
                            if content_result.get('streaming'):
                                print(f"🎬 [ConversationOrchestrator] CourseStructureAgent returned streaming signal")
                                # Return streaming signal for content structure generation
                                return {
                                    "response": course_structure_result.get('response', ''),
                                    "course_id": final_course_id,
                                    "function_results": content_function_results,
                                    "streaming": {
                                        "type": "content_structure_generation",
                                        "course_id": content_result.get('course_id'),
                                        "focus": None
                                    },
                                    "workflow_transition": {
                                        "from_agent": "course_design",
                                        "to_agent": "course_structure",
                                        "automatic": True
                                    }
                                }
                        
                        # If no streaming, return the course structure result
                        return {
                            "response": course_structure_result.get('response', ''),
                            "course_id": final_course_id,
                            "function_results": content_function_results,
                            "workflow_transition": {
                                "from_agent": "course_design",
                                "to_agent": "course_structure",
                                "automatic": True,
                                "completed": True
                            }
                        }
                        
                    except Exception as e:
                        print(f"❌ [ConversationOrchestrator] Failed to auto-trigger CourseStructureAgent: {e}")
                        import traceback
                        print(f"Full traceback: {traceback.format_exc()}")
                        
                        # Return original result with error info
                        return {
                            "response": agent_result.get('response', ''),
                            "course_id": final_course_id,
                            "function_results": function_results,
                            "workflow_transition": {
                                "from_agent": "course_design",
                                "to_agent": "course_structure",
                                "automatic": True,
                                "error": str(e)
                            }
                        }
            
            # Use agent's response directly - agents handle their own message storage
            final_response = agent_result.get('response', '')
            
            if not final_response:
                # Only generate orchestrator response if agent didn't provide one
                final_response = await self._generate_conversational_response(
                    user_message, agent_result, context, intent_result
                )
                
                # Store the orchestrator response if we generated one
                if final_course_id:
                    await self.message_service.store_message(
                        final_course_id, user_id, final_response, "assistant", 
                        agent_result.get('function_results', {})
                    )
            
            # Update context summary if needed
            if course_id and await self.message_service.should_update_context_summary(
                course_id, agent_result.get('function_results', {})
            ):
                await self.context_service.update_context_summary(course_id)
            
            return {
                "response": final_response,
                "course_id": agent_result.get('course_id', course_id),
                "function_results": agent_result.get('function_results', {}),
                "intent": intent_result
            }
            
        except Exception as e:
            print(f"ConversationOrchestrator error: {e}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            
            return {
                "response": "I apologize, but I'm experiencing some technical difficulties. Please try again in a moment.",
                "course_id": course_id,
                "function_results": {},
                "error": str(e)
            }
    
    async def _handle_general_conversation(self, user_message: str, context: Dict[str, Any], 
                                         course_id: Optional[str], user_id: str) -> Dict[str, Any]:
        """Handle general conversation that doesn't require agents"""
        
        # Check if user is asking about course creation capabilities
        if any(word in user_message.lower() for word in ['help', 'what', 'how', 'can you']):
            response = await self._generate_helpful_response(user_message, context)
        else:
            # Polite redirect to course creation
            response = await self._generate_redirect_response(user_message, context)
        
        return {
            "response": response,
            "course_id": course_id,
            "function_results": {}
        }
    
    async def _generate_conversational_response(self, user_message: str, agent_result: Dict[str, Any], 
                                              context: Dict[str, Any], intent_result: Dict[str, Any]) -> str:
        """Generate natural conversational response using AI"""
        
        # If agent already provided a good response, use it
        agent_response = agent_result.get('response', '')
        if agent_response and len(agent_response) > 50:  # Substantial response
            return agent_response
        
        # Generate enhanced conversational response
        function_results = agent_result.get('function_results', {})
        course_state = context.get('course_state', {})
        
        system_prompt = f"""You are a friendly Course Creation Assistant. Generate a natural, helpful response.

User said: "{user_message}"
Intent: {intent_result.get('reasoning', 'General request')}
Agent executed: {function_results}
Current course: {course_state.get('name', 'No course yet')}
Current step: {context.get('current_step', 'Getting started')}

Generate a response that:
1. Acknowledges what the user wanted
2. Explains what was accomplished (if anything)
3. Guides them to the next logical step
4. Maintains conversational flow
5. Is warm, helpful, and educational

Be concise but informative. Don't repeat the user's exact words."""
        
        try:
            client = await self.openai_service.get_client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_completion_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Failed to generate conversational response: {e}")
            # Fallback to agent response or default
            return agent_response or "I'm here to help you create courses. What would you like to work on?"
    
    async def _generate_helpful_response(self, user_message: str, context: Dict[str, Any]) -> str:
        """Generate helpful response for capability questions"""
        
        course_state = context.get('course_state', {})
        current_step = context.get('current_step', 'getting_started')
        
        help_prompt = f"""You are a Course Creation Assistant. The user is asking for help or information.

User question: "{user_message}"
Current context: {course_state.get('name', 'No course yet')} at step {current_step}

Provide a helpful response that explains:
1. What you can help with (course creation, curriculum generation, content management)
2. Current status of their course (if any)
3. Next steps they can take
4. Be encouraging and specific

Keep it concise and actionable."""
        
        try:
            client = await self.openai_service.get_client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": help_prompt}],
                max_completion_tokens=200
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Failed to generate help response: {e}")
            return "I'm here to help you create courses! I can help you set up courses, generate curricula, and manage content. What would you like to work on?"
    
    async def _generate_redirect_response(self, user_message: str, context: Dict[str, Any]) -> str:
        """Generate polite redirect response for off-topic requests"""
        
        course_state = context.get('course_state', {})
        
        redirect_prompt = f"""The user said something off-topic: "{user_message}"
Current course context: {course_state.get('name', 'No course yet')}

Generate a polite redirect that:
1. Acknowledges their message briefly
2. Redirects to course creation capabilities
3. Suggests a specific next step
4. Is friendly and helpful

Keep it short and natural."""
        
        try:
            client = await self.openai_service.get_client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": redirect_prompt}],
                max_completion_tokens=150
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Failed to generate redirect response: {e}")
            return "I'm focused on helping you create and manage courses. Is there anything you'd like to work on with your course creation?"
    
    async def update_context_summary(self, course_id: str):
        """Manually trigger context summary update"""
        await self.context_service.update_context_summary(course_id)
    
    async def get_conversation_context(self, course_id: Optional[str], user_id: str) -> Dict[str, Any]:
        """Get conversation context for external use"""
        return await self.context_service.get_conversation_context(course_id, user_id)
    
    async def _should_send_welcome_message(self, course_id: Optional[str], user_id: str) -> bool:
        """Check if we should send a welcome message (first message in conversation)"""
        if not course_id:
            # No course ID means this is the very first interaction
            return True
        
        # Check if there are any messages in this course
        message_count = await self.message_service.get_message_count(course_id)
        return message_count == 0
    
    async def _send_welcome_message(self, course_id: Optional[str], user_id: str) -> Dict[str, Any]:
        """Send the welcome message as the agent's first message"""
        welcome_content = """👋 **Welcome to Course Creation Copilot!**

I'll help you create comprehensive course content including:

- Curriculum structure
- Pedagogy strategies  
- Assessment frameworks

**Let's start:** What would you like to name your course?"""
        
        # If no course ID, we need to create a draft course first
        if not course_id:
            try:
                from ...database import get_database
                from datetime import datetime
                from bson import ObjectId
                
                db = await get_database()
                
                # Create draft course
                course_data = {
                    "name": "Untitled Course",
                    "description": "",
                    "user_id": ObjectId(user_id),
                    "structure": {},
                    "status": "draft",
                    "workflow_step": "course_naming",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                result = await db.courses.insert_one(course_data)
                course_id = str(result.inserted_id)
                
                # Create chat session
                session_data = {
                    "course_id": ObjectId(course_id),
                    "user_id": ObjectId(user_id),
                    "context_summary": "",
                    "last_activity": datetime.utcnow(),
                    "total_messages": 0,
                    "context_window_start": 0
                }
                
                await db.chat_sessions.insert_one(session_data)
                
            except Exception as e:
                print(f"Failed to create draft course for welcome message: {e}")
                return {
                    "response": welcome_content,
                    "course_id": None,
                    "function_results": {}
                }
        
        # Store the welcome message
        try:
            await self.message_service.store_message(course_id, user_id, welcome_content, "assistant")
        except Exception as e:
            print(f"Failed to store welcome message: {e}")
        
        return {
            "response": welcome_content,
            "course_id": course_id,
            "function_results": {}
        }

    def _get_material_file_path_from_material(self, material: Dict[str, Any], targeted_slide: Dict[str, Any]) -> str:
        """Generate the file path for a material based on its structure and targeted slide"""
        try:
            # CRITICAL FIX: Get the actual material structure from the database if needed
            # The material passed here might not have all the structure info
            
            # Extract module and chapter information from the material or targeted slide
            module_number = targeted_slide.get('module_number') if targeted_slide else None
            chapter_number = targeted_slide.get('chapter_number') if targeted_slide else None
            slide_number = targeted_slide.get('slide_number') if targeted_slide else None
            
            # If not in targeted_slide or targeted_slide is empty, extract from material directly
            if not module_number or not chapter_number:
                # First try to get from material properties directly
                module_number = material.get('module_number')
                chapter_number = material.get('chapter_number')
                slide_number = material.get('slide_number')
                
                # CRITICAL FIX: If we still don't have the info, try to get it from the R2 key
                if not module_number or not chapter_number:
                    r2_key = material.get('r2_key', '')
                    if r2_key:
                        # Parse R2 key format: "courses/.../content/module_1_chapter_2_3_understanding..."
                        import re
                        match = re.search(r'module_(\d+)_chapter_(\d+)_(\d+)', r2_key)
                        if match:
                            module_number = int(match.group(1))
                            chapter_number = int(match.group(2))
                            slide_number = int(match.group(3))
                            print(f"🔍 [ConversationOrchestrator] Extracted from R2 key: Module {module_number}, Chapter {chapter_number}, Slide {slide_number}")
                
                # If still not found, try to parse from material title
                if not module_number or not chapter_number:
                    title = material.get('title', '')
                    if 'Module' in title and 'Chapter' in title:
                        # Parse "Module X Chapter Y - Title" format
                        import re
                        match = re.search(r'Module\s+(\d+).*?Chapter\s+(\d+)', title)
                        if match:
                            module_number = int(match.group(1))
                            chapter_number = int(match.group(2))
                    
                    # Fallback to material structure if available
                    if not module_number or not chapter_number:
                        structure = material.get('structure', {})
                        module_number = structure.get('module_number')
                        chapter_number = structure.get('chapter_number')
                        slide_number = structure.get('slide_number')
            
            # If we still don't have valid numbers, log the issue but continue with fallbacks
            if not module_number or not chapter_number:
                print(f"⚠️ [ConversationOrchestrator] Could not determine module/chapter numbers from material: {material.get('title', 'Unknown')}")
                print(f"   📋 Available material keys: {list(material.keys())}")
                print(f"   📋 R2 key: {material.get('r2_key', 'None')}")
            
            # Ensure we have valid numbers with proper fallbacks
            module_number = module_number or 1
            chapter_number = chapter_number or 1
            slide_number = slide_number or 1
            
            # Generate the file path in the format expected by the frontend
            # Format: "Module X/Chapter Y/Slide Z.md"
            file_path = f"Module {module_number}/Chapter {chapter_number}/Slide {slide_number}.md"
            
            print(f"🗂️ [ConversationOrchestrator] Generated file path: {file_path}")
            print(f"   📋 Material: {material.get('title', 'Unknown')}")
            print(f"   📍 Module: {module_number}, Chapter: {chapter_number}, Slide: {slide_number}")
            
            return file_path
            
        except Exception as e:
            print(f"❌ [ConversationOrchestrator] Error generating file path: {e}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            # Fallback to a default path
            return "Module 1/Chapter 1/Slide 1.md"

    def _get_storage_path_from_material(self, material: Dict[str, Any], targeted_slide: Dict[str, Any]) -> str:
        """Generate the storage path that matches the course file store structure"""
        try:
            # CRITICAL FIX: Instead of trying to generate a path, use the materialId to find the existing file
            # The frontend course file store already has the correct paths for all materials
            
            # For streaming events, we should use a generic path that the frontend can map to the correct file
            # using the materialId. The frontend will handle the path mapping in handleContentMaterialEvent.
            
            # Extract basic info for logging
            module_number = material.get('module_number', 1)
            chapter_number = material.get('chapter_number', 1) 
            slide_number = material.get('slide_number', 1)
            title = material.get('title', 'Unknown')
            material_id = material.get('id')
            
            # CRITICAL: Use a consistent path format that the frontend can recognize
            # The frontend will use materialId to find and update the correct existing file
            # This path is just for the streaming event - the frontend will map it to the actual file
            
            # Use the EXACT same sanitization logic as courseFileStore to ensure consistency
            # This matches the sanitizeFileName function in frontend/src/lib/courseFileStore.ts
            import re
            
            # Python equivalent of the JavaScript sanitization logic
            sanitized_title = re.sub(r'[^a-z0-9\s-]', '', title.lower())  # Remove special characters
            sanitized_title = re.sub(r'\s+', '-', sanitized_title)        # Replace spaces with hyphens
            sanitized_title = re.sub(r'-+', '-', sanitized_title)         # Replace multiple hyphens with single
            sanitized_title = sanitized_title.strip('-')                  # Remove leading/trailing hyphens
            sanitized_title = sanitized_title[:50]                        # Limit length
            
            # Generate path that matches courseFileStore.loadContentMaterials() format exactly
            # This MUST match the path generation in courseFileStore.loadContentMaterials()
            storage_path = f"/content/module-{module_number}/chapter-{module_number}-{chapter_number}/{sanitized_title}.md"
            
            print(f"🗂️ [ConversationOrchestrator] Generated storage path: {storage_path}")
            print(f"   📋 Material: {title}")
            print(f"   📍 Module: {module_number}, Chapter: {chapter_number}, Slide: {slide_number}")
            print(f"   🆔 Material ID: {material_id}")
            
            return storage_path
            
        except Exception as e:
            print(f"❌ [ConversationOrchestrator] Error generating storage path: {e}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            # Fallback to a default storage path
            return "/content/module-1/chapter-1-1/unknown.md"

    async def close_clients(self):
        """Close all service clients"""
        await self.openai_service.close_client()
