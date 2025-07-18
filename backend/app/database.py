from motor.motor_asyncio import AsyncIOMotorClient
from decouple import config
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    database = None

db = Database()

async def get_database():
    return db.database

async def connect_to_mongo():
    """Create database connection"""
    try:
        db.client = AsyncIOMotorClient(config("MONGODB_URI"))
        db.database = db.client[config("DATABASE_NAME", default="ProfessorAI")]
        
        # Test the connection
        await db.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        
        # Create indexes
        await create_indexes()
        
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
        logger.info("Disconnected from MongoDB")

async def create_indexes():
    """Create database indexes for better performance"""
    try:
        # Create unique index on email for users collection
        await db.database.users.create_index("email", unique=True)
        
        # Create unique index on role name
        await db.database.roles.create_index("name", unique=True)
        
        # Create unique index on permission name
        await db.database.permissions.create_index("name", unique=True)
        
        # Create compound index on permission resource and action
        await db.database.permissions.create_index([("resource", 1), ("action", 1)])
        
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")

# Collection getters
async def get_users_collection():
    database = await get_database()
    return database.users

async def get_password_reset_collection():
    database = await get_database()
    return database.password_resets

async def get_roles_collection():
    database = await get_database()
    return database.roles

async def get_permissions_collection():
    database = await get_database()
    return database.permissions
