# Frontend Deployment Guide - Connecting to Koyeb Backend

This guide explains how to configure your Next.js frontend (deployed on Vercel) to connect to your Koyeb backend.

## 🔧 Configuration Changes Made

### 1. **API Configuration System**
- Created `src/lib/api-config.ts` - Centralized API configuration
- Updated `src/lib/auth.ts` - Uses new API configuration
- Updated `src/app/courses/create/components/chat-interface.tsx` - All API calls now use environment-based URLs

### 2. **Environment Variable Setup**
- Created `frontend/.env.local` for local development
- All API calls now use `NEXT_PUBLIC_API_URL` environment variable

## 🚀 Deployment Steps

### Step 1: Update Backend CORS Settings

First, ensure your Koyeb backend allows requests from your Vercel frontend domain.

In your Koyeb dashboard, set these environment variables:

```env
FRONTEND_URL=https://your-vercel-app.vercel.app
PRODUCTION_ORIGINS=https://your-vercel-app.vercel.app,https://your-custom-domain.com
```

### Step 2: Configure Vercel Environment Variables

In your Vercel dashboard:

1. **Go to your project settings**
2. **Navigate to "Environment Variables"**
3. **Add the following variable:**

```env
NEXT_PUBLIC_API_URL=https://your-koyeb-backend-url.koyeb.app
```

**Important:** Replace `your-koyeb-backend-url.koyeb.app` with your actual Koyeb backend URL.

### Step 3: Deploy to Vercel

```bash
# Commit your changes
git add .
git commit -m "Configure frontend for Koyeb backend connection"
git push origin main

# Vercel will automatically deploy
```

## 🔍 How It Works

### Local Development
- Uses `frontend/.env.local`
- `NEXT_PUBLIC_API_URL=http://localhost:8000`
- Connects to your local backend

### Production (Vercel)
- Uses Vercel environment variables
- `NEXT_PUBLIC_API_URL=https://your-koyeb-backend-url.koyeb.app`
- Connects to your Koyeb backend

### API Configuration Flow

```typescript
// src/lib/api-config.ts
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// All API calls use this centralized configuration
const response = await fetch(getApiUrl(API_ENDPOINTS.AUTH.LOGIN), {
  method: 'POST',
  headers: { /* ... */ },
  body: JSON.stringify(data)
});
```

## 📋 Environment Variables Reference

### Local Development (`.env.local`)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NODE_ENV=development
```

### Production (Vercel Dashboard)
```env
NEXT_PUBLIC_API_URL=https://your-koyeb-backend-url.koyeb.app
```

## 🧪 Testing Your Configuration

### 1. **Local Testing**
```bash
# Start your local backend
cd backend
python main.py

# Start your frontend
cd frontend
npm run dev

# Test at http://localhost:3000
```

### 2. **Production Testing**
After deploying to Vercel:

1. **Open your Vercel app URL**
2. **Open browser developer tools**
3. **Check Network tab for API calls**
4. **Verify requests go to your Koyeb backend URL**

### 3. **Debug API Calls**
The configuration includes debug logging in development:

```typescript
// Only logs in development
logApiCall('POST', '/auth/login', { email: 'user@example.com' });
// Output: 🌐 API POST: https://your-backend.koyeb.app/auth/login
```

## 🔧 Troubleshooting

### Issue: CORS Errors
**Solution:** Update your Koyeb backend CORS settings:

```env
# In Koyeb dashboard
FRONTEND_URL=https://your-vercel-app.vercel.app
PRODUCTION_ORIGINS=https://your-vercel-app.vercel.app
```

### Issue: API Calls Still Going to Localhost
**Solutions:**
1. Check Vercel environment variables are set correctly
2. Redeploy your Vercel app after setting environment variables
3. Clear browser cache

### Issue: Environment Variable Not Working
**Check:**
1. Variable name starts with `NEXT_PUBLIC_`
2. Variable is set in Vercel dashboard (not in code)
3. Vercel app has been redeployed after setting variables

## 📱 Mobile/Device Testing

Your app will work on all devices since:
- Environment variables are resolved at build time
- All API calls use the centralized configuration
- CORS is properly configured for your domain

## 🔒 Security Notes

1. **Environment Variables:**
   - `NEXT_PUBLIC_*` variables are exposed to the browser
   - Only put non-sensitive configuration in these variables
   - Backend URL is safe to expose

2. **CORS Configuration:**
   - Backend only allows requests from your specified domains
   - Prevents unauthorized access from other websites

## 📊 Monitoring

### Check API Calls
In production, you can monitor API calls:

1. **Browser Developer Tools** → Network tab
2. **Vercel Analytics** (if enabled)
3. **Koyeb Logs** for backend monitoring

### Performance
- API calls are optimized with proper error handling
- Debug logging is disabled in production
- Centralized configuration reduces bundle size

## 🚀 Next Steps

1. **Deploy your frontend to Vercel**
2. **Set the environment variable in Vercel dashboard**
3. **Update your Koyeb backend CORS settings**
4. **Test the connection**
5. **Monitor for any issues**

Your frontend will now seamlessly connect to your Koyeb backend in production while still working with localhost during development! 🎉

## 📞 Support

If you encounter issues:
1. Check Vercel deployment logs
2. Check Koyeb backend logs
3. Verify environment variables are set correctly
4. Test API endpoints directly with curl/Postman
