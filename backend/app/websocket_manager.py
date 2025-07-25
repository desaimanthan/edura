import asyncio
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        # Store active connections by session_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        
        self.active_connections[session_id].add(websocket)
        logger.info(f"WebSocket connected for session {session_id}. Total connections: {len(self.active_connections[session_id])}")
        
        # Send initial connection confirmation
        await self.send_message(session_id, {
            "type": "connection_established",
            "message": "Connected to slide generation session",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def disconnect(self, websocket: WebSocket, session_id: str):
        """Remove a WebSocket connection"""
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            
            # Clean up empty session
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
                
        logger.info(f"WebSocket disconnected for session {session_id}")
    
    async def send_message(self, session_id: str, message: dict):
        """Send a message to all connections for a session"""
        if session_id not in self.active_connections:
            return
        
        # Create a copy of the set to avoid modification during iteration
        connections = self.active_connections[session_id].copy()
        
        for websocket in connections:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to WebSocket: {e}")
                # Remove failed connection
                self.active_connections[session_id].discard(websocket)
    
    async def send_agent_message(self, session_id: str, agent_name: str, agent_role: str, message: str, step: int):
        """Send an agent conversation message"""
        await self.send_message(session_id, {
            "type": "agent_message",
            "step": step,
            "agent_name": agent_name,
            "agent_role": agent_role,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def send_status_update(self, session_id: str, status: str, details: str = None):
        """Send a status update"""
        await self.send_message(session_id, {
            "type": "status_update",
            "status": status,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def send_progress_update(self, session_id: str, current_step: int, total_steps: int, description: str):
        """Send a progress update"""
        await self.send_message(session_id, {
            "type": "progress_update",
            "current_step": current_step,
            "total_steps": total_steps,
            "description": description,
            "progress_percentage": (current_step / total_steps) * 100 if total_steps > 0 else 0,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def send_slide_generated(self, session_id: str, slide_number: int, title: str, total_slides: int):
        """Send notification when a slide is generated"""
        await self.send_message(session_id, {
            "type": "slide_generated",
            "slide_number": slide_number,
            "title": title,
            "total_slides": total_slides,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def send_completion(self, session_id: str, total_slides: int, success: bool, error_message: str = None):
        """Send completion notification"""
        await self.send_message(session_id, {
            "type": "generation_complete",
            "success": success,
            "total_slides": total_slides,
            "error_message": error_message,
            "timestamp": datetime.utcnow().isoformat()
        })

# Global WebSocket manager instance
websocket_manager = WebSocketManager()
