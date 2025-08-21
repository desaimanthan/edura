import axios from 'axios';
import { API_BASE_URL, API_ENDPOINTS, logApiCall } from './api-config';

// Configure axios to suppress console errors in development
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  // Suppress axios console errors
  validateStatus: function (status) {
    // Don't throw errors for any status code - we'll handle them manually
    return status < 600;
  }
});

// Add response interceptor to suppress console logging
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Suppress error logging completely and return the error response
    return Promise.resolve(error.response || error);
  }
);

export interface User {
  id: string;
  email: string;
  name: string;
  is_active: boolean;
  role_id?: string;
  role_name?: string;
  google_id?: string;
  avatar?: string;
  approval_status?: string;
  requested_role_name?: string;
  approved_by?: string;
  approved_at?: string;
  approval_reason?: string;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  id: string;
  email: string;
  name: string;
  role_name?: string;
  access_token: string;
  token_type: string;
}

class AuthService {
  private token: string | null = null;
  private user: User | null = null;

  constructor() {
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('auth_token');
      const userData = localStorage.getItem('auth_user');
      if (userData && userData !== 'undefined' && userData !== 'null') {
        try {
          this.user = JSON.parse(userData);
        } catch (error) {
          console.error('Error parsing user data:', error);
          this.clearAuth();
        }
      }
    }
  }

  async login(email: string, password: string): Promise<User> {
    logApiCall('POST', API_ENDPOINTS.AUTH.LOGIN, { email });
    const response = await apiClient.post<AuthResponse>(API_ENDPOINTS.AUTH.LOGIN, {
      email,
      password,
    });

    // Handle error responses manually
    if (response.status === 401) {
      throw new Error('Invalid email or password');
    } else if (response.status === 400) {
      throw new Error('Please check your email and password');
    } else if (response.status >= 500) {
      throw new Error('Server error. Please try again later');
    } else if (response.status >= 400) {
      throw new Error('Login failed. Please try again');
    }

    const { access_token, id, email: userEmail, name } = response.data;
    
    this.token = access_token;

    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', access_token);
    }

    // Fetch full user data after login
    const user = await this.getCurrentUser();
    if (!user) {
      throw new Error('Failed to fetch user data after login');
    }

    return user;
  }

  async register(name: string, email: string, password: string, role?: string): Promise<{ requiresApproval: boolean; message: string }> {
    const requestData = {
      name,
      email,
      password,
      intended_role_name: role || 'Student',
    };
    
    console.log('🔍 Auth Service Debug - Register Request:', requestData);
    logApiCall('POST', API_ENDPOINTS.AUTH.REGISTER, requestData);
    
    const response = await apiClient.post(API_ENDPOINTS.AUTH.REGISTER, requestData);
    
    console.log('🔍 Auth Service Debug - Register Response:', {
      status: response.status,
      data: response.data
    });

    // Handle error responses manually
    if (response.status === 400) {
      const detail = response.data?.detail;
      if (detail === 'Email already registered') {
        throw new Error('An account with this email already exists');
      }
      throw new Error(detail || 'Please check your information and try again');
    } else if (response.status >= 500) {
      throw new Error('Server error. Please try again later');
    } else if (response.status >= 400) {
      throw new Error('Registration failed. Please try again');
    }

    // Return the response data which includes approval status
    return {
      requiresApproval: response.data?.requires_approval || false,
      message: response.data?.message || 'Account created successfully'
    };
  }

  async getCurrentUser(): Promise<User | null> {
    if (!this.token) return null;

    logApiCall('GET', API_ENDPOINTS.AUTH.ME);
    const response = await apiClient.get<User>(API_ENDPOINTS.AUTH.ME, {
      headers: {
        Authorization: `Bearer ${this.token}`,
      },
    });

    // Handle error responses - if unauthorized, clear auth
    if (response.status >= 400) {
      this.clearAuth();
      return null;
    }

    this.user = response.data;
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_user', JSON.stringify(this.user));
    }

    return this.user;
  }

  async logout(): Promise<void> {
    if (this.token) {
      logApiCall('POST', API_ENDPOINTS.AUTH.LOGOUT);
      await apiClient.post(API_ENDPOINTS.AUTH.LOGOUT, {}, {
        headers: {
          Authorization: `Bearer ${this.token}`,
        },
      });
    }
    this.clearAuth();
  }

  async getGoogleAuthUrl(role?: string): Promise<string> {
    const params = role ? `?role=${encodeURIComponent(role)}` : '';
    const endpoint = `${API_ENDPOINTS.AUTH.GOOGLE_LOGIN}${params}`;
    
    logApiCall('GET', endpoint);
    const response = await apiClient.get(endpoint);
    
    // Handle error responses manually
    if (response.status >= 500) {
      throw new Error('Server error. Please try again later');
    } else if (response.status >= 400) {
      throw new Error('Unable to connect to Google. Please try again');
    }
    
    return response.data.authorization_url;
  }

  async handleAuthCallback(token: string, userId: string): Promise<User> {
    this.token = token;
    
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token);
    }

    // Fetch full user data before returning
    const user = await this.getCurrentUser();
    if (!user) {
      throw new Error('Failed to fetch user data');
    }

    // Dispatch custom event to notify components of user data update
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('auth-user-updated', { detail: user }));
    }

    return user;
  }

  private clearAuth(): void {
    this.token = null;
    this.user = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
    }
  }

  getToken(): string | null {
    return this.token;
  }

  getUser(): User | null {
    return this.user;
  }

  isAuthenticated(): boolean {
    return !!this.token && !!this.user;
  }
}

export const authService = new AuthService();
