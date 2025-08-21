from typing import Dict, Any, Optional, List
import json

from ...infrastructure.ai.openai_service import OpenAIService


class IntentService:
    """Pure LLM-powered intent classification and workflow decision service"""
    
    def __init__(self, openai_service: OpenAIService):
        self.openai = openai_service
        self.model = "gpt-4o-mini"
    
    async def analyze_request(self, user_message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user request using pure LLM intelligence"""
        return await self._ai_analyze_request(user_message, context)
    
    async def _ai_analyze_request(self, user_message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to analyze all user requests with comprehensive context understanding"""
        
        course_state = context.get('course_state', {})
        course_name = course_state.get('name', 'Untitled Course')
        workflow_step = context.get('current_step', 'course_naming')
        recent_messages = context.get('recent_messages', [])
        
        # Build conversation history for better context
        conversation_context = ""
        if recent_messages:
            conversation_context = "\n".join([
                f"- {msg.get('role', 'unknown')}: {msg.get('content', '')[:100]}..."
                for msg in recent_messages[-3:]  # Last 3 messages for context
            ])
        
        analysis_prompt = f"""You are an intelligent intent classifier for a course creation system. Analyze the user's message and determine the complete routing decision based on context.

CURRENT CONTEXT:
- Course Name: "{course_name}"
- Current Workflow Step: {workflow_step}
- Course Status: {course_state.get('status', 'draft')}
- Workflow Step: {course_state.get('workflow_step', 'course_naming')}
- Available Files:
  * Research: {"✅ Available" if course_state.get('research_public_url') or course_state.get('research_r2_key') else "❌ Missing"}
  * Course Design: {"✅ Available" if course_state.get('course_design_public_url') or course_state.get('curriculum_public_url') or course_state.get('course_design_r2_key') or course_state.get('curriculum_r2_key') else "❌ Missing"}
  * Content Structure: {"✅ Available" if course_state.get('structure') and course_state.get('structure') != {} else "❌ Missing"}

RECENT CONVERSATION:
{conversation_context if conversation_context else "No recent conversation"}

USER MESSAGE: "{user_message}"

SYSTEM CAPABILITIES:

Available Workflow Actions:
1. START_NEW_WORKFLOW - User wants to create something completely new
2. JUMP_TO_STEP - User wants to modify/update a specific part of existing workflow
3. CONTINUE_CURRENT - User is responding to continue the current workflow step
4. GENERAL_CONVERSATION - General chat, questions, or non-workflow requests

Available Workflows:
- course_creation: Complete course creation workflow
  Steps: course_naming → initial_research → course_design_method_selection → course_design_generation → content_structure_generation → content_structure_approval → content_creation

Available Agents:
- course_creation: Handles course setup, naming, basic course management, initial course creation
- initial_research: Handles comprehensive research and web search for course topics
- course_design: Handles curriculum generation, pedagogy planning, assessment creation (formerly curriculum agent)
- course_structure: Handles content structure generation, material organization, and content creation workflow
- material_content_generator: Handles detailed study material content generation for slides and assessments, supports both sequential workflow and natural language targeting

ANALYSIS GUIDELINES:

1. **CRITICAL: Approval Context Handling**:
   - If current workflow step is "content_structure_approval" or similar AND user message contains "approve", "proceed", "approve and proceed", "start content creation" → JUMP_TO_STEP to content_creation with course_structure agent
   - If user says "modify structure", "modify", "change structure" when in approval context → JUMP_TO_STEP to content_structure_generation with course_structure agent
   - Approval messages should NEVER be classified as structure generation unless explicitly asking to modify

2. **Course Names/Titles**: If user provides what looks like a course title (e.g., "Introduction to RAG", "Python Basics", "Machine Learning 101"), this usually means:
   - If no course exists or course is "Untitled Course" → JUMP_TO_STEP to course_naming with course_creation agent
   - If course already has a name → User wants to rename, so JUMP_TO_STEP to course_naming

3. **Course Design Requests**: Keywords like "curriculum", "syllabus", "modules", "lessons", "pedagogy", "assessment", "course content" → JUMP_TO_STEP to initial_research with initial_research agent

4. **Context-Aware "Generate for me"**: The phrase "generate for me" should be interpreted based on current workflow context:
   - If research exists but no course design → JUMP_TO_STEP to course_design_generation with course_design agent
   - If no research exists → JUMP_TO_STEP to initial_research with initial_research agent
   - If course design exists → JUMP_TO_STEP to content_creation with course_structure agent

5. **Content Creation Requests**: Keywords like "content creation", "start content creation", "create content", "material creation", "material generation", "course material generation" → JUMP_TO_STEP to content_creation with material_content_generator agent

6. **Structure Generation Requests**: Keywords like "content structure", "generate structure", "create structure" (but NOT when in approval context) → JUMP_TO_STEP to content_structure_generation with course_structure agent

7. **Slide Creation Requests**: Keywords like "slide creation", "start slide creation", "create slides", "generate slides", "slide content", "individual slides" → JUMP_TO_STEP to content_creation with course_structure agent (Note: CourseStructureAgent will handle the workflow and delegate to SlidesAgent when appropriate)

8. **Continuation Responses**: "Yes", "Sure", "Okay", "Go ahead", "Continue" → CONTINUE_CURRENT with current agent

9. **New Course Requests**: "Create new course", "Start over", "New course" → START_NEW_WORKFLOW

10. **Context Awareness**: Consider the conversation flow, current workflow step, and available files to make intelligent routing decisions

CONFIDENCE SCORING:
- high: Very clear intent, specific keywords, or obvious context
- medium: Somewhat clear but could have multiple interpretations
- low: Ambiguous, unclear, or requires more context

Respond with JSON only (no markdown, no extra text):
{{
    "category": "workflow_request|general_query",
    "workflow_action": "START_NEW_WORKFLOW|JUMP_TO_STEP|CONTINUE_CURRENT|null",
    "target_workflow": "course_creation|null",
    "target_step": "course_naming|initial_research|course_design_method_selection|course_design_generation|content_structure_generation|content_structure_approval|content_creation|null",
    "target_agent": "course_creation|initial_research|course_design|course_structure|material_content_generator",
    "confidence": "high|medium|low",
    "reasoning": "Detailed explanation of why you made this decision, including what specific indicators led to this classification"
}}"""

        try:
            print(f"\n{'='*60}")
            print(f"🔄 \033[96m[IntentService]\033[0m \033[1mSending request to OpenAI...\033[0m")
            print(f"   📝 Model: \033[93m{self.model}\033[0m")
            print(f"   📝 User Message: \033[92m'{user_message}'\033[0m")
            print(f"   📝 Prompt Preview: \033[90m{analysis_prompt[:200]}...\033[0m")
            print(f"{'='*60}")
            
            client = await self.openai.get_client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.1,
                max_tokens=400
            )
            
            result = response.choices[0].message.content.strip()
            
            print(f"\n✅ \033[96m[IntentService]\033[0m \033[1m\033[92mOpenAI Response received\033[0m")
            print(f"   💰 Tokens used: \033[93m{response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}\033[0m")
            print(f"   📄 Raw response:")
            print(f"   \033[90m{'-'*50}\033[0m")
            
            # Pretty print JSON if it's valid JSON
            try:
                parsed_json = json.loads(result)
                formatted_json = json.dumps(parsed_json, indent=2)
                for line in formatted_json.split('\n'):
                    print(f"   \033[94m{line}\033[0m")
            except:
                # If not JSON, just print normally
                for line in result.split('\n'):
                    print(f"   \033[94m{line}\033[0m")
            
            print(f"   \033[90m{'-'*50}\033[0m")
            
            # Clean up the response - remove any markdown formatting
            if result.startswith('```json'):
                result = result.replace('```json', '').replace('```', '').strip()
            elif result.startswith('```'):
                result = result.replace('```', '').strip()
            
            # Try to extract JSON if it's embedded in text
            if '{' in result and '}' in result:
                start = result.find('{')
                end = result.rfind('}') + 1
                result = result[start:end]
            
            parsed_result = json.loads(result)
            
            # Validate and ensure required fields
            parsed_result = self._validate_and_enhance_result(parsed_result, user_message, context)
            
            return parsed_result
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse AI intent analysis JSON: {e}")
            print(f"Raw response: {result}")
            return self._fallback_analysis(user_message, context)
        except Exception as e:
            print(f"AI intent analysis error: {e}")
            return self._fallback_analysis(user_message, context)
    
    def _validate_and_enhance_result(self, result: Dict[str, Any], user_message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance the AI result with required fields and logic checks"""
        
        # Ensure required fields exist
        if 'category' not in result:
            result['category'] = 'general_query'
        if 'confidence' not in result:
            result['confidence'] = 'medium'
        if 'reasoning' not in result:
            result['reasoning'] = 'AI analysis completed'
        
        # CRITICAL: Override AI decision for approval messages in approval context
        workflow_step = context.get('current_step', 'course_naming')
        message_lower = user_message.lower()
        
        # Force correct routing for approval messages
        if ('content_structure_approval' in workflow_step or 'approval' in workflow_step):
            if any(word in message_lower for word in ['approve', 'proceed', 'approve and proceed', 'start content creation']):
                result.update({
                    'category': 'workflow_request',
                    'workflow_action': 'JUMP_TO_STEP',
                    'target_workflow': 'course_creation',
                    'target_step': 'content_creation',
                    'target_agent': 'course_structure',  # ✅ Fixed: Route to course_structure first to process approval, then auto-trigger content generation
                    'confidence': 'high',
                    'reasoning': 'Validation override - detected approval message in structure approval context, routing to course_structure to process approval and start content creation'
                })
                return result
            elif any(word in message_lower for word in ['modify', 'change', 'modify structure', 'change structure']):
                result.update({
                    'category': 'workflow_request',
                    'workflow_action': 'JUMP_TO_STEP',
                    'target_workflow': 'course_creation',
                    'target_step': 'content_structure_generation',
                    'target_agent': 'course_structure',
                    'confidence': 'high',
                    'reasoning': 'Validation override - detected modification request in structure approval context, forcing structure generation routing'
                })
                return result
        
        # CRITICAL FIX: Handle material content approval messages (approve and continue to next slide/material)
        if any(phrase in message_lower for phrase in [
            'approve and continue to next slide',
            'approve and continue to next material', 
            'approve & continue to next slide',
            'approve & continue to next material',
            'approve and continue',
            'approve & continue'
        ]):
            result.update({
                'category': 'workflow_request',
                'workflow_action': 'JUMP_TO_STEP',
                'target_workflow': 'course_creation',
                'target_step': 'content_creation',
                'target_agent': 'material_content_generator',  # ✅ Route to material_content_generator for material approval
                'confidence': 'high',
                'reasoning': 'Validation override - detected material content approval message (approve and continue to next slide), routing to material_content_generator'
            })
            return result
        
        # General approval message override (regardless of context)
        if any(phrase in message_lower for phrase in ['approve and proceed with content creation', 'start content creation', 'proceed with content creation']):
            result.update({
                'category': 'workflow_request',
                'workflow_action': 'JUMP_TO_STEP',
                'target_workflow': 'course_creation',
                'target_step': 'content_creation',
                'target_agent': 'course_structure',  # ✅ Fixed: Route to course_structure first to process approval, then auto-trigger content generation
                'confidence': 'high',
                'reasoning': 'Validation override - detected explicit content creation approval message, routing to course_structure to process approval and start content creation'
            })
            return result
        
        # CRITICAL FIX: Handle material generation requests explicitly
        if any(phrase in message_lower for phrase in [
            'start course material generation',
            'start material generation',
            'generate course materials',
            'begin material generation',
            'start generating materials'
        ]):
            result.update({
                'category': 'workflow_request',
                'workflow_action': 'JUMP_TO_STEP',
                'target_workflow': 'course_creation',
                'target_step': 'content_creation',
                'target_agent': 'material_content_generator',
                'confidence': 'high',
                'reasoning': 'Validation override - detected material generation request, routing to material_content_generator'
            })
            return result
        
        # CRITICAL FIX: Override AI routing for content_creation step - should always go to material_content_generator
        if (result.get('target_step') == 'content_creation' and 
            result.get('target_agent') == 'course_structure' and
            any(word in message_lower for word in ['approve', 'continue', 'next', 'slide', 'material'])):
            result.update({
                'target_agent': 'material_content_generator',
                'reasoning': result.get('reasoning', '') + ' [OVERRIDE: content_creation step should use material_content_generator, not course_structure]'
            })
        
        # Natural language slide targeting patterns
        slide_patterns = [
            r'generate.*slide\s+\d+.*of.*chapter\s+\d+',
            r'create.*content.*for.*slide\s+\d+',
            r'edit.*slide\s+\d+.*of.*chapter',
            r'generate.*material.*for.*slide\s+\d+',
            r'modify.*slide\s+\d+',
            r'generate.*assessment\s+\d+',
            r'create.*quiz.*for.*module\s+\d+',
            r'edit.*assessment.*of.*chapter'
        ]
        
        import re
        for pattern in slide_patterns:
            if re.search(pattern, message_lower):
                result.update({
                    'category': 'workflow_request',
                    'workflow_action': 'JUMP_TO_STEP',
                    'target_workflow': 'course_creation',
                    'target_step': 'content_creation',
                    'target_agent': 'material_content_generator',
                    'confidence': 'high',
                    'reasoning': f'Validation override - detected natural language slide targeting pattern: {pattern}'
                })
                return result
        
        # Ensure target_agent is set for workflow requests
        if result.get('category') == 'workflow_request' and not result.get('target_agent'):
            # Default agent selection logic
            if 'curriculum' in user_message.lower() or 'syllabus' in user_message.lower():
                result['target_agent'] = 'course_design'
            else:
                result['target_agent'] = 'course_creation'
        
        # Validate workflow consistency
        if result.get('workflow_action') == 'JUMP_TO_STEP' and not result.get('target_step'):
            # Infer target step based on content
            if any(word in message_lower for word in ['curriculum', 'syllabus', 'modules', 'lessons', 'pedagogy', 'assessment', 'generate']):
                result['target_step'] = 'initial_research'
                result['target_agent'] = 'initial_research'
            else:
                result['target_step'] = 'course_naming'
                result['target_agent'] = 'course_creation'
        
        # Set target_workflow for workflow requests
        if result.get('category') == 'workflow_request' and not result.get('target_workflow'):
            result['target_workflow'] = 'course_creation'
        
        return result
    
    def _fallback_analysis(self, user_message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback analysis when AI fails - simple heuristic-based classification"""
        
        message_lower = user_message.lower()
        workflow_step = context.get('current_step', 'course_naming')
        
        # CRITICAL: Handle approval messages in structure approval context
        if ('content_structure_approval' in workflow_step or 'approval' in workflow_step) and any(word in message_lower for word in ['approve', 'proceed', 'approve and proceed', 'start content creation']):
            return {
                'category': 'workflow_request',
                'workflow_action': 'JUMP_TO_STEP',
                'target_workflow': 'course_creation',
                'target_step': 'content_creation',
                'target_agent': 'course_structure',  # ✅ Fixed: Route to course_structure first to process approval, then auto-trigger content generation
                'confidence': 'high',
                'reasoning': 'Fallback analysis - detected approval message in structure approval context, routing to course_structure to process approval and start content creation'
            }
        
        # Handle modification requests in approval context
        if ('content_structure_approval' in workflow_step or 'approval' in workflow_step) and any(word in message_lower for word in ['modify', 'change', 'modify structure', 'change structure']):
            return {
                'category': 'workflow_request',
                'workflow_action': 'JUMP_TO_STEP',
                'target_workflow': 'course_creation',
                'target_step': 'content_structure_generation',
                'target_agent': 'course_structure',
                'confidence': 'high',
                'reasoning': 'Fallback analysis - detected modification request in structure approval context, routing to structure generation'
            }
        
        # General approval messages (when not in specific approval context)
        if any(word in message_lower for word in ['approve and proceed with content creation', 'start content creation', 'proceed with content creation']):
            return {
                'category': 'workflow_request',
                'workflow_action': 'JUMP_TO_STEP',
                'target_workflow': 'course_creation',
                'target_step': 'content_creation',
                'target_agent': 'course_structure',  # ✅ Fixed: Route to course_structure first to process approval, then auto-trigger content generation
                'confidence': 'high',
                'reasoning': 'Fallback analysis - detected explicit content creation approval message, routing to course_structure to process approval and start content creation'
            }
        
        # Natural language slide targeting patterns (fallback)
        slide_patterns = [
            r'generate.*slide\s+\d+.*of.*chapter\s+\d+',
            r'create.*content.*for.*slide\s+\d+',
            r'edit.*slide\s+\d+.*of.*chapter',
            r'generate.*material.*for.*slide\s+\d+',
            r'modify.*slide\s+\d+',
            r'generate.*assessment\s+\d+',
            r'create.*quiz.*for.*module\s+\d+',
            r'edit.*assessment.*of.*chapter'
        ]
        
        import re
        for pattern in slide_patterns:
            if re.search(pattern, message_lower):
                return {
                    'category': 'workflow_request',
                    'workflow_action': 'JUMP_TO_STEP',
                    'target_workflow': 'course_creation',
                    'target_step': 'content_creation',
                    'target_agent': 'material_content_generator',
                    'confidence': 'high',
                    'reasoning': f'Fallback analysis - detected natural language slide targeting pattern: {pattern}'
                }
        
        # Simple heuristics for common cases
        if any(word in message_lower for word in ['curriculum', 'syllabus', 'modules', 'lessons', 'pedagogy', 'assessment']) and 'generate' in message_lower:
            return {
                'category': 'workflow_request',
                'workflow_action': 'JUMP_TO_STEP',
                'target_workflow': 'course_creation',
                'target_step': 'initial_research',
                'target_agent': 'initial_research',
                'confidence': 'low',
                'reasoning': 'Fallback analysis - detected course design keywords'
            }
        
        # Content creation requests
        if any(word in message_lower for word in ['content creation', 'start content', 'create content', 'material creation']):
            return {
                'category': 'workflow_request',
                'workflow_action': 'JUMP_TO_STEP',
                'target_workflow': 'course_creation',
                'target_step': 'content_creation',
                'target_agent': 'course_structure',
                'confidence': 'medium',
                'reasoning': 'Fallback analysis - detected content creation keywords'
            }
        
        # Structure generation requests (but not in approval context)
        if any(word in message_lower for word in ['content structure', 'generate structure', 'create structure']) and 'approval' not in workflow_step:
            return {
                'category': 'workflow_request',
                'workflow_action': 'JUMP_TO_STEP',
                'target_workflow': 'course_creation',
                'target_step': 'content_structure_generation',
                'target_agent': 'course_structure',
                'confidence': 'medium',
                'reasoning': 'Fallback analysis - detected structure generation keywords'
            }
        
        # Slide creation requests
        if any(word in message_lower for word in ['slide creation', 'start slide', 'create slides', 'generate slides', 'slide content', 'individual slides']):
            return {
                'category': 'workflow_request',
                'workflow_action': 'JUMP_TO_STEP',
                'target_workflow': 'course_creation',
                'target_step': 'content_creation',
                'target_agent': 'course_structure',
                'confidence': 'medium',
                'reasoning': 'Fallback analysis - detected slide creation keywords, routing to course_structure for proper workflow'
            }
        
        # Check if it looks like a course name (multiple words, not a question)
        words = user_message.strip().split()
        if len(words) >= 2 and not any(word in message_lower for word in ['what', 'how', 'when', 'where', 'why', 'who', '?']):
            return {
                'category': 'workflow_request',
                'workflow_action': 'JUMP_TO_STEP',
                'target_workflow': 'course_creation',
                'target_step': 'course_naming',
                'target_agent': 'course_creation',
                'confidence': 'low',
                'reasoning': 'Fallback analysis - appears to be a course name'
            }
        
        # Default to general conversation
        return {
            'category': 'general_query',
            'workflow_action': None,
            'target_workflow': None,
            'target_step': None,
            'target_agent': 'course_creation',
            'confidence': 'low',
            'reasoning': 'Fallback analysis - treating as general conversation'
        }
    
    def determine_agent_from_intent(self, intent_result: Dict[str, Any]) -> str:
        """Determine which agent should handle the request"""
        if 'target_agent' in intent_result and intent_result['target_agent']:
            return intent_result['target_agent']
        
        # Fallback logic based on workflow and step
        workflow = intent_result.get('target_workflow', '')
        step = intent_result.get('target_step', '')
        
        if 'course_design' in step or 'curriculum' in step:
            return 'course_design'
        else:
            return 'course_creation'
