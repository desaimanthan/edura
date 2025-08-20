"use client"

import { useCallback } from 'react'
import { useFileOperations, FileData, generateSuccessMessage } from './fileOperations'
import { useCourseStructure } from './courseStructure'

// Unified File Manager Hook - combines file operations with course structure management
export function useUnifiedFileManager(courseId: string) {
  const fileOperations = useFileOperations()
  const courseStructure = useCourseStructure(courseId)

  // Create file and add to structure immediately
  const createAndAddFile = useCallback(async (fileType: string, operation: 'generate' | 'modify' = 'generate', options: any = {}) => {
    // 1. Create empty file immediately
    const file = fileOperations.createFile(fileType, courseId, operation)
    
    // 2. Add to course structure immediately (appears in sidebar)
    courseStructure.addFile(file, 'top')
    
    // 3. Auto-select the file (opens in preview)
    courseStructure.selectFile(file.id)
    
    return file
  }, [fileOperations, courseStructure, courseId])

  // Generate file with full workflow
  const generateFile = useCallback(async (fileType: string, options: any = {}) => {
    // Create and add file immediately
    const file = await createAndAddFile(fileType, 'generate', options)
    
    // Start streaming generation
    const endpoint = `http://localhost:8000/courses/${courseId}/generate-${fileType.replace('_', '-')}`
    
    await fileOperations.streamFile(file.id, {
      type: 'generate',
      fileType,
      endpoint,
      payload: options,
      onProgress: (content) => {
        // Update file in structure
        courseStructure.updateFile(file.id, { content })
      },
      onComplete: (finalContent, successMessage) => {
        // Mark file as complete and move to permanent files
        courseStructure.updateFile(file.id, { 
          content: finalContent, 
          status: 'complete' 
        })
        
        // Show success message (this will be handled by the chat interface)
        console.log(`✅ ${fileType} generation complete`)
      },
      onError: (error) => {
        courseStructure.updateFile(file.id, { 
          status: 'error',
          content: `❌ Failed to generate ${fileType}: ${error}`
        })
      }
    })
    
    return file
  }, [createAndAddFile, fileOperations, courseStructure, courseId])

  // Modify file with full workflow
  const modifyFile = useCallback(async (fileId: string, fileType: string, modification: string) => {
    // Update file status to show modification is starting
    courseStructure.updateFile(fileId, { 
      status: 'generating',
      content: `🔄 Modifying ${fileType}...`
    })
    
    const endpoint = `http://localhost:8000/courses/${courseId}/modify-${fileType.replace('_', '-')}`
    
    await fileOperations.streamFile(fileId, {
      type: 'modify',
      fileType,
      endpoint,
      payload: { modification_request: modification },
      onProgress: (content) => {
        courseStructure.updateFile(fileId, { content })
      },
      onTargetedChange: (changeData) => {
        // Update file with targeted change data
        courseStructure.updateFile(fileId, {
          targetedChange: {
            type: changeData.change_type || 'modification',
            target: changeData.target || '',
            replacement: changeData.replacement || '',
            description: changeData.description || '',
            coordinates: changeData.coordinates,
            status: 'highlighting'
          }
        })
      },
      onComplete: (finalContent, successMessage) => {
        courseStructure.updateFile(fileId, { 
          content: finalContent, 
          status: 'complete' 
        })
        console.log(`✅ ${fileType} modification complete`)
      },
      onError: (error) => {
        courseStructure.updateFile(fileId, { 
          status: 'error',
          content: `❌ Failed to modify ${fileType}: ${error}`
        })
      }
    })
  }, [fileOperations, courseStructure, courseId])

  // Load existing course data
  const loadCourseData = useCallback((courseData: any) => {
    return courseStructure.loadFromCourseData(courseData)
  }, [courseStructure])

  // Handle file selection
  const selectFile = useCallback((file: FileData) => {
    courseStructure.selectFile(file.id)
  }, [courseStructure])

  // Get current selected file
  const getSelectedFile = useCallback((): FileData | null => {
    return courseStructure.selectedFile
  }, [courseStructure])

  // Cancel any ongoing operations
  const cancelOperation = useCallback((fileId: string) => {
    fileOperations.cancelStream(fileId)
    courseStructure.updateFile(fileId, {
      status: 'error',
      content: '⏹️ Operation cancelled by user'
    })
  }, [fileOperations, courseStructure])

  // Remove file from structure
  const removeFile = useCallback((fileId: string) => {
    fileOperations.removeFile(fileId)
    courseStructure.removeFile(fileId)
  }, [fileOperations, courseStructure])

  // Get all files for display
  const getAllFiles = useCallback(() => {
    return courseStructure.allFiles
  }, [courseStructure])

  // Check if any operations are in progress
  const hasActiveOperations = useCallback(() => {
    return courseStructure.hasStreamingFiles()
  }, [courseStructure])

  return {
    // Main operations
    generateFile,
    modifyFile,
    selectFile,
    removeFile,
    cancelOperation,
    
    // File management
    createAndAddFile,
    loadCourseData,
    
    // State access
    selectedFile: getSelectedFile(),
    allFiles: getAllFiles(),
    pendingFiles: courseStructure.pendingFiles,
    permanentFiles: courseStructure.permanentFiles,
    hasActiveOperations: hasActiveOperations(),
    
    // Direct access to underlying managers (if needed)
    fileOperations,
    courseStructure
  }
}

// Standard file operation patterns
export const STANDARD_FILE_OPERATIONS = {
  // Course Design Generation
  generateCourseDesign: async (manager: ReturnType<typeof useUnifiedFileManager>, options: { focus?: string } = {}) => {
    return await manager.generateFile('course-design', options)
  },
  
  // Course Design Modification
  modifyCourseDesign: async (manager: ReturnType<typeof useUnifiedFileManager>, fileId: string, modification: string) => {
    return await manager.modifyFile(fileId, 'course-design', modification)
  },
  
  // Curriculum Generation
  generateCurriculum: async (manager: ReturnType<typeof useUnifiedFileManager>, options: { modules?: number } = {}) => {
    return await manager.generateFile('curriculum', options)
  },
  
  // Assessment Generation
  generateAssessments: async (manager: ReturnType<typeof useUnifiedFileManager>, options: { type?: string } = {}) => {
    return await manager.generateFile('assessments', options)
  },
  
  // Lesson Plans Generation
  generateLessonPlans: async (manager: ReturnType<typeof useUnifiedFileManager>, options: { module?: number } = {}) => {
    return await manager.generateFile('lesson-plans', options)
  }
}

// Success message handler for chat integration
export const handleSuccessMessage = (operation: string, fileType: string, onSuccessMessage?: (message: string) => void) => {
  const message = generateSuccessMessage(operation, fileType)
  onSuccessMessage?.(message)
  return message
}

// File operation status checker
export const getOperationStatus = (files: FileData[]) => {
  const pending = files.filter(f => f.status === 'pending').length
  const generating = files.filter(f => f.status === 'generating').length
  const streaming = files.filter(f => f.status === 'streaming').length
  const complete = files.filter(f => f.status === 'complete').length
  const error = files.filter(f => f.status === 'error').length
  
  return {
    pending,
    generating,
    streaming,
    complete,
    error,
    total: files.length,
    hasActiveOperations: pending + generating + streaming > 0
  }
}
