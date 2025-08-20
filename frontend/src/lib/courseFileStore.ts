"use client"

import { useSyncExternalStore } from 'react'

export type FileNodeKind = 'folder' | 'file'
export type FileNodeStatus = 'streaming' | 'pending' | 'saved' | 'error' | 'generating'
export type FileNodeSource = 'stream' | 'db' | 'r2'

interface ContentMaterial {
  _id?: string;
  id?: string;
  course_id?: string;
  module_number: number;
  chapter_number: number;
  material_type: string;
  title: string;
  description?: string;
  content?: string;
  status?: string;
  content_status?: string;
  r2_key?: string;
  public_url?: string;
  url?: string;
  created_at?: string;
  updated_at?: string;
  slide_number?: number | null;
  material_id?: string;
  file_path?: string;
}

export interface FileNode {
  id: string
  name: string
  path: string
  kind: FileNodeKind
  status: FileNodeStatus
  fileType?: 'markdown' | 'pdf' | 'image' | 'slide-template'
  content?: string
  url?: string
  r2Key?: string
  children?: FileNode[]
  version?: number
  source: FileNodeSource
  parentPath?: string
  createdAt?: number // Add timestamp for generation order
  slideNumber?: number | null // Add slide number for proper sorting and display
  displayTitle?: string // Human-readable title for display in UI
  materialId?: string // Database material ID for assessments and other content
}

export interface CourseFileTreeSnapshot {
  tree: FileNode
  nodesByPath: Map<string, FileNode>
  selectedPath: string | null
}

class CourseFileStore {
  private listeners = new Set<() => void>()
  private nodesByPath = new Map<string, FileNode>()
  private selectedPath: string | null = null
  private courseId: string | null = null
  private cachedSnapshot: CourseFileTreeSnapshot | null = null
  private snapshotVersion = 0
  private isLoadingContent = false // Flag to prevent auto-selection during content loading

  constructor() {
    // Initialize with root folder
    this.nodesByPath.set('/', {
      id: 'root',
      name: 'Course Files',
      path: '/',
      kind: 'folder',
      status: 'saved',
      children: [],
      source: 'stream'
    })
  }

  subscribe = (listener: () => void) => {
    this.listeners.add(listener)
    return () => {
      this.listeners.delete(listener)
    }
  }

  private notifyThrottleTimeout: NodeJS.Timeout | null = null
  private pendingNotification = false

  private notify = () => {
    this.snapshotVersion++
    this.cachedSnapshot = null // Invalidate cache
    
    // Throttle notifications to prevent excessive updates during streaming
    if (this.notifyThrottleTimeout) {
      this.pendingNotification = true
      return
    }
    
    this.performNotification()
    
    // Set throttle timeout - increased to 100ms for better performance
    this.notifyThrottleTimeout = setTimeout(() => {
      this.notifyThrottleTimeout = null
      if (this.pendingNotification) {
        this.pendingNotification = false
        this.performNotification()
      }
    }, 100) // 100ms throttle for better performance
  }

  private performNotification = () => {
    this.listeners.forEach((listener) => {
      try {
        listener()
      } catch (error) {
        console.error(`❌ [COURSE FILE STORE] Error in listener:`, error)
      }
    })
  }

  getSnapshot = (): CourseFileTreeSnapshot => {
    if (!this.cachedSnapshot) {
      this.cachedSnapshot = {
        tree: this.buildTree(),
        nodesByPath: new Map(this.nodesByPath),
        selectedPath: this.selectedPath
      }
    }
    return this.cachedSnapshot
  }

  private buildTree = (): FileNode => {
    const root = this.nodesByPath.get('/') || {
      id: 'root',
      name: 'Course Files',
      path: '/',
      kind: 'folder' as const,
      status: 'saved' as const,
      children: [],
      source: 'stream' as const
    }

    // Build children recursively
    const buildChildren = (parentPath: string): FileNode[] => {
      const children: FileNode[] = []
      
      for (const [path, node] of this.nodesByPath) {
        if (path === parentPath || path === '/') continue
        
        // Proper parent-child relationship validation
        // A node is a direct child if:
        // 1. It starts with the parent path + '/'
        // 2. It has exactly one more path segment than the parent
        
        const normalizedParentPath = parentPath === '/' ? '' : parentPath
        const expectedPrefix = normalizedParentPath + '/'
        
        if (path.startsWith(expectedPrefix)) {
          // Get the remaining path after the parent
          const remainingPath = path.substring(expectedPrefix.length)
          
          // Check if this is a direct child (no additional '/' in remaining path)
          if (remainingPath && !remainingPath.includes('/')) {
            const nodeWithChildren = {
              ...node,
              children: node.kind === 'folder' ? buildChildren(path) : undefined
            }
            children.push(nodeWithChildren)
          }
        }
      }
      
      return children.sort((a, b) => {
        // Folders first, then files
        if (a.kind !== b.kind) {
          return a.kind === 'folder' ? -1 : 1
        }
        
        // For files in content folders, sort by material type first (slides before assessments), then by slide number
        if (a.kind === 'file' && b.kind === 'file' && a.path.includes('/content/')) {
          // Extract material type and slide number from file names
          const getFileInfo = (node: FileNode) => {
            const fileName = node.name.toLowerCase()
            let materialType = 'other'
            let slideNumber = 0
            
            if (fileName.startsWith('slide-') || fileName.includes('slide ')) {
              materialType = 'slide'
              // Extract number from patterns like "slide-1", "slide 1:", etc.
              const slideMatch = fileName.match(/slide[-\s]?(\d+)/)
              if (slideMatch) {
                slideNumber = parseInt(slideMatch[1])
              }
            } else if (fileName.startsWith('assessment-') || fileName.includes('assessment ')) {
              materialType = 'assessment'
              // Extract number from patterns like "assessment-1", "assessment 1:", etc.
              const assessmentMatch = fileName.match(/assessment[-\s]?(\d+)/)
              if (assessmentMatch) {
                slideNumber = parseInt(assessmentMatch[1])
              }
            }
            
            // Use stored slideNumber if available (more reliable)
            if (node.slideNumber !== null && node.slideNumber !== undefined) {
              slideNumber = node.slideNumber
            }
            
            return { materialType, slideNumber }
          }
          
          const aInfo = getFileInfo(a)
          const bInfo = getFileInfo(b)
          
          // Define type priority: slides first, then assessments, then others
          const getTypePriority = (materialType: string) => {
            switch (materialType) {
              case 'slide': return 1
              case 'assessment': return 2
              default: return 3
            }
          }
          
          const aPriority = getTypePriority(aInfo.materialType)
          const bPriority = getTypePriority(bInfo.materialType)
          
          // First sort by material type priority
          if (aPriority !== bPriority) {
            return aPriority - bPriority
          }
          
          // Within the same type, sort by slide number
          if (aInfo.slideNumber !== bInfo.slideNumber) {
            return aInfo.slideNumber - bInfo.slideNumber
          }
          
          // Fallback to creation time if slide numbers are the same
          const aTime = a.createdAt || 0
          const bTime = b.createdAt || 0
          if (aTime !== bTime) {
            return aTime - bTime
          }
        }
        
        // For non-content files, sort alphabetically
        if (a.kind === 'file' && b.kind === 'file' && !a.path.includes('/content/')) {
          return a.name.localeCompare(b.name)
        }
        
        // Fallback to alphabetical for folders or files with same timestamp
        return a.name.localeCompare(b.name)
      })
    }

    const builtTree = {
      ...root,
      children: buildChildren('/')
    }
    
    return builtTree
  }

  private normalizePath = (path: string): string => {
    if (!path.startsWith('/')) {
      path = '/' + path
    }
    return path.replace(/\/+/g, '/').replace(/\/$/, '') || '/'
  }

  ensureFolder = (path: string): void => {
    const normalizedPath = this.normalizePath(path)
    if (normalizedPath === '/') return

    const segments = normalizedPath.split('/').filter(Boolean)
    let currentPath = ''

    for (const segment of segments) {
      currentPath += '/' + segment
      const normalizedCurrentPath = this.normalizePath(currentPath)

      if (!this.nodesByPath.has(normalizedCurrentPath)) {
        const parentPath = segments.length === 1 ? '/' : normalizedCurrentPath.substring(0, normalizedCurrentPath.lastIndexOf('/')) || '/'
        
        this.nodesByPath.set(normalizedCurrentPath, {
          id: normalizedCurrentPath.replace(/\//g, '_'),
          name: segment,
          path: normalizedCurrentPath,
          kind: 'folder',
          status: 'saved',
          children: [],
          source: 'stream',
          parentPath
        })
      }
    }
    
    this.saveToLocalStorage()
    this.notify()
  }

  upsertFile = (path: string, attrs: Partial<FileNode>): void => {
    const normalizedPath = this.normalizePath(path)
    const segments = normalizedPath.split('/').filter(Boolean)
    const fileName = segments[segments.length - 1]
    const parentPath = segments.length === 1 ? '/' : normalizedPath.substring(0, normalizedPath.lastIndexOf('/')) || '/'

    // Ensure parent folder exists
    if (parentPath !== '/') {
      this.ensureFolder(parentPath)
    }

    const existing = this.nodesByPath.get(normalizedPath)
    const newNode: FileNode = {
      id: normalizedPath.replace(/\//g, '_'),
      name: fileName,
      path: normalizedPath,
      kind: 'file',
      status: 'pending',
      source: 'stream',
      parentPath,
      createdAt: existing?.createdAt || Date.now(), // Preserve existing timestamp or set new one
      ...existing,
      ...attrs
    }

    this.nodesByPath.set(normalizedPath, newNode)
    
    // Auto-select file when it starts streaming (Issue 2 fix)
    if (attrs.status === 'streaming') {
      this.selectedPath = normalizedPath
    }
    
    this.saveToLocalStorage()
    this.notify()
  }

  appendContent = (path: string, chunk: string): void => {
    const normalizedPath = this.normalizePath(path)
    const existing = this.nodesByPath.get(normalizedPath)
    
    if (existing) {
      const updated = {
        ...existing,
        content: (existing.content || '') + chunk,
        status: 'streaming' as const,
        version: (existing.version || 0) + 1
      }
      this.nodesByPath.set(normalizedPath, updated)
      this.saveToLocalStorage()
      this.notify()
    }
  }

  setContent = (path: string, content: string): void => {
    const normalizedPath = this.normalizePath(path)
    const existing = this.nodesByPath.get(normalizedPath)
    
    if (existing) {
      const updated = {
        ...existing,
        content,
        status: 'streaming' as const,
        version: (existing.version || 0) + 1
      }
      this.nodesByPath.set(normalizedPath, updated)
      this.saveToLocalStorage()
      this.notify()
    }
  }

  finalizeFile = (path: string, attrs: { url?: string; r2Key?: string; status?: FileNodeStatus }): void => {
    const normalizedPath = this.normalizePath(path)
    const existing = this.nodesByPath.get(normalizedPath)
    
    if (existing) {
      const updated = {
        ...existing,
        ...attrs,
        status: attrs.status || 'saved' as const,
        source: attrs.url ? 'r2' as const : existing.source
      }
      this.nodesByPath.set(normalizedPath, updated)
      this.saveToLocalStorage()
      this.notify()
    }
  }

  removeNode = (path: string): void => {
    const normalizedPath = this.normalizePath(path)
    this.nodesByPath.delete(normalizedPath)
    
    // Remove all children if it's a folder
    for (const [nodePath] of this.nodesByPath) {
      if (nodePath.startsWith(normalizedPath + '/')) {
        this.nodesByPath.delete(nodePath)
      }
    }
    
    this.saveToLocalStorage()
    this.notify()
  }

  setSelectedPath = (path: string | null): void => {
    this.selectedPath = path
    this.notify()
  }

  // Get all parent folder paths for a given file path
  getParentFolderPaths = (filePath: string): string[] => {
    if (!filePath || filePath === '/') return []
    
    const parentPaths: string[] = []
    const segments = filePath.split('/').filter(Boolean)
    
    // Build parent paths progressively
    let currentPath = ''
    for (let i = 0; i < segments.length - 1; i++) { // -1 to exclude the file itself
      currentPath += '/' + segments[i]
      parentPaths.push(currentPath)
    }
    
    return parentPaths
  }

  // Auto-select file when it starts streaming (for Issue 2 fix)
  autoSelectStreamingFile = (path: string): void => {
    const normalizedPath = this.normalizePath(path)
    this.selectedPath = normalizedPath
    this.notify()
  }

  getSelectedNode = (): FileNode | null => {
    return this.selectedPath ? this.nodesByPath.get(this.selectedPath) || null : null
  }

  // Check if content is currently loading (prevents auto-selection)
  isContentLoading = (): boolean => {
    return this.isLoadingContent
  }

  clear = (): void => {
    this.nodesByPath.clear()
    this.nodesByPath.set('/', {
      id: 'root',
      name: 'Course Files',
      path: '/',
      kind: 'folder',
      status: 'saved',
      children: [],
      source: 'stream'
    })
    this.selectedPath = null
    this.saveToLocalStorage()
    this.notify()
  }

  setCourseId = (courseId: string): void => {
    if (this.courseId !== courseId) {
      console.log(`🔄 [COURSE FILE STORE] Switching from course ${this.courseId} to ${courseId}`)
      
      // Stop any existing periodic refresh
      this.stopPeriodicRefresh()
      
      // Clear existing data completely to prevent cross-contamination
      this.clear()
      
      // Set new course ID
      this.courseId = courseId
      
      // Load data for the new course from localStorage
      this.loadFromLocalStorage()
      
      console.log(`✅ [COURSE FILE STORE] Course switched to ${courseId}`)
    }
  }

  private getStorageKey = (): string => {
    return `courseFileTree_${this.courseId}`
  }

  private saveToLocalStorage = (): void => {
    if (!this.courseId) return
    
    try {
      // Create a lightweight version of the data for localStorage
        const lightweightNodes = Array.from(this.nodesByPath.entries()).map(([path, node]) => {
        // Only store essential data, exclude large content
        const lightNode = {
          id: node.id,
          name: node.name,
          path: node.path,
          kind: node.kind,
          status: node.status,
          fileType: node.fileType,
          url: node.url,
          r2Key: node.r2Key,
          source: node.source,
          parentPath: node.parentPath,
          createdAt: node.createdAt,
          slideNumber: node.slideNumber,
          materialId: node.materialId, // Include materialId in localStorage
          displayTitle: node.displayTitle, // Include displayTitle in localStorage
          version: node.version,
          // Only store content for small files or if no URL exists
          content: (!node.url && node.content && node.content.length < 1000) ? node.content : undefined
        }
        return [path, lightNode]
      })
      
      const data = {
        nodesByPath: lightweightNodes,
        selectedPath: this.selectedPath,
        timestamp: Date.now(),
        version: '2.0' // Version for future migrations
      }
      
      const serializedData = JSON.stringify(data)
      
      // Check if data size is reasonable (under 4MB to leave buffer)
      const dataSize = new Blob([serializedData]).size
      if (dataSize > 4 * 1024 * 1024) { // 4MB limit
        console.warn(`📦 [COURSE FILE STORE] Data size (${Math.round(dataSize / 1024)}KB) is large, implementing cleanup...`)
        this.performStorageCleanup()
        return
      }
      
      localStorage.setItem(this.getStorageKey(), serializedData)
      
      // Log storage usage for monitoring
      if (dataSize > 1024 * 1024) { // Log if over 1MB
        console.info(`📦 [COURSE FILE STORE] Saved ${Math.round(dataSize / 1024)}KB to localStorage`)
      }
      
    } catch (error) {
      if (error instanceof DOMException && error.name === 'QuotaExceededError') {
        console.warn('📦 [COURSE FILE STORE] localStorage quota exceeded, implementing fallback strategy...')
        this.handleQuotaExceeded()
      } else {
        console.warn('📦 [COURSE FILE STORE] Failed to save to localStorage:', error)
      }
    }
  }

  private performStorageCleanup = (): void => {
    try {
      // Strategy 1: Remove content from files that have URLs (can be fetched)
      const cleanedNodes = Array.from(this.nodesByPath.entries()).map(([path, node]) => {
        const cleanNode = {
          id: node.id,
          name: node.name,
          path: node.path,
          kind: node.kind,
          status: node.status,
          fileType: node.fileType,
          url: node.url,
          r2Key: node.r2Key,
          source: node.source,
          parentPath: node.parentPath,
          createdAt: node.createdAt,
          slideNumber: node.slideNumber,
          version: node.version,
          // Only keep content for files without URLs
          content: node.url ? undefined : node.content
        }
        return [path, cleanNode]
      })
      
      const cleanedData = {
        nodesByPath: cleanedNodes,
        selectedPath: this.selectedPath,
        timestamp: Date.now(),
        version: '2.0',
        cleaned: true
      }
      
      const serializedData = JSON.stringify(cleanedData)
      const dataSize = new Blob([serializedData]).size
      
      if (dataSize > 4 * 1024 * 1024) {
        // Still too large, use emergency cleanup
        this.performEmergencyCleanup()
        return
      }
      
      localStorage.setItem(this.getStorageKey(), serializedData)
      console.info(`📦 [COURSE FILE STORE] Cleanup successful, reduced to ${Math.round(dataSize / 1024)}KB`)
      
    } catch (error) {
      console.warn('📦 [COURSE FILE STORE] Cleanup failed:', error)
      this.performEmergencyCleanup()
    }
  }

  private performEmergencyCleanup = (): void => {
    try {
      // Emergency strategy: Only store structure, no content at all
      const structureOnlyNodes = Array.from(this.nodesByPath.entries()).map(([path, node]) => {
        const structureNode = {
          id: node.id,
          name: node.name,
          path: node.path,
          kind: node.kind,
          status: node.status,
          fileType: node.fileType,
          url: node.url,
          source: node.source,
          parentPath: node.parentPath,
          createdAt: node.createdAt,
          slideNumber: node.slideNumber
          // No content, no version, minimal data
        }
        return [path, structureNode]
      })
      
      const emergencyData = {
        nodesByPath: structureOnlyNodes,
        selectedPath: this.selectedPath,
        timestamp: Date.now(),
        version: '2.0',
        emergency: true
      }
      
      localStorage.setItem(this.getStorageKey(), JSON.stringify(emergencyData))
      console.warn('📦 [COURSE FILE STORE] Emergency cleanup applied - structure only saved')
      
    } catch (error) {
      console.error('📦 [COURSE FILE STORE] Emergency cleanup failed, clearing localStorage:', error)
      this.clearLocalStorage()
    }
  }

  private handleQuotaExceeded = (): void => {
    try {
      // Strategy 1: Clear old course data
      this.clearOldCourseData()
      
      // Strategy 2: Try saving again with cleanup
      this.performStorageCleanup()
      
    } catch (error) {
      console.error('📦 [COURSE FILE STORE] Quota exceeded handler failed:', error)
      // Last resort: clear all localStorage for this domain
      this.clearLocalStorage()
    }
  }

  private clearOldCourseData = (): void => {
    try {
      const keysToRemove: string[] = []
      
      // Find all courseFileTree keys
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        if (key && key.startsWith('courseFileTree_') && key !== this.getStorageKey()) {
          keysToRemove.push(key)
        }
      }
      
      // Remove old course data
      keysToRemove.forEach(key => {
        localStorage.removeItem(key)
      })
      
      if (keysToRemove.length > 0) {
        console.info(`📦 [COURSE FILE STORE] Cleared ${keysToRemove.length} old course data entries`)
      }
      
    } catch (error) {
      console.warn('📦 [COURSE FILE STORE] Failed to clear old course data:', error)
    }
  }

  private clearLocalStorage = (): void => {
    try {
      localStorage.removeItem(this.getStorageKey())
      console.warn('📦 [COURSE FILE STORE] Cleared localStorage for current course')
    } catch (error) {
      console.error('📦 [COURSE FILE STORE] Failed to clear localStorage:', error)
    }
  }

  // Enhanced method to get storage usage info
  getStorageInfo = (): { used: number; available: number; percentage: number } => {
    try {
      let used = 0
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        if (key) {
          const value = localStorage.getItem(key)
          if (value) {
            used += new Blob([key + value]).size
          }
        }
      }
      
      // Estimate available space (5MB is common limit)
      const estimated = 5 * 1024 * 1024 // 5MB
      const available = Math.max(0, estimated - used)
      const percentage = (used / estimated) * 100
      
      return { used, available, percentage }
    } catch (error) {
      return { used: 0, available: 0, percentage: 0 }
    }
  }

  private loadFromLocalStorage = (): void => {
    if (!this.courseId) return
    
    try {
      const stored = localStorage.getItem(this.getStorageKey())
      if (stored) {
        const data = JSON.parse(stored)
        
        // Handle different data versions
        if (data.version === '2.0') {
          // New lightweight format - restore full node structure
          this.nodesByPath = new Map(data.nodesByPath.map(([path, node]: [string, Partial<FileNode>]) => {
            const fullNode: FileNode = {
              id: node.id || '',
              name: node.name || '',
              path: node.path || '',
              kind: node.kind || 'file',
              status: node.status || 'pending',
              source: node.source || 'stream',
              fileType: node.fileType,
              url: node.url,
              r2Key: node.r2Key,
              parentPath: node.parentPath,
              createdAt: node.createdAt,
              slideNumber: node.slideNumber,
              materialId: node.materialId, // Restore materialId from localStorage
              displayTitle: node.displayTitle, // Restore displayTitle from localStorage
              version: node.version,
              content: node.content // Only small content was stored
            }
            return [path, fullNode]
          }))
          
          // Log if this was a cleaned or emergency save
          if (data.cleaned) {
            console.info('📦 [COURSE FILE STORE] Loaded cleaned data from localStorage')
          } else if (data.emergency) {
            console.warn('📦 [COURSE FILE STORE] Loaded emergency data from localStorage (structure only)')
          }
        } else {
          // Legacy format - direct map restoration
          this.nodesByPath = new Map(data.nodesByPath)
          console.info('📦 [COURSE FILE STORE] Loaded legacy data format from localStorage')
        }
        
        this.selectedPath = data.selectedPath
        
        // Ensure root exists
        if (!this.nodesByPath.has('/')) {
          this.nodesByPath.set('/', {
            id: 'root',
            name: 'Course Files',
            path: '/',
            kind: 'folder',
            status: 'saved',
            children: [],
            source: 'stream'
          })
        }
        
        this.notify()
      }
    } catch (error) {
      console.warn('📦 [COURSE FILE STORE] Failed to load from localStorage:', error)
      // Clear corrupted data
      this.clearLocalStorage()
    }
  }

  // Initialize from course data (DB URLs)
  initializeFromCourse = (course: Record<string, unknown>): void => {
    // Set loading flag IMMEDIATELY to prevent auto-selection during initialization
    this.isLoadingContent = true
    
    // DON'T clear existing files - preserve real-time updates
    // Only clear if this is the first initialization (no files exist except root)
    const hasExistingFiles = this.nodesByPath.size > 1 // More than just root folder
    
    if (!hasExistingFiles) {
      // First time initialization - safe to clear
      this.clear()
    }
    
    // Option 1: Dynamic files array (if backend supports it)
    if (course.files && Array.isArray(course.files)) {
      course.files.forEach((file: Record<string, unknown>) => {
        this.upsertFile((file.path as string) || `/${file.name as string}`, {
          fileType: ((file.type as string) || 'markdown') as 'markdown' | 'pdf' | 'image' | 'slide-template',
          url: file.url as string,
          status: 'saved',
          source: 'r2'
        })
      })
      return
    }

    // Handle cover image with priority for large size
    const coverImageUrl = course.cover_image_large_public_url || 
                         course.cover_image_public_url || 
                         course.cover_image_medium_public_url || 
                         course.cover_image_small_public_url ||
                         course.cover_image_large_url || 
                         course.cover_image_url || 
                         course.cover_image_medium_url || 
                         course.cover_image_small_url

    if (coverImageUrl && typeof coverImageUrl === 'string') {
      const existing = this.nodesByPath.get('/cover-image.png')
      const shouldUpdate = !existing || existing.url !== coverImageUrl || (!existing.url && coverImageUrl)
      
      if (shouldUpdate) {
        this.upsertFile('/cover-image.png', {
          fileType: 'image',
          url: coverImageUrl,
          status: 'saved',
          source: 'r2',
          createdAt: existing?.createdAt || 1
        });
      }
    }

    // Handle other files
    const otherFileProperties = {
      research_public_url: { path: '/research.md', type: 'markdown', createdAt: 2 },
      course_design_public_url: { path: '/course-design.md', type: 'markdown', createdAt: 3 },
      curriculum_public_url: { path: '/curriculum.md', type: 'markdown', createdAt: 4 }
    };

    for (const [key, { path, type, createdAt }] of Object.entries(otherFileProperties)) {
      if (course[key]) {
        // Update if file doesn't exist, URL has changed, or file exists without URL (newly generated)
        const existing = this.nodesByPath.get(this.normalizePath(path))
        const shouldUpdate = !existing || existing.url !== course[key] || (!existing.url && course[key])
        
        if (shouldUpdate) {
          this.upsertFile(path, {
            fileType: type as 'markdown' | 'pdf' | 'image' | 'slide-template',
            url: course[key] as string,
            status: 'saved',
            source: 'r2',
            createdAt: existing?.createdAt || createdAt // Preserve existing timestamp
          });
        }
      }
    }
    
    // Option 3: Load generated content materials from database
    this.loadContentMaterials((course.id || course._id) as string)
    
    // Clear loading flag after a short delay to allow auto-selection
    setTimeout(() => {
      this.isLoadingContent = false
      // Force a notification to allow auto-selection to work
      this.notify()
    }, 200)
    
    // Force a notification to update all subscribers
    this.notify()
  }

  // Force refresh Course Files UI with multiple notification attempts
  forceRefreshCourseFiles = (): void => {
    // Invalidate cache and trigger multiple notifications with delays
    this.cachedSnapshot = null
    this.snapshotVersion++
    
    // Immediate notification
    this.notify()
    
    // Reduced notifications for smoother UI experience
    const delays = [100, 300, 600]
    delays.forEach((delay, index) => {
      setTimeout(() => {
        this.notify()
      }, delay)
    })
  }

  // Force reload content materials (clears cache and reloads from API)
  forceReloadContentMaterials = async (): Promise<void> => {
    if (!this.courseId) return
    
    // Clear localStorage cache
    try {
      localStorage.removeItem(this.getStorageKey())
    } catch (error) {
      console.warn('Failed to clear localStorage cache:', error)
    }
    
      // Clear all content files from memory (but preserve other files like cover images)
      const contentPaths = Array.from(this.nodesByPath.keys()).filter(path => path.startsWith('/content/'))
      contentPaths.forEach(path => {
        this.nodesByPath.delete(path)
      })
    
    // Invalidate cache
    this.cachedSnapshot = null
    this.snapshotVersion++
    
    // Force immediate notification
    this.notify()
    
    // Reload content materials from API
    await this.loadContentMaterials(this.courseId)
  }

  // Periodically refresh course data to catch newly generated files (like cover images)
  startPeriodicRefresh = (courseId: string): void => {
    // Clear any existing interval
      if ((this as Record<string, unknown>).refreshInterval) {
        clearInterval((this as Record<string, unknown>).refreshInterval as NodeJS.Timeout)
      }

      // Set up periodic refresh every 5 seconds when course is being created
      ;(this as Record<string, unknown>).refreshInterval = setInterval(async () => {
      try {
        const token = localStorage.getItem('auth_token')
        if (!token) return

        const response = await fetch(`http://localhost:8000/courses/${courseId}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          cache: 'no-store'
        })

        if (response.ok) {
          const courseData = await response.json()
          this.initializeFromCourse(courseData)
        }
      } catch (error) {
        console.error('🔄 [COURSE FILE STORE] Periodic refresh error:', error)
      }
    }, 5000) // Every 5 seconds
  }

  stopPeriodicRefresh = (): void => {
    if ((this as Record<string, unknown>).refreshInterval) {
      clearInterval((this as Record<string, unknown>).refreshInterval as NodeJS.Timeout)
      ;(this as Record<string, unknown>).refreshInterval = null
    }
  }

  // Load generated content materials from the database
  loadContentMaterials = async (courseId: string): Promise<void> => {
    if (!courseId) {
      console.warn(`🚨 [COURSE FILE STORE] No courseId provided to loadContentMaterials`)
      return
    }

    // CRITICAL FIX: Strict validation that this courseId matches the current course
    if (this.courseId !== courseId) {
      console.error(`🚨 [COURSE FILE STORE] CRITICAL: Course ID mismatch! Store: ${this.courseId}, Request: ${courseId}. REJECTING REQUEST to prevent cross-contamination.`)
      return
    }

    console.log(`📚 [COURSE FILE STORE] Loading content materials for course: ${courseId} (Store course: ${this.courseId})`)

    try {
      // Set loading flag to prevent auto-selection during this process
      this.isLoadingContent = true
      
      console.log(`📚 [COURSE FILE STORE] Loading content materials for course: ${courseId}`)
      
      // Preserve important files before clearing
      const coverImageFile = this.nodesByPath.get('/cover-image.png')
      const researchFile = this.nodesByPath.get('/research.md')
      const courseDesignFile = this.nodesByPath.get('/course-design.md')
      const curriculumFile = this.nodesByPath.get('/curriculum.md')
      
      // Immediately invalidate any cached data to ensure fresh load
      this.cachedSnapshot = null
      this.snapshotVersion++
      
      // Clear any existing content files first to avoid stale data
      const contentPaths = Array.from(this.nodesByPath.keys()).filter(path => path.startsWith('/content/'))
      contentPaths.forEach(path => {
        this.nodesByPath.delete(path)
      })
      
      // Restore preserved files
      if (coverImageFile) {
        this.nodesByPath.set('/cover-image.png', coverImageFile)
      }
      if (researchFile) {
        this.nodesByPath.set('/research.md', researchFile)
      }
      if (courseDesignFile) {
        this.nodesByPath.set('/course-design.md', courseDesignFile)
      }
      if (curriculumFile) {
        this.nodesByPath.set('/curriculum.md', curriculumFile)
      }
      
      const token = localStorage.getItem('auth_token')
      if (!token) {
        console.warn(`🚨 [COURSE FILE STORE] No auth token found - user not authenticated`)
        // Force notification even without materials to ensure UI updates
        this.notify()
        return
      }
      
      console.log(`🌐 [COURSE FILE STORE] Fetching content materials from API for course: ${courseId}`)
      
      // Double-check course ID before making API call
      if (this.courseId !== courseId) {
        console.error(`🚨 [COURSE FILE STORE] Course ID changed during API call! Aborting. Store: ${this.courseId}, Request: ${courseId}`)
        return
      }
      
      const response = await fetch(`http://localhost:8000/courses/${courseId}/content-materials`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          console.error(`❌ [COURSE FILE STORE] Authentication failed. Status: ${response.status}. User may need to log in again.`)
          // Clear invalid token
          localStorage.removeItem('auth_token')
          localStorage.removeItem('auth_user')
        } else {
          console.error(`❌ [COURSE FILE STORE] Failed to fetch content materials. Status: ${response.status}`)
        }
        // Force notification even on error to ensure UI updates
        this.notify()
        return
      }

      const data = await response.json()
      const materials = data.materials || []
      
      // Final validation before processing materials
      if (this.courseId !== courseId) {
        console.error(`🚨 [COURSE FILE STORE] Course ID changed during data processing! Aborting. Store: ${this.courseId}, Request: ${courseId}`)
        return
      }
      
      console.log(`📊 [COURSE FILE STORE] Received ${materials.length} content materials for course: ${courseId} (Store course: ${this.courseId})`)
      
      if (materials.length === 0) {
        console.log(`📝 [COURSE FILE STORE] No content materials found for course: ${courseId}`)
        // Force notification even if no materials to ensure UI updates
        this.notify()
        return
      }

      // Create a simple structure: module -> chapter -> files
      const processedStructure: { [moduleKey: string]: { [chapterKey: string]: ContentMaterial[] } } = {}
      
      materials.forEach((material: ContentMaterial) => {
        const moduleKey = `${material.module_number}`
        const chapterKey = `${material.chapter_number}`
        
        if (!processedStructure[moduleKey]) {
          processedStructure[moduleKey] = {}
        }
        if (!processedStructure[moduleKey][chapterKey]) {
          processedStructure[moduleKey][chapterKey] = []
        }
        
        processedStructure[moduleKey][chapterKey].push(material)
      })

      // Create folders and files based on processed structure
      Object.entries(processedStructure).forEach(([moduleKey, moduleChapters]) => {
        const moduleNumber = parseInt(moduleKey)
        const modulePath = `/content/module-${moduleNumber}`
        
        // Ensure module folder exists
        this.ensureFolder(modulePath)
        
        // Update module folder name
        const moduleNode = this.nodesByPath.get(modulePath)
        if (moduleNode) {
          moduleNode.name = `Module ${moduleNumber}`
          this.nodesByPath.set(modulePath, moduleNode)
        }
        
        // Process each chapter in this module
        Object.entries(moduleChapters).forEach(([chapterKey, chapterMaterials]) => {
          const chapterNumber = parseInt(chapterKey)
          const chapterPath = `${modulePath}/chapter-${moduleNumber}-${chapterNumber}`
          
          // Ensure chapter folder exists
          this.ensureFolder(chapterPath)
          
          // Update chapter folder name
          const chapterNode = this.nodesByPath.get(chapterPath)
          if (chapterNode) {
            chapterNode.name = `Chapter ${moduleNumber}.${chapterNumber}`
            this.nodesByPath.set(chapterPath, chapterNode)
          }
          
          // Filter materials to only include those for THIS specific chapter
          const filteredMaterials = chapterMaterials.filter((material: ContentMaterial) => {
            return material.module_number === moduleNumber && material.chapter_number === chapterNumber
          })
          
          // Sort materials by material type first (slides before assessments), then by sequential number
          filteredMaterials.sort((a: ContentMaterial, b: ContentMaterial) => {
            // Define type priority: slides first, then assessments, then others
            const getTypePriority = (materialType: string) => {
              switch (materialType) {
                case 'slide': return 1
                case 'assessment': return 2
                case 'quiz': return 3
                default: return 4
              }
            }
            
            const aPriority = getTypePriority(a.material_type)
            const bPriority = getTypePriority(b.material_type)
            
            // First sort by material type priority
            if (aPriority !== bPriority) {
              return aPriority - bPriority
            }
            
            // Within the same type, sort by slide_number (sequential number)
            if (a.slide_number !== null && b.slide_number !== null && typeof a.slide_number === 'number' && typeof b.slide_number === 'number') {
              return a.slide_number - b.slide_number
            }
            
            // Materials with slide_number come before those without
            if (a.slide_number !== null && b.slide_number === null) {
              return -1
            }
            if (a.slide_number === null && b.slide_number !== null) {
              return 1
            }
            
            // For materials without slide_number, sort by title
            return a.title.localeCompare(b.title)
          })
          
          // Create files for this specific chapter ONLY
          filteredMaterials.forEach((material: ContentMaterial, materialIndex: number) => {
            
            // Create display name with sequential number for slides and assessments
            let displayName = material.title
            if (material.slide_number !== null) {
              if (material.material_type === 'slide') {
                displayName = `Slide ${material.slide_number}: ${material.title}`
              } else if (material.material_type === 'assessment') {
                displayName = `Assessment ${material.slide_number}: ${material.title}`
              }
            }
            
            const fileName = this.sanitizeFileName(displayName)
            const fileExtension = this.getFileExtension(material.material_type)
            const filePath = `${chapterPath}/${fileName}${fileExtension}`
            
            // Create content based on material type and content_status (database field)
            let content = ''
            let fileStatus: FileNodeStatus = 'pending'
            
            if (material.content_status === 'completed' && material.content) {
              // Material is completed with content - use the actual content
              content = material.content
              fileStatus = 'saved'
            } else if (material.content_status === 'not done') {
              // Material is not done - show title and description from DB
              const descriptionSection = material.description ? 
                `\n\n**Description:**\n${material.description}\n` : ''
              
              content = `# ${displayName}${descriptionSection}\n\n---\n\n*This content is pending generation. Click "Approve & Proceed" to start generating content.*`
              fileStatus = 'pending'
            } else if (material.content_status === 'generating') {
              // Material is being generated - show generating status
              const descriptionSection = material.description ? 
                `\n\n**Description:**\n${material.description}\n` : ''
              
              content = `# ${displayName}${descriptionSection}\n\n---\n\n*Content is being generated... Please wait.*`
              fileStatus = 'generating'
            } else {
              // Fallback for any other status
              const descriptionSection = material.description ? 
                `\n\n**Description:**\n${material.description}\n` : ''
              
              content = `# ${displayName}${descriptionSection}\n\n---\n\n*Content status: ${material.content_status || 'unknown'}*`
              fileStatus = 'pending'
            }

            // Calculate creation time to maintain the sorted order from above
            // Use materialIndex from the already-sorted array to preserve the correct order
            const createdAt = 1000 + (moduleNumber * 100) + (chapterNumber * 10) + materialIndex

            const materialId = material._id || material.id

            this.upsertFile(filePath, {
              fileType: 'markdown',
              content: content,
              status: fileStatus,
              source: 'db',
              createdAt: createdAt,
              slideNumber: material.slide_number, // Store sequential number for reference
              displayTitle: displayName, // Set human-readable display title
              materialId: materialId, // Store the actual database material ID - try both _id and id
              // Only set URL if material is completed and has both URL and content
              url: (material.content_status === 'completed' && material.url && material.content) ? material.url : undefined
            })
          })
        })
      })

      // Save to localStorage immediately before notifications
      this.saveToLocalStorage()
      
      // Optimized notification strategy - reduced for better performance
      // 1. Immediate notification
      this.notify()
      
      // 2. Follow-up notifications with reasonable delays
      const delays = [200, 500, 1000]
      delays.forEach((delay) => {
        setTimeout(() => {
          this.notify()
        }, delay)
      })

    } catch (error) {
      console.error(`❌ [COURSE FILE STORE] Error loading content materials for course ${courseId}:`, error)
      // Still trigger notification even on error to ensure UI updates
      this.notify()
      
      // Additional error recovery notifications
      setTimeout(() => this.notify(), 200)
      setTimeout(() => this.notify(), 500)
    } finally {
      // Clear loading flag and allow auto-selection after content loading is complete
      this.isLoadingContent = false
      
      // Trigger a final notification to allow auto-selection to work
      setTimeout(() => {
        this.notify()
      }, 100)
    }
  }

  // Helper method to sanitize file names
  private sanitizeFileName = (title: string): string => {
    return title
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '') // Remove special characters
      .replace(/\s+/g, '-') // Replace spaces with hyphens
      .replace(/-+/g, '-') // Replace multiple hyphens with single
      .replace(/^-|-$/g, '') // Remove leading/trailing hyphens
      .substring(0, 50) // Limit length
  }

  // Helper method to get file extension based on material type
  private getFileExtension = (materialType: string): string => {
    switch (materialType?.toLowerCase()) {
      case 'slide':
      case 'slides':
      case 'presentation':
        return '.md' // Slides as markdown for now
      case 'assessment':
      case 'quiz':
      case 'exam':
        return '.md'
      case 'assignment':
      case 'project':
        return '.md'
      case 'reading':
      case 'article':
        return '.md'
      case 'video':
      case 'lecture':
        return '.md' // Video scripts/notes as markdown
      default:
        return '.md'
    }
  }

  // Add a method to update a single file URL (for real-time updates)
  updateFileUrl = (path: string, url: string): void => {
    const normalizedPath = this.normalizePath(path)
    const existing = this.nodesByPath.get(normalizedPath)
    
    if (existing) {
      const updated = {
        ...existing,
        url: url,
        status: 'saved' as const,
        source: 'r2' as const
      }
      this.nodesByPath.set(normalizedPath, updated)
      this.saveToLocalStorage()
      this.notify()
    } else {
      // Create the file if it doesn't exist
      const fileName = normalizedPath.split('/').pop() || 'unknown'
      const fileType = fileName.endsWith('.png') || fileName.endsWith('.jpg') || fileName.endsWith('.jpeg') ? 'image' : 'markdown'
      
      this.upsertFile(normalizedPath, {
        fileType: fileType as 'markdown' | 'pdf' | 'image' | 'slide-template',
        url: url,
        status: 'saved',
        source: 'r2',
        createdAt: Date.now()
      })
    }
  }

  // Content material event handlers for real-time file/folder updates
  handleContentMaterialEvent = (eventData: Record<string, unknown>): void => {
    if (eventData.type === 'folder_created') {
      this.ensureFolder(eventData.file_path as string)
    } else if (eventData.type === 'material_created') {
      // Create content based on material type and status
      let content = ''
      if (eventData.description) {
        const materialTypeLabel = eventData.material_type === 'slide' ? 'Slide' : 
                                 eventData.material_type === 'assessment' ? 'Assessment' : 
                                 'Content'
        
        content = `# ${eventData.title}\n\n*This ${materialTypeLabel.toLowerCase()} is being generated...*\n\n**Description:**\n${eventData.description}\n\n---\n\n*Content will appear here as it's generated.*`
      } else {
        content = `# ${eventData.title}\n\n*This content is being generated...*\n\n---\n\n*Please wait while content is being created.*`
      }
      
      const normalizedPath = this.normalizePath(eventData.file_path as string)
      const existing = this.nodesByPath.get(normalizedPath)
      
      if (existing) {
        // Update existing file in place - preserve original createdAt and slideNumber
        this.upsertFile(eventData.file_path as string, {
          fileType: 'markdown',
          status: eventData.status === 'saved' ? 'saved' : 'generating',
          source: 'stream',
          content: content,
          createdAt: existing.createdAt, // Preserve original creation time for sorting
          slideNumber: existing.slideNumber, // Preserve original slide number
          displayTitle: existing.displayTitle || (eventData.title as string), // Preserve display title
          materialId: existing.materialId // CRITICAL: Preserve materialId for assessments
        })
      } else {
        // Create new file only if it doesn't exist
        this.upsertFile(eventData.file_path as string, {
          fileType: 'markdown',
          status: eventData.status === 'saved' ? 'saved' : 'generating',
          source: 'stream',
          content: content,
          createdAt: Date.now(),
          slideNumber: eventData.slide_number as number | null,
          displayTitle: eventData.title as string,
          materialId: eventData.material_id as string // Store materialId for new files
        })
      }
      
      // Auto-select the first material file for immediate feedback
      if (eventData.slide_number === 1 || !this.selectedPath) {
        this.autoSelectStreamingFile(eventData.file_path as string)
      }
    } else if (eventData.type === 'material_content_start') {
      // Handle agent_5 content generation start
      const normalizedPath = this.normalizePath(eventData.file_path as string)
      const existing = this.nodesByPath.get(normalizedPath)
      
      // CRITICAL FIX: Find existing file by materialId if path-based lookup fails
      let targetFile = existing
      let originalPath = normalizedPath
      
      if (!targetFile && eventData.material_id) {
        // Search for existing file with matching materialId
        for (const [path, node] of this.nodesByPath) {
          if (node.materialId === eventData.material_id) {
            targetFile = node
            originalPath = path
            break
          }
        }
      }
      
      // CRITICAL FIX: If we found an existing file by materialId, update it in place at its ORIGINAL path
      if (targetFile && originalPath !== normalizedPath) {
        // Update the existing file at its original path, don't create a new one
        this.upsertFile(originalPath, {
          fileType: 'markdown',
          status: 'generating',
          source: 'stream',
          content: `# ${eventData.title as string}\n\n*Generating comprehensive study material content...*\n\n---\n\n*Content will appear here as it's generated.*`,
          createdAt: targetFile.createdAt, // Preserve original creation time for sorting
          slideNumber: targetFile.slideNumber, // Preserve original slide number
          displayTitle: targetFile.displayTitle || (eventData.title as string), // Preserve display title
          materialId: targetFile.materialId || (eventData.material_id as string) // CRITICAL: Preserve materialId
        })
        
        // CRITICAL: Auto-select the ORIGINAL file path, not the event path
        this.setSelectedPath(originalPath)
      } else if (targetFile) {
        // Update existing file at the same path
        this.upsertFile(normalizedPath, {
          fileType: 'markdown',
          status: 'generating',
          source: 'stream',
          content: `# ${eventData.title as string}\n\n*Generating comprehensive study material content...*\n\n---\n\n*Content will appear here as it's generated.*`,
          createdAt: targetFile.createdAt, // Preserve original creation time for sorting
          slideNumber: targetFile.slideNumber, // Preserve original slide number
          displayTitle: targetFile.displayTitle || (eventData.title as string), // Preserve display title
          materialId: targetFile.materialId || (eventData.material_id as string) // CRITICAL: Preserve materialId
        })
        
        // Auto-select the file being generated
        this.setSelectedPath(normalizedPath)
      } else {
        // Create new file only if it doesn't exist anywhere
        this.upsertFile(normalizedPath, {
          fileType: 'markdown',
          status: 'generating',
          source: 'stream',
          content: `# ${eventData.title as string}\n\n*Generating comprehensive study material content...*\n\n---\n\n*Content will appear here as it's generated.*`,
          createdAt: Date.now(),
          slideNumber: eventData.slide_number as number | null,
          displayTitle: eventData.title as string,
          materialId: eventData.material_id as string
        })
        
        // Auto-select the new file
        this.setSelectedPath(normalizedPath)
      }
      
      // Force immediate notification
      this.notify()
    } else if (eventData.type === 'material_content_progress') {
      // Handle agent_5 content generation progress
      const existing = this.nodesByPath.get(this.normalizePath(eventData.file_path as string))
      if (existing) {
        this.upsertFile(eventData.file_path as string, {
          status: 'generating',
          content: existing.content + `\n\n*${eventData.message as string}*`,
          materialId: existing.materialId // Preserve materialId
        })
      }
    } else if (eventData.type === 'material_content_stream') {
      // Handle agent_5 content streaming
      const normalizedPath = this.normalizePath(eventData.file_path as string)
      let existing = this.nodesByPath.get(normalizedPath)
      let targetPath = normalizedPath
      
      // CRITICAL FIX: Find existing file by materialId if path-based lookup fails
      if (!existing && eventData.material_id) {
        // Search for existing file with matching materialId
        for (const [path, node] of this.nodesByPath) {
          if (node.materialId === eventData.material_id) {
            existing = node
            targetPath = path
            break
          }
        }
      }
      
      // Update file with streamed content at the correct path
      this.setContent(targetPath, eventData.content as string)
      
      // Ensure materialId is preserved during streaming
      if (existing && existing.materialId) {
        const updated = this.nodesByPath.get(targetPath)
        if (updated) {
          updated.materialId = existing.materialId
          this.nodesByPath.set(targetPath, updated)
        }
      }
      
      // Ensure file is selected during streaming (use the correct path)
      if (this.selectedPath !== targetPath) {
        this.setSelectedPath(targetPath)
      }
    } else if (eventData.type === 'material_content_complete') {
      // Handle agent_5 content generation completion
      const normalizedPath = this.normalizePath(eventData.file_path as string)
      let existing = this.nodesByPath.get(normalizedPath)
      let targetPath = normalizedPath
      
      // CRITICAL FIX: Find existing file by materialId if path-based lookup fails
      if (!existing && eventData.material_id) {
        // Search for existing file with matching materialId
        for (const [path, node] of this.nodesByPath) {
          if (node.materialId === eventData.material_id) {
            existing = node
            targetPath = path
            break
          }
        }
      }
      
      // CRITICAL FIX: Update content FIRST at the correct path, then finalize
      if (eventData.content) {
        this.setContent(targetPath, eventData.content as string)
      }
      
      // For assessments, DON'T set R2 URL since they should render from database
      const isAssessment = (eventData.title as string)?.toLowerCase().includes('assessment') || 
                          (eventData.title as string)?.toLowerCase().includes('true or false') ||
                          (eventData.title as string)?.toLowerCase().includes('quiz')
      
      if (isAssessment) {
        // For assessments: only update status, preserve materialId, NO R2 URL
        this.finalizeFile(targetPath, {
          status: 'saved'
          // Deliberately NOT setting url or r2Key for assessments
        })
        
        // Ensure materialId is preserved for assessments
        if (existing && existing.materialId) {
          const updated = this.nodesByPath.get(targetPath)
          if (updated) {
            updated.materialId = existing.materialId
            this.nodesByPath.set(targetPath, updated)
          }
        }
      } else {
        // For slides: set R2 URL and finalize normally
        this.finalizeFile(targetPath, {
          url: eventData.public_url as string,
          r2Key: eventData.r2_key as string,
          status: 'saved'
        })
      }
      
      // CRITICAL: Ensure file is selected and visible (use the correct path)
      this.setSelectedPath(targetPath)
      
      // Force multiple notifications to ensure UI updates
      this.notify()
      setTimeout(() => this.notify(), 100)
      setTimeout(() => this.notify(), 300)
      setTimeout(() => this.notify(), 600)
      
      // Force refresh to ensure UI updates
      setTimeout(() => {
        this.forceRefreshCourseFiles()
      }, 800)
    } else if (eventData.type === 'material_content_error') {
      // Handle agent_5 content generation error
      const existing = this.nodesByPath.get(this.normalizePath(eventData.file_path as string))
      
      this.finalizeFile(eventData.file_path as string, {
        status: 'error'
      })
      
      // Update with error content while preserving materialId
      const errorContent = `# Content Generation Failed\n\n**Error:** ${eventData.error_message as string}\n\n---\n\n*Please try generating the content again or contact support if the issue persists.*`
      this.setContent(eventData.file_path as string, errorContent)
      
      // Preserve materialId for error state
      if (existing && existing.materialId) {
        const updated = this.nodesByPath.get(this.normalizePath(eventData.file_path as string))
        if (updated) {
          updated.materialId = existing.materialId
          this.nodesByPath.set(this.normalizePath(eventData.file_path as string), updated)
        }
      }
      
      // Ensure error file is selected
      this.setSelectedPath(eventData.file_path as string)
    }
  }

  // Image generation event handlers
  handleImageGenerationStart = (filePath: string, imageType: string = 'cover'): void => {
    this.upsertFile(filePath, {
      fileType: 'image',
      status: 'generating',
      source: 'stream',
      createdAt: Date.now()
    })
    
    // Auto-select the generating image file
    this.autoSelectStreamingFile(filePath)
  }

  handleImageGenerationProgress = (filePath: string, stage: string, progressMessage: string): void => {
    const existing = this.nodesByPath.get(this.normalizePath(filePath))
    if (existing) {
      const updated = {
        ...existing,
        status: 'generating' as const,
        content: progressMessage, // Store progress message as content for display
        version: (existing.version || 0) + 1
      }
      this.nodesByPath.set(this.normalizePath(filePath), updated)
      this.saveToLocalStorage()
      this.notify()
    }
  }

  handleImageGenerationComplete = (filePath: string, publicUrl: string, r2Key: string, fileSize: number, metadata?: Record<string, unknown>): void => {
    this.finalizeFile(filePath, {
      url: publicUrl,
      r2Key: r2Key,
      status: 'saved'
    })
    
    // Update the existing node with additional metadata
    const existing = this.nodesByPath.get(this.normalizePath(filePath))
    if (existing && metadata && typeof metadata === 'object') {
      const updated: FileNode = {
        ...existing,
        content: undefined, // Clear progress message content
      }
      
      // Store metadata for potential future use with proper type checking
      if (metadata.images && typeof metadata.images === 'object') {
        (updated as unknown as Record<string, unknown>).images = metadata.images
      }
      
      if (metadata.image_metadata && typeof metadata.image_metadata === 'object') {
        (updated as unknown as Record<string, unknown>).imageMetadata = metadata.image_metadata
      }
      
      this.nodesByPath.set(this.normalizePath(filePath), updated)
    }
    
    this.saveToLocalStorage()
    this.notify()
  }

  handleImageGenerationError = (filePath: string, errorMessage: string, errorData?: Record<string, unknown>): void => {
    this.finalizeFile(filePath, {
      status: 'error'
    })
    
    // Update the existing node with enhanced error information
    const existing = this.nodesByPath.get(this.normalizePath(filePath))
    if (existing) {
      // Create detailed error content with recovery suggestions
      let errorContent = `# Image Generation Failed\n\n**Error:** ${errorMessage}\n\n`
      
      if (errorData) {
        if (errorData.error_type) {
          errorContent += `**Error Type:** ${errorData.error_type}\n\n`
        }
        
        if (errorData.recovery_suggestions && Array.isArray(errorData.recovery_suggestions) && errorData.recovery_suggestions.length > 0) {
          errorContent += `**Recovery Suggestions:**\n`
          errorData.recovery_suggestions.forEach((suggestion: unknown) => {
            if (typeof suggestion === 'string') {
              errorContent += `• ${suggestion}\n`
            }
          })
          errorContent += `\n`
        }
        
        if (errorData.can_retry) {
          errorContent += `**Retry Available:** Yes (${errorData.retry_count || 0}/3 attempts)\n\n`
        }
        
        if (errorData.metadata && typeof errorData.metadata === 'object') {
          const metadata = errorData.metadata as Record<string, unknown>
          errorContent += `**Additional Information:**\n`
          if (metadata.style_preference && typeof metadata.style_preference === 'string') {
            errorContent += `• Style: ${metadata.style_preference}\n`
          }
          if (metadata.image_type && typeof metadata.image_type === 'string') {
            errorContent += `• Type: ${metadata.image_type}\n`
          }
        }
      }
      
      errorContent += `---\n\n*You can try generating the image again or contact support if the issue persists.*`
      
      const updated = {
        ...existing,
        content: errorContent,
        version: (existing.version || 0) + 1,
        errorData: errorData // Store full error data for potential retry logic
      }
      this.nodesByPath.set(this.normalizePath(filePath), updated)
    }
    
    this.saveToLocalStorage()
    this.notify()
  }

}

// Global store instance
const courseFileStore = new CourseFileStore()

// React hook
export const useCourseFileTree = () => {
  return useSyncExternalStore(
    courseFileStore.subscribe,
    courseFileStore.getSnapshot,
    // Server snapshot for SSR/hydration stability
    () => ({
      tree: {
        id: 'root',
        name: 'Course Files',
        path: '/',
        kind: 'folder' as const,
        status: 'saved' as const,
        children: [],
        source: 'stream' as const
      },
      nodesByPath: new Map([
        ['/', {
          id: 'root',
          name: 'Course Files',
          path: '/',
          kind: 'folder' as const,
          status: 'saved' as const,
          children: [],
          source: 'stream' as const
        }]
      ]),
      selectedPath: null
    })
  )
}

// Store operations
export const courseFileOperations = {
  setCourseId: courseFileStore.setCourseId,
  ensureFolder: courseFileStore.ensureFolder,
  upsertFile: courseFileStore.upsertFile,
  appendContent: courseFileStore.appendContent,
  setContent: courseFileStore.setContent,
  finalizeFile: courseFileStore.finalizeFile,
  removeNode: courseFileStore.removeNode,
  setSelectedPath: courseFileStore.setSelectedPath,
  autoSelectStreamingFile: courseFileStore.autoSelectStreamingFile,
  getSelectedNode: courseFileStore.getSelectedNode,
  isContentLoading: courseFileStore.isContentLoading,
  getParentFolderPaths: courseFileStore.getParentFolderPaths,
  initializeFromCourse: courseFileStore.initializeFromCourse,
  updateFileUrl: courseFileStore.updateFileUrl,
  loadContentMaterials: courseFileStore.loadContentMaterials,
  forceRefreshCourseFiles: courseFileStore.forceRefreshCourseFiles,
  forceReloadContentMaterials: courseFileStore.forceReloadContentMaterials,
  startPeriodicRefresh: courseFileStore.startPeriodicRefresh,
  stopPeriodicRefresh: courseFileStore.stopPeriodicRefresh,
  clear: courseFileStore.clear,
  subscribe: courseFileStore.subscribe,
  getSnapshot: courseFileStore.getSnapshot,
  // Storage management
  getStorageInfo: courseFileStore.getStorageInfo,
  // Content material event handlers
  handleContentMaterialEvent: courseFileStore.handleContentMaterialEvent,
  // Image generation event handlers
  handleImageGenerationStart: courseFileStore.handleImageGenerationStart,
  handleImageGenerationProgress: courseFileStore.handleImageGenerationProgress,
  handleImageGenerationComplete: courseFileStore.handleImageGenerationComplete,
  handleImageGenerationError: courseFileStore.handleImageGenerationError
}
