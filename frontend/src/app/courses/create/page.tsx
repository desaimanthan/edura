"use client"

import { useState, useEffect } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { DashboardLayout } from "@/components/layout/dashboard-layout"
import { CourseCreationNav } from "@/components/course-creation-nav"
import { BookOpen, ArrowRight, Loader2 } from "lucide-react"
import { courseAPI, Course } from "@/lib/api"
import { toast } from "sonner"

export default function CreateCourse() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const editCourseId = searchParams.get('edit') // Check if we're editing an existing course
  
  const [formData, setFormData] = useState({
    name: "",
    description: ""
  })
  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingCourse, setIsLoadingCourse] = useState(false)
  const [existingCourse, setExistingCourse] = useState<Course | null>(null)

  // Load existing course data if editing
  useEffect(() => {
    const loadCourse = async () => {
      if (!editCourseId) return

      setIsLoadingCourse(true)
      try {
        const courseData = await courseAPI.getCourse(editCourseId)
        setExistingCourse(courseData)
        setFormData({
          name: courseData.name,
          description: courseData.description || ""
        })
      } catch (error) {
        toast.error("Failed to load course data")
        router.push("/courses")
      } finally {
        setIsLoadingCourse(false)
      }
    }

    loadCourse()
  }, [editCourseId, router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.name.trim()) {
      toast.error("Please enter a course name")
      return
    }

    setIsLoading(true)
    
    try {
      if (existingCourse) {
        // Update existing course
        await courseAPI.updateCourse(existingCourse.id, {
          name: formData.name.trim(),
          description: formData.description.trim() || undefined
        })
        
        toast.success("Course information updated!")
        router.push(`/courses/create/${existingCourse.id}/curriculum`)
      } else {
        // Create new course
        const course = await courseAPI.createCourse({
          name: formData.name.trim(),
          description: formData.description.trim() || undefined
        })
        
        toast.success("Course created successfully!")
        router.push(`/courses/create/${course.id}/curriculum`)
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to save course")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <DashboardLayout title="Create New Course" icon={BookOpen}>
      <div className="mx-auto">
        {/* Course Creation Navigation */}
        <CourseCreationNav course={existingCourse} currentStep="info" courseId={existingCourse?.id} />

        {/* Course Creation Form */}
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl flex items-center">
              <BookOpen className="h-6 w-6 mr-2" />
              Course Information
            </CardTitle>
            <CardDescription>
              Let's start by giving your course a name and description. You can always change these later.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="name">Course Name *</Label>
                <Input
                  id="name"
                  type="text"
                  placeholder="e.g., Introduction to Machine Learning"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  disabled={isLoading}
                  className="text-lg"
                />
                <p className="text-sm text-muted-foreground">
                  Choose a clear, descriptive name for your course
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Course Description (Optional)</Label>
                <textarea
                  id="description"
                  placeholder="Brief description of what this course covers..."
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  disabled={isLoading}
                  className="w-full min-h-[100px] px-3 py-2 border border-input bg-background text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 rounded-md resize-none"
                />
                <p className="text-sm text-muted-foreground">
                  A brief overview to help you remember what this course is about
                </p>
              </div>

              <div className="flex justify-between pt-6">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => router.push("/courses")}
                  disabled={isLoading}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={isLoading || !formData.name.trim()}>
                  {isLoading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      {existingCourse ? "Updating..." : "Creating..."}
                    </>
                  ) : (
                    <>
                      Next: Curriculum
                      <ArrowRight className="h-4 w-4 ml-2" />
                    </>
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Help Text */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <h3 className="font-medium text-blue-900 mb-2">What's Next?</h3>
          <p className="text-sm text-blue-700">
            After creating your course, you'll set up the curriculum (detailed week-by-week plan) 
            and pedagogy (teaching methods and learning approaches). You can upload existing files, 
            write content directly, or use AI to generate these for you.
          </p>
        </div>
      </div>
    </DashboardLayout>
  )
}
