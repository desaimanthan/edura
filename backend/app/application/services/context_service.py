from typing import Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

from ...infrastructure.database.database_service import DatabaseService
from .message_service import MessageService
from ...infrastructure.ai.openai_service import OpenAIService


class ContextService:
    """Handles conversation context and summarization"""
    
    def __init__(self, database_service: DatabaseService, openai_service: OpenAIService, message_service: MessageService):
        self.db = database_service
        self.openai = openai_service
        self.messages = message_service
    
    async def get_conversation_context(self, course_id: Optional[str], user_id: str) -> Dict[str, Any]:
        """Get conversation context for the current course"""
        context = {
            "course_state": None,
            "context_summary": "",
            "recent_messages": [],
            "current_step": "course_naming"
        }
        
        if not course_id:
            return context
        
        # Get course data
        course = await self.db.find_course(course_id, user_id)
        if course:
            context["course_state"] = course
            context["current_step"] = course.get("workflow_step", "course_naming")
        
        # Get chat session for context summary
        session = await self.db.find_chat_session(course_id)
        if session:
            context["context_summary"] = session.get("context_summary", "")
        
        # Get recent messages
        context["recent_messages"] = await self.messages.get_recent_messages(course_id, 20)
        
        return context
    
    async def update_context_summary(self, course_id: str):
        """Update the context summary for the chat session"""
        try:
            # Get recent messages for summarization (last 50 messages)
            recent_messages = await self.messages.get_recent_messages(course_id, 50)
            
            if len(recent_messages) < 5:  # Don't summarize if too few messages
                return
            
            # Get course info for context
            course = await self.db.find_course(course_id)
            if not course:
                return
            
            # Build conversation text for summarization
            conversation_text = f"Course: {course.get('name', 'Untitled Course')}\n"
            conversation_text += f"Status: {course.get('status', 'unknown')}\n"
            conversation_text += f"Workflow Step: {course.get('workflow_step', 'unknown')}\n\n"
            conversation_text += "Recent Conversation:\n"
            
            for msg in recent_messages:
                role = "User" if msg["role"] == "user" else "Assistant"
                conversation_text += f"{role}: {msg['content']}\n"
            
            # Generate summary using OpenAI
            summary_prompt = f"""Summarize the following conversation between a user and a course creation assistant. Focus on:
1. What has been accomplished so far
2. Current course details (name, description, status)
3. Key decisions made
4. Current workflow step and next steps
5. Any important context for future conversations

Keep the summary concise but comprehensive (2-3 paragraphs max).

Conversation:
{conversation_text}"""
            
            client = await self.openai.get_client()
            response = await client.chat.completions.create(
                model="gpt-5-nano-2025-08-07",
                messages=[{"role": "user", "content": summary_prompt}],
                max_completion_tokens=500
            )
            
            summary = response.choices[0].message.content
            
            # Update the chat session with the new summary
            await self.db.update_chat_session(course_id, {
                "context_summary": summary,
                "summary_updated_at": datetime.utcnow()
            })
            
            print(f"Updated context summary for course {course_id}")
            
        except Exception as e:
            print(f"Failed to update context summary: {e}")
            # Don't raise the exception as this is a background task
    
    async def build_context_for_agent(self, course_id: Optional[str], user_id: str) -> Dict[str, Any]:
        """Build formatted context for agent consumption"""
        context = await self.get_conversation_context(course_id, user_id)
        
        # Add current course_id to context for system prompt
        context["current_course_id"] = course_id
        
        return context
    
    async def manage_context_window(self, course_id: str) -> Dict[str, Any]:
        """Manage context window size and relevance"""
        # Get current message count
        message_count = await self.messages.get_message_count(course_id)
        
        # If we have too many messages, ensure we have a recent summary
        if message_count > 100:
            session = await self.db.find_chat_session(course_id)
            if not session or not session.get("context_summary"):
                await self.update_context_summary(course_id)
        
        return {
            "message_count": message_count,
            "needs_summary": message_count > 100,
            "context_window_size": min(message_count, 20)  # Limit to last 20 messages
        }
