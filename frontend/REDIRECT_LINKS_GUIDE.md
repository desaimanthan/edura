# Redirect Links Guide

## Overview
This application supports URL redirects that can be easily configured without modifying route handlers.

## Current Redirects

### Direct Route: `/video-demo`
- **Current Target**: https://www.youtube.com/watch?v=R363pqsI3Vs&feature=youtu.be
- **Access via**: http://yourdomain.com/video-demo

### Dynamic Routes: `/r/[slug]`
- **Access via**: http://yourdomain.com/r/video-demo
- This pattern allows multiple redirects using the same route handler

## How to Change Redirect Links

1. Open the file: `frontend/src/config/redirects.ts`
2. Find the redirect you want to change
3. Update the URL in the `redirectLinks` object
4. Save the file - changes will take effect after the next build/deployment

### Example:
```typescript
export const redirectLinks = {
  // Change this URL to update where /video-demo redirects to
  'video-demo': 'https://www.youtube.com/watch?v=NEW_VIDEO_ID',
  
  // Add new redirects here
  'documentation': 'https://docs.example.com',
  'support': 'https://support.example.com',
};
```

## Adding New Redirects

### Method 1: Create a dedicated route
1. Create a new folder in `frontend/src/app/` with your desired path name
2. Add a `route.ts` file similar to the video-demo example
3. Update the redirect URL in `redirects.ts`

### Method 2: Use the dynamic route (Recommended)
1. Simply add a new entry to the `redirectLinks` object in `redirects.ts`
2. Access it via `/r/your-new-slug`

Example:
```typescript
export const redirectLinks = {
  'video-demo': 'https://www.youtube.com/watch?v=R363pqsI3Vs',
  'github': 'https://github.com/yourrepo',  // New redirect
  'discord': 'https://discord.gg/yourinvite', // New redirect
};
```

Now you can access:
- `/r/github` → redirects to your GitHub repo
- `/r/discord` → redirects to your Discord server

## Testing Locally

1. Start the development server:
   ```bash
   cd frontend
   npm run dev
   ```

2. Visit the redirect URLs:
   - http://localhost:3000/video-demo
   - http://localhost:3000/r/video-demo

## Notes

- Redirects are performed server-side for better SEO and performance
- Invalid redirect slugs will return a 404 error
- The redirect configuration is loaded at build time, so changes require a rebuild in production
- For development, changes are reflected immediately with hot reload
