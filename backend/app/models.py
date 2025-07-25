from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        return core_schema.no_info_plain_validator_function(
            cls.validate,
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str) and ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId")

# User Models
class UserBase(BaseModel):
    email: EmailStr
    name: str
    is_active: bool = True

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str = Field(alias="_id")
    email: EmailStr
    name: str
    is_active: bool
    role_id: Optional[str] = None
    role_name: Optional[str] = None  # Populated role name
    google_id: Optional[str] = None
    avatar: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class UserInDB(UserBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    password_hash: Optional[str] = None
    google_id: Optional[str] = None
    avatar: Optional[str] = None
    role_id: Optional[PyObjectId] = None  # Single role ID as ObjectId - defaults to Student role
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Token Models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Password Reset Models
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str

class PasswordResetInDB(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    email: EmailStr
    token: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    used: bool = False

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Google OAuth Models
class GoogleUserInfo(BaseModel):
    id: str
    email: EmailStr
    name: str
    picture: Optional[str] = None
    verified_email: bool

# Permission Models
class Permission(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str  # e.g., "user_create", "role_edit"
    description: str
    resource: str  # e.g., "users", "roles", "dashboard"
    action: str    # e.g., "create", "read", "update", "delete"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class PermissionCreate(BaseModel):
    name: str
    description: str
    resource: str
    action: str

class PermissionResponse(BaseModel):
    id: str = Field(alias="_id")
    name: str
    description: str
    resource: str
    action: str
    created_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

# Role Models
class Role(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    description: str
    permission_ids: list[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class RoleCreate(BaseModel):
    name: str
    description: str
    permission_ids: list[str] = []

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permission_ids: Optional[list[str]] = None

class RoleResponse(BaseModel):
    id: str = Field(alias="_id")
    name: str
    description: str
    permission_ids: list[str]
    permissions: list[PermissionResponse] = []  # Populated permissions
    user_count: int = 0  # Count of users with this role
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

# Course Models
class Course(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    description: Optional[str] = None
    curriculum_content: Optional[str] = None  # Markdown text
    pedagogy_content: Optional[str] = None    # Markdown text
    created_by: PyObjectId  # User ID
    status: str = "draft"  # draft, curriculum_complete, pedagogy_complete, complete
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class CourseCreate(BaseModel):
    name: str
    description: Optional[str] = None

class CourseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    curriculum_content: Optional[str] = None
    pedagogy_content: Optional[str] = None
    status: Optional[str] = None

class CourseResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    curriculum_content: Optional[str] = None
    pedagogy_content: Optional[str] = None
    created_by: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class ContentGenerationRequest(BaseModel):
    course_name: str
    curriculum_content: Optional[str] = None  # For pedagogy generation

class ContentEnhancementRequest(BaseModel):
    content: str
    content_type: str  # "curriculum" or "pedagogy"

class AIResponse(BaseModel):
    content: str
    suggestions: Optional[list] = None  # For enhancement responses

# Research Report Models
class ResearchReport(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    course_id: PyObjectId  # FK to Course
    task_id: str  # OpenAI o3-deep-research task ID
    status: str = "pending"  # pending, processing, completed, failed
    markdown_report: Optional[str] = None  # Final research output
    input_data: dict = {}  # Original course data used for research
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ResearchReportCreate(BaseModel):
    course_id: str
    task_id: str
    input_data: dict = {}

class ResearchStatusResponse(BaseModel):
    id: str
    course_id: str
    task_id: str
    status: str
    progress: Optional[str] = None
    markdown_report: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class ResearchGenerationRequest(BaseModel):
    course_name: str
    description: Optional[str] = None
    curriculum_content: Optional[str] = None
    pedagogy_content: Optional[str] = None

# Slide Generation Models
class SlideDeck(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    course_id: PyObjectId  # FK to Course
    title: str
    description: Optional[str] = None
    status: str = "draft"  # draft, generating, completed, failed
    total_slides: int = 0
    created_by: PyObjectId  # User ID
    generation_session_id: Optional[str] = None  # Link to generation session
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class Slide(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    deck_id: PyObjectId  # FK to SlideDeck
    slide_number: int
    title: str
    content: dict = {}  # Flexible JSON structure for different slide types
    template_type: str  # geometric_abstract, split_image_text, data_table, etc.
    layout_config: dict = {}  # Position, size, styling information
    images: list = []  # List of image objects
    ai_generated: bool = True
    agent_decisions: dict = {}  # Decisions made by agents for this slide
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class SlideImage(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    slide_id: PyObjectId
    image_url: str  # Stored image URL
    original_prompt: str  # The prompt used to generate the image
    alt_text: str  # Accessibility text
    position: dict = {}  # x, y, width, height in slide
    generated_by_ai: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class SlideGenerationSession(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    course_id: PyObjectId
    deck_id: Optional[PyObjectId] = None
    status: str = "in_progress"  # in_progress, completed, failed, cancelled
    conversation_log: list = []  # Full agent conversation
    agent_decisions: dict = {}  # Key decisions made by each agent
    generation_metadata: dict = {}
    websocket_clients: list = []  # Connected WebSocket clients
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class AgentDecision(BaseModel):
    agent_name: str
    agent_role: str
    decision_type: str  # template_selection, content_creation, image_prompt, etc.
    decision_data: dict
    reasoning: str
    slide_number: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Response Models for API
class SlideDeckResponse(BaseModel):
    id: str
    course_id: str
    title: str
    description: Optional[str] = None
    status: str
    total_slides: int
    created_by: str
    generation_session_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class SlideResponse(BaseModel):
    id: str
    deck_id: str
    slide_number: int
    title: str
    content: dict
    template_type: str
    layout_config: dict
    images: list
    ai_generated: bool
    agent_decisions: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class SlideGenerationRequest(BaseModel):
    course_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    template_preferences: Optional[dict] = None

class SlideGenerationStatusResponse(BaseModel):
    session_id: str
    status: str
    progress: Optional[int] = None
    current_agent: Optional[str] = None
    total_slides_generated: int = 0
    conversation_messages: int = 0
    error_message: Optional[str] = None
    websocket_url: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}
