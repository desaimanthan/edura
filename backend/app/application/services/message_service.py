from typing import Dict, Any, Optional, List
from datetime import datetime
from bson import ObjectId

from ...infrastructure.database.database_service import DatabaseService


class MessageService:
    """Handles message storage and retrieval operations"""
    
    def __init__(self, database_service: DatabaseService):
        self.db = database_service
    
    async def store_message(self, course_id: str, user_id: str, content: str, role: str, metadata: Dict[str, Any] = None) -> str:
        """Store a chat message"""
        # Get current message count for indexing
        message_count = await self.db.count_messages(course_id)
        
        message_data = {
            "course_id": ObjectId(course_id),
            "user_id": ObjectId(user_id),
            "content": content,
            "role": role,
            "message_index": message_count,
            "metadata": metadata or {}
        }
        
        # Store the message
        message_id = await self.db.insert_message(message_data)
        
        # Update session stats
        new_message_count = message_count + 1
        await self.db.update_chat_session(course_id, {
            "total_messages": new_message_count
        })
        
        return message_id
    
    async def get_recent_messages(self, course_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent messages for a course"""
        return await self.db.get_messages(course_id, limit)
    
    async def get_message_count(self, course_id: str) -> int:
        """Get total message count for a course"""
        return await self.db.count_messages(course_id)
    
    def build_openai_messages(self, context: Dict[str, Any], current_message: str, system_prompt: str) -> List[Dict[str, str]]:
        """Build messages array for OpenAI API"""
        messages = []
        
        # System prompt
        messages.append({"role": "system", "content": system_prompt})
        
        # Add context summary if available
        if context.get("context_summary"):
            messages.append({
                "role": "system", 
                "content": f"Previous conversation summary: {context['context_summary']}"
            })
        
        # Add recent messages
        for msg in context.get("recent_messages", []):
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add current message
        messages.append({"role": "user", "content": current_message})
        
        return messages
    
    async def should_update_context_summary(self, course_id: str, metadata: Dict[str, Any] = None) -> bool:
        """Determine if context summary should be updated"""
        message_count = await self.get_message_count(course_id)
        
        # Update every 10 messages
        if message_count % 10 == 0:
            return True
        
        # Update when significant events occur
        if metadata and any(key in metadata for key in ["course_created", "curriculum_generated", "structure_updated"]):
            return True
        
        return False
    
    async def send_streaming_event(self, event_data: Dict[str, Any]) -> None:
        """Send streaming event to frontend via SSE
        
        This method stores the event data that will be picked up by the SSE endpoint.
        The actual streaming is handled by the routes layer.
        """
        try:
            # For now, we'll just log the event
            # In a production system, this could use Redis, WebSockets, or another pub/sub mechanism
            print(f"📡 [MessageService] Streaming event: {event_data.get('type', 'unknown')} - {event_data.get('message', 'No message')}")
            
            # TODO: Implement actual streaming mechanism (Redis pub/sub, WebSockets, etc.)
            # For now, the events will be handled directly by the agent coordinator
            
        except Exception as e:
            print(f"❌ [MessageService] Error sending streaming event: {e}")
