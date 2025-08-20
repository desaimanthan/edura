"use client"

import { useState, useCallback, useRef } from 'react'

// Types
export interface FileData {
  id: string
  name: string
  type: 'file' | 'folder'
  content?: string
  fileType?: 'markdown' | 'image' | 'pdf' | 'slide-template'
  status?: 'pending' | 'generating' | 'streaming' | 'complete' | 'error'
  progress?: number
  isR2File?: boolean
  lastUpdated?: number
  children?: FileData[]
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

export interface StreamOperation {
  type: 'generate' | 'modify'
  fileType: string
  endpoint: string
  payload: any
  onProgress?: (content: string, progress?: number) => void
  onComplete?: (finalContent: string, successMessage: string) => void
  onError?: (error: string) => void
  onTargetedChange?: (changeData: any) => void
}

export interface StreamEvent {
  type: 'start' | 'content' | 'progress' | 'targeted_change_start' | 'targeted_change_complete' | 'complete' | 'error'
  content?: string
  full_content?: string
  progress?: string
  change_type?: string
  target?: string
  replacement?: string
  description?: string
  coordinates?: any
  r2_key?: string
  public_url?: string
}

// File Operations Hook
export function useFileOperations() {
  const [files, setFiles] = useState<Map<string, FileData>>(new Map())
  const streamingRefs = useRef<Map<string, AbortController>>(new Map())

  // Create empty file immediately and add to structure
  const createFile = useCallback((fileType: string, courseId: string, operation: 'generate' | 'modify' = 'generate'): FileData => {
    const fileId = `${fileType}-${operation}-${Date.now()}`
    const fileName = `${fileType}.md`
    
    const initialContent = operation === 'generate' 
      ? `🔄 Preparing to generate ${fileType}...`
      : `🔄 Preparing to modify ${fileType}...`

    const newFile: FileData = {
      id: fileId,
      name: fileName,
      type: 'file',
      fileType: 'markdown',
      content: initialContent,
      status: 'pending',
      lastUpdated: Date.now()
    }

    setFiles(prev => new Map(prev.set(fileId, newFile)))
    return newFile
  }, [])

  // Update file content in real-time
  const updateFileContent = useCallback((fileId: string, updates: Partial<FileData>) => {
    setFiles(prev => {
      const current = prev.get(fileId)
      if (!current) return prev
      
      const updated = { ...current, ...updates, lastUpdated: Date.now() }
      return new Map(prev.set(fileId, updated))
    })
  }, [])

  // Get file by ID
  const getFile = useCallback((fileId: string): FileData | undefined => {
    return files.get(fileId)
  }, [files])

  // Get all files as array
  const getAllFiles = useCallback((): FileData[] => {
    return Array.from(files.values())
  }, [files])

  // Remove file
  const removeFile = useCallback((fileId: string) => {
    setFiles(prev => {
      const newMap = new Map(prev)
      newMap.delete(fileId)
      return newMap
    })
    
    // Cancel any ongoing streaming
    const controller = streamingRefs.current.get(fileId)
    if (controller) {
      controller.abort()
      streamingRefs.current.delete(fileId)
    }
  }, [])

  // Parse streaming event data
  const parseStreamEvent = useCallback((eventData: string): StreamEvent | null => {
    try {
      if (!eventData || eventData === '{}' || !eventData.startsWith('{') || !eventData.endsWith('}')) {
        return null
      }
      return JSON.parse(eventData)
    } catch (error) {
      console.warn('Failed to parse stream event:', error)
      return null
    }
  }, [])

  // Handle streaming for any file type
  const streamFile = useCallback(async (fileId: string, operation: StreamOperation): Promise<void> => {
    const controller = new AbortController()
    streamingRefs.current.set(fileId, controller)

    try {
      // Update file to generating state
      updateFileContent(fileId, {
        status: 'generating',
        content: `🤖 AI is ${operation.type === 'generate' ? 'generating' : 'modifying'} ${operation.fileType}...`
      })

      const token = localStorage.getItem('auth_token')
      if (!token) {
        throw new Error('No authentication token found. Please sign in again.')
      }

      const response = await fetch(operation.endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(operation.payload),
        signal: controller.signal
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`)
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
              const eventData = line.slice(6).trim()
              const event = parseStreamEvent(eventData)
              
              if (!event) continue

              await handleStreamEvent(fileId, event, operation)
            }
          }
        }
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        return // Stream was cancelled
      }
      
      const errorMessage = error instanceof Error ? error.message : String(error)
      updateFileContent(fileId, {
        status: 'error',
        content: `❌ Failed to ${operation.type} ${operation.fileType}: ${errorMessage}`
      })
      
      operation.onError?.(errorMessage)
    } finally {
      streamingRefs.current.delete(fileId)
    }
  }, [updateFileContent, parseStreamEvent])

  // Handle individual stream events
  const handleStreamEvent = useCallback(async (fileId: string, event: StreamEvent, operation: StreamOperation) => {
    switch (event.type) {
      case 'start':
        updateFileContent(fileId, {
          status: 'streaming',
          content: event.content || 'Starting generation...'
        })
        break

      case 'content':
        if (event.full_content) {
          updateFileContent(fileId, {
            status: 'streaming',
            content: event.full_content
          })
          operation.onProgress?.(event.full_content)
        }
        break

      case 'progress':
        if (event.content) {
          const currentFile = getFile(fileId)
          if (currentFile && operation.type === 'generate') {
            // For generation, append progress messages
            updateFileContent(fileId, {
              content: (currentFile.content || '') + '\n\n' + event.content
            })
          }
          // For modifications, don't update content with progress messages
        }
        break

      case 'targeted_change_start':
        updateFileContent(fileId, {
          targetedChange: {
            type: event.change_type || 'modification',
            target: event.target || '',
            replacement: event.replacement || '',
            description: event.description || '',
            coordinates: event.coordinates,
            status: 'highlighting'
          }
        })
        operation.onTargetedChange?.(event)
        break

      case 'targeted_change_complete':
        if (event.full_content) {
          updateFileContent(fileId, {
            content: event.full_content,
            targetedChange: {
              type: event.change_type || 'modification',
              target: event.target || '',
              replacement: event.replacement || '',
              description: event.description || '',
              coordinates: event.coordinates,
              status: 'completed'
            }
          })
        }
        break

      case 'complete':
        updateFileContent(fileId, {
          status: 'complete',
          content: event.full_content || event.content || ''
        })
        
        operation.onComplete?.(
          event.full_content || event.content || '',
          event.content || `${operation.fileType} ${operation.type}d successfully!`
        )
        break

      case 'error':
        updateFileContent(fileId, {
          status: 'error',
          content: `❌ Error: ${event.content}`
        })
        operation.onError?.(event.content || 'Unknown error')
        break
    }
  }, [updateFileContent, getFile])

  // Generate file (common function)
  const generateFile = useCallback(async (fileType: string, courseId: string, options: any = {}): Promise<FileData> => {
    const file = createFile(fileType, courseId, 'generate')
    
    const endpoint = `http://localhost:8000/courses/${courseId}/generate-${fileType.replace('_', '-')}`
    
    await streamFile(file.id, {
      type: 'generate',
      fileType,
      endpoint,
      payload: options,
      onProgress: (content) => {
        // Progress handled by streamFile
      },
      onComplete: (finalContent, successMessage) => {
        console.log(`✅ ${fileType} generation complete`)
      },
      onError: (error) => {
        console.error(`❌ ${fileType} generation failed:`, error)
      }
    })

    return file
  }, [createFile, streamFile])

  // Modify file (common function)
  const modifyFile = useCallback(async (fileId: string, fileType: string, courseId: string, modification: string): Promise<void> => {
    const endpoint = `http://localhost:8000/courses/${courseId}/modify-${fileType.replace('_', '-')}`
    
    await streamFile(fileId, {
      type: 'modify',
      fileType,
      endpoint,
      payload: { modification_request: modification },
      onTargetedChange: (changeData) => {
        console.log(`🎯 Targeted change for ${fileType}:`, changeData.description)
      },
      onComplete: (finalContent, successMessage) => {
        console.log(`✅ ${fileType} modification complete`)
      },
      onError: (error) => {
        console.error(`❌ ${fileType} modification failed:`, error)
      }
    })
  }, [streamFile])

  // Cancel streaming operation
  const cancelStream = useCallback((fileId: string) => {
    const controller = streamingRefs.current.get(fileId)
    if (controller) {
      controller.abort()
      streamingRefs.current.delete(fileId)
      
      updateFileContent(fileId, {
        status: 'error',
        content: '⏹️ Operation cancelled by user'
      })
    }
  }, [updateFileContent])

  return {
    // File management
    files: getAllFiles(),
    createFile,
    updateFileContent,
    getFile,
    removeFile,
    
    // Streaming operations
    streamFile,
    generateFile,
    modifyFile,
    cancelStream,
    
    // Utilities
    parseStreamEvent,
    handleStreamEvent
  }
}

// Success message templates
export const generateSuccessMessage = (operation: string, fileType: string): string => {
  const templates = {
    generate: {
      'course-design': '✅ **Course design generated successfully:** Your course now includes comprehensive instructional design.\n\n**Next Step:** Review & Refine\n\nYour course design includes:\n\n- Curriculum structure\n- Pedagogy strategies\n- Assessment frameworks\n\nYou can now review the generated content or request specific modifications to enhance your course.',
      'curriculum': '✅ **Curriculum generated successfully:** Your course curriculum is now complete.\n\n**Next Step:** Add Assessments\n\nYour curriculum includes:\n\n- Learning objectives\n- Module structure\n- Content outline\n\nWould you like to generate assessments or make modifications?',
      'assessments': '✅ **Assessments generated successfully:** Your assessment package is ready.\n\n**Next Step:** Review & Implement\n\nYour assessments include:\n\n- Formative assessments\n- Summative evaluations\n- Rubrics and criteria\n\nReview the assessments or request modifications as needed.'
    },
    modify: {
      'course-design': '✅ **Course design modified successfully:** Your requested changes have been applied.\n\n**Next Step:** Continue Refining\n\nYou can make additional modifications or proceed with implementation.',
      'curriculum': '✅ **Curriculum modified successfully:** Your curriculum has been updated.\n\n**Next Step:** Review Changes\n\nCheck the modifications and make further adjustments if needed.',
      'assessments': '✅ **Assessments modified successfully:** Your assessment updates are complete.\n\n**Next Step:** Finalize Assessments\n\nReview the changes and implement in your course.'
    }
  }
  
  return templates[operation as keyof typeof templates]?.[fileType as keyof typeof templates.generate] || 
         `✅ **${fileType} ${operation}d successfully!** Your content is ready for review.`
}

// File type configurations
export const FILE_TYPE_CONFIG = {
  'course-design': {
    displayName: 'Course Design',
    description: 'Comprehensive instructional design with curriculum, pedagogy, and assessments',
    icon: '📚',
    generateEndpoint: 'generate-course-design',
    modifyEndpoint: 'modify-course-design'
  },
  'curriculum': {
    displayName: 'Curriculum',
    description: 'Course curriculum structure and content outline',
    icon: '📋',
    generateEndpoint: 'generate-curriculum',
    modifyEndpoint: 'modify-curriculum'
  },
  'assessments': {
    displayName: 'Assessments',
    description: 'Assessment strategies, rubrics, and evaluation methods',
    icon: '📝',
    generateEndpoint: 'generate-assessments',
    modifyEndpoint: 'modify-assessments'
  },
  'lesson-plans': {
    displayName: 'Lesson Plans',
    description: 'Detailed lesson plans for each module',
    icon: '📖',
    generateEndpoint: 'generate-lesson-plans',
    modifyEndpoint: 'modify-lesson-plans'
  }
}
