"use client"

import { useRouter, useParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { BookOpen, FileText, GraduationCap, Brain, Check, Circle } from "lucide-react"
import { Course } from "@/lib/api"

interface CourseCreationNavProps {
  course: Course | null
  currentStep: 'info' | 'curriculum' | 'pedagogy' | 'workspace'
  courseId?: string
}

export function CourseCreationNav({ course, currentStep, courseId: propCourseId }: CourseCreationNavProps) {
  const router = useRouter()
  const params = useParams()
  const courseId = propCourseId || (Array.isArray(params.id) ? params.id[0] : params.id as string)

  const steps = [
    {
      id: 'info',
      title: 'Course Information',
      icon: BookOpen,
      path: courseId ? `/courses/create?edit=${courseId}` : '/courses/create',
      completed: course ? true : false,
      available: true
    },
    {
      id: 'curriculum',
      title: 'Curriculum',
      icon: FileText,
      path: courseId ? `/courses/create/${courseId}/curriculum` : null,
      completed: course?.curriculum_content ? true : false,
      available: course ? true : false
    },
    {
      id: 'pedagogy',
      title: 'Pedagogy',
      icon: GraduationCap,
      path: courseId ? `/courses/create/${courseId}/pedagogy` : null,
      completed: course?.pedagogy_content ? true : false,
      available: course ? true : false
    },
    {
      id: 'workspace',
      title: 'Research & Workspace',
      icon: Brain,
      path: courseId ? `/courses/create/${courseId}/workspace` : null,
      completed: false, // Research is optional, so never marked as "completed"
      available: course?.curriculum_content && course?.pedagogy_content ? true : false
    }
  ]

  const handleStepClick = (step: typeof steps[0]) => {
    if (!step.available || !step.path) return
    router.push(step.path)
  }

  return (
    <Card className="p-4 mb-6">
      <div className="flex items-center justify-between">
        {steps.map((step, index) => {
          const Icon = step.icon
          const isActive = currentStep === step.id
          const isCompleted = step.completed
          const isAvailable = step.available

          return (
            <div key={step.id} className="flex items-center">
              {/* Step Circle */}
              <Button
                variant={isActive ? "default" : "ghost"}
                size="sm"
                onClick={() => handleStepClick(step)}
                disabled={!isAvailable}
                className={`
                  w-10 h-10 rounded-full p-0 flex items-center justify-center
                  ${isActive 
                    ? 'bg-blue-600 text-white hover:bg-blue-700' 
                    : isCompleted 
                      ? 'bg-green-600 text-white hover:bg-green-700'
                      : isAvailable
                        ? 'border-2 border-gray-300 text-gray-600 hover:border-gray-400 hover:text-gray-800'
                        : 'border-2 border-gray-200 text-gray-400 cursor-not-allowed'
                  }
                `}
              >
                {isCompleted && !isActive ? (
                  <Check className="h-4 w-4" />
                ) : (
                  <Icon className="h-4 w-4" />
                )}
              </Button>

              {/* Step Label */}
              <div className="ml-3">
                <Button
                  variant="ghost"
                  onClick={() => handleStepClick(step)}
                  disabled={!isAvailable}
                  className={`
                    p-0 h-auto font-medium text-sm
                    ${isActive 
                      ? 'text-blue-600 hover:text-blue-700' 
                      : isCompleted 
                        ? 'text-green-600 hover:text-green-700'
                        : isAvailable
                          ? 'text-gray-700 hover:text-gray-900'
                          : 'text-gray-400 cursor-not-allowed'
                    }
                  `}
                >
                  {step.title}
                </Button>
                <div className="flex items-center mt-1">
                  <Circle className={`h-2 w-2 mr-1 ${
                    isCompleted ? 'fill-green-600 text-green-600' :
                    isActive ? 'fill-blue-600 text-blue-600' :
                    'fill-gray-300 text-gray-300'
                  }`} />
                  <span className="text-xs text-gray-500">
                    {isCompleted ? 'Complete' : isActive ? 'In Progress' : isAvailable ? 'Available' : 'Locked'}
                  </span>
                </div>
              </div>

              {/* Connector Line */}
              {index < steps.length - 1 && (
                <div className={`flex-1 mx-6 h-px ${
                  steps[index + 1].completed || (isCompleted && steps[index + 1].available)
                    ? 'bg-green-300' 
                    : isCompleted 
                      ? 'bg-blue-300'
                      : 'bg-gray-200'
                }`} />
              )}
            </div>
          )
        })}
      </div>

      {/* Progress Summary */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>
            Progress: {steps.filter(s => s.completed).length} of {steps.length} sections complete
          </span>
          <div className="flex items-center space-x-4">
            <div className="flex items-center">
              <div className="w-3 h-3 bg-green-600 rounded-full mr-2"></div>
              <span>Complete</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-blue-600 rounded-full mr-2"></div>
              <span>Current</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 border-2 border-gray-300 rounded-full mr-2"></div>
              <span>Available</span>
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
}
