#!/usr/bin/env python3
"""
Migration script to update existing courses with multi-size cover images.

This script:
1. Finds courses with single cover images (legacy format)
2. Downloads the existing image
3. Generates small and medium sizes using PIL
4. Uploads all sizes to R2 storage
5. Updates the database with multi-size URLs

Usage:
    python migrate_existing_courses_to_multi_size_images.py
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from io import BytesIO
from PIL import Image
import aiohttp

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.infrastructure.database.database_service import DatabaseService
from app.infrastructure.storage.r2_storage import R2StorageService
from app.models import Course


class MultiSizeImageMigrator:
    """Migrates existing courses to use multi-size cover images"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.r2_service = R2StorageService()
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _resize_image(self, image_bytes: bytes, target_size: Tuple[int, int], quality: int = 85) -> bytes:
        """
        Resize image to target size while maintaining quality
        
        Args:
            image_bytes: Original image bytes
            target_size: Target (width, height) tuple
            quality: JPEG quality (1-100), ignored for PNG
            
        Returns:
            Resized image bytes
        """
        try:
            # Open image from bytes
            image = Image.open(BytesIO(image_bytes))
            
            # Resize with high-quality resampling
            resized_image = image.resize(target_size, Image.Resampling.LANCZOS)
            
            # Save to bytes
            output_buffer = BytesIO()
            
            # Determine format from original image
            original_format = image.format or 'PNG'
            
            if original_format.upper() == 'PNG':
                # For PNG, maintain transparency and use optimization
                resized_image.save(output_buffer, format='PNG', optimize=True)
            else:
                # For JPEG and other formats
                resized_image.save(output_buffer, format=original_format, quality=quality, optimize=True)
            
            return output_buffer.getvalue()
            
        except Exception as e:
            print(f"❌ Error resizing image to {target_size}: {str(e)}")
            raise e
    
    def _generate_multiple_sizes(self, original_image_bytes: bytes) -> Dict[str, bytes]:
        """
        Generate multiple sizes from original image
        
        Args:
            original_image_bytes: Original large image bytes
            
        Returns:
            Dictionary with size names as keys and image bytes as values
        """
        try:
            print(f"🔄 Generating multiple image sizes...")
            
            # Define size configurations
            size_configs = {
                'large': (1536, 1024),   # Original size (L)
                'medium': (768, 512),    # 50% scale (M)
                'small': (384, 256)      # 25% scale (S)
            }
            
            sizes = {}
            
            # Large size is the original
            sizes['large'] = original_image_bytes
            print(f"   📏 LARGE: 1536x1024 ({len(original_image_bytes)} bytes)")
            
            # Generate medium and small sizes
            for size_name, (width, height) in size_configs.items():
                if size_name == 'large':
                    continue  # Already handled
                
                try:
                    resized_bytes = self._resize_image(original_image_bytes, (width, height), quality=90)
                    sizes[size_name] = resized_bytes
                    print(f"   📏 {size_name.upper()}: {width}x{height} ({len(resized_bytes)} bytes)")
                    
                except Exception as e:
                    print(f"❌ Failed to generate {size_name} size: {str(e)}")
                    # Continue with other sizes even if one fails
            
            print(f"✅ Generated {len(sizes)} image sizes")
            return sizes
            
        except Exception as e:
            print(f"❌ Error generating multiple sizes: {str(e)}")
            raise e
    
    async def _download_image(self, url: str) -> Optional[bytes]:
        """Download image from URL"""
        try:
            print(f"📥 Downloading image from: {url}")
            async with self.session.get(url) as response:
                if response.status == 200:
                    image_bytes = await response.read()
                    print(f"✅ Downloaded {len(image_bytes)} bytes")
                    return image_bytes
                else:
                    print(f"❌ Failed to download image: HTTP {response.status}")
                    return None
        except Exception as e:
            print(f"❌ Error downloading image: {str(e)}")
            return None
    
    async def _upload_multi_size_images(self, course_id: str, image_sizes: Dict[str, bytes], 
                                       filename: str = "cover_image.png") -> Optional[Dict[str, Any]]:
        """Upload multi-size images to R2"""
        try:
            result = await self.r2_service.upload_images_multi_size(
                course_id=course_id,
                large_image=image_sizes['large'],
                medium_image=image_sizes.get('medium', image_sizes['large']),
                small_image=image_sizes.get('small', image_sizes['large']),
                filename=filename,
                image_type="cover",
                content_type="image/png"
            )
            
            if result["success"]:
                print(f"✅ Multi-size images uploaded successfully")
                return result["images"]
            else:
                print(f"❌ Failed to upload multi-size images: {result.get('error')}")
                return None
                
        except Exception as e:
            print(f"❌ Error uploading multi-size images: {str(e)}")
            return None
    
    async def _update_course_with_multi_size_urls(self, course_id: str, images: Dict[str, Any]) -> bool:
        """Update course database record with multi-size image URLs"""
        try:
            update_data = {
                # Multi-size image fields
                "cover_image_large_r2_key": images.get("large", {}).get("r2_key"),
                "cover_image_large_public_url": images.get("large", {}).get("public_url"),
                "cover_image_medium_r2_key": images.get("medium", {}).get("r2_key"),
                "cover_image_medium_public_url": images.get("medium", {}).get("public_url"),
                "cover_image_small_r2_key": images.get("small", {}).get("r2_key"),
                "cover_image_small_public_url": images.get("small", {}).get("public_url"),
                # Keep legacy fields for backward compatibility (use large image)
                "cover_image_r2_key": images.get("large", {}).get("r2_key"),
                "cover_image_public_url": images.get("large", {}).get("public_url"),
                # Update metadata
                "cover_image_updated_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            success = await self.db_service.update_course(course_id, update_data)
            
            if success:
                print(f"✅ Course database updated with multi-size URLs")
                return True
            else:
                print(f"❌ Failed to update course database")
                return False
                
        except Exception as e:
            print(f"❌ Error updating course database: {str(e)}")
            return False
    
    async def migrate_course(self, course: Dict[str, Any]) -> bool:
        """Migrate a single course to multi-size images"""
        course_id = str(course["_id"])
        course_name = course.get("name", "Unknown Course")
        
        print(f"\n🔄 Migrating course: {course_name} (ID: {course_id})")
        
        # Check if course already has multi-size images
        if course.get("cover_image_large_public_url"):
            print(f"⏭️  Course already has multi-size images, skipping...")
            return True
        
        # Check if course has a legacy cover image
        legacy_image_url = course.get("cover_image_public_url")
        if not legacy_image_url:
            print(f"⏭️  Course has no cover image, skipping...")
            return True
        
        try:
            # Step 1: Download the existing image
            image_bytes = await self._download_image(legacy_image_url)
            if not image_bytes:
                print(f"❌ Failed to download existing image")
                return False
            
            # Step 2: Generate multiple sizes
            image_sizes = self._generate_multiple_sizes(image_bytes)
            if not image_sizes:
                print(f"❌ Failed to generate multiple sizes")
                return False
            
            # Step 3: Upload multi-size images to R2
            uploaded_images = await self._upload_multi_size_images(course_id, image_sizes)
            if not uploaded_images:
                print(f"❌ Failed to upload multi-size images")
                return False
            
            # Step 4: Update database with new URLs
            success = await self._update_course_with_multi_size_urls(course_id, uploaded_images)
            if not success:
                print(f"❌ Failed to update database")
                return False
            
            print(f"✅ Successfully migrated course: {course_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error migrating course {course_name}: {str(e)}")
            return False
    
    async def migrate_all_courses(self) -> Dict[str, int]:
        """Migrate all courses with legacy cover images"""
        print(f"\n🚀 Starting migration of courses to multi-size images...")
        print(f"📅 Migration started at: {datetime.now().isoformat()}")
        
        stats = {
            "total": 0,
            "migrated": 0,
            "skipped": 0,
            "failed": 0
        }
        
        try:
            # Get database connection
            db = await self.db_service.get_database()
            
            # Find all courses with cover images
            courses_cursor = db.courses.find({
                "cover_image_public_url": {"$exists": True, "$ne": None}
            })
            
            courses = await courses_cursor.to_list(length=None)
            stats["total"] = len(courses)
            
            print(f"📊 Found {stats['total']} courses with cover images")
            
            if stats["total"] == 0:
                print(f"✅ No courses to migrate")
                return stats
            
            # Migrate each course
            for i, course in enumerate(courses, 1):
                course_name = course.get("name", "Unknown Course")
                print(f"\n📋 Processing course {i}/{stats['total']}: {course_name}")
                
                try:
                    success = await self.migrate_course(course)
                    if success:
                        stats["migrated"] += 1
                    else:
                        stats["failed"] += 1
                        
                except Exception as e:
                    print(f"❌ Unexpected error migrating course {course_name}: {str(e)}")
                    stats["failed"] += 1
                
                # Add a small delay to avoid overwhelming the system
                await asyncio.sleep(0.5)
            
            # Calculate skipped courses
            stats["skipped"] = stats["total"] - stats["migrated"] - stats["failed"]
            
            print(f"\n🎉 Migration completed!")
            print(f"📊 Final Statistics:")
            print(f"   📈 Total courses: {stats['total']}")
            print(f"   ✅ Successfully migrated: {stats['migrated']}")
            print(f"   ⏭️  Skipped (already migrated): {stats['skipped']}")
            print(f"   ❌ Failed: {stats['failed']}")
            print(f"📅 Migration completed at: {datetime.now().isoformat()}")
            
            return stats
            
        except Exception as e:
            print(f"❌ Critical error during migration: {str(e)}")
            stats["failed"] = stats["total"] - stats["migrated"] - stats["skipped"]
            return stats
    
    async def verify_migration(self) -> Dict[str, int]:
        """Verify the migration results"""
        print(f"\n🔍 Verifying migration results...")
        
        verification_stats = {
            "total_courses": 0,
            "with_multi_size": 0,
            "with_legacy_only": 0,
            "without_images": 0
        }
        
        try:
            # Get database connection
            db = await self.db_service.get_database()
            
            # Count all courses
            verification_stats["total_courses"] = await db.courses.count_documents({})
            
            # Count courses with multi-size images
            verification_stats["with_multi_size"] = await db.courses.count_documents({
                "cover_image_large_public_url": {"$exists": True, "$ne": None}
            })
            
            # Count courses with only legacy images
            verification_stats["with_legacy_only"] = await db.courses.count_documents({
                "cover_image_public_url": {"$exists": True, "$ne": None},
                "cover_image_large_public_url": {"$exists": False}
            })
            
            # Count courses without any images
            verification_stats["without_images"] = await db.courses.count_documents({
                "$and": [
                    {"cover_image_public_url": {"$exists": False}},
                    {"cover_image_large_public_url": {"$exists": False}}
                ]
            })
            
            print(f"📊 Verification Results:")
            print(f"   📈 Total courses: {verification_stats['total_courses']}")
            print(f"   🎨 With multi-size images: {verification_stats['with_multi_size']}")
            print(f"   📷 With legacy images only: {verification_stats['with_legacy_only']}")
            print(f"   🚫 Without images: {verification_stats['without_images']}")
            
            return verification_stats
            
        except Exception as e:
            print(f"❌ Error during verification: {str(e)}")
            return verification_stats


async def main():
    """Main migration function"""
    print("🚀 Multi-Size Image Migration Tool")
    print("=" * 50)
    
    try:
        async with MultiSizeImageMigrator() as migrator:
            # Run the migration
            migration_stats = await migrator.migrate_all_courses()
            
            # Verify the results
            verification_stats = await migrator.verify_migration()
            
            # Summary
            print(f"\n📋 MIGRATION SUMMARY")
            print(f"=" * 30)
            print(f"Migration completed with {migration_stats['migrated']} courses successfully migrated")
            print(f"Verification shows {verification_stats['with_multi_size']} courses now have multi-size images")
            
            if migration_stats['failed'] > 0:
                print(f"⚠️  {migration_stats['failed']} courses failed to migrate - please check logs")
                return 1
            else:
                print(f"✅ All eligible courses migrated successfully!")
                return 0
                
    except Exception as e:
        print(f"❌ Critical error: {str(e)}")
        return 1


if __name__ == "__main__":
    # Run the migration
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
