#!/usr/bin/env python3
"""
Script to update existing courses to use small images instead of large images
for better performance on the courses listing page.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.database import get_database, connect_to_mongo, close_mongo_connection


async def update_courses_to_small_images():
    """Update existing courses to use small images instead of large images"""
    
    print("🔄 Starting update of existing courses to use small images...")
    
    try:
        # Initialize database connection
        await connect_to_mongo()
        
        # Get database connection
        db = await get_database()
        
        # Find all courses that have cover images
        courses_cursor = db.courses.find({
            "cover_image_public_url": {"$exists": True, "$ne": None}
        })
        
        courses = await courses_cursor.to_list(None)
        
        print(f"📊 Found {len(courses)} courses with cover images")
        
        updated_count = 0
        
        for course in courses:
            course_id = str(course["_id"])
            current_url = course.get("cover_image_public_url", "")
            
            print(f"\n📋 Processing course: {course.get('name', 'Unnamed')} (ID: {course_id})")
            print(f"   🔗 Current URL: {current_url}")
            
            # Check if the URL contains "/large/" and replace with "/small/"
            if "/large/" in current_url:
                new_url = current_url.replace("/large/", "/small/")
                new_r2_key = course.get("cover_image_r2_key", "").replace("/large/", "/small/")
                
                print(f"   ✅ Updating to small image...")
                print(f"   🔗 New URL: {new_url}")
                
                # Update the course in the database
                update_result = await db.courses.update_one(
                    {"_id": course["_id"]},
                    {
                        "$set": {
                            "cover_image_public_url": new_url,
                            "cover_image_r2_key": new_r2_key,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                
                if update_result.modified_count > 0:
                    updated_count += 1
                    print(f"   ✅ Successfully updated!")
                else:
                    print(f"   ⚠️ Update failed or no changes made")
                    
            else:
                print(f"   ℹ️ URL doesn't contain '/large/', skipping...")
        
        print(f"\n🎉 Update complete!")
        print(f"   📊 Total courses processed: {len(courses)}")
        print(f"   ✅ Courses updated: {updated_count}")
        print(f"   ℹ️ Courses skipped: {len(courses) - updated_count}")
        
        if updated_count > 0:
            print(f"\n🚀 All updated courses will now use small images for better performance!")
        
    except Exception as e:
        print(f"❌ Error updating courses: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
    finally:
        # Close database connection
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(update_courses_to_small_images())
