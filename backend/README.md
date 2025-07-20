# ProfessorAI Backend

FastAPI-based backend service providing authentication, user management, and role-based access control for the ProfessorAI educational platform.

## 🚀 Overview

This backend service provides a robust API for user authentication, role-based permissions, and educational content management. Built with FastAPI and MongoDB, it offers high performance and scalability.

## ✨ Features

- **Authentication & Authorization**
  - JWT token-based authentication
  - Google OAuth 2.0 integration
  - Password hashing with bcrypt
  - Session management with middleware

- **Role-Based Access Control (RBAC)**
  - Granular permission system
  - Resource-based access control
  - Default roles: Administrator, Teacher, Student
  - Dynamic role and permission management

- **User Management**
  - User registration and login
  - Profile management
  - Password reset functionality
  - Google account integration

- **Database Management**
  - MongoDB with async Motor driver
  - Pydantic models for data validation
  - Database seeding with default data
  - Connection pooling and optimization

## 🛠️ Technology Stack

- **Framework**: FastAPI 0.104.1
- **Database**: MongoDB with Motor (async driver)
- **Authentication**: 
  - JWT with python-jose
  - Google OAuth with authlib
  - Password hashing with passlib[bcrypt]
- **Validation**: Pydantic models with email validation
- **ASGI Server**: Uvicorn with standard extras
- **Configuration**: python-decouple for environment variables

## 📦 Dependencies

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
motor==3.3.2
pymongo==4.6.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
python-decouple==3.8
google-auth==2.23.4
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.2.0
authlib==1.2.1
pydantic[email]>=2.8.0
```

## 🚦 Getting Started

### Prerequisites
- Python 3.8 or higher
- MongoDB database (local or cloud)
- Google OAuth credentials (optional)

### Installation

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Create a `.env` file in the backend directory:
   ```env
   # Database
   MONGODB_URL=mongodb://localhost:27017
   DATABASE_NAME=professorai

   # JWT Configuration
   JWT_SECRET_KEY=your-super-secret-jwt-key-here
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30

   # Server Configuration
   HOST=0.0.0.0
   PORT=8000
   FRONTEND_URL=http://localhost:3000

   # Google OAuth (Optional)
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
   ```

5. **Initialize Database**
   ```bash
   python seed_data.py
   ```

6. **Start the server**
   ```bash
   python main.py
   ```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📁 Project Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── seed_data.py           # Database initialization script
├── .env                   # Environment variables (create this)
└── app/
    ├── __init__.py
    ├── auth.py            # Authentication utilities
    ├── database.py        # MongoDB connection and utilities
    ├── models.py          # Pydantic data models
    └── routes/
        ├── __init__.py
        ├── auth.py        # Authentication endpoints
        ├── users.py       # User management endpoints
        ├── roles.py       # Role management endpoints
        └── permissions.py # Permission management endpoints
```

## 🌐 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/google` - Google OAuth login
- `GET /auth/google/callback` - Google OAuth callback
- `POST /auth/logout` - User logout
- `POST /auth/refresh` - Refresh access token
- `POST /auth/forgot-password` - Request password reset
- `POST /auth/reset-password` - Reset password

### User Management
- `GET /users` - List all users (Admin only)
- `GET /users/me` - Get current user profile
- `PUT /users/me` - Update current user profile
- `GET /users/{user_id}` - Get user by ID (Admin only)
- `PUT /users/{user_id}` - Update user (Admin only)
- `DELETE /users/{user_id}` - Delete user (Admin only)

### Role Management
- `GET /masters/roles` - List all roles
- `POST /masters/roles` - Create new role (Admin only)
- `GET /masters/roles/{role_id}` - Get role by ID
- `PUT /masters/roles/{role_id}` - Update role (Admin only)
- `DELETE /masters/roles/{role_id}` - Delete role (Admin only)

### Permission Management
- `GET /masters/permissions` - List all permissions
- `POST /masters/permissions` - Create new permission (Admin only)
- `GET /masters/permissions/{permission_id}` - Get permission by ID
- `PUT /masters/permissions/{permission_id}` - Update permission (Admin only)
- `DELETE /masters/permissions/{permission_id}` - Delete permission (Admin only)

### Health Check
- `GET /` - Root endpoint
- `GET /health` - Health check endpoint

## 🔐 Authentication Flow

1. **Registration/Login**: User provides credentials
2. **Token Generation**: JWT access token is created
3. **Token Validation**: Each request validates the token
4. **Permission Check**: User permissions are verified for protected routes
5. **Role-Based Access**: Access granted based on user role and permissions

## 🗄️ Database Schema

### Users Collection
```json
{
  "_id": "ObjectId",
  "email": "user@example.com",
  "name": "User Name",
  "password_hash": "hashed_password",
  "google_id": "google_user_id",
  "avatar": "avatar_url",
  "role_id": "ObjectId",
  "is_active": true,
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Roles Collection
```json
{
  "_id": "ObjectId",
  "name": "Role Name",
  "description": "Role Description",
  "permission_ids": ["ObjectId", "ObjectId"],
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Permissions Collection
```json
{
  "_id": "ObjectId",
  "name": "permission_name",
  "description": "Permission Description",
  "resource": "resource_name",
  "action": "action_name",
  "created_at": "datetime"
}
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_URL` | MongoDB connection string | `mongodb://localhost:27017` |
| `DATABASE_NAME` | Database name | `professorai` |
| `JWT_SECRET_KEY` | JWT signing secret | Required |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration | `30` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `FRONTEND_URL` | Frontend URL for CORS | `http://localhost:3000` |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | Optional |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | Optional |

### Default Roles & Permissions

The system initializes with three default roles:

**Administrator**
- Full system access
- All CRUD operations on users, roles, and permissions
- Dashboard and masters management

**Teacher**
- User and content management
- Dashboard access
- Profile management

**Student** (Default for new users)
- Basic dashboard access
- Content viewing
- Profile management

## 🧪 Testing

Run the development server with auto-reload:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Test API endpoints using the interactive documentation at http://localhost:8000/docs

## 🚀 Deployment

### Production Setup

1. **Set production environment variables**
2. **Use a production ASGI server**:
   ```bash
   pip install gunicorn
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```
3. **Configure reverse proxy** (nginx recommended)
4. **Set up SSL certificates**
5. **Configure MongoDB with authentication**

### Docker Deployment

Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🔍 Monitoring & Logging

- FastAPI provides automatic request/response logging
- Health check endpoint for monitoring
- Error handling with detailed error responses
- CORS configuration for cross-origin requests

## 🤝 Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Write docstrings for all modules and functions
4. Test all endpoints before submitting
5. Update this README for any new features

## 📄 License

This project is part of the ProfessorAI platform and follows the same license terms.
