from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
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
    intended_role_name: Optional[str] = "Student"  # Role selection from frontend

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
    # Teacher approval system fields
    approval_status: Optional[str] = None
    requested_role_name: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    approval_reason: Optional[str] = None
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
    # Teacher approval system fields
    approval_status: Optional[str] = None  # "pending", "approved", "rejected"
    requested_role_name: Optional[str] = None  # Track what role was requested
    approved_by: Optional[PyObjectId] = None  # Admin who approved/rejected
    approved_at: Optional[datetime] = None  # When approval action was taken
    approval_reason: Optional[str] = None  # Reason for rejection or notes
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
    user_id: PyObjectId
    structure: dict = {}  # Course outline, chapters, files
    status: str = "creating"  # creating, in_progress, completed
    workflow_step: str = "course_naming"  # Track current step in workflow
    # Legacy curriculum fields (for backward compatibility)
    curriculum_r2_key: Optional[str] = None  # R2 storage key for curriculum
    curriculum_public_url: Optional[str] = None  # Public URL for curriculum
    curriculum_source: Optional[str] = None  # "generated" | "uploaded"
    curriculum_version: int = 1  # Current curriculum version
    curriculum_updated_at: Optional[datetime] = None  # When curriculum was last updated
    # Research fields
    research_r2_key: Optional[str] = None  # R2 storage key for research
    research_public_url: Optional[str] = None  # Public URL for research
    research_updated_at: Optional[datetime] = None  # When research was last updated
    # New course design fields (curriculum + pedagogy + assessments)
    course_design_r2_key: Optional[str] = None  # R2 storage key for course design
    course_design_public_url: Optional[str] = None  # Public URL for course design
    course_design_source: Optional[str] = None  # "generated" | "uploaded" | "uploaded_processed"
    course_design_version: int = 1  # Current course design version
    course_design_updated_at: Optional[datetime] = None  # When course design was last updated
    has_pedagogy: bool = False  # Whether course design includes pedagogy
    has_assessments: bool = False  # Whether course design includes assessments
    design_components: list[str] = []  # List of components: ["curriculum", "pedagogy", "assessments"]
    # New enhanced course creation fields
    learning_outcomes: list[str] = []  # What you'll learn items
    prerequisites: list[str] = []  # Prerequisites items
    # Multi-size cover image fields
    cover_image_large_r2_key: Optional[str] = None  # R2 key for large cover image (1536x1024)
    cover_image_large_public_url: Optional[str] = None  # Public URL for large cover image
    cover_image_medium_r2_key: Optional[str] = None  # R2 key for medium cover image (768x512)
    cover_image_medium_public_url: Optional[str] = None  # Public URL for medium cover image
    cover_image_small_r2_key: Optional[str] = None  # R2 key for small cover image (384x256)
    cover_image_small_public_url: Optional[str] = None  # Public URL for small cover image
    # Legacy single image fields (for backward compatibility)
    cover_image_r2_key: Optional[str] = None  # R2 key for cover image (deprecated, use large)
    cover_image_public_url: Optional[str] = None  # Public URL for cover image (deprecated, use large)
    cover_image_metadata: dict = {}  # Image metadata (size, format, quality, etc.)
    cover_image_updated_at: Optional[datetime] = None  # When cover image was last updated
    content_generated_at: Optional[datetime] = None  # When auto-content was generated
    auto_generated_fields: list[str] = []  # Track which fields were auto-generated
    # Content structure fields (replaces CourseStructureChecklist)
    content_structure: dict = {}  # Parsed structure from course design (modules, chapters, materials)
    structure_approved: bool = False  # User approval of the structure
    structure_approved_at: Optional[datetime] = None  # When structure was approved
    total_content_items: int = 0  # Total number of content materials
    completed_content_items: int = 0  # Number of completed content materials
    structure_generated_at: Optional[datetime] = None  # When structure was generated
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class CourseCreate(BaseModel):
    name: str
    description: Optional[str] = None

class CourseResponse(BaseModel):
    id: str = Field(alias="_id")
    name: str
    description: Optional[str] = None
    user_id: str
    structure: dict = {}
    status: str
    workflow_step: str
    # Legacy curriculum fields (for backward compatibility)
    curriculum_r2_key: Optional[str] = None
    curriculum_public_url: Optional[str] = None
    curriculum_source: Optional[str] = None
    curriculum_version: int = 1
    curriculum_updated_at: Optional[datetime] = None
    # Research fields
    research_r2_key: Optional[str] = None
    research_public_url: Optional[str] = None
    research_updated_at: Optional[datetime] = None
    # New course design fields (curriculum + pedagogy + assessments)
    course_design_r2_key: Optional[str] = None
    course_design_public_url: Optional[str] = None
    course_design_source: Optional[str] = None
    course_design_version: int = 1
    course_design_updated_at: Optional[datetime] = None
    has_pedagogy: bool = False
    has_assessments: bool = False
    design_components: list[str] = []
    # New enhanced course creation fields
    learning_outcomes: list[str] = []
    prerequisites: list[str] = []
    # Multi-size cover image fields
    cover_image_large_r2_key: Optional[str] = None
    cover_image_large_public_url: Optional[str] = None
    cover_image_medium_r2_key: Optional[str] = None
    cover_image_medium_public_url: Optional[str] = None
    cover_image_small_r2_key: Optional[str] = None
    cover_image_small_public_url: Optional[str] = None
    # Legacy single image fields (for backward compatibility)
    cover_image_r2_key: Optional[str] = None
    cover_image_public_url: Optional[str] = None
    cover_image_metadata: dict = {}
    cover_image_updated_at: Optional[datetime] = None
    content_generated_at: Optional[datetime] = None
    auto_generated_fields: list[str] = []
    # Content structure fields (replaces CourseStructureChecklist)
    content_structure: dict = {}  # Parsed structure from course design (modules, chapters, materials)
    structure_approved: bool = False  # User approval of the structure
    structure_approved_at: Optional[datetime] = None  # When structure was approved
    total_content_items: int = 0  # Total number of content materials
    completed_content_items: int = 0  # Number of completed content materials
    structure_generated_at: Optional[datetime] = None  # When structure was generated
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

# Chat Message Models
class ChatMessage(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    course_id: PyObjectId
    user_id: PyObjectId
    content: str
    role: str  # "user", "assistant", "system"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message_index: int  # Order in conversation (0, 1, 2...)
    metadata: dict = {}  # Function calls, tool usage, generated content refs

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ChatMessageCreate(BaseModel):
    content: str
    context_hints: Optional[Dict[str, Any]] = None  # Frontend workflow context hints

class ChatMessageResponse(BaseModel):
    id: str = Field(alias="_id")
    course_id: str
    user_id: str
    content: str
    role: str
    timestamp: datetime
    message_index: int
    metadata: dict = {}

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

# Chat Session Models
class ChatSession(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    course_id: PyObjectId
    user_id: PyObjectId
    context_summary: str = ""  # AI-generated summary of older messages
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    total_messages: int = 0
    context_window_start: int = 0  # Which message index to start full context from
    summary_updated_at: Optional[datetime] = None  # When context summary was last updated

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ChatSessionResponse(BaseModel):
    id: str = Field(alias="_id")
    course_id: str
    user_id: str
    context_summary: str
    last_activity: datetime
    total_messages: int
    context_window_start: int
    summary_updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

# Content Creation Models
class ContentMaterial(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    course_id: PyObjectId
    module_number: int
    chapter_number: int
    material_type: str  # "slide", "quiz", "assessment", "module_quiz"
    title: str
    description: Optional[str] = None
    content: Optional[str] = None  # Generated content (for slides) or JSON string (for assessments)
    status: str = "pending"  # pending, generating, completed, approved, needs_revision
    content_status: str = "not done"  # Track content generation status for next agent
    slide_number: Optional[int] = None  # Slide number within the chapter (for slide materials)
    # Assessment-specific fields
    assessment_format: Optional[str] = None  # "multiple_choice", "true_false", "scenario_choice", "matching", etc.
    assessment_data: Optional[Dict[str, Any]] = None  # Structured question data for assessments
    question_difficulty: Optional[str] = None  # "beginner", "intermediate", "advanced"
    learning_objective: Optional[str] = None  # Specific learning objective this material addresses
    r2_key: Optional[str] = None
    public_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ContentMaterialResponse(BaseModel):
    id: str = Field(alias="_id")
    course_id: str
    module_number: int
    chapter_number: int
    material_type: str
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    status: str
    content_status: str = "not done"  # Track content generation status for next agent
    slide_number: Optional[int] = None  # Slide number within the chapter (for slide materials)
    # Assessment-specific fields
    assessment_format: Optional[str] = None  # "multiple_choice", "true_false", "scenario_choice", "matching", etc.
    assessment_data: Optional[Dict[str, Any]] = None  # Structured question data for assessments
    question_difficulty: Optional[str] = None  # "beginner", "intermediate", "advanced"
    learning_objective: Optional[str] = None  # Specific learning objective this material addresses
    r2_key: Optional[str] = None
    public_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class CourseStructureChecklist(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    course_id: PyObjectId
    structure: Dict[str, Any]  # Nested structure of modules/chapters/materials
    total_items: int
    completed_items: int = 0
    status: str = "pending"  # pending, approved, in_progress, completed
    user_approved: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class CourseStructureChecklistResponse(BaseModel):
    id: str = Field(alias="_id")
    course_id: str
    structure: Dict[str, Any]
    total_items: int
    completed_items: int
    status: str
    user_approved: bool
    created_at: datetime
    approved_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class SlideContent(BaseModel):
    slide_number: int
    title: str
    content_type: str  # "comprehensive", "interactive", "visual", "assessment"
    content: str
    learning_tips: Optional[str] = None  # Tips and reminders for students
    self_check_questions: list[str] = []  # Questions for self-assessment
    visual_elements: list[str] = []  # Descriptions of visual elements needed
    key_takeaways: list[str] = []  # Essential points to remember

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Assessment Response Models
class AssessmentResponse(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    course_id: PyObjectId
    material_id: PyObjectId  # Reference to the ContentMaterial (assessment)
    user_answer: Dict[str, Any]  # User's selected answer(s) - format depends on assessment type
    is_correct: bool  # Whether the answer was correct
    time_taken: Optional[int] = None  # Time taken to answer in seconds
    attempt_number: int = 1  # Allow multiple attempts
    feedback_shown: bool = False  # Whether feedback was displayed to user
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class AssessmentResponseCreate(BaseModel):
    material_id: str
    user_answer: Dict[str, Any]
    time_taken: Optional[int] = None

class AssessmentResponseResponse(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    course_id: str
    material_id: str
    user_answer: Dict[str, Any]
    is_correct: bool
    time_taken: Optional[int] = None
    attempt_number: int
    feedback_shown: bool
    created_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

# Teacher Approval Models
class TeacherApprovalAction(BaseModel):
    action: str  # "approve" or "reject"
    reason: Optional[str] = None  # Optional reason for rejection or notes

class TeacherApprovalResponse(BaseModel):
    message: str
    user_id: str
    action: str
    approved_by: str
