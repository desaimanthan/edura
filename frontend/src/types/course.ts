export interface FeaturedCourse {
  id: number
  title: string
  description: string
  fullDescription: string
  image: string
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced'
  duration: string
  students: number
  rating: number
  reviews: number
  category: string
  instructor: string
  instructorBio: string
  instructorImage: string
  price: number
  lessons: number
  projects: number
  certificate: boolean
  skills: string[]
  prerequisites: string[]
  curriculum: Array<{
    title: string
    lessons: number
    duration: string
  }>
}

export interface CourseFilters {
  searchQuery: string
  selectedCategory: string
  difficulty?: string
  priceRange?: [number, number]
}

export interface Course {
  id: string
  name: string
  description?: string
  status: string
  workflow_step: string
  created_at: string
  updated_at: string
  curriculum_source?: string
  // Multi-size cover image fields
  cover_image_large_public_url?: string
  cover_image_medium_public_url?: string
  cover_image_small_public_url?: string
  // Legacy cover image field (for backward compatibility)
  cover_image_public_url?: string
  enrolled_students?: number
  // Publishing fields
  is_published?: boolean
  published_at?: string
  published_by?: string
  public_access_key?: string
}

export interface PublishCourseRequest {
  generate_access_key?: boolean
}

export interface PublishCourseResponse {
  success: boolean
  message: string
  public_url?: string
  access_key?: string
  published_at: string
}

export interface AssessmentQuestion {
  text: string
  options?: Array<{ id: string; text: string } | string>
  correct_answer?: string
  explanation?: string
}

export interface AssessmentData {
  question?: AssessmentQuestion | string
}

export interface CourseMaterial {
  _id: string
  title: string
  description?: string
  material_type: 'slide' | 'assessment'
  module_number: number
  chapter_number: number
  slide_number?: number
  content?: string
  assessment_data?: AssessmentData
  assessment_format?: string
}

export interface PublicCourseData {
  id: string
  name: string
  description?: string
  learning_outcomes: string[]
  prerequisites: string[]
  cover_image_large_public_url?: string
  cover_image_medium_public_url?: string
  cover_image_small_public_url?: string
  cover_image_public_url?: string
  content_structure: Record<string, unknown>
  total_content_items: number
  completed_content_items: number
  published_at?: string
  materials: CourseMaterial[]
}
