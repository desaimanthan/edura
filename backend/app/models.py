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
