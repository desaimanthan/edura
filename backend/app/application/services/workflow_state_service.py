from typing import Dict, Any, Optional, List
from datetime import datetime
from bson import ObjectId

from ...infrastructure.database.database_service import DatabaseService


class WorkflowStateService:
    """Manages workflow state and transitions"""
    
    def __init__(self, database_service: DatabaseService):
        self.db = database_service
        
        # Define workflow definitions
        self.workflows = {
            "course_creation": {
                "name": "course_creation",
                "steps": [
                    {
                        "id": "course_naming",
                        "name": "Course Naming",
                        "required": True,
                        "next": "initial_research"
                    },
                    {
                        "id": "initial_research",
                        "name": "Initial Research",
                        "required": True,
                        "next": "course_design_method_selection"
                    },
                    {
                        "id": "course_design_method_selection",
                        "name": "Course Design Method Selection",
                        "required": True,
                        "next": "course_design_generation"
                    },
                    {
                        "id": "course_design_generation",
                        "name": "Course Design Generation",
                        "required": True,
                        "next": "course_design_complete"
                    },
                    {
                        "id": "course_design_complete",
                        "name": "Course Design Complete",
                        "required": False,
                        "next": "content_structure_generation"
                    },
                    {
                        "id": "content_structure_generation",
                        "name": "Content Structure Generation",
                        "required": True,
                        "next": "content_structure_approval"
                    },
                    {
                        "id": "content_structure_approval",
                        "name": "Content Structure Approval",
                        "required": True,
                        "next": "content_creation"
                    },
                    {
                        "id": "content_creation",
                        "name": "Content Creation",
                        "required": True,
                        "next": "content_complete"
                    },
                    {
                        "id": "content_complete",
                        "name": "Content Creation Complete",
                        "required": False,
                        "next": None
                    }
                ]
            },
            "content_update": {
                "name": "content_update",
                "steps": [
                    {
                        "id": "content_analysis",
                        "name": "Content Analysis",
                        "required": True,
                        "next": "content_modification"
                    },
                    {
                        "id": "content_modification",
                        "name": "Content Modification",
                        "required": True,
                        "next": "content_review"
                    },
                    {
                        "id": "content_review",
                        "name": "Content Review",
                        "required": False,
                        "next": None
                    }
                ]
            }
        }
    
    async def get_workflow_state(self, course_id: str) -> Dict[str, Any]:
        """Get current workflow state for a course"""
        course = await self.db.find_course(course_id)
        if not course:
            return {
                "current_workflow": None,
                "current_step": "course_naming",
                "completed_steps": [],
                "workflow_status": "not_started",
                "step_data": {}
            }
        
        return {
            "current_workflow": course.get("current_workflow", "course_creation"),
            "current_step": course.get("workflow_step", "course_naming"),
            "completed_steps": course.get("completed_steps", []),
            "workflow_status": course.get("workflow_status", "in_progress"),
            "step_data": course.get("workflow_data", {})
        }
    
    async def start_workflow(self, course_id: str, workflow_name: str) -> Dict[str, Any]:
        """Initialize a new workflow for a course"""
        if workflow_name not in self.workflows:
            raise ValueError(f"Unknown workflow: {workflow_name}")
        
        workflow = self.workflows[workflow_name]
        first_step = workflow["steps"][0]["id"]
        
        workflow_data = {
            "current_workflow": workflow_name,
            "workflow_step": first_step,
            "completed_steps": [],
            "workflow_status": "in_progress",
            "workflow_data": {},
            "workflow_started_at": datetime.utcnow()
        }
        
        success = await self.db.update_course(course_id, workflow_data)
        
        if success:
            return {
                "success": True,
                "workflow": workflow_name,
                "current_step": first_step,
                "message": f"Started {workflow_name} workflow at step {first_step}"
            }
        else:
            return {
                "success": False,
                "error": "Failed to update course with workflow state"
            }
    
    async def update_workflow_state(self, course_id: str, new_step: str, step_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Update workflow state to a new step"""
        current_state = await self.get_workflow_state(course_id)
        current_workflow = current_state["current_workflow"]
        current_step = current_state["current_step"]
        completed_steps = current_state["completed_steps"].copy()
        
        # Add current step to completed steps if moving to a new step
        if current_step and current_step != new_step and current_step not in completed_steps:
            completed_steps.append(current_step)
        
        # Merge step data
        workflow_data = current_state["step_data"].copy()
        if step_data:
            workflow_data.update(step_data)
        
        update_data = {
            "workflow_step": new_step,
            "completed_steps": completed_steps,
            "workflow_data": workflow_data,
            "workflow_updated_at": datetime.utcnow()
        }
        
        success = await self.db.update_course(course_id, update_data)
        
        if success:
            return {
                "success": True,
                "previous_step": current_step,
                "current_step": new_step,
                "completed_steps": completed_steps
            }
        else:
            return {
                "success": False,
                "error": "Failed to update workflow state"
            }
    
    async def jump_to_workflow_step(self, course_id: str, target_step: str, workflow_name: str = None) -> Dict[str, Any]:
        """Jump to a specific workflow step"""
        current_state = await self.get_workflow_state(course_id)
        
        # If workflow_name is provided, switch workflows
        if workflow_name and workflow_name != current_state["current_workflow"]:
            await self.start_workflow(course_id, workflow_name)
        
        # Update to target step
        return await self.update_workflow_state(course_id, target_step)
    
    async def complete_workflow(self, course_id: str) -> Dict[str, Any]:
        """Mark workflow as complete"""
        current_state = await self.get_workflow_state(course_id)
        current_step = current_state["current_step"]
        completed_steps = current_state["completed_steps"].copy()
        
        # Add current step to completed if not already there
        if current_step and current_step not in completed_steps:
            completed_steps.append(current_step)
        
        update_data = {
            "workflow_status": "completed",
            "completed_steps": completed_steps,
            "workflow_completed_at": datetime.utcnow()
        }
        
        success = await self.db.update_course(course_id, update_data)
        
        if success:
            return {
                "success": True,
                "workflow": current_state["current_workflow"],
                "completed_steps": completed_steps,
                "message": "Workflow completed successfully"
            }
        else:
            return {
                "success": False,
                "error": "Failed to complete workflow"
            }
    
    def can_transition_to_step(self, current_step: str, target_step: str, workflow_name: str) -> bool:
        """Validate if step transition is allowed"""
        if workflow_name not in self.workflows:
            return False
        
        workflow = self.workflows[workflow_name]
        steps = {step["id"]: step for step in workflow["steps"]}
        
        # Allow jumping to any step (flexible workflow)
        return target_step in steps
    
    def get_next_possible_steps(self, current_step: str, workflow_name: str) -> List[str]:
        """Get valid next steps from current state"""
        if workflow_name not in self.workflows:
            return []
        
        workflow = self.workflows[workflow_name]
        
        for step in workflow["steps"]:
            if step["id"] == current_step:
                next_step = step.get("next")
                if next_step:
                    return [next_step]
                else:
                    return []  # End of workflow
        
        return []
    
    def get_workflow_definition(self, workflow_name: str) -> Optional[Dict[str, Any]]:
        """Get workflow definition"""
        return self.workflows.get(workflow_name)
    
    def get_step_definition(self, workflow_name: str, step_id: str) -> Optional[Dict[str, Any]]:
        """Get step definition"""
        workflow = self.workflows.get(workflow_name)
        if not workflow:
            return None
        
        for step in workflow["steps"]:
            if step["id"] == step_id:
                return step
        
        return None
    
    async def get_workflow_history(self, course_id: str) -> List[Dict[str, Any]]:
        """Get workflow execution history"""
        # This could be expanded to track detailed history
        # For now, return basic state information
        current_state = await self.get_workflow_state(course_id)
        
        history = []
        for step_id in current_state["completed_steps"]:
            history.append({
                "step_id": step_id,
                "status": "completed",
                "timestamp": None  # Would need to track this separately
            })
        
        # Add current step
        if current_state["current_step"]:
            history.append({
                "step_id": current_state["current_step"],
                "status": "in_progress",
                "timestamp": None
            })
        
        return history
