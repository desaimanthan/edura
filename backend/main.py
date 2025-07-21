from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from decouple import config
import uvicorn

from app.routes import auth, users, roles, permissions
from app.database import connect_to_mongo, close_mongo_connection

app = FastAPI(
    title="ProfessorAI API",
    description="Authentication API for ProfessorAI application",
    version="1.0.0"
)

# Session middleware for OAuth state management
app.add_middleware(
    SessionMiddleware, 
    secret_key=config("JWT_SECRET_KEY", default="your-secret-key")
)

# CORS middleware - more permissive for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        config("FRONTEND_URL", default="http://localhost:3000")
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Database connection events
@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(roles.router, prefix="/masters/roles", tags=["roles"])
app.include_router(permissions.router, prefix="/masters/permissions", tags=["permissions"])

@app.get("/")
async def root():
    return {"message": "ProfessorAI API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config("HOST", default="0.0.0.0"),
        port=config("PORT", default=8000, cast=int),
        reload=True
    )
