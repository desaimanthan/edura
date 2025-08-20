"use client"

import { useState, useEffect } from "react"
import { 
  Folder as FolderIcon, 
  FileText,
  Image as ImageIcon,
  ChevronRight,
  ChevronDown
} from "lucide-react"
import { Tree, Folder, File, type TreeViewElement } from "@/components/magicui/file-tree"
import { useCourseFileTree, courseFileOperations, type FileNode } from "@/lib/courseFileStore"

interface FileData {
  id: string
  name: string
  type: 'file' | 'folder'
  content?: string
  fileType?: 'markdown' | 'pdf' | 'image' | 'slide-template'
  children?: FileData[]
  url?: string // R2 URL for fetching content
  isR2File?: boolean
  status?: 'generating' | 'saved' | 'error' | 'pending' | 'streaming'
  displayTitle?: string // Human-readable title for display in UI
  materialId?: string // Database material ID for assessments and other content
}

interface CourseStructureProps {
  onFileSelect: (file: FileData) => void
  course?: any // The full course object from the API
}

export function CourseStructure({ onFileSelect, course }: CourseStructureProps) {
  const { tree, selectedPath } = useCourseFileTree()
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set([
    'root', 
    '/content',
    '/content/module-1',
    '/content/module-2',
    '/content/module-3',
    '/content/module-4',
    '/content/module-5',
    '/content/module-6'
  ]))


  // Convert FileNode to FileData for backward compatibility with onFileSelect
  const convertNodeToFileData = (node: FileNode): FileData => ({
    id: node.id,
    name: node.name,
    type: node.kind === 'folder' ? 'folder' : 'file',
    content: node.content,
    fileType: node.fileType,
    url: node.url,
    displayTitle: node.displayTitle, // Pass through displayTitle
    materialId: node.materialId // Pass through materialId
  })

  // Auto-expand parent folders when a file is selected
  const autoExpandParentFolders = (filePath: string) => {
    const parentPaths = courseFileOperations.getParentFolderPaths(filePath)
    if (parentPaths.length > 0) {
      setExpandedFolders(prev => {
        const newSet = new Set(prev)
        parentPaths.forEach((path: string) => newSet.add(path))
        return newSet
      })
    }
  }

  // Auto-select first file when tree changes (but not during content loading)
  useEffect(() => {
    if (tree.children && tree.children.length > 0 && !selectedPath) {
      // Check if content is currently loading to prevent auto-selection during that process
      const isLoading = courseFileOperations.isContentLoading()
      
      if (!isLoading) {
        const firstFile = tree.children[0]
        
        // Additional validation: ensure the first file has a proper URL if it's an image
        if (firstFile.fileType === 'image' && !firstFile.url) {
          return
        }
        
        courseFileOperations.setSelectedPath(firstFile.path)
        handleFileSelect(firstFile)
      }
    }
  }, [tree.children, selectedPath])

  // Auto-expand folders when selectedPath changes (for real-time auto-selection)
  useEffect(() => {
    if (selectedPath) {
      autoExpandParentFolders(selectedPath)
    }
  }, [selectedPath])

  const handleFileSelect = async (node: FileNode) => {
    courseFileOperations.setSelectedPath(node.path)
    
    // Convert to FileData and handle URL fetching
    const fileData = convertNodeToFileData(node)
    
    // Handle different file types
    if (node.fileType === 'image') {
      // For image files, don't fetch content - just pass the URL
      onFileSelect({
        ...fileData,
        url: node.url // Ensure URL is passed for image display
      })
    } else {
      // For all other files, just pass the data - let file-preview handle fetching
      // This prevents duplicate network calls
      onFileSelect({
        ...fileData,
        url: node.url,
        isR2File: node.source === 'r2',
        status: node.status
      })
    }
  }

  const handleTreeSelect = (nodeId: string) => {
    // Find the node by ID in the tree
    const findNodeById = (nodes: FileNode[], id: string): FileNode | null => {
      for (const node of nodes) {
        if (node.id === id) return node
        if (node.children) {
          const found = findNodeById(node.children, id)
          if (found) return found
        }
      }
      return null
    }

    const node = findNodeById(tree.children || [], nodeId)
    if (node) {
      handleFileSelect(node)
    }
  }

  const files = tree.children || []
  
  // Count total files recursively
  const countTotalFiles = (nodes: FileNode[]): number => {
    let count = 0
    for (const node of nodes) {
      if (node.kind === 'file') {
        count++
      }
      if (node.children) {
        count += countTotalFiles(node.children)
      }
    }
    return count
  }
  
  const totalFiles = countTotalFiles(files)
  
  // Toggle folder expansion
  const toggleFolder = (folderPath: string, event: React.MouseEvent) => {
    event.stopPropagation() // Prevent file selection when clicking chevron
    setExpandedFolders(prev => {
      const newSet = new Set(prev)
      if (newSet.has(folderPath)) {
        newSet.delete(folderPath)
      } else {
        newSet.add(folderPath)
      }
      return newSet
    })
  }

  // Render tree structure recursively with collapsible folders
  const renderTreeNode = (node: FileNode, level: number = 0): React.ReactNode => {
    const isFolder = node.kind === 'folder'
    const isSelected = selectedPath === node.path
    const hasChildren = node.children && node.children.length > 0
    const isExpanded = expandedFolders.has(node.path)
    
    // Choose appropriate icon
    const NodeIcon = isFolder ? FolderIcon : (node.fileType === 'image' ? ImageIcon : FileText)
    const iconColor = isFolder ? 'text-yellow-600' : (node.fileType === 'image' ? 'text-blue-600' : 'text-gray-600')
    
    return (
      <div key={node.id}>
        <div
          className={`flex items-center gap-2 py-1 px-2 hover:bg-gray-50 cursor-pointer rounded-md transition-colors ${
            isSelected ? 'bg-slate-50 border-l-2 border-slate-500' : ''
          }`}
          style={{ paddingLeft: `${8 + level * 16}px` }}
          onClick={() => isFolder ? toggleFolder(node.path, event as any) : handleTreeSelect(node.id)}
        >
          {/* Chevron for folders */}
          {isFolder && hasChildren && (
            <button
              onClick={(e) => toggleFolder(node.path, e)}
              className="p-0.5 hover:bg-gray-200 rounded transition-colors"
            >
              {isExpanded ? (
                <ChevronDown className="h-3 w-3 text-gray-500" />
              ) : (
                <ChevronRight className="h-3 w-3 text-gray-500" />
              )}
            </button>
          )}
          
          {/* Icon spacing for files without chevron */}
          {(!isFolder || !hasChildren) && (
            <div className="w-4 h-4 flex-shrink-0" />
          )}
          
          <NodeIcon className={`h-4 w-4 ${iconColor} flex-shrink-0`} />
          <span 
            className="text-sm text-gray-700 truncate flex-1"
            onClick={(e) => {
              if (!isFolder) {
                e.stopPropagation()
                handleTreeSelect(node.id)
              }
            }}
          >
            {node.displayTitle || node.name}
          </span>
          {isFolder && hasChildren && (
            <span className="text-xs text-gray-400">
              ({node.children?.length})
            </span>
          )}
        </div>
        
        {/* Render children only if folder is expanded - THIS IS THE KEY PERFORMANCE FIX */}
        {isFolder && hasChildren && isExpanded && (
          <div>
            {node.children?.map(child => renderTreeNode(child, level + 1))}
          </div>
        )}
      </div>
    )
  }
  
  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-gray-50 h-16 flex items-center">
        <div className="flex items-center justify-between w-full">
          <h3 className="font-semibold text-gray-900">Course Files</h3>
          <div className="text-xs text-gray-500">
            {totalFiles} file{totalFiles !== 1 ? 's' : ''}
          </div>
        </div>
      </div>
      
      {/* File Tree */}
      <div className="flex-1 p-2 overflow-y-auto">
        {files.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <FolderIcon className="h-16 w-16 mx-auto mb-4 text-gray-300" />
              <p className="text-sm font-medium mb-2">No files yet</p>
              <p className="text-xs text-gray-400">Generate course content to see files here</p>
            </div>
          </div>
        ) : (
          <div className="space-y-1">
            {files.map(file => renderTreeNode(file))}
          </div>
        )}
      </div>
    </div>
  )
}
