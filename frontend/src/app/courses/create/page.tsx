"use client"

import { DashboardLayout } from "@/components/layout/dashboard-layout"
import { Bot } from "lucide-react"
import { CourseStructure } from "./components/course-structure"
import { FilePreview } from "./components/file-preview"
import { ChatInterface } from "./components/chat-interface"
import { useState, useEffect, useRef, useCallback } from "react"
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
  progressData?: ProgressData
  researchProgress?: {
    isActive: boolean
    currentSource: string
    currentUrl: string
    searchCount: number
    totalSearches: number
  }
}

interface Course extends Record<string, unknown> {
  id: string
  name: string
  description?: string
  status: string
  structure: Record<string, unknown>
  course_design_public_url?: string
}

export default function CreateCourse() {
  const [selectedFile, setSelectedFile] = useState<FileData | null>(null)
  const [courseName, setCourseName] = useState<string>("")
  const [course, setCourse] = useState<Course | null>(null)
  const [successMessage, setSuccessMessage] = useState<string>('')
  const [successMessageTimestamp, setSuccessMessageTimestamp] = useState<number>(0)
  const [generatedFiles, setGeneratedFiles] = useState<{[key: string]: FileData}>({}) // Track all generated files
  const router = useRouter()
  
  // Use refs to prevent infinite loops during streaming
  const isStreamingRef = useRef(false)
  const researchCompletedRef = useRef(false)
  const lastUpdateRef = useRef<string>('')
  const updateThrottleRef = useRef<NodeJS.Timeout | null>(null)

  // Cleanup throttle timeout on unmount
  useEffect(() => {
    return () => {
      if (updateThrottleRef.current) {
        clearTimeout(updateThrottleRef.current)
      }
    }
  }, [])

  // Load existing course data if courseId is in URL
  useEffect(() => {
    const loadExistingCourse = async () => {
      const currentPath = window.location.pathname
      const courseIdMatch = currentPath.match(/\/courses\/create\/([a-f0-9]{24})/)
      
      if (courseIdMatch) {
        const courseId = courseIdMatch[1]
        
        try {
          const token = localStorage.getItem('auth_token')
          if (!token) {
            router.push('/auth/signin')
            return
          }

          const courseResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/courses/${courseId}`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          })

          if (courseResponse.ok) {
            const courseData = await courseResponse.json()
            
            setCourse(courseData)
            setCourseName(courseData.name)
            
            // Initialize the course file store
            courseFileOperations.setCourseId(courseId)
            courseFileOperations.initializeFromCourse(courseData)
            
            
            // Auto-select the first available file
            if (courseData.course_design_public_url) {
              // Fetch the course design content
              try {
                const contentResponse = await fetch(courseData.course_design_public_url)
                if (contentResponse.ok) {
                  const content = await contentResponse.text()
                  const courseDesignFile = {
                    id: 'course-design-existing',
                    name: 'course-design.md',
                    type: 'file' as const,
                    content: content,
                    fileType: 'markdown' as const
                  }
                  setSelectedFile(courseDesignFile)
                }
              } catch (error) {
                console.error('Failed to fetch course design content:', error)
                // Fallback: create file with URL as placeholder
                const courseDesignFile = {
                  id: 'course-design-existing',
                  name: 'course-design.md',
                  type: 'file' as const,
                  content: `# ${courseData.name}\n\nLoading course design content...`,
                  fileType: 'markdown' as const
                }
                setSelectedFile(courseDesignFile)
              }
            }
          } else if (courseResponse.status === 404) {
            // Course not found, redirect to create page
            router.push('/courses/create')
          } else if (courseResponse.status === 401) {
            // Unauthorized, redirect to signin
            router.push('/auth/signin')
          }
        } catch (error) {
          console.error('Failed to load existing course:', error)
        }
      } else {
        // No courseId in URL - this is a fresh course creation session
        // Clear any existing course data and reset the store
        courseFileOperations.clear()
        setCourse(null)
        setCourseName("")
        setSelectedFile(null)
      }
    }

    loadExistingCourse()
  }, [router])

  const handleCourseCreated = (courseId: string, name: string) => {
    setCourseName(name)
    // Use replace instead of push to avoid flicker, and update URL without full page reload
    window.history.replaceState(null, '', `/courses/create/${courseId}`)
    
    // Initialize the course file store for new courses
    courseFileOperations.setCourseId(courseId)
  }

  const handleCurriculumStreaming = async (courseId: string, focus?: string, modificationType?: string) => {
    
    // Don't set initial file - let the streaming events handle file creation
    // This prevents showing "Initializing Course Design..." when research starts first

    try {
      const token = localStorage.getItem('auth_token')
      
      // Determine the correct endpoint based on modification type
      let endpoint = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/courses/${courseId}/generate-course-design`
      let requestBody: Record<string, unknown> = { focus }
      
      if (modificationType === 'research') {
        endpoint = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/courses/${courseId}/generate-research`
        requestBody = { focus_area: focus }
      } else if (modificationType === 'modification') {
        endpoint = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/courses/${courseId}/modify-course-design`
        requestBody = { modification_request: focus }
      } else {
      }
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      })
      
      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`HTTP ${response.status}: ${errorText}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let fullContent = ''

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
                
                if (!jsonStr || jsonStr === '{}' || !jsonStr.startsWith('{') || !jsonStr.endsWith('}')) {
                  continue
                }
                
                let data
                try {
                  data = JSON.parse(jsonStr)
                } catch (parseError) {
                  continue
                }

                // Handle new research_progress events (Issue 1 & 2 fix)
                if (data.type === 'research_progress') {
                  // Update the file-preview component's research progress state
                  // This will show the blue loader with meaningful source information
                  // Update ANY research.md file, regardless of current selection
                  if (selectedFile && (selectedFile.name === 'research.md' || selectedFile.id.includes('research'))) {
                    setSelectedFile(prev => prev ? {
                      ...prev,
                      // Don't update content - keep existing content without progress messages
                      // The TrueWYSIWYGEditor will handle showing the loader based on this event
                      researchProgress: {
                        isActive: data.status === 'searching', // Hide loader when status is 'completed'
                        currentSource: data.current_source || `Web Search ${data.search_count}`,
                        currentUrl: data.message || 'Searching for latest information...',
                        searchCount: data.search_count || 0,
                        totalSearches: data.total_searches || 30
                      }
                    } : null)
                  }
                }
                // Handle workflow transition events from orchestrator
                else if (data.type === 'workflow_transition') {
                  
                  // Show transition message in chat or as a temporary file
                  const transitionFile: FileData = {
                    id: 'workflow-transition',
                    name: 'Workflow Transition',
                    type: 'progress',
                    fileType: 'generation-progress',
                    content: data.content || 'Transitioning to next workflow step...',
                    progressData: {
                      type: 'generation',
                      completed: 0,
                      total: 1,
                      currentPhase: data.content || 'Starting course design generation...',
                      totalWords: 0,
                      totalSections: 0,
                      overallProgress: 0,
                      phases: []
                    }
                  }
                  setSelectedFile(transitionFile)
                }
                // Handle both new and legacy research/content streaming events
                else if (data.type === 'start') {
                  
                  if (data.file_type === 'research') {
                    // Create research.md file in store
                    courseFileOperations.upsertFile('/research.md', {
                      fileType: 'markdown',
                      status: 'streaming',
                      source: 'stream',
                      content: ''
                    })
                    
                    // Auto-select research.md when it starts streaming
                    courseFileOperations.autoSelectStreamingFile('/research.md')
                    
                    const researchFile: FileData = {
                      id: 'research-streaming',
                      name: 'research.md',
                      type: 'file',
                      content: '',
                      fileType: 'markdown'
                    }
                    setSelectedFile(researchFile)
                  } else {
                    // Create course-design.md file in store
                    
                    // Get research content if available for context
                    const researchContext = (window as unknown as Record<string, unknown>).researchContent ? 
                      '\n\n*Building upon comprehensive research findings...*\n\n' : 
                      '\n\n*Preparing comprehensive course design...*\n\n'
                    
                    const initialContent = `# 🎯 Course Design Generation\n\n*Analyzing research findings and generating comprehensive course structure...*${researchContext}⏳ **Status:** Initializing course design generation\n\n📊 **Progress:** Preparing content based on latest research\n\n---\n\n*Content will appear here as it's generated...*`
                    
                    courseFileOperations.upsertFile('/course-design.md', {
                      fileType: 'markdown',
                      status: 'streaming',
                      source: 'stream',
                      content: initialContent
                    })
                    
                    // Auto-select course-design.md when it starts streaming (Issue 2 fix)
                    courseFileOperations.autoSelectStreamingFile('/course-design.md')
                    
                    const courseDesignFile: FileData = {
                      id: 'course-design-streaming',
                      name: 'course-design.md',
                      type: 'file',
                      content: initialContent,
                      fileType: 'markdown'
                    }
                    setSelectedFile(courseDesignFile)
                  }
                }
                else if (data.type === 'content') {
                  
                  if (data.file_type === 'research') {
                    // Stream content to research.md in store
                    fullContent = data.full_content || fullContent
                    courseFileOperations.setContent('/research.md', fullContent)
                    
                    setSelectedFile(prev => prev ? {
                      ...prev,
                      id: 'research-streaming',
                      name: 'research.md',
                      type: 'file',
                      fileType: 'markdown',
                      content: fullContent
                    } : null)
                  } else {
                    // Stream content to course-design.md in store
                    fullContent = data.data?.full_content || data.full_content || fullContent
                    courseFileOperations.setContent('/course-design.md', fullContent)
                    
                    // If we're in generation progress mode, update the progress based on content
                    if (selectedFile?.type === 'progress' && selectedFile?.fileType === 'generation-progress') {
                      const wordCount = fullContent.split(/\s+/).length
                      const sectionCount = (fullContent.match(/^##?\s/gm) || []).length
                      const estimatedTotalWords = 3000
                      const currentProgress = Math.min(Math.floor((wordCount / estimatedTotalWords) * 6), 5)
                      
                      // Only update if progress has actually changed
                      if (selectedFile.progressData && (currentProgress > selectedFile.progressData.completed || wordCount > (selectedFile.progressData.totalWords || 0))) {
                        setSelectedFile(prev => prev && prev.progressData ? {
                          ...prev,
                          progressData: {
                            ...prev.progressData,
                            completed: currentProgress,
                            totalWords: wordCount,
                            totalSections: sectionCount,
                            currentPhase: `Generating content... (${wordCount} words, ${sectionCount} sections)`,
                            overallProgress: Math.floor((wordCount / estimatedTotalWords) * 100)
                          }
                        } : prev)
                      }
                    } else {
                      // Switch to file view when content is substantial
                      setSelectedFile(prev => prev ? {
                        ...prev,
                        type: 'file',
                        fileType: 'markdown',
                        content: fullContent
                      } : null)
                    }
                  }
                }
                // LEGACY EVENT HANDLERS - Handle old research events and convert them to research.md
                else if (data.type === 'research_start') {
                  const researchFile: FileData = {
                    id: 'research-streaming',
                    name: 'research.md',
                    type: 'file',
                    content: `# 🔬 Research Analysis\n\n<div style="display: flex; align-items: center; gap: 8px; margin: 16px 0;">\n  <div style="width: 20px; height: 20px; border: 2px solid #e5e7eb; border-top: 2px solid #3b82f6; border-radius: 50%; animation: spin 1s linear infinite;"></div>\n  <em>Starting comprehensive research analysis...</em>\n</div>\n\n<style>\n@keyframes spin {\n  0% { transform: rotate(0deg); }\n  100% { transform: rotate(360deg); }\n}\n</style>\n\n`,
                    fileType: 'markdown'
                  }
                  setSelectedFile(researchFile)
                }
                else if (data.type === 'research_content') {
                  const researchChunk = data.content || ''
                  const fullResearch = data.full_research || ''
                  
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
                    setGeneratedFiles(prev => ({
                      ...prev,
                      'research.md': researchFile
                    }))
                    
                    // Keep research file selected for now
                    setSelectedFile(researchFile)
                    
                    // Store research content for later access
                    ;(window as unknown as Record<string, unknown>).researchContent = completedResearchContent
                  }, 100)
                }
                else if (data.type === 'generation_start') {
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
                else if (data.type === 'start') {
                  const generationFile: FileData = {
                    id: 'generation-progress',
                    name: 'Course Generation',
                    type: 'progress',
                    fileType: 'generation-progress',
                    progressData: {
                      type: 'generation',
                      completed: 0,
                      total: 6,
                      currentPhase: 'Starting generation...',
                      totalWords: 0,
                      totalSections: 0,
                      overallProgress: 0,
                      phases: []
                    }
                  }
                  setSelectedFile(generationFile)
                }
                else if (data.type === 'content') {
                  fullContent = data.data?.full_content || data.full_content || fullContent
                  
                  // If we're in generation progress mode, update the progress based on content
                  if (selectedFile?.type === 'progress' && selectedFile?.fileType === 'generation-progress') {
                    const wordCount = fullContent.split(/\s+/).length
                    const sectionCount = (fullContent.match(/^##?\s/gm) || []).length
                    const estimatedTotalWords = 3000
                    const currentProgress = Math.min(Math.floor((wordCount / estimatedTotalWords) * 6), 5)
                    
                    // Only update if progress has actually changed
                    if (selectedFile.progressData && (currentProgress > selectedFile.progressData.completed || wordCount > (selectedFile.progressData.totalWords || 0))) {
                      setSelectedFile(prev => prev && prev.progressData ? {
                        ...prev,
                        progressData: {
                          ...prev.progressData,
                          completed: currentProgress,
                          totalWords: wordCount,
                          totalSections: sectionCount,
                          currentPhase: `Generating content... (${wordCount} words, ${sectionCount} sections)`,
                          overallProgress: Math.floor((wordCount / estimatedTotalWords) * 100)
                        }
                      } : prev)
                    }
                  } else {
                    // Switch to file view when content is substantial
                    setSelectedFile(prev => prev ? {
                      ...prev,
                      type: 'file',
                      fileType: 'markdown',
                      content: fullContent
                    } : null)
                  }
                }
                else if (data.type === 'progress') {
                  const progressContent = data.data?.content || data.content || ''
                  
                  if (selectedFile?.type === 'progress' && selectedFile?.fileType === 'research-progress') {
                    setSelectedFile(prev => prev && prev.progressData ? {
                      ...prev,
                      progressData: {
                        ...prev.progressData,
                        currentTask: progressContent.replace('🌐 ', '').replace('✅ ', ''),
                        completed: progressContent.includes('✅') ? prev.progressData.completed + 1 : prev.progressData.completed,
                        estimatedTimeRemaining: progressContent.includes('sources analyzed') ? 
                          progressContent.match(/(\d+m \d+s)/)?.[1] : prev.progressData.estimatedTimeRemaining
                      }
                    } : prev)
                  } else {
                    setSelectedFile(prev => prev ? {
                      ...prev,
                      content: fullContent + '\n\n' + progressContent
                    } : null)
                  }
                }
                else if (data.type === 'complete') {
                  const isStructureComplete = !!(data.structure_data)
                  const hasAutoTransition =
                    !!(data.workflow_transition?.automatic ||
                       data.workflow_transition?.trigger_automatically ||
                       (data.workflow_transition?.next_agent === 'course_structure'))
                  
                  if (isStructureComplete) {
                    try {
                      await courseFileOperations.loadContentMaterials(courseId)
                    } catch (e) {
                      console.error('Failed to reload content materials:', e)
                    }
                    
                    setSuccessMessage(
                      "✅ Content Structure Generated!\n\nYour comprehensive content structure has been created with detailed checklists for all course materials. The structure includes:\n\n- Module and chapter breakdown\n- Individual slide content items\n- Assessment and quiz materials\n- Learning objectives and outcomes\n\nWould you like to approve this structure and proceed with individual content creation, or modify anything?"
                    )
                    setSuccessMessageTimestamp(Date.now())
                    break
                  } else {
                    const finalContent = data.data?.full_content || data.full_content || fullContent
                    
                    // Clear research progress state when any completion happens
                    setSelectedFile(prev => prev ? {
                      ...prev,
                      id: prev.name === 'research.md' ? 'research-complete' : 'curriculum-complete',
                      type: 'file',
                      fileType: 'markdown',
                      content: finalContent,
                      // Clear research progress state to hide blue loader
                      researchProgress: undefined
                    } : null)
                    
                    const completionMessage = data.data?.content || data.content || 'Course design completed successfully!'
                    setSuccessMessage(completionMessage)
                    setSuccessMessageTimestamp(Date.now())
                    
                    // Update URL without page reload to reflect the course ID
                    window.history.replaceState(null, '', `/courses/create/${courseId}`)
                    
                    // Refresh course data
                    setTimeout(async () => {
                      try {
                        const token = localStorage.getItem('auth_token')
                        const courseResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/courses/${courseId}`, {
                          headers: {
                            'Authorization': `Bearer ${token}`,
                            'Content-Type': 'application/json'
                          }
                        })
                        if (courseResponse.ok) {
                          const courseData = await courseResponse.json()
                          setCourse(courseData)
                          
                          if (courseData.course_design_public_url) {
                            const courseDesignFile = {
                              id: 'course-design-complete',
                              name: 'course-design.md',
                              type: 'file' as const,
                              content: finalContent,
                              fileType: 'markdown' as const
                            }
                            setSelectedFile(courseDesignFile)
                          }
                        }
                      } catch (error) {
                        console.error('Failed to refresh course data:', error)
                      }
                    }, 1000)
                    
                    // IMPORTANT: Do NOT break here; keep stream open to receive auto-triggered structure events
                  }
                }
                else if (data.type === 'error') {
                  console.error('Stream error:', data.data?.content || data.content)
                  setSelectedFile(prev => prev ? {
                    ...prev,
                    content: `❌ Error: ${data.data?.content || data.content || 'Unknown error occurred'}`
                  } : null)
                  break
                }
                else {
                  // Unhandled event type
                }
              } catch (e) {
                console.error('Error parsing stream event:', e, 'Line:', line)
              }
            }
          }
        }
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error)
      console.error('Stream handling error:', errorMessage)
      
      setSelectedFile(prev => prev ? {
        ...prev,
        content: `❌ Failed to generate curriculum. Error: ${errorMessage}\n\nPlease try again.`
      } : null)
    }
  }

  return (
    <DashboardLayout 
      title={courseName ? `Course Copilot - ${courseName}` : "Course Copilot"} 
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
            course={course || undefined}
          />
        </div>

        {/* File Preview - Center Column */}
        <div className="bg-white rounded-lg border shadow-sm h-full overflow-hidden">
          <FilePreview selectedFile={selectedFile} />
        </div>

        {/* Chat Interface - Right Column */}
        <div className="bg-white rounded-lg border shadow-sm h-full overflow-hidden">
          <ChatInterface 
            onCourseCreated={handleCourseCreated}
            onCurriculumStreaming={handleCurriculumStreaming}
            successMessage={successMessage}
            successMessageTimestamp={successMessageTimestamp}
            initialMessages={[]} // Explicitly pass empty array to ensure welcome message is added
          />
        </div>
      </div>
    </DashboardLayout>
  )
}
