from typing import Dict, Any, Optional

from .workflow_state_service import WorkflowStateService


class AgentCoordinator:
    """Coordinates agent execution and workflow state updates"""
    
    def __init__(self, workflow_state_service: WorkflowStateService):
        self.workflow_state = workflow_state_service
        self.agents = {}
    
    def register_agent(self, agent_name: str, agent_instance):
        """Register an agent with the coordinator"""
        self.agents[agent_name] = agent_instance
    
    def get_agent(self, agent_name: str):
        """Get an agent instance"""
        return self.agents.get(agent_name)
    
    async def execute_with_agent(self, intent_result: Dict[str, Any], course_id: Optional[str], user_id: str, user_message: str) -> Dict[str, Any]:
        """Execute request with appropriate agent and manage workflow state"""
        
        # Determine which agent to use
        agent_name = intent_result.get('target_agent', 'course_creation')
        agent = self.get_agent(agent_name)
        
        if not agent:
            return {
                "response": f"Agent '{agent_name}' not found. Please try again.",
                "course_id": course_id,
                "function_results": {},
                "error": f"Agent not registered: {agent_name}"
            }
        
        # Handle workflow state updates based on intent
        if intent_result.get('category') == 'workflow_request':
            await self._handle_workflow_state_updates(intent_result, course_id)
        
        # Execute with the agent
        try:
            # Check if agent supports intent information (CourseCreationAgent does)
            if hasattr(agent, 'process_message') and agent_name == 'course_creation':
                result = await agent.process_message(course_id, user_id, user_message, intent_result)
            else:
                result = await agent.process_message(course_id, user_id, user_message)
            
            # Update workflow state after successful agent execution
            if intent_result.get('category') == 'workflow_request' and result.get('function_results'):
                await self._update_workflow_after_execution(intent_result, course_id, result)
            
            return result
            
        except Exception as e:
            print(f"Agent execution error: {e}")
            return {
                "response": "I encountered an error processing your request. Please try again.",
                "course_id": course_id,
                "function_results": {},
                "error": str(e)
            }
    
    async def _handle_workflow_state_updates(self, intent_result: Dict[str, Any], course_id: Optional[str]):
        """Handle workflow state updates based on intent"""
        if not course_id:
            return
        
        workflow_action = intent_result.get('workflow_action')
        
        if workflow_action == 'START_NEW_WORKFLOW':
            workflow_name = intent_result.get('target_workflow', 'course_creation')
            await self.workflow_state.start_workflow(course_id, workflow_name)
            
        elif workflow_action == 'JUMP_TO_STEP':
            target_step = intent_result.get('target_step')
            target_workflow = intent_result.get('target_workflow')
            if target_step:
                await self.workflow_state.jump_to_workflow_step(course_id, target_step, target_workflow)
        
        # CONTINUE_CURRENT doesn't need state updates here - handled after execution
    
    async def _update_workflow_after_execution(self, intent_result: Dict[str, Any], course_id: str, agent_result: Dict[str, Any]):
        """Update workflow state after successful agent execution"""
        function_results = agent_result.get('function_results', {})
        
        # Determine next step based on what was accomplished
        if 'course_created' in function_results:
            await self.workflow_state.update_workflow_state(course_id, 'curriculum_planning')
            
        elif 'curriculum_generated' in function_results:
            await self.workflow_state.update_workflow_state(course_id, 'content_creation')
            
        elif 'curriculum_choice' in function_results:
            choice_result = function_results['curriculum_choice']
            if choice_result.get('choice') == 'generate':
                await self.workflow_state.update_workflow_state(course_id, 'curriculum_generation')
            elif choice_result.get('choice') == 'upload':
                await self.workflow_state.update_workflow_state(course_id, 'curriculum_upload')
                
        elif 'content_modified' in function_results or 'content_updated' in function_results:
            await self.workflow_state.update_workflow_state(course_id, 'content_review')
    
    async def route_to_agent(self, agent_name: str, course_id: Optional[str], user_id: str, user_message: str) -> Dict[str, Any]:
        """Direct routing to a specific agent (bypass workflow logic)"""
        agent = self.get_agent(agent_name)
        
        if not agent:
            return {
                "response": f"Agent '{agent_name}' not found.",
                "course_id": course_id,
                "function_results": {},
                "error": f"Agent not registered: {agent_name}"
            }
        
        try:
            return await agent.process_message(course_id, user_id, user_message)
        except Exception as e:
            print(f"Direct agent routing error: {e}")
            return {
                "response": "I encountered an error processing your request. Please try again.",
                "course_id": course_id,
                "function_results": {},
                "error": str(e)
            }
    
    def get_registered_agents(self) -> Dict[str, Any]:
        """Get list of registered agents"""
        return {
            name: {
                "name": name,
                "class": agent.__class__.__name__,
                "available": True
            }
            for name, agent in self.agents.items()
        }
    
    async def execute_workflow_step(self, step_name: str, course_id: str, user_id: str, user_message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific workflow step"""
        # Determine agent based on step
        agent_name = self._get_agent_for_step(step_name)
        agent = self.get_agent(agent_name)
        
        if not agent:
            return {
                "response": f"No agent available for step '{step_name}'.",
                "course_id": course_id,
                "function_results": {},
                "error": f"No agent for step: {step_name}"
            }
        
        try:
            result = await agent.process_message(course_id, user_id, user_message)
            
            # Update workflow state after step execution
            await self._update_workflow_step_completion(step_name, course_id, result)
            
            return result
            
        except Exception as e:
            print(f"Workflow step execution error: {e}")
            return {
                "response": "I encountered an error executing this workflow step. Please try again.",
                "course_id": course_id,
                "function_results": {},
                "error": str(e)
            }
    
    def _get_agent_for_step(self, step_name: str) -> str:
        """Determine which agent should handle a specific workflow step"""
        if step_name == 'initial_research':
            return 'initial_research'
        elif 'course_design' in step_name:
            return 'course_design'
        elif step_name in ['content_structure_generation', 'content_structure_approval']:
            return 'course_structure'
        elif step_name in ['content_creation', 'content_generation']:  # ✅ Fixed: Handle both content_creation and content_generation
            return 'material_content_generator'
        elif 'curriculum' in step_name:
            return 'course_design'  # Backward compatibility
        elif 'content' in step_name and step_name not in ['content_structure_generation', 'content_structure_approval', 'content_creation', 'content_generation']:
            return 'course_design'  # Legacy content handling
        else:
            return 'course_creation'
    
    async def _update_workflow_step_completion(self, step_name: str, course_id: str, agent_result: Dict[str, Any]):
        """Update workflow state after step completion"""
        function_results = agent_result.get('function_results', {})
        
        # Determine next step based on current step and results
        next_step_mapping = {
            'course_naming': 'initial_research',
            'initial_research': 'course_design_method_selection',
            'course_design_method_selection': 'course_design_generation',
            'course_design_generation': 'course_design_complete',
            # Backward compatibility
            'curriculum_planning': 'curriculum_generation',
            'curriculum_generation': 'content_creation',
            'content_modification': 'content_review'
        }
        
        next_step = next_step_mapping.get(step_name)
        if next_step and function_results:  # Only advance if there were successful function calls
            await self.workflow_state.update_workflow_state(course_id, next_step)
