from typing import Dict, Any
from ...infrastructure.ai.openai_service import OpenAIService
from ...infrastructure.database.database_service import DatabaseService
from ...infrastructure.storage.r2_storage import R2StorageService
from .message_service import MessageService
from .context_service import ContextService

from ..agents.agent_1_course_creation_agent import CourseCreationAgent
from ..agents.agent_2_initial_research_agent import InitialResearchAgent
from ..agents.agent_3_course_design_agent import CourseDesignAgent
from ..agents.agent_C1_image_generation_agent import ImageGenerationAgent
from ..agents.agent_4_course_structure_agent import CourseStructureAgent
from ..agents.agent_5_material_content_generator_agent import MaterialContentGeneratorAgent


class AgentFactory:
    """Factory for creating domain agents with proper dependency injection"""
    
    def __init__(self, openai_service: OpenAIService, database_service: DatabaseService,
                 message_service: MessageService, context_service: ContextService,
                 r2_storage_service: R2StorageService):
        self.openai_service = openai_service
        self.database_service = database_service
        self.message_service = message_service
        self.context_service = context_service
        self.r2_storage_service = r2_storage_service
        
        # Cache for created agents to avoid recreating them
        self._agent_cache: Dict[str, Any] = {}
    
    def create_image_generation_agent(self) -> ImageGenerationAgent:
        """Create ImageGenerationAgent"""
        if 'image_generation' not in self._agent_cache:
            self._agent_cache['image_generation'] = ImageGenerationAgent(
                openai_service=self.openai_service,
                r2_storage=self.r2_storage_service
            )
        return self._agent_cache['image_generation']
    
    def create_course_creation_agent(self) -> CourseCreationAgent:
        """Create CourseCreationAgent"""
        if 'course_creation' not in self._agent_cache:
            image_agent = self.create_image_generation_agent()
            self._agent_cache['course_creation'] = CourseCreationAgent(
                openai_service=self.openai_service,
                database_service=self.database_service,
                message_service=self.message_service,
                context_service=self.context_service,
                image_generation_agent=image_agent
            )
        return self._agent_cache['course_creation']
    
    def create_course_design_agent(self) -> CourseDesignAgent:
        """Create CourseDesignAgent"""
        if 'course_design' not in self._agent_cache:
            self._agent_cache['course_design'] = CourseDesignAgent(
                openai_service=self.openai_service,
                database_service=self.database_service,
                message_service=self.message_service,
                context_service=self.context_service,
                r2_storage_service=self.r2_storage_service
            )
        return self._agent_cache['course_design']
    
    def create_initial_research_agent(self) -> InitialResearchAgent:
        """Create InitialResearchAgent"""
        if 'initial_research' not in self._agent_cache:
            self._agent_cache['initial_research'] = InitialResearchAgent(
                openai_service=self.openai_service,
                database_service=self.database_service,
                message_service=self.message_service,
                context_service=self.context_service,
                r2_storage_service=self.r2_storage_service
            )
        return self._agent_cache['initial_research']
    
    def create_course_structure_agent(self) -> CourseStructureAgent:
        """Create CourseStructureAgent with constraints"""
        if 'course_structure' not in self._agent_cache:
            self._agent_cache['course_structure'] = CourseStructureAgent(
                openai_service=self.openai_service,
                database_service=self.database_service,
                message_service=self.message_service,
                context_service=self.context_service,
                r2_storage_service=self.r2_storage_service
            )
        return self._agent_cache['course_structure']
    
    def create_material_content_generator_agent(self) -> MaterialContentGeneratorAgent:
        """Create MaterialContentGeneratorAgent with image generation support"""
        if 'material_content_generator' not in self._agent_cache:
            image_agent = self.create_image_generation_agent()
            self._agent_cache['material_content_generator'] = MaterialContentGeneratorAgent(
                openai_service=self.openai_service,
                database_service=self.database_service,
                message_service=self.message_service,
                context_service=self.context_service,
                r2_storage_service=self.r2_storage_service,
                image_generation_agent=image_agent
            )
        return self._agent_cache['material_content_generator']
    
    def get_agent(self, agent_name: str):
        """Get an agent by name"""
        agent_creators = {
            'course_creation': self.create_course_creation_agent,
            'course_design': self.create_course_design_agent,
            'initial_research': self.create_initial_research_agent,
            'course_structure': self.create_course_structure_agent,
            'material_content_generator': self.create_material_content_generator_agent,
            'image_generation': self.create_image_generation_agent
        }
        
        if agent_name in agent_creators:
            return agent_creators[agent_name]()
        else:
            raise ValueError(f"Unknown agent: {agent_name}")
    
    def clear_cache(self):
        """Clear the agent cache (useful for testing)"""
        self._agent_cache.clear()
