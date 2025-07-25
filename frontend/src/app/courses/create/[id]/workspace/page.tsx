"use client"

import { useState, useEffect, useCallback } from "react"
import { useRouter, useParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { DashboardLayout } from "@/components/layout/dashboard-layout"
import { CourseCreationNav } from "@/components/course-creation-nav"
import { 
  BookOpen, 
  ArrowLeft, 
  Sparkles, 
  Loader2, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Download,
  RefreshCw,
  FileText,
  Brain,
  Zap
} from "lucide-react"
import { courseAPI, Course, ResearchStatusResponse } from "@/lib/api"
import { toast } from "sonner"
import dynamic from "next/dynamic"

// Dynamically import MDEditor to avoid SSR issues
const MDEditor = dynamic(
  () => import("@uiw/react-md-editor").then((mod) => mod.default),
  { ssr: false }
)

export default function WorkspacePage() {
  const router = useRouter()
  const params = useParams()
  const courseId = Array.isArray(params.id) ? params.id[0] : params.id as string

  const [course, setCourse] = useState<Course | null>(null)
  const [researchStatus, setResearchStatus] = useState<ResearchStatusResponse | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isPolling, setIsPolling] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null)
  const [researchReport, setResearchReport] = useState<string>("")
  const [showReport, setShowReport] = useState(false)
  const [isCancelling, setIsCancelling] = useState(false)
  const [isGeneratingSlides, setIsGeneratingSlides] = useState(false)
  const [slideGenerationSession, setSlideGenerationSession] = useState<string | null>(null)
  const [websocket, setWebsocket] = useState<WebSocket | null>(null)
  const [agentMessages, setAgentMessages] = useState<Array<{
    step: number
    agent_name: string
    agent_role: string
    message: string
    timestamp: string
  }>>([])
  const [generationProgress, setGenerationProgress] = useState<{
    current: number
    total: number
    description: string
  } | null>(null)

  // Helper function to format time in IST (backend now stores IST directly)
  const formatTimeIST = (istTimeString: string) => {
    const istDate = new Date(istTimeString)
    
    return istDate.toLocaleString('en-IN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true
    }) + ' IST'
  }

  // Load course data
  useEffect(() => {
    const loadCourse = async () => {
      try {
        const courseData = await courseAPI.getCourse(courseId)
        setCourse(courseData)
      } catch (error) {
        toast.error("Failed to load course")
        router.push("/courses")
      }
    }

    if (courseId) {
      loadCourse()
    }
  }, [courseId, router])

  // Check for existing research status on load
  useEffect(() => {
    const checkExistingResearch = async () => {
      if (!courseId) return
      
      try {
        const status = await courseAPI.getResearchStatus(courseId)
        console.log("Existing research status:", status)
        setResearchStatus(status)
        
        if (status.status === "completed" && status.markdown_report) {
          setResearchReport(status.markdown_report)
          setShowReport(true)
        } else if (status.status === "pending" || status.status === "in_progress" || status.status === "queued") {
          console.log("Starting polling for status:", status.status)
          startPolling()
        }
      } catch (error) {
        // No existing research found, which is fine
        console.log("No existing research found")
      }
    }

    if (courseId) {
      checkExistingResearch()
    }
  }, [courseId])

  // Polling function
  const pollResearchStatus = useCallback(async () => {
    if (!courseId) return

    try {
      const status = await courseAPI.getResearchStatus(courseId)
      setResearchStatus(status)

      if (status.status === "completed") {
        if (status.markdown_report) {
          setResearchReport(status.markdown_report)
          setShowReport(true)
          toast.success("Deep research completed successfully!")
        }
        stopPolling()
      } else if (status.status === "failed") {
        toast.error(`Research failed: ${status.error_message || "Unknown error"}`)
        stopPolling()
      }
    } catch (error) {
      console.error("Error polling research status:", error)
      // Don't show error toast for polling failures to avoid spam
    }
  }, [courseId])

  // Start polling
  const startPolling = useCallback(() => {
    if (pollingInterval) return // Already polling

    setIsPolling(true)
    const interval = setInterval(pollResearchStatus, 30000) // Poll every 30 seconds
    setPollingInterval(interval)
  }, [pollResearchStatus, pollingInterval])

  // Stop polling
  const stopPolling = useCallback(() => {
    if (pollingInterval) {
      clearInterval(pollingInterval)
      setPollingInterval(null)
    }
    setIsPolling(false)
  }, [pollingInterval])

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval)
      }
    }
  }, [pollingInterval])

  // Generate research
  const handleGenerateResearch = async () => {
    if (!course) return

    setIsGenerating(true)
    try {
      const result = await courseAPI.generateResearch(courseId)
      
      setResearchStatus({
        id: result.research_id,
        course_id: courseId,
        task_id: result.task_id,
        status: "pending",
        created_at: new Date().toISOString()
      })
      
      toast.success("Deep research generation started! This may take several minutes.")
      startPolling()
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to start research generation")
    } finally {
      setIsGenerating(false)
    }
  }

  // Manual refresh
  const handleRefresh = async () => {
    if (!courseId || !researchStatus) return

    setIsRefreshing(true)
    try {
      await pollResearchStatus()
      toast.success("Status refreshed")
    } catch (error) {
      toast.error("Failed to refresh status")
    } finally {
      setIsRefreshing(false)
    }
  }

  // Cancel research
  const handleCancelResearch = async () => {
    if (!courseId || !researchStatus) return

    setIsCancelling(true)
    try {
      await courseAPI.cancelResearch(courseId)
      
      // Update local state
      setResearchStatus({
        ...researchStatus,
        status: "cancelled",
        error_message: "Research task cancelled by user"
      })
      
      // Stop polling
      stopPolling()
      
      toast.success("Research task cancelled successfully")
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to cancel research")
    } finally {
      setIsCancelling(false)
    }
  }

  // Download report
  const handleDownload = () => {
    if (!researchReport || !course) return

    const blob = new Blob([researchReport], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${course.name.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_research_report.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    
    toast.success("Research report downloaded!")
  }

  // Generate slides
  const handleGenerateSlides = async () => {
    if (!course) return

    setIsGeneratingSlides(true)
    setAgentMessages([])
    setGenerationProgress(null)
    
    try {
      const result = await courseAPI.generateSlidesWithAgents(courseId, {
        title: `${course.name} - AI Generated Slides`
      })
      
      setSlideGenerationSession(result.session_id)
      toast.success("Slide generation started! Connecting to real-time updates...")
      
      // Connect to WebSocket for real-time updates
      connectToWebSocket(result.session_id)
      
      // Start polling for slide generation status as backup
      pollSlideGenerationStatus(result.session_id)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to start slide generation")
      setIsGeneratingSlides(false)
    }
  }

  // Connect to WebSocket for real-time updates
  const connectToWebSocket = (sessionId: string) => {
    const wsUrl = `ws://localhost:8000/ws/slides/generation/${sessionId}`
    const ws = new WebSocket(wsUrl)
    
    ws.onopen = () => {
      console.log('WebSocket connected for slide generation')
      setWebsocket(ws)
    }
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        console.log('WebSocket message:', data)
        
        switch (data.type) {
          case 'agent_message':
            setAgentMessages(prev => [...prev, {
              step: data.step,
              agent_name: data.agent_name,
              agent_role: data.agent_role,
              message: data.message,
              timestamp: new Date().toISOString()
            }])
            break
            
          case 'progress_update':
            setGenerationProgress({
              current: data.current,
              total: data.total,
              description: data.description
            })
            break
            
          case 'status_update':
            console.log('Status update:', data.status, data.details)
            break
            
          case 'generation_complete':
            if (data.success) {
              toast.success(`Slide generation completed! Generated ${data.slides_count} slides.`)
              setTimeout(() => {
                router.push(`/courses/${courseId}/slides`)
              }, 2000)
            } else {
              toast.error(`Slide generation failed: ${data.error || 'Unknown error'}`)
            }
            setIsGeneratingSlides(false)
            ws.close()
            break
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error)
      }
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      toast.error('Lost connection to real-time updates')
    }
    
    ws.onclose = () => {
      console.log('WebSocket connection closed')
      setWebsocket(null)
    }
  }

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (websocket) {
        websocket.close()
      }
    }
  }, [websocket])

  // Poll slide generation status
  const pollSlideGenerationStatus = async (sessionId: string) => {
    try {
      const status = await courseAPI.getSlideGenerationStatus(courseId, sessionId)
      
      if (status.status === "completed") {
        toast.success("Slide generation completed successfully!")
        setIsGeneratingSlides(false)
        // Optionally redirect to slides view
        router.push(`/courses/${courseId}/slides`)
      } else if (status.status === "failed") {
        toast.error(`Slide generation failed: ${status.error_message || "Unknown error"}`)
        setIsGeneratingSlides(false)
      } else {
        // Continue polling
        setTimeout(() => pollSlideGenerationStatus(sessionId), 10000) // Poll every 10 seconds
      }
    } catch (error) {
      console.error("Error polling slide generation status:", error)
      setIsGeneratingSlides(false)
    }
  }

  // Get status display info
  const getStatusInfo = () => {
    if (!researchStatus) {
      return {
        icon: <Brain className="h-5 w-5 text-gray-400" />,
        text: "Ready to generate research",
        color: "text-gray-600",
        bgColor: "bg-gray-50"
      }
    }

    switch (researchStatus.status) {
      case "pending":
        return {
          icon: <Clock className="h-5 w-5 text-yellow-500 animate-pulse" />,
          text: "Research queued for processing...",
          color: "text-yellow-700",
          bgColor: "bg-yellow-50"
        }
      case "queued":
        return {
          icon: <Clock className="h-5 w-5 text-yellow-500 animate-pulse" />,
          text: "Research queued in OpenAI system...",
          color: "text-yellow-700",
          bgColor: "bg-yellow-50"
        }
      case "in_progress":
        return {
          icon: <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />,
          text: "Deep research in progress...",
          color: "text-blue-700",
          bgColor: "bg-blue-50"
        }
      case "completed":
        return {
          icon: <CheckCircle className="h-5 w-5 text-green-500" />,
          text: "Research completed successfully!",
          color: "text-green-700",
          bgColor: "bg-green-50"
        }
      case "failed":
        return {
          icon: <XCircle className="h-5 w-5 text-red-500" />,
          text: `Research failed: ${researchStatus.error_message || "Unknown error"}`,
          color: "text-red-700",
          bgColor: "bg-red-50"
        }
      case "cancelled":
        return {
          icon: <XCircle className="h-5 w-5 text-gray-500" />,
          text: "Research task was cancelled",
          color: "text-gray-700",
          bgColor: "bg-gray-50"
        }
      default:
        return {
          icon: <Clock className="h-5 w-5 text-blue-500 animate-pulse" />,
          text: `Research status: ${researchStatus.status} - Please wait...`,
          color: "text-blue-700",
          bgColor: "bg-blue-50"
        }
    }
  }

  const statusInfo = getStatusInfo()

  if (!course) {
    return (
      <DashboardLayout title="Loading..." icon={BookOpen}>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout title={`Course Workspace: ${course.name}`} icon={BookOpen}>
      <div className="mx-auto">
        {/* Course Creation Navigation */}
        <CourseCreationNav course={course} currentStep="workspace" />

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Course Overview */}
          <div className="lg:col-span-1 space-y-6">
            {/* Course Summary */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center">
                  <FileText className="h-5 w-5 mr-2" />
                  Course Summary
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="font-medium text-sm text-gray-700 mb-1">Course Name</h4>
                  <p className="text-sm">{course.name}</p>
                </div>
                
                {course.description && (
                  <div>
                    <h4 className="font-medium text-sm text-gray-700 mb-1">Description</h4>
                    <p className="text-sm text-gray-600">{course.description}</p>
                  </div>
                )}
                
                <div>
                  <h4 className="font-medium text-sm text-gray-700 mb-1">Status</h4>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    course.status === 'complete' ? 'bg-green-100 text-green-800' :
                    course.status === 'pedagogy_complete' ? 'bg-blue-100 text-blue-800' :
                    course.status === 'curriculum_complete' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {course.status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </span>
                </div>

                <div>
                  <h4 className="font-medium text-sm text-gray-700 mb-1">Content Ready</h4>
                  <div className="space-y-1">
                    <div className="flex items-center text-xs">
                      {course.curriculum_content ? (
                        <CheckCircle className="h-3 w-3 text-green-500 mr-1" />
                      ) : (
                        <XCircle className="h-3 w-3 text-red-500 mr-1" />
                      )}
                      Curriculum
                    </div>
                    <div className="flex items-center text-xs">
                      {course.pedagogy_content ? (
                        <CheckCircle className="h-3 w-3 text-green-500 mr-1" />
                      ) : (
                        <XCircle className="h-3 w-3 text-red-500 mr-1" />
                      )}
                      Pedagogy
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Research Status */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center">
                  <Brain className="h-5 w-5 mr-2" />
                  Research Status
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`p-4 rounded-lg ${statusInfo.bgColor} mb-4`}>
                  <div className="flex items-center">
                    {statusInfo.icon}
                    <span className={`ml-2 text-sm font-medium ${statusInfo.color}`}>
                      {statusInfo.text}
                    </span>
                  </div>
                </div>

                {researchStatus && (
                  <div className="space-y-2 text-xs text-gray-600">
                    <div>Task ID: {researchStatus.task_id}</div>
                    <div>Started: {formatTimeIST(researchStatus.created_at)}</div>
                    {researchStatus.completed_at && (
                      <div>Completed: {formatTimeIST(researchStatus.completed_at)}</div>
                    )}
                    {isPolling && (
                      <div className="flex items-center text-blue-600">
                        <Clock className="h-3 w-3 mr-1" />
                        Auto-polling every 30 seconds
                      </div>
                    )}
                  </div>
                )}

                <div className="flex gap-2 mt-4">
                  {(!researchStatus || researchStatus.status === "failed") && (
                    <Button
                      onClick={handleGenerateResearch}
                      disabled={isGenerating || !course.curriculum_content || !course.pedagogy_content}
                      className="flex-1"
                    >
                      {isGenerating ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Starting...
                        </>
                      ) : (
                        <>
                          <Zap className="h-4 w-4 mr-2" />
                          Generate Research
                        </>
                      )}
                    </Button>
                  )}

                  {researchStatus && (researchStatus.status === "pending" || researchStatus.status === "in_progress" || researchStatus.status === "queued") && (
                    <>
                      <Button
                        variant="outline"
                        onClick={handleRefresh}
                        disabled={isRefreshing}
                      >
                        <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
                        Refresh
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={handleCancelResearch}
                        disabled={isCancelling}
                      >
                        {isCancelling ? (
                          <>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            Cancelling...
                          </>
                        ) : (
                          <>
                            <XCircle className="h-4 w-4 mr-2" />
                            Cancel
                          </>
                        )}
                      </Button>
                    </>
                  )}
                </div>

                {(!course.curriculum_content || !course.pedagogy_content) && (
                  <p className="text-xs text-amber-600 mt-2">
                    Complete curriculum and pedagogy setup before generating research.
                  </p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Research Report */}
          <div className="lg:col-span-2">
            <Card className="h-full">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-xl flex items-center">
                    <Sparkles className="h-6 w-6 mr-2" />
                    Deep Research Report
                  </CardTitle>
                  <div className="flex gap-2">
                    {showReport && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleDownload}
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Download
                      </Button>
                    )}
                    {showReport && (
                      <Button
                        size="sm"
                        onClick={handleGenerateSlides}
                        disabled={isGeneratingSlides}
                        className="bg-purple-600 hover:bg-purple-700"
                      >
                        {isGeneratingSlides ? (
                          <>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            Generating...
                          </>
                        ) : (
                          <>
                            <Sparkles className="h-4 w-4 mr-2" />
                            Generate Slides
                          </>
                        )}
                      </Button>
                    )}
                  </div>
                </div>
                <CardDescription>
                  AI-powered comprehensive research for your course content
                </CardDescription>
              </CardHeader>
              <CardContent>
                {showReport ? (
                  <div className="border rounded-lg overflow-hidden">
                    <MDEditor
                      value={researchReport}
                      preview="preview"
                      hideToolbar
                      data-color-mode="light"
                      height={600}
                    />
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-96 text-center">
                    <Brain className="h-16 w-16 text-gray-300 mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      No Research Report Yet
                    </h3>
                    <p className="text-gray-600 mb-6 max-w-md">
                      Generate a comprehensive research report using OpenAI's o3-deep-research model. 
                      This will provide detailed academic insights, real-world examples, and teaching resources.
                    </p>
                    
                    {researchStatus?.status === "pending" || researchStatus?.status === "in_progress" ? (
                      <div className="text-center">
                        <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2 text-blue-500" />
                        <p className="text-sm text-gray-600">
                          Research in progress... This typically takes 5-15 minutes.
                        </p>
                      </div>
                    ) : (
                      <Button
                        onClick={handleGenerateResearch}
                        disabled={isGenerating || !course.curriculum_content || !course.pedagogy_content}
                        size="lg"
                      >
                        {isGenerating ? (
                          <>
                            <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                            Starting Research...
                          </>
                        ) : (
                          <>
                            <Zap className="h-5 w-5 mr-2" />
                            Start Deep Research
                          </>
                        )}
                      </Button>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Navigation */}
        <div className="flex justify-between pt-6 border-t mt-6">
          <Button
            variant="outline"
            onClick={() => router.push(`/courses/create/${courseId}/pedagogy`)}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Pedagogy
          </Button>
          <Button
            onClick={() => router.push("/courses")}
            className="bg-green-600 hover:bg-green-700"
          >
            <CheckCircle className="h-4 w-4 mr-2" />
            Complete & Return to Courses
          </Button>
        </div>

        {/* Real-time Agent Conversation */}
        {isGeneratingSlides && (
          <div className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center">
                  <Sparkles className="h-5 w-5 mr-2" />
                  Live Agent Conversation
                </CardTitle>
                <CardDescription>
                  Watch the AI agents collaborate in real-time to create your slides
                </CardDescription>
              </CardHeader>
              <CardContent>
                {/* Progress Bar */}
                {generationProgress && (
                  <div className="mb-4">
                    <div className="flex justify-between text-sm text-gray-600 mb-2">
                      <span>{generationProgress.description}</span>
                      <span>{generationProgress.current} / {generationProgress.total}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${(generationProgress.current / generationProgress.total) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                )}

                {/* Agent Messages */}
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {agentMessages.length === 0 ? (
                    <div className="text-center py-8">
                      <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2 text-blue-500" />
                      <p className="text-sm text-gray-600">Waiting for agents to start conversation...</p>
                    </div>
                  ) : (
                    agentMessages.map((message, index) => (
                      <div key={index} className="border-l-4 border-blue-400 pl-4 py-2 bg-blue-50 rounded-r-lg">
                        <div className="flex items-center justify-between mb-1">
                          <div className="flex items-center">
                            <span className="font-medium text-blue-800">{message.agent_name}</span>
                            <span className="text-xs text-blue-600 ml-2">({message.agent_role})</span>
                          </div>
                          <span className="text-xs text-gray-500">Step {message.step}</span>
                        </div>
                        <p className="text-sm text-gray-700">{message.message}</p>
                      </div>
                    ))
                  )}
                </div>

                {/* WebSocket Status */}
                <div className="mt-4 pt-4 border-t">
                  <div className="flex items-center text-xs text-gray-600">
                    {websocket ? (
                      <>
                        <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                        Connected to real-time updates
                      </>
                    ) : (
                      <>
                        <div className="w-2 h-2 bg-red-500 rounded-full mr-2"></div>
                        Disconnected from real-time updates
                      </>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Info Section */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <h3 className="font-medium text-blue-900 mb-2">About Deep Research</h3>
          <p className="text-sm text-blue-700">
            The deep research feature uses OpenAI's o3-deep-research model to conduct comprehensive academic research 
            for your course. It analyzes your curriculum and pedagogy to provide detailed insights, real-world examples, 
            academic sources, and teaching recommendations that can be used for slide generation and course development.
          </p>
        </div>
      </div>
    </DashboardLayout>
  )
}
