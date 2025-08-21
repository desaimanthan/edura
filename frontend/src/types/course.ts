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
