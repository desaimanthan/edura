#!/usr/bin/env python3
"""
Test script to verify the curriculum generation fix
"""
import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.services.agents.curriculum_agent import CurriculumAgent
from backend.app.database import get_database
from bson import ObjectId

async def test_curriculum_generation():
    """Test curriculum generation and message storage"""
    
    # Initialize the curriculum agent
    agent = CurriculumAgent()
    
    # Test course ID (you'll need to replace this with an actual course ID)
    test_course_id = "6899641a8e0fa0450e2d8174"  # Replace with actual course ID
    test_user_id = "687a6561eba67e7ade83f1f9"   # Replace with actual user ID
    
    print("Testing curriculum generation...")
    
    try:
        # Test the streaming generation
        print("Starting curriculum generation stream...")
        
        async for event in agent.stream_curriculum_generation(test_course_id, None, test_user_id):
            print(f"Event: {event['type']} - {event.get('content', '')[:100]}...")
            
            if event['type'] == 'complete':
                print("✅ Curriculum generation completed successfully!")
                print(f"Success message: {event['content']}")
                break
            elif event['type'] == 'error':
                print(f"❌ Error: {event['content']}")
                break
        
        # Verify the message was stored in the database
        print("\nVerifying message storage...")
        db = await get_database()
        
        # Check for the success message in chat_messages
        success_message = await db.chat_messages.find_one({
            "course_id": ObjectId(test_course_id),
            "content": {"$regex": "Curriculum generated successfully"}
        })
        
        if success_message:
            print("✅ Success message found in database!")
            print(f"Message content: {success_message['content']}")
            print(f"Role: {success_message['role']}")
            print(f"Timestamp: {success_message['timestamp']}")
        else:
            print("❌ Success message not found in database")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await agent.close_client()

if __name__ == "__main__":
    print("🧪 Testing Curriculum Generation Fix")
    print("=" * 50)
    asyncio.run(test_curriculum_generation())
