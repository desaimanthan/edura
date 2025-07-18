from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from typing import List
from bson import ObjectId

from ..models import UserResponse, UserInDB
from ..auth import get_current_active_user
from ..database import get_users_collection, get_roles_collection

router = APIRouter()

@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user: UserInDB = Depends(get_current_active_user)):
    """Get current user profile"""
    return UserResponse(
        _id=str(current_user.id),
        email=current_user.email,
        name=current_user.name,
        is_active=current_user.is_active,
        google_id=current_user.google_id,
        avatar=current_user.avatar,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )

@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    profile_data: dict,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update user profile"""
    users_collection = await get_users_collection()
    
    # Only allow updating certain fields
    allowed_fields = {"name"}
    update_data = {
        key: value for key, value in profile_data.items() 
        if key in allowed_fields and value is not None
    }
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )
    
    update_data["updated_at"] = datetime.utcnow()
    
    # Update user in database
    result = await users_collection.update_one(
        {"_id": current_user.id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No changes made"
        )
    
    # Get updated user
    updated_user = await users_collection.find_one({"_id": current_user.id})
    
    return UserResponse(
        _id=str(updated_user["_id"]),
        email=updated_user["email"],
        name=updated_user["name"],
        is_active=updated_user["is_active"],
        google_id=updated_user.get("google_id"),
        avatar=updated_user.get("avatar"),
        created_at=updated_user["created_at"],
        updated_at=updated_user["updated_at"]
    )

@router.delete("/profile")
async def delete_user_account(current_user: UserInDB = Depends(get_current_active_user)):
    """Delete user account"""
    users_collection = await get_users_collection()
    
    # Soft delete - mark as inactive
    result = await users_collection.update_one(
        {"_id": current_user.id},
        {
            "$set": {
                "is_active": False,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete account"
        )
    
    return {"message": "Account deleted successfully"}


# Admin endpoints for user management
@router.get("/", response_model=List[dict])
async def get_all_users(current_user: UserInDB = Depends(get_current_active_user)):
    """Get all users with their role information (admin only)"""
    users_collection = await get_users_collection()
    roles_collection = await get_roles_collection()
    
    # Get all users
    users_cursor = users_collection.find({})
    users = await users_cursor.to_list(length=None)
    
    # Get all roles for lookup
    roles_cursor = roles_collection.find({})
    roles = await roles_cursor.to_list(length=None)
    roles_dict = {str(role["_id"]): role for role in roles}
    
    # Populate users with role information
    result = []
    for user in users:
        role_id = user.get("role_id")
        role = roles_dict.get(str(role_id)) if role_id else None
        
        user_data = {
            "_id": str(user["_id"]),
            "email": user["email"],
            "name": user["name"],
            "role_id": str(role_id) if role_id else None,
            "role": {
                "_id": str(role["_id"]),
                "name": role["name"],
                "description": role["description"]
            } if role else {"_id": "", "name": "No Role", "description": "No role assigned"},
            "is_active": user.get("is_active", True),
            "created_at": user["created_at"].isoformat() if user.get("created_at") else None,
            "updated_at": user["updated_at"].isoformat() if user.get("updated_at") else None
        }
        result.append(user_data)
    
    return result


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    user_data: dict,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update user (admin only)"""
    users_collection = await get_users_collection()
    
    try:
        user_object_id = ObjectId(user_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )
    
    # Check if user exists
    existing_user = await users_collection.find_one({"_id": user_object_id})
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prepare update data
    allowed_fields = {"name", "email", "role_id", "is_active"}
    update_data = {
        key: value for key, value in user_data.items() 
        if key in allowed_fields and value is not None
    }
    
    # Convert role_id to ObjectId if provided
    if "role_id" in update_data and update_data["role_id"]:
        try:
            update_data["role_id"] = ObjectId(update_data["role_id"])
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role ID"
            )
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )
    
    update_data["updated_at"] = datetime.utcnow()
    
    # Update user
    result = await users_collection.update_one(
        {"_id": user_object_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No changes made"
        )
    
    # Get updated user with role information
    updated_user = await users_collection.find_one({"_id": user_object_id})
    
    # Get role information
    role = None
    if updated_user.get("role_id"):
        roles_collection = await get_roles_collection()
        role = await roles_collection.find_one({"_id": updated_user["role_id"]})
    
    return {
        "_id": str(updated_user["_id"]),
        "email": updated_user["email"],
        "name": updated_user["name"],
        "role_id": str(updated_user["role_id"]) if updated_user.get("role_id") else None,
        "role": {
            "_id": str(role["_id"]),
            "name": role["name"],
            "description": role["description"]
        } if role else {"_id": "", "name": "No Role", "description": "No role assigned"},
        "is_active": updated_user.get("is_active", True),
        "created_at": updated_user["created_at"].isoformat() if updated_user.get("created_at") else None,
        "updated_at": updated_user["updated_at"].isoformat() if updated_user.get("updated_at") else None
    }


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Delete user (admin only)"""
    users_collection = await get_users_collection()
    
    try:
        user_object_id = ObjectId(user_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )
    
    # Check if user exists
    existing_user = await users_collection.find_one({"_id": user_object_id})
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Don't allow deleting yourself
    if str(user_object_id) == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Delete user
    result = await users_collection.delete_one({"_id": user_object_id})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete user"
        )
    
    return {"message": "User deleted successfully"}
