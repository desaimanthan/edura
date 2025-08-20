"use client"

import React, { createContext, useContext, useCallback } from 'react'

interface FileCreationContextType {
  createFileImmediately: (fileType: string, operation: 'generate' | 'modify') => void
}

const FileCreationContext = createContext<FileCreationContextType | null>(null)

export function FileCreationProvider({ 
  children, 
  onCreateFile 
}: { 
  children: React.ReactNode
  onCreateFile: (fileType: string, operation: 'generate' | 'modify') => void
}) {
  const createFileImmediately = useCallback((fileType: string, operation: 'generate' | 'modify') => {
    console.log('🎯 FileCreationContext: Creating file immediately:', { fileType, operation })
    onCreateFile(fileType, operation)
  }, [onCreateFile])

  return (
    <FileCreationContext.Provider value={{ createFileImmediately }}>
      {children}
    </FileCreationContext.Provider>
  )
}

export function useFileCreation() {
  const context = useContext(FileCreationContext)
  if (!context) {
    // Return a no-op function if context is not available
    console.warn('useFileCreation called outside of FileCreationProvider, using fallback')
    return {
      createFileImmediately: (fileType: string, operation: 'generate' | 'modify') => {
        console.warn('FileCreation fallback called:', { fileType, operation })
      }
    }
  }
  return context
}
