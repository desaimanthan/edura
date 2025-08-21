# Frontend-Backend Connection Configuration Summary

This document summarizes all the changes made to configure your frontend (Vercel) to connect to your backend (Koyeb) with environment-based URL switching.

## 🎯 Problem Solved

**Before:** Frontend had hardcoded `http://localhost:8000` URLs that only worked in development.

**After:** Frontend uses environment variables to automatically connect to:
- `http://localhost:8000` in development
- `https://your-koyeb-backend.koyeb.app` in production

## 📁 Files Created/Modified

### 1. **New Files Created**

#### `frontend/src/lib/api-config.ts`
- Centralized API configuration system
- Environment-based URL management
- Standardized endpoint definitions
- Debug logging for development

#### `frontend/.env.local`
- Local development environment variables
- Sets `NEXT_PUBLIC_API_URL=http://localhost:8000`

#### `frontend/VERCEL_DEPLOYMENT_GUIDE.md`
- Complete deployment instructions
- Troubleshooting guide
- Testing procedures

#### `FRONTEND_BACKEND_CONNECTION_SUMMARY.md` (this file)
- Overview of all changes made

### 2. **Files Modified**

#### `frontend/src/lib/auth.ts`
- Updated to use centralized API configuration
- All authentication endpoints now use environment variables
- Added debug logging for development

#### `frontend/src/app/courses/create/components/chat-interface.tsx`
- Replaced all hardcoded URLs with environment-based URLs
- Updated all API calls to use the new configuration system
- Added proper logging for debugging

## 🔧 How It Works

### Development Environment
```typescript
// Uses frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000

// All API calls automatically use localhost
const response = await fetch(getApiUrl('/auth/login'), { ... });
// → http://localhost:8000/auth/login
```

### Production Environment (Vercel)
```typescript
// Uses Vercel environment variables
NEXT_PUBLIC_API_URL=https://your-backend.koyeb.app

// All API calls automatically use Koyeb backend
const response = await fetch(getApiUrl('/auth/login'), { ... });
// → https://your-backend.koyeb.app/auth/login
```

## 🚀 Next Steps for You

### Step 1: Get Your Koyeb Backend URL
From your Koyeb dashboard, copy your backend service URL. It should look like:
```
https://your-service-name-your-org.koyeb.app
```

### Step 2: Update Koyeb Backend CORS
In your Koyeb service environment variables, add:
```env
FRONTEND_URL=https://your-vercel-app.vercel.app
PRODUCTION_ORIGINS=https://your-vercel-app.vercel.app
```

### Step 3: Configure Vercel Environment Variable
In your Vercel project dashboard:
1. Go to Settings → Environment Variables
2. Add: `NEXT_PUBLIC_API_URL` = `https://your-koyeb-backend-url.koyeb.app`

### Step 4: Deploy and Test
```bash
# Commit the changes
git add .
git commit -m "Configure frontend for production backend connection"
git push origin main

# Vercel will automatically deploy
```

## 🧪 Testing Your Setup

### Local Development Test
```bash
# Terminal 1: Start backend
cd backend
python main.py

# Terminal 2: Start frontend  
cd frontend
npm run dev

# Visit http://localhost:3000
# Check browser dev tools → Network tab
# API calls should go to http://localhost:8000
```

### Production Test
```bash
# After deploying to Vercel
# Visit your Vercel app URL
# Check browser dev tools → Network tab  
# API calls should go to https://your-koyeb-backend.koyeb.app
```

## 📊 Benefits of This Configuration

### 1. **Environment Flexibility**
- Automatically works in development and production
- No manual URL changes needed
- Easy to switch between different backend environments

### 2. **Maintainability**
- Centralized API configuration
- Single place to update endpoints
- Consistent error handling

### 3. **Developer Experience**
- Debug logging in development
- Clear error messages
- Easy troubleshooting

### 4. **Security**
- CORS properly configured
- Environment variables managed securely
- No hardcoded sensitive URLs

## 🔍 Key Configuration Points

### API Base URL Resolution
```typescript
// Priority order:
// 1. NEXT_PUBLIC_API_URL environment variable
// 2. Fallback to http://localhost:8000
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
```

### Endpoint Management
```typescript
// Centralized endpoint definitions
export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    // ...
  },
  COURSES: {
    CHAT: (courseId: string) => `/courses/${courseId}/chat`,
    // ...
  }
};
```

### Debug Logging
```typescript
// Only logs in development
export const logApiCall = (method: string, url: string, data?: any) => {
  if (isDevelopment) {
    console.log(`🌐 API ${method.toUpperCase()}: ${url}`, data ? { data } : '');
  }
};
```

## 🚨 Important Notes

### Environment Variables
- Must start with `NEXT_PUBLIC_` to be available in the browser
- Set in Vercel dashboard, not in code files
- Require redeployment to take effect

### CORS Configuration
- Backend must allow requests from your Vercel domain
- Update both `FRONTEND_URL` and `PRODUCTION_ORIGINS` in Koyeb
- Test CORS with browser developer tools

### Caching
- Clear browser cache when testing
- Vercel may cache environment variables
- Force refresh (Ctrl+F5) when testing changes

## 🎉 Result

Your frontend now seamlessly works in both environments:

- **Development**: `localhost:3000` → `localhost:8000`
- **Production**: `your-app.vercel.app` → `your-backend.koyeb.app`

No more manual URL changes or environment-specific code! 🚀

## 📞 Troubleshooting Quick Reference

| Issue | Solution |
|-------|----------|
| CORS errors | Update Koyeb CORS settings |
| Still using localhost in prod | Check Vercel env vars & redeploy |
| API calls failing | Verify Koyeb backend is running |
| Environment variable not working | Ensure `NEXT_PUBLIC_` prefix |
| Network errors | Check browser dev tools Network tab |

Your frontend is now production-ready and will automatically connect to the correct backend based on the environment! 🎯
