from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List, Optional
from bson import ObjectId
from datetime import datetime
import json
import asyncio
from ...application.agents.agent_3_course_design_agent import CourseDesignAgent

from ...auth import get_current_user
from ...database import get_database
from ...models import (
    UserInDB, Course, CourseCreate, CourseResponse, 
    ChatMessageCreate, ChatMessageResponse, ChatSessionResponse,
    ContentMaterialResponse
)
from ...application.services.service_container import get_service_container
from ...infrastructure.storage.r2_storage import R2StorageService

router = APIRouter()

# Get service container
service_container = get_service_container()
conversation_orchestrator = service_container.get_conversation_orchestrator()

@router.post("/", response_model=CourseResponse)
async def create_course(
    course_data: CourseCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    """Create a new course"""
    db = await get_database()
    
    course = Course(
        name=course_data.name,
        description=course_data.description,
        user_id=current_user.id,
        structure={},
        status="creating",
        workflow_step="course_naming"
    )
    
    result = await db.courses.insert_one(course.dict(by_alias=True))
    
    # Get the created course
    created_course = await db.courses.find_one({"_id": result.inserted_id})
    
    # Convert ObjectIds to strings
    created_course["_id"] = str(created_course["_id"])
    created_course["user_id"] = str(created_course["user_id"])
    
    return CourseResponse(**created_course)

@router.get("/", response_model=List[CourseResponse])
async def get_user_courses(
    current_user: UserInDB = Depends(get_current_user)
):
    """Get all courses for the current user"""
    db = await get_database()
    
    courses_cursor = db.courses.find({"user_id": current_user.id}).sort("created_at", -1)
    courses = await courses_cursor.to_list(100)
    
    # Convert ObjectIds to strings for each course
    for course in courses:
        course["_id"] = str(course["_id"])
        course["user_id"] = str(course["user_id"])
    
    return [CourseResponse(**course) for course in courses]

@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get a specific course"""
    db = await get_database()
    
    if not ObjectId.is_valid(course_id):
        raise HTTPException(status_code=400, detail="Invalid course ID")
    
    course = await db.courses.find_one({
        "_id": ObjectId(course_id),
        "user_id": current_user.id
    })
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Convert ObjectIds to strings
    course["_id"] = str(course["_id"])
    course["user_id"] = str(course["user_id"])
    
    return CourseResponse(**course)

@router.get("/{course_id}/restore-workflow")
async def restore_workflow_context(
    course_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Restore workflow context after page refresh or session interruption"""
    try:
        service_container = get_service_container()
        workflow_restoration_service = service_container.get_workflow_restoration_service()
        
        print(f"\n🔄 [WORKFLOW RESTORATION] Restoring context for course: {course_id}")
        print(f"   👤 User: {current_user.id}")
        
        # Restore workflow context
        restoration_result = await workflow_restoration_service.restore_workflow_context(
            course_id=course_id,
            user_id=str(current_user.id)
        )
        
        if not restoration_result.get("success"):
            error_msg = restoration_result.get("error", "Failed to restore workflow context")
            print(f"❌ [WORKFLOW RESTORATION] {error_msg}")
            
            if restoration_result.get("should_redirect"):
                raise HTTPException(
                    status_code=404, 
                    detail=error_msg,
                    headers={"X-Redirect-URL": restoration_result.get("redirect_url", "/courses")}
                )
            else:
                raise HTTPException(status_code=500, detail=error_msg)
        
        print(f"✅ [WORKFLOW RESTORATION] Context restored successfully")
        print(f"   📋 Current step: {restoration_result['workflow_state']['current_step']}")
        print(f"   🎯 Next action: {restoration_result['next_action']['type']}")
        
        # Check if we should auto-trigger continuation
        next_action = restoration_result["next_action"]
        if next_action.get("auto_trigger"):
            print(f"🚀 [WORKFLOW RESTORATION] Auto-triggering continuation...")
            continuation_result = await workflow_restoration_service.trigger_workflow_continuation(
                course_id=course_id,
                user_id=str(current_user.id),
                next_action=next_action
            )
            
            if continuation_result.get("success"):
                restoration_result["auto_continuation"] = continuation_result
                print(f"✅ [WORKFLOW RESTORATION] Auto-continuation triggered")
            else:
                print(f"⚠️ [WORKFLOW RESTORATION] Auto-continuation failed: {continuation_result.get('error')}")
        
        return restoration_result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [WORKFLOW RESTORATION] CRITICAL ERROR: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restore workflow context: {str(e)}"
        )

@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: str,
    course_data: CourseCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    """Update a course"""
    db = await get_database()
    
    if not ObjectId.is_valid(course_id):
        raise HTTPException(status_code=400, detail="Invalid course ID")
    
    # Check if course exists and belongs to user
    existing_course = await db.courses.find_one({
        "_id": ObjectId(course_id),
        "user_id": current_user.id
    })
    
    if not existing_course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Update course
    update_data = {
        "name": course_data.name,
        "description": course_data.description,
        "updated_at": datetime.utcnow()
    }
    
    await db.courses.update_one(
        {"_id": ObjectId(course_id)},
        {"$set": update_data}
    )
    
    # Get updated course
    updated_course = await db.courses.find_one({"_id": ObjectId(course_id)})
    
    # Convert ObjectIds to strings
    updated_course["_id"] = str(updated_course["_id"])
    updated_course["user_id"] = str(updated_course["user_id"])
    
    return CourseResponse(**updated_course)

@router.delete("/{course_id}")
async def delete_course(
    course_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Delete a course and all associated data"""
    db = await get_database()
    
    if not ObjectId.is_valid(course_id):
        raise HTTPException(status_code=400, detail="Invalid course ID")
    
    # Check if course exists and belongs to user
    course = await db.courses.find_one({
        "_id": ObjectId(course_id),
        "user_id": current_user.id
    })
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Delete all files from R2 storage
    r2_service = R2StorageService()
    r2_deleted = await r2_service.delete_all_course_files(course_id)
    
    if not r2_deleted:
        print(f"Warning: Failed to delete R2 files for course {course_id}")
    
    # Delete course and associated data from database
    await db.courses.delete_one({"_id": ObjectId(course_id)})
    await db.chat_messages.delete_many({"course_id": ObjectId(course_id)})
    await db.chat_sessions.delete_many({"course_id": ObjectId(course_id)})
    
    return {"message": "Course deleted successfully"}

def serialize_datetime(obj):
    """JSON serializer for datetime objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def clean_function_results(data):
    """Recursively clean function results to remove non-serializable objects"""
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            if isinstance(value, datetime):
                cleaned[key] = value.isoformat()
            elif isinstance(value, (dict, list)):
                cleaned[key] = clean_function_results(value)
            elif hasattr(value, '__dict__'):
                # Skip complex objects that can't be serialized
                continue
            else:
                cleaned[key] = value
        return cleaned
    elif isinstance(data, list):
        return [clean_function_results(item) for item in data]
    elif isinstance(data, datetime):
        return data.isoformat()
    else:
        return data

async def stream_response(text: str, course_id: str = None, function_results: dict = None):
    """Stream response with standardized event format"""
    sequence = 0
    
    # Debug logging
    print(f"🔄 [STREAM_RESPONSE] Starting stream for text: {text[:100]}...")
    print(f"   📋 Course ID: {course_id}")
    print(f"   🔧 Function Results: {function_results}")
    
    # First send metadata if available
    if course_id or function_results:
        sequence += 1
        
        # Clean function results to remove non-serializable objects
        cleaned_results = clean_function_results(function_results or {})
        
        metadata = {
            "type": "metadata",
            "data": {
                "course_id": course_id,
                "function_results": cleaned_results
            },
            "sequence": sequence,
            "timestamp": datetime.utcnow().isoformat()
        }
        print(f"   📤 Sending metadata: {metadata}")
        yield f"data: {json.dumps(metadata, default=serialize_datetime)}\n\n"
    
    # Ensure we have text content to send
    if text and text.strip():
        # Stream the complete text at once (no character-by-character)
        sequence += 1
        text_event = {
            "type": "text",
            "data": {
                "content": text,
                "complete": True
            },
            "sequence": sequence,
            "timestamp": datetime.utcnow().isoformat()
        }
        print(f"   📤 Sending text event: {text_event['type']} with {len(text)} characters")
        yield f"data: {json.dumps(text_event)}\n\n"
    else:
        print(f"   ⚠️ No text content to send, text was: '{text}'")
    
    # Send completion signal
    sequence += 1
    completion = {
        "type": "complete",
        "data": {},
        "sequence": sequence,
        "timestamp": datetime.utcnow().isoformat()
    }
    print(f"   📤 Sending completion: {completion}")
    yield f"data: {json.dumps(completion)}\n\n"
    print(f"✅ [STREAM_RESPONSE] Stream complete")

async def stream_material_content_response(text: str, course_id: str = None, function_results: dict = None, streaming_events: list = None):
    """Stream response with material content streaming events"""
    sequence = 0
    
    # Debug logging
    print(f"🎨 [MATERIAL_CONTENT_STREAM] Starting material content stream")
    print(f"   📋 Course ID: {course_id}")
    print(f"   📝 Text length: {len(text) if text else 0}")
    print(f"   🎬 Streaming events: {len(streaming_events) if streaming_events else 0}")
    
    # First send metadata if available
    if course_id or function_results:
        sequence += 1
        
        # Clean function results to remove non-serializable objects
        cleaned_results = clean_function_results(function_results or {})
        
        metadata = {
            "type": "metadata",
            "data": {
                "course_id": course_id,
                "function_results": cleaned_results
            },
            "sequence": sequence,
            "timestamp": datetime.utcnow().isoformat()
        }
        print(f"   📤 Sending metadata: {metadata}")
        yield f"data: {json.dumps(metadata, default=serialize_datetime)}\n\n"
    
    # Send text content if available
    if text and text.strip():
        sequence += 1
        text_event = {
            "type": "text",
            "data": {
                "content": text,
                "complete": True
            },
            "sequence": sequence,
            "timestamp": datetime.utcnow().isoformat()
        }
        print(f"   📤 Sending text event with {len(text)} characters")
        yield f"data: {json.dumps(text_event)}\n\n"
    
    # Stream material content events
    if streaming_events:
        print(f"   🎬 Streaming {len(streaming_events)} material content events...")
        for event in streaming_events:
            sequence += 1
            # Add sequence and timestamp to each event
            event_with_metadata = {
                **event,
                "sequence": sequence,
                "timestamp": datetime.utcnow().isoformat()
            }
            print(f"   📤 Sending material event: {event.get('type')} - {event.get('message', 'No message')}")
            yield f"data: {json.dumps(event_with_metadata, default=serialize_datetime)}\n\n"
            
            # Small delay between events for better frontend processing
            await asyncio.sleep(0.1)
    
    # Send completion signal
    sequence += 1
    completion = {
        "type": "complete",
        "data": {},
        "sequence": sequence,
        "timestamp": datetime.utcnow().isoformat()
    }
    print(f"   📤 Sending completion: {completion}")
    yield f"data: {json.dumps(completion)}\n\n"
    print(f"✅ [MATERIAL_CONTENT_STREAM] Stream complete")

@router.post("/create-draft")
async def create_draft_course(
    current_user: UserInDB = Depends(get_current_user)
):
    """Create a draft course for immediate chat storage or return existing one"""
    db = await get_database()
    
    # Check if there's already a draft course for this user
    existing_draft = await db.courses.find_one({
        "user_id": current_user.id,
        "status": "draft",
        "name": "Untitled Course"
    })
    
    if existing_draft:
        # Return existing draft course
        return {"course_id": str(existing_draft["_id"])}
    
    # Create new draft course if none exists
    course_data = {
        "name": "Untitled Course",
        "description": "",
        "user_id": current_user.id,
        "structure": {},
        "status": "draft",
        "workflow_step": "course_naming",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.courses.insert_one(course_data)
    course_id = str(result.inserted_id)
    
    # Create chat session
    session_data = {
        "course_id": ObjectId(course_id),
        "user_id": current_user.id,
        "context_summary": "",
        "last_activity": datetime.utcnow(),
        "total_messages": 0,
        "context_window_start": 0
    }
    
    await db.chat_sessions.insert_one(session_data)
    
    return {"course_id": course_id}

@router.post("/chat")
async def chat_without_course(
    message_data: ChatMessageCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    """Chat endpoint for initial course creation (no course ID yet)"""
    try:
        print(f"Processing chat message: {message_data.content}")
        print(f"User ID: {current_user.id}")
        
        result = await conversation_orchestrator.process_message(
            course_id=None,
            user_id=str(current_user.id),
            user_message=message_data.content
        )
        
        print(f"Agent result: {result}")
        
        # Check if result contains material content streaming events
        streaming_events = result.get("streaming_events")
        if streaming_events and result.get("material_content_streaming"):
            print(f"🎨 [CHAT WITHOUT COURSE] Using material content streaming with {len(streaming_events)} events")
            return StreamingResponse(
                stream_material_content_response(
                    result["response"],
                    result.get("course_id"),
                    result.get("function_results", {}),
                    streaming_events
                ),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/event-stream"
                }
            )
        else:
            # Use regular streaming for non-material content
            return StreamingResponse(
                stream_response(
                    result["response"],
                    result.get("course_id"),
                    result.get("function_results", {})
                ),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/event-stream"
                }
            )
        
    except Exception as e:
        import traceback
        print(f"Route error: {e}")
        print(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )

@router.post("/{course_id}/chat")
async def chat_with_course(
    course_id: str,
    message_data: ChatMessageCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    """Chat endpoint for existing course"""
    db = await get_database()
    
    if not ObjectId.is_valid(course_id):
        raise HTTPException(status_code=400, detail="Invalid course ID")
    
    # Verify course belongs to user
    course = await db.courses.find_one({
        "_id": ObjectId(course_id),
        "user_id": current_user.id
    })
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    try:
        print(f"Processing course chat message: {message_data.content}")
        print(f"Course ID: {course_id}, User ID: {current_user.id}")
        
        # Check for context hints from frontend
        context_hints = getattr(message_data, 'context_hints', None)
        if context_hints:
            print(f"📋 Received context hints from frontend: {context_hints}")
        
        result = await conversation_orchestrator.process_message(
            course_id=course_id,
            user_id=str(current_user.id),
            user_message=message_data.content,
            context_hints=context_hints
        )
        
        print(f"Agent result: {result}")
        
        # Check if result contains material content streaming events
        streaming_events = result.get("streaming_events")
        if streaming_events and result.get("material_content_streaming"):
            print(f"🎨 [CHAT WITH COURSE] Using material content streaming with {len(streaming_events)} events")
            return StreamingResponse(
                stream_material_content_response(
                    result["response"],
                    result.get("course_id"),
                    result.get("function_results", {}),
                    streaming_events
                ),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/event-stream"
                }
            )
        else:
            # Use regular streaming for non-material content
            return StreamingResponse(
                stream_response(
                    result["response"],
                    result.get("course_id"),
                    result.get("function_results", {})
                ),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/event-stream"
                }
            )
        
    except Exception as e:
        import traceback
        print(f"Route error: {e}")
        print(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )

@router.get("/{course_id}/messages", response_model=List[ChatMessageResponse])
async def get_course_messages(
    course_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get chat messages for a course"""
    print(f"\n📨 [GET MESSAGES] Retrieving ALL messages for course: {course_id}")
    print(f"   👤 User: {current_user.id}")
    print(f"   📏 Limit: No limit (retrieving all messages)")
    
    db = await get_database()
    
    if not ObjectId.is_valid(course_id):
        print(f"❌ [GET MESSAGES] Invalid course ID: {course_id}")
        raise HTTPException(status_code=400, detail="Invalid course ID")
    
    # Verify course belongs to user
    course = await db.courses.find_one({
        "_id": ObjectId(course_id),
        "user_id": current_user.id
    })
    
    if not course:
        print(f"❌ [GET MESSAGES] Course not found: {course_id}")
        raise HTTPException(status_code=404, detail="Course not found")
    
    print(f"✅ [GET MESSAGES] Course found: {course.get('name')}")
    
    # Get ALL messages (no limit)
    messages_cursor = db.chat_messages.find({
        "course_id": ObjectId(course_id)
    }).sort("message_index", 1)
    
    messages = await messages_cursor.to_list(None)  # None means no limit
    
    print(f"📊 [GET MESSAGES] Found {len(messages)} messages in database")
    for i, msg in enumerate(messages):
        print(f"   📝 Message {i+1}: {msg.get('role')} - {msg.get('content')[:100]}...")
    
    # Convert ObjectIds to strings for each message
    for message in messages:
        message["_id"] = str(message["_id"])
        message["course_id"] = str(message["course_id"])
        message["user_id"] = str(message["user_id"])
    
    formatted_messages = [ChatMessageResponse(**message) for message in messages]
    print(f"✅ [GET MESSAGES] Returning {len(formatted_messages)} formatted messages")
    
    return formatted_messages

@router.get("/{course_id}/session", response_model=ChatSessionResponse)
async def get_chat_session(
    course_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get chat session info for a course"""
    db = await get_database()
    
    if not ObjectId.is_valid(course_id):
        raise HTTPException(status_code=400, detail="Invalid course ID")
    
    # Verify course belongs to user
    course = await db.courses.find_one({
        "_id": ObjectId(course_id),
        "user_id": current_user.id
    })
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Get session
    session = await db.chat_sessions.find_one({
        "course_id": ObjectId(course_id)
    })
    
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    return ChatSessionResponse(**session)

@router.post("/{course_id}/upload-course-design")
async def upload_course_design(
    course_id: str,
    curriculum_file: UploadFile = File(...),
    pedagogy_file: Optional[UploadFile] = File(None),
    current_user: UserInDB = Depends(get_current_user)
):
    """Upload course design materials (curriculum required, pedagogy optional)"""
    db = await get_database()
    
    if not ObjectId.is_valid(course_id):
        raise HTTPException(status_code=400, detail="Invalid course ID")
    
    # Verify course belongs to user
    course = await db.courses.find_one({
        "_id": ObjectId(course_id),
        "user_id": current_user.id
    })
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Validate curriculum file type
    if not curriculum_file.filename.endswith('.md'):
        raise HTTPException(status_code=400, detail="Curriculum file must be .md format")
    
    # Validate pedagogy file type if provided
    if pedagogy_file and not pedagogy_file.filename.endswith('.md'):
        raise HTTPException(status_code=400, detail="Pedagogy file must be .md format")
    
    try:
        # Read curriculum file content
        curriculum_content = await curriculum_file.read()
        curriculum_text = curriculum_content.decode('utf-8')
        
        # Read pedagogy file content if provided
        pedagogy_text = None
        if pedagogy_file:
            pedagogy_content = await pedagogy_file.read()
            pedagogy_text = pedagogy_content.decode('utf-8')
        
        # Get course design agent and process materials
        course_design_agent = service_container.get_course_design_agent()
        
        # Process uploaded materials into unified course design
        result = await course_design_agent._process_uploaded_materials(
            course_id=course_id,
            curriculum_content=curriculum_text,
            pedagogy_content=pedagogy_text
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to process materials: {result.get('error')}"
            )
        
        return {
            "success": True,
            "message": "Course design materials processed successfully",
            "r2_key": result["r2_key"],
            "public_url": result["public_url"],
            "has_pedagogy": pedagogy_text is not None,
            "version": result["version"]
        }
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be valid UTF-8 text")
    except Exception as e:
        import traceback
        print(f"Upload error: {e}")
        print(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload curriculum: {str(e)}"
        )

async def stream_course_design_generation(course_id: str, user_id: str, focus: Optional[str] = None):
    """Stream course design generation events with FIXED auto-trigger logic"""
    print(f"🚀🚀🚀 [COURSE DESIGN ROUTE] Starting FIXED stream_course_design_generation")
    print(f"   📋 Course ID: {course_id}")
    print(f"   👤 User ID: {user_id}")
    print(f"   🎯 Focus: {focus}")
    
    course_design_agent = service_container.get_course_design_agent()
    course_structure_agent = service_container.get_course_structure_agent()
    message_service = service_container.get_message_service()
    
    try:
        print(f"🔄 [COURSE DESIGN ROUTE] Starting to iterate through agent events...")
        event_count = 0
        completion_event_received = False
        
        async for event in course_design_agent.stream_course_design_generation(course_id, focus, user_id):
            event_count += 1
            print(f"🔍 [COURSE DESIGN ROUTE] Event #{event_count}: {event.get('type')}")
            
            # CRITICAL FIX: Always yield the event first, then check for auto-trigger
            yield f"data: {json.dumps(event)}\n\n"
            
            # Check for completion event with workflow transition
            if event.get("type") == "complete":
                completion_event_received = True
                workflow_transition = event.get("workflow_transition", {})
                should_auto_trigger = workflow_transition.get("trigger_automatically") is True
                
                print(f"🎯 [COURSE DESIGN ROUTE] COMPLETION EVENT DETECTED!")
                print(f"   🔍 Workflow transition: {workflow_transition}")
                print(f"   🔍 Should auto-trigger: {should_auto_trigger}")
                
                if should_auto_trigger:
                    print(f"🚀🚀🚀 [COURSE DESIGN ROUTE] AUTO-TRIGGER ACTIVATED!")
                    
                    # Small delay for frontend processing
                    await asyncio.sleep(0.5)
                    
                    # Send transition signal
                    transition_event = {
                        "type": "workflow_transition",
                        "content": "🎯 **Starting Content Structure Generation**\n\nAnalyzing course design and creating content structure...",
                        "next_step": "content_structure_generation",
                        "next_agent": "course_structure",
                        "automatic": True
                    }
                    print(f"🔄 [COURSE DESIGN ROUTE] Sending transition event")
                    yield f"data: {json.dumps(transition_event)}\n\n"
                    
                    # Store transition message in chat
                    try:
                        transition_message = "🎯 **Starting Content Structure Generation**\n\nAnalyzing course design and creating comprehensive content structure:\n\n- Parsing course modules and chapters\n- Creating content material checklist\n- Organizing learning objectives and assessments\n- Preparing for individual content creation\n\n*← Content structure will appear in real-time*"
                        await message_service.store_message(course_id, user_id, transition_message, "assistant")
                        print(f"✅ [COURSE DESIGN ROUTE] Stored transition message")
                    except Exception as e:
                        print(f"❌ [COURSE DESIGN ROUTE] Failed to store transition message: {e}")
                    
                    # CRITICAL FIX: Direct agent invocation with proper error handling
                    try:
                        print(f"🎬 [COURSE DESIGN ROUTE] Invoking CourseStructureAgent...")
                        
                        content_event_count = 0
                        async for content_event in course_structure_agent.stream_structure_generation(
                            course_id=course_id, 
                            preferences=None, 
                            user_id=user_id
                        ):
                            content_event_count += 1
                            print(f"📤 [COURSE DESIGN ROUTE] Content event #{content_event_count}: {content_event.get('type')}")
                            
                            # Validate and yield content event
                            if isinstance(content_event, dict):
                                yield f"data: {json.dumps(content_event)}\n\n"
                            
                            # Break on completion
                            if content_event.get("type") == "complete":
                                print(f"✅ [COURSE DESIGN ROUTE] Content structure completed after {content_event_count} events")
                                break
                        
                        if content_event_count == 0:
                            print(f"⚠️ [COURSE DESIGN ROUTE] No events from CourseStructureAgent!")
                            error_event = {
                                "type": "error", 
                                "content": "Content structure generation produced no events"
                            }
                            yield f"data: {json.dumps(error_event)}\n\n"
                        else:
                            print(f"🎉 [COURSE DESIGN ROUTE] Auto-trigger completed successfully!")
                        
                    except Exception as content_error:
                        print(f"❌ [COURSE DESIGN ROUTE] Content structure error: {content_error}")
                        import traceback
                        print(f"Full traceback: {traceback.format_exc()}")
                        error_event = {
                            "type": "error", 
                            "content": f"Content structure generation failed: {str(content_error)}"
                        }
                        yield f"data: {json.dumps(error_event)}\n\n"
                    
                    # Exit after auto-trigger
                    print(f"🔚 [COURSE DESIGN ROUTE] Exiting after successful auto-trigger")
                    break
                else:
                    print(f"🔍 [COURSE DESIGN ROUTE] Completion without auto-trigger")
            
        print(f"✅ [COURSE DESIGN ROUTE] Stream completed. Events: {event_count}, Completion: {completion_event_received}")
                
    except Exception as e:
        print(f"❌ [COURSE DESIGN ROUTE] CRITICAL ERROR: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        error_event = {"type": "error", "content": f"Generation failed: {str(e)}"}
        yield f"data: {json.dumps(error_event)}\n\n"

async def stream_course_design_modification(course_id: str, user_id: str, modification_request: str):
    """Stream course design modification events"""
    course_design_agent = service_container.get_course_design_agent()
    
    try:
        async for event in course_design_agent.stream_course_design_modification(course_id, modification_request, user_id):
            yield f"data: {json.dumps(event)}\n\n"
    except Exception as e:
        error_event = {"type": "error", "content": f"Modification failed: {str(e)}"}
        yield f"data: {json.dumps(error_event)}\n\n"

async def stream_research_generation(course_id: str, user_id: str, focus_area: Optional[str] = None):
    """Stream research generation events"""
    initial_research_agent = service_container.get_initial_research_agent()
    course_design_agent = service_container.get_course_design_agent()
    message_service = service_container.get_message_service()
    
    try:
        async for event in initial_research_agent.stream_research_generation(course_id, focus_area, user_id):
            # Check if this is a completion event with workflow transition
            if event.get("type") == "complete" and event.get("workflow_transition", {}).get("trigger_automatically"):
                print(f"🎯 [RESEARCH ROUTE] Research completed - automatically triggering course design generation")
                
                # Send the research completion event first
                yield f"data: {json.dumps(event)}\n\n"
                
                # Add a small delay to ensure frontend processes the research completion
                import asyncio
                await asyncio.sleep(0.5)
                
                # Send transition signal
                transition_event = {
                    "type": "workflow_transition",
                    "content": "🎯 **Starting Course Design Generation**\n\nBuilding upon comprehensive research findings...",
                    "next_step": "course_design_generation",
                    "next_agent": "course_design"
                }
                yield f"data: {json.dumps(transition_event)}\n\n"
                
                # Store the course design start message in chat history
                course_design_start_message = "🎯 **Starting Course Design Generation**\n\nBuilding comprehensive course design based on research findings:\n\n- Curriculum structure with learning objectives\n- Pedagogy strategies and teaching methods\n- Assessment frameworks and rubrics\n- Current 2025 technologies and best practices\n\n*← Course design will appear in real-time*"
                try:
                    print(f"💬 [RESEARCH ROUTE] Storing course design start message in chat...")
                    await message_service.store_message(course_id, user_id, course_design_start_message, "assistant")
                    print(f"✅ [RESEARCH ROUTE] Successfully stored course design start message")
                except Exception as e:
                    print(f"❌ [RESEARCH ROUTE] Failed to store course design start message: {e}")
                
                # Automatically start course design generation
                print(f"🚀 [RESEARCH ROUTE] Auto-triggering course design generation...")
                try:
                    async for design_event in course_design_agent.stream_course_design_generation(course_id, focus_area, user_id):
                        yield f"data: {json.dumps(design_event)}\n\n"
                except Exception as design_error:
                    print(f"❌ [RESEARCH ROUTE] Error in auto-triggered course design: {design_error}")
                    error_event = {"type": "error", "content": f"Course design generation failed: {str(design_error)}"}
                    yield f"data: {json.dumps(error_event)}\n\n"
                
                break  # Exit the research stream loop since we've transitioned
            else:
                # Regular research event - pass through
                yield f"data: {json.dumps(event)}\n\n"
                
    except Exception as e:
        error_event = {"type": "error", "content": f"Research failed: {str(e)}"}
        yield f"data: {json.dumps(error_event)}\n\n"

from pydantic import BaseModel

class CourseDesignGenerateRequest(BaseModel):
    focus: Optional[str] = None

class CourseDesignModifyRequest(BaseModel):
    modification_request: str

class ResearchGenerateRequest(BaseModel):
    focus_area: Optional[str] = None

class ContentStructureApprovalRequest(BaseModel):
    approved: bool
    modifications: Optional[str] = None

class ContentApprovalRequest(BaseModel):
    material_id: str
    approved: bool
    modifications: Optional[str] = None

class ContentGenerationRequest(BaseModel):
    focus: Optional[str] = None

@router.post("/{course_id}/generate-course-design")
async def generate_course_design_stream(
    course_id: str,
    request: CourseDesignGenerateRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """Stream comprehensive course design generation in real-time"""
    print(f"\n🎯🎯🎯 [STREAMING ENDPOINT HIT] Course design generation requested for course: {course_id}")
    print(f"   👤 User: {current_user.id}")
    print(f"   🎯 Focus: {request.focus}")
    print(f"   📋 Request body: {request}")
    
    try:
        db = await get_database()
        
        if not ObjectId.is_valid(course_id):
            print(f"❌ [STREAMING ENDPOINT] Invalid course ID: {course_id}")
            raise HTTPException(status_code=400, detail="Invalid course ID")
        
        # Verify course belongs to user
        course = await db.courses.find_one({
            "_id": ObjectId(course_id),
            "user_id": current_user.id
        })
        
        if not course:
            print(f"❌ [STREAMING ENDPOINT] Course not found: {course_id}")
            raise HTTPException(status_code=404, detail="Course not found")
        
        print(f"✅ [STREAMING ENDPOINT] Course found: {course.get('name')}")
        print(f"🚀 [STREAMING ENDPOINT] Starting streaming response...")
        
        return StreamingResponse(
            stream_course_design_generation(course_id, str(current_user.id), request.focus),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )
    except Exception as e:
        print(f"❌❌❌ [STREAMING ENDPOINT] CRITICAL ERROR: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise e

# Test endpoint to verify routing
@router.get("/{course_id}/test-streaming")
async def test_streaming_endpoint(
    course_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Test endpoint to verify streaming route is working"""
    print(f"🧪🧪🧪 [TEST ENDPOINT HIT] Course ID: {course_id}, User: {current_user.id}")
    return {"message": "Streaming endpoint is reachable", "course_id": course_id, "user_id": str(current_user.id)}

@router.post("/{course_id}/modify-course-design")
async def modify_course_design_stream(
    course_id: str,
    request: CourseDesignModifyRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """Stream course design modification in real-time"""
    print(f"\n🔄🔄🔄 [MODIFICATION ENDPOINT HIT] Course design modification requested for course: {course_id}")
    print(f"   👤 User: {current_user.id}")
    print(f"   🔧 Modification: {request.modification_request}")
    print(f"   📋 Request body: {request}")
    
    try:
        db = await get_database()
        
        if not ObjectId.is_valid(course_id):
            print(f"❌ [MODIFICATION ENDPOINT] Invalid course ID: {course_id}")
            raise HTTPException(status_code=400, detail="Invalid course ID")
        
        # Verify course belongs to user
        course = await db.courses.find_one({
            "_id": ObjectId(course_id),
            "user_id": current_user.id
        })
        
        if not course:
            print(f"❌ [MODIFICATION ENDPOINT] Course not found: {course_id}")
            raise HTTPException(status_code=404, detail="Course not found")
        
        print(f"✅ [MODIFICATION ENDPOINT] Course found: {course.get('name')}")
        print(f"🚀 [MODIFICATION ENDPOINT] Starting streaming response...")
        
        return StreamingResponse(
            stream_course_design_modification(course_id, str(current_user.id), request.modification_request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )
    except Exception as e:
        print(f"❌❌❌ [MODIFICATION ENDPOINT] CRITICAL ERROR: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise e

class FileSaveRequest(BaseModel):
    file_name: str
    content: str
    file_type: str = "markdown"

@router.post("/{course_id}/save-file")
async def save_file_content(
    course_id: str,
    request: FileSaveRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """Save file content to R2 storage and update database"""
    print(f"\n💾💾💾 [SAVE FILE ENDPOINT HIT] Saving file for course: {course_id}")
    print(f"   👤 User: {current_user.id}")
    print(f"   📄 File: {request.file_name}")
    print(f"   📝 Content length: {len(request.content)}")
    
    try:
        db = await get_database()
        
        if not ObjectId.is_valid(course_id):
            print(f"❌ [SAVE FILE ENDPOINT] Invalid course ID: {course_id}")
            raise HTTPException(status_code=400, detail="Invalid course ID")
        
        # Verify course belongs to user
        course = await db.courses.find_one({
            "_id": ObjectId(course_id),
            "user_id": current_user.id
        })
        
        if not course:
            print(f"❌ [SAVE FILE ENDPOINT] Course not found: {course_id}")
            raise HTTPException(status_code=404, detail="Course not found")
        
        print(f"✅ [SAVE FILE ENDPOINT] Course found: {course.get('name')}")
        
        # Get R2 storage service
        r2_service = R2StorageService()
        
        # Determine the file type and save accordingly
        if request.file_name in ['course-design.md', 'curriculum.md']:
            # This is a course design file - save as course design
            print(f"📋 [SAVE FILE ENDPOINT] Saving as course design file...")
            
            # Get current version and increment
            current_version = course.get("course_design_version", course.get("curriculum_version", 1))
            new_version = current_version + 1
            
            # Upload to R2
            upload_result = await r2_service.upload_course_design(
                course_id=course_id,
                content=request.content,
                source="edited",
                version=new_version
            )
            
            if not upload_result.get("success"):
                error_msg = f"Failed to upload file: {upload_result.get('error')}"
                print(f"❌ [SAVE FILE ENDPOINT] {error_msg}")
                raise HTTPException(status_code=500, detail=error_msg)
            
            # Update course with new R2 information
            update_result = await db.courses.update_one(
                {"_id": ObjectId(course_id)},
                {"$set": {
                    "course_design_r2_key": upload_result["r2_key"],
                    "course_design_public_url": upload_result["public_url"],
                    "course_design_version": new_version,
                    "course_design_updated_at": datetime.utcnow()
                }}
            )
            
            print(f"✅ [SAVE FILE ENDPOINT] Course design saved successfully")
            return {
                "success": True,
                "message": "Course design saved successfully",
                "r2_key": upload_result["r2_key"],
                "public_url": upload_result["public_url"],
                "version": new_version
            }
        
        else:
            # This is a regular file - save as generic file
            print(f"📄 [SAVE FILE ENDPOINT] Saving as regular file...")
            
            # For now, we'll save regular files to R2 as well
            # In a more complex system, you might have different storage for different file types
            file_key = f"courses/{course_id}/files/{request.file_name}"
            
            upload_result = await r2_service.upload_file_content(
                key=file_key,
                content=request.content,
                content_type="text/markdown" if request.file_type == "markdown" else "text/plain"
            )
            
            if not upload_result.get("success"):
                error_msg = f"Failed to upload file: {upload_result.get('error')}"
                print(f"❌ [SAVE FILE ENDPOINT] {error_msg}")
                raise HTTPException(status_code=500, detail=error_msg)
            
            print(f"✅ [SAVE FILE ENDPOINT] Regular file saved successfully")
            return {
                "success": True,
                "message": "File saved successfully",
                "r2_key": upload_result.get("r2_key", file_key),
                "public_url": upload_result.get("public_url")
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌❌❌ [SAVE FILE ENDPOINT] CRITICAL ERROR: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )

@router.post("/{course_id}/generate-research")
async def generate_research_stream(
    course_id: str,
    request: ResearchGenerateRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """Stream comprehensive research generation in real-time"""
    print(f"\n🔬🔬🔬 [RESEARCH ENDPOINT HIT] Research generation requested for course: {course_id}")
    print(f"   👤 User: {current_user.id}")
    print(f"   🎯 Focus Area: {request.focus_area}")
    print(f"   📋 Request body: {request}")
    
    try:
        db = await get_database()
        
        if not ObjectId.is_valid(course_id):
            print(f"❌ [RESEARCH ENDPOINT] Invalid course ID: {course_id}")
            raise HTTPException(status_code=400, detail="Invalid course ID")
        
        # Verify course belongs to user
        course = await db.courses.find_one({
            "_id": ObjectId(course_id),
            "user_id": current_user.id
        })
        
        if not course:
            print(f"❌ [RESEARCH ENDPOINT] Course not found: {course_id}")
            raise HTTPException(status_code=404, detail="Course not found")
        
        print(f"✅ [RESEARCH ENDPOINT] Course found: {course.get('name')}")
        print(f"🚀 [RESEARCH ENDPOINT] Starting streaming response...")
        
        return StreamingResponse(
            stream_research_generation(course_id, str(current_user.id), request.focus_area),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )
    except Exception as e:
        print(f"❌❌❌ [RESEARCH ENDPOINT] CRITICAL ERROR: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise e

# Backward compatibility endpoint
@router.post("/{course_id}/generate-curriculum")
async def generate_curriculum_stream_legacy(
    course_id: str,
    request: CourseDesignGenerateRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """Legacy endpoint - redirects to course design generation"""
    return await generate_course_design_stream(course_id, request, current_user)

# ============================================================================
# CONTENT CREATOR AGENT ENDPOINTS
# ============================================================================

async def stream_content_structure_generation(course_id: str, user_id: str, focus: Optional[str] = None):
    """Stream content structure generation events"""
    course_structure_agent = service_container.get_course_structure_agent()
    
    try:
        # Fix method signature - pass user_id as named parameter
        async for event in course_structure_agent.stream_structure_generation(course_id, preferences=None, user_id=user_id):
            yield f"data: {json.dumps(event)}\n\n"
    except Exception as e:
        error_event = {"type": "error", "content": f"Content structure generation failed: {str(e)}"}
        yield f"data: {json.dumps(error_event)}\n\n"

@router.post("/{course_id}/generate-content-structure")
async def generate_content_structure_stream(
    course_id: str,
    request: ContentGenerationRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """Stream content structure generation in real-time"""
    print(f"\n📚📚📚 [CONTENT STRUCTURE ENDPOINT HIT] Content structure generation requested for course: {course_id}")
    print(f"   👤 User: {current_user.id}")
    print(f"   🎯 Focus: {request.focus}")
    print(f"   📋 Request body: {request}")
    
    try:
        db = await get_database()
        
        if not ObjectId.is_valid(course_id):
            print(f"❌ [CONTENT STRUCTURE ENDPOINT] Invalid course ID: {course_id}")
            raise HTTPException(status_code=400, detail="Invalid course ID")
        
        # Verify course belongs to user
        course = await db.courses.find_one({
            "_id": ObjectId(course_id),
            "user_id": current_user.id
        })
        
        if not course:
            print(f"❌ [CONTENT STRUCTURE ENDPOINT] Course not found: {course_id}")
            raise HTTPException(status_code=404, detail="Course not found")
        
        print(f"✅ [CONTENT STRUCTURE ENDPOINT] Course found: {course.get('name')}")
        print(f"🚀 [CONTENT STRUCTURE ENDPOINT] Starting streaming response...")
        
        return StreamingResponse(
            stream_content_structure_generation(course_id, str(current_user.id), request.focus),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )
    except Exception as e:
        print(f"❌❌❌ [CONTENT STRUCTURE ENDPOINT] CRITICAL ERROR: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise e

@router.post("/{course_id}/approve-content-structure")
async def approve_content_structure(
    course_id: str,
    request: ContentStructureApprovalRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """Approve or request modifications to content structure"""
    print(f"\n✅✅✅ [CONTENT STRUCTURE APPROVAL ENDPOINT HIT] Approval for course: {course_id}")
    print(f"   👤 User: {current_user.id}")
    print(f"   ✅ Approved: {request.approved}")
    print(f"   🔧 Modifications: {request.modifications}")
    
    try:
        db = await get_database()
        
        if not ObjectId.is_valid(course_id):
            print(f"❌ [CONTENT STRUCTURE APPROVAL] Invalid course ID: {course_id}")
            raise HTTPException(status_code=400, detail="Invalid course ID")
        
        # Verify course belongs to user
        course = await db.courses.find_one({
            "_id": ObjectId(course_id),
            "user_id": current_user.id
        })
        
        if not course:
            print(f"❌ [CONTENT STRUCTURE APPROVAL] Course not found: {course_id}")
            raise HTTPException(status_code=404, detail="Course not found")
        
        print(f"✅ [CONTENT STRUCTURE APPROVAL] Course found: {course.get('name')}")
        
        # Get course structure agent
        course_structure_agent = service_container.get_course_structure_agent()
        
        # Process approval
        result = await course_structure_agent.process_structure_approval(
            course_id=course_id,
            user_id=str(current_user.id),
            approved=request.approved,
            modifications=request.modifications
        )
        
        if not result.get("success"):
            error_msg = f"Failed to process approval: {result.get('error')}"
            print(f"❌ [CONTENT STRUCTURE APPROVAL] {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        print(f"✅ [CONTENT STRUCTURE APPROVAL] Approval processed successfully")
        return {
            "success": True,
            "message": result.get("message", "Content structure approval processed"),
            "next_step": result.get("next_step"),
            "workflow_updated": result.get("workflow_updated", False)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌❌❌ [CONTENT STRUCTURE APPROVAL] CRITICAL ERROR: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process content structure approval: {str(e)}"
        )

async def stream_material_content_generation(course_id: str, user_id: str, material_id: Optional[str] = None):
    """Stream material content generation events"""
    material_content_generator_agent = service_container.get_material_content_generator_agent()
    
    try:
        # If material_id is provided, generate content for specific material
        if material_id:
            print(f"🎯 [MATERIAL CONTENT STREAM] Generating content for specific material: {material_id}")
            async for event in material_content_generator_agent.stream_material_content_generation(course_id, material_id, user_id):
                yield f"data: {json.dumps(event)}\n\n"
        else:
            # Start content generation process (will auto-generate first material)
            print(f"🚀 [MATERIAL CONTENT STREAM] Starting content generation process for course: {course_id}")
            async for event in material_content_generator_agent.stream_content_generation_start(course_id, user_id):
                yield f"data: {json.dumps(event)}\n\n"
    except Exception as e:
        error_event = {"type": "error", "content": f"Material content generation failed: {str(e)}"}
        yield f"data: {json.dumps(error_event)}\n\n"

class MaterialContentGenerationRequest(BaseModel):
    material_id: Optional[str] = None

@router.post("/{course_id}/generate-material-content")
async def generate_material_content_stream(
    course_id: str,
    request: MaterialContentGenerationRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """Stream material content generation in real-time"""
    print(f"\n🎨🎨🎨 [MATERIAL CONTENT ENDPOINT HIT] Material content generation requested for course: {course_id}")
    print(f"   👤 User: {current_user.id}")
    print(f"   📝 Material ID: {request.material_id}")
    print(f"   📋 Request body: {request}")
    
    try:
        db = await get_database()
        
        if not ObjectId.is_valid(course_id):
            print(f"❌ [MATERIAL CONTENT ENDPOINT] Invalid course ID: {course_id}")
            raise HTTPException(status_code=400, detail="Invalid course ID")
        
        # Verify course belongs to user
        course = await db.courses.find_one({
            "_id": ObjectId(course_id),
            "user_id": current_user.id
        })
        
        if not course:
            print(f"❌ [MATERIAL CONTENT ENDPOINT] Course not found: {course_id}")
            raise HTTPException(status_code=404, detail="Course not found")
        
        print(f"✅ [MATERIAL CONTENT ENDPOINT] Course found: {course.get('name')}")
        print(f"🚀 [MATERIAL CONTENT ENDPOINT] Starting streaming response...")
        
        return StreamingResponse(
            stream_material_content_generation(course_id, str(current_user.id), request.material_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )
    except Exception as e:
        print(f"❌❌❌ [MATERIAL CONTENT ENDPOINT] CRITICAL ERROR: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise e

# Add a new endpoint specifically for chat-based material content generation
class MaterialContentChatRequest(BaseModel):
    message: str

@router.post("/{course_id}/chat-material-content")
async def chat_material_content_stream(
    course_id: str,
    request: MaterialContentChatRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """Stream material content generation from chat messages in real-time"""
    print(f"\n🎨💬 [CHAT MATERIAL CONTENT ENDPOINT] Chat-based material content generation for course: {course_id}")
    print(f"   👤 User: {current_user.id}")
    print(f"   💬 Message: {request.message}")
    
    try:
        db = await get_database()
        
        if not ObjectId.is_valid(course_id):
            print(f"❌ [CHAT MATERIAL CONTENT] Invalid course ID: {course_id}")
            raise HTTPException(status_code=400, detail="Invalid course ID")
        
        # Verify course belongs to user
        course = await db.courses.find_one({
            "_id": ObjectId(course_id),
            "user_id": current_user.id
        })
        
        if not course:
            print(f"❌ [CHAT MATERIAL CONTENT] Course not found: {course_id}")
            raise HTTPException(status_code=404, detail="Course not found")
        
        print(f"✅ [CHAT MATERIAL CONTENT] Course found: {course.get('name')}")
        print(f"🚀 [CHAT MATERIAL CONTENT] Processing through conversation orchestrator...")
        
        # Process through conversation orchestrator to get streaming events
        result = await conversation_orchestrator.process_message(
            course_id=course_id,
            user_id=str(current_user.id),
            user_message=request.message
        )
        
        print(f"🎯 [CHAT MATERIAL CONTENT] Orchestrator result: {result.keys()}")
        
        # Check if we have streaming events
        streaming_events = result.get("streaming_events")
        if streaming_events and result.get("material_content_streaming"):
            print(f"🎬 [CHAT MATERIAL CONTENT] Found {len(streaming_events)} streaming events")
            
            # Stream the events directly
            async def stream_chat_material_events():
                sequence = 0
                
                # Send initial response
                if result.get("response"):
                    sequence += 1
                    text_event = {
                        "type": "text",
                        "data": {"content": result["response"]},
                        "sequence": sequence,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    yield f"data: {json.dumps(text_event)}\n\n"
                
                # Stream material content events
                for event in streaming_events:
                    sequence += 1
                    event_with_metadata = {
                        **event,
                        "sequence": sequence,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    print(f"   📤 [CHAT MATERIAL CONTENT] Streaming event: {event.get('type')}")
                    yield f"data: {json.dumps(event_with_metadata)}\n\n"
                    await asyncio.sleep(0.1)
                
                # Send completion
                sequence += 1
                completion = {
                    "type": "complete",
                    "data": {},
                    "sequence": sequence,
                    "timestamp": datetime.utcnow().isoformat()
                }
                yield f"data: {json.dumps(completion)}\n\n"
            
            return StreamingResponse(
                stream_chat_material_events(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*"
                }
            )
        else:
            print(f"⚠️ [CHAT MATERIAL CONTENT] No streaming events found, using regular response")
            # Fallback to regular streaming
            return StreamingResponse(
                stream_response(
                    result["response"],
                    result.get("course_id"),
                    result.get("function_results", {})
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*"
                }
            )
        
    except Exception as e:
        print(f"❌❌❌ [CHAT MATERIAL CONTENT] CRITICAL ERROR: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat material content: {str(e)}"
        )

@router.get("/{course_id}/content-materials")
async def get_content_materials(
    course_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get content materials for a course"""
    print(f"\n📚📚📚 [CONTENT MATERIALS ENDPOINT HIT] Getting content materials for course: {course_id}")
    print(f"   👤 User: {current_user.id}")
    
    try:
        db = await get_database()
        
        if not ObjectId.is_valid(course_id):
            print(f"❌ [CONTENT MATERIALS] Invalid course ID: {course_id}")
            raise HTTPException(status_code=400, detail="Invalid course ID")
        
        # Verify course belongs to user
        course = await db.courses.find_one({
            "_id": ObjectId(course_id),
            "user_id": current_user.id
        })
        
        if not course:
            print(f"❌ [CONTENT MATERIALS] Course not found: {course_id}")
            raise HTTPException(status_code=404, detail="Course not found")
        
        print(f"✅ [CONTENT MATERIALS] Course found: {course.get('name')}")
        
        # Get content materials from database
        materials_cursor = db.content_materials.find({
            "course_id": ObjectId(course_id)
        }).sort([("module_number", 1), ("chapter_number", 1), ("slide_number", 1)])
        
        materials = await materials_cursor.to_list(None)  # Get all materials
        
        print(f"📊 [CONTENT MATERIALS] Found {len(materials)} content materials")
        
        # Convert ObjectIds to strings for each material
        formatted_materials = []
        for material in materials:
            material["_id"] = str(material["_id"])
            material["course_id"] = str(material["course_id"])
            
            # Add learning objectives and assessment criteria if they exist in the course structure
            content_structure = course.get("content_structure", {})
            if content_structure:
                # Try to find matching module and chapter in content structure
                module_key = f"module_{material['module_number']}"
                if module_key in content_structure:
                    module_data = content_structure[module_key]
                    chapter_key = f"chapter_{material['chapter_number']}"
                    if chapter_key in module_data.get("chapters", {}):
                        chapter_data = module_data["chapters"][chapter_key]
                        material["learning_objectives"] = chapter_data.get("learning_objectives", [])
                        material["assessment_criteria"] = chapter_data.get("assessment_criteria", [])
            
            formatted_materials.append(ContentMaterialResponse(**material))
        
        print(f"✅ [CONTENT MATERIALS] Returning {len(formatted_materials)} formatted materials")
        
        return {
            "materials": [material.dict() for material in formatted_materials],
            "total_count": len(formatted_materials),
            "course_id": course_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌❌❌ [CONTENT MATERIALS] CRITICAL ERROR: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get content materials: {str(e)}"
        )

@router.get("/{course_id}/assessment/{material_id}")
async def get_assessment_data(
    course_id: str,
    material_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get assessment data from database for a specific material"""
    print(f"\n🎯🎯🎯 [ASSESSMENT DATA ENDPOINT] Getting assessment data for material: {material_id}")
    print(f"   📋 Course ID: {course_id}")
    print(f"   👤 User: {current_user.id}")
    
    try:
        db = await get_database()
        
        if not ObjectId.is_valid(course_id):
            print(f"❌ [ASSESSMENT DATA] Invalid course ID: {course_id}")
            raise HTTPException(status_code=400, detail="Invalid course ID")
        
        if not ObjectId.is_valid(material_id):
            print(f"❌ [ASSESSMENT DATA] Invalid material ID: {material_id}")
            raise HTTPException(status_code=400, detail="Invalid material ID")
        
        # Verify course belongs to user
        course = await db.courses.find_one({
            "_id": ObjectId(course_id),
            "user_id": current_user.id
        })
        
        if not course:
            print(f"❌ [ASSESSMENT DATA] Course not found: {course_id}")
            raise HTTPException(status_code=404, detail="Course not found")
        
        print(f"✅ [ASSESSMENT DATA] Course found: {course.get('name')}")
        
        # Get the specific material
        material = await db.content_materials.find_one({
            "_id": ObjectId(material_id),
            "course_id": ObjectId(course_id)
        })
        
        if not material:
            print(f"❌ [ASSESSMENT DATA] Material not found: {material_id}")
            raise HTTPException(status_code=404, detail="Material not found")
        
        # Check if this is an assessment material
        if material.get("material_type") != "assessment":
            print(f"❌ [ASSESSMENT DATA] Material is not an assessment: {material.get('material_type')}")
            raise HTTPException(status_code=400, detail="Material is not an assessment")
        
        # Check if assessment data exists
        assessment_data = material.get("assessment_data")
        if not assessment_data:
            print(f"❌ [ASSESSMENT DATA] No assessment data found for material: {material_id}")
            raise HTTPException(status_code=404, detail="Assessment data not found")
        
        print(f"✅ [ASSESSMENT DATA] Found assessment data: {material.get('assessment_format')}")
        
        # Return structured assessment data
        return {
            "success": True,
            "material_id": material_id,
            "material_title": material.get("title"),
            "assessment_format": material.get("assessment_format"),
            "assessment_data": assessment_data,
            "question_difficulty": material.get("question_difficulty"),
            "learning_objective": material.get("learning_objective"),
            "content_status": material.get("content_status"),
            "created_at": material.get("created_at"),
            "updated_at": material.get("updated_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌❌❌ [ASSESSMENT DATA] CRITICAL ERROR: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get assessment data: {str(e)}"
        )
