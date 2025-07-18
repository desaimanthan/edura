"""
Seed script to populate the database with default roles and permissions
Run this script after setting up the database to create initial data
"""

import asyncio
from datetime import datetime
from bson import ObjectId

from app.database import connect_to_mongo, get_roles_collection, get_permissions_collection, get_users_collection
from app.models import Role, Permission

# Default permissions
DEFAULT_PERMISSIONS = [
    # User Management
    {"name": "user_read", "description": "View users", "resource": "users", "action": "read"},
    {"name": "user_create", "description": "Create users", "resource": "users", "action": "create"},
    {"name": "user_update", "description": "Update users", "resource": "users", "action": "update"},
    {"name": "user_delete", "description": "Delete users", "resource": "users", "action": "delete"},
    
    # Role Management
    {"name": "role_read", "description": "View roles", "resource": "roles", "action": "read"},
    {"name": "role_create", "description": "Create roles", "resource": "roles", "action": "create"},
    {"name": "role_update", "description": "Update roles", "resource": "roles", "action": "update"},
    {"name": "role_delete", "description": "Delete roles", "resource": "roles", "action": "delete"},
    
    # Permission Management
    {"name": "permission_read", "description": "View permissions", "resource": "permissions", "action": "read"},
    {"name": "permission_create", "description": "Create permissions", "resource": "permissions", "action": "create"},
    {"name": "permission_update", "description": "Update permissions", "resource": "permissions", "action": "update"},
    {"name": "permission_delete", "description": "Delete permissions", "resource": "permissions", "action": "delete"},
    
    # Dashboard
    {"name": "dashboard_read", "description": "View dashboard", "resource": "dashboard", "action": "read"},
    {"name": "dashboard_admin", "description": "Admin dashboard access", "resource": "dashboard", "action": "admin"},
    
    # Masters
    {"name": "masters_read", "description": "View masters", "resource": "masters", "action": "read"},
    {"name": "masters_manage", "description": "Manage masters", "resource": "masters", "action": "manage"},
    
    # Content Management (for future use)
    {"name": "content_read", "description": "View content", "resource": "content", "action": "read"},
    {"name": "content_create", "description": "Create content", "resource": "content", "action": "create"},
    {"name": "content_update", "description": "Update content", "resource": "content", "action": "update"},
    {"name": "content_delete", "description": "Delete content", "resource": "content", "action": "delete"},
    
    # Profile Management
    {"name": "profile_read", "description": "View own profile", "resource": "profile", "action": "read"},
    {"name": "profile_update", "description": "Update own profile", "resource": "profile", "action": "update"},
]

async def seed_permissions():
    """Create default permissions"""
    permissions_collection = await get_permissions_collection()
    
    print("Creating default permissions...")
    
    permission_ids = {}
    
    for perm_data in DEFAULT_PERMISSIONS:
        # Check if permission already exists
        existing = await permissions_collection.find_one({"name": perm_data["name"]})
        
        if not existing:
            permission = Permission(**perm_data)
            result = await permissions_collection.insert_one(permission.dict(by_alias=True))
            permission_ids[perm_data["name"]] = str(result.inserted_id)
            print(f"  ✓ Created permission: {perm_data['name']}")
        else:
            permission_ids[perm_data["name"]] = str(existing["_id"])
            print(f"  - Permission already exists: {perm_data['name']}")
    
    return permission_ids

async def seed_roles(permission_ids):
    """Create default roles with assigned permissions"""
    roles_collection = await get_roles_collection()
    
    print("\nCreating default roles...")
    
    # Define roles with their permissions
    roles_data = [
        {
            "name": "Administrator",
            "description": "Full system access with all permissions",
            "permissions": [
                "user_read", "user_create", "user_update", "user_delete",
                "role_read", "role_create", "role_update", "role_delete",
                "permission_read", "permission_create", "permission_update", "permission_delete",
                "dashboard_read", "dashboard_admin",
                "masters_read", "masters_manage",
                "content_read", "content_create", "content_update", "content_delete",
                "profile_read", "profile_update"
            ]
        },
        {
            "name": "Teacher",
            "description": "Access to teaching materials and student management",
            "permissions": [
                "user_read",
                "role_read",
                "permission_read",
                "dashboard_read",
                "masters_read",
                "content_read", "content_create", "content_update",
                "profile_read", "profile_update"
            ]
        },
        {
            "name": "Student",
            "description": "Basic access to learning materials and assignments",
            "permissions": [
                "dashboard_read",
                "content_read",
                "profile_read", "profile_update"
            ]
        }
    ]
    
    role_ids = {}
    
    for role_data in roles_data:
        # Check if role already exists
        existing = await roles_collection.find_one({"name": role_data["name"]})
        
        if not existing:
            # Map permission names to IDs
            permission_id_list = []
            for perm_name in role_data["permissions"]:
                if perm_name in permission_ids:
                    permission_id_list.append(permission_ids[perm_name])
            
            role = Role(
                name=role_data["name"],
                description=role_data["description"],
                permission_ids=permission_id_list
            )
            
            result = await roles_collection.insert_one(role.dict(by_alias=True))
            role_ids[role_data["name"]] = str(result.inserted_id)
            print(f"  ✓ Created role: {role_data['name']} with {len(permission_id_list)} permissions")
        else:
            role_ids[role_data["name"]] = str(existing["_id"])
            print(f"  - Role already exists: {role_data['name']}")
    
    return role_ids

async def assign_default_roles(role_ids):
    """Assign Student role to users who don't have a role"""
    users_collection = await get_users_collection()
    
    print("\nAssigning default roles to existing users...")
    
    student_role_id = role_ids.get("Student")
    if not student_role_id:
        print("  ! Student role not found, skipping role assignment")
        return
    
    # Find users without roles
    users_without_roles = await users_collection.count_documents({"role_id": {"$exists": False}})
    
    if users_without_roles > 0:
        # Update users without roles to have Student role (convert to ObjectId)
        result = await users_collection.update_many(
            {"role_id": {"$exists": False}},
            {"$set": {"role_id": ObjectId(student_role_id), "updated_at": datetime.utcnow()}}
        )
        print(f"  ✓ Assigned Student role to {result.modified_count} users")
    else:
        # Check if existing users have string role_ids and convert them to ObjectId
        users_with_string_roles = await users_collection.find({"role_id": {"$type": "string"}}).to_list(length=None)
        if users_with_string_roles:
            print(f"  ! Found {len(users_with_string_roles)} users with string role_ids, converting to ObjectId...")
            for user in users_with_string_roles:
                try:
                    await users_collection.update_one(
                        {"_id": user["_id"]},
                        {"$set": {"role_id": ObjectId(user["role_id"]), "updated_at": datetime.utcnow()}}
                    )
                except Exception as e:
                    print(f"    ! Error converting role_id for user {user.get('email', user['_id'])}: {e}")
            print(f"  ✓ Converted string role_ids to ObjectId for existing users")
        else:
            print("  - All users already have roles assigned")

async def main():
    """Main seed function"""
    print("🌱 Starting database seeding...")
    
    try:
        # Connect to database
        await connect_to_mongo()
        print("✓ Connected to database")
        
        # Seed permissions
        permission_ids = await seed_permissions()
        
        # Seed roles
        role_ids = await seed_roles(permission_ids)
        
        # Assign default roles to existing users
        await assign_default_roles(role_ids)
        
        print("\n🎉 Database seeding completed successfully!")
        print("\nDefault roles created:")
        print("  - Administrator: Full system access")
        print("  - Teacher: Teaching and content management")
        print("  - Student: Basic learning access (default for new users)")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        raise
    
    finally:
        # Close database connection
        from app.database import close_mongo_connection
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(main())
