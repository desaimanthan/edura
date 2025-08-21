# Koyeb Deployment Guide for Edura Backend

This guide will walk you through deploying your FastAPI backend to Koyeb.

## Prerequisites

- [x] Koyeb account set up
- [x] MongoDB Atlas database configured
- [x] All environment variables ready
- [x] Production frontend URL available
- [x] GitHub repository with your code

## Deployment Files Created

The following files have been created for your deployment:

1. **`Dockerfile`** - Production-optimized container configuration
2. **`.dockerignore`** - Optimizes build context and reduces image size
3. **`koyeb.yaml`** - Service configuration (optional but recommended)
4. **`main.py`** - Updated with production optimizations

## Step-by-Step Deployment

### 1. Push Code to GitHub

First, ensure all your deployment files are committed and pushed to your GitHub repository:

```bash
git add .
git commit -m "Add Koyeb deployment configuration"
git push origin main
```

### 2. Create Koyeb Service

#### Option A: Using Koyeb Dashboard (Recommended)

1. **Login to Koyeb Dashboard**
   - Go to [https://app.koyeb.com](https://app.koyeb.com)
   - Sign in to your account

2. **Create New Service**
   - Click "Create Service"
   - Choose "GitHub" as the source
   - Connect your GitHub account if not already connected
   - Select your repository: `edura`
   - Set branch to `main` (or your default branch)

3. **Configure Build Settings**
   - **Build method**: Docker
   - **Dockerfile path**: `backend/Dockerfile`
   - **Build context**: `backend/`

4. **Configure Service Settings**
   - **Service name**: `edura-backend`
   - **Region**: Choose closest to your users (e.g., Frankfurt `fra`)
   - **Instance type**: Start with `nano` (can scale up later)
   - **Port**: `8000`
   - **Health check path**: `/health`

#### Option B: Using Koyeb CLI

```bash
# Install Koyeb CLI
curl -fsSL https://cli.koyeb.com/install.sh | sh

# Login
koyeb login

# Deploy from the backend directory
cd backend
koyeb service create edura-backend \
  --git github.com/yourusername/edura \
  --git-branch main \
  --git-build-command "docker build -f backend/Dockerfile backend/" \
  --ports 8000:http \
  --routes /:8000 \
  --health-check-path /health
```

### 3. Configure Environment Variables

In the Koyeb dashboard, go to your service settings and add these environment variables:

#### Required Environment Variables

```env
# Production Environment
ENVIRONMENT=production

# Database Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/database_name
DATABASE_NAME=your_database_name

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# CORS Configuration
FRONTEND_URL=https://your-frontend-domain.com
PRODUCTION_ORIGINS=https://your-frontend-domain.com,https://www.your-frontend-domain.com

# OpenAI Configuration
OPENAI_API_KEY=sk-proj-your-openai-api-key

# Cloudflare R2 Configuration
R2_ACCOUNT_ID=your-r2-account-id
R2_ACCESS_KEY_ID=your-r2-access-key-id
R2_SECRET_ACCESS_KEY=your-r2-secret-access-key
R2_ENDPOINT_URL=https://your-account-id.r2.cloudflarestorage.com
R2_BUCKET_NAME=your-bucket-name
R2_PUBLIC_URL=https://your-public-url.r2.dev

# Server Configuration (Koyeb will set PORT automatically)
HOST=0.0.0.0
```

### 4. Deploy and Monitor

1. **Deploy the Service**
   - Click "Deploy" in the Koyeb dashboard
   - Monitor the build logs for any issues
   - Wait for the service to become "Running"

2. **Verify Deployment**
   - Check the service URL provided by Koyeb
   - Test the health endpoint: `https://your-service-url.koyeb.app/health`
   - Verify the root endpoint: `https://your-service-url.koyeb.app/`

### 5. Configure Custom Domain (Optional)

1. **Add Custom Domain**
   - In Koyeb dashboard, go to your service
   - Click "Domains" tab
   - Add your custom domain (e.g., `api.yourdomain.com`)
   - Update your DNS records as instructed

2. **Update CORS Settings**
   - Update `FRONTEND_URL` and `PRODUCTION_ORIGINS` environment variables
   - Include your custom domain in the allowed origins

## Testing Your Deployment

### Health Check
```bash
curl https://your-service-url.koyeb.app/health
# Expected response: {"status": "healthy"}
```

### API Root
```bash
curl https://your-service-url.koyeb.app/
# Expected response: {"message": "Edura API is running!"}
```

### Authentication Endpoint
```bash
curl -X POST https://your-service-url.koyeb.app/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "name": "Test User", "password": "testpassword"}'
```

## Monitoring and Maintenance

### Viewing Logs
- In Koyeb dashboard, go to your service
- Click "Logs" tab to view real-time logs
- Monitor for errors and performance issues

### Scaling
- Go to service settings in Koyeb dashboard
- Adjust instance type (nano → micro → small → medium)
- Configure auto-scaling rules if needed

### Updates
- Push changes to your GitHub repository
- Koyeb will automatically rebuild and deploy
- Monitor deployment status in the dashboard

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check Dockerfile syntax
   - Verify all dependencies in requirements.txt
   - Check build logs for specific errors

2. **Health Check Failures**
   - Ensure `/health` endpoint is accessible
   - Check if service is binding to correct port
   - Verify environment variables are set correctly

3. **Database Connection Issues**
   - Verify MongoDB URI is correct
   - Check if MongoDB Atlas allows connections from Koyeb IPs
   - Test connection string locally first

4. **CORS Issues**
   - Verify `FRONTEND_URL` is set correctly
   - Check `PRODUCTION_ORIGINS` includes all necessary domains
   - Test with browser developer tools

### Getting Help

- Check Koyeb documentation: [https://www.koyeb.com/docs](https://www.koyeb.com/docs)
- View service logs in Koyeb dashboard
- Check GitHub Actions if using automated deployment

## Security Considerations

1. **Environment Variables**
   - Never commit `.env` files to version control
   - Use strong, unique secrets for production
   - Rotate secrets regularly

2. **Database Security**
   - Use MongoDB Atlas with IP whitelisting
   - Enable authentication and use strong passwords
   - Regular security updates

3. **API Security**
   - HTTPS is enforced by Koyeb
   - JWT tokens have expiration
   - Rate limiting can be added if needed

## Performance Optimization

1. **Instance Sizing**
   - Start with nano instance
   - Monitor CPU and memory usage
   - Scale up as needed

2. **Database Optimization**
   - Use connection pooling (already configured)
   - Add database indexes for frequently queried fields
   - Monitor query performance

3. **Caching**
   - Consider adding Redis for session storage
   - Cache frequently accessed data
   - Use CDN for static assets

## Cost Management

- **Nano instance**: ~$5.50/month
- **Micro instance**: ~$11/month
- **Small instance**: ~$22/month

Monitor usage and scale appropriately to manage costs.

---

Your Edura backend is now ready for production deployment on Koyeb! 🚀
