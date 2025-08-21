"use client"

import { useState, useRef, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Send, Bot, User, Sparkles, Upload, Building2, Check, Edit3 } from "lucide-react"
import { useRouter } from "next/navigation"
import { courseFileOperations } from "@/lib/courseFileStore"
import { API_ENDPOINTS, getApiUrl, logApiCall } from "@/lib/api-config"

// Simple markdown renderer for chat messages
const SimpleMarkdownRenderer = ({ content }: { content: string }) => {
  // Simple markdown parsing for chat messages
  const renderMarkdown = (text: string) => {
    return text
      // Headers
      .replace(/^### (.*$)/gm, '<h3 class="text-sm font-bold mb-1 text-gray-900">$1</h3>')
      .replace(/^## (.*$)/gm, '<h2 class="text-base font-bold mb-2 text-gray-900">$1</h2>')
      .replace(/^# (.*$)/gm, '<h1 class="text-lg font-bold mb-2 text-gray-900">$1</h1>')
      // Bold and italic
      .replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-gray-900">$1</strong>')
      .replace(/\*(.*?)\*/g, '<em class="italic text-gray-900">$1</em>')
      // Code
      .replace(/`([^`]+)`/g, '<code class="bg-gray-200 px-1 py-0.5 rounded text-xs font-mono text-gray-800">$1</code>')
      // Lists (simple)
      .replace(/^- (.*$)/gm, '<li class="mb-0.5 text-gray-900 list-disc list-inside">$1</li>')
      .replace(/^\* (.*$)/gm, '<li class="mb-0.5 text-gray-900 list-disc list-inside">$1</li>')
      // Line breaks
      .replace(/\n\n/g, '</p><p class="mb-2 mt-2 text-gray-900">')
  }

  const processedContent = renderMarkdown(content)
  
  return (
    <div 
      className="prose prose-sm max-w-none text-gray-900"
      dangerouslySetInnerHTML={{ 
        __html: `<p class="mb-2 text-gray-900">${processedContent}</p>` 
      }} 
    />
  )
}

interface Message {
  id: string
  content: string
  sender: 'user' | 'ai'
  timestamp: Date
  isStreaming?: boolean
}

interface ChatInterfaceProps {
  courseId?: string
  courseName?: string
  onCourseCreated?: (courseId: string, courseName: string) => void
  initialMessages?: Array<Record<string, unknown>>
  onCurriculumStreaming?: (courseId: string, focus?: string, modificationType?: string) => Promise<void>
  successMessage?: string
  successMessageTimestamp?: number
}


export function ChatInterface({ 
  courseId, 
  onCourseCreated, 
  onCurriculumStreaming, 
  successMessage, 
  successMessageTimestamp 
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [currentCourseId, setCurrentCourseId] = useState<string | undefined>(courseId)
  const [showQuickActions, setShowQuickActions] = useState(false)
  const [showContentApprovalActions, setShowContentApprovalActions] = useState(false)
  const [showMaterialContentApprovalActions, setShowMaterialContentApprovalActions] = useState(false)
  const [showUploadInterface, setShowUploadInterface] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [isLoadingMessages, setIsLoadingMessages] = useState(false)
  
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Helper function to check if message should show quick actions
  const shouldShowQuickActions = useCallback((content: string) => {
    const lowerContent = content.toLowerCase()
    // Check for course design/curriculum generation questions
    return (lowerContent.includes("course materials") || 
            lowerContent.includes("curriculum") ||
            lowerContent.includes("course design")) && 
           (lowerContent.includes("generate everything") || 
            lowerContent.includes("generate for you") ||
            lowerContent.includes("have course materials") ||
            lowerContent.includes("already have")) &&
           (content.includes("?") || lowerContent.includes("would you like"))
  }, [])

  // Helper function to check if message should show content approval actions
  const shouldShowContentApprovalActions = useCallback((content: string) => {
    const lowerContent = content.toLowerCase()
    // Check for content structure completion messages
    return (lowerContent.includes("structure generated successfully") || 
            lowerContent.includes("content structure generated") ||
            lowerContent.includes("constrained structure generated") ||
            lowerContent.includes("course structure") ||
            lowerContent.includes("checklist") ||
            lowerContent.includes("comprehensive content structure")) &&
           (lowerContent.includes("generated") || 
            lowerContent.includes("created") ||
            lowerContent.includes("ready") ||
            lowerContent.includes("successfully")) &&
           (lowerContent.includes("approve") || 
            lowerContent.includes("review") ||
            lowerContent.includes("modify") ||
            lowerContent.includes("next step") ||
            lowerContent.includes("would you like to approve"))
  }, [])

  // Helper function to check if message should show material content approval actions - SIMPLIFIED
  const shouldShowMaterialContentApprovalActions = useCallback((content: string) => {
    const lowerContent = content.toLowerCase()
    
    // SIMPLIFIED: Check for the new streamlined messages from Agent 5
    const hasGeneratedContent = lowerContent.includes("generated content for") && 
                               lowerContent.includes("**") // Has bold formatting for title
    
    // Check for diff preview messages
    const isDiffPreviewMessage = lowerContent.includes("preview changes for") ||
                                (lowerContent.includes("preview") && lowerContent.includes("changes"))
    
    // Check for "All Done" message - should NOT show approval buttons
    const isAllDone = lowerContent.includes("all done") || 
                     lowerContent.includes("you can publish this course now")
    
    // Show approval buttons only if content was generated and it's not the final "All Done" message
    return (hasGeneratedContent || isDiffPreviewMessage) && !isAllDone
  }, [])

  // Helper function to check if message should show course structure generation button
  const shouldShowStructureGenerationAction = useCallback((content: string) => {
    const lowerContent = content.toLowerCase()
    // Show for course design completion messages
    return (lowerContent.includes("course design generated successfully") || 
            lowerContent.includes("course now includes curriculum structure")) &&
           (lowerContent.includes("pedagogy strategies") ||
            lowerContent.includes("assessment frameworks"))
  }, [])

  // Load messages on mount
  useEffect(() => {
    loadMessages()
  }, [courseId])

  // Trigger welcome message for new conversations
  useEffect(() => {
    const triggerWelcomeMessage = async () => {
      // Only trigger if:
      // 1. No course ID (completely new conversation)
      // 2. No messages loaded
      // 3. Not currently loading messages (to avoid race condition)
      if (!courseId && messages.length === 0 && !isLoadingMessages) {
        try {
          const token = localStorage.getItem('auth_token')
          const url = getApiUrl(API_ENDPOINTS.CHAT)
          logApiCall('POST', API_ENDPOINTS.CHAT, { content: '__WELCOME_TRIGGER__' })
          const response = await fetch(url, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ content: '__WELCOME_TRIGGER__' })
          })

          if (response.ok) {
            await handleStreamingResponse(response, null)
          }
        } catch {
          // Failed to trigger welcome message
        }
      }
    }

    // Small delay to ensure component is fully mounted and loading state is set
    const timer = setTimeout(triggerWelcomeMessage, 200)
    return () => clearTimeout(timer)
  }, [courseId, messages.length, isLoadingMessages])

  // Handle success messages from parent
  useEffect(() => {
    if (successMessage && successMessageTimestamp) {
      const successMsg: Message = {
        id: `success-${successMessageTimestamp}`,
        content: successMessage,
        sender: 'ai',
        timestamp: new Date()
      }
      
      setMessages(prev => {
        const exists = prev.find(msg => msg.id === successMsg.id)
        return exists ? prev : [...prev, successMsg]
      })
    }
  }, [successMessage, successMessageTimestamp])

  const loadMessages = async () => {
    if (!courseId) {
      // No course ID, show empty state - backend will send welcome message
      setMessages([])
      setIsLoadingMessages(false)
      return
    }

    setIsLoadingMessages(true)
    try {
      const token = localStorage.getItem('auth_token')
      const url = getApiUrl(API_ENDPOINTS.COURSES.MESSAGES(courseId))
      logApiCall('GET', API_ENDPOINTS.COURSES.MESSAGES(courseId))
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const messagesData = await response.json()
        const formattedMessages: Message[] = messagesData.map((msg: {
          _id?: string;
          id?: string;
          content: string;
          role: string;
          timestamp: string;
        }) => ({
          id: msg._id || msg.id,
          content: msg.content,
          sender: msg.role === 'assistant' ? 'ai' : 'user',
          timestamp: new Date(msg.timestamp)
        }))

        setMessages(formattedMessages)
        
        // Check if last AI message should show quick actions
        const lastAiMessage = [...formattedMessages].reverse().find(msg => msg.sender === 'ai')
        if (lastAiMessage && shouldShowQuickActions(lastAiMessage.content)) {
          setShowQuickActions(true)
        }
        
        // Check if last AI message should show content approval actions
        if (lastAiMessage && shouldShowContentApprovalActions(lastAiMessage.content)) {
          setShowContentApprovalActions(true)
        }
        
        // Check if last AI message should show material content approval actions
        if (lastAiMessage && shouldShowMaterialContentApprovalActions(lastAiMessage.content)) {
          setShowMaterialContentApprovalActions(true)
        }

        // Check if should show upload interface
        const lastUserMessage = [...formattedMessages].reverse().find(msg => msg.sender === 'user')
        if (lastUserMessage && lastUserMessage.content.toLowerCase().includes('i have one')) {
          setShowUploadInterface(true)
        }
      }
    } catch {
      setMessages([])
    } finally {
      setIsLoadingMessages(false)
    }
  }

  const createDraftCourse = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      const url = getApiUrl(API_ENDPOINTS.COURSES.CREATE_DRAFT)
      logApiCall('POST', API_ENDPOINTS.COURSES.CREATE_DRAFT)
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const result = await response.json()
        setCurrentCourseId(result.course_id)
        if (onCourseCreated) {
          onCourseCreated(result.course_id, 'Untitled Course')
        }
        return result.course_id
      }
    } catch {
      // Failed to create draft course
    }
    return null
  }

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      sender: 'user',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    const messageContent = inputValue
    setInputValue('')
    setIsTyping(true)
    setShowQuickActions(false)
    setShowContentApprovalActions(false)

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }

    try {
      let targetCourseId = currentCourseId
      
      // Create draft course if needed
      if (!targetCourseId) {
        targetCourseId = await createDraftCourse()
        if (!targetCourseId) {
          throw new Error('Failed to create course')
        }
      }

      // Check for workflow context to provide better intent classification
      let workflowContext = null
      try {
        const storedContext = sessionStorage.getItem(`workflow_context_${targetCourseId}`)
        if (storedContext) {
          workflowContext = JSON.parse(storedContext)
        }
      } catch {
        // Failed to parse stored workflow context
      }

      const token = localStorage.getItem('auth_token')
      
      // OPTION B: Detect material content generation requests and use dedicated endpoint
      const isMaterialContentRequest = detectMaterialContentRequest(messageContent, workflowContext)
      
      let endpoint: string
      let requestBody: Record<string, unknown>
      
      if (isMaterialContentRequest && targetCourseId) {
        endpoint = getApiUrl(API_ENDPOINTS.COURSES.CHAT_MATERIAL_CONTENT(targetCourseId))
        requestBody = { message: messageContent }
      } else {
        // Use regular chat endpoint
        endpoint = targetCourseId 
          ? getApiUrl(API_ENDPOINTS.COURSES.CHAT(targetCourseId))
          : getApiUrl(API_ENDPOINTS.CHAT)

        // Enhanced request body with workflow context hints
        requestBody = { content: messageContent }
        
        // Add context hints if available
        if (workflowContext) {
          requestBody.context_hints = {
            current_step: workflowContext.workflowState?.current_step,
            available_files: workflowContext.availableFiles,
            suggested_message: workflowContext.suggestedMessage
          }
        }
      }

      logApiCall('POST', endpoint, requestBody)
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      })

      if (response.ok) {
        await handleStreamingResponse(response, targetCourseId)
      } else {
        throw new Error('Failed to send message')
      }
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: "I apologize, but I'm experiencing some technical difficulties. Please try again in a moment.",
        sender: 'ai',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsTyping(false)
    }
  }

  // Helper function to detect material content generation requests
  const detectMaterialContentRequest = (message: string, workflowContext: Record<string, unknown> | null): boolean => {
    const lowerMessage = message.toLowerCase()
    
    // Check for explicit material content generation patterns
    const materialContentPatterns = [
      'generate content for material',
      'generate content for slide',
      'create content for',
      'generate slide',
      'create slide content',
      'material content',
      'slide content'
    ]
    
    // Check for workflow context indicating content generation step
    const workflowState = workflowContext?.workflowState as { current_step?: string } | undefined
    const isContentGenerationStep = workflowState?.current_step === 'content_structure_generation' ||
                                   workflowState?.current_step === 'material_content_generation'
    
    // Check for approval messages that should continue with material content
    const isApprovalMessage = lowerMessage.includes('approve and continue') ||
                             lowerMessage.includes('approve & continue') ||
                             lowerMessage.includes('approve and proceed')
    
    return materialContentPatterns.some(pattern => lowerMessage.includes(pattern)) ||
           (isContentGenerationStep && isApprovalMessage)
  }

  const handleStreamingResponse = async (response: Response, courseId: string | null) => {
    setIsTyping(false)
    
    const reader = response.body?.getReader()
    const decoder = new TextDecoder()
    let streamedContent = ''
    let aiMessageId: string | null = null
    let functionResults = {}

    if (reader) {
      while (true) {
        const { done, value } = await reader.read()
        if (done) {
          break
        }

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const jsonStr = line.slice(6).trim()
              if (!jsonStr || jsonStr === '{}') continue

              const data = JSON.parse(jsonStr)
              
              // Handle image generation events
              if (data.type === 'image_generation_start') {
                if (data.file_path && currentCourseId) {
                  courseFileOperations.handleImageGenerationStart(data.file_path, data.image_type || 'cover')
                }
              } else if (data.type === 'image_generation_progress') {
                if (data.file_path) {
                  courseFileOperations.handleImageGenerationProgress(
                    data.file_path, 
                    data.stage || 'processing', 
                    data.message || 'Generating image...'
                  )
                }
              } else if (data.type === 'image_generation_complete') {
                if (data.file_path && data.public_url) {
                  courseFileOperations.handleImageGenerationComplete(
                    data.file_path,
                    data.public_url,
                    data.r2_key || '',
                    data.file_size || 0,
                    data.metadata
                  )
                }
              } else if (data.type === 'image_generation_error') {
                if (data.file_path) {
                  courseFileOperations.handleImageGenerationError(
                    data.file_path,
                    data.error_message || 'Image generation failed',
                    data.error_data
                  )
                }
              } else if (data.type === 'material_content_start' || data.type === 'material_content_progress' || 
                        data.type === 'material_content_stream' || data.type === 'material_content_complete' || 
                        data.type === 'material_content_error') {
                // CRITICAL FIX: Use the course file store's unified event handler
                // This ensures proper materialId-based file lookup and path handling
                if (currentCourseId) {
                  courseFileOperations.handleContentMaterialEvent(data)
                }
              } else if (data.type === 'folder_created' || data.type === 'material_created' || data.type === 'material_progress') {
                // Handle content material events for real-time file tree updates
                if (currentCourseId) {
                  courseFileOperations.handleContentMaterialEvent(data)
                }
              } else if (data.type === 'metadata') {
                if (data.data?.course_id && !currentCourseId) {
                  setCurrentCourseId(data.data.course_id)
                }
                functionResults = data.data?.function_results || {}
                
                // CRITICAL FIX: Handle targeted edit responses from Agent 5
                const targetedEditResult = (functionResults as Record<string, unknown>).slide_content_edited_targeted as Record<string, unknown>
                if (targetedEditResult?.success && targetedEditResult.requires_approval && currentCourseId) {
                  handleTargetedEditResponse(targetedEditResult, currentCourseId)
                }
              } else if (data.type === 'text') {
                // Handle both old and new data structure
                const content = data.content || data.data?.content || ''
                if (content) {
                  streamedContent += content
                  
                  if (!aiMessageId) {
                    aiMessageId = (Date.now() + 1).toString()
                    const aiMessage: Message = {
                      id: aiMessageId,
                      content: streamedContent,
                      sender: 'ai',
                      timestamp: new Date()
                    }
                    setMessages(prev => {
                      const newMessages = [...prev, aiMessage]
                      // Trigger scroll after state update for new messages
                      setTimeout(() => {
                        if (shouldAutoScroll()) {
                          scrollToBottom()
                        }
                      }, 50)
                      return newMessages
                    })
                  } else {
                    setMessages(prev => {
                      const updatedMessages = prev.map(msg => 
                        msg.id === aiMessageId ? { ...msg, content: streamedContent } : msg
                      )
                      // Trigger scroll after content update during streaming
                      setTimeout(() => {
                        if (shouldAutoScroll()) {
                          scrollToBottom()
                        }
                      }, 50)
                      return updatedMessages
                    })
                  }

                  // Check for quick actions during streaming
                  if (shouldShowQuickActions(streamedContent)) {
                    setShowQuickActions(true)
                  }
                  
                  // Check for content approval actions during streaming
                  if (shouldShowContentApprovalActions(streamedContent)) {
                    setShowContentApprovalActions(true)
                  }
                  
                  // SIMPLIFIED: Check for material content approval actions during streaming
                  // Only show if not "All Done" message
                  if (shouldShowMaterialContentApprovalActions(streamedContent)) {
                    const isAllDone = streamedContent.toLowerCase().includes("all done") || 
                                     streamedContent.toLowerCase().includes("you can publish this course now")
                    if (!isAllDone) {
                      setShowMaterialContentApprovalActions(true)
                    } else {
                      // Hide approval buttons for "All Done" message
                      setShowMaterialContentApprovalActions(false)
                    }
                  }
                }
              } else if (data.type === 'complete') {
                // Ensure final message is preserved
                if (aiMessageId && streamedContent) {
                  setMessages(prev => prev.map(msg => 
                    msg.id === aiMessageId ? { ...msg, content: streamedContent } : msg
                  ))
                }

                // Handle function results
                const functionResultsTyped = functionResults as Record<string, unknown>
                const researchResult = functionResultsTyped.research_conducted as Record<string, unknown>
                const generationResult = (functionResultsTyped.curriculum_generated || 
                                       functionResultsTyped.course_design_generated) as Record<string, unknown>
                const modificationResult = functionResultsTyped.course_design_modified as Record<string, unknown>
                const contentStructureResult = functionResultsTyped.structure_generated as Record<string, unknown>
                const contentCreationResult = functionResultsTyped.content_creation_started as Record<string, unknown>
                const contentApprovedResult = functionResultsTyped.content_approved as Record<string, unknown>
                
                // Handle research generation
                if (researchResult && researchResult.streaming && onCurriculumStreaming) {
                  try {
                    await onCurriculumStreaming(researchResult.course_id as string, researchResult.focus_area as string, 'research')
                  } catch {
                    // Error in research streaming
                  }
                }
                
                // Handle course design generation
                if (generationResult && generationResult.streaming && onCurriculumStreaming) {
                  try {
                    await onCurriculumStreaming(generationResult.course_id as string, generationResult.focus as string)
                  } catch {
                    // Error in curriculum streaming callback
                  }
                }
                
                // Handle course design modification
                if (modificationResult && modificationResult.streaming && onCurriculumStreaming) {
                  try {
                    await onCurriculumStreaming(modificationResult.course_id as string, modificationResult.modification_request as string, 'modification')
                  } catch {
                    // Error in course design modification callback
                  }
                }
                
                // Handle content structure generation
                if (contentStructureResult && contentStructureResult.streaming) {
                  try {
                    await handleContentStructureStreaming(contentStructureResult.course_id as string)
                  } catch {
                    // Error in content structure streaming
                  }
                }
                
                // Handle content creation - FIXED: Don't call onCurriculumStreaming for content creation
                // The backend auto-trigger mechanism will handle the transition to MaterialContentGeneratorAgent
                if (contentCreationResult && contentCreationResult.streaming) {
                  // Content creation is handled by the backend auto-trigger mechanism
                  // No need to make additional frontend calls that could interfere with the workflow
                  console.log('Content creation started, backend will handle auto-trigger to MaterialContentGeneratorAgent')
                }
                
                // CRITICAL FIX: Handle auto-generation of specific material content
                const contentGenerationResult = functionResultsTyped.content_generation_started as Record<string, unknown>
                if (contentGenerationResult && contentGenerationResult.auto_generate && contentGenerationResult.next_material) {
                  try {
                    // Automatically trigger content generation for the specific material
                    const nextMaterial = contentGenerationResult.next_material as Record<string, unknown>
                    await handleMaterialContentGeneration(
                      nextMaterial.id as string,
                      nextMaterial.title as string,
                      currentCourseId || courseId
                    )
                  } catch {
                    // Auto-generation failed
                  }
                }
                
                // SIMPLIFIED: Handle content approval and continuation
                if (contentApprovedResult && contentApprovedResult.success && contentApprovedResult.continue_generation) {
                  // The backend will automatically continue to the next material
                  // No need to show verbose messages - the next content generation will show its own message
                  console.log('Content approved, backend will auto-continue to next material')
                }

                // CRITICAL FIX: Handle auto-trigger completion from ConversationOrchestrator
                const autoTriggerResult = functionResultsTyped.auto_trigger as Record<string, unknown>
                if (autoTriggerResult && autoTriggerResult.type === 'content_creation') {
                  try {
                    // Automatically connect to MaterialContentGeneratorAgent streaming endpoint
                    await handleMaterialContentGenerationStreaming(currentCourseId || courseId)
                  } catch {
                    // Failed to connect to material content streaming
                  }
                }

                // Handle course creation
                if (functionResultsTyped.course_created && onCourseCreated) {
                  try {
                    const courseCreatedResult = functionResultsTyped.course_created as Record<string, unknown>
                    
                    // Set course ID in file store first
                    if (courseCreatedResult.course_id) {
                      courseFileOperations.setCourseId(courseCreatedResult.course_id as string)
                    }
                    
                    // Extract cover image URLs and update file store immediately
                    if (courseCreatedResult.cover_image_url || courseCreatedResult.cover_image_large_url || 
                        courseCreatedResult.cover_image_medium_url || courseCreatedResult.cover_image_small_url) {
                      
                      // Use the first available URL (prioritize large, then medium, then small, then generic)
                      const coverImageUrl = (courseCreatedResult.cover_image_large_url as string) || 
                                          (courseCreatedResult.cover_image_url as string) || 
                                          (courseCreatedResult.cover_image_medium_url as string) || 
                                          (courseCreatedResult.cover_image_small_url as string)
                      
                      // Add cover image to file store immediately
                      if (coverImageUrl) {
                        courseFileOperations.upsertFile('/cover-image.png', {
                          fileType: 'image',
                          url: coverImageUrl,
                          status: 'saved',
                          source: 'r2',
                          createdAt: Date.now()
                        })
                      }
                      
                      // Force refresh to ensure UI updates
                      courseFileOperations.forceRefreshCourseFiles()
                    }
                    
                    // CRITICAL FIX: Show "Generate for me" button when course is created successfully
                    // This should happen regardless of the message content
                    setShowQuickActions(true)
                    
                    const token = localStorage.getItem('auth_token')
                    const targetCourseId = (courseCreatedResult.course_id as string) || courseId || ''
                    const courseUrl = getApiUrl(API_ENDPOINTS.COURSES.DETAIL(targetCourseId))
                    logApiCall('GET', API_ENDPOINTS.COURSES.DETAIL(targetCourseId))
                    const courseResponse = await fetch(courseUrl, {
                      headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                      }
                    })
                    if (courseResponse.ok) {
                      const courseData = await courseResponse.json()
                      onCourseCreated(courseData._id, courseData.name)
                    }
                    } catch {
                      // Failed to get course data
                    }
                }
                break
              }
            } catch {
              // Failed to parse SSE data
            }
          }
        }
      }
    }

    // If no content was streamed, show a fallback message
    if (!streamedContent && !aiMessageId) {
      const fallbackMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: "I'm here to help you create courses! What would you like to work on?",
        sender: 'ai',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, fallbackMessage])
    }
  }

  const handleQuickAction = async (action: 'generate') => {
    setShowQuickActions(false)
    
    const actionMessage = 'Generate for me'
    
    const userMessage: Message = {
      id: Date.now().toString(),
      content: actionMessage,
      sender: 'user',
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, userMessage])
    setIsTyping(true)

    try {
      let targetCourseId = currentCourseId
      
      if (!targetCourseId) {
        targetCourseId = await createDraftCourse()
        if (!targetCourseId) {
          throw new Error('Failed to create course')
        }
      }

      const token = localStorage.getItem('auth_token')
      const endpoint = getApiUrl(API_ENDPOINTS.COURSES.CHAT(targetCourseId))

      logApiCall('POST', API_ENDPOINTS.COURSES.CHAT(targetCourseId), { content: actionMessage })
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content: actionMessage })
      })

      if (response.ok) {
        await handleStreamingResponse(response, targetCourseId)
      } else {
        throw new Error('Failed to send message')
      }
    } catch {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: "I apologize, but I'm experiencing some technical difficulties. Please try again in a moment.",
        sender: 'ai',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsTyping(false)
    }
  }

  const handleContentApprovalAction = async (action: 'approve' | 'modify') => {
    setShowContentApprovalActions(false)
    
    const actionMessage = action === 'approve' ? 'Approve and proceed with content creation' : 'I want to modify the structure'
    
    const userMessage: Message = {
      id: Date.now().toString(),
      content: actionMessage,
      sender: 'user',
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, userMessage])
    setIsTyping(true)

    try {
      let targetCourseId = currentCourseId
      
      if (!targetCourseId) {
        targetCourseId = await createDraftCourse()
        if (!targetCourseId) {
          throw new Error('Failed to create course')
        }
      }

      const token = localStorage.getItem('auth_token')
      
      // CRITICAL FIX: For approval actions, use the regular chat endpoint but ensure proper workflow context
      // The backend ConversationOrchestrator will handle the workflow transition correctly
      const endpoint = getApiUrl(API_ENDPOINTS.COURSES.CHAT(targetCourseId))

      const requestBody = { 
        content: actionMessage,
        // Add context hint to help the orchestrator understand this is a structure approval
        context_hints: {
          current_step: 'content_structure_approval',
          action_type: action === 'approve' ? 'structure_approval' : 'structure_modification'
        }
      }

      logApiCall('POST', API_ENDPOINTS.COURSES.CHAT(targetCourseId), requestBody)
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      })

      if (response.ok) {
        await handleStreamingResponse(response, targetCourseId)
      } else {
        throw new Error('Failed to send message')
      }
    } catch {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: "I apologize, but I'm experiencing some technical difficulties. Please try again in a moment.",
        sender: 'ai',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsTyping(false)
    }
  }

  const handleMaterialContentApprovalAction = async (action: 'approve' | 'modify') => {
    setShowMaterialContentApprovalActions(false)
    
    // SIMPLIFIED: Show loading state immediately
    if (action === 'approve') {
      // Add a loading message for approval
      const loadingMessage: Message = {
        id: Date.now().toString(),
        content: 'Generating content for next slide...',
        sender: 'ai',
        timestamp: new Date(),
        isStreaming: true
      }
      setMessages(prev => [...prev, loadingMessage])
    }
    
    const actionMessage = action === 'approve' ? 'Approve and continue to next slide' : 'I want to modify this content'
    
    const userMessage: Message = {
      id: (Date.now() + 1).toString(),
      content: actionMessage,
      sender: 'user',
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, userMessage])
    setIsTyping(true)

    try {
      let targetCourseId = currentCourseId
      
      if (!targetCourseId) {
        targetCourseId = await createDraftCourse()
        if (!targetCourseId) {
          throw new Error('Failed to create course')
        }
      }

      const token = localStorage.getItem('auth_token')
      
      // Use dedicated material content endpoint for approval actions
      const endpoint = getApiUrl(API_ENDPOINTS.COURSES.CHAT_MATERIAL_CONTENT(targetCourseId))

      logApiCall('POST', API_ENDPOINTS.COURSES.CHAT_MATERIAL_CONTENT(targetCourseId), { message: actionMessage })
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: actionMessage })
      })

      if (response.ok) {
        await handleStreamingResponse(response, targetCourseId)
      } else {
        throw new Error('Failed to send message')
      }
    } catch {
      const errorMessage: Message = {
        id: (Date.now() + 2).toString(),
        content: "I apologize, but I'm experiencing some technical difficulties. Please try again in a moment.",
        sender: 'ai',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsTyping(false)
    }
  }

  const handleStructureGenerationAction = async () => {
    const actionMessage = 'Generate Course Structure'
    
    const userMessage: Message = {
      id: Date.now().toString(),
      content: actionMessage,
      sender: 'user',
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, userMessage])
    setIsTyping(true)

    try {
      let targetCourseId = currentCourseId
      
      if (!targetCourseId) {
        targetCourseId = await createDraftCourse()
        if (!targetCourseId) {
          throw new Error('Failed to create course')
        }
      }

      const token = localStorage.getItem('auth_token')
      
      // Call the content structure generation endpoint directly
      const url = getApiUrl(API_ENDPOINTS.COURSES.GENERATE_CONTENT_STRUCTURE(targetCourseId))
      logApiCall('POST', API_ENDPOINTS.COURSES.GENERATE_CONTENT_STRUCTURE(targetCourseId), { focus: null })
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ focus: null })
      })

      if (response.ok) {
        // Handle the streaming response for structure generation
        await handleContentStructureStreaming(targetCourseId)
      } else {
        throw new Error('Failed to generate course structure')
      }
    } catch {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: "I apologize, but I'm experiencing some technical difficulties generating the course structure. Please try again in a moment.",
        sender: 'ai',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsTyping(false)
    }
  }

  const handleFileUpload = async () => {
    if (!selectedFile || !currentCourseId) return

    setIsUploading(true)
    
    try {
      const token = localStorage.getItem('auth_token')
      const formData = new FormData()
      formData.append('file', selectedFile)

      const url = getApiUrl(API_ENDPOINTS.COURSES.UPLOAD_CURRICULUM(currentCourseId))
      logApiCall('POST', API_ENDPOINTS.COURSES.UPLOAD_CURRICULUM(currentCourseId))
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      })

      if (response.ok) {
        const successMessage: Message = {
          id: Date.now().toString(),
          content: `✅ Curriculum uploaded successfully! Your curriculum "${selectedFile.name}" has been processed and is now available in the course structure.`,
          sender: 'ai',
          timestamp: new Date()
        }
        setMessages(prev => [...prev, successMessage])
        
        setSelectedFile(null)
        setShowUploadInterface(false)
        if (fileInputRef.current) {
          fileInputRef.current.value = ''
        }
      } else {
        throw new Error('Upload failed')
      }
    } catch {
      const errorMessage: Message = {
        id: Date.now().toString(),
        content: `❌ Upload failed. Please try again or contact support if the problem persists.`,
        sender: 'ai',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsUploading(false)
    }
  }

  // Auto-resize textarea
  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current
    if (!textarea) return

    textarea.style.height = 'auto'
    const lineHeight = 20
    const maxLines = 3
    const minHeight = lineHeight + 16
    const maxHeight = (lineHeight * maxLines) + 16
    const scrollHeight = textarea.scrollHeight
    
    if (scrollHeight <= maxHeight) {
      textarea.style.height = `${Math.max(scrollHeight, minHeight)}px`
      textarea.style.overflowY = 'hidden'
    } else {
      textarea.style.height = `${maxHeight}px`
      textarea.style.overflowY = 'auto'
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }

  // Smart auto-scrolling: only scroll if user is already near the bottom
  const shouldAutoScroll = () => {
    const messagesContainer = messagesEndRef.current?.parentElement
    if (!messagesContainer) return true
    
    const { scrollTop, scrollHeight, clientHeight } = messagesContainer
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight
    
    // Auto-scroll if user is within 150px of the bottom or if it's a new conversation
    return distanceFromBottom < 150 || messages.length <= 2
  }

  // Auto-scroll effect for messages
  useEffect(() => {
    const timer = setTimeout(() => {
      if (shouldAutoScroll()) {
        scrollToBottom()
      }
    }, 100) // Small delay to ensure DOM is updated

    return () => clearTimeout(timer)
  }, [messages])

  // Auto-scroll during streaming (for real-time updates)
  useEffect(() => {
    if (isTyping) {
      const interval = setInterval(() => {
        if (shouldAutoScroll()) {
          scrollToBottom()
        }
      }, 500) // Check every 500ms during streaming

      return () => clearInterval(interval)
    }
  }, [isTyping])

  useEffect(() => {
    adjustTextareaHeight()
  }, [inputValue])

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleFileSelect = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      if (!file.name.endsWith('.md')) {
        alert('Please select a .md (Markdown) file')
        return
      }
      setSelectedFile(file)
    }
  }

  const handleResearchStreaming = async (courseId: string, focusArea: string) => {
    // Don't add a duplicate start message - the initial chat response already shows it
    
    try {
      const token = localStorage.getItem('auth_token')
      const url = getApiUrl(API_ENDPOINTS.COURSES.GENERATE_RESEARCH(courseId))
      logApiCall('POST', API_ENDPOINTS.COURSES.GENERATE_RESEARCH(courseId), { focus_area: focusArea })
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ focus_area: focusArea })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

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
                if (!jsonStr || jsonStr === '{}') continue

                const data = JSON.parse(jsonStr)

                // Handle different event types from research generation
                if (data.type === 'start') {
                  // Don't add another message - just log that streaming started
                } else if (data.type === 'research_progress') {
                  // Progress events are handled by parent component for file display
                } else if (data.type === 'content') {
                  // Content events are handled by parent component for file display
                } else if (data.type === 'complete') {
                  
                  const completionMessage: Message = {
                    id: Date.now().toString(),
                    content: "✅ **Research Analysis Complete!**\n\nComprehensive research has been generated and saved to `research.md`. The analysis includes:\n\n- Latest industry trends and technologies\n- Current best practices and methodologies\n- Academic research and findings\n- Real-world applications and case studies\n\n🎯 **Next Step:** Course design generation will begin automatically based on these research findings.",
                    sender: 'ai',
                    timestamp: new Date()
                  }
                  
                  setMessages(prev => [...prev, completionMessage])
                  
                  // Research completion automatically triggers course design generation
                  // This is handled by the backend workflow transition
                  break
                } else if (data.type === 'workflow_transition') {
                  const transitionMessage: Message = {
                    id: Date.now().toString(),
                    content: data.content,
                    sender: 'ai',
                    timestamp: new Date()
                  }
                  setMessages(prev => [...prev, transitionMessage])
                } else if (data.type === 'error') {
                  const errorMessage: Message = {
                    id: Date.now().toString(),
                    content: `❌ **Research Generation Failed**\n\nError: ${data.content}\n\nPlease try again or contact support if the problem persists.`,
                    sender: 'ai',
                    timestamp: new Date()
                  }
                  setMessages(prev => [...prev, errorMessage])
                  break
                }
              } catch {
                // Failed to parse research event
              }
            }
          }
        }
      }
    } catch (error) {
      const errorMessage: Message = {
        id: Date.now().toString(),
        content: `❌ **Research Generation Failed**\n\nError: ${error instanceof Error ? error.message : String(error)}\n\nPlease try again or contact support if the problem persists.`,
        sender: 'ai',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    }
  }

  const handleMaterialContentGeneration = async (materialId: string, materialTitle: string, courseId: string | null) => {
    if (!courseId) {
      return
    }
    
    try {
      const token = localStorage.getItem('auth_token')
      
      // Call the backend to generate content for the specific material
      const url = getApiUrl(API_ENDPOINTS.COURSES.CHAT(courseId))
      const requestBody = { content: `Generate content for material: ${materialTitle}` }
      logApiCall('POST', API_ENDPOINTS.COURSES.CHAT(courseId), requestBody)
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      })

      if (response.ok) {
        // The streaming response will be handled by the existing SSE handlers
        await handleStreamingResponse(response, courseId)
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
    } catch (error) {
      // Show error message in chat
      const errorMessage: Message = {
        id: Date.now().toString(),
        content: `❌ **Material Content Generation Failed**\n\nError: ${error instanceof Error ? error.message : String(error)}\n\nPlease try again or contact support if the problem persists.`,
        sender: 'ai',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    }
  }

  const handleMaterialContentGenerationStreaming = async (courseId: string | null) => {
    if (!courseId) {
      return
    }
    
    try {
      const token = localStorage.getItem('auth_token')
      
      // Connect to the dedicated MaterialContentGeneratorAgent streaming endpoint
      const url = getApiUrl(API_ENDPOINTS.COURSES.GENERATE_MATERIAL_CONTENT(courseId))
      const requestBody = { material_id: null } // Start content generation process (will auto-generate first material)
      logApiCall('POST', API_ENDPOINTS.COURSES.GENERATE_MATERIAL_CONTENT(courseId), requestBody)
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

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
                if (!jsonStr || jsonStr === '{}') continue

                const data = JSON.parse(jsonStr)

                // CRITICAL FIX: Use the course file store's unified event handler for all material content events
                // This ensures proper materialId-based file lookup and path handling
                if (data.type === 'material_content_start' || data.type === 'material_content_progress' || 
                   data.type === 'material_content_stream' || data.type === 'material_content_complete' || 
                   data.type === 'material_content_error') {
                  if (courseId) {
                    courseFileOperations.handleContentMaterialEvent(data)
                  }
                  
                  // Show completion message in chat for successful completion
                  if (data.type === 'material_content_complete') {
                    const completionMessage: Message = {
                      id: Date.now().toString(),
                      content: `✅ **Content Generated Successfully!**\n\n"${data.title}" has been generated and is now available in the course files. The content includes comprehensive study material with:\n\n- Detailed explanations and examples\n- Learning objectives and key concepts\n- Interactive elements and assessments\n- Real-world applications\n\n📄 **File:** \`${data.file_path}\`\n🌐 **Saved to:** R2 Storage\n\nWould you like to **approve & continue** to the next slide, or **request modifications** to this content?`,
                      sender: 'ai',
                      timestamp: new Date()
                    }
                    setMessages(prev => [...prev, completionMessage])
                    setShowMaterialContentApprovalActions(true)
                  } else if (data.type === 'material_content_error') {
                    // Show error message in chat
                    const errorMessage: Message = {
                      id: Date.now().toString(),
                      content: `❌ **Material Content Generation Failed**\n\nError: ${data.error_message}\n\nPlease try again or contact support if the problem persists.`,
                      sender: 'ai',
                      timestamp: new Date()
                    }
                    setMessages(prev => [...prev, errorMessage])
                  }
                } else if (data.type === 'complete') {
                  break
                } else if (data.type === 'error') {
                  const errorMessage: Message = {
                    id: Date.now().toString(),
                    content: `❌ **Material Content Generation Failed**\n\nError: ${data.content}\n\nPlease try again or contact support if the problem persists.`,
                    sender: 'ai',
                    timestamp: new Date()
                  }
                  setMessages(prev => [...prev, errorMessage])
                  break
                }
              } catch {
                // Failed to parse MaterialContentGenerator event
              }
            }
          }
        }
      }
    } catch (error) {
      // Show error message in chat
      const errorMessage: Message = {
        id: Date.now().toString(),
        content: `❌ **Material Content Generation Failed**\n\nError: ${error instanceof Error ? error.message : String(error)}\n\nPlease try again or contact support if the problem persists.`,
        sender: 'ai',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    }
  }

  // Handle targeted edit responses from Agent 5
  const handleTargetedEditResponse = (targetedEditResult: Record<string, unknown>, courseId: string) => {
    try {
      console.log('Processing Agent 5 targeted edit response:', targetedEditResult)
      
      // Agent 5 returns: material_id, material_title, original_content, modified_content, edit_preview
      const materialId = targetedEditResult.material_id as string
      const materialTitle = targetedEditResult.material_title as string
      const originalContent = targetedEditResult.original_content as string
      const modifiedContent = targetedEditResult.modified_content as string
      const editPreview = targetedEditResult.edit_preview as Record<string, unknown>
      const changesDescription = targetedEditResult.changes_summary as string
      
      if (!materialId || !materialTitle || !originalContent || !modifiedContent) {
        console.warn('Missing required fields in Agent 5 targeted edit response:', {
          hasMaterialId: !!materialId,
          hasMaterialTitle: !!materialTitle,
          hasOriginalContent: !!originalContent,
          hasModifiedContent: !!modifiedContent
        })
        return
      }
      
      // Find the file path for this material in the course file store
      const snapshot = courseFileOperations.getSnapshot()
      let targetFilePath: string | null = null
      
      // Search for the material by title or content match
      for (const [path, node] of snapshot.nodesByPath.entries()) {
        if (node.fileType === 'markdown' && 
            (path.includes(materialTitle.toLowerCase().replace(/[^a-z0-9]/g, '_')) ||
             (node.content && originalContent && node.content.includes(originalContent.substring(0, 100))))) {
          targetFilePath = path
          break
        }
      }
      
      // If not found by content match, try to construct the expected path
      if (!targetFilePath) {
        // Try to find any markdown file that might match
        const markdownFiles = Array.from(snapshot.nodesByPath.entries())
          .filter(([path, node]) => node.fileType === 'markdown')
        
        if (markdownFiles.length > 0) {
          // Use the first markdown file as fallback, or try to find the most recently updated one
          const sortedFiles = markdownFiles.sort((a, b) => (b[1].createdAt || 0) - (a[1].createdAt || 0))
          targetFilePath = sortedFiles[0][0]
          console.log('Using fallback file path for targeted edit:', targetFilePath)
        }
      }
      
      if (!targetFilePath) {
        console.warn('Could not find file path for material:', materialTitle)
        return
      }
      
      // CRITICAL FIX: Create targetedChange data that matches what file-preview expects
      const targetedChange = {
        type: editPreview?.change_type as string || 'content_modification',
        target: editPreview?.target_section as string || materialTitle,
        replacement: modifiedContent,
        description: changesDescription || editPreview?.description as string || 'Content modification',
        coordinates: {
          start_line: 1,
          end_line: originalContent.split('\n').length,
          exact_text_to_replace: originalContent,
          replacement_text: modifiedContent
        },
        // Add the required fields for diff modal
        originalContent: originalContent,
        modifiedContent: modifiedContent,
        materialId: materialId,
        materialTitle: materialTitle
      }
      
      // Update the course file store with the targeted change data
      const existing = snapshot.nodesByPath.get(targetFilePath)
      
      if (existing) {
        // CRITICAL FIX: Update the file with both content and targetedChange
        courseFileOperations.upsertFile(targetFilePath, {
          content: modifiedContent, // Use the modified content from Agent 5
          targetedChange: targetedChange,
          displayTitle: materialTitle // Add display title for better UI
        })
        
        // Auto-select the file being edited to trigger the diff modal
        courseFileOperations.setSelectedPath(targetFilePath)
        
        console.log('Agent 5 targeted edit response processed successfully:', {
          materialId,
          materialTitle,
          filePath: targetFilePath,
          changeType: targetedChange.type,
          description: targetedChange.description
        })
      } else {
        console.warn('File not found in course file store:', targetFilePath)
      }
    } catch (error) {
      console.error('Error handling Agent 5 targeted edit response:', error)
    }
  }

  const handleContentStructureStreaming = async (courseId: string) => {
    try {
      const token = localStorage.getItem('auth_token')
      const url = getApiUrl(API_ENDPOINTS.COURSES.GENERATE_CONTENT_STRUCTURE(courseId))
      logApiCall('POST', API_ENDPOINTS.COURSES.GENERATE_CONTENT_STRUCTURE(courseId), { focus: null })
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ focus: null })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

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
                if (!jsonStr || jsonStr === '{}') continue

                const data = JSON.parse(jsonStr)

                // Handle different event types from content structure generation
                if (data.type === 'start') {
                  // Content structure generation started
                } else if (data.type === 'progress') {
                  // Content structure progress
                } else if (data.type === 'folder_created') {
                  // Handle real-time folder creation during content structure generation
                  courseFileOperations.ensureFolder(data.file_path)
                } else if (data.type === 'material_created') {
                  // Handle real-time material file creation during content structure generation
                  
                  // Create content based on material type and status
                  let content = ''
                  if (data.description) {
                    const materialTypeLabel = data.material_type === 'slide' ? 'Slide' : 
                                             data.material_type === 'assessment' ? 'Assessment' : 
                                             'Content'
                    
                    content = `# ${data.title}\n\n*This ${materialTypeLabel.toLowerCase()} is being generated...*\n\n**Description:**\n${data.description}\n\n---\n\n*Content will appear here as it's generated.*`
                  } else {
                    content = `# ${data.title}\n\n*This content is being generated...*\n\n---\n\n*Please wait while content is being created.*`
                  }
                  
                  courseFileOperations.upsertFile(data.file_path, {
                    fileType: 'markdown',
                    status: data.status === 'saved' ? 'saved' : 'generating',
                    source: 'stream',
                    content: content,
                    createdAt: Date.now(),
                    slideNumber: data.slide_number
                  })
                  
                  // Auto-select the first material file for immediate feedback
                  if (data.slide_number === 1 || !courseFileOperations.getSelectedNode()) {
                    courseFileOperations.setSelectedPath(data.file_path)
                  }
                } else if (data.type === 'material_progress') {
                  // Handle real-time material progress updates during content structure generation
                  const existing = courseFileOperations.getSnapshot().nodesByPath.get(data.file_path)
                  if (existing) {
                    courseFileOperations.upsertFile(data.file_path, {
                      status: 'generating',
                      content: existing.content + `\n\n*${data.message}*`
                    })
                  }
                } else if (data.type === 'complete') {
                  // Reload content materials in the file store
                  try {
                    const { courseFileOperations } = await import('@/lib/courseFileStore')
                    await courseFileOperations.loadContentMaterials(courseId)
                } catch {
                  // Failed to reload content materials
                }
                  
                  // Show success message and trigger approval buttons
                  const completionMessage: Message = {
                    id: Date.now().toString(),
                    content: "✅ **Content Structure Generated!**\n\nYour comprehensive content structure has been created with detailed checklists for all course materials. The structure includes:\n\n- Module and chapter breakdown\n- Individual slide content items\n- Assessment and quiz materials\n- Learning objectives and outcomes\n\nWould you like to **approve** this structure and proceed with individual content creation, or would you like to **modify** anything?",
                    sender: 'ai',
                    timestamp: new Date()
                  }
                  
                  setMessages(prev => [...prev, completionMessage])
                  setShowContentApprovalActions(true)
                  break
                } else if (data.type === 'error') {
                  const errorMessage: Message = {
                    id: Date.now().toString(),
                    content: `❌ **Content Structure Generation Failed**\n\nError: ${data.content}\n\nPlease try again or contact support if the problem persists.`,
                    sender: 'ai',
                    timestamp: new Date()
                  }
                  setMessages(prev => [...prev, errorMessage])
                  break
                }
              } catch {
                // Failed to parse content structure event
              }
            }
          }
        }
      }
    } catch (error) {
      const errorMessage: Message = {
        id: Date.now().toString(),
        content: `❌ **Content Structure Generation Failed**\n\nError: ${error instanceof Error ? error.message : String(error)}\n\nPlease try again or contact support if the problem persists.`,
        sender: 'ai',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    }
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-gray-50 h-16 flex items-center flex-shrink-0">
        <div className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-gray-700" />
          <h3 className="font-semibold text-gray-900">Course Copilot</h3>
        </div>
      </div>

      {/* Messages Container */}
      <div className="overflow-y-auto px-4 pt-4 pb-0 space-y-4 min-h-0 flex-grow">
        {messages.map((message, index) => (
          <div key={message.id}>
            <div className={`flex gap-3 ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
              {message.sender === 'ai' && (
                <Avatar className="h-8 w-8 bg-gray-200 flex-shrink-0">
                  <AvatarFallback>
                    <Bot className="h-4 w-4 text-gray-700" />
                  </AvatarFallback>
                </Avatar>
              )}
              
              <div className={`max-w-[80%] rounded-lg px-3 py-2 text-sm break-words ${
                message.sender === 'user' ? 'bg-gray-800 text-white' : 'bg-gray-100 text-gray-900'
              }`}>
                {message.sender === 'ai' ? (
                  <SimpleMarkdownRenderer content={message.content} />
                ) : (
                  <div className="whitespace-pre-wrap">
                    {message.content}
                  </div>
                )}
              </div>

              {message.sender === 'user' && (
                <Avatar className="h-8 w-8 bg-gray-100 flex-shrink-0">
                  <AvatarFallback>
                    <User className="h-4 w-4 text-gray-600" />
                  </AvatarFallback>
                </Avatar>
              )}
            </div>
            
            {/* Quick Action Buttons */}
            {showQuickActions && 
             message.sender === 'ai' && 
             index === messages.length - 1 && 
             shouldShowQuickActions(message.content) && (
              <div className="flex gap-3 mt-3">
                <div className="w-8 h-8 flex-shrink-0"></div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    onClick={() => handleQuickAction('generate')}
                    className="flex items-center gap-2 bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 text-sm px-3 py-2 h-auto rounded-lg shadow-sm"
                    disabled={isTyping}
                  >
                    <Sparkles className="h-4 w-4" />
                    Generate for me
                  </Button>
                </div>
              </div>
            )}
            
            {/* Content Approval Action Buttons */}
            {showContentApprovalActions && 
             message.sender === 'ai' && 
             index === messages.length - 1 && 
             shouldShowContentApprovalActions(message.content) && (
              <div className="flex gap-3 mt-3">
                <div className="w-8 h-8 flex-shrink-0"></div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    onClick={() => handleContentApprovalAction('approve')}
                    className="flex items-center gap-2 bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 text-sm px-3 py-2 h-auto rounded-lg shadow-sm"
                    disabled={isTyping}
                  >
                    <Check className="h-4 w-4" />
                    Approve & Proceed
                  </Button>
                  <Button
                    onClick={() => handleContentApprovalAction('modify')}
                    className="flex items-center gap-2 bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 text-sm px-3 py-2 h-auto rounded-lg shadow-sm"
                    disabled={isTyping}
                  >
                    <Edit3 className="h-4 w-4" />
                    Modify Structure
                  </Button>
                </div>
              </div>
            )}

            {/* Material Content Approval Action Buttons - SIMPLIFIED */}
            {showMaterialContentApprovalActions && 
             message.sender === 'ai' && 
             index === messages.length - 1 && 
             shouldShowMaterialContentApprovalActions(message.content) && (
              <div className="flex gap-3 mt-3">
                <div className="w-8 h-8 flex-shrink-0"></div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    onClick={() => handleMaterialContentApprovalAction('approve')}
                    className="flex items-center gap-2 bg-green-600 text-white hover:bg-green-700 text-sm px-4 py-2 h-auto rounded-lg shadow-sm"
                    disabled={isTyping}
                  >
                    <Check className="h-4 w-4" />
                    Approve & Generate Next
                  </Button>
                  <Button
                    onClick={() => handleMaterialContentApprovalAction('modify')}
                    className="flex items-center gap-2 bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 text-sm px-3 py-2 h-auto rounded-lg shadow-sm"
                    disabled={isTyping}
                  >
                    <Edit3 className="h-4 w-4" />
                    Redo
                  </Button>
                </div>
              </div>
            )}

            {/* Course Structure Generation Button */}
            {message.sender === 'ai' && 
             index === messages.length - 1 && 
             shouldShowStructureGenerationAction(message.content) && (
              <div className="flex gap-3 mt-3">
                <div className="w-8 h-8 flex-shrink-0"></div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    onClick={() => handleStructureGenerationAction()}
                    className="flex items-center gap-2 bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 text-sm px-3 py-2 h-auto rounded-lg shadow-sm"
                    disabled={isTyping}
                  >
                    <Building2 className="h-4 w-4" />
                    Generate Course Structure
                  </Button>
                </div>
              </div>
            )}
          </div>
        ))}

        {/* Typing indicator */}
        {isTyping && (
          <div className="flex gap-3 justify-start">
            <Avatar className="h-8 w-8 bg-gray-200 flex-shrink-0">
              <AvatarFallback>
                <Bot className="h-4 w-4 text-gray-700" />
              </AvatarFallback>
            </Avatar>
            <div className="bg-gray-100 rounded-lg px-3 py-2">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Upload Interface */}
      {showUploadInterface && (
        <div className="px-4 py-3 border-t bg-blue-50 flex-shrink-0">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Upload className="h-4 w-4 text-blue-600" />
              <span className="text-sm font-medium text-blue-900">Upload Curriculum</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowUploadInterface(false)}
              className="text-blue-600 hover:text-blue-800 h-6 w-6 p-0"
            >
              ×
            </Button>
          </div>
          
          <input
            ref={fileInputRef}
            type="file"
            accept=".md"
            onChange={handleFileChange}
            className="hidden"
          />
          
          <div className="flex gap-2 items-center">
            <Button
              variant="outline"
              size="sm"
              onClick={handleFileSelect}
              disabled={isUploading}
              className="flex items-center gap-2 text-blue-700 border-blue-300 hover:bg-blue-100"
            >
              <Upload className="h-4 w-4" />
              Choose File
            </Button>
            
            {selectedFile ? (
              <div className="flex items-center gap-2">
                <span className="text-sm text-blue-700 font-medium">
                  {selectedFile.name}
                </span>
                <Button
                  size="sm"
                  onClick={handleFileUpload}
                  disabled={isUploading}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  {isUploading ? 'Uploading...' : 'Upload'}
                </Button>
              </div>
            ) : (
              <span className="text-sm text-blue-600 flex items-center">
                Upload your curriculum.md file
              </span>
            )}
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="px-4 pt-4 pb-4 border-t bg-gray-50 flex-shrink-0">
        <div className="flex gap-2 items-end">
          <textarea
            ref={textareaRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            className="flex-1 resize-none rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 h-[36px] max-h-[76px] transition-all duration-200"
            disabled={isTyping}
            rows={1}
            style={{
              lineHeight: '20px',
              paddingTop: '8px',
              paddingBottom: '8px'
            }}
          />
          <Button 
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isTyping}
            size="sm"
            className="h-[36px] px-3 flex-shrink-0 mt-0"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}
