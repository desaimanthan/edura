"use client"

import { useState, useEffect, useRef } from "react"
import { FileText, Image, FileType, FileSliders, Edit, Eye } from "lucide-react"
import dynamic from "next/dynamic"
import { Button } from "@/components/ui/button"
import { ResearchProgressDashboard } from "@/components/progress/ResearchProgressDashboard"
import { GenerationProgressDashboard } from "@/components/progress/GenerationProgressDashboard"
import { AssessmentRenderer } from "@/components/assessment/AssessmentRenderer"
import { AssessmentFromDatabase } from "@/components/assessment/AssessmentFromDatabase"

// Dynamically import TOAST UI Editor for true WYSIWYG editing
const ToastEditor = dynamic(
  () => import("@toast-ui/react-editor").then((mod) => mod.Editor),
  { ssr: false }
)

const ToastViewer = dynamic(
  () => import("@toast-ui/react-editor").then((mod) => mod.Viewer),
  { ssr: false }
)

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
  status?: 'generating' | 'saved' | 'error' // Status for generated content
  displayTitle?: string // Human-readable title for display in UI
  materialId?: string // Database material ID for assessments and other content
  progressData?: ProgressData
  researchProgress?: {
    isActive: boolean
    currentSource: string
    currentUrl: string
    searchCount: number
    totalSearches: number
  }
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
  }
}

interface FilePreviewProps {
  selectedFile: FileData | null
  onFileUpdate?: (updatedFile: FileData) => void
}

const TrueWYSIWYGEditor = ({ 
  content, 
  isEditable = false, 
  onSave,
  isStreaming = false,
  editMode = false,
  onEditModeChange,
  onHasChangesChange,
  onContentChange,
  targetedChange,
  researchProgress
}: { 
  content: string
  isEditable?: boolean
  onSave?: (content: string) => void 
  isStreaming?: boolean
  editMode?: boolean
  onEditModeChange?: (editMode: boolean) => void
  onHasChangesChange?: (hasChanges: boolean) => void
  onContentChange?: (content: string) => void
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
  researchProgress?: {
    isActive: boolean
    currentSource: string
    currentUrl: string
    searchCount: number
    totalSearches: number
  }
}) => {
  const [markdownContent, setMarkdownContent] = useState(content)
  const [hasChanges, setHasChanges] = useState(false)
  const editorRef = useRef<{ getInstance: () => { setMarkdown: (content: string) => void; getMarkdown: () => string } } | null>(null)
  const viewerRef = useRef<{ getInstance: () => { setMarkdown: (content: string, sanitize?: boolean) => void; setHTML: (content: string) => void; getElement: () => HTMLElement } } | null>(null)
  const viewerContainerRef = useRef<HTMLDivElement>(null)
  const [highlightedContent, setHighlightedContent] = useState<string>('')
  const [processedHighlightingId, setProcessedHighlightingId] = useState<string>('')

  // Function to detect if we need to show a loader after "## Research Findings"
  const needsResearchLoader = (content: string, isStreaming: boolean) => {
    if (!isStreaming) return false
    
    // Check if content contains "## Research Findings" but has minimal actual research content
    const researchFindingsMatch = content.match(/## Research Findings\s*\n([\s\S]*?)(?=\n##|\n---|\n\*\*|$)/i)
    
    if (researchFindingsMatch) {
      const contentAfterHeading = researchFindingsMatch[1].trim()
      
      // Filter out progress messages and loader HTML to check for actual content
      const progressPattern = /🔍\s*(Conducting web search \d+|Web search \d+|Searching|Analyzing).*?\n/gi
      const loaderPattern = /<div id="research-loader"[\s\S]*?<\/div>/gi
      const stylePattern = /<style>[\s\S]*?<\/style>/gi
      
        const actualContent = contentAfterHeading
        .replace(progressPattern, '')
        .replace(loaderPattern, '')
        .replace(stylePattern, '')
        .trim()
      
      // Show loader if there's minimal actual content (not just progress messages)
      // Enhanced detection to include more research content indicators
      const hasActualContent = actualContent.length > 200 && 
                              (actualContent.includes('Comprehensive research report') || 
                               actualContent.includes('Research report:') || 
                               actualContent.includes('Executive summary') ||
                               actualContent.includes('Summary statement') ||
                               actualContent.includes('Latest Technologies') ||
                               actualContent.includes('Recent Breakthroughs') ||
                               actualContent.includes('Introduction to') ||
                               actualContent.includes('### 1.') ||
                               actualContent.includes('### 2.') ||
                               actualContent.includes('## 1.') ||
                               actualContent.includes('## 2.') ||
                               actualContent.includes('**1.') ||
                               actualContent.includes('**2.'))
      
      return !hasActualContent
    }
    
    return false
  }

  // Function to add enhanced loader with progress info after "## Research Findings"
  const addResearchLoader = (content: string) => {
    if (!needsResearchLoader(content, isStreaming)) return content
    
    const progressInfo = researchProgress?.isActive ? 
      `<div style="margin-top: 8px; font-size: 14px; color: #64748b;">
        <div><strong>🌐 ${researchProgress.currentSource || 'Web Source'}</strong></div>
        <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">${researchProgress.currentUrl || 'Searching for latest information...'}</div>
        <div style="margin-top: 6px; font-size: 12px;">Progress: ${researchProgress.searchCount}/${researchProgress.totalSearches || '~30'} sources analyzed</div>
      </div>` : ''
    
    const loaderHtml = `
<div id="research-loader" style="display: flex; flex-direction: column; gap: 8px; margin: 16px 0; padding: 16px; background-color: #f8fafc; border-radius: 8px; border-left: 4px solid #3b82f6; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
  <div style="display: flex; align-items: center; gap: 8px;">
    <div style="width: 20px; height: 20px; border: 2px solid #e5e7eb; border-top: 2px solid #3b82f6; border-radius: 50%; animation: spin 1s linear infinite;"></div>
    <em style="color: #64748b; font-weight: 500;">Analyzing and compiling research findings...</em>
  </div>
  ${progressInfo}
</div>

<style>
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
`
    
    // Insert the loader right after "## Research Findings"
    return content.replace(
      /(## Research Findings\s*\n)/i,
      `$1${loaderHtml}\n`
    )
  }


  // Auto-scroll function for the viewer during streaming
  const scrollViewerToBottom = () => {
    if (!editMode) {
      // Try to scroll the outer container first
      if (viewerContainerRef.current) {
        viewerContainerRef.current.scrollTo({
          top: viewerContainerRef.current.scrollHeight,
          behavior: 'smooth'
        })
      }
      
      // Also try to find and scroll the TOAST UI Viewer's internal container
      if (viewerRef.current) {
        try {
          // Get the TOAST UI Viewer's DOM element
          const viewerElement = viewerRef.current.getInstance().getElement()
          if (viewerElement) {
            // Find the scrollable container within the viewer
            const scrollableElement = viewerElement.querySelector('.toastui-editor-contents') || 
                                    viewerElement.querySelector('.toastui-editor-md-container') ||
                                    viewerElement
            
            if (scrollableElement) {
              scrollableElement.scrollTop = scrollableElement.scrollHeight
            }
          }
        } catch (error) {
          // Fallback: try to find any scrollable element in the viewer container
          if (viewerContainerRef.current) {
            const scrollableElements = viewerContainerRef.current.querySelectorAll('[class*="toastui"], [class*="editor"], .ProseMirror')
            scrollableElements.forEach(element => {
              if (element.scrollHeight > element.clientHeight) {
                element.scrollTop = element.scrollHeight
              }
            })
          }
        }
      }
    }
  }

  // Auto-scroll when content changes during streaming
  useEffect(() => {
    if (isStreaming && content) {
      // Multiple scroll attempts to ensure it works
      setTimeout(() => scrollViewerToBottom(), 100)
      setTimeout(() => scrollViewerToBottom(), 300)
      setTimeout(() => scrollViewerToBottom(), 600)
    }
  }, [content, isStreaming, editMode])

  // Handle targeted changes with visual highlighting
  useEffect(() => {
    if (targetedChange && targetedChange.coordinates) {
      
      // Create a unique ID for this highlighting operation
      const highlightingId = `${targetedChange.coordinates.start_line}-${targetedChange.coordinates.exact_text_to_replace}-${targetedChange.status}`
      
      if (targetedChange.status === 'highlighting') {
        // Check if we've already processed this highlighting
        if (processedHighlightingId === highlightingId) {
          return
        }
        
        // Yellow highlighting phase - show what will be changed
        
        // Mark this highlighting as processed
        setProcessedHighlightingId(highlightingId)
        
        // FORCE the highlighting to show by using HTML with actual background colors
        const lines = content.split('\n')
        const targetLine = targetedChange.coordinates.start_line - 1
        
        if (targetLine >= 0 && targetLine < lines.length) {
          const originalLine = lines[targetLine]
          const targetText = targetedChange.coordinates.exact_text_to_replace
          
          if (originalLine.includes(targetText)) {
            // Use CSS class for yellow highlighting (should be better supported)
            const highlightedLine = originalLine.replace(
              targetText,
              `<mark class="highlight-yellow">${targetText}</mark>`
            )
            lines[targetLine] = highlightedLine
            
            const highlightedContent = lines.join('\n')
            setHighlightedContent(highlightedContent)
            
            // Update viewer with highlighted content - FORCE the update
            if (viewerRef.current && !editMode) {
              try {
                // Force the viewer to re-render with HTML content
                viewerRef.current.getInstance().setMarkdown(highlightedContent, true)
              } catch (error) {
                // Fallback: try setting as HTML
                try {
                  viewerRef.current.getInstance().setHTML(highlightedContent)
                } catch (htmlError) {
                  // Silent fallback failure
                }
              }
            }
          }
        }
      } else if (targetedChange.status === 'completed') {
        // Green flash phase - show successful change
        
        // Simple text-based flash approach
        const lines = content.split('\n')
        const targetLine = targetedChange.coordinates.start_line - 1
        
        if (targetLine >= 0 && targetLine < lines.length) {
          const originalLine = lines[targetLine]
          const newText = targetedChange.coordinates.replacement_text
          
          if (originalLine.includes(newText)) {
            // Use HTML with actual green background for flash (this works perfectly)
            const flashLine = originalLine.replace(
              newText,
              `<mark style="background-color: #bbf7d0; padding: 2px 4px; border-radius: 3px; font-weight: bold; animation: pulse 0.5s ease-in-out 3;">${newText}</mark>`
            )
            lines[targetLine] = flashLine
            
            const flashContent = lines.join('\n')
            setHighlightedContent(flashContent)
            
            // Update viewer with flash content - FORCE HTML rendering
            if (viewerRef.current && !editMode) {
              try {
                // Try multiple methods to force HTML rendering
                viewerRef.current.getInstance().setMarkdown(flashContent, true)
              } catch (error) {
                try {
                  viewerRef.current.getInstance().setHTML(flashContent)
                } catch (htmlError) {
                  // Silent fallback failure
                }
              }
            }
            
            // After 3 seconds, remove the flash and show normal content
            setTimeout(() => {
              setHighlightedContent('')
              if (viewerRef.current && !editMode) {
                try {
                  viewerRef.current.getInstance().setMarkdown(content)
                } catch (error) {
                  // Silent fallback failure
                }
              }
            }, 3000)
          }
        }
      }
    } else {
      // No targeted change, use normal content
      setHighlightedContent('')
    }
  }, [targetedChange, content, editMode])

  // Update content when prop changes (important for streaming)
  useEffect(() => {
    setMarkdownContent(content)
    setHasChanges(false)
    if (onHasChangesChange) {
      onHasChangesChange(false)
    }
    
    // Update editor content if it exists and we're in edit mode
    if (editorRef.current && editMode) {
      try {
        editorRef.current.getInstance().setMarkdown(content)
      } catch (error) {
        // Silent error handling
      }
    }
    
    // Update viewer content if it exists and we're NOT in edit mode (but only if no highlighting is active)
    if (viewerRef.current && !editMode && !highlightedContent) {
      try {
        // Add research loader if needed before setting content
        const contentWithLoader = addResearchLoader(content)
        viewerRef.current.getInstance().setMarkdown(contentWithLoader)
      } catch (error) {
        // Silent error handling
      }
    }
  }, [content, editMode, onHasChangesChange, highlightedContent])


  // Update parent when hasChanges changes
  useEffect(() => {
    if (onHasChangesChange) {
      onHasChangesChange(hasChanges)
    }
  }, [hasChanges, onHasChangesChange])

  const handleContentChange = () => {
    if (editorRef.current) {
      try {
        const newContent = editorRef.current.getInstance().getMarkdown()
        setMarkdownContent(newContent)
        const newHasChanges = newContent !== content
        setHasChanges(newHasChanges)
        if (onHasChangesChange) {
          onHasChangesChange(newHasChanges)
        }
        if (onContentChange) {
          onContentChange(newContent)
        }
      } catch (error) {
        // Silent error handling
      }
    }
  }

  const handleSave = () => {
    if (onSave && hasChanges) {
      onSave(markdownContent)
      setHasChanges(false)
      if (onHasChangesChange) {
        onHasChangesChange(false)
      }
    }
  }

  const handleCancel = () => {
    setMarkdownContent(content)
    setHasChanges(false)
    if (onHasChangesChange) {
      onHasChangesChange(false)
    }
    if (onEditModeChange) {
      onEditModeChange(false)
    }
    
    // Reset editor content
    if (editorRef.current) {
      try {
        editorRef.current.getInstance().setMarkdown(content)
      } catch (error) {
        // Silent error handling
      }
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* TOAST UI Editor/Viewer */}
      <div className="flex-1 overflow-hidden">
        {editMode ? (
          <ToastEditor
            ref={editorRef}
            initialValue={markdownContent}
            previewStyle="vertical"
            height="100%"
            initialEditType="wysiwyg"
            useCommandShortcut={true}
            onChange={handleContentChange}
            toolbarItems={[
              ['heading', 'bold', 'italic', 'strike'],
              ['hr', 'quote'],
              ['ul', 'ol', 'task', 'indent', 'outdent'],
              ['table', 'image', 'link'],
              ['code', 'codeblock']
            ]}
          />
        ) : (
          <div ref={viewerContainerRef} className="h-full overflow-y-auto p-6">
            <ToastViewer
              ref={viewerRef}
              initialValue={addResearchLoader(markdownContent)}
            />
          </div>
        )}
      </div>
    </div>
  )
}

const ImagePreview = ({ content, name, url }: { content?: string; name: string; url?: string }) => {
  const [imageError, setImageError] = useState(false)
  const [imageLoading, setImageLoading] = useState(true)
  
  // Use URL if available, otherwise fall back to content
  // For cover images, prefer large size for detail view
  let imageUrl = url || content
  
  // If this is a cover image URL, try to get the large version
  if (imageUrl && imageUrl.includes('/cover/')) {
    // Check if it's already a large image or if we need to convert it
    if (imageUrl.includes('/small/') || imageUrl.includes('/medium/')) {
      // Convert to large image URL
      imageUrl = imageUrl.replace('/small/', '/large/').replace('/medium/', '/large/')
    } else if (!imageUrl.includes('/large/')) {
      // If it's the old format without size, try to construct large URL
      const parts = imageUrl.split('/cover/')
      if (parts.length === 2) {
        imageUrl = `${parts[0]}/cover/large/${parts[1]}`
      }
    }
  }
  
  if (!imageUrl) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <div className="bg-gray-100 rounded-lg p-8 max-w-md">
          <Image className="h-24 w-24 mx-auto mb-4 text-gray-500" />
          <p className="text-center text-gray-600 text-sm">
            Image Preview: {name}
          </p>
          <p className="text-center text-gray-400 text-xs mt-2">
            No image URL available
          </p>
        </div>
      </div>
    )
  }
  
  return (
    <div className="flex flex-col h-full">
      {/* Header with image info */}
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center gap-2">
          <Image className="h-5 w-5 text-blue-600" />
          <h4 className="font-medium text-gray-900">{name}</h4>
        </div>
        <p className="text-sm text-gray-500 mt-1">Course Cover Image</p>
      </div>
      
      {/* Image display */}
      <div className="flex-1 flex items-center justify-center p-6 bg-gray-50">
        {imageError ? (
          <div className="text-center">
            <Image className="h-16 w-16 mx-auto mb-4 text-gray-400" />
            <p className="text-gray-600 text-sm">Failed to load image</p>
            <p className="text-gray-400 text-xs mt-1">{imageUrl}</p>
          </div>
        ) : (
          <div className="relative max-w-full max-h-full">
            {imageLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            )}
            <img
              src={imageUrl}
              alt={name}
              className="max-w-full max-h-full object-contain rounded-lg shadow-lg"
              onLoad={() => setImageLoading(false)}
              onError={() => {
                setImageError(true)
                setImageLoading(false)
              }}
              style={{ maxHeight: 'calc(100vh - 200px)' }}
            />
          </div>
        )}
      </div>
      
      {/* Image details */}
      <div className="p-4 border-t border-gray-200 bg-white">
        <div className="text-xs text-gray-500 space-y-1">
          <div>URL: <span className="font-mono text-gray-700">{imageUrl}</span></div>
          <div>Generated automatically as course cover image</div>
        </div>
      </div>
    </div>
  )
}

const PDFPreview = ({ name }: { name: string }) => {
  return (
    <div className="flex flex-col items-center justify-center h-full">
      <div className="bg-gray-100 rounded-lg p-8 max-w-md">
        <FileType className="h-24 w-24 mx-auto mb-4 text-gray-500" />
        <p className="text-center text-gray-600 text-sm">
          PDF Document: {name}
        </p>
        <p className="text-center text-gray-400 text-xs mt-2">
          PDF preview will be available when backend is connected
        </p>
      </div>
    </div>
  )
}

const SlideTemplatePreview = ({ content, name }: { content: string; name: string }) => {
  return (
    <div className="p-6">
      <div className="bg-gray-100 rounded-lg p-8">
        <div className="flex items-center mb-4">
          <FileSliders className="h-6 w-6 text-gray-700 mr-2" />
          <h3 className="text-lg font-medium text-gray-900">{name}</h3>
        </div>
        
        <div className="bg-white rounded-lg p-6 shadow-sm">
          <div className="space-y-4">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-3 bg-gray-100 rounded w-full"></div>
            <div className="h-3 bg-gray-100 rounded w-5/6"></div>
            
            <div className="grid grid-cols-2 gap-4 mt-6">
              <div className="h-20 bg-gray-50 rounded border-2 border-dashed border-gray-200"></div>
              <div className="h-20 bg-gray-50 rounded border-2 border-dashed border-gray-200"></div>
            </div>
          </div>
        </div>
        
        <p className="text-center text-gray-500 text-sm mt-4">
          Custom Slide Template Preview
        </p>
      </div>
    </div>
  )
}

export function FilePreview({ selectedFile, onFileUpdate }: FilePreviewProps) {
  const [r2Content, setR2Content] = useState<string>("")
  const [loadingR2, setLoadingR2] = useState(false)
  const [r2Error, setR2Error] = useState<string>("")
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [editMode, setEditMode] = useState(false)
  const [hasChanges, setHasChanges] = useState(false)
  const [currentEditedContent, setCurrentEditedContent] = useState<string>("")
  const [generatingAssessment, setGeneratingAssessment] = useState(false)
  const [assessmentTitle, setAssessmentTitle] = useState<string>("")

  // Function to generate assessment content using Agent 5
  const handleGenerateAssessment = async () => {
    if (!selectedFile) return
    
    setGeneratingAssessment(true)
    
    try {
      // Get course ID from URL
      const pathParts = window.location.pathname.split('/')
      const courseId = pathParts[pathParts.indexOf('create') + 1]
      
      if (!courseId) {
        alert('Course ID not found')
        return
      }
      
      // Get auth token
      const token = localStorage.getItem('auth_token')
      if (!token) {
        alert('Authentication required. Please sign in again.')
        return
      }
      
      // Call the chat API to trigger Agent 5 assessment generation
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/courses/${courseId}/chat`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: `Generate assessment content for "${selectedFile.displayTitle || selectedFile.name}"`,
          context_hints: {
            workflow_step: 'content_generation',
            target_material_type: 'assessment',
            material_title: selectedFile.displayTitle || selectedFile.name
          }
        })
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }
      
      const result = await response.json()
      
      // Show success message and refresh the file
      alert('Assessment generation started! The content will be generated and appear shortly.')
      
      // Optionally trigger a refresh of the file data
      if (onFileUpdate) {
        // Update the file status to indicate generation is in progress
        const updatedFile = { ...selectedFile, status: 'generating' as const }
        onFileUpdate(updatedFile)
      }
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
      alert(`Failed to generate assessment: ${errorMessage}`)
    } finally {
      setGeneratingAssessment(false)
    }
  }

  // Function to detect if this is an assessment file that should fetch data from DB
  const isAssessmentFile = (fileName?: string, fileStatus?: string, materialType?: string, materialId?: string): boolean => {
    if (!fileName) return false
    
    // Check material type first (most reliable) - handle both 'assessment' and file-based detection
    if (materialType === 'assessment') return true
    
    // Check if filename indicates this is an assessment (regardless of status for better detection)
    const isAssessmentByName = fileName.toLowerCase().includes('assessment')
    
    // For assessment files, we want to use database rendering ONLY if:
    // 1. It's clearly an assessment by name, AND
    // 2. It has a valid materialId (24 character MongoDB ObjectId), AND
    // 3. The file status indicates it's been saved/completed
    if (isAssessmentByName && materialId && materialId.length === 24 && fileStatus === 'saved') {
      return true
    }
    
    return false
  }

  // Function to fetch assessment title for header display
  const fetchAssessmentTitle = async (selectedFile: FileData) => {
    if (!isAssessmentFile(selectedFile.name, selectedFile.status, (selectedFile as FileData & { materialType?: string }).materialType, selectedFile.materialId)) {
      setAssessmentTitle("")
      return
    }

    try {
      // Get course ID from URL
      const pathParts = window.location.pathname.split('/')
      const courseId = pathParts[pathParts.indexOf('create') + 1]
      
      if (!courseId) {
        setAssessmentTitle("")
        return
      }

      // Extract material ID from the selected file - use materialId if available, otherwise fallback
      const materialId = (selectedFile as FileData & { materialType?: string; materialId?: string }).materialId || selectedFile.id || selectedFile.name
      
      // Check if we have a valid MongoDB ObjectId
      if (!materialId || typeof materialId !== 'string' || materialId.length !== 24) {
        setAssessmentTitle("")
        return
      }

      // Get auth token
      const token = localStorage.getItem('auth_token')
      if (!token) {
        setAssessmentTitle("")
        return
      }

      // Fetch assessment data from the API
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/courses/${courseId}/assessment/${materialId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        }
      })

      if (response.ok) {
        const data = await response.json()
        const title = data.material_title || selectedFile.displayTitle || selectedFile.name
        setAssessmentTitle(title)
      } else {
        setAssessmentTitle("")
      }
    } catch (error) {
      setAssessmentTitle("")
    }
  }

  // Fetch assessment title when file changes
  useEffect(() => {
    if (selectedFile) {
      // First, immediately set the title from displayTitle if available
      if (selectedFile.displayTitle && isAssessmentFile(selectedFile.name, selectedFile.status, (selectedFile as FileData & { materialType?: string }).materialType, selectedFile.materialId)) {
        setAssessmentTitle(selectedFile.displayTitle)
      } else {
        setAssessmentTitle("")
      }
      
      // Then optionally fetch from API as backup (only if displayTitle is not available)
      if (!selectedFile.displayTitle && isAssessmentFile(selectedFile.name, selectedFile.status, (selectedFile as FileData & { materialType?: string }).materialType, selectedFile.materialId)) {
        fetchAssessmentTitle(selectedFile)
      }
    } else {
      setAssessmentTitle("")
    }
  }, [selectedFile?.id, selectedFile?.name, selectedFile?.status, selectedFile?.displayTitle, (selectedFile as FileData & { materialId?: string })?.materialId])

  // Function to extract JSON from content that might be wrapped in markdown
  const extractJsonFromContent = (content: string): string | null => {
    if (!content) return null
    
    // Try to find JSON block in markdown code fences
    const jsonBlockMatch = content.match(/```json\s*\n([\s\S]*?)\n```/i)
    if (jsonBlockMatch) {
      return jsonBlockMatch[1].trim()
    }
    
    // Try to find JSON block in generic code fences
    const codeBlockMatch = content.match(/```\s*\n(\{[\s\S]*?\})\s*\n```/i)
    if (codeBlockMatch) {
      return codeBlockMatch[1].trim()
    }
    
    // Try to find JSON object directly in content - improved regex
    const jsonMatch = content.match(/(\{[\s\S]*?"type"\s*:\s*"assessment"[\s\S]*?\}(?:\s*\})*)/i)
    if (jsonMatch) {
      const extractedJson = jsonMatch[1].trim()
      
      // Apply brace counting to ensure we have complete JSON
      let braceCount = 0
      let jsonEnd = -1
      
      for (let i = 0; i < extractedJson.length; i++) {
        if (extractedJson[i] === '{') {
          braceCount++
        } else if (extractedJson[i] === '}') {
          braceCount--
          if (braceCount === 0) {
            jsonEnd = i
            break
          }
        }
      }
      
      if (jsonEnd > 0) {
        const completeJson = extractedJson.substring(0, jsonEnd + 1)
        return completeJson
      }
      
      return extractedJson
    }
    
    // If content looks like pure JSON, return as is
    const trimmed = content.trim()
    if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
      // Try to find the complete JSON object by counting braces
      let braceCount = 0
      let jsonEnd = -1
      
      for (let i = 0; i < trimmed.length; i++) {
        if (trimmed[i] === '{') {
          braceCount++
        } else if (trimmed[i] === '}') {
          braceCount--
          if (braceCount === 0) {
            jsonEnd = i
            break
          }
        }
      }
      
      if (jsonEnd > 0) {
        const extractedJson = trimmed.substring(0, jsonEnd + 1)
        return extractedJson
      }
      
      return trimmed
    }
    
    return null
  }

  // Function to parse markdown-formatted assessment content
  const parseMarkdownAssessment = (content: string) => {
    try {
      const lowerContent = content.toLowerCase()
      
      // Extract title from markdown header
      const titleMatch = content.match(/^#\s*(.+)$/m)
      const title = titleMatch ? titleMatch[1].trim() : 'Assessment Question'
      
      // Extract question text
      const questionMatch = content.match(/question:\s*(.+?)(?=\n|options:|$)/i)
      const questionText = questionMatch ? questionMatch[1].trim() : title
      
      // Determine format based on content
      let format = 'multiple_choice'
      let options: Array<{ id: string; text: string; correct: boolean }> = []
      let correctAnswer = ''
      
      if (lowerContent.includes('true or false')) {
        format = 'true_false'
        options = [
          { id: 'true', text: 'True', correct: false },
          { id: 'false', text: 'False', correct: false }
        ]
        
        // Try to determine correct answer from content
        if (lowerContent.includes('answer: true') || lowerContent.includes('correct: true')) {
          correctAnswer = 'true'
          options[0].correct = true
        } else {
          correctAnswer = 'false'
          options[1].correct = true
        }
      } else if (lowerContent.includes('multiple choice')) {
        format = 'multiple_choice'
        
        // Extract options from content
        const optionsMatch = content.match(/options:\s*([\s\S]*?)(?=\n\n|format:|$)/i)
        if (optionsMatch) {
          const optionsText = optionsMatch[1]
          const optionLines = optionsText.split(/\n/).filter(line => line.trim())
          
          options = optionLines.map((line, index) => {
            const cleanLine = line.trim().replace(/^[A-D]\)\s*/, '')
            return {
              id: String.fromCharCode(65 + index), // A, B, C, D
              text: cleanLine,
              correct: index === 0 // Default to first option as correct
            }
          })
          
          correctAnswer = 'A'
        }
      }
      
      // Create assessment data structure
      return {
        type: 'assessment',
        format: format,
        question: {
          text: questionText,
          options: options,
          correct_answer: correctAnswer,
          explanation: `This is a ${format.replace('_', ' ')} question about the topic.`,
          difficulty: 'intermediate'
        },
        difficulty: 'intermediate',
        learning_objective: title
      }
    } catch (error) {
      console.error('Failed to parse markdown assessment:', error)
      return null
    }
  }

  // Function to parse assessment content
  const parseAssessmentContent = (content: string) => {
    try {
      // First try to extract JSON from content
      const extractedJson = extractJsonFromContent(content)
      
      if (extractedJson) {
        const parsed = JSON.parse(extractedJson)
        return parsed
      }
      
      // Fallback: try to parse content directly as JSON
      const directParsed = JSON.parse(content)
      return directParsed
    } catch (error) {
      // If JSON parsing fails, try to parse markdown-formatted assessment
      const markdownAssessment = parseMarkdownAssessment(content)
      if (markdownAssessment) {
        return markdownAssessment
      }
      
      return null
    }
  }

  // Auto-scroll to bottom when content changes during streaming
  const scrollToBottom = (smooth = true) => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTo({
        top: scrollContainerRef.current.scrollHeight,
        behavior: smooth ? 'smooth' : 'auto'
      })
    }
  }

  // Function to update research progress and pass to TrueWYSIWYGEditor
  const updateResearchProgress = (content: string) => {
    // This will be passed to the TrueWYSIWYGEditor component
    // The actual logic is in the TrueWYSIWYGEditor component
  }

  // Update research progress when content changes for research.md files
  useEffect(() => {
    if (isStreaming && selectedFile?.content && selectedFile.name === 'research.md') {
      updateResearchProgress(selectedFile.content)
    }
  }, [selectedFile?.content, isStreaming])

  // Detect streaming files and enable auto-scroll
  useEffect(() => {
    if (selectedFile) {
      // Check if this is a streaming file (only files with streaming IDs, not static files)
      const isStreamingFile = selectedFile.id === 'curriculum-generating' || 
                             selectedFile.id === 'curriculum-complete' ||
                             selectedFile.id === 'course-design-generating' ||
                             selectedFile.id === 'course-design-complete' ||
                             selectedFile.id === 'course-design-streaming' ||
                             selectedFile.id === 'research-streaming' ||
                             selectedFile.id === 'research-complete' ||
                             // Only check content for active streaming indicators, not static files
                             (selectedFile.content && (
                               selectedFile.content.includes('⏳ **Status:** Initializing') ||
                               selectedFile.content.includes('*Content will appear here as it\'s generated*') ||
                               selectedFile.content.includes('Starting comprehensive research analysis') ||
                               selectedFile.content.includes('*Analyzing research findings and generating*')
                             ))
      
      setIsStreaming(Boolean(isStreamingFile))
    } else {
      setIsStreaming(false)
    }
  }, [selectedFile])

  // Auto-scroll when content changes during streaming
  useEffect(() => {
    if (isStreaming && selectedFile?.content) {
      // Small delay to ensure DOM is updated
      setTimeout(() => {
        scrollToBottom(true)
      }, 100)
      
      // Also scroll after a longer delay to catch any delayed rendering
      setTimeout(() => {
        scrollToBottom(true)
      }, 500)
    }
  }, [selectedFile?.content, isStreaming])

  // Cache for R2 content to prevent duplicate fetches
  const [contentCache, setContentCache] = useState<Map<string, string>>(new Map())
  const [fetchingUrls, setFetchingUrls] = useState<Set<string>>(new Set())

  // Fetch R2 content when a file with R2 URL is selected (but skip images)
  useEffect(() => {
    if (selectedFile?.url && (selectedFile.status === 'saved' || selectedFile.isR2File) && selectedFile.fileType !== 'image') {
      // Check if content is already cached
      if (contentCache.has(selectedFile.url)) {
        setR2Content(contentCache.get(selectedFile.url) || "")
        setR2Error("")
        setLoadingR2(false)
        return
      }
      
      // Check if we're already fetching this URL
      if (fetchingUrls.has(selectedFile.url)) {
        return
      }
      
      fetchR2Content(selectedFile.url)
    } else {
      setR2Content("")
      setR2Error("")
      setLoadingR2(false)
    }
  }, [selectedFile?.url, selectedFile?.status, selectedFile?.isR2File, selectedFile?.fileType])

  const fetchR2Content = async (url: string) => {
    // Prevent duplicate fetches
    if (fetchingUrls.has(url)) {
      return
    }
    
    setFetchingUrls(prev => new Set(prev).add(url))
    setLoadingR2(true)
    setR2Error("")
    
    try {
      const response = await fetch(url)
      if (response.ok) {
        const content = await response.text()
        setR2Content(content)
        
        // Cache the content
        setContentCache(prev => new Map(prev).set(url, content))
      } else {
        setR2Error("Failed to load content from R2")
      }
    } catch (error) {
      setR2Error("Error fetching content")
    } finally {
      setLoadingR2(false)
      setFetchingUrls(prev => {
        const newSet = new Set(prev)
        newSet.delete(url)
        return newSet
      })
    }
  }

  if (!selectedFile) {
    return (
      <div className="h-full flex flex-col">
        <div className="p-4 border-b border-gray-200 bg-gray-50 h-16 flex items-center">
          <h3 className="font-semibold text-gray-900">Files Preview</h3>
        </div>
        
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center text-gray-500">
            <FileText className="h-16 w-16 mx-auto mb-4 text-gray-300" />
            <p className="text-lg font-medium mb-2">Select a file to preview its content</p>
            <p className="text-sm text-gray-400">
              Choose any file from the course structure to see its preview
            </p>
          </div>
        </div>
      </div>
    )
  }

  const renderFileContent = () => {
    // Handle progress files
    if (selectedFile.type === 'progress' && selectedFile.progressData) {
      if (selectedFile.fileType === 'research-progress') {
        return (
          <ResearchProgressDashboard 
            data={{
              completed: selectedFile.progressData.completed,
              total: selectedFile.progressData.total,
              currentTask: selectedFile.progressData.currentTask,
              estimatedTimeRemaining: selectedFile.progressData.estimatedTimeRemaining,
              sources: selectedFile.progressData.sources || []
            }}
          />
        )
      } else if (selectedFile.fileType === 'generation-progress') {
        return (
          <GenerationProgressDashboard 
            data={{
              completed: selectedFile.progressData.completed,
              total: selectedFile.progressData.total,
              currentPhase: selectedFile.progressData.currentPhase,
              totalWords: selectedFile.progressData.totalWords,
              totalSections: selectedFile.progressData.totalSections,
              overallProgress: selectedFile.progressData.overallProgress,
              phases: selectedFile.progressData.phases || []
            }}
          />
        )
      }
    }

    // Handle R2 files (files with saved status and R2 URL) - but skip images
    if (selectedFile.url && (selectedFile.status === 'saved' || selectedFile.isR2File) && selectedFile.fileType !== 'image') {
      if (loadingR2) {
        return (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p>Loading content from R2...</p>
            </div>
          </div>
        )
      }
      
      if (r2Error) {
        return (
          <div className="flex items-center justify-center h-full text-red-500">
            <div className="text-center">
              <p className="mb-2">{r2Error}</p>
              <p className="text-sm text-gray-500">URL: {selectedFile.url}</p>
            </div>
          </div>
        )
      }
      
      if (!r2Content) {
        return (
          <div className="flex items-center justify-center h-full text-gray-500">
            <p>No content available</p>
          </div>
        )
      }
      
      // Use R2 content for rendering
      switch (selectedFile.fileType) {
        case 'markdown':
          // Check if this is an assessment file and fetch data from DB
          if (isAssessmentFile(selectedFile.name, selectedFile.status)) {
            return <AssessmentFromDatabase selectedFile={selectedFile} />
          }
          
          return (
            <TrueWYSIWYGEditor 
              content={r2Content} 
              isEditable={true}
              editMode={editMode}
              onEditModeChange={setEditMode}
              onHasChangesChange={setHasChanges}
              onContentChange={setCurrentEditedContent}
              onSave={(content: string) => {
                // TODO: Implement save to R2
              }}
            />
          )
        default:
          return (
            <div className="p-4">
              <pre className="whitespace-pre-wrap text-sm text-gray-700">
                {r2Content}
              </pre>
            </div>
          )
      }
    }

    // Handle different file types - images don't need content, just URL
    switch (selectedFile.fileType) {
      case 'image':
        return <ImagePreview content={selectedFile.content} name={selectedFile.name} url={selectedFile.url} />
      case 'markdown':
        // First check if this file has been generated and saved to R2
        // This should take priority over checking placeholder content
        if (selectedFile.url && selectedFile.status === 'saved') {
          // This is a generated file with R2 content - the R2 section above should handle it
          // But if we reach here, it means R2 fetch failed or is in progress
          if (loadingR2) {
            return (
              <div className="flex items-center justify-center h-full text-gray-500">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  <p>Loading generated content...</p>
                </div>
              </div>
            )
          }
          if (r2Error) {
            return (
              <div className="flex items-center justify-center h-full text-red-500">
                <div className="text-center">
                  <p className="mb-2">Failed to load generated content</p>
                  <p className="text-sm text-gray-500">Error: {r2Error}</p>
                  <p className="text-xs text-gray-400 mt-2">URL: {selectedFile.url}</p>
                </div>
              </div>
            )
          }
          if (r2Content) {
            return (
              <TrueWYSIWYGEditor 
                content={r2Content} 
                isEditable={true}
                editMode={editMode}
                onEditModeChange={setEditMode}
                onHasChangesChange={setHasChanges}
                onContentChange={setCurrentEditedContent}
                onSave={(content: string) => {
                  // TODO: Implement save to R2
                }}
              />
            )
          }
        }
        
        // Check if this is a file that's currently being generated
        if (selectedFile.status === 'generating') {
          return (
            <div className="flex items-center justify-center h-full text-gray-500">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="mb-2">Content is being generated...</p>
                <p className="text-sm text-gray-400">Please wait while the content is created</p>
              </div>
            </div>
          )
        }
        
        // Check if this is a file that hasn't been generated yet (but show title/description if available)
        if (!selectedFile.content || 
            (selectedFile.content.includes('This content is pending generation') && 
             !selectedFile.content.includes('**Description:**') && 
             !selectedFile.content.includes('# '))) {
          return (
            <div className="flex items-center justify-center h-full text-gray-500">
              <div className="text-center">
                <p className="mb-2">This content is pending generation</p>
                <p className="text-sm text-gray-400">Content will appear here once generated</p>
              </div>
            </div>
          )
        }
        
        // Check if this is assessment content that has been properly generated and has a valid materialId
        if (selectedFile.content && isAssessmentFile(selectedFile.name, selectedFile.status, (selectedFile as FileData & { materialType?: string }).materialType, selectedFile.materialId)) {
          // Use AssessmentFromDatabase only for completed assessment files with valid materialId
          return <AssessmentFromDatabase selectedFile={selectedFile} />
        }
        
        // Regular markdown file with content
        return (
          <TrueWYSIWYGEditor 
            content={selectedFile.content} 
            isEditable={true}
            isStreaming={isStreaming}
            editMode={editMode}
            onEditModeChange={setEditMode}
            onHasChangesChange={setHasChanges}
            onContentChange={setCurrentEditedContent}
            targetedChange={selectedFile.targetedChange}
            researchProgress={selectedFile.researchProgress}
            onSave={(content: string) => {
              // TODO: Implement save functionality for regular files
            }}
          />
        )
      case 'pdf':
        return <PDFPreview name={selectedFile.name} />
      case 'slide-template':
        if (!selectedFile.content) {
          return (
            <div className="flex items-center justify-center h-full text-gray-500">
              <p>No content available</p>
            </div>
          )
        }
        return <SlideTemplatePreview content={selectedFile.content} name={selectedFile.name} />
      default:
        if (!selectedFile.content) {
          return (
            <div className="flex items-center justify-center h-full text-gray-500">
              <p>No content available</p>
            </div>
          )
        }
        return (
          <div className="p-4">
            <pre className="whitespace-pre-wrap text-sm text-gray-700">
              {selectedFile.content}
            </pre>
          </div>
        )
    }
  }

  const handleSaveFile = async (content: string) => {
    try {
      // Get course ID from URL
      const pathParts = window.location.pathname.split('/')
      const courseId = pathParts[pathParts.indexOf('create') + 1]
      
      if (!courseId) {
        return false
      }
      
      // Get auth token
      const token = localStorage.getItem('auth_token')
      if (!token) {
        alert('Authentication required. Please sign in again.')
        return false
      }
      
      // Prepare the save request
      const saveRequest = {
        file_name: selectedFile?.name || 'unknown.md',
        content: content,
        file_type: selectedFile?.fileType || 'markdown'
      }
      
      // Call the save API endpoint with correct URL and auth
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/courses/${courseId}/save-file`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(saveRequest)
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }
      
      const result = await response.json()
      
      // Update the local file content to reflect the saved state
      if (selectedFile) {
        selectedFile.content = content
      }
      
      return true
    } catch (error) {
      // You could show a toast notification here
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
      alert(`Failed to save file: ${errorMessage}`)
      return false
    }
  }

  const renderEditButtons = () => {
    if (selectedFile?.fileType !== 'markdown') return null
    
    return (
      <div className="flex items-center gap-2">
        {!editMode ? (
          <Button
            variant="outline"
            size="sm"
            onClick={() => setEditMode(true)}
            className="flex items-center gap-2"
          >
            <Edit className="h-4 w-4" />
            Edit
          </Button>
        ) : (
          <>
            <Button
              variant="default"
              size="sm"
              onClick={async () => {
                // Use the current edited content from the editor
                const contentToSave = currentEditedContent || selectedFile?.content || ''
                const success = await handleSaveFile(contentToSave)
                
                if (success) {
                  setHasChanges(false)
                  setEditMode(false)
                  // Update the original file content with the saved content
                  if (selectedFile) {
                    selectedFile.content = contentToSave
                  }
                }
              }}
              disabled={!hasChanges}
              className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400"
            >
              Save
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setHasChanges(false)
                setEditMode(false)
              }}
            >
              Cancel
            </Button>
          </>
        )}
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-gray-200 bg-gray-50 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold text-gray-900">Files Preview</h3>
          <span className="text-sm text-gray-500">• {selectedFile.name}</span>
        </div>
        {renderEditButtons()}
      </div>
      
      <div ref={scrollContainerRef} className="flex-1 overflow-y-auto">
        {renderFileContent()}
      </div>
    </div>
  )
}
