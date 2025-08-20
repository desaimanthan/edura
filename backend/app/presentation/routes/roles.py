from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime
from bson import ObjectId

from ...models import (
    Role, RoleCreate, RoleUpdate, RoleResponse, 
    PermissionResponse, UserInDB
)
from ...auth import get_current_active_user
from ...database import get_roles_collection, get_permissions_collection, get_users_collection

router = APIRouter()

@router.get("/", response_model=List[RoleResponse])
async def get_roles(current_user: UserInDB = Depends(get_current_active_user)):
    """Get all roles with populated permissions and user counts"""
    roles_collection = await get_roles_collection()
    permissions_collection = await get_permissions_collection()
    users_collection = await get_users_collection()
    
    # Get all roles
    roles_cursor = roles_collection.find({})
    roles = await roles_cursor.to_list(length=None)
    
    # Get all permissions for lookup
    permissions_cursor = permissions_collection.find({})
    permissions = await permissions_cursor.to_list(length=None)
    permissions_dict = {str(perm["_id"]): perm for perm in permissions}
    
    # Build response with populated data
    role_responses = []
    for role in roles:
        # Get user count for this role
        user_count = await users_collection.count_documents({"role_id": role["_id"]})
        
        # Populate permissions
        populated_permissions = []
        for perm_id in role.get("permission_ids", []):
            if perm_id in permissions_dict:
                perm = permissions_dict[perm_id]
                populated_permissions.append(PermissionResponse(
                    _id=str(perm["_id"]),
                    name=perm["name"],
                    description=perm["description"],
                    resource=perm["resource"],
                    action=perm["action"],
                    created_at=perm["created_at"]
                ))
        
        role_responses.append(RoleResponse(
            _id=str(role["_id"]),
            name=role["name"],
            description=role["description"],
            permission_ids=role.get("permission_ids", []),
            permissions=populated_permissions,
            user_count=user_count,
            created_at=role["created_at"],
            updated_at=role["updated_at"]
        ))
    
    return role_responses

@router.post("/", response_model=RoleResponse)
async def create_role(
    role_data: RoleCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create a new role"""
    roles_collection = await get_roles_collection()
    permissions_collection = await get_permissions_collection()
    
    # Check if role name already exists
    existing_role = await roles_collection.find_one({"name": role_data.name})
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role with this name already exists"
        )
    
    # Validate permission IDs
    if role_data.permission_ids:
        permission_object_ids = []
        for perm_id in role_data.permission_ids:
            if not ObjectId.is_valid(perm_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid permission ID: {perm_id}"
                )
            permission_object_ids.append(ObjectId(perm_id))
        
        # Check if all permissions exist
        existing_perms = await permissions_collection.count_documents(
            {"_id": {"$in": permission_object_ids}}
        )
        if existing_perms != len(permission_object_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more permission IDs do not exist"
            )
    
    # Create role
    role = Role(
        name=role_data.name,
        description=role_data.description,
        permission_ids=role_data.permission_ids
    )
    
    result = await roles_collection.insert_one(role.dict(by_alias=True))
    
    # Get created role with populated permissions
    created_role = await roles_collection.find_one({"_id": result.inserted_id})
    
    # Populate permissions
    populated_permissions = []
    if role_data.permission_ids:
        permissions_cursor = permissions_collection.find(
            {"_id": {"$in": [ObjectId(pid) for pid in role_data.permission_ids]}}
        )
        permissions = await permissions_cursor.to_list(length=None)
        populated_permissions = [
            PermissionResponse(
                _id=str(perm["_id"]),
                name=perm["name"],
                description=perm["description"],
                resource=perm["resource"],
                action=perm["action"],
                created_at=perm["created_at"]
            ) for perm in permissions
        ]
    
    return RoleResponse(
        _id=str(created_role["_id"]),
        name=created_role["name"],
        description=created_role["description"],
        permission_ids=created_role.get("permission_ids", []),
        permissions=populated_permissions,
        user_count=0,
        created_at=created_role["created_at"],
        updated_at=created_role["updated_at"]
    )

@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: str,
    role_data: RoleUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update a role"""
    if not ObjectId.is_valid(role_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role ID"
        )
    
    roles_collection = await get_roles_collection()
    permissions_collection = await get_permissions_collection()
    users_collection = await get_users_collection()
    
    # Check if role exists
    existing_role = await roles_collection.find_one({"_id": ObjectId(role_id)})
    if not existing_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Build update data
    update_data = {"updated_at": datetime.utcnow()}
    
    if role_data.name is not None:
        # Check if new name conflicts with existing role
        name_conflict = await roles_collection.find_one({
            "name": role_data.name,
            "_id": {"$ne": ObjectId(role_id)}
        })
        if name_conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role with this name already exists"
            )
        update_data["name"] = role_data.name
    
    if role_data.description is not None:
        update_data["description"] = role_data.description
    
    if role_data.permission_ids is not None:
        # Validate permission IDs
        if role_data.permission_ids:
            permission_object_ids = []
            for perm_id in role_data.permission_ids:
                if not ObjectId.is_valid(perm_id):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid permission ID: {perm_id}"
                    )
                permission_object_ids.append(ObjectId(perm_id))
            
            # Check if all permissions exist
            existing_perms = await permissions_collection.count_documents(
                {"_id": {"$in": permission_object_ids}}
            )
            if existing_perms != len(permission_object_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One or more permission IDs do not exist"
                )
        
        update_data["permission_ids"] = role_data.permission_ids
    
    # Update role
    result = await roles_collection.update_one(
        {"_id": ObjectId(role_id)},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No changes made"
        )
    
    # Get updated role
    updated_role = await roles_collection.find_one({"_id": ObjectId(role_id)})
    
    # Get user count
    user_count = await users_collection.count_documents({"role_id": ObjectId(role_id)})
    
    # Populate permissions
    populated_permissions = []
    if updated_role.get("permission_ids"):
        permissions_cursor = permissions_collection.find(
            {"_id": {"$in": [ObjectId(pid) for pid in updated_role["permission_ids"]]}}
        )
        permissions = await permissions_cursor.to_list(length=None)
        populated_permissions = [
            PermissionResponse(
                _id=str(perm["_id"]),
                name=perm["name"],
                description=perm["description"],
                resource=perm["resource"],
                action=perm["action"],
                created_at=perm["created_at"]
            ) for perm in permissions
        ]
    
    return RoleResponse(
        _id=str(updated_role["_id"]),
        name=updated_role["name"],
        description=updated_role["description"],
        permission_ids=updated_role.get("permission_ids", []),
        permissions=populated_permissions,
        user_count=user_count,
        created_at=updated_role["created_at"],
        updated_at=updated_role["updated_at"]
    )

@router.delete("/{role_id}")
async def delete_role(
    role_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Delete a role"""
    if not ObjectId.is_valid(role_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role ID"
        )
    
    roles_collection = await get_roles_collection()
    users_collection = await get_users_collection()
    
    # Check if role exists
    existing_role = await roles_collection.find_one({"_id": ObjectId(role_id)})
    if not existing_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Check if any users have this role
    users_with_role = await users_collection.count_documents({"role_id": ObjectId(role_id)})
    if users_with_role > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete role. {users_with_role} users are assigned to this role."
        )
    
    # Delete role
    result = await roles_collection.delete_one({"_id": ObjectId(role_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete role"
        )
    
    return {"message": "Role deleted successfully"}

@router.get("/{role_id}/users")
async def get_role_users(
    role_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get all users assigned to a specific role"""
    if not ObjectId.is_valid(role_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role ID"
        )
    
    roles_collection = await get_roles_collection()
    users_collection = await get_users_collection()
    
    # Check if role exists
    role = await roles_collection.find_one({"_id": ObjectId(role_id)})
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Get users with this role
    users_cursor = users_collection.find({"role_id": ObjectId(role_id)})
    users = await users_cursor.to_list(length=None)
    
    return {
        "role_name": role["name"],
        "users": [
            {
                "id": str(user["_id"]),
                "name": user["name"],
                "email": user["email"],
                "is_active": user["is_active"],
                "created_at": user["created_at"]
            } for user in users
        ]
    }
