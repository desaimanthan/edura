/**
 * API Configuration
 * Centralized configuration for API endpoints that works in both development and production
 */

// Get the API base URL from environment variables
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * API endpoint builder
 * Creates full API URLs by combining base URL with endpoint paths
 */
export const apiEndpoint = (path: string): string => {
  // Ensure path starts with /
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
};

/**
 * Common API endpoints
 * Centralized endpoint definitions for consistency
 */
export const API_ENDPOINTS = {
  // Authentication
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    ME: '/auth/me',
    LOGOUT: '/auth/logout',
    GOOGLE_LOGIN: '/auth/google/login',
  },
  
  // Courses
  COURSES: {
    LIST: '/courses',
    CREATE_DRAFT: '/courses/create-draft',
    DETAIL: (courseId: string) => `/courses/${courseId}`,
    MESSAGES: (courseId: string) => `/courses/${courseId}/messages`,
    CHAT: (courseId: string) => `/courses/${courseId}/chat`,
    CHAT_MATERIAL_CONTENT: (courseId: string) => `/courses/${courseId}/chat-material-content`,
    UPLOAD_CURRICULUM: (courseId: string) => `/courses/${courseId}/upload-curriculum`,
    GENERATE_RESEARCH: (courseId: string) => `/courses/${courseId}/generate-research`,
    GENERATE_CONTENT_STRUCTURE: (courseId: string) => `/courses/${courseId}/generate-content-structure`,
    GENERATE_MATERIAL_CONTENT: (courseId: string) => `/courses/${courseId}/generate-material-content`,
  },
  
  // General
  CHAT: '/courses/chat',
} as const;

/**
 * Get full API URL for an endpoint
 */
export const getApiUrl = (endpoint: string): string => {
  return apiEndpoint(endpoint);
};

/**
 * Environment information
 */
export const isProduction = process.env.NODE_ENV === 'production';
export const isDevelopment = process.env.NODE_ENV === 'development';

/**
 * Debug logging for API calls (only in development)
 */
export const logApiCall = (method: string, url: string, data?: any) => {
  if (isDevelopment) {
    console.log(`🌐 API ${method.toUpperCase()}: ${url}`, data ? { data } : '');
  }
};
