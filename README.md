# Edura

A full-stack educational platform with comprehensive authentication, role-based access control, and course management capabilities.

## 🚀 Overview

Edura is a modern educational platform built with Next.js frontend and FastAPI backend, designed to facilitate online learning with robust user management and course administration features.

## 🏗️ Architecture

```
Edura/
├── frontend/          # Next.js React application
├── backend/           # FastAPI Python application
└── README.md         # This file
```

## ✨ Key Features

- **Authentication System**
  - Email/password authentication
  - Google OAuth integration
  - JWT token-based sessions
  - Password reset functionality

- **Role-Based Access Control (RBAC)**
  - Three default roles: Administrator, Teacher, Student
  - Granular permission system
  - Resource-based access control

- **User Management**
  - User registration and profile management
  - Role assignment and management
  - Permission management interface

- **Course Management**
  - Course creation and management
  - Student enrollment tracking
  - Course statistics and analytics

- **Modern UI/UX**
  - Responsive design with Tailwind CSS
  - Component-based architecture with Radix UI
  - Dark/light theme support
  - Toast notifications

## 🛠️ Technology Stack

### Frontend
- **Framework**: Next.js 15.4.1 with React 19
- **Styling**: Tailwind CSS with custom components
- **UI Components**: Radix UI primitives
- **Forms**: React Hook Form with Zod validation
- **HTTP Client**: Axios
- **Icons**: Lucide React

### Backend
- **Framework**: FastAPI 0.104.1
- **Database**: MongoDB with Motor (async driver)
- **Authentication**: JWT with Google OAuth
- **Password Hashing**: Passlib with bcrypt
- **Validation**: Pydantic models
- **CORS**: FastAPI CORS middleware

## 🚦 Getting Started

### Prerequisites
- Node.js 18+ and npm
- Python 3.8+
- MongoDB database
- Google OAuth credentials (optional)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/desaimanthan/professorAI.git
   cd professorAI
   ```

2. **Set up the backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   # Configure environment variables (see backend/README.md)
   python seed_data.py  # Initialize database with default roles
   python main.py       # Start the API server
   ```

3. **Set up the frontend**
   ```bash
   cd frontend
   npm install
   npm run dev         # Start the development server
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 📁 Project Structure

```
Edura/
├── backend/           # FastAPI Python application
├── frontend/          # Next.js React application
├── docs/              # Documentation and development notes
├── tests/             # Test files
├── scripts/           # Utility and migration scripts
└── README.md         # This file
```

### Backend (`/backend`)
- `main.py` - FastAPI application entry point
- `app/models.py` - Pydantic data models
- `app/database.py` - MongoDB connection and utilities
- `app/auth.py` - Authentication utilities
- `app/routes/` - API route handlers
- `seed_data.py` - Database initialization script

### Frontend (`/frontend`)
- `src/app/` - Next.js app router pages
- `src/components/` - Reusable React components
- `src/lib/` - Utility functions and configurations
- `public/` - Static assets

### Documentation (`/docs`)
- Agent development guides and summaries
- Implementation documentation
- Architecture and planning documents
- Feature implementation notes

### Tests (`/tests`)
- Unit and integration tests
- Agent functionality tests
- Feature-specific test files

### Scripts (`/scripts`)
- Database migration scripts
- Utility scripts for maintenance
- Data transformation tools

## 🔐 Default Roles & Permissions

The system comes with three pre-configured roles:

- **Administrator**: Full system access with all permissions
- **Teacher**: Access to teaching materials and student management
- **Student**: Basic access to learning materials (default for new users)

## 🌐 API Endpoints

- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/google` - Google OAuth login
- `GET /users` - List users (admin only)
- `GET /masters/roles` - Manage roles
- `GET /masters/permissions` - Manage permissions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the documentation in each component's README file

## 🔗 Links

- [Frontend Documentation](./frontend/README.md)
- [Backend Documentation](./backend/README.md)
- [API Documentation](http://localhost:8000/docs) (when running)
