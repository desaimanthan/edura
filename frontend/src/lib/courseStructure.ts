"use client"

import { useState, useCallback, useEffect } from 'react'
import { FileData } from './fileOperations'

export interface CourseStructureState {
  permanentFiles: FileData[]
  pendingFiles: FileData[]
  selectedFileId: string | null
}

// Course Structure Manager Hook
export function useCourseStructure(courseId?: string) {
  const [structure, setStructure] = useState<CourseStructureState>({
    permanentFiles: [],
    pendingFiles: [],
    selectedFileId: null
  })

  // Add file to structure immediately (real-time, no refresh)
  const addFile = useCallback((file: FileData, position: 'top' | 'bottom' = 'top') => {
    setStructure(prev => {
      const isPending = file.status === 'pending' || file.status === 'generating' || file.status === 'streaming'
      
      if (isPending) {
        // Add to pending files
        const newPendingFiles = position === 'top' 
          ? [file, ...prev.pendingFiles]
          : [...prev.pendingFiles, file]
        
        return {
          ...prev,
          pendingFiles: newPendingFiles,
          selectedFileId: file.id // Auto-select new file
        }
      } else {
        // Add to permanent files
        const newPermanentFiles = position === 'top'
          ? [file, ...prev.permanentFiles]
          : [...prev.permanentFiles, file]
        
        return {
          ...prev,
          permanentFiles: newPermanentFiles,
          selectedFileId: file.id
        }
      }
    })
  }, [])

  // Update file in structure (real-time updates)
  const updateFile = useCallback((fileId: string, updates: Partial<FileData>) => {
    setStructure(prev => {
      // Find file in pending files
      const pendingIndex = prev.pendingFiles.findIndex(f => f.id === fileId)
      if (pendingIndex !== -1) {
        const updatedFile = { ...prev.pendingFiles[pendingIndex], ...updates }
        const newPendingFiles = [...prev.pendingFiles]
        newPendingFiles[pendingIndex] = updatedFile

        // If file is now complete, move to permanent files
        if (updatedFile.status === 'complete') {
          const newPermanentFiles = [updatedFile, ...prev.permanentFiles]
          newPendingFiles.splice(pendingIndex, 1)
          
          return {
            ...prev,
            permanentFiles: newPermanentFiles,
            pendingFiles: newPendingFiles
          }
        }

        return {
          ...prev,
          pendingFiles: newPendingFiles
        }
      }

      // Find file in permanent files
      const permanentIndex = prev.permanentFiles.findIndex(f => f.id === fileId)
      if (permanentIndex !== -1) {
        const updatedFile = { ...prev.permanentFiles[permanentIndex], ...updates }
        const newPermanentFiles = [...prev.permanentFiles]
        newPermanentFiles[permanentIndex] = updatedFile

        return {
          ...prev,
          permanentFiles: newPermanentFiles
        }
      }

      return prev
    })
  }, [])

  // Remove file from structure
  const removeFile = useCallback((fileId: string) => {
    setStructure(prev => ({
      ...prev,
      pendingFiles: prev.pendingFiles.filter(f => f.id !== fileId),
      permanentFiles: prev.permanentFiles.filter(f => f.id !== fileId),
      selectedFileId: prev.selectedFileId === fileId ? null : prev.selectedFileId
    }))
  }, [])

  // Select file
  const selectFile = useCallback((fileId: string | null) => {
    setStructure(prev => ({
      ...prev,
      selectedFileId: fileId
    }))
  }, [])

  // Get file by ID
  const getFile = useCallback((fileId: string): FileData | undefined => {
    const allFiles = [...structure.pendingFiles, ...structure.permanentFiles]
    return allFiles.find(f => f.id === fileId)
  }, [structure])

  // Get all files (pending first, then permanent)
  const getAllFiles = useCallback((): FileData[] => {
    return [...structure.pendingFiles, ...structure.permanentFiles]
  }, [structure])

  // Get selected file
  const getSelectedFile = useCallback((): FileData | null => {
    if (!structure.selectedFileId) return null
    return getFile(structure.selectedFileId) || null
  }, [structure.selectedFileId, getFile])

  // Load structure from course data (for existing files)
  const loadFromCourseData = useCallback((courseData: any) => {
    const files: FileData[] = []
    let fileId = 1

    // Handle course design from R2 URL
    if (courseData.course_design_public_url || courseData.curriculum_public_url) {
      files.push({
        id: (fileId++).toString(),
        name: 'course-design.md',
        type: 'file',
        fileType: 'markdown',
        content: courseData.course_design_public_url || courseData.curriculum_public_url,
        isR2File: true,
        status: 'complete'
      })
    }

    // Handle other sections from structure
    if (courseData.structure && Object.keys(courseData.structure).length > 0) {
      Object.entries(courseData.structure).forEach(([sectionName, sectionData]: [string, any]) => {
        if (sectionName === 'curriculum') return // Already handled above

        const sectionNode: FileData = {
          id: (fileId++).toString(),
          name: sectionName,
          type: 'folder',
          children: []
        }

        if (typeof sectionData === 'object' && sectionData !== null) {
          Object.entries(sectionData).forEach(([contentType, content]: [string, any]) => {
            if (typeof content === 'string') {
              sectionNode.children!.push({
                id: (fileId++).toString(),
                name: `${contentType}.md`,
                type: 'file',
                fileType: 'markdown',
                content: content,
                status: 'complete'
              })
            }
          })
        }

        if (sectionNode.children && sectionNode.children.length > 0) {
          files.push(sectionNode)
        }
      })
    }

    setStructure(prev => ({
      ...prev,
      permanentFiles: files,
      selectedFileId: files.length > 0 ? files[0].id : null
    }))

    // Auto-select first file if available
    if (files.length > 0) {
      return files[0]
    }
    return null
  }, [])

  // Add file from URL (for R2 files)
  const addFileFromUrl = useCallback(async (fileName: string, url: string) => {
    try {
      const response = await fetch(url)
      if (response.ok) {
        const content = await response.text()
        const file: FileData = {
          id: `url-${Date.now()}`,
          name: fileName,
          type: 'file',
          fileType: 'markdown',
          content: content,
          isR2File: true,
          status: 'complete'
        }
        addFile(file)
        return file
      }
    } catch (error) {
      console.error('Failed to fetch file from URL:', error)
      // Create placeholder file
      const file: FileData = {
        id: `url-${Date.now()}`,
        name: fileName,
        type: 'file',
        fileType: 'markdown',
        content: '# Loading...\n\nFetching content from server...',
        isR2File: true,
        status: 'complete'
      }
      addFile(file)
      return file
    }
    return null
  }, [addFile])

  // Move file from pending to permanent
  const promoteFile = useCallback((fileId: string) => {
    setStructure(prev => {
      const pendingIndex = prev.pendingFiles.findIndex(f => f.id === fileId)
      if (pendingIndex === -1) return prev

      const file = { ...prev.pendingFiles[pendingIndex], status: 'complete' as const }
      const newPendingFiles = [...prev.pendingFiles]
      newPendingFiles.splice(pendingIndex, 1)

      return {
        ...prev,
        pendingFiles: newPendingFiles,
        permanentFiles: [file, ...prev.permanentFiles]
      }
    })
  }, [])

  // Get files by status
  const getFilesByStatus = useCallback((status: FileData['status']) => {
    return getAllFiles().filter(f => f.status === status)
  }, [getAllFiles])

  // Check if any files are streaming
  const hasStreamingFiles = useCallback(() => {
    return structure.pendingFiles.some(f => f.status === 'streaming' || f.status === 'generating')
  }, [structure.pendingFiles])

  return {
    // State
    structure,
    selectedFile: getSelectedFile(),
    allFiles: getAllFiles(),
    pendingFiles: structure.pendingFiles,
    permanentFiles: structure.permanentFiles,
    
    // File management
    addFile,
    updateFile,
    removeFile,
    selectFile,
    getFile,
    promoteFile,
    
    // Loading and URL handling
    loadFromCourseData,
    addFileFromUrl,
    
    // Utilities
    getFilesByStatus,
    hasStreamingFiles
  }
}

// File state utilities
export const getFileStateIcon = (status: FileData['status']) => {
  switch (status) {
    case 'pending':
      return { icon: '⏳', className: 'text-yellow-500 animate-pulse' }
    case 'generating':
      return { icon: '🤖', className: 'text-blue-500 animate-pulse' }
    case 'streaming':
      return { icon: '⚡', className: 'text-green-500 animate-bounce' }
    case 'complete':
      return { icon: '✅', className: 'text-green-600' }
    case 'error':
      return { icon: '❌', className: 'text-red-500' }
    default:
      return { icon: '📄', className: 'text-gray-500' }
  }
}

export const getFileTypeIcon = (fileType?: string) => {
  switch (fileType) {
    case 'markdown':
      return '📝'
    case 'image':
      return '🖼️'
    case 'pdf':
      return '📄'
    case 'slide-template':
      return '🎯'
    default:
      return '📄'
  }
}

// Convert legacy structure to new format
export const convertLegacyStructure = (legacyStructure: any): FileData[] => {
  const files: FileData[] = []
  let fileId = 1

  if (legacyStructure && Object.keys(legacyStructure).length > 0) {
    Object.entries(legacyStructure).forEach(([sectionName, sectionData]: [string, any]) => {
      if (typeof sectionData === 'string') {
        // Simple file
        files.push({
          id: (fileId++).toString(),
          name: `${sectionName}.md`,
          type: 'file',
          fileType: 'markdown',
          content: sectionData,
          status: 'complete'
        })
      } else if (typeof sectionData === 'object' && sectionData !== null) {
        // Folder with children
        const children: FileData[] = []
        Object.entries(sectionData).forEach(([contentType, content]: [string, any]) => {
          if (typeof content === 'string') {
            children.push({
              id: (fileId++).toString(),
              name: `${contentType}.md`,
              type: 'file',
              fileType: 'markdown',
              content: content,
              status: 'complete'
            })
          }
        })

        if (children.length > 0) {
          files.push({
            id: (fileId++).toString(),
            name: sectionName,
            type: 'folder',
            children: children
          })
        }
      }
    })
  }

  return files
}
