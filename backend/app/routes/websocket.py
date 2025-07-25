from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
from ..websocket_manager import websocket_manager
from ..database import get_database
from bson import ObjectId

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/ws/slides/generation/{session_id}")
async def websocket_slide_generation(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time slide generation updates"""
    
    try:
        # Connect to the WebSocket manager
        await websocket_manager.connect(websocket, session_id)
        
        # Verify the session exists
        db = await get_database()
        session = await db.slide_generation_sessions.find_one(
            {"generation_metadata.session_id": session_id}
        )
        
        if not session:
            await websocket_manager.send_message(session_id, {
                "type": "error",
                "message": "Session not found"
            })
            return
        
        # Send current session status
        await websocket_manager.send_status_update(
            session_id, 
            session.get("status", "unknown"),
            f"Connected to session {session_id}"
        )
        
        # Keep the connection alive and listen for disconnection
        try:
            while True:
                # Wait for any message from client (ping/pong)
                data = await websocket.receive_text()
                
                # Handle ping/pong or other client messages
                if data == "ping":
                    await websocket.send_text("pong")
                    
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for session {session_id}")
            
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {str(e)}")
        
    finally:
        # Clean up the connection
        websocket_manager.disconnect(websocket, session_id)
