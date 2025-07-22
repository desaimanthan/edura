from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Body
from fastapi.security import HTTPBearer
from typing import List, Optional
from bson import ObjectId
from datetime import datetime
import io

from ..database import get_database
from ..auth import get_current_user
from ..models import (
    Course, CourseCreate, CourseUpdate, CourseResponse,
    ContentGenerationRequest, ContentEnhancementRequest, AIResponse,
    UserInDB
)
from ..openai_service import openai_service

router = APIRouter()
security = HTTPBearer()

@router.get("/", response_model=List[CourseResponse])
async def get_courses(
    current_user: UserInDB = Depends(get_current_user)
):
    """Get all courses for the current user"""
    db = await get_database()
    
    # Find all courses created by the current user
    courses_cursor = db.courses.find({"created_by": current_user.id})
    courses = await courses_cursor.to_list(length=None)
    
    # Convert ObjectId to string for each course
    course_responses = []
    for course in courses:
        course["id"] = str(course["_id"])
        course["created_by"] = str(course["created_by"])
        # Remove the original _id field since we now have id
        del course["_id"]
        course_responses.append(CourseResponse(**course))
    
    return course_responses

@router.post("/", response_model=CourseResponse)
async def create_course(
    course_data: CourseCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    """Create a new course"""
    db = await get_database()
    
    # Create course document
    course = Course(
        name=course_data.name,
        description=course_data.description,
        created_by=current_user.id,
        status="draft"
    )
    
    # Insert into database
    result = await db.courses.insert_one(course.dict(by_alias=True))
    
    # Fetch the created course
    created_course = await db.courses.find_one({"_id": result.inserted_id})
    if not created_course:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create course"
        )
    
    # Convert ObjectId to string for response
    created_course["id"] = str(created_course["_id"])
    created_course["created_by"] = str(created_course["created_by"])
    # Remove the original _id field since we now have id
    del created_course["_id"]
    
    return CourseResponse(**created_course)

@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: str,
    course_data: CourseUpdate,
    current_user: UserInDB = Depends(get_current_user)
):
    """Update course basic information"""
    db = await get_database()
    
    if not ObjectId.is_valid(course_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid course ID"
        )
    
    # Check if course exists and user has permission
    course = await db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    if course["created_by"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this course"
        )
    
    # Update course data
    update_data = {
        "name": course_data.name,
        "description": course_data.description,
        "updated_at": datetime.utcnow()
    }
    
    result = await db.courses.update_one(
        {"_id": ObjectId(course_id)},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update course"
        )
    
    # Fetch the updated course
    updated_course = await db.courses.find_one({"_id": ObjectId(course_id)})
    if not updated_course:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch updated course"
        )
    
    # Convert ObjectId to string for response
    updated_course["id"] = str(updated_course["_id"])
    updated_course["created_by"] = str(updated_course["created_by"])
    # Remove the original _id field since we now have id
    del updated_course["_id"]
    
    return CourseResponse(**updated_course)

@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get course by ID"""
    db = await get_database()
    
    if not ObjectId.is_valid(course_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid course ID"
        )
    
    course = await db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Convert ObjectId to string for response
    course["id"] = str(course["_id"])
    course["created_by"] = str(course["created_by"])
    # Remove the original _id field since we now have id
    del course["_id"]
    
    return CourseResponse(**course)

@router.put("/{course_id}/curriculum")
async def update_curriculum(
    course_id: str,
    curriculum_content: str = Body(..., media_type="text/plain"),
    current_user: UserInDB = Depends(get_current_user)
):
    """Update course curriculum content"""
    db = await get_database()
    
    if not ObjectId.is_valid(course_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid course ID"
        )
    
    # Check if course exists and user has permission
    course = await db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    if course["created_by"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this course"
        )
    
    # Update curriculum content and status
    update_data = {
        "curriculum_content": curriculum_content,
        "updated_at": datetime.utcnow()
    }
    
    # Update status based on content completion
    if curriculum_content and course.get("pedagogy_content"):
        update_data["status"] = "complete"
    elif curriculum_content:
        update_data["status"] = "curriculum_complete"
    
    result = await db.courses.update_one(
        {"_id": ObjectId(course_id)},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update curriculum"
        )
    
    return {"message": "Curriculum updated successfully"}

@router.put("/{course_id}/pedagogy")
async def update_pedagogy(
    course_id: str,
    pedagogy_content: str = Body(..., media_type="text/plain"),
    current_user: UserInDB = Depends(get_current_user)
):
    """Update course pedagogy content"""
    db = await get_database()
    
    if not ObjectId.is_valid(course_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid course ID"
        )
    
    # Check if course exists and user has permission
    course = await db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    if course["created_by"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this course"
        )
    
    # Update pedagogy content and status
    update_data = {
        "pedagogy_content": pedagogy_content,
        "updated_at": datetime.utcnow()
    }
    
    # Update status based on content completion
    if pedagogy_content and course.get("curriculum_content"):
        update_data["status"] = "complete"
    elif pedagogy_content:
        update_data["status"] = "pedagogy_complete"
    
    result = await db.courses.update_one(
        {"_id": ObjectId(course_id)},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update pedagogy"
        )
    
    return {"message": "Pedagogy updated successfully"}

@router.post("/{course_id}/generate-curriculum", response_model=AIResponse)
async def generate_curriculum(
    course_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Generate curriculum content using AI"""
    db = await get_database()
    
    if not ObjectId.is_valid(course_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid course ID"
        )
    
    # Get course details
    course = await db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    if course["created_by"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to generate content for this course"
        )
    
    try:
        # Generate curriculum using OpenAI
        print(f"Generating curriculum for course: {course['name']}")
        curriculum_content = openai_service.generate_curriculum(course["name"])
        print(f"Generated curriculum content length: {len(curriculum_content)}")
        
        return AIResponse(content=curriculum_content)
    except Exception as e:
        print(f"Error generating curriculum: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate curriculum: {str(e)}"
        )

@router.post("/{course_id}/generate-pedagogy", response_model=AIResponse)
async def generate_pedagogy(
    course_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Generate pedagogy content using AI"""
    db = await get_database()
    
    if not ObjectId.is_valid(course_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid course ID"
        )
    
    # Get course details
    course = await db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    if course["created_by"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to generate content for this course"
        )
    
    try:
        # Generate pedagogy using OpenAI
        pedagogy_content = openai_service.generate_pedagogy(
            course["name"], 
            course.get("curriculum_content")
        )
        
        return AIResponse(content=pedagogy_content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate pedagogy: {str(e)}"
        )

@router.post("/{course_id}/enhance-curriculum")
async def enhance_curriculum(
    course_id: str,
    request: ContentEnhancementRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """Enhance curriculum content using AI"""
    db = await get_database()
    
    if not ObjectId.is_valid(course_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid course ID"
        )
    
    # Check course ownership
    course = await db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    if course["created_by"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to enhance content for this course"
        )
    
    try:
        # Enhance content using OpenAI
        enhancement_result = openai_service.enhance_content(
            request.content, 
            "curriculum"
        )
        
        return enhancement_result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enhance curriculum: {str(e)}"
        )

@router.post("/{course_id}/enhance-pedagogy")
async def enhance_pedagogy(
    course_id: str,
    request: ContentEnhancementRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """Enhance pedagogy content using AI"""
    db = await get_database()
    
    if not ObjectId.is_valid(course_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid course ID"
        )
    
    # Check course ownership
    course = await db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    if course["created_by"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to enhance content for this course"
        )
    
    try:
        # Enhance content using OpenAI
        enhancement_result = openai_service.enhance_content(
            request.content, 
            "pedagogy"
        )
        
        return enhancement_result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enhance pedagogy: {str(e)}"
        )

@router.post("/{course_id}/upload-curriculum")
async def upload_curriculum_file(
    course_id: str,
    file: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_user)
):
    """Upload curriculum markdown file"""
    if not ObjectId.is_valid(course_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid course ID"
        )
    
    # Check file type
    if not file.filename.endswith('.md'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only markdown (.md) files are allowed"
        )
    
    try:
        # Read file content
        content = await file.read()
        curriculum_content = content.decode('utf-8')
        
        # Update curriculum using existing endpoint logic
        await update_curriculum(course_id, curriculum_content, current_user)
        
        return {"message": "Curriculum file uploaded successfully", "content": curriculum_content}
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file encoding. Please use UTF-8 encoded markdown files."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload curriculum file: {str(e)}"
        )

@router.post("/{course_id}/upload-pedagogy")
async def upload_pedagogy_file(
    course_id: str,
    file: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_user)
):
    """Upload pedagogy markdown file"""
    if not ObjectId.is_valid(course_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid course ID"
        )
    
    # Check file type
    if not file.filename.endswith('.md'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only markdown (.md) files are allowed"
        )
    
    try:
        # Read file content
        content = await file.read()
        pedagogy_content = content.decode('utf-8')
        
        # Update pedagogy using existing endpoint logic
        await update_pedagogy(course_id, pedagogy_content, current_user)
        
        return {"message": "Pedagogy file uploaded successfully", "content": pedagogy_content}
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file encoding. Please use UTF-8 encoded markdown files."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload pedagogy file: {str(e)}"
        )
