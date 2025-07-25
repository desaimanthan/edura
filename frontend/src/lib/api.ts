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

// Research interfaces
export interface ResearchStatusResponse {
  id: string;
  course_id: string;
  task_id: string;
  status: 'pending' | 'queued' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
  progress?: string;
  markdown_report?: string;
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

export interface ResearchReportResponse {
  course_id: string;
  task_id: string;
  markdown_report: string;
  created_at: string;
  completed_at: string;
}

export interface ResearchGenerationResponse {
  message: string;
  task_id: string;
  research_id: string;
  status: string;
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

  // Research API methods
  async generateResearch(courseId: string): Promise<ResearchGenerationResponse> {
    const response = await apiClient.post<ResearchGenerationResponse>(`/courses/${courseId}/generate-research`);

    if (response.status === 404) {
      throw new Error('Course not found.');
    } else if (response.status === 403) {
      throw new Error('Not authorized to generate research for this course.');
    } else if (response.status === 401) {
      throw new Error('Unauthorized. Please log in again.');
    } else if (response.status >= 500) {
      throw new Error('Server error. Please try again later.');
    } else if (response.status >= 400) {
      throw new Error('Failed to start research generation.');
    }

    return response.data;
  }

  async getResearchStatus(courseId: string): Promise<ResearchStatusResponse> {
    const response = await apiClient.get<ResearchStatusResponse>(`/courses/${courseId}/research-status`);

    if (response.status === 404) {
      throw new Error('No research report found for this course.');
    } else if (response.status === 403) {
      throw new Error('Not authorized to access research for this course.');
    } else if (response.status === 401) {
      throw new Error('Unauthorized. Please log in again.');
    } else if (response.status >= 500) {
      throw new Error('Server error. Please try again later.');
    } else if (response.status >= 400) {
      throw new Error('Failed to get research status.');
    }

    return response.data;
  }

  async getResearchReport(courseId: string): Promise<ResearchReportResponse> {
    const response = await apiClient.get<ResearchReportResponse>(`/courses/${courseId}/research-report`);

    if (response.status === 404) {
      throw new Error('No completed research report found for this course.');
    } else if (response.status === 403) {
      throw new Error('Not authorized to access research for this course.');
    } else if (response.status === 401) {
      throw new Error('Unauthorized. Please log in again.');
    } else if (response.status >= 500) {
      throw new Error('Server error. Please try again later.');
    } else if (response.status >= 400) {
      throw new Error('Failed to get research report.');
    }

    return response.data;
  }

  async cancelResearch(courseId: string): Promise<{ message: string; task_id: string; status: string }> {
    const response = await apiClient.post<{ message: string; task_id: string; status: string }>(`/courses/${courseId}/cancel-research`);

    if (response.status === 404) {
      throw new Error('No active research task found for this course.');
    } else if (response.status === 403) {
      throw new Error('Not authorized to cancel research for this course.');
    } else if (response.status === 401) {
      throw new Error('Unauthorized. Please log in again.');
    } else if (response.status >= 500) {
      throw new Error('Server error. Please try again later.');
    } else if (response.status >= 400) {
      throw new Error('Failed to cancel research.');
    }

    return response.data;
  }

  // Slide Generation API methods
  async generateSlidesWithAgents(courseId: string, request?: { title?: string; description?: string }): Promise<{ session_id: string; status: string; message: string; websocket_url: string }> {
    const response = await apiClient.post(`/courses/${courseId}/slides/generate-with-agents`, request || {});

    if (response.status === 404) {
      throw new Error('Course not found.');
    } else if (response.status === 403) {
      throw new Error('Not authorized to generate slides for this course.');
    } else if (response.status === 400) {
      throw new Error('Course must have both curriculum and pedagogy content before generating slides.');
    } else if (response.status === 401) {
      throw new Error('Unauthorized. Please log in again.');
    } else if (response.status >= 500) {
      throw new Error('Server error. Please try again later.');
    } else if (response.status >= 400) {
      throw new Error('Failed to start slide generation.');
    }

    return response.data;
  }

  async getSlideGenerationStatus(courseId: string, sessionId: string): Promise<{
    session_id: string;
    status: string;
    progress?: number;
    current_agent?: string;
    total_slides_generated: number;
    conversation_messages: number;
    error_message?: string;
    websocket_url?: string;
    created_at: string;
    completed_at?: string;
  }> {
    const response = await apiClient.get(`/courses/${courseId}/slides/generation/${sessionId}/status`);

    if (response.status === 404) {
      throw new Error('Slide generation session not found.');
    } else if (response.status === 403) {
      throw new Error('Not authorized to access slide generation for this course.');
    } else if (response.status === 401) {
      throw new Error('Unauthorized. Please log in again.');
    } else if (response.status >= 500) {
      throw new Error('Server error. Please try again later.');
    } else if (response.status >= 400) {
      throw new Error('Failed to get slide generation status.');
    }

    return response.data;
  }

  async getSlideDecks(courseId: string): Promise<Array<{
    id: string;
    course_id: string;
    title: string;
    description?: string;
    status: string;
    total_slides: number;
    created_by: string;
    generation_session_id?: string;
    created_at: string;
    updated_at: string;
  }>> {
    const response = await apiClient.get(`/courses/${courseId}/slides`);

    if (response.status === 404) {
      throw new Error('Course not found.');
    } else if (response.status === 403) {
      throw new Error('Not authorized to access slides for this course.');
    } else if (response.status === 401) {
      throw new Error('Unauthorized. Please log in again.');
    } else if (response.status >= 500) {
      throw new Error('Server error. Please try again later.');
    } else if (response.status >= 400) {
      throw new Error('Failed to get slide decks.');
    }

    return response.data;
  }

  async getSlidesInDeck(courseId: string, deckId: string): Promise<Array<{
    id: string;
    deck_id: string;
    slide_number: number;
    title: string;
    content: any;
    template_type: string;
    layout_config: any;
    images: any[];
    ai_generated: boolean;
    agent_decisions: any;
    created_at: string;
    updated_at: string;
  }>> {
    const response = await apiClient.get(`/courses/${courseId}/slides/${deckId}`);

    if (response.status === 404) {
      throw new Error('Slide deck not found.');
    } else if (response.status === 403) {
      throw new Error('Not authorized to access slides for this course.');
    } else if (response.status === 401) {
      throw new Error('Unauthorized. Please log in again.');
    } else if (response.status >= 500) {
      throw new Error('Server error. Please try again later.');
    } else if (response.status >= 400) {
      throw new Error('Failed to get slides.');
    }

    return response.data;
  }

  async getAgentConversation(courseId: string, sessionId: string): Promise<{
    session_id: string;
    conversation_log: Array<{
      step: number;
      agent_name: string;
      agent_role: string;
      message: string;
      timestamp: string;
      message_type: string;
    }>;
    agent_decisions: any;
    generation_metadata: any;
  }> {
    const response = await apiClient.get(`/courses/${courseId}/slides/generation/${sessionId}/conversation`);

    if (response.status === 404) {
      throw new Error('Generation session not found.');
    } else if (response.status === 403) {
      throw new Error('Not authorized to access conversation for this course.');
    } else if (response.status === 401) {
      throw new Error('Unauthorized. Please log in again.');
    } else if (response.status >= 500) {
      throw new Error('Server error. Please try again later.');
    } else if (response.status >= 400) {
      throw new Error('Failed to get agent conversation.');
    }

    return response.data;
  }

  async getLatestSlides(courseId: string): Promise<{
    slides: Array<{
      slide_number: number;
      title: string;
      content: {
        main_content: string;
        supporting_text: string;
        table_data?: {
          headers: string[];
          rows: string[][];
        };
      };
      template_type: string;
      images: Array<{
        url: string;
        alt_text: string;
        prompt: string;
      }>;
      layout_config: any;
    }>;
    deck_info: {
      title: string;
      description: string;
      total_slides: number;
      created_at: string;
    };
  }> {
    const response = await apiClient.get(`/courses/${courseId}/slides/latest`);

    if (response.status === 404) {
      throw new Error('No completed slide deck found for this course.');
    } else if (response.status === 403) {
      throw new Error('Not authorized to access slides for this course.');
    } else if (response.status === 401) {
      throw new Error('Unauthorized. Please log in again.');
    } else if (response.status >= 500) {
      throw new Error('Server error. Please try again later.');
    } else if (response.status >= 400) {
      throw new Error('Failed to get latest slides.');
    }

    return response.data;
  }
}

export const courseAPI = new CourseAPI();
