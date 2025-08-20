import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from typing import Optional, Dict, Any, List
from datetime import datetime
from decouple import config
import json
import hashlib
import ssl
import certifi


class R2StorageService:
    """Service for managing file storage in Cloudflare R2"""
    
    def __init__(self):
        self.client = None
        self.bucket_name = config("R2_BUCKET_NAME")
        self.public_url = config("R2_PUBLIC_URL")
    
    def get_client(self):
        """Get or create R2 client with SSL configuration"""
        if not self.client:
            # For development, directly use SSL verification disabled to avoid certificate issues
            print("Using SSL verification disabled for R2 client (development mode)")
            boto_config = Config(
                region_name='auto',
                retries={'max_attempts': 3, 'mode': 'adaptive'},
                signature_version='s3v4'
            )
            
            self.client = boto3.client(
                's3',
                endpoint_url=config("R2_ENDPOINT_URL"),
                aws_access_key_id=config("R2_ACCESS_KEY_ID"),
                aws_secret_access_key=config("R2_SECRET_ACCESS_KEY"),
                config=boto_config,
                verify=False
            )
        return self.client
    
    def _get_curriculum_key(self, course_id: str, version: int = None) -> str:
        """Generate R2 key for curriculum file"""
        if version:
            return f"courses/{course_id}/curriculum-v{version}.md"
        return f"courses/{course_id}/curriculum.md"
    
    def _get_course_design_key(self, course_id: str, version: int = None) -> str:
        """Generate R2 key for course design file"""
        if version:
            return f"courses/{course_id}/course_design-v{version}.md"
        return f"courses/{course_id}/course_design.md"
    
    def _get_upload_key(self, course_id: str, filename: str) -> str:
        """Generate R2 key for uploaded files"""
        return f"courses/{course_id}/uploads/{filename}"
    
    def _get_public_url(self, key: str) -> str:
        """Generate public URL for R2 object"""
        return f"{self.public_url}/{key}"
    
    async def upload_curriculum(self, course_id: str, content: str, source: str, version: int = 1) -> Dict[str, Any]:
        """Upload curriculum content to R2"""
        try:
            client = self.get_client()
            
            # Generate key and metadata
            key = self._get_curriculum_key(course_id, version)
            public_url = self._get_public_url(key)
            
            # Create metadata
            metadata = {
                'source': source,
                'version': str(version),
                'created_at': datetime.utcnow().isoformat(),
                'content_type': 'text/markdown',
                'course_id': course_id
            }
            
            # Upload to R2
            client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content.encode('utf-8'),
                ContentType='text/markdown',
                Metadata=metadata
            )
            
            return {
                "success": True,
                "r2_key": key,
                "public_url": public_url,
                "source": source,
                "version": version,
                "file_size": len(content.encode('utf-8')),
                "created_at": datetime.utcnow().isoformat()
            }
            
        except ClientError as e:
            return {
                "success": False,
                "error": f"R2 upload failed: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Upload failed: {str(e)}"
            }
    
    async def get_curriculum(self, course_id: str, version: int = None) -> Optional[str]:
        """Retrieve curriculum content from R2"""
        try:
            client = self.get_client()
            key = self._get_curriculum_key(course_id, version)
            
            response = client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            content = response['Body'].read().decode('utf-8')
            return content
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            raise e
        except Exception as e:
            print(f"Error retrieving curriculum: {e}")
            return None
    
    async def delete_curriculum(self, course_id: str, version: int = None) -> bool:
        """Delete curriculum file from R2"""
        try:
            client = self.get_client()
            key = self._get_curriculum_key(course_id, version)
            
            client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            return True
            
        except ClientError as e:
            print(f"Error deleting curriculum: {e}")
            return False
        except Exception as e:
            print(f"Error deleting curriculum: {e}")
            return False
    
    # Course Design Methods (New)
    async def upload_course_design(self, course_id: str, content: str, source: str, version: int = 1) -> Dict[str, Any]:
        """Upload course design content to R2"""
        try:
            client = self.get_client()
            
            # Generate key and metadata
            key = self._get_course_design_key(course_id, version)
            public_url = self._get_public_url(key)
            
            # Create metadata
            metadata = {
                'source': source,
                'version': str(version),
                'created_at': datetime.utcnow().isoformat(),
                'content_type': 'text/markdown',
                'course_id': course_id,
                'design_type': 'comprehensive'
            }
            
            # Upload to R2
            client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content.encode('utf-8'),
                ContentType='text/markdown',
                Metadata=metadata
            )
            
            return {
                "success": True,
                "r2_key": key,
                "public_url": public_url,
                "source": source,
                "version": version,
                "file_size": len(content.encode('utf-8')),
                "created_at": datetime.utcnow().isoformat()
            }
            
        except ClientError as e:
            return {
                "success": False,
                "error": f"R2 upload failed: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Upload failed: {str(e)}"
            }
    
    async def get_course_design(self, course_id: str, version: int = None) -> Optional[str]:
        """Retrieve course design content from R2"""
        try:
            client = self.get_client()
            key = self._get_course_design_key(course_id, version)
            
            response = client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            content = response['Body'].read().decode('utf-8')
            return content
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            raise e
        except Exception as e:
            print(f"Error retrieving course design: {e}")
            return None
    
    async def get_course_design_content(self, r2_key: str) -> Optional[str]:
        """Retrieve course design content by R2 key (for backward compatibility)"""
        try:
            client = self.get_client()
            
            response = client.get_object(
                Bucket=self.bucket_name,
                Key=r2_key
            )
            
            content = response['Body'].read().decode('utf-8')
            return content
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            raise e
        except Exception as e:
            print(f"Error retrieving course design content: {e}")
            return None
    
    async def delete_course_design(self, course_id: str, version: int = None) -> bool:
        """Delete course design file from R2"""
        try:
            client = self.get_client()
            key = self._get_course_design_key(course_id, version)
            
            client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            return True
            
        except ClientError as e:
            print(f"Error deleting course design: {e}")
            return False
        except Exception as e:
            print(f"Error deleting course design: {e}")
            return False
    
    async def get_course_design_versions(self, course_id: str) -> List[Dict[str, Any]]:
        """Get all versions of course design for a course"""
        try:
            client = self.get_client()
            prefix = f"courses/{course_id}/course_design"
            
            response = client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            versions = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    filename = key.split('/')[-1]
                    
                    # Extract version from filename
                    version = 1
                    if '-v' in filename:
                        try:
                            version = int(filename.split('-v')[1].split('.')[0])
                        except:
                            version = 1
                    
                    versions.append({
                        "version": version,
                        "key": key,
                        "filename": filename,
                        "size": obj['Size'],
                        "last_modified": obj['LastModified'].isoformat(),
                        "public_url": self._get_public_url(key)
                    })
            
            # Sort by version number
            versions.sort(key=lambda x: x['version'], reverse=True)
            return versions
            
        except ClientError as e:
            print(f"Error getting course design versions: {e}")
            return []
        except Exception as e:
            print(f"Error getting course design versions: {e}")
            return []
    
    # Backward compatibility method
    async def get_curriculum_content(self, r2_key: str) -> Optional[str]:
        """Retrieve curriculum content by R2 key (backward compatibility)"""
        return await self.get_course_design_content(r2_key)
    
    async def upload_file(self, course_id: str, file_content: bytes, filename: str, content_type: str = None) -> Dict[str, Any]:
        """Upload any file to R2"""
        try:
            client = self.get_client()
            
            # Generate key and metadata
            key = self._get_upload_key(course_id, filename)
            public_url = self._get_public_url(key)
            
            # Detect content type if not provided
            if not content_type:
                if filename.endswith('.md'):
                    content_type = 'text/markdown'
                elif filename.endswith('.pdf'):
                    content_type = 'application/pdf'
                elif filename.endswith(('.jpg', '.jpeg')):
                    content_type = 'image/jpeg'
                elif filename.endswith('.png'):
                    content_type = 'image/png'
                else:
                    content_type = 'application/octet-stream'
            
            # Create metadata
            metadata = {
                'uploaded_at': datetime.utcnow().isoformat(),
                'course_id': course_id,
                'original_filename': filename
            }
            
            # Upload to R2
            client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_content,
                ContentType=content_type,
                Metadata=metadata
            )
            
            return {
                "success": True,
                "r2_key": key,
                "public_url": public_url,
                "filename": filename,
                "file_size": len(file_content),
                "content_type": content_type,
                "uploaded_at": datetime.utcnow().isoformat()
            }
            
        except ClientError as e:
            return {
                "success": False,
                "error": f"R2 upload failed: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Upload failed: {str(e)}"
            }
    
    async def upload_file_content(self, key: str, content: str, content_type: str = "text/plain") -> Dict[str, Any]:
        """Upload file content directly with a specific key"""
        try:
            client = self.get_client()
            
            # Create metadata
            metadata = {
                'uploaded_at': datetime.utcnow().isoformat(),
                'content_type': content_type
            }
            
            # Upload to R2
            client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content.encode('utf-8'),
                ContentType=content_type,
                Metadata=metadata
            )
            
            return {
                "success": True,
                "r2_key": key,
                "public_url": self._get_public_url(key),
                "file_size": len(content.encode('utf-8')),
                "content_type": content_type,
                "uploaded_at": datetime.utcnow().isoformat()
            }
            
        except ClientError as e:
            return {
                "success": False,
                "error": f"R2 upload failed: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Upload failed: {str(e)}"
            }
    
    async def list_course_files(self, course_id: str) -> List[Dict[str, Any]]:
        """List all files for a course"""
        try:
            client = self.get_client()
            prefix = f"courses/{course_id}/"
            
            response = client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    filename = key.split('/')[-1]
                    
                    files.append({
                        "key": key,
                        "filename": filename,
                        "size": obj['Size'],
                        "last_modified": obj['LastModified'].isoformat(),
                        "public_url": self._get_public_url(key)
                    })
            
            return files
            
        except ClientError as e:
            print(f"Error listing files: {e}")
            return []
        except Exception as e:
            print(f"Error listing files: {e}")
            return []
    
    async def get_curriculum_versions(self, course_id: str) -> List[Dict[str, Any]]:
        """Get all versions of curriculum for a course"""
        try:
            client = self.get_client()
            prefix = f"courses/{course_id}/curriculum"
            
            response = client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            versions = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    filename = key.split('/')[-1]
                    
                    # Extract version from filename
                    version = 1
                    if '-v' in filename:
                        try:
                            version = int(filename.split('-v')[1].split('.')[0])
                        except:
                            version = 1
                    
                    versions.append({
                        "version": version,
                        "key": key,
                        "filename": filename,
                        "size": obj['Size'],
                        "last_modified": obj['LastModified'].isoformat(),
                        "public_url": self._get_public_url(key)
                    })
            
            # Sort by version number
            versions.sort(key=lambda x: x['version'], reverse=True)
            return versions
            
        except ClientError as e:
            print(f"Error getting curriculum versions: {e}")
            return []
        except Exception as e:
            print(f"Error getting curriculum versions: {e}")
            return []
    
    async def delete_all_course_files(self, course_id: str) -> bool:
        """Delete all files for a course from R2"""
        try:
            client = self.get_client()
            prefix = f"courses/{course_id}/"
            
            # List all objects with the course prefix
            response = client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                return True  # No files to delete
            
            # Prepare objects for deletion
            objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
            
            # Delete objects in batches (max 1000 per batch)
            batch_size = 1000
            for i in range(0, len(objects_to_delete), batch_size):
                batch = objects_to_delete[i:i + batch_size]
                
                client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={
                        'Objects': batch,
                        'Quiet': True
                    }
                )
            
            return True
            
        except ClientError as e:
            print(f"Error deleting course files: {e}")
            return False
        except Exception as e:
            print(f"Error deleting course files: {e}")
            return False
    
    # Image Storage Methods (Generic)
    def _get_image_key(self, course_id: str, filename: str, image_type: str = "cover", size: str = None) -> str:
        """Generate R2 key for course images with configurable type and optional size"""
        if size:
            return f"courses/{course_id}/images/{image_type}/{size}/{filename}"
        return f"courses/{course_id}/images/{image_type}/{filename}"
    
    # Backward compatibility method
    def _get_cover_image_key(self, course_id: str, filename: str, size: str = None) -> str:
        """Generate R2 key for course cover image with optional size (backward compatibility)"""
        return self._get_image_key(course_id, filename, "cover", size)
    
    async def upload_course_cover_image(self, course_id: str, image_data: bytes, 
                                       filename: str, content_type: str = "image/png") -> Dict[str, Any]:
        """Upload binary image data to R2 for course cover"""
        try:
            client = self.get_client()
            
            # Generate R2 key
            key = self._get_cover_image_key(course_id, filename)
            public_url = self._get_public_url(key)
            
            # Create metadata
            metadata = {
                'uploaded_at': datetime.utcnow().isoformat(),
                'course_id': course_id,
                'image_type': 'cover',
                'generated_by': 'gpt-image-1'
            }
            
            print(f"\n📤 \033[94m[R2 Storage]\033[0m \033[1mUploading cover image...\033[0m")
            print(f"   🗂️  Key: \033[93m{key}\033[0m")
            print(f"   📏 Size: \033[93m{len(image_data)} bytes\033[0m")
            print(f"   📄 Type: \033[93m{content_type}\033[0m")
            
            # Upload binary data directly to R2
            client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=image_data,  # Binary data, not encoded
                ContentType=content_type,
                Metadata=metadata
            )
            
            print(f"✅ \033[94m[R2 Storage]\033[0m \033[1m\033[92mCover image uploaded successfully\033[0m")
            print(f"   🌐 URL: \033[93m{public_url}\033[0m")
            
            return {
                "success": True,
                "r2_key": key,
                "public_url": public_url,
                "file_size": len(image_data),
                "content_type": content_type,
                "uploaded_at": datetime.utcnow().isoformat()
            }
            
        except ClientError as e:
            print(f"❌ \033[94m[R2 Storage]\033[0m \033[1m\033[91mR2 upload failed: {str(e)}\033[0m")
            return {
                "success": False,
                "error": f"R2 upload failed: {str(e)}"
            }
        except Exception as e:
            print(f"❌ \033[94m[R2 Storage]\033[0m \033[1m\033[91mUpload failed: {str(e)}\033[0m")
            return {
                "success": False,
                "error": f"Upload failed: {str(e)}"
            }
    
    async def get_course_cover_image(self, course_id: str, filename: str) -> Optional[bytes]:
        """Retrieve course cover image binary data from R2"""
        try:
            client = self.get_client()
            key = self._get_cover_image_key(course_id, filename)
            
            response = client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            image_data = response['Body'].read()
            return image_data
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            print(f"Error retrieving cover image: {e}")
            return None
        except Exception as e:
            print(f"Error retrieving cover image: {e}")
            return None
    
    async def delete_course_cover_image(self, course_id: str, filename: str) -> bool:
        """Delete course cover image from R2"""
        try:
            client = self.get_client()
            key = self._get_cover_image_key(course_id, filename)
            
            client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            return True
            
        except ClientError as e:
            print(f"Error deleting cover image: {e}")
            return False
        except Exception as e:
            print(f"Error deleting cover image: {e}")
            return False
    
    async def list_course_cover_images(self, course_id: str) -> List[Dict[str, Any]]:
        """List all cover images for a course"""
        try:
            client = self.get_client()
            prefix = f"courses/{course_id}/images/cover/"
            
            response = client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            images = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    filename = key.split('/')[-1]
                    
                    images.append({
                        "key": key,
                        "filename": filename,
                        "size": obj['Size'],
                        "last_modified": obj['LastModified'].isoformat(),
                        "public_url": self._get_public_url(key)
                    })
            
            return images
            
        except ClientError as e:
            print(f"Error listing cover images: {e}")
            return []
        except Exception as e:
            print(f"Error listing cover images: {e}")
            return []
    
    # Multi-Size Cover Image Methods
    async def upload_course_cover_images_multi_size(self, course_id: str, 
                                                   large_image: bytes, medium_image: bytes, small_image: bytes,
                                                   filename: str, content_type: str = "image/png") -> Dict[str, Any]:
        """Upload multiple sizes of course cover image to R2"""
        try:
            client = self.get_client()
            
            # Define size mappings
            sizes = {
                'large': large_image,
                'medium': medium_image,
                'small': small_image
            }
            
            uploaded_images = {}
            upload_errors = []
            
            print(f"\n📤 \033[94m[R2 Storage]\033[0m \033[1mUploading multi-size cover images...\033[0m")
            
            # Upload each size
            for size_name, image_data in sizes.items():
                try:
                    key = self._get_cover_image_key(course_id, filename, size_name)
                    public_url = self._get_public_url(key)
                    
                    # Create metadata
                    metadata = {
                        'uploaded_at': datetime.utcnow().isoformat(),
                        'course_id': course_id,
                        'image_type': 'cover',
                        'size_variant': size_name,
                        'generated_by': 'gpt-image-1',
                        'processed_by': 'backend_resize'
                    }
                    
                    print(f"   📏 {size_name.upper()}: \033[93m{len(image_data)} bytes\033[0m")
                    
                    # Upload to R2
                    client.put_object(
                        Bucket=self.bucket_name,
                        Key=key,
                        Body=image_data,
                        ContentType=content_type,
                        Metadata=metadata
                    )
                    
                    uploaded_images[size_name] = {
                        "r2_key": key,
                        "public_url": public_url,
                        "file_size": len(image_data),
                        "content_type": content_type,
                        "uploaded_at": datetime.utcnow().isoformat()
                    }
                    
                except Exception as e:
                    upload_errors.append(f"{size_name}: {str(e)}")
            
            if upload_errors:
                print(f"❌ \033[94m[R2 Storage]\033[0m \033[1m\033[91mSome uploads failed: {', '.join(upload_errors)}\033[0m")
                return {
                    "success": False,
                    "error": f"Upload errors: {', '.join(upload_errors)}",
                    "partial_success": uploaded_images
                }
            
            print(f"✅ \033[94m[R2 Storage]\033[0m \033[1m\033[92mAll cover image sizes uploaded successfully\033[0m")
            
            return {
                "success": True,
                "images": uploaded_images,
                "total_sizes": len(uploaded_images),
                "uploaded_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ \033[94m[R2 Storage]\033[0m \033[1m\033[91mMulti-size upload failed: {str(e)}\033[0m")
            return {
                "success": False,
                "error": f"Multi-size upload failed: {str(e)}"
            }
    
    async def get_course_cover_image_by_size(self, course_id: str, filename: str, size: str) -> Optional[bytes]:
        """Retrieve course cover image by specific size from R2"""
        try:
            client = self.get_client()
            key = self._get_cover_image_key(course_id, filename, size)
            
            response = client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            image_data = response['Body'].read()
            return image_data
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            print(f"Error retrieving cover image ({size}): {e}")
            return None
        except Exception as e:
            print(f"Error retrieving cover image ({size}): {e}")
            return None
    
    async def list_course_cover_images_by_size(self, course_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """List all cover images for a course organized by size"""
        try:
            client = self.get_client()
            prefix = f"courses/{course_id}/images/cover/"
            
            response = client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            images_by_size = {
                'large': [],
                'medium': [],
                'small': [],
                'other': []  # For backward compatibility with old single-size images
            }
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    path_parts = key.split('/')
                    filename = path_parts[-1]
                    
                    # Determine size from path structure
                    size_category = 'other'
                    if len(path_parts) >= 6:  # courses/id/images/cover/size/filename
                        potential_size = path_parts[-2]
                        if potential_size in ['large', 'medium', 'small']:
                            size_category = potential_size
                    
                    image_info = {
                        "key": key,
                        "filename": filename,
                        "size": obj['Size'],
                        "last_modified": obj['LastModified'].isoformat(),
                        "public_url": self._get_public_url(key)
                    }
                    
                    images_by_size[size_category].append(image_info)
            
            return images_by_size
            
        except ClientError as e:
            print(f"Error listing cover images by size: {e}")
            return {'large': [], 'medium': [], 'small': [], 'other': []}
        except Exception as e:
            print(f"Error listing cover images by size: {e}")
            return {'large': [], 'medium': [], 'small': [], 'other': []}
    
    async def delete_course_cover_images_all_sizes(self, course_id: str, filename: str) -> Dict[str, bool]:
        """Delete course cover image in all sizes from R2"""
        try:
            client = self.get_client()
            sizes = ['large', 'medium', 'small']
            deletion_results = {}
            
            for size in sizes:
                try:
                    key = self._get_cover_image_key(course_id, filename, size)
                    client.delete_object(
                        Bucket=self.bucket_name,
                        Key=key
                    )
                    deletion_results[size] = True
                except Exception as e:
                    print(f"Error deleting {size} cover image: {e}")
                    deletion_results[size] = False
            
            # Also try to delete old format (backward compatibility)
            try:
                key = self._get_cover_image_key(course_id, filename)
                client.delete_object(
                    Bucket=self.bucket_name,
                    Key=key
                )
                deletion_results['legacy'] = True
            except Exception as e:
                deletion_results['legacy'] = False
            
            return deletion_results
            
        except Exception as e:
            print(f"Error deleting cover images: {e}")
            return {'large': False, 'medium': False, 'small': False, 'legacy': False}
    
    # Generic Multi-Size Image Methods
    async def upload_images_multi_size(self, course_id: str, 
                                     large_image: bytes, medium_image: bytes, small_image: bytes,
                                     filename: str, image_type: str = "cover", 
                                     content_type: str = "image/png") -> Dict[str, Any]:
        """Upload multiple sizes of course images to R2 with configurable image type"""
        try:
            client = self.get_client()
            
            # Define size mappings
            sizes = {
                'large': large_image,
                'medium': medium_image,
                'small': small_image
            }
            
            uploaded_images = {}
            upload_errors = []
            
            print(f"\n📤 \033[94m[R2 Storage]\033[0m \033[1mUploading multi-size {image_type} images...\033[0m")
            
            # Upload each size
            for size_name, image_data in sizes.items():
                try:
                    key = self._get_image_key(course_id, filename, image_type, size_name)
                    public_url = self._get_public_url(key)
                    
                    # Create metadata
                    metadata = {
                        'uploaded_at': datetime.utcnow().isoformat(),
                        'course_id': course_id,
                        'image_type': image_type,
                        'size_variant': size_name,
                        'generated_by': 'gpt-image-1',
                        'processed_by': 'backend_resize'
                    }
                    
                    print(f"   📏 {size_name.upper()}: \033[93m{len(image_data)} bytes\033[0m")
                    
                    # Upload to R2
                    client.put_object(
                        Bucket=self.bucket_name,
                        Key=key,
                        Body=image_data,
                        ContentType=content_type,
                        Metadata=metadata
                    )
                    
                    uploaded_images[size_name] = {
                        "r2_key": key,
                        "public_url": public_url,
                        "file_size": len(image_data),
                        "content_type": content_type,
                        "uploaded_at": datetime.utcnow().isoformat()
                    }
                    
                except Exception as e:
                    upload_errors.append(f"{size_name}: {str(e)}")
            
            if upload_errors:
                print(f"❌ \033[94m[R2 Storage]\033[0m \033[1m\033[91mSome uploads failed: {', '.join(upload_errors)}\033[0m")
                return {
                    "success": False,
                    "error": f"Upload errors: {', '.join(upload_errors)}",
                    "partial_success": uploaded_images
                }
            
            print(f"✅ \033[94m[R2 Storage]\033[0m \033[1m\033[92mAll {image_type} image sizes uploaded successfully\033[0m")
            
            return {
                "success": True,
                "images": uploaded_images,
                "total_sizes": len(uploaded_images),
                "uploaded_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ \033[94m[R2 Storage]\033[0m \033[1m\033[91mMulti-size {image_type} upload failed: {str(e)}\033[0m")
            return {
                "success": False,
                "error": f"Multi-size {image_type} upload failed: {str(e)}"
            }
    
    async def get_image_by_size(self, course_id: str, filename: str, image_type: str, size: str) -> Optional[bytes]:
        """Retrieve course image by specific size and type from R2"""
        try:
            client = self.get_client()
            key = self._get_image_key(course_id, filename, image_type, size)
            
            response = client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            image_data = response['Body'].read()
            return image_data
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            print(f"Error retrieving {image_type} image ({size}): {e}")
            return None
        except Exception as e:
            print(f"Error retrieving {image_type} image ({size}): {e}")
            return None
    
    async def list_images_by_size(self, course_id: str, image_type: str) -> Dict[str, List[Dict[str, Any]]]:
        """List all images for a course organized by size and type"""
        try:
            client = self.get_client()
            prefix = f"courses/{course_id}/images/{image_type}/"
            
            response = client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            images_by_size = {
                'large': [],
                'medium': [],
                'small': [],
                'other': []  # For backward compatibility with old single-size images
            }
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    path_parts = key.split('/')
                    filename = path_parts[-1]
                    
                    # Determine size from path structure
                    size_category = 'other'
                    if len(path_parts) >= 6:  # courses/id/images/type/size/filename
                        potential_size = path_parts[-2]
                        if potential_size in ['large', 'medium', 'small']:
                            size_category = potential_size
                    
                    image_info = {
                        "key": key,
                        "filename": filename,
                        "size": obj['Size'],
                        "last_modified": obj['LastModified'].isoformat(),
                        "public_url": self._get_public_url(key)
                    }
                    
                    images_by_size[size_category].append(image_info)
            
            return images_by_size
            
        except ClientError as e:
            print(f"Error listing {image_type} images by size: {e}")
            return {'large': [], 'medium': [], 'small': [], 'other': []}
        except Exception as e:
            print(f"Error listing {image_type} images by size: {e}")
            return {'large': [], 'medium': [], 'small': [], 'other': []}
    
    async def delete_images_all_sizes(self, course_id: str, filename: str, image_type: str) -> Dict[str, bool]:
        """Delete course images in all sizes from R2 for a specific type"""
        try:
            client = self.get_client()
            sizes = ['large', 'medium', 'small']
            deletion_results = {}
            
            for size in sizes:
                try:
                    key = self._get_image_key(course_id, filename, image_type, size)
                    client.delete_object(
                        Bucket=self.bucket_name,
                        Key=key
                    )
                    deletion_results[size] = True
                except Exception as e:
                    print(f"Error deleting {size} {image_type} image: {e}")
                    deletion_results[size] = False
            
            # Also try to delete old format (backward compatibility)
            try:
                key = self._get_image_key(course_id, filename, image_type)
                client.delete_object(
                    Bucket=self.bucket_name,
                    Key=key
                )
                deletion_results['legacy'] = True
            except Exception as e:
                deletion_results['legacy'] = False
            
            return deletion_results
            
        except Exception as e:
            print(f"Error deleting {image_type} images: {e}")
            return {'large': False, 'medium': False, 'small': False, 'legacy': False}
    
    # Course Content Methods
    def _get_course_content_key(self, course_id: str, filename: str) -> str:
        """Generate R2 key for course content files"""
        return f"courses/{course_id}/content/{filename}"
    
    async def upload_course_content(self, course_id: str, content: str, filename: str, content_type: str = "text/markdown") -> Dict[str, Any]:
        """Upload course content (like generated slide content) to R2"""
        try:
            client = self.get_client()
            
            # Generate key and metadata
            key = self._get_course_content_key(course_id, filename)
            public_url = self._get_public_url(key)
            
            # Create metadata
            metadata = {
                'uploaded_at': datetime.utcnow().isoformat(),
                'course_id': course_id,
                'content_type': content_type,
                'generated_by': 'material_content_generator_agent'
            }
            
            print(f"\n📤 \033[94m[R2 Storage]\033[0m \033[1mUploading course content...\033[0m")
            print(f"   🗂️  Key: \033[93m{key}\033[0m")
            print(f"   📏 Size: \033[93m{len(content.encode('utf-8'))} bytes\033[0m")
            print(f"   📄 Type: \033[93m{content_type}\033[0m")
            
            # Upload to R2
            client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content.encode('utf-8'),
                ContentType=content_type,
                Metadata=metadata
            )
            
            print(f"✅ \033[94m[R2 Storage]\033[0m \033[1m\033[92mCourse content uploaded successfully\033[0m")
            print(f"   🌐 URL: \033[93m{public_url}\033[0m")
            
            return {
                "success": True,
                "r2_key": key,
                "public_url": public_url,
                "file_size": len(content.encode('utf-8')),
                "content_type": content_type,
                "uploaded_at": datetime.utcnow().isoformat()
            }
            
        except ClientError as e:
            print(f"❌ \033[94m[R2 Storage]\033[0m \033[1m\033[91mR2 upload failed: {str(e)}\033[0m")
            return {
                "success": False,
                "error": f"R2 upload failed: {str(e)}"
            }
        except Exception as e:
            print(f"❌ \033[94m[R2 Storage]\033[0m \033[1m\033[91mUpload failed: {str(e)}\033[0m")
            return {
                "success": False,
                "error": f"Upload failed: {str(e)}"
            }
    
    async def get_course_content(self, course_id: str, filename: str) -> Optional[str]:
        """Retrieve course content from R2"""
        try:
            client = self.get_client()
            key = self._get_course_content_key(course_id, filename)
            
            response = client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            content = response['Body'].read().decode('utf-8')
            return content
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            print(f"Error retrieving course content: {e}")
            return None
        except Exception as e:
            print(f"Error retrieving course content: {e}")
            return None
    
    async def delete_course_content(self, course_id: str, filename: str) -> bool:
        """Delete course content file from R2"""
        try:
            client = self.get_client()
            key = self._get_course_content_key(course_id, filename)
            
            client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            return True
            
        except ClientError as e:
            print(f"Error deleting course content: {e}")
            return False
        except Exception as e:
            print(f"Error deleting course content: {e}")
            return False
    
    async def list_course_content(self, course_id: str) -> List[Dict[str, Any]]:
        """List all course content files for a course"""
        try:
            client = self.get_client()
            prefix = f"courses/{course_id}/content/"
            
            response = client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            content_files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    filename = key.split('/')[-1]
                    
                    content_files.append({
                        "key": key,
                        "filename": filename,
                        "size": obj['Size'],
                        "last_modified": obj['LastModified'].isoformat(),
                        "public_url": self._get_public_url(key)
                    })
            
            return content_files
            
        except ClientError as e:
            print(f"Error listing course content: {e}")
            return []
        except Exception as e:
            print(f"Error listing course content: {e}")
            return []
