"use client"

import { useEffect, useState, use, useRef } from "react"
import { DashboardLayout } from "@/components/layout/dashboard-layout"
import { Bot } from "lucide-react"
import { CourseStructure } from "../components/course-structure"
import { FilePreview } from "../components/file-preview"
import { ChatInterface } from "../components/chat-interface"
import { useRouter } from "next/navigation"
import { courseFileOperations } from "@/lib/courseFileStore"

interface ProgressData {
  type: 'research' | 'generation'
  completed: number
  total: number
  currentTask?: string
  currentPhase?: string
  estimatedTimeRemaining?: string
  totalWords?: number
  totalSections?: number
  overallProgress?: number
  sources?: Array<{
    id: string
    title: string
    description: string
    status: 'pending' | 'active' | 'complete'
    duration?: string
    progress?: number
    icon?: React.ReactNode
  }>
  phases?: Array<{
    id: string
    title: string
    description: string
    status: 'pending' | 'active' | 'complete'
    progress?: number
    wordsGenerated?: number
    icon?: React.ReactNode
  }>
}

interface FileData {
  id: string
  name: string
  type: 'file' | 'folder' | 'progress'
  content?: string
  fileType?: 'markdown' | 'image' | 'pdf' | 'slide-template' | 'research-progress' | 'generation-progress'
  isR2File?: boolean
  url?: string // R2 URL for fetching content
  progressData?: ProgressData
  targetedChange?: {
    type: string
    target: string
    replacement: string
    description: string
    coordinates?: {
      start_line: number
      end_line: number
      exact_text_to_replace: string
      replacement_text: string
    }
    status?: 'highlighting' | 'completed'
  }
}

interface Course {
  id: string
  name: string
  description?: string
  status: string
  structure: Record<string, unknown>
  curriculum_public_url?: string
  course_design_public_url?: string
  research_public_url?: string
  research_r2_key?: string
  research_updated_at?: string
  cover_image_public_url?: string
  cover_image_r2_key?: string
  cover_image_updated_at?: string
}

export default function CourseChat({ params }: { params: Promise<{ courseId: string }> }) {
  const resolvedParams = use(params)
  const [selectedFile, setSelectedFile] = useState<FileData | null>(null)
  const [course, setCourse] = useState<Course | null>(null)
  const [messages, setMessages] = useState<Array<Record<string, unknown>>>([])
  const [loading, setLoading] = useState(true)
  const [successMessage, setSuccessMessage] = useState<string>('')
  const [successMessageTimestamp, setSuccessMessageTimestamp] = useState<number>(0)
  const isLoadingCourse = useRef(false)
  const researchCompletedRef = useRef(false) // Prevent infinite loops
  const lastUpdateRef = useRef<string>('')
  const updateThrottleRef = useRef<NodeJS.Timeout | null>(null)
  const router = useRouter()

  // Cleanup timeouts on unmount
  useEffect(() => {
    return () => {
      if (updateThrottleRef.current) {
        clearTimeout(updateThrottleRef.current)
      }
    }
  }, [])

  useEffect(() => {
    if (!isLoadingCourse.current) {
      isLoadingCourse.current = true
      loadCourseAndMessages()
    }
  }, [resolvedParams.courseId])

  // Set up file store listener to sync selectedFile with course file store
  useEffect(() => {
    const unsubscribe = courseFileOperations.subscribe(() => {
      const selectedNode = courseFileOperations.getSelectedNode()
      if (selectedNode) {
        // Additional validation: don't set selectedFile for images without URLs
        if (selectedNode.fileType === 'image' && !selectedNode.url) {
          return
        }
        
        setSelectedFile({
          id: selectedNode.id,
          name: selectedNode.name,
          type: 'file',
          content: selectedNode.content || '',
          fileType: selectedNode.fileType || 'markdown',
          isR2File: selectedNode.source === 'r2',
          url: selectedNode.url, // Ensure URL is passed for image display
          displayTitle: selectedNode.displayTitle, // Pass through displayTitle
          materialId: selectedNode.materialId, // Pass through materialId
          status: selectedNode.status // Pass through status for assessment detection
        } as FileData & Record<string, unknown>) // Cast to allow additional properties
      }
    })

    return unsubscribe
  }, [])

  const loadCourseAndMessages = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      if (!token) {
        router.push('/auth/signin')
        return
      }

      // First restore workflow context to determine current state
      const workflowResponse = await fetch(`http://localhost:8000/courses/${resolvedParams.courseId}/restore-workflow`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      let workflowContext = null
      let shouldAutoTriggerStreaming = false
      let streamingType = null
      
      if (workflowResponse.ok) {
        workflowContext = await workflowResponse.json()
        
        // Handle workflow restoration results
        if (workflowContext.success) {
          const nextAction = workflowContext.next_action
          
          // Check if we should auto-trigger streaming based on current step and available files
          const availableFiles = workflowContext.restoration_context?.available_files || {}
          
          if (nextAction.auto_trigger) {
            if (nextAction.next_step === 'initial_research' && !availableFiles.research) {
              shouldAutoTriggerStreaming = true
              streamingType = 'research'
            } else if (nextAction.next_step === 'course_design_generation' && !availableFiles.course_design) {
              shouldAutoTriggerStreaming = true
              streamingType = 'course_design'
            }
          }
        }
      } else {
        // Failed to restore workflow context - continue with normal flow
      }

      // Load course and messages in parallel
      const [courseResponse, messagesResponse] = await Promise.all([
        fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/courses/${resolvedParams.courseId}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }),
        fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/courses/${resolvedParams.courseId}/messages`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })
      ])

      if (courseResponse.ok) {
        const courseData = await courseResponse.json()
        setCourse(courseData)
        
        // Initialize the course file store
        courseFileOperations.setCourseId(resolvedParams.courseId)
        courseFileOperations.initializeFromCourse(courseData)
      } else if (courseResponse.status === 401) {
        router.push('/auth/signin')
        return
      } else if (courseResponse.status === 404) {
        router.push('/courses/create')
        return
      } else {
        router.push('/courses/create')
        return
      }

      if (messagesResponse.ok) {
        const messagesData = await messagesResponse.json()
        setMessages(messagesData)
      } else if (messagesResponse.status === 404) {
        // Course exists but no messages yet - this is normal for new courses
        setMessages([])
      } else {
        setMessages([])
      }

      // Auto-trigger streaming if workflow restoration indicates it should continue
      if (shouldAutoTriggerStreaming && streamingType) {
        setTimeout(() => {
          if (streamingType === 'research') {
            handleCurriculumStreaming(resolvedParams.courseId, '', 'research')
          } else if (streamingType === 'course_design') {
            handleCurriculumStreaming(resolvedParams.courseId, '')
          }
        }, 1000) // Small delay to ensure UI is ready
      }

      // Store workflow context for better intent classification
      if (workflowContext?.success) {
        const contextData = {
          courseId: resolvedParams.courseId,
          workflowState: workflowContext.workflow_state,
          nextAction: workflowContext.next_action,
          availableFiles: workflowContext.restoration_context?.available_files || {},
          suggestedMessage: workflowContext.restoration_context?.suggested_message
        }
        
        // Store in sessionStorage for the chat interface to use
        sessionStorage.setItem(`workflow_context_${resolvedParams.courseId}`, JSON.stringify(contextData))
      }

    } catch {
      router.push('/courses/create')
    } finally {
      setLoading(false)
    }
  }

  const handleCourseCreated = (courseId: string, courseName: string) => {
    // Update the course state with the new name
    setCourse(prev => prev ? { ...prev, name: courseName } : null)
    
    // Refresh course data to get the latest information including cover image
    setTimeout(async () => {
      try {
        const token = localStorage.getItem('auth_token')
        const courseResponse = await fetch(`http://localhost:8000/courses/${courseId}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          cache: 'no-store'
        })
        if (courseResponse.ok) {
          const courseData = await courseResponse.json()
          setCourse(courseData)
          
          // Reinitialize store with updated course data
          courseFileOperations.initializeFromCourse(courseData)
        }
      } catch {
        // Failed to refresh course data
      }
    }, 2000) // Wait 2 seconds for backend to complete image generation
  }

  const handleCurriculumStreaming = async (courseId: string, focus?: string, modificationType?: string) => {
    // Determine the type of streaming
    const isResearch = modificationType === 'research'
    const isModification = modificationType === 'modification'
    const endpoint = isResearch ? 'generate-research' : 
                    isModification ? 'modify-course-design' : 'generate-course-design'
    
    // Reset refs to prevent infinite loops
    researchCompletedRef.current = false
    lastUpdateRef.current = ''
    if (updateThrottleRef.current) {
      clearTimeout(updateThrottleRef.current)
      updateThrottleRef.current = null
    }

    // Show research progress UI immediately when research streaming starts in normal mode
    if (isResearch) {
      const initialResearchProgressFile: FileData = {
        id: 'research-progress-initial',
        name: 'Research Progress',
        type: 'progress',
        fileType: 'research-progress',
        progressData: {
          type: 'research',
          completed: 0,
          total: 0, // Will be updated by backend events with actual total
          currentTask: 'Initializing research analysis...',
          estimatedTimeRemaining: undefined,
          sources: []
        }
      }
      setSelectedFile(initialResearchProgressFile)
    }

    try {
      const token = localStorage.getItem('auth_token')
      
      const requestBody = isResearch
        ? { focus_area: focus }
        : isModification 
        ? { modification_request: focus || 'Apply requested modifications' }
        : { focus }
      
      const requestHeaders = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
      
      // Add timeout to prevent hanging requests
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 60000) // 60 second timeout
      
      const response = await fetch(`http://localhost:8000/courses/${courseId}/${endpoint}`, {
        method: 'POST',
        headers: requestHeaders,
        body: JSON.stringify(requestBody),
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`HTTP ${response.status}: ${errorText}`)
      }

      if (response.ok) {
        const reader = response.body?.getReader()
        const decoder = new TextDecoder()
        let fullContent = ''
        let researchContent = ''
        let originalContent = ''
        let hasSetResearchFile = false
        let hasSetCourseDesignFile = false
        // Fallback control for auto-trigger to structure
        let designCompleted = false
        let structureFallbackTimer: NodeJS.Timeout | null = null

        // For modifications, we need to preserve the original content
        if (isModification) {
          try {
            const token = localStorage.getItem('auth_token')
            const courseResponse = await fetch(`http://localhost:8000/courses/${courseId}`, {
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
              }
            })
            if (courseResponse.ok) {
              const courseData = await courseResponse.json()
              if (courseData.course_design_public_url) {
                const contentResponse = await fetch(courseData.course_design_public_url)
                if (contentResponse.ok) {
                  originalContent = await contentResponse.text()
                  fullContent = originalContent
                }
              }
            }
          } catch {
            // Failed to get original content for modification
          }
        }

        if (reader) {
          while (true) {
            const { done, value } = await reader.read()
            if (done) break

            const chunk = decoder.decode(value)
            const lines = chunk.split('\n')

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const jsonStr = line.slice(6).trim()
                  
                  // Skip empty lines
                  if (!jsonStr) {
                    continue
                  }
                  
                  // Skip malformed JSON lines
                  if (jsonStr === '{}' || !jsonStr.startsWith('{') || !jsonStr.endsWith('}')) {
                    continue
                  }
                  
                  // Parse with error handling
                  let data
                  try {
                    data = JSON.parse(jsonStr)
                  } catch {
                    continue
                  }

                  // Handle both new and legacy research/content streaming events
                  if (data.type === 'start') {
                    if (data.file_type === 'research' && !hasSetResearchFile) {
                      // Create research.md file in store
                      hasSetResearchFile = true
                      courseFileOperations.upsertFile('/research.md', {
                        fileType: 'markdown',
                        status: 'streaming',
                        source: 'stream',
                        content: ''
                      })
                      courseFileOperations.setSelectedPath('/research.md')
                    } else if (data.file_type !== 'research' && !hasSetCourseDesignFile) {
                      // Create course-design.md file in store
                      hasSetCourseDesignFile = true
                      const initialContent = isModification && originalContent ? 
                        originalContent + '\n\n---\n\n' + (data.data?.content || data.content || 'Starting modification...') :
                        `# 🎯 Course Design Generation\n\n*Analyzing research findings and generating comprehensive course structure...*\n\n*Preparing comprehensive course design...*\n\n⏳ **Status:** Initializing course design generation\n\n📊 **Progress:** Preparing content based on latest research\n\n---\n\n*Content will appear here as it's generated...*`
                      
                      courseFileOperations.upsertFile('/course-design.md', {
                        fileType: 'markdown',
                        status: 'streaming',
                        source: 'stream',
                        content: initialContent
                      })
                      courseFileOperations.setSelectedPath('/course-design.md')
                    }
                  }
                  else if (data.type === 'research_progress') {
                    // Create or update research progress display
                    const progressMessage = data.message || `Conducting web search ${data.search_count || 0}...`
                    const isCompleted = data.status === 'completed'
                    
                    if (isCompleted) {
                      // Research is complete, switch to research.md file
                      courseFileOperations.setSelectedPath('/research.md')
                      const selectedNode = courseFileOperations.getSelectedNode()
                      if (selectedNode) {
                        setSelectedFile({
                          id: 'research-complete',
                          name: 'research.md',
                          type: 'file',
                          fileType: 'markdown',
                          content: selectedNode.content || ''
                        })
                      }
                    } else {
                      // Show research progress file with current status - use actual backend data
                      const researchProgressFile: FileData = {
                        id: 'research-progress',
                        name: 'Research Progress',
                        type: 'progress',
                        fileType: 'research-progress',
                        progressData: {
                          type: 'research',
                          completed: data.search_count || 0,
                          total: data.total_searches || Math.max(data.search_count || 0, 1), // Use backend total or at least current count
                          currentTask: progressMessage,
                          estimatedTimeRemaining: undefined,
                          sources: []
                        }
                      }
                      setSelectedFile(researchProgressFile)
                    }
                  }
                  else if (data.type === 'content') {
                    if (data.file_type === 'research') {
                      // Stream content to research.md in store
                      researchContent = data.full_content || researchContent
                      courseFileOperations.setContent('/research.md', researchContent)
                      
                      // Check if research streaming is complete
                      if (data.is_complete || data.final) {
                        courseFileOperations.finalizeFile('/research.md', { status: 'saved' })
                      }
                    } else {
                      // Stream content to course-design.md in store
                      fullContent = data.data?.full_content || data.full_content || fullContent
                      courseFileOperations.setContent('/course-design.md', fullContent)
                      
                      // Check if course design streaming is complete
                      if (data.is_complete || data.final) {
                        courseFileOperations.finalizeFile('/course-design.md', { status: 'saved' })
                      }
                    }
                  }
                  // LEGACY EVENT HANDLERS - Handle old research events and convert them to research.md
                  else if (data.type === 'research_start') {
                    // Create research.md file in store immediately
                    const initialContent = `# 🔬 Research Analysis\n\n<div style="display: flex; align-items: center; gap: 8px; margin: 16px 0;">\n  <div style="width: 20px; height: 20px; border: 2px solid #e5e7eb; border-top: 2px solid #3b82f6; border-radius: 50%; animation: spin 1s linear infinite;"></div>\n  <em>Starting comprehensive research analysis...</em>\n</div>\n\n<style>\n@keyframes spin {\n  0% { transform: rotate(0deg); }\n  100% { transform: rotate(360deg); }\n}\n</style>\n\n`
                    
                    courseFileOperations.upsertFile('/research.md', {
                      fileType: 'markdown',
                      status: 'streaming',
                      source: 'stream',
                      content: initialContent
                    })
                    
                    // Also set selected file for backward compatibility
                    const researchFile: FileData = {
                      id: 'research-streaming',
                      name: 'research.md',
                      type: 'file',
                      content: initialContent,
                      fileType: 'markdown'
                    }
                    setSelectedFile(researchFile)
                  }
                  else if (data.type === 'research_content') {
                    const researchChunk = data.content || ''
                    const fullResearch = data.full_research || ''
                    
                    // Update store with research content
                    if (fullResearch) {
                      courseFileOperations.setContent('/research.md', fullResearch)
                    } else if (researchChunk) {
                      courseFileOperations.appendContent('/research.md', researchChunk)
                    }
                    
                    // Throttle updates to prevent infinite loops
                    const contentHash = fullResearch || (selectedFile?.content + researchChunk)
                    if (lastUpdateRef.current === contentHash) {
                      continue // Skip duplicate content
                    }
                    lastUpdateRef.current = contentHash
                    
                    // Clear any existing throttle
                    if (updateThrottleRef.current) {
                      clearTimeout(updateThrottleRef.current)
                    }
                    
                    // Throttle the update to prevent rapid state changes
                    updateThrottleRef.current = setTimeout(() => {
                      setSelectedFile(prev => prev ? {
                        ...prev,
                        id: 'research-streaming',
                        name: 'research.md',
                        type: 'file',
                        fileType: 'markdown',
                        content: fullResearch || (prev.content + researchChunk)
                      } : null)
                    }, 50) // 50ms throttle
                  }
                  else if (data.type === 'research_findings') {
                    // Prevent infinite loops during research completion
                    if (researchCompletedRef.current) {
                      continue
                    }
                    researchCompletedRef.current = true
                    
                    const findings = data.full_findings || data.content || ''
                    
                    // Complete the research.md file WITHOUT transition message (Issue 2 fix)
                    const completedResearchContent = findings + '\n\n---\n\n✅ **Research Analysis Complete**'
                    const researchFile: FileData = {
                      id: 'research-complete',
                      name: 'research.md',
                      type: 'file',
                      fileType: 'markdown',
                      content: completedResearchContent
                    }
                    
                    // Use setTimeout to prevent rapid state updates that cause infinite loops
                    setTimeout(() => {
                      // Add research.md to store
                      courseFileOperations.upsertFile('/research.md', {
                        fileType: 'markdown',
                        status: 'saved',
                        source: 'stream',
                        content: completedResearchContent
                      })
                      
                      // Keep research file selected for now
                      setSelectedFile(researchFile)
                      
                      // Trigger immediate course data refresh for research completion
                      const refreshCourseDataForResearch = async (retryCount = 0) => {
                        try {
                          const token = localStorage.getItem('auth_token')
                          const courseResponse = await fetch(`http://localhost:8000/courses/${resolvedParams.courseId}`, {
                            headers: {
                              'Authorization': `Bearer ${token}`,
                              'Content-Type': 'application/json'
                            }
                          })
                          if (courseResponse.ok) {
                            const courseData = await courseResponse.json()
                            setCourse(courseData)
                            
                            // Reinitialize store with updated course data
                            courseFileOperations.initializeFromCourse(courseData)
                            return true
                          } else {
                            if (retryCount < 3) {
                              const delay = retryCount === 0 ? 300 : 1000 * (retryCount + 1)
                              setTimeout(() => refreshCourseDataForResearch(retryCount + 1), delay)
                            }
                            return false
                          }
                        } catch {
                          if (retryCount < 3) {
                            const delay = retryCount === 0 ? 300 : 1000 * (retryCount + 1)
                            setTimeout(() => refreshCourseDataForResearch(retryCount + 1), delay)
                          }
                          return false
                        }
                      }
                      
                      // Start refresh after a short delay to allow backend to complete
                      setTimeout(() => refreshCourseDataForResearch(), 500)
                    }, 100)
                  }
                  else if (data.type === 'generation_start') {
                    // Create course-design.md file in store if not already created
                    if (!hasSetCourseDesignFile) {
                      hasSetCourseDesignFile = true
                      const initialContent = `# 🎯 Course Design Generation\n\n*Analyzing research findings and generating comprehensive course structure...*\n\n*Preparing comprehensive course design...*\n\n⏳ **Status:** Initializing course design generation\n\n📊 **Progress:** Preparing content based on latest research\n\n---\n\n*Content will appear here as it's generated...*`
                      
                      courseFileOperations.upsertFile('/course-design.md', {
                        fileType: 'markdown',
                        status: 'streaming',
                        source: 'stream',
                        content: initialContent
                      })
                      courseFileOperations.setSelectedPath('/course-design.md')
                    }
                    
                    const generationFile: FileData = {
                      id: 'generation-progress',
                      name: 'Course Generation',
                      type: 'progress',
                      fileType: 'generation-progress',
                      progressData: {
                        type: 'generation',
                        completed: 0,
                        total: data.data?.total_phases || 6,
                        currentPhase: data.data?.current_phase || 'Starting generation...',
                        totalWords: 0,
                        totalSections: 0,
                        overallProgress: 0,
                        phases: []
                      }
                    }
                    setSelectedFile(generationFile)
                  }
                  else if (data.type === 'complete') {
                    // Determine if this is the CourseStructureAgent completion or CourseDesignAgent completion
                    const isStructureComplete = !!(data.structure_data)
                    
                    if (isStructureComplete) {
                      // Cancel any pending fallback timer
                      if (structureFallbackTimer) {
                        clearTimeout(structureFallbackTimer)
                        structureFallbackTimer = null
                      }
                      
                      // Structure generation completed - real-time events handled via SSE
                      
                      // Load final content materials to ensure UI is up to date
                      try {
                        await courseFileOperations.loadContentMaterials(courseId)
                      } catch {
                        console.error('Failed to reload content materials')
                      }
                      
                      // Surface structure completion to chat via success message props
                      setSuccessMessage(
                        "✅ **Content Structure Generated!**\n\nYour comprehensive content structure has been created with detailed checklists for all course materials. The structure includes:\n\n- Module and chapter breakdown\n- Individual slide content items\n- Assessment and quiz materials\n- Learning objectives and outcomes\n\nWould you like to **approve** this structure and proceed with individual content creation, or would you like to **modify** anything?"
                      )
                      setSuccessMessageTimestamp(Date.now())
                      break
                    } else {
                      // Course design completed
                      
                      // Finalize files in store
                      courseFileOperations.finalizeFile('/course-design.md', { 
                        status: 'saved'
                      })
                      
                      const completionMessage = data.data?.content || data.content || 'Course design completed successfully!'
                      setSuccessMessage(completionMessage)
                      setSuccessMessageTimestamp(Date.now())
                      
                      // Immediate course data refresh with aggressive retry mechanism
                      const refreshCourseData = async (retryCount = 0) => {
                        try {
                          const token = localStorage.getItem('auth_token')
                          const courseResponse = await fetch(`http://localhost:8000/courses/${resolvedParams.courseId}`, {
                            headers: {
                              'Authorization': `Bearer ${token}`,
                              'Content-Type': 'application/json'
                            },
                            cache: 'no-store'
                          })
                          if (courseResponse.ok) {
                            const courseData = await courseResponse.json()
                            setCourse(courseData)
                            
                            // Reinitialize store with updated course data (including R2 URLs)
                            courseFileOperations.initializeFromCourse(courseData)
                            return true // Success
                          } else {
                            // Retry up to 5 times with shorter, more aggressive intervals
                            if (retryCount < 5) {
                              const delay = retryCount === 0 ? 500 : Math.min(1000 * Math.pow(1.5, retryCount), 5000)
                              setTimeout(() => refreshCourseData(retryCount + 1), delay)
                            }
                            return false
                          }
                        } catch {
                          // Retry up to 5 times with shorter, more aggressive intervals
                          if (retryCount < 5) {
                            const delay = retryCount === 0 ? 500 : Math.min(1000 * Math.pow(1.5, retryCount), 5000)
                            setTimeout(() => refreshCourseData(retryCount + 1), delay)
                          }
                          return false
                        }
                      }
                      
                      // Start refresh immediately with minimal delay
                      setTimeout(() => refreshCourseData(), 200)

                      // Mark design complete - no fallback needed as backend handles workflow transitions
                      designCompleted = true
                      
                      // Keep stream open after course design completion to allow auto-triggered structure events.
                      // The backend streaming route will close the stream when finished, so we safely continue reading.
                    }
                  }
                  else if (data.type === 'error') {
                    setSelectedFile(prev => prev ? {
                      ...prev,
                      content: `❌ Error: ${data.data?.content || data.content || 'Unknown error occurred'}`
                    } : null)
                    break
                  }
                } catch {
                  // Error parsing stream event
                }
              }
            }
          }
        }
      } else {
        const errorText = await response.text()
        setSelectedFile(prev => prev ? {
          ...prev,
          content: `❌ Failed to ${isModification ? 'modify' : 'generate'} course design. Status: ${response.status}\nError: ${errorText}`
        } : null)
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error)
      
      setSelectedFile(prev => prev ? {
        ...prev,
        content: `❌ Failed to ${isModification ? 'modify' : 'generate'} curriculum. Error: ${errorMessage}\n\nPlease try again.`
      } : null)
    }
  }

  if (loading) {
    return (
      <DashboardLayout 
        title="Loading..." 
        icon={Bot}
        showBackButton={true}
        backUrl="/courses"
        backLabel="Back to Courses"
      >
        <div className="flex items-center justify-center h-full">
          <div className="text-gray-500">Loading course...</div>
        </div>
      </DashboardLayout>
    )
  }

  if (!course) {
    return (
      <DashboardLayout 
        title="Course Not Found" 
        icon={Bot}
        showBackButton={true}
        backUrl="/courses"
        backLabel="Back to Courses"
      >
        <div className="flex items-center justify-center h-full">
          <div className="text-gray-500">Course not found</div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout 
      title={`Course Copilot - ${course.name}`}
      icon={Bot}
      showBackButton={true}
      backUrl="/courses"
      backLabel="Back to Courses"
    >
      <div className="flex-1 min-h-0 grid grid-cols-[300px_1fr_400px] gap-6 overflow-hidden">
        {/* Course Structure - Left Column */}
        <div className="bg-white rounded-lg border shadow-sm h-full overflow-hidden">
          <CourseStructure 
            onFileSelect={setSelectedFile} 
            course={course}
          />
        </div>

        {/* File Preview - Center Column */}
        <div className="bg-white rounded-lg border shadow-sm h-full overflow-hidden">
          <FilePreview 
            selectedFile={selectedFile} 
            onFileUpdate={(updatedFile) => {
              setSelectedFile(updatedFile)
            }}
          />
        </div>

        {/* Chat Interface - Right Column */}
        <div className="bg-white rounded-lg border shadow-sm h-full overflow-hidden">
          <ChatInterface 
            courseId={resolvedParams.courseId}
            courseName={course.name}
            onCourseCreated={handleCourseCreated}
            initialMessages={messages}
            onCurriculumStreaming={(courseId: string, focus?: string, modificationType?: string) => {
              const result = handleCurriculumStreaming(courseId, focus, modificationType)
              return result
            }}
            successMessage={successMessage}
            successMessageTimestamp={successMessageTimestamp}
          />
        </div>
      </div>
    </DashboardLayout>
  )
}
