from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from bson import ObjectId

from ..models import (
    Permission, PermissionCreate, PermissionResponse, UserInDB
)
from ..auth import get_current_active_user
from ..database import get_permissions_collection, get_roles_collection

router = APIRouter()

@router.get("/", response_model=List[PermissionResponse])
async def get_permissions(current_user: UserInDB = Depends(get_current_active_user)):
    """Get all permissions"""
    permissions_collection = await get_permissions_collection()
    
    # Get all permissions
    permissions_cursor = permissions_collection.find({}).sort("resource", 1).sort("action", 1)
    permissions = await permissions_cursor.to_list(length=None)
    
    return [
        PermissionResponse(
            _id=str(perm["_id"]),
            name=perm["name"],
            description=perm["description"],
            resource=perm["resource"],
            action=perm["action"],
            created_at=perm["created_at"]
        ) for perm in permissions
    ]

@router.post("/", response_model=PermissionResponse)
async def create_permission(
    permission_data: PermissionCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create a new permission"""
    permissions_collection = await get_permissions_collection()
    
    # Check if permission name already exists
    existing_permission = await permissions_collection.find_one({"name": permission_data.name})
    if existing_permission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission with this name already exists"
        )
    
    # Check if resource + action combination already exists
    existing_combo = await permissions_collection.find_one({
        "resource": permission_data.resource,
        "action": permission_data.action
    })
    if existing_combo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Permission for {permission_data.resource}:{permission_data.action} already exists"
        )
    
    # Create permission
    permission = Permission(
        name=permission_data.name,
        description=permission_data.description,
        resource=permission_data.resource,
        action=permission_data.action
    )
    
    result = await permissions_collection.insert_one(permission.dict(by_alias=True))
    
    # Get created permission
    created_permission = await permissions_collection.find_one({"_id": result.inserted_id})
    
    return PermissionResponse(
        _id=str(created_permission["_id"]),
        name=created_permission["name"],
        description=created_permission["description"],
        resource=created_permission["resource"],
        action=created_permission["action"],
        created_at=created_permission["created_at"]
    )

@router.put("/{permission_id}", response_model=PermissionResponse)
async def update_permission(
    permission_id: str,
    permission_data: PermissionCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update a permission"""
    if not ObjectId.is_valid(permission_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid permission ID"
        )
    
    permissions_collection = await get_permissions_collection()
    
    # Check if permission exists
    existing_permission = await permissions_collection.find_one({"_id": ObjectId(permission_id)})
    if not existing_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    
    # Check if new name conflicts with existing permission
    name_conflict = await permissions_collection.find_one({
        "name": permission_data.name,
        "_id": {"$ne": ObjectId(permission_id)}
    })
    if name_conflict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission with this name already exists"
        )
    
    # Check if new resource + action combination conflicts
    combo_conflict = await permissions_collection.find_one({
        "resource": permission_data.resource,
        "action": permission_data.action,
        "_id": {"$ne": ObjectId(permission_id)}
    })
    if combo_conflict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Permission for {permission_data.resource}:{permission_data.action} already exists"
        )
    
    # Update permission
    update_data = {
        "name": permission_data.name,
        "description": permission_data.description,
        "resource": permission_data.resource,
        "action": permission_data.action
    }
    
    result = await permissions_collection.update_one(
        {"_id": ObjectId(permission_id)},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No changes made"
        )
    
    # Get updated permission
    updated_permission = await permissions_collection.find_one({"_id": ObjectId(permission_id)})
    
    return PermissionResponse(
        _id=str(updated_permission["_id"]),
        name=updated_permission["name"],
        description=updated_permission["description"],
        resource=updated_permission["resource"],
        action=updated_permission["action"],
        created_at=updated_permission["created_at"]
    )

@router.delete("/{permission_id}")
async def delete_permission(
    permission_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Delete a permission"""
    if not ObjectId.is_valid(permission_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid permission ID"
        )
    
    permissions_collection = await get_permissions_collection()
    roles_collection = await get_roles_collection()
    
    # Check if permission exists
    existing_permission = await permissions_collection.find_one({"_id": ObjectId(permission_id)})
    if not existing_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    
    # Check if any roles use this permission
    roles_with_permission = await roles_collection.count_documents(
        {"permission_ids": permission_id}
    )
    if roles_with_permission > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete permission. {roles_with_permission} roles are using this permission."
        )
    
    # Delete permission
    result = await permissions_collection.delete_one({"_id": ObjectId(permission_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete permission"
        )
    
    return {"message": "Permission deleted successfully"}

@router.get("/{permission_id}/roles")
async def get_permission_roles(
    permission_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get all roles that have a specific permission"""
    if not ObjectId.is_valid(permission_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid permission ID"
        )
    
    permissions_collection = await get_permissions_collection()
    roles_collection = await get_roles_collection()
    
    # Check if permission exists
    permission = await permissions_collection.find_one({"_id": ObjectId(permission_id)})
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    
    # Get roles with this permission
    roles_cursor = roles_collection.find({"permission_ids": permission_id})
    roles = await roles_cursor.to_list(length=None)
    
    return {
        "permission_name": permission["name"],
        "roles": [
            {
                "id": str(role["_id"]),
                "name": role["name"],
                "description": role["description"],
                "created_at": role["created_at"]
            } for role in roles
        ]
    }

@router.get("/resources")
async def get_permission_resources(current_user: UserInDB = Depends(get_current_active_user)):
    """Get all unique resources from permissions"""
    permissions_collection = await get_permissions_collection()
    
    # Get distinct resources
    resources = await permissions_collection.distinct("resource")
    
    return {"resources": sorted(resources)}

@router.get("/actions")
async def get_permission_actions(current_user: UserInDB = Depends(get_current_active_user)):
    """Get all unique actions from permissions"""
    permissions_collection = await get_permissions_collection()
    
    # Get distinct actions
    actions = await permissions_collection.distinct("action")
    
    return {"actions": sorted(actions)}
