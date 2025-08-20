from typing import Dict, Any, Optional
from datetime import datetime

from .workflow_state_service import WorkflowStateService
from ...infrastructure.database.database_service import DatabaseService


class WorkflowRestorationService:
    """Service to restore workflow state after page refresh or session interruption"""
    
    def __init__(self, database_service: DatabaseService, workflow_state_service: WorkflowStateService):
        self.db = database_service
        self.workflow_state = workflow_state_service
    
    async def restore_workflow_context(self, course_id: str, user_id: str) -> Dict[str, Any]:
        """Restore complete workflow context for a course"""
        try:
            # Get course data
            course = await self.db.find_course(course_id)
            if not course:
                return {
                    "success": False,
                    "error": "Course not found",
                    "should_redirect": True,
                    "redirect_url": "/courses"
                }
            
            # Serialize course data to handle ObjectId and datetime objects
            serialized_course = self._serialize_course_data(course)
            
            # Get workflow state
            workflow_state = await self.workflow_state.get_workflow_state(course_id)
            
            # Determine what should happen next based on current state
            next_action = await self._determine_next_action(course, workflow_state)
            
            return {
                "success": True,
                "course": serialized_course,
                "workflow_state": workflow_state,
                "next_action": next_action,
                "restoration_context": {
                    "current_step": workflow_state["current_step"],
                    "completed_steps": workflow_state["completed_steps"],
                    "workflow_status": workflow_state["workflow_status"],
                    "available_files": await self._get_available_files(course),
                    "suggested_message": await self._get_suggested_continuation_message(workflow_state, course)
                }
            }
            
        except Exception as e:
            print(f"❌ [WorkflowRestorationService] Error restoring workflow: {e}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": f"Failed to restore workflow: {str(e)}"
            }
    
    async def _determine_next_action(self, course: Dict[str, Any], workflow_state: Dict[str, Any]) -> Dict[str, Any]:
        """Determine what action should be taken next based on current state"""
        current_step = workflow_state["current_step"]
        workflow_status = workflow_state["workflow_status"]
        
        # Check what files are available
        has_research = bool(course.get("research_r2_key") or course.get("research_public_url"))
        has_course_design = bool(course.get("course_design_r2_key") or course.get("curriculum_r2_key") or 
                                course.get("course_design_public_url") or course.get("curriculum_public_url"))
        has_content_structure = bool(course.get("structure") and course.get("structure") != {})
        
        print(f"🔍 [WorkflowRestoration] Determining next action:")
        print(f"   📋 Current step: {current_step}")
        print(f"   📊 Workflow status: {workflow_status}")
        print(f"   🔬 Has research: {has_research}")
        print(f"   📄 Has course design: {has_course_design}")
        print(f"   📚 Has content structure: {has_content_structure}")
        
        # If workflow is completed, suggest next steps
        if workflow_status == "completed":
            return {
                "type": "workflow_complete",
                "message": "Course creation workflow is complete!",
                "suggestions": [
                    "Review and modify course content",
                    "Generate additional materials",
                    "Export course content"
                ]
            }
        
        # Smart workflow determination based on available files and current state
        if not has_research:
            # No research exists - need to start with research
            print(f"🎯 [WorkflowRestoration] No research found - directing to research generation")
            return {
                "type": "user_choice_required",
                "next_step": "initial_research",
                "message": "Ready to continue with research generation",
                "auto_trigger": False,
                "suggested_message": "Generate for me",
                "choices": [
                    {"id": "generate", "label": "Generate for me", "description": "AI will conduct comprehensive research"},
                    {"id": "upload", "label": "I have materials", "description": "Upload your own research materials"}
                ]
            }
        
        elif has_research and not has_course_design:
            # Research exists but no course design - should generate course design
            print(f"🎯 [WorkflowRestoration] Research exists, no course design - directing to course design")
            return {
                "type": "user_choice_required",
                "next_step": "course_design_method_selection",
                "message": "Research complete, ready for course design",
                "auto_trigger": False,
                "suggested_message": "Generate for me",
                "choices": [
                    {"id": "generate", "label": "Generate for me", "description": "AI will create comprehensive course design"},
                    {"id": "upload", "label": "Upload materials", "description": "Upload your own curriculum files"}
                ]
            }
        
        elif has_research and has_course_design and not has_content_structure:
            # Both research and course design exist - should generate content structure
            print(f"🎯 [WorkflowRestoration] Research and course design exist - directing to content structure")
            return {
                "type": "auto_continue",
                "next_step": "content_structure_generation",
                "message": "Course design complete, ready for content structure",
                "auto_trigger": True,
                "suggested_message": "Generate content structure"
            }
        
        elif has_research and has_course_design and has_content_structure:
            # Everything exists - ready for content creation
            print(f"🎯 [WorkflowRestoration] All components exist - ready for content creation")
            return {
                "type": "auto_continue",
                "next_step": "content_creation",
                "message": "Content structure ready, can start content creation",
                "auto_trigger": False,
                "suggested_message": "Start content creation"
            }
        
        # Fallback to current step logic for edge cases
        if current_step == "course_naming":
            if course.get("name") and course.get("name") != "Untitled Course":
                # Course is named, should move to research but require user action
                return {
                    "type": "user_choice_required",
                    "next_step": "initial_research",
                    "message": "Course created successfully! Ready to continue with research generation",
                    "auto_trigger": False,
                    "suggested_message": "Generate for me",
                    "choices": [
                        {"id": "generate", "label": "Generate for me", "description": "AI will conduct comprehensive research"},
                        {"id": "upload", "label": "I have materials", "description": "Upload your own research materials"}
                    ]
                }
            else:
                return {
                    "type": "user_input_required",
                    "message": "Please provide a course name to continue",
                    "input_type": "course_name",
                    "suggested_message": "What would you like to name your course?"
                }
        
        # Handle legacy workflow steps
        elif current_step == "curriculum_planning":
            # Legacy step - map to course_design_method_selection
            return {
                "type": "user_choice_required",
                "message": "Choose how to create your course design",
                "auto_trigger": False,
                "suggested_message": "Generate for me",
                "choices": [
                    {"id": "generate", "label": "Generate for me", "description": "AI will create comprehensive course design"},
                    {"id": "upload", "label": "Upload materials", "description": "Upload your own curriculum files"}
                ]
            }
        
        else:
            # Generic continuation based on file availability
            print(f"🎯 [WorkflowRestoration] Generic continuation for step: {current_step}")
            return {
                "type": "continue_workflow",
                "message": f"Continue from {current_step}",
                "auto_trigger": False,
                "suggested_message": "Continue with course creation"
            }
    
    async def _get_available_files(self, course: Dict[str, Any]) -> Dict[str, Any]:
        """Get list of available files for the course"""
        files = {}
        
        # Helper function to convert datetime objects to strings
        def serialize_datetime(dt):
            if dt is None:
                return None
            if hasattr(dt, 'isoformat'):
                return dt.isoformat()
            return str(dt)
        
        # Research file
        if course.get("research_r2_key") or course.get("research_public_url"):
            files["research"] = {
                "name": "research.md",
                "type": "research",
                "url": course.get("research_public_url"),
                "r2_key": course.get("research_r2_key"),
                "updated_at": serialize_datetime(course.get("research_updated_at"))
            }
        
        # Course design file
        if course.get("course_design_r2_key") or course.get("curriculum_r2_key"):
            files["course_design"] = {
                "name": "course-design.md",
                "type": "course_design", 
                "url": course.get("course_design_public_url") or course.get("curriculum_public_url"),
                "r2_key": course.get("course_design_r2_key") or course.get("curriculum_r2_key"),
                "updated_at": serialize_datetime(course.get("course_design_updated_at") or course.get("curriculum_updated_at"))
            }
        
        # Cover image
        if course.get("cover_image_r2_key") or course.get("cover_image_public_url"):
            files["cover_image"] = {
                "name": "cover-image.png",
                "type": "image",
                "url": course.get("cover_image_public_url"),
                "r2_key": course.get("cover_image_r2_key"),
                "updated_at": serialize_datetime(course.get("cover_image_updated_at"))
            }
        
        return files
    
    async def _get_suggested_continuation_message(self, workflow_state: Dict[str, Any], course: Dict[str, Any]) -> str:
        """Get a suggested message for the user to continue the workflow"""
        current_step = workflow_state["current_step"]
        
        suggestions = {
            "course_naming": "What would you like to name your course?",
            "initial_research": "Generate research for me",
            "course_design_method_selection": "Generate for me",
            "course_design_generation": "Generate course design",
            "content_structure_generation": "Generate content structure",
            "content_structure_approval": "Approve the content structure",
            "content_creation": "Start content creation"
        }
        
        return suggestions.get(current_step, "Continue with course creation")
    
    def _serialize_course_data(self, course: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize course data to handle ObjectId and datetime objects"""
        from bson import ObjectId
        
        serialized = {}
        
        for key, value in course.items():
            if isinstance(value, ObjectId):
                # Convert ObjectId to string
                serialized[key] = str(value)
            elif isinstance(value, datetime):
                # Convert datetime to ISO string
                serialized[key] = value.isoformat()
            elif isinstance(value, dict):
                # Recursively serialize nested dictionaries
                serialized[key] = self._serialize_dict(value)
            elif isinstance(value, list):
                # Recursively serialize lists
                serialized[key] = self._serialize_list(value)
            else:
                # Keep other types as-is
                serialized[key] = value
        
        return serialized
    
    def _serialize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively serialize dictionary values"""
        from bson import ObjectId
        
        serialized = {}
        for key, value in data.items():
            if isinstance(value, ObjectId):
                serialized[key] = str(value)
            elif isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif isinstance(value, dict):
                serialized[key] = self._serialize_dict(value)
            elif isinstance(value, list):
                serialized[key] = self._serialize_list(value)
            else:
                serialized[key] = value
        return serialized
    
    def _serialize_list(self, data: list) -> list:
        """Recursively serialize list values"""
        from bson import ObjectId
        
        serialized = []
        for item in data:
            if isinstance(item, ObjectId):
                serialized.append(str(item))
            elif isinstance(item, datetime):
                serialized.append(item.isoformat())
            elif isinstance(item, dict):
                serialized.append(self._serialize_dict(item))
            elif isinstance(item, list):
                serialized.append(self._serialize_list(item))
            else:
                serialized.append(item)
        return serialized

    async def trigger_workflow_continuation(self, course_id: str, user_id: str, next_action: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger automatic workflow continuation if needed"""
        if not next_action.get("auto_trigger"):
            return {"success": False, "message": "No auto-trigger required"}
        
        try:
            next_step = next_action["next_step"]
            
            # Update workflow state to next step
            await self.workflow_state.update_workflow_state(course_id, next_step)
            
            # Return continuation signal
            return {
                "success": True,
                "auto_continue": True,
                "next_step": next_step,
                "message": next_action["message"],
                "suggested_user_message": await self._get_suggested_continuation_message(
                    {"current_step": next_step}, 
                    await self.db.find_course(course_id)
                )
            }
            
        except Exception as e:
            print(f"❌ [WorkflowRestorationService] Error triggering continuation: {e}")
            return {
                "success": False,
                "error": f"Failed to trigger continuation: {str(e)}"
            }
