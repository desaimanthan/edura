from ...infrastructure.ai.openai_service import OpenAIService
from ...infrastructure.database.database_service import DatabaseService
from ...infrastructure.storage.r2_storage import R2StorageService
from .message_service import MessageService
from .context_service import ContextService
from .intent_service import IntentService
from .workflow_state_service import WorkflowStateService
from .workflow_restoration_service import WorkflowRestorationService
from .agent_factory import AgentFactory
from .agent_coordinator import AgentCoordinator
from .conversation_orchestrator import ConversationOrchestrator


class ServiceContainer:
    """Dependency injection container for all services and agents"""
    
    def __init__(self):
        # Initialize services in dependency order
        self._initialize_services()
        self._initialize_agents()
        self._initialize_orchestrator()
    
    def _initialize_services(self):
        """Initialize all services with proper dependencies"""
        
        # Core infrastructure services
        self.openai_service = OpenAIService()
        self.database_service = DatabaseService()
        self.r2_storage_service = R2StorageService()
        
        # Dependent services
        self.message_service = MessageService(self.database_service)
        self.context_service = ContextService(
            self.database_service, 
            self.openai_service, 
            self.message_service
        )
        
        # AI-powered services
        self.intent_service = IntentService(self.openai_service)
        
        # Workflow management
        self.workflow_state_service = WorkflowStateService(self.database_service)
        self.workflow_restoration_service = WorkflowRestorationService(
            self.database_service,
            self.workflow_state_service
        )
        
        # Agent coordination
        self.agent_coordinator = AgentCoordinator(self.workflow_state_service)
    
    def _initialize_agents(self):
        """Initialize agent factory for creating domain agents"""
        
        # Create agent factory with infrastructure services
        self.agent_factory = AgentFactory(
            openai_service=self.openai_service,
            database_service=self.database_service,
            message_service=self.message_service,
            context_service=self.context_service,
            r2_storage_service=self.r2_storage_service
        )
        
        # Register agents with coordinator using factory
        self.agent_coordinator.register_agent('course_creation', self.agent_factory.create_course_creation_agent())
        self.agent_coordinator.register_agent('course_design', self.agent_factory.create_course_design_agent())
        self.agent_coordinator.register_agent('initial_research', self.agent_factory.create_initial_research_agent())
        self.agent_coordinator.register_agent('course_structure', self.agent_factory.create_course_structure_agent())
        self.agent_coordinator.register_agent('material_content_generator', self.agent_factory.create_material_content_generator_agent())
    
    def _initialize_orchestrator(self):
        """Initialize the main conversation orchestrator"""
        
        self.conversation_orchestrator = ConversationOrchestrator(
            intent_service=self.intent_service,
            agent_coordinator=self.agent_coordinator,
            context_service=self.context_service,
            message_service=self.message_service,
            openai_service=self.openai_service
        )
    
    # Service getters
    def get_conversation_orchestrator(self) -> ConversationOrchestrator:
        """Get the main conversation orchestrator"""
        return self.conversation_orchestrator
    
    def get_openai_service(self) -> OpenAIService:
        """Get OpenAI service"""
        return self.openai_service
    
    def get_database_service(self) -> DatabaseService:
        """Get database service"""
        return self.database_service
    
    def get_message_service(self) -> MessageService:
        """Get message service"""
        return self.message_service
    
    def get_context_service(self) -> ContextService:
        """Get context service"""
        return self.context_service
    
    def get_intent_service(self) -> IntentService:
        """Get intent service"""
        return self.intent_service
    
    def get_workflow_state_service(self) -> WorkflowStateService:
        """Get workflow state service"""
        return self.workflow_state_service
    
    def get_workflow_restoration_service(self) -> WorkflowRestorationService:
        """Get workflow restoration service"""
        return self.workflow_restoration_service
    
    def get_agent_coordinator(self) -> AgentCoordinator:
        """Get agent coordinator"""
        return self.agent_coordinator
    
    def get_r2_storage_service(self) -> R2StorageService:
        """Get R2 storage service"""
        return self.r2_storage_service
    
    # Agent getters (using factory)
    def get_agent_factory(self) -> AgentFactory:
        """Get the agent factory"""
        return self.agent_factory
    
    def get_course_creation_agent(self):
        """Get course creation agent"""
        return self.agent_factory.create_course_creation_agent()
    
    def get_course_design_agent(self):
        """Get course design agent"""
        return self.agent_factory.create_course_design_agent()
    
    def get_curriculum_agent(self):
        """Get curriculum agent (backward compatibility)"""
        return self.agent_factory.create_course_design_agent()
    
    def get_initial_research_agent(self):
        """Get initial research agent"""
        return self.agent_factory.create_initial_research_agent()
    
    def get_image_generation_agent(self):
        """Get image generation agent"""
        return self.agent_factory.create_image_generation_agent()
    
    def get_course_structure_agent(self):
        """Get course structure agent"""
        return self.agent_factory.create_course_structure_agent()
    
    def get_material_content_generator_agent(self):
        """Get material content generator agent"""
        return self.agent_factory.create_material_content_generator_agent()
    
    # Utility methods
    def get_all_services(self) -> dict:
        """Get all services for debugging/monitoring"""
        return {
            'openai_service': self.openai_service,
            'database_service': self.database_service,
            'message_service': self.message_service,
            'context_service': self.context_service,
            'intent_service': self.intent_service,
            'workflow_state_service': self.workflow_state_service,
            'agent_coordinator': self.agent_coordinator,
            'r2_storage_service': self.r2_storage_service,
            'conversation_orchestrator': self.conversation_orchestrator
        }
    
    def get_all_agents(self) -> dict:
        """Get all agents for debugging/monitoring"""
        return {
            'course_creation': self.agent_factory.create_course_creation_agent(),
            'course_design': self.agent_factory.create_course_design_agent(),
            'initial_research': self.agent_factory.create_initial_research_agent(),
            'course_structure': self.agent_factory.create_course_structure_agent(),
            'material_content_generator': self.agent_factory.create_material_content_generator_agent(),
            'image_generation': self.agent_factory.create_image_generation_agent()
        }
    
    async def close_all_clients(self):
        """Close all service clients"""
        await self.conversation_orchestrator.close_clients()
    
    def health_check(self) -> dict:
        """Basic health check for all services"""
        return {
            'services_initialized': len(self.get_all_services()),
            'agents_registered': len(self.agent_coordinator.get_registered_agents()),
            'orchestrator_ready': self.conversation_orchestrator is not None,
            'status': 'healthy'
        }


# Global service container instance
_service_container = None


def get_service_container() -> ServiceContainer:
    """Get the global service container instance"""
    global _service_container
    if _service_container is None:
        _service_container = ServiceContainer()
    return _service_container


def reset_service_container():
    """Reset the global service container (useful for testing)"""
    global _service_container
    _service_container = None
