import axios from 'axios';
import { authService } from './auth';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Configure axios to suppress console errors in development
const apiClient = axios.create({
  baseURL: API_URL,
  validateStatus: function (status) {
    return status < 600;
  }
});

// Add response interceptor to suppress console logging
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    return Promise.resolve(error.response || error);
  }
);

// Add request interceptor to include auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = authService.getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Course interfaces
export interface Course {
  id: string;
  name: string;
  description?: string;
  curriculum_content?: string;
  pedagogy_content?: string;
  created_by: string;
  status: 'draft' | 'curriculum_complete' | 'pedagogy_complete' | 'complete';
  created_at: string;
  updated_at: string;
}

export interface CourseCreate {
  name: string;
  description?: string;
}

export interface AIResponse {
  content: string;
  suggestions?: any[];
}

export interface EnhancementResponse {
  enhanced_content: string;
  diff: DiffChunk[];
  has_changes: boolean;
}

export interface DiffChunk {
  header: string;
  changes: DiffChange[];
}

export interface DiffChange {
  type: 'added' | 'removed' | 'unchanged';
  content: string;
}

class CourseAPI {
  async createCourse(courseData: CourseCreate): Promise<Course> {
    const response = await apiClient.post<Course>('/courses/', courseData);

    if (response.status === 401) {
      throw new Error('Unauthorized. Please log in again.');
    } else if (response.status === 400) {
      throw new Error('Invalid course data. Please check your input.');
    } else if (response.status >= 500) {
      throw new Error('Server error. Please try again later.');
    } else if (response.status >= 400) {
      throw new Error('Failed to create course. Please try again.');
    }

    return response.data;
  }

  async getCourses(): Promise<Course[]> {
    const response = await apiClient.get<Course[]>('/courses/');

    if (response.status === 401) {
      throw new Error('Unauthorized. Please log in again.');
    } else if (response.status >= 500) {
      throw new Error('Server error. Please try again later.');
    } else if (response.status >= 400) {
      throw new Error('Failed to fetch courses.');
    }

    return response.data;
  }

  async getCourse(courseId: string): Promise<Course> {
    const response = await apiClient.get<Course>(`/courses/${courseId}`);

    if (response.status === 404) {
      throw new Error('Course not found.');
    } else if (response.status === 401) {
      throw new Error('Unauthorized. Please log in again.');
    } else if (response.status >= 500) {
      throw new Error('Server error. Please try again later.');
    } else if (response.status >= 400) {
      throw new Error('Failed to fetch course.');
    }

    return response.data;
  }

  async updateCourse(courseId: string, courseData: CourseCreate): Promise<Course> {
    const response = await apiClient.put<Course>(`/courses/${courseId}`, courseData);

    if (response.status === 404) {
      throw new Error('Course not found.');
    } else if (response.status === 403) {
      throw new Error('Not authorized to update this course.');
    } else if (response.status === 401) {
      throw new Error('Unauthorized. Please log in again.');
    } else if (response.status >= 500) {
      throw new Error('Server error. Please try again later.');
    } else if (response.status >= 400) {
      throw new Error('Failed to update course.');
    }

    return response.data;
  }

  async updateCurriculum(courseId: string, content: string): Promise<void> {
    const response = await apiClient.put(`/courses/${courseId}/curriculum`, content, {
      headers: {
        'Content-Type': 'text/plain',
      },
    });

    if (response.status === 404) {
      throw new Error('Course not found.');
    } else if (response.status === 403) {
      throw new Error('Not authorized to update this course.');
    } else if (response.status === 401) {
      throw new Error('Unauthorized. Please log in again.');
    } else if (response.status >= 500) {
      throw new Error('Server error. Please try again later.');
    } else if (response.status >= 400) {
      throw new Error('Failed to update curriculum.');
    }
  }

  async updatePedagogy(courseId: string, content: string): Promise<void> {
    const response = await apiClient.put(`/courses/${courseId}/pedagogy`, content, {
      headers: {
        'Content-Type': 'text/plain',
      },
    });

    if (response.status === 404) {
      throw new Error('Course not found.');
    } else if (response.status === 403) {
      throw new Error('Not authorized to update this course.');
    } else if (response.status === 401) {
      throw new Error('Unauthorized. Please log in again.');
    } else if (response.status >= 500) {
      throw new Error('Server error. Please try again later.');
    } else if (response.status >= 400) {
      throw new Error('Failed to update pedagogy.');
    }
  }

  async generateCurriculum(courseId: string): Promise<AIResponse> {
    const response = await apiClient.post<AIResponse>(`/courses/${courseId}/generate-curriculum`);

    if (response.status === 404) {
      throw new Error('Course not found.');
    } else if (response.status === 403) {
      throw new Error('Not authorized to generate content for this course.');
    } else if (response.status === 401) {
      throw new Error('Unauthorized. Please log in again.');
    } else if (response.status >= 500) {
      throw new Error('Server error. Please try again later.');
    } else if (response.status >= 400) {
      throw new Error('Failed to generate curriculum.');
    }

    return response.data;
  }

  async generatePedagogy(courseId: string): Promise<AIResponse> {
    const response = await apiClient.post<AIResponse>(`/courses/${courseId}/generate-pedagogy`);

    if (response.status === 404) {
      throw new Error('Course not found.');
    } else if (response.status === 403) {
      throw new Error('Not authorized to generate content for this course.');
    } else if (response.status === 401) {
      throw new Error('Unauthorized. Please log in again.');
    } else if (response.status >= 500) {
      throw new Error('Server error. Please try again later.');
    } else if (response.status >= 400) {
      throw new Error('Failed to generate pedagogy.');
    }

    return response.data;
  }

  async enhanceCurriculum(courseId: string, content: string): Promise<EnhancementResponse> {
    const response = await apiClient.post<EnhancementResponse>(
      `/courses/${courseId}/enhance-curriculum`,
      {
        content,
        content_type: 'curriculum',
      }
    );

    if (response.status === 404) {
      throw new Error('Course not found.');
    } else if (response.status === 403) {
      throw new Error('Not authorized to enhance content for this course.');
    } else if (response.status === 401) {
      throw new Error('Unauthorized. Please log in again.');
    } else if (response.status >= 500) {
      throw new Error('Server error. Please try again later.');
    } else if (response.status >= 400) {
      throw new Error('Failed to enhance curriculum.');
    }

    return response.data;
  }

  async enhancePedagogy(courseId: string, content: string): Promise<EnhancementResponse> {
    const response = await apiClient.post<EnhancementResponse>(
      `/courses/${courseId}/enhance-pedagogy`,
      {
        content,
        content_type: 'pedagogy',
      }
    );

    if (response.status === 404) {
      throw new Error('Course not found.');
    } else if (response.status === 403) {
      throw new Error('Not authorized to enhance content for this course.');
    } else if (response.status === 401) {
      throw new Error('Unauthorized. Please log in again.');
    } else if (response.status >= 500) {
      throw new Error('Server error. Please try again later.');
    } else if (response.status >= 400) {
      throw new Error('Failed to enhance pedagogy.');
    }

    return response.data;
  }

  async uploadCurriculumFile(courseId: string, file: File): Promise<{ message: string; content: string }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post(`/courses/${courseId}/upload-curriculum`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    if (response.status === 400) {
      throw new Error(response.data?.detail || 'Invalid file. Please upload a markdown (.md) file.');
    } else if (response.status === 404) {
      throw new Error('Course not found.');
    } else if (response.status === 403) {
      throw new Error('Not authorized to upload files for this course.');
    } else if (response.status === 401) {
      throw new Error('Unauthorized. Please log in again.');
    } else if (response.status >= 500) {
      throw new Error('Server error. Please try again later.');
    } else if (response.status >= 400) {
      throw new Error('Failed to upload curriculum file.');
    }

    return response.data;
  }

  async uploadPedagogyFile(courseId: string, file: File): Promise<{ message: string; content: string }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post(`/courses/${courseId}/upload-pedagogy`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    if (response.status === 400) {
      throw new Error(response.data?.detail || 'Invalid file. Please upload a markdown (.md) file.');
    } else if (response.status === 404) {
      throw new Error('Course not found.');
    } else if (response.status === 403) {
      throw new Error('Not authorized to upload files for this course.');
    } else if (response.status === 401) {
      throw new Error('Unauthorized. Please log in again.');
    } else if (response.status >= 500) {
      throw new Error('Server error. Please try again later.');
    } else if (response.status >= 400) {
      throw new Error('Failed to upload pedagogy file.');
    }

    return response.data;
  }
}

export const courseAPI = new CourseAPI();
