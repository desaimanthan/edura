"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { DashboardLayout } from "@/components/layout/dashboard-layout"
import { BookOpen, Plus, Users, Clock, Star, Edit, CheckCircle, AlertCircle, Loader2, Presentation, Sparkles } from "lucide-react"
import Link from "next/link"
import { courseAPI, Course } from "@/lib/api"
import { toast } from "sonner"

const getStatusInfo = (status: string) => {
  switch (status) {
    case 'draft':
      return {
        label: 'Draft',
        color: 'bg-gray-100 text-gray-800',
        icon: AlertCircle,
        description: 'Course setup incomplete'
      }
    case 'curriculum_complete':
      return {
        label: 'Curriculum Ready',
        color: 'bg-blue-100 text-blue-800',
        icon: Clock,
        description: 'Curriculum complete, pedagogy pending'
      }
    case 'pedagogy_complete':
      return {
        label: 'Pedagogy Ready',
        color: 'bg-yellow-100 text-yellow-800',
        icon: Clock,
        description: 'Pedagogy complete, curriculum pending'
      }
    case 'complete':
      return {
        label: 'Complete',
        color: 'bg-green-100 text-green-800',
        icon: CheckCircle,
        description: 'Course setup complete'
      }
    default:
      return {
        label: 'Unknown',
        color: 'bg-gray-100 text-gray-800',
        icon: AlertCircle,
        description: 'Unknown status'
      }
  }
}

const getNextAction = (course: Course) => {
  switch (course.status) {
    case 'draft':
      return {
        label: 'Continue Setup',
        href: `/courses/create/${course.id}/curriculum`,
        variant: 'default' as const
      }
    case 'curriculum_complete':
      return {
        label: 'Add Pedagogy',
        href: `/courses/create/${course.id}/pedagogy`,
        variant: 'default' as const
      }
    case 'pedagogy_complete':
      return {
        label: 'Add Curriculum',
        href: `/courses/create/${course.id}/curriculum`,
        variant: 'default' as const
      }
    case 'complete':
      return {
        label: 'Edit Course',
        href: `/courses/create/${course.id}/curriculum`,
        variant: 'outline' as const
      }
    default:
      return {
        label: 'Continue Setup',
        href: `/courses/create/${course.id}/curriculum`,
        variant: 'default' as const
      }
  }
}

export default function Courses() {
  const [courses, setCourses] = useState<Course[]>([])
  const [courseSlides, setCourseSlides] = useState<Record<string, any[]>>({})
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchCourses = async () => {
      try {
        const coursesData = await courseAPI.getCourses()
        setCourses(coursesData)
        
        // Fetch slide decks for each course
        const slidesData: Record<string, any[]> = {}
        for (const course of coursesData) {
          try {
            const decks = await courseAPI.getSlideDecks(course.id)
            slidesData[course.id] = decks
          } catch (error) {
            // If slides don't exist, set empty array
            slidesData[course.id] = []
          }
        }
        setCourseSlides(slidesData)
      } catch (error) {
        toast.error(error instanceof Error ? error.message : "Failed to fetch courses")
      } finally {
        setIsLoading(false)
      }
    }

    fetchCourses()
  }, [])

  const completeCourses = courses.filter(course => course.status === 'complete')
  const inProgressCourses = courses.filter(course => course.status !== 'complete')
  const coursesWithSlides = courses.filter(course => courseSlides[course.id] && courseSlides[course.id].length > 0)

  return (
    <DashboardLayout title="Courses" icon={BookOpen}>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Welcome Card */}
        <Card className="col-span-full">
          <CardHeader>
            <CardTitle className="text-2xl flex items-center">
              <BookOpen className="h-6 w-6 mr-2" />
              Course Management
            </CardTitle>
            <CardDescription>
              Manage your courses, view progress, and continue course creation.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              <Link href="/courses/create">
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Create New Course
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>

        {/* Course Statistics */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <BookOpen className="h-5 w-5 mr-2" />
              Total Courses
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{courses.length}</div>
            <p className="text-sm text-muted-foreground">
              {completeCourses.length} complete, {inProgressCourses.length} in progress
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <CheckCircle className="h-5 w-5 mr-2" />
              Complete Courses
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{completeCourses.length}</div>
            <p className="text-sm text-muted-foreground">Ready for content creation</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Presentation className="h-5 w-5 mr-2" />
              Courses with Slides
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{coursesWithSlides.length}</div>
            <p className="text-sm text-muted-foreground">Ready for presentation</p>
          </CardContent>
        </Card>

        {/* Courses List */}
        <Card className="col-span-full">
          <CardHeader>
            <CardTitle>Your Courses</CardTitle>
            <CardDescription>
              {courses.length > 0 
                ? "Manage and continue working on your courses"
                : "You haven't created any courses yet. Start by creating your first course!"
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin" />
                <span className="ml-2">Loading courses...</span>
              </div>
            ) : courses.length === 0 ? (
              <div className="text-center py-8">
                <BookOpen className="h-16 w-16 mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No courses yet</h3>
                <p className="text-gray-600 mb-4">
                  Create your first course to get started with ProfessorAI
                </p>
                <Link href="/courses/create">
                  <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    Create Your First Course
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-4">
                {courses.map((course, index) => {
                  const statusInfo = getStatusInfo(course.status)
                  const nextAction = getNextAction(course)
                  const StatusIcon = statusInfo.icon
                  const hasSlides = courseSlides[course.id] && courseSlides[course.id].length > 0

                  return (
                    <div key={course.id || `course-${index}`} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                      <div className="flex items-center space-x-4">
                        <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                          <BookOpen className="h-6 w-6 text-blue-600" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-medium">{course.name}</h3>
                            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${statusInfo.color}`}>
                              <StatusIcon className="h-3 w-3 mr-1" />
                              {statusInfo.label}
                            </span>
                            {hasSlides && (
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                                <Presentation className="h-3 w-3 mr-1" />
                                {courseSlides[course.id].length} Slide Deck{courseSlides[course.id].length > 1 ? 's' : ''}
                              </span>
                            )}
                          </div>
                          {course.description && (
                            <p className="text-sm text-muted-foreground mb-1">{course.description}</p>
                          )}
                          <p className="text-xs text-muted-foreground">{statusInfo.description}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="text-right mr-4">
                          <div className="flex items-center text-sm text-muted-foreground">
                            <Clock className="h-4 w-4 mr-1" />
                            <span>
                              Updated {new Date(course.updated_at).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                        
                        {/* Slide Actions */}
                        {hasSlides ? (
                          <Link href={`/courses/${course.id}/slides`}>
                            <Button variant="default" size="sm" className="bg-purple-600 hover:bg-purple-700">
                              <Presentation className="h-4 w-4 mr-2" />
                              View Slides
                            </Button>
                          </Link>
                        ) : course.status === 'complete' ? (
                          <Link href={`/courses/create/${course.id}/workspace`}>
                            <Button variant="default" size="sm" className="bg-green-600 hover:bg-green-700">
                              <Sparkles className="h-4 w-4 mr-2" />
                              Generate Slides
                            </Button>
                          </Link>
                        ) : null}
                        
                        {/* Course Edit Action */}
                        <Link href={nextAction.href}>
                          <Button variant={nextAction.variant} size="sm">
                            <Edit className="h-4 w-4 mr-2" />
                            {nextAction.label}
                          </Button>
                        </Link>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}
