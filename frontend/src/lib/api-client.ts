/**
 * Centralized API Client for Course Creation
 * 
 * This module handles all API communication with the backend,
 * including REST calls and Server-Sent Events (SSE) streaming.
 */

import { StreamEventParser } from '@/utils/StreamEventParser';

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  status: number;
}

export interface StreamEvent {
  type: string;
  source: string;
  timestamp: string;
  sequence: number;
  priority: string;
  payload: any;
}

export interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: string;
  course_id?: string;
}

export interface Course {
  _id: string;
  name: string;
  description: string;
  status: string;
  workflow_step: string;
  created_at: string;
  updated_at: string;
}

export interface WorkflowStatus {
  exists: boolean;
  current_step: string | null;
  previous_step?: string;
  completed_steps: string[];
  context: Record<string, any>;
  available_actions: string[];
}

class ApiClient {
  private baseUrl: string;
  private eventSource: EventSource | null = null;

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }

  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('auth_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
    };
  }

  private async handleResponse<T>(response: Response): Promise<ApiResponse<T>> {
    const status = response.status;
    
    try {
      if (response.headers.get('content-type')?.includes('application/json')) {
        const data = await response.json();
        
        if (response.ok) {
          return { success: true, data, status };
        } else {
          return { 
            success: false, 
            error: data.detail || data.message || 'Request failed', 
            status 
          };
        }
      } else {
        const text = await response.text();
        if (response.ok) {
          return { success: true, data: text as T, status };
        } else {
          return { success: false, error: text || 'Request failed', status };
        }
      }
    } catch (error) {
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Failed to parse response', 
        status 
      };
    }
  }

  // Course Management
  async createDraftCourse(): Promise<ApiResponse<{ course_id: string }>> {
    const response = await fetch(`${this.baseUrl}/courses/create-draft`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    });

    return this.handleResponse(response);
  }

  async getCourse(courseId: string): Promise<ApiResponse<Course>> {
    const response = await fetch(`${this.baseUrl}/courses/${courseId}`, {
      headers: this.getAuthHeaders(),
    });

    return this.handleResponse(response);
  }

  async getUserCourses(): Promise<ApiResponse<Course[]>> {
    const response = await fetch(`${this.baseUrl}/courses/`, {
      headers: this.getAuthHeaders(),
    });

    return this.handleResponse(response);
  }

  async updateCourse(courseId: string, data: Partial<Course>): Promise<ApiResponse<Course>> {
    const response = await fetch(`${this.baseUrl}/courses/${courseId}`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(data),
    });

    return this.handleResponse(response);
  }

  async deleteCourse(courseId: string): Promise<ApiResponse<{ message: string }>> {
    const response = await fetch(`${this.baseUrl}/courses/${courseId}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
    });

    return this.handleResponse(response);
  }

  // Chat and Messaging
  async sendMessage(
    courseId: string | null, 
    content: string,
    contextHints?: Record<string, any>
  ): Promise<ApiResponse<any>> {
    const url = courseId 
      ? `${this.baseUrl}/courses/${courseId}/chat`
      : `${this.baseUrl}/courses/chat`;

    const body: any = { content };
    if (contextHints) {
      body.context_hints = contextHints;
    }

    const response = await fetch(url, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(body),
    });

    return this.handleResponse(response);
  }

  async getCourseMessages(courseId: string): Promise<ApiResponse<ChatMessage[]>> {
    const response = await fetch(`${this.baseUrl}/courses/${courseId}/messages`, {
      headers: this.getAuthHeaders(),
    });

    return this.handleResponse(response);
  }

  // Workflow Management
  async getWorkflowStatus(courseId: string): Promise<ApiResponse<WorkflowStatus>> {
    const response = await fetch(`${this.baseUrl}/courses/${courseId}/workflow-status`, {
      headers: this.getAuthHeaders(),
    });

    return this.handleResponse(response);
  }

  async restoreWorkflowContext(courseId: string): Promise<ApiResponse<any>> {
    const response = await fetch(`${this.baseUrl}/courses/${courseId}/restore-workflow`, {
      headers: this.getAuthHeaders(),
    });

    return this.handleResponse(response);
  }

  // File Operations
  async saveFile(
    courseId: string, 
    fileName: string, 
    content: string, 
    fileType: string = 'markdown'
  ): Promise<ApiResponse<any>> {
    const response = await fetch(`${this.baseUrl}/courses/${courseId}/save-file`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({
        file_name: fileName,
        content,
        file_type: fileType,
      }),
    });

    return this.handleResponse(response);
  }

  async uploadFile(courseId: string, file: File): Promise<ApiResponse<any>> {
    const token = localStorage.getItem('auth_token');
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/courses/${courseId}/upload-curriculum`, {
      method: 'POST',
      headers: {
        ...(token && { 'Authorization': `Bearer ${token}` }),
      },
      body: formData,
    });

    return this.handleResponse(response);
  }

  // Content Management
  async getContentProgress(courseId: string): Promise<ApiResponse<any>> {
    const response = await fetch(`${this.baseUrl}/courses/${courseId}/content-progress`, {
      headers: this.getAuthHeaders(),
    });

    return this.handleResponse(response);
  }

  async getContentMaterials(courseId: string): Promise<ApiResponse<any>> {
    const response = await fetch(`${this.baseUrl}/courses/${courseId}/content-materials`, {
      headers: this.getAuthHeaders(),
    });

    return this.handleResponse(response);
  }

  async approveContentStructure(
    courseId: string, 
    approved: boolean, 
    modifications?: string
  ): Promise<ApiResponse<any>> {
    const response = await fetch(`${this.baseUrl}/courses/${courseId}/approve-content-structure`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({
        approved,
        modifications,
      }),
    });

    return this.handleResponse(response);
  }

  async approveContent(
    courseId: string, 
    materialId: string, 
    approved: boolean, 
    modifications?: string
  ): Promise<ApiResponse<any>> {
    const response = await fetch(`${this.baseUrl}/courses/${courseId}/approve-content`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({
        material_id: materialId,
        approved,
        modifications,
      }),
    });

    return this.handleResponse(response);
  }

  // Streaming Operations
  startWorkflowStream(
    courseId: string,
    onEvent: (event: StreamEvent) => void,
    onError?: (error: Event) => void,
    onComplete?: () => void
  ): EventSource {
    // Close existing connection if any
    this.closeStream();

    const token = localStorage.getItem('auth_token');
    const url = `${this.baseUrl}/courses/${courseId}/workflow-stream`;
    
    this.eventSource = new EventSource(url, {
      withCredentials: true,
    });

    // Add auth header if possible (note: EventSource doesn't support custom headers)
    // This would need to be handled via query params or cookies in a real implementation

    this.eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onEvent(data);
      } catch (error) {
        console.error('Failed to parse SSE event:', error);
      }
    };

    this.eventSource.onerror = (error) => {
      console.error('SSE connection error:', error);
      if (onError) {
        onError(error);
      }
    };

    this.eventSource.onopen = () => {
      console.log('SSE connection opened');
    };

    return this.eventSource;
  }

  startChatStream(
    courseId: string | null,
    message: string,
    onEvent: (event: any) => void,
    onError?: (error: Event) => void,
    onComplete?: () => void,
    contextHints?: Record<string, any>
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      // Close existing connection if any
      this.closeStream();

      const url = courseId 
        ? `${this.baseUrl}/courses/${courseId}/chat`
        : `${this.baseUrl}/courses/chat`;

      const body: any = { content: message };
      if (contextHints) {
        body.context_hints = contextHints;
      }

      fetch(url, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(body),
      })
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
          throw new Error('No response body reader available');
        }

        const readStream = async () => {
          try {
            while (true) {
              const { done, value } = await reader.read();
              if (done) {
                if (onComplete) onComplete();
                resolve();
                break;
              }

              const chunk = decoder.decode(value);
              const lines = chunk.split('\n');

              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  try {
                    const jsonStr = line.slice(6).trim();
                    if (!jsonStr || jsonStr === '{}') continue;

                    const data = JSON.parse(jsonStr);
                    onEvent(data);
                  } catch (e) {
                    console.warn('Failed to parse SSE data:', e, 'Line:', line);
                  }
                }
              }
            }
          } catch (error) {
            console.error('Stream reading error:', error);
            if (onError) {
              onError(error as Event);
            }
            reject(error);
          }
        };

        readStream();
      })
      .catch(error => {
        console.error('Chat stream error:', error);
        if (onError) {
          onError(error as Event);
        }
        reject(error);
      });
    });
  }

  closeStream(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }

  // Utility Methods
  isAuthenticated(): boolean {
    return !!localStorage.getItem('auth_token');
  }

  setAuthToken(token: string): void {
    localStorage.setItem('auth_token', token);
  }

  clearAuthToken(): void {
    localStorage.removeItem('auth_token');
  }

  getAuthToken(): string | null {
    return localStorage.getItem('auth_token');
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
export default apiClient;
