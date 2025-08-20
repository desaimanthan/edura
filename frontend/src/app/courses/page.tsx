"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { DashboardLayout } from "@/components/layout/dashboard-layout"
import { BookOpen, Plus, Users, Clock, Star, Edit, Trash2, Eye } from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { toast } from "sonner"

interface Course {
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
}

export default function Courses() {
  const [courses, setCourses] = useState<Course[]>([])
  const [loading, setLoading] = useState(true)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null)
  const [editForm, setEditForm] = useState({ name: "", description: "" })
  const [deleting, setDeleting] = useState(false)
  const [updating, setUpdating] = useState(false)
  const router = useRouter()

  useEffect(() => {
    fetchCourses()
  }, [])

  const fetchCourses = async () => {
    try {
      const token = localStorage.getItem("auth_token")
      if (!token) {
        router.push("/auth/signin")
        return
      }

      const response = await fetch("http://localhost:8000/courses", {
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      })

      if (!response.ok) {
        if (response.status === 401) {
          localStorage.removeItem("auth_token")
          localStorage.removeItem("auth_user")
          router.push("/auth/signin")
          return
        }
        throw new Error("Failed to fetch courses")
      }

      const data = await response.json()
      
      // Ensure each course has an id field (handle both _id and id)
      const coursesWithId = data.map((course: any) => ({
        ...course,
        id: course.id || course._id
      }))
      
      setCourses(coursesWithId)
    } catch (error) {
      console.error("Error fetching courses:", error)
      toast.error("Failed to load courses")
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteCourse = async () => {
    if (!selectedCourse) return

    setDeleting(true)
    try {
      const token = localStorage.getItem("auth_token")
      const response = await fetch(`http://localhost:8000/courses/${selectedCourse.id}`, {
        method: "DELETE",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      })

      if (!response.ok) {
        throw new Error("Failed to delete course")
      }

      toast.success("Course deleted successfully")
      setCourses(courses.filter(course => course.id !== selectedCourse.id))
      setDeleteDialogOpen(false)
      setSelectedCourse(null)
    } catch (error) {
      console.error("Error deleting course:", error)
      toast.error("Failed to delete course")
    } finally {
      setDeleting(false)
    }
  }

  const handleEditCourse = async () => {
    if (!selectedCourse) return

    setUpdating(true)
    try {
      const token = localStorage.getItem("auth_token")
      const response = await fetch(`http://localhost:8000/courses/${selectedCourse.id}`, {
        method: "PUT",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: editForm.name,
          description: editForm.description,
        }),
      })

      if (!response.ok) {
        throw new Error("Failed to update course")
      }

      const updatedCourse = await response.json()
      toast.success("Course updated successfully")
      
      // Ensure the updated course has the correct id field
      const courseWithId = {
        ...updatedCourse,
        id: updatedCourse.id || updatedCourse._id
      }
      
      setCourses(courses.map(course => 
        course.id === selectedCourse.id ? courseWithId : course
      ))
      setEditDialogOpen(false)
      setSelectedCourse(null)
      setEditForm({ name: "", description: "" })
    } catch (error) {
      console.error("Error updating course:", error)
      toast.error("Failed to update course")
    } finally {
      setUpdating(false)
    }
  }

  const openEditDialog = (course: Course) => {
    setSelectedCourse(course)
    setEditForm({
      name: course.name,
      description: course.description || "",
    })
    setEditDialogOpen(true)
  }

  const openDeleteDialog = (course: Course) => {
    setSelectedCourse(course)
    setDeleteDialogOpen(true)
  }

  const getStatusBadge = (status: string) => {
    const statusColors = {
      draft: "bg-gray-100 text-gray-800",
      creating: "bg-yellow-100 text-yellow-800",
      active: "bg-green-100 text-green-800",
      completed: "bg-blue-100 text-blue-800",
    }
    
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[status as keyof typeof statusColors] || statusColors.draft}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    )
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffTime = Math.abs(now.getTime() - date.getTime())
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    
    if (diffDays === 1) return "1 day ago"
    if (diffDays < 7) return `${diffDays} days ago`
    if (diffDays < 30) return `${Math.ceil(diffDays / 7)} weeks ago`
    return date.toLocaleDateString()
  }

  if (loading) {
    return (
      <DashboardLayout title="Courses" icon={BookOpen}>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
            <p className="mt-2 text-sm text-muted-foreground">Loading courses...</p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout title="Courses" icon={BookOpen}>
      <div className="flex-1 overflow-y-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Welcome Card */}
        <Card className="col-span-full">
          <CardHeader>
            <CardTitle className="text-2xl flex items-center">
              <BookOpen className="h-6 w-6 mr-2" />
              Course Management
            </CardTitle>
            <CardDescription>
              Manage your courses, view enrollments, and track progress.
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
              <Button variant="outline">
                Import Courses
              </Button>
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
            <p className="text-sm text-muted-foreground">Your courses</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Users className="h-5 w-5 mr-2" />
              Active Courses
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {courses.filter(course => course.status === "active").length}
            </div>
            <p className="text-sm text-muted-foreground">Ready to use</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Star className="h-5 w-5 mr-2" />
              Draft Courses
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {courses.filter(course => course.status === "draft" || course.status === "creating").length}
            </div>
            <p className="text-sm text-muted-foreground">In development</p>
          </CardContent>
        </Card>

        {/* Courses List */}
        <Card className="col-span-full">
          <CardHeader>
            <CardTitle>Your Courses</CardTitle>
            <CardDescription>
              {courses.length === 0 
                ? "No courses found. Create your first course to get started."
                : `You have ${courses.length} course${courses.length !== 1 ? 's' : ''}`
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            {courses.length === 0 ? (
              <div className="text-center py-8">
                <BookOpen className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground mb-4">No courses yet</p>
                <Link href="/courses/create">
                  <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    Create Your First Course
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-4">
                {courses.map((course) => (
                  <div key={course.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                    <div className="flex items-center space-x-4">
                      {/* Course Image/Placeholder with 3:2 aspect ratio */}
                      <div className="w-32 h-20 rounded-lg overflow-hidden flex-shrink-0">
                        {/* Use small image for list view, with fallbacks to medium, large, then legacy */}
                        {(course.cover_image_small_public_url || course.cover_image_medium_public_url || course.cover_image_large_public_url || course.cover_image_public_url) ? (
                          <img 
                            src={course.cover_image_small_public_url || course.cover_image_medium_public_url || course.cover_image_large_public_url || course.cover_image_public_url} 
                            alt={course.name}
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              // Fallback to placeholder if image fails to load
                              const target = e.target as HTMLImageElement;
                              target.style.display = 'none';
                              target.nextElementSibling?.classList.remove('hidden');
                            }}
                          />
                        ) : null}
                        <div className={`w-full h-full bg-blue-100 flex items-center justify-center ${(course.cover_image_small_public_url || course.cover_image_medium_public_url || course.cover_image_large_public_url || course.cover_image_public_url) ? 'hidden' : ''}`}>
                          <BookOpen className="h-8 w-8 text-blue-600" />
                        </div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="text-xl font-bold truncate">{course.name}</h3>
                          {getStatusBadge(course.status)}
                        </div>
                        {/* Description with 1-line limit and ellipsis */}
                        <p className="text-sm text-muted-foreground line-clamp-1 mb-2 w-[90%]">
                          {course.description || "No description"}
                        </p>
                        <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                          <div className="flex items-center">
                            <Users className="h-3 w-3 mr-1" />
                            {course.enrolled_students || 0} students enrolled
                          </div>
                          {course.curriculum_source && (
                            <div>
                              Curriculum: {course.curriculum_source}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                    {/* Action buttons in same line */}
                    <div className="flex items-center space-x-2">
                      <Link href={`/courses/create/${course.id}`}>
                        <Button variant="outline" size="sm" className="h-9 px-3">
                          <Eye className="h-4 w-4" />
                        </Button>
                      </Link>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="h-9 px-3"
                        onClick={() => openEditDialog(course)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="h-9 px-3 text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200 hover:border-red-300"
                        onClick={() => openDeleteDialog(course)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
        </div>
      </div>

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Course</DialogTitle>
            <DialogDescription>
              Update the course name and description.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="name">Course Name</Label>
              <Input
                id="name"
                value={editForm.name}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEditForm({ ...editForm, name: e.target.value })}
                placeholder="Enter course name"
              />
            </div>
            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={editForm.description}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setEditForm({ ...editForm, description: e.target.value })}
                placeholder="Enter course description"
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleEditCourse} disabled={updating || !editForm.name.trim()}>
              {updating ? "Updating..." : "Update Course"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Course</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{selectedCourse?.name}"? This action cannot be undone.
              All course data, including curriculum files and chat history, will be permanently deleted.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteCourse}
              disabled={deleting}
              className="bg-red-600 hover:bg-red-700"
            >
              {deleting ? "Deleting..." : "Delete Course"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </DashboardLayout>
  )
}
