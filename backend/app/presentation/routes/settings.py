from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime
from bson import ObjectId
from typing import List

from ...models import (
    SystemSettings, SystemSettingsUpdate, SystemSettingsResponse, UserInDB
)
from ...auth import get_current_active_user
from ...database import get_database

router = APIRouter()

async def get_settings_collection():
    """Get the system settings collection"""
    db = await get_database()
    return db.system_settings

async def is_admin(current_user: UserInDB):
    """Check if current user is an administrator"""
    db = await get_database()
    roles_collection = db.roles
    
    admin_role = await roles_collection.find_one({"name": "Administrator"})
    
    if not admin_role or str(current_user.role_id) != str(admin_role["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access system settings"
        )
    
    return True

@router.get("/", response_model=List[SystemSettingsResponse])
async def get_all_settings(current_user: UserInDB = Depends(get_current_active_user)):
    """Get all system settings (Admin only)"""
    await is_admin(current_user)
    
    settings_collection = await get_settings_collection()
    settings = await settings_collection.find().to_list(length=None)
    
    response_list = []
    for setting in settings:
        setting_dict = dict(setting)
        setting_dict["_id"] = str(setting_dict["_id"])
        if "updated_by" in setting_dict and setting_dict["updated_by"]:
            setting_dict["updated_by"] = str(setting_dict["updated_by"])
        response_list.append(SystemSettingsResponse(**setting_dict))
    return response_list

@router.get("/{setting_key}", response_model=SystemSettingsResponse)
async def get_setting(setting_key: str):
    """Get a specific system setting by key (Public - for checking teacher approval flow)"""
    settings_collection = await get_settings_collection()
    
    setting = await settings_collection.find_one({"setting_key": setting_key})
    
    if not setting:
        # Return default value for teacher approval flow
        if setting_key == "teacher_approval_required":
            return SystemSettingsResponse(
                _id="default",
                setting_key="teacher_approval_required",
                setting_value=True,  # Default to requiring approval
                setting_type="boolean",
                description="Whether teacher accounts require admin approval",
                updated_by=None,
                updated_at=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting with key '{setting_key}' not found"
        )
    
    setting_dict = dict(setting)
    setting_dict["_id"] = str(setting_dict["_id"])
    if "updated_by" in setting_dict and setting_dict["updated_by"]:
        setting_dict["updated_by"] = str(setting_dict["updated_by"])
    return SystemSettingsResponse(**setting_dict)

@router.put("/{setting_key}", response_model=SystemSettingsResponse)
async def update_setting(
    setting_key: str,
    update_data: SystemSettingsUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update a system setting (Admin only)"""
    await is_admin(current_user)
    
    settings_collection = await get_settings_collection()
    
    # Check if setting exists
    existing_setting = await settings_collection.find_one({"setting_key": setting_key})
    
    if existing_setting:
        # Update existing setting
        await settings_collection.update_one(
            {"setting_key": setting_key},
            {
                "$set": {
                    "setting_value": update_data.setting_value,
                    "updated_by": current_user.id,
                    "updated_at": datetime.utcnow()
                }
            }
        )
    else:
        # Create new setting if it doesn't exist (for teacher_approval_required)
        if setting_key == "teacher_approval_required":
            new_setting = {
                "setting_key": setting_key,
                "setting_value": update_data.setting_value,
                "setting_type": "boolean",
                "description": "Whether teacher accounts require admin approval",
                "updated_by": current_user.id,
                "updated_at": datetime.utcnow(),
                "created_at": datetime.utcnow()
            }
            result = await settings_collection.insert_one(new_setting)
            new_setting["_id"] = result.inserted_id
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting with key '{setting_key}' not found"
            )
    
    # Get updated setting
    updated_setting = await settings_collection.find_one({"setting_key": setting_key})
    
    updated_dict = dict(updated_setting)
    updated_dict["_id"] = str(updated_dict["_id"])
    if "updated_by" in updated_dict and updated_dict["updated_by"]:
        updated_dict["updated_by"] = str(updated_dict["updated_by"])
    return SystemSettingsResponse(**updated_dict)

@router.post("/initialize", response_model=dict)
async def initialize_settings(current_user: UserInDB = Depends(get_current_active_user)):
    """Initialize default system settings (Admin only)"""
    await is_admin(current_user)
    
    settings_collection = await get_settings_collection()
    
    # Default settings
    default_settings = [
        {
            "setting_key": "teacher_approval_required",
            "setting_value": True,
            "setting_type": "boolean",
            "description": "Whether teacher accounts require admin approval",
            "updated_by": current_user.id,
            "updated_at": datetime.utcnow(),
            "created_at": datetime.utcnow()
        }
    ]
    
    initialized = []
    for setting in default_settings:
        # Check if setting already exists
        existing = await settings_collection.find_one({"setting_key": setting["setting_key"]})
        if not existing:
            await settings_collection.insert_one(setting)
            initialized.append(setting["setting_key"])
    
    return {
        "message": "Settings initialized successfully",
        "initialized_settings": initialized
    }
