import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Configure axios to suppress console errors in development
const apiClient = axios.create({
  baseURL: API_URL,
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
  avatar?: string;
  google_id?: string;
}

export interface AuthResponse {
  id: string;
  email: string;
  name: string;
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
      if (userData) {
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
    const response = await apiClient.post<AuthResponse>('/auth/login', {
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
    this.user = { id, email: userEmail, name };

    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', access_token);
      localStorage.setItem('auth_user', JSON.stringify(this.user));
    }

    return this.user;
  }

  async register(name: string, email: string, password: string): Promise<void> {
    const response = await apiClient.post('/auth/register', {
      name,
      email,
      password,
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
  }

  async getCurrentUser(): Promise<User | null> {
    if (!this.token) return null;

    const response = await apiClient.get<User>('/auth/me', {
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
      await apiClient.post('/auth/logout', {}, {
        headers: {
          Authorization: `Bearer ${this.token}`,
        },
      });
    }
    this.clearAuth();
  }

  async getGoogleAuthUrl(): Promise<string> {
    const response = await apiClient.get('/auth/google/login');
    
    // Handle error responses manually
    if (response.status >= 500) {
      throw new Error('Server error. Please try again later');
    } else if (response.status >= 400) {
      throw new Error('Unable to connect to Google. Please try again');
    }
    
    return response.data.authorization_url;
  }

  handleAuthCallback(token: string, userId: string): User {
    this.token = token;
    
    // We'll get the full user data from the token
    // For now, create a basic user object
    this.user = { id: userId, email: '', name: '' };

    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token);
      localStorage.setItem('auth_user', JSON.stringify(this.user));
    }

    // Fetch full user data
    this.getCurrentUser();

    return this.user;
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
