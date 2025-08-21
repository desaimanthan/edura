from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from decouple import config
import uvicorn
import time
import os

from app.presentation.routes import auth, users, roles, permissions, courses
from app.database import connect_to_mongo, close_mongo_connection

# Determine if we're in production
IS_PRODUCTION = config("ENVIRONMENT", default="development") == "production"

app = FastAPI(
    title="Edura API",
    description="Educational platform API with AI-powered course generation",
    version="1.0.0",
    docs_url=None if IS_PRODUCTION else "/docs",  # Disable docs in production
    redoc_url=None if IS_PRODUCTION else "/redoc"  # Disable redoc in production
)

# Add request logging middleware (simplified for production)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    if not IS_PRODUCTION:
        print(f"🌐 [REQUEST] {request.method} {request.url}")
        print(f"   🔍 Path: {request.url.path}")
        print(f"   📊 Query params: {dict(request.query_params)}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    if not IS_PRODUCTION:
        print(f"✅ [RESPONSE] {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.4f}s")
    else:
        # Production logging - only log errors and important info
        if response.status_code >= 400:
            print(f"❌ [ERROR] {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.4f}s")
    
    return response

# Session middleware for OAuth state management
app.add_middleware(
    SessionMiddleware, 
    secret_key=config("JWT_SECRET_KEY", default="your-secret-key")
)

# CORS middleware - production-ready configuration
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    config("FRONTEND_URL", default="http://localhost:3000")
]

# Add additional production origins if specified
production_origins = config("PRODUCTION_ORIGINS", default="").split(",")
if production_origins and production_origins[0]:  # Check if not empty
    allowed_origins.extend([origin.strip() for origin in production_origins])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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
app.include_router(courses.router, prefix="/courses", tags=["courses"])

@app.get("/")
async def root():
    return {"message": "Edura API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    # Production-ready server configuration
    uvicorn.run(
        "main:app",
        host=config("HOST", default="0.0.0.0"),
        port=config("PORT", default=8000, cast=int),
        reload=not IS_PRODUCTION,  # Disable reload in production
        workers=1 if IS_PRODUCTION else 1,  # Koyeb handles scaling
        access_log=not IS_PRODUCTION,  # Reduce logging in production
        log_level="info" if IS_PRODUCTION else "debug"
    )
