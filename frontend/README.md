# Edura Frontend

Modern React-based frontend application built with Next.js, providing a comprehensive user interface for the Edura educational platform.

## 🚀 Overview

The frontend application delivers a responsive, accessible, and intuitive user experience for students, teachers, and administrators. Built with Next.js 15 and React 19, it features modern UI components, authentication flows, and role-based interfaces.

## ✨ Features

- **Modern Authentication UI**
  - Email/password login and registration
  - Google OAuth integration
  - Password reset functionality
  - Protected route handling

- **Role-Based Dashboard**
  - Administrator: Full system management
  - Teacher: Course and student management
  - Student: Learning dashboard and course access

- **User Management Interface**
  - User listing and management
  - Role assignment and permissions
  - Profile management

- **Course Management**
  - Course creation and editing
  - Student enrollment tracking
  - Course statistics and analytics

- **Responsive Design**
  - Mobile-first approach
  - Dark/light theme support
  - Accessible UI components
  - Toast notifications

## 🛠️ Technology Stack

- **Framework**: Next.js 15.4.1 with App Router
- **React**: React 19.1.0 with React DOM
- **Styling**: Tailwind CSS 3.4.17 with custom configuration
- **UI Components**: 
  - Radix UI primitives for accessibility
  - Custom component library
  - Lucide React icons
- **Forms**: React Hook Form 7.60.0 with Zod validation
- **HTTP Client**: Axios 1.10.0
- **State Management**: React Context API
- **Animations**: Tailwind CSS animations
- **Theme**: Next Themes for dark/light mode

## 📦 Dependencies

### Production Dependencies
```json
{
  "@hookform/resolvers": "^5.1.1",
  "@radix-ui/react-avatar": "^1.1.10",
  "@radix-ui/react-checkbox": "^1.3.2",
  "@radix-ui/react-dialog": "^1.1.14",
  "@radix-ui/react-form": "^0.1.7",
  "@radix-ui/react-label": "^2.1.7",
  "@radix-ui/react-popover": "^1.1.14",
  "@radix-ui/react-slot": "^1.2.3",
  "axios": "^1.10.0",
  "class-variance-authority": "^0.7.1",
  "clsx": "^2.1.1",
  "cmdk": "^1.1.1",
  "lucide-react": "^0.525.0",
  "next": "15.4.1",
  "next-themes": "^0.4.6",
  "react": "19.1.0",
  "react-dom": "19.1.0",
  "react-hook-form": "^7.60.0",
  "sonner": "^2.0.6",
  "tailwind-merge": "^3.3.1",
  "tailwindcss": "^3.4.17",
  "tailwindcss-animate": "^1.0.7",
  "zod": "^4.0.5"
}
```

## 🚦 Getting Started

### Prerequisites
- Node.js 18 or higher
- npm or yarn package manager
- Backend API running (see backend/README.md)

### Installation

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Environment Configuration**
   Create a `.env.local` file in the frontend directory:
   ```env
   # API Configuration
   NEXT_PUBLIC_API_URL=http://localhost:8000
   
   # Google OAuth (Optional - must match backend config)
   NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id
   
   # App Configuration
   NEXT_PUBLIC_APP_NAME=Edura
   NEXT_PUBLIC_APP_URL=http://localhost:3000
   ```

4. **Start development server**
   ```bash
   npm run dev
   # or
   yarn dev
   ```

5. **Access the application**
   Open http://localhost:3000 in your browser

## 📁 Project Structure

```
frontend/
├── public/                 # Static assets
│   ├── next.svg
│   ├── vercel.svg
│   └── ...
├── src/
│   ├── app/               # Next.js App Router pages
│   │   ├── layout.tsx     # Root layout
│   │   ├── page.tsx       # Home page
│   │   ├── globals.css    # Global styles
│   │   ├── auth/          # Authentication pages
│   │   │   ├── signin/
│   │   │   ├── signup/
│   │   │   └── callback/
│   │   ├── dashboard/     # Dashboard page
│   │   ├── courses/       # Course management
│   │   └── masters/       # Admin management
│   │       ├── users/
│   │       ├── roles/
│   │       └── permissions/
│   ├── components/        # Reusable components
│   │   ├── layout/        # Layout components
│   │   ├── providers/     # Context providers
│   │   └── ui/           # UI component library
│   └── lib/              # Utility functions
│       ├── auth.ts       # Authentication utilities
│       └── utils.ts      # General utilities
├── package.json
├── tailwind.config.ts    # Tailwind configuration
├── tsconfig.json        # TypeScript configuration
└── next.config.ts       # Next.js configuration
```

## 🎨 UI Components

The application uses a custom component library built on top of Radix UI primitives:

### Core Components
- **Button**: Various button styles and sizes
- **Card**: Content containers with headers and footers
- **Dialog**: Modal dialogs and overlays
- **Form**: Form components with validation
- **Input**: Text inputs with validation states
- **Table**: Data tables with sorting and pagination
- **Avatar**: User profile pictures
- **Badge**: Status indicators and labels

### Layout Components
- **DashboardLayout**: Main application layout with sidebar
- **PageHeader**: Consistent page headers
- **Sidebar**: Navigation sidebar with role-based menu items

### Specialized Components
- **AuthProvider**: Authentication context provider
- **Combobox**: Searchable select components
- **Command**: Command palette interface

## 🔐 Authentication Flow

1. **Login/Register**: User accesses auth pages
2. **API Communication**: Credentials sent to backend
3. **Token Storage**: JWT tokens stored securely
4. **Route Protection**: Protected routes check authentication
5. **Role-Based Access**: UI adapts based on user role
6. **Auto-Refresh**: Tokens refreshed automatically

## 📱 Pages & Routes

### Public Routes
- `/` - Landing page
- `/auth/signin` - User login
- `/auth/signup` - User registration
- `/auth/callback` - OAuth callback

### Protected Routes
- `/dashboard` - Main dashboard (all roles)
- `/courses` - Course management (Teacher, Admin)
- `/masters` - System administration (Admin only)
  - `/masters/users` - User management
  - `/masters/roles` - Role management
  - `/masters/permissions` - Permission management

## 🎯 Role-Based Features

### Student Dashboard
- Course enrollment and progress
- Assignment submissions
- Grade viewing
- Profile management

### Teacher Dashboard
- Course creation and management
- Student enrollment management
- Content creation tools
- Grade management

### Administrator Dashboard
- Full user management
- Role and permission management
- System configuration
- Analytics and reporting

## 🎨 Styling & Theming

### Tailwind CSS Configuration
- Custom color palette
- Responsive breakpoints
- Animation utilities
- Component variants

### Theme Support
- Light/dark mode toggle
- System preference detection
- Persistent theme selection
- Smooth transitions

### Design System
- Consistent spacing scale
- Typography hierarchy
- Color semantics
- Accessibility compliance

## 📱 Responsive Design

- **Mobile First**: Optimized for mobile devices
- **Breakpoints**: 
  - `sm`: 640px and up
  - `md`: 768px and up
  - `lg`: 1024px and up
  - `xl`: 1280px and up
- **Flexible Layouts**: Grid and flexbox layouts
- **Touch Friendly**: Appropriate touch targets

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | Google OAuth client ID | Optional |
| `NEXT_PUBLIC_APP_NAME` | Application name | `Edura` |
| `NEXT_PUBLIC_APP_URL` | Frontend URL | `http://localhost:3000` |

### Next.js Configuration
- TypeScript support enabled
- ESLint configuration
- Tailwind CSS integration
- Optimized builds

## 🧪 Development

### Available Scripts
```bash
npm run dev      # Start development server
npm run build    # Build for production
npm run start    # Start production server
npm run lint     # Run ESLint
```

### Development Server
- Hot reload enabled
- Error overlay
- Fast refresh
- TypeScript checking

### Code Quality
- ESLint configuration
- TypeScript strict mode
- Prettier formatting (recommended)
- Component prop validation

## 🚀 Build & Deployment

### Production Build
```bash
npm run build
npm run start
```

### Static Export (Optional)
```bash
# Add to next.config.ts
output: 'export'
```

### Deployment Options
- **Vercel**: Optimized for Next.js
- **Netlify**: Static site hosting
- **Docker**: Containerized deployment
- **Traditional Hosting**: Static file serving

### Performance Optimization
- Automatic code splitting
- Image optimization
- Font optimization
- Bundle analysis

## 🔍 Monitoring & Analytics

- Built-in Next.js analytics
- Error boundary implementation
- Performance monitoring ready
- User interaction tracking ready

## 🧪 Testing (Recommended Setup)

```bash
# Install testing dependencies
npm install --save-dev @testing-library/react @testing-library/jest-dom jest jest-environment-jsdom

# Add test scripts to package.json
"test": "jest",
"test:watch": "jest --watch"
```

## 🤝 Contributing

1. Follow React and Next.js best practices
2. Use TypeScript for all components
3. Implement responsive design
4. Add proper accessibility attributes
5. Test across different devices and browsers
6. Update component documentation

### Component Development Guidelines
- Use functional components with hooks
- Implement proper TypeScript interfaces
- Follow naming conventions
- Add JSDoc comments
- Handle loading and error states

## 📄 License

This project is part of the Edura platform and follows the same license terms.

## 🔗 Related Documentation

- [Backend API Documentation](../backend/README.md)
- [Project Overview](../README.md)
- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Radix UI Documentation](https://www.radix-ui.com/docs)
