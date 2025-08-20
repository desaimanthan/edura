from typing import Dict, Any, Optional, List
from bson import ObjectId
from datetime import datetime

from ...database import get_database


class DatabaseService:
    """Handles all database operations"""
    
    def __init__(self):
        self.db = None
    
    async def get_database(self):
        """Get database connection"""
        if self.db is None:
            self.db = await get_database()
        return self.db
    
    async def find_course(self, course_id: str, user_id: str = None) -> Optional[Dict[str, Any]]:
        """Find a course by ID"""
        db = await self.get_database()
        query = {"_id": ObjectId(course_id)}
        if user_id:
            query["user_id"] = ObjectId(user_id)
        return await db.courses.find_one(query)
    
    async def create_course(self, course_data: Dict[str, Any]) -> str:
        """Create a new course"""
        db = await self.get_database()
        course_data["created_at"] = datetime.utcnow()
        course_data["updated_at"] = datetime.utcnow()
        result = await db.courses.insert_one(course_data)
        return str(result.inserted_id)
    
    async def update_course(self, course_id: str, update_data: Dict[str, Any]) -> bool:
        """Update a course"""
        db = await self.get_database()
        update_data["updated_at"] = datetime.utcnow()
        result = await db.courses.update_one(
            {"_id": ObjectId(course_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def find_chat_session(self, course_id: str) -> Optional[Dict[str, Any]]:
        """Find chat session for a course"""
        db = await self.get_database()
        return await db.chat_sessions.find_one({"course_id": ObjectId(course_id)})
    
    async def create_chat_session(self, session_data: Dict[str, Any]) -> str:
        """Create a new chat session"""
        db = await self.get_database()
        session_data["created_at"] = datetime.utcnow()
        session_data["last_activity"] = datetime.utcnow()
        result = await db.chat_sessions.insert_one(session_data)
        return str(result.inserted_id)
    
    async def update_chat_session(self, course_id: str, update_data: Dict[str, Any]) -> bool:
        """Update chat session"""
        db = await self.get_database()
        update_data["last_activity"] = datetime.utcnow()
        result = await db.chat_sessions.update_one(
            {"course_id": ObjectId(course_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def get_messages(self, course_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent messages for a course"""
        db = await self.get_database()
        cursor = db.chat_messages.find({
            "course_id": ObjectId(course_id)
        }).sort("message_index", -1).limit(limit)
        
        messages = await cursor.to_list(limit)
        return list(reversed(messages))  # Return in chronological order
    
    async def count_messages(self, course_id: str) -> int:
        """Count messages for a course"""
        db = await self.get_database()
        return await db.chat_messages.count_documents({
            "course_id": ObjectId(course_id)
        })
    
    async def insert_message(self, message_data: Dict[str, Any]) -> str:
        """Insert a new message"""
        db = await self.get_database()
        message_data["timestamp"] = datetime.utcnow()
        result = await db.chat_messages.insert_one(message_data)
        return str(result.inserted_id)
    
    async def insert_document(self, collection: str, document: Dict[str, Any]) -> str:
        """Generic document insertion"""
        db = await self.get_database()
        result = await db[collection].insert_one(document)
        return str(result.inserted_id)
    
    async def update_document(self, collection: str, doc_id: str, update_data: Dict[str, Any]) -> bool:
        """Generic document update"""
        db = await self.get_database()
        result = await db[collection].update_one(
            {"_id": ObjectId(doc_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def find_document(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generic document find"""
        db = await self.get_database()
        return await db[collection].find_one(query)
    
    async def count_documents(self, collection: str, query: Dict[str, Any]) -> int:
        """Generic document count"""
        db = await self.get_database()
        return await db[collection].count_documents(query)
