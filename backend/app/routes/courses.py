from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Body
from fastapi.security import HTTPBearer
from typing import List, Optional
from bson import ObjectId
from datetime import datetime, timezone, timedelta
import io
import uuid

# IST timezone (UTC + 5:30)
IST = timezone(timedelta(hours=5, minutes=30))

from ..database import get_database
from ..auth import get_current_user
from ..models import (
    Course, CourseCreate, CourseUpdate, CourseResponse,
    ContentGenerationRequest, ContentEnhancementRequest, AIResponse,
    ResearchReport, ResearchReportCreate, ResearchStatusResponse, ResearchGenerationRequest,
    UserInDB
)
from ..openai_service import openai_service
from ..deep_research_service import deep_research_service
from ..autogen_slide_service import autogen_orchestrator
from ..websocket_manager import websocket_manager
from ..models import (
    SlideDeck, SlideDeckResponse, Slide, SlideResponse, 
    SlideGenerationRequest, SlideGenerationStatusResponse,
    SlideGenerationSession
)

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

# Deep Research Endpoints

@router.post("/{course_id}/generate-research")
async def generate_research(
    course_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Start deep research generation for a course"""
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
            detail="Not authorized to generate research for this course"
        )
    
    # Check if research already exists and is in progress
    existing_research = await db.research_reports.find_one({
        "course_id": ObjectId(course_id),
        "status": {"$in": ["pending", "processing"]}
    })
    
    if existing_research:
        return {
            "message": "Research generation already in progress",
            "task_id": existing_research["task_id"],
            "status": existing_research["status"]
        }
    
    try:
        # Prepare course data for research
        course_data = {
            "course_name": course["name"],
            "description": course.get("description", ""),
            "curriculum_content": course.get("curriculum_content", ""),
            "pedagogy_content": course.get("pedagogy_content", "")
        }
        
        # Start deep research task
        task_id = deep_research_service.start_deep_research(course_data)
        
        # Create research report record
        research_report = ResearchReport(
            course_id=ObjectId(course_id),
            task_id=task_id,
            status="pending",
            input_data=course_data,
            created_at=datetime.now(IST)
        )
        
        # Insert into database
        result = await db.research_reports.insert_one(research_report.dict(by_alias=True))
        
        return {
            "message": "Deep research generation started",
            "task_id": task_id,
            "research_id": str(result.inserted_id),
            "status": "pending"
        }
        
    except Exception as e:
        print(f"Error starting research generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start research generation: {str(e)}"
        )

@router.get("/{course_id}/research-status", response_model=ResearchStatusResponse)
async def get_research_status(
    course_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get the status of research generation for a course"""
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
            detail="Not authorized to access research for this course"
        )
    
    # Find the latest research report for this course
    research_report = await db.research_reports.find_one(
        {"course_id": ObjectId(course_id)},
        sort=[("created_at", -1)]
    )
    
    if not research_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No research report found for this course"
        )
    
    # If research is still in progress, check status with OpenAI
    if research_report["status"] in ["pending", "processing", "queued", "in_progress"]:
        try:
            print(f"Checking OpenAI status for task: {research_report['task_id']}")
            status_result = deep_research_service.check_research_status(research_report["task_id"])
            print(f"OpenAI returned status: {status_result}")
            
            # Update database with latest status
            update_data = {
                "status": status_result["status"],
                "updated_at": datetime.now(IST)
            }
            
            if status_result["status"] == "completed" and status_result["output"]:
                update_data["markdown_report"] = status_result["output"]
                update_data["completed_at"] = datetime.now(IST)
                print(f"Research completed! Report length: {len(status_result['output'])} characters")
            elif status_result["status"] == "failed":
                update_data["error_message"] = status_result.get("error", "Research task failed")
                print(f"Research failed: {status_result.get('error', 'Unknown error')}")
            elif status_result["status"] in ["in_progress", "queued"]:
                print(f"Research still {status_result['status']}, continuing to poll...")
            
            await db.research_reports.update_one(
                {"_id": research_report["_id"]},
                {"$set": update_data}
            )
            
            # Update the research_report dict for response
            research_report.update(update_data)
            
        except Exception as e:
            print(f"Error checking research status: {str(e)}")
            # Don't fail the request, just return current status
    
    # Convert ObjectId to string for response
    research_report["id"] = str(research_report["_id"])
    research_report["course_id"] = str(research_report["course_id"])
    
    print(f"Returning research status response: {research_report['status']} for task {research_report['task_id']}")
    
    return ResearchStatusResponse(**research_report)

@router.get("/{course_id}/research-report")
async def get_research_report(
    course_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get the completed research report for a course"""
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
            detail="Not authorized to access research for this course"
        )
    
    # Find the latest completed research report
    research_report = await db.research_reports.find_one(
        {
            "course_id": ObjectId(course_id),
            "status": "completed",
            "markdown_report": {"$exists": True, "$ne": None}
        },
        sort=[("completed_at", -1)]
    )
    
    if not research_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No completed research report found for this course"
        )
    
    return {
        "course_id": str(research_report["course_id"]),
        "task_id": research_report["task_id"],
        "markdown_report": research_report["markdown_report"],
        "created_at": research_report["created_at"],
        "completed_at": research_report["completed_at"]
    }

@router.post("/{course_id}/cancel-research")
async def cancel_research(
    course_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Cancel a running research task for a course"""
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
            detail="Not authorized to cancel research for this course"
        )
    
    # Find the active research report
    research_report = await db.research_reports.find_one(
        {
            "course_id": ObjectId(course_id),
            "status": {"$in": ["pending", "queued", "in_progress"]}
        },
        sort=[("created_at", -1)]
    )
    
    if not research_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active research task found for this course"
        )
    
    try:
        # Cancel the research task with OpenAI
        cancel_result = deep_research_service.cancel_research(research_report["task_id"])
        
        # Update database with cancellation
        await db.research_reports.update_one(
            {"_id": research_report["_id"]},
            {
                "$set": {
                    "status": "cancelled",
                    "error_message": "Research task cancelled by user",
                    "completed_at": datetime.now(IST)
                }
            }
        )
        
        return {
            "message": "Research task cancelled successfully",
            "task_id": research_report["task_id"],
            "status": "cancelled"
        }
        
    except Exception as e:
        print(f"Error cancelling research: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel research: {str(e)}"
        )

# Slide Generation Endpoints

@router.post("/{course_id}/slides/generate-with-agents")
async def generate_slides_with_agents(
    course_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Start multi-agent slide generation with conversation tracking"""
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
            detail="Not authorized to generate slides for this course"
        )
    
    # Check if course has required content
    if not course.get("curriculum_content") or not course.get("pedagogy_content"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course must have both curriculum and pedagogy content before generating slides"
        )
    
    # Get research report if available
    research_report = await db.research_reports.find_one(
        {
            "course_id": ObjectId(course_id),
            "status": "completed",
            "markdown_report": {"$exists": True, "$ne": None}
        },
        sort=[("completed_at", -1)]
    )
    
    try:
        # Create generation session
        session_id = str(uuid.uuid4())
        session = SlideGenerationSession(
            course_id=ObjectId(course_id),
            status="in_progress",
            generation_metadata={
                "session_id": session_id,
                "started_by": str(current_user.id),
                "course_name": course["name"]
            }
        )
        
        # Insert session into database
        session_result = await db.slide_generation_sessions.insert_one(session.dict(by_alias=True))
        
        # Prepare course data for agents
        course_data = {
            "name": course["name"],
            "description": course.get("description", ""),
            "curriculum_content": course.get("curriculum_content", ""),
            "pedagogy_content": course.get("pedagogy_content", ""),
            "research_report": research_report.get("markdown_report", "") if research_report else ""
        }
        
        # Start background task for slide generation
        import asyncio
        asyncio.create_task(
            generate_slides_background_task(session_id, course_data, course_id, current_user.id)
        )
        
        return {
            "session_id": session_id,
            "status": "started",
            "message": "Multi-agent slide generation started",
            "websocket_url": f"/ws/slides/generation/{session_id}"
        }
        
    except Exception as e:
        print(f"Error starting slide generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start slide generation: {str(e)}"
        )

async def generate_slides_background_task(session_id: str, course_data: dict, course_id: str, user_id: ObjectId):
    """Background task to generate slides using multi-agent system"""
    import os
    from dotenv import load_dotenv
    
    # Ensure environment variables are loaded in the background task
    load_dotenv()
    
    # Verify OPENAI_API_KEY is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print(f"❌ OPENAI_API_KEY not found in background task. Available env vars: {list(os.environ.keys())}")
        # Update session with error
        db = await get_database()
        await db.slide_generation_sessions.update_one(
            {"generation_metadata.session_id": session_id},
            {
                "$set": {
                    "status": "failed",
                    "generation_metadata.error": "OPENAI_API_KEY environment variable is required",
                    "completed_at": datetime.utcnow()
                }
            }
        )
        return
    
    print(f"✅ OPENAI_API_KEY found in background task: {api_key[:10]}...")
    
    db = await get_database()
    
    try:
        # Update session status
        await db.slide_generation_sessions.update_one(
            {"generation_metadata.session_id": session_id},
            {"$set": {"status": "generating"}}
        )
        
        # Generate slides using AutoGen orchestrator
        result = await autogen_orchestrator.generate_slides_with_conversation(course_data, session_id)
        
        # Create slide deck
        deck_title = f"{course_data['name']} - Slides"
        slide_deck = SlideDeck(
            course_id=ObjectId(course_id),
            title=deck_title,
            description=f"AI-generated slides for {course_data['name']}",
            status="completed",
            total_slides=len(result.get('slides', [])),
            created_by=user_id,
            generation_session_id=session_id
        )
        
        # Insert slide deck
        deck_result = await db.slide_decks.insert_one(slide_deck.dict(by_alias=True))
        deck_id = deck_result.inserted_id
        
        # Insert individual slides
        for slide_data in result.get('slides', []):
            slide = Slide(
                deck_id=deck_id,
                slide_number=slide_data['slide_number'],
                title=slide_data['title'],
                content=slide_data['content'],
                template_type=slide_data['template_type'],
                layout_config=slide_data['layout_config'],
                images=slide_data['images'],
                agent_decisions=slide_data['agent_decisions']
            )
            await db.slides.insert_one(slide.dict(by_alias=True))
        
        # Update session with completion
        await db.slide_generation_sessions.update_one(
            {"generation_metadata.session_id": session_id},
            {
                "$set": {
                    "status": "completed",
                    "deck_id": deck_id,
                    "conversation_log": result.get('conversation_log', []),
                    "agent_decisions": result.get('agent_decisions', {}),
                    "completed_at": datetime.utcnow()
                }
            }
        )
        
        # Send completion notification via WebSocket
        await websocket_manager.send_completion(
            session_id, 
            len(result.get('slides', [])), 
            True
        )
        
        print(f"✅ Slide generation completed for session {session_id}")
        
    except Exception as e:
        print(f"❌ Error in slide generation background task: {str(e)}")
        
        # Update session with error
        await db.slide_generation_sessions.update_one(
            {"generation_metadata.session_id": session_id},
            {
                "$set": {
                    "status": "failed",
                    "generation_metadata.error": str(e),
                    "completed_at": datetime.utcnow()
                }
            }
        )
        
        # Send error notification via WebSocket
        await websocket_manager.send_completion(
            session_id, 
            0, 
            False, 
            str(e)
        )

@router.get("/{course_id}/slides/generation/{session_id}/status", response_model=SlideGenerationStatusResponse)
async def get_slide_generation_status(
    course_id: str,
    session_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get the status of slide generation session"""
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
            detail="Not authorized to access slide generation for this course"
        )
    
    # Find the generation session
    session = await db.slide_generation_sessions.find_one(
        {"generation_metadata.session_id": session_id}
    )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slide generation session not found"
        )
    
    # Count generated slides if completed
    total_slides_generated = 0
    if session.get("deck_id"):
        total_slides_generated = await db.slides.count_documents({"deck_id": session["deck_id"]})
    
    return SlideGenerationStatusResponse(
        session_id=session_id,
        status=session["status"],
        current_agent=session.get("current_agent"),
        total_slides_generated=total_slides_generated,
        conversation_messages=len(session.get("conversation_log", [])),
        error_message=session.get("generation_metadata", {}).get("error"),
        websocket_url=f"/ws/slides/generation/{session_id}",
        created_at=session["created_at"],
        completed_at=session.get("completed_at")
    )

@router.get("/{course_id}/slides", response_model=List[SlideDeckResponse])
async def get_slide_decks(
    course_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get all slide decks for a course"""
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
            detail="Not authorized to access slides for this course"
        )
    
    # Find all slide decks for this course
    decks_cursor = db.slide_decks.find({"course_id": ObjectId(course_id)})
    decks = await decks_cursor.to_list(length=None)
    
    # Convert to response format
    deck_responses = []
    for deck in decks:
        deck["id"] = str(deck["_id"])
        deck["course_id"] = str(deck["course_id"])
        deck["created_by"] = str(deck["created_by"])
        del deck["_id"]
        deck_responses.append(SlideDeckResponse(**deck))
    
    return deck_responses

@router.get("/{course_id}/slides/{deck_id}", response_model=List[SlideResponse])
async def get_slides_in_deck(
    course_id: str,
    deck_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get all slides in a specific deck"""
    db = await get_database()
    
    if not ObjectId.is_valid(course_id) or not ObjectId.is_valid(deck_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid course ID or deck ID"
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
            detail="Not authorized to access slides for this course"
        )
    
    # Check if deck exists and belongs to the course
    deck = await db.slide_decks.find_one({
        "_id": ObjectId(deck_id),
        "course_id": ObjectId(course_id)
    })
    
    if not deck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slide deck not found"
        )
    
    # Find all slides in the deck
    slides_cursor = db.slides.find({"deck_id": ObjectId(deck_id)}).sort("slide_number", 1)
    slides = await slides_cursor.to_list(length=None)
    
    # Convert to response format
    slide_responses = []
    for slide in slides:
        slide["id"] = str(slide["_id"])
        slide["deck_id"] = str(slide["deck_id"])
        del slide["_id"]
        slide_responses.append(SlideResponse(**slide))
    
    return slide_responses

@router.get("/{course_id}/slides/generation/{session_id}/conversation")
async def get_agent_conversation(
    course_id: str,
    session_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get the full agent conversation log for a generation session"""
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
            detail="Not authorized to access conversation for this course"
        )
    
    # Find the generation session
    session = await db.slide_generation_sessions.find_one(
        {"generation_metadata.session_id": session_id}
    )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation session not found"
        )
    
    return {
        "session_id": session_id,
        "conversation_log": session.get("conversation_log", []),
        "agent_decisions": session.get("agent_decisions", {}),
        "generation_metadata": session.get("generation_metadata", {})
    }

@router.post("/test-image-generation")
async def test_image_generation(
    prompt: str = "Create an educational diagram showing UX research methods",
    current_user: UserInDB = Depends(get_current_user)
):
    """Test image generation with gpt-image-1 model"""
    try:
        from ..autogen_slide_service import autogen_orchestrator
        
        # Test image generation
        result = await autogen_orchestrator.generate_image_from_prompt(prompt)
        
        if result:
            return {
                "success": True,
                "image": result,
                "message": "Image generated successfully"
            }
        else:
            return {
                "success": False,
                "error": "Failed to generate image",
                "message": "Check logs for detailed error information"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Exception occurred during image generation"
        }

@router.get("/{course_id}/slides/latest")
async def get_latest_slides(
    course_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get the latest generated slides for a course"""
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
            detail="Not authorized to access slides for this course"
        )
    
    # Find the latest completed slide deck
    deck = await db.slide_decks.find_one(
        {
            "course_id": ObjectId(course_id),
            "status": "completed"
        },
        sort=[("created_at", -1)]
    )
    
    if not deck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No completed slide deck found for this course"
        )
    
    # Get all slides in the deck
    slides_cursor = db.slides.find({"deck_id": deck["_id"]}).sort("slide_number", 1)
    slides = await slides_cursor.to_list(length=None)
    
    # Convert slides to proper format
    formatted_slides = []
    for slide in slides:
        formatted_slide = {
            "slide_number": slide["slide_number"],
            "title": slide["title"],
            "content": slide["content"],
            "template_type": slide["template_type"],
            "images": slide.get("images", []),
            "layout_config": slide.get("layout_config", {})
        }
        formatted_slides.append(formatted_slide)
    
    return {
        "slides": formatted_slides,
        "deck_info": {
            "title": deck["title"],
            "description": deck["description"],
            "total_slides": len(formatted_slides),
            "created_at": deck["created_at"]
        }
    }
