"use client"

import { useState, useEffect } from "react"
import { useRouter, useParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { DashboardLayout } from "@/components/layout/dashboard-layout"
import { CourseCreationNav } from "@/components/course-creation-nav"
import { BookOpen, ArrowRight, ArrowLeft, Upload, Edit, Sparkles, Loader2, FileText, Check, X } from "lucide-react"
import { courseAPI, Course } from "@/lib/api"
import { toast } from "sonner"
import { useDropzone } from "react-dropzone"
import dynamic from "next/dynamic"

// Dynamically import MDEditor to avoid SSR issues
const MDEditor = dynamic(
  () => import("@uiw/react-md-editor").then((mod) => mod.default),
  { ssr: false }
)

type TabType = "upload" | "editor" | "ai"

export default function CurriculumPage() {
  const router = useRouter()
  const params = useParams()
  const courseId = Array.isArray(params.id) ? params.id[0] : params.id as string

  const [course, setCourse] = useState<Course | null>(null)
  const [activeTab, setActiveTab] = useState<TabType>("upload")
  const [content, setContent] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  const [showDiffView, setShowDiffView] = useState(false)
  const [enhancementResult, setEnhancementResult] = useState<any>(null)
  const [originalContent, setOriginalContent] = useState("")
  const [acceptedChanges, setAcceptedChanges] = useState<Set<string>>(new Set())
  const [finalContent, setFinalContent] = useState("")

  // Load course data
  useEffect(() => {
    const loadCourse = async () => {
      try {
        const courseData = await courseAPI.getCourse(courseId)
        setCourse(courseData)
        if (courseData.curriculum_content) {
          setContent(courseData.curriculum_content)
        }
      } catch (error) {
        toast.error("Failed to load course")
        router.push("/courses")
      }
    }

    if (courseId) {
      loadCourse()
    }
  }, [courseId, router])

  // File upload handling
  const onDrop = async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    if (!file.name.endsWith('.md')) {
      toast.error("Please upload a markdown (.md) file")
      return
    }

    setIsLoading(true)
    try {
      const result = await courseAPI.uploadCurriculumFile(courseId, file)
      setContent(result.content)
      setHasUnsavedChanges(false)
      toast.success("Curriculum file uploaded and saved successfully!")
      setActiveTab("editor") // Switch to editor tab after upload
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to upload file")
    } finally {
      setIsLoading(false)
    }
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/markdown': ['.md']
    },
    multiple: false
  })

  // AI Generation
  const handleAIGenerate = async () => {
    if (!course) return

    setIsGenerating(true)
    try {
      const result = await courseAPI.generateCurriculum(courseId)
      setContent(result.content)
      
      // Auto-save the generated content
      await courseAPI.updateCurriculum(courseId, result.content)
      setHasUnsavedChanges(false)
      
      toast.success("Curriculum generated and saved successfully!")
      setActiveTab("editor") // Switch to editor to show generated content
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to generate curriculum")
    } finally {
      setIsGenerating(false)
    }
  }

  // AI Enhancement
  const handleEnhanceWithAI = async () => {
    if (!content.trim()) {
      toast.error("Please add some content to enhance")
      return
    }

    setIsGenerating(true)
    try {
      const result = await courseAPI.enhanceCurriculum(courseId, content)
      setOriginalContent(content)
      setEnhancementResult(result)
      setFinalContent(result.enhanced_content) // Initialize final content with AI suggestions
      setShowDiffView(true)
      toast.success("Enhancement suggestions ready for review!")
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to enhance curriculum")
    } finally {
      setIsGenerating(false)
    }
  }

  // Create line-by-line diff
  const createLineDiff = (original: string, enhanced: string) => {
    const originalLines = original.split('\n')
    const enhancedLines = enhanced.split('\n')
    const diffLines: Array<{
      type: 'unchanged' | 'removed' | 'added'
      originalIndex?: number
      enhancedIndex?: number
      content: string
      id: string
    }> = []

    let originalIndex = 0
    let enhancedIndex = 0
    let lineId = 0

    // Simple line-by-line comparison (in production, you'd use a proper diff algorithm)
    const maxLines = Math.max(originalLines.length, enhancedLines.length)
    
    for (let i = 0; i < maxLines; i++) {
      const originalLine = originalLines[i]
      const enhancedLine = enhancedLines[i]
      
      if (originalLine === enhancedLine) {
        // Unchanged line
        if (originalLine !== undefined) {
          diffLines.push({
            type: 'unchanged',
            originalIndex: originalIndex++,
            enhancedIndex: enhancedIndex++,
            content: originalLine,
            id: `unchanged-${lineId++}`
          })
        }
      } else {
        // Changed lines
        if (originalLine !== undefined) {
          diffLines.push({
            type: 'removed',
            originalIndex: originalIndex++,
            content: originalLine,
            id: `removed-${lineId++}`
          })
        }
        if (enhancedLine !== undefined) {
          diffLines.push({
            type: 'added',
            enhancedIndex: enhancedIndex++,
            content: enhancedLine,
            id: `added-${lineId++}`
          })
        }
      }
    }

    return diffLines
  }

  // Diff view handlers
  const handleAcceptAllChanges = () => {
    if (enhancementResult) {
      setContent(enhancementResult.enhanced_content)
      setHasUnsavedChanges(true)
      setShowDiffView(false)
      setEnhancementResult(null)
      setAcceptedChanges(new Set())
      toast.success("All changes accepted!")
    }
  }

  const handleRejectAllChanges = () => {
    setShowDiffView(false)
    setEnhancementResult(null)
    setAcceptedChanges(new Set())
    toast.info("Changes rejected")
  }

  const handleAcceptChange = (lineId: string) => {
    const newAccepted = new Set(acceptedChanges)
    newAccepted.add(lineId)
    setAcceptedChanges(newAccepted)
    toast.success("Line accepted")
  }

  const handleRejectChange = (lineId: string) => {
    const newAccepted = new Set(acceptedChanges)
    newAccepted.delete(lineId)
    setAcceptedChanges(newAccepted)
    toast.info("Line rejected")
  }

  const applySelectedChanges = () => {
    if (!enhancementResult || !originalContent) return

    const originalLines = originalContent.split('\n')
    const enhancedLines = enhancementResult.enhanced_content.split('\n')
    const resultLines: string[] = []

    // Build result line by line based on user decisions
    const maxLines = Math.max(originalLines.length, enhancedLines.length)
    
    for (let i = 0; i < maxLines; i++) {
      const originalLine = originalLines[i]
      const enhancedLine = enhancedLines[i]
      const lineId = `enhanced-${i}`
      
      if (originalLine === enhancedLine) {
        // Unchanged line - always use it
        if (originalLine !== undefined) {
          resultLines.push(originalLine)
        }
      } else {
        // Changed line - check user decision
        if (acceptedChanges.has(lineId)) {
          // User accepted the change - use enhanced line
          if (enhancedLine !== undefined) {
            resultLines.push(enhancedLine)
          }
        } else {
          // User rejected the change or didn't decide - use original line
          if (originalLine !== undefined) {
            resultLines.push(originalLine)
          }
        }
      }
    }

    // Apply the result
    setContent(resultLines.join('\n'))
    setHasUnsavedChanges(true)
    setShowDiffView(false)
    setEnhancementResult(null)
    setAcceptedChanges(new Set())
    
    const acceptedCount = acceptedChanges.size
    if (acceptedCount > 0) {
      toast.success(`Applied ${acceptedCount} accepted changes`)
    } else {
      toast.info("Applied changes (all enhancements rejected)")
    }
  }

  // Save content
  const handleSave = async () => {
    if (!content.trim()) {
      toast.error("Please add some curriculum content before saving")
      return
    }

    setIsSaving(true)
    try {
      await courseAPI.updateCurriculum(courseId, content)
      setHasUnsavedChanges(false)
      toast.success("Curriculum saved successfully!")
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to save curriculum")
    } finally {
      setIsSaving(false)
    }
  }

  // Continue to next step
  const handleContinue = async () => {
    if (hasUnsavedChanges) {
      await handleSave()
    }
    router.push(`/courses/create/${courseId}/pedagogy`)
  }

  if (!course) {
    return (
      <DashboardLayout title="Loading..." icon={BookOpen}>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout title={`Create Course: ${course.name}`} icon={BookOpen}>
      <div className="mx-auto">
        {/* Course Creation Navigation */}
        <CourseCreationNav course={course} currentStep="curriculum" />

        {/* Main Content */}
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl flex items-center">
              <FileText className="h-6 w-6 mr-2" />
              Curriculum Setup
            </CardTitle>
            <CardDescription>
              Create your detailed week-by-week curriculum. Choose how you'd like to add the content.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {/* Tab Navigation */}
            <div className="flex space-x-1 mb-6 bg-gray-100 p-1 rounded-lg">
              <button
                onClick={() => setActiveTab("upload")}
                className={`flex-1 flex items-center justify-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeTab === "upload"
                    ? "bg-white text-blue-600 shadow-sm"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                <Upload className="h-4 w-4 mr-2" />
                Upload File
              </button>
              <button
                onClick={() => setActiveTab("editor")}
                className={`flex-1 flex items-center justify-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeTab === "editor"
                    ? "bg-white text-blue-600 shadow-sm"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                <Edit className="h-4 w-4 mr-2" />
                Editor
              </button>
              <button
                onClick={() => setActiveTab("ai")}
                className={`flex-1 flex items-center justify-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeTab === "ai"
                    ? "bg-white text-blue-600 shadow-sm"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                <Sparkles className="h-4 w-4 mr-2" />
                AI Generate
              </button>
            </div>

            {/* Tab Content */}
            <div className="min-h-[400px]">
              {activeTab === "upload" && (
                <div className="space-y-4">
                  <div
                    {...getRootProps()}
                    className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                      isDragActive
                        ? "border-blue-500 bg-blue-50"
                        : "border-gray-300 hover:border-gray-400"
                    }`}
                  >
                    <input {...getInputProps()} />
                    <Upload className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                    {isDragActive ? (
                      <p className="text-blue-600">Drop your markdown file here...</p>
                    ) : (
                      <div>
                        <p className="text-lg font-medium text-gray-900 mb-2">
                          Upload Curriculum File
                        </p>
                        <p className="text-gray-600 mb-4">
                          Drag and drop your curriculum.md file here, or click to browse
                        </p>
                        <Button variant="outline" disabled={isLoading}>
                          {isLoading ? (
                            <>
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                              Uploading...
                            </>
                          ) : (
                            "Choose File"
                          )}
                        </Button>
                      </div>
                    )}
                  </div>
                  <p className="text-sm text-gray-600">
                    Supported format: Markdown (.md) files only
                  </p>
                </div>
              )}

              {activeTab === "editor" && (
                <div className="space-y-4">
                  {!showDiffView ? (
                    <>
                      <div className="flex justify-between items-center">
                        <h3 className="text-lg font-medium">Curriculum Editor</h3>
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={handleEnhanceWithAI}
                            disabled={!content.trim() || isGenerating}
                          >
                            {isGenerating ? (
                              <>
                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                Enhancing...
                              </>
                            ) : (
                              <>
                                <Sparkles className="h-4 w-4 mr-2" />
                                Enhance with AI
                              </>
                            )}
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={handleSave}
                            disabled={isSaving || !hasUnsavedChanges}
                          >
                            {isSaving ? (
                              <>
                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                Saving...
                              </>
                            ) : (
                              "Save"
                            )}
                          </Button>
                        </div>
                      </div>
                      <div className="border rounded-lg overflow-hidden">
                        <MDEditor
                          value={content}
                          onChange={(val) => {
                            setContent(val || "")
                            setHasUnsavedChanges(true)
                          }}
                          height={400}
                          preview="edit"
                          hideToolbar={false}
                          data-color-mode="light"
                        />
                      </div>
                      {hasUnsavedChanges && (
                        <p className="text-sm text-amber-600">
                          You have unsaved changes. Don't forget to save!
                        </p>
                      )}
                    </>
                  ) : (
                    /* Side-by-Side Diff View */
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <h3 className="text-lg font-medium">AI Enhancement Suggestions</h3>
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={handleRejectAllChanges}
                          >
                            <X className="h-4 w-4 mr-2" />
                            Reject All
                          </Button>
                          <Button
                            size="sm"
                            onClick={handleAcceptAllChanges}
                            className="bg-green-600 hover:bg-green-700"
                          >
                            <Check className="h-4 w-4 mr-2" />
                            Accept All
                          </Button>
                        </div>
                      </div>
                      
                      {/* Simple Two-Column Diff View */}
                      <div className="border rounded-lg overflow-hidden bg-white">
                        {/* Header */}
                        <div className="bg-gray-50 px-4 py-2 border-b border-gray-200">
                          <h4 className="text-sm font-medium text-gray-700">Curriculum Enhancement Review</h4>
                        </div>
                        
                        <div className="grid grid-cols-2 divide-x divide-gray-200 max-h-96 overflow-hidden">
                          {/* Left Column - Original Content */}
                          <div className="flex flex-col">
                            <div className="bg-red-100 px-3 py-1 text-xs font-medium text-red-800 border-b border-red-200">
                              Original Content
                            </div>
                            <div className="overflow-y-auto max-h-80">
                              {originalContent.split('\n').map((line, index) => {
                                const enhancedLine = (enhancementResult?.enhanced_content || '').split('\n')[index]
                                const isChanged = line !== enhancedLine
                                
                                return (
                                  <div
                                    key={`original-${index}`}
                                    className={`flex items-start text-sm font-mono ${
                                      isChanged ? 'bg-red-50' : 'bg-white'
                                    } hover:bg-red-25`}
                                  >
                                    <div className="flex-shrink-0 w-8 px-1 py-1 text-xs text-gray-500 bg-gray-50 border-r border-gray-200 text-right">
                                      {index + 1}
                                    </div>
                                    <div className="flex-1 px-2 py-1 min-h-[24px] flex items-center">
                                      {isChanged && (
                                        <span className="inline-block w-4 text-center mr-2 text-red-600 font-bold">-</span>
                                      )}
                                      <span className="whitespace-pre-wrap">{line || ' '}</span>
                                    </div>
                                  </div>
                                )
                              })}
                            </div>
                          </div>
                          
                          {/* Right Column - AI Enhanced Content (Final) */}
                          <div className="flex flex-col">
                            <div className="bg-green-100 px-3 py-1 text-xs font-medium text-green-800 border-b border-green-200">
                              AI Enhanced (Final)
                            </div>
                            <div className="overflow-y-auto max-h-80">
                              {finalContent.split('\n').map((line: string, index: number) => {
                                const originalLine = originalContent.split('\n')[index]
                                const enhancedLine = (enhancementResult?.enhanced_content || '').split('\n')[index]
                                const isChanged = originalLine !== enhancedLine
                                const isRejected = line === originalLine && isChanged
                                const lineId = `line-${index}`
                                
                                return (
                                  <div
                                    key={`final-${index}`}
                                    className={`flex items-start text-sm font-mono ${
                                      isChanged ? (isRejected ? 'bg-red-50' : 'bg-green-50') : 'bg-white'
                                    } hover:bg-green-25`}
                                  >
                                    <div className="flex-shrink-0 w-8 px-1 py-1 text-xs text-gray-500 bg-gray-50 border-r border-gray-200 text-right">
                                      {index + 1}
                                    </div>
                                    <div className="flex-1 px-2 py-1 min-h-[24px] flex items-center justify-between">
                                      <div className="flex items-center flex-1">
                                        {isChanged && (
                                          <span className={`inline-block w-4 text-center mr-2 font-bold ${
                                            isRejected ? 'text-red-600' : 'text-green-600'
                                          }`}>
                                            {isRejected ? '-' : '+'}
                                          </span>
                                        )}
                                        <span className="whitespace-pre-wrap">{line || ' '}</span>
                                      </div>
                                      {isChanged && (
                                        <div className="flex gap-1 ml-2">
                                          <Button
                                            size="sm"
                                            variant={isRejected ? "outline" : "default"}
                                            onClick={() => {
                                              const finalLines = finalContent.split('\n')
                                              finalLines[index] = enhancedLine
                                              setFinalContent(finalLines.join('\n'))
                                              toast.success("Line accepted")
                                            }}
                                            className="h-5 w-5 p-0 bg-green-600 hover:bg-green-700 text-white hover:text-white"
                                            title="Accept AI suggestion"
                                          >
                                            <Check className="h-3 w-3" />
                                          </Button>
                                          <Button
                                            size="sm"
                                            variant={isRejected ? "default" : "outline"}
                                            onClick={() => {
                                              const finalLines = finalContent.split('\n')
                                              finalLines[index] = originalLine
                                              setFinalContent(finalLines.join('\n'))
                                              toast.success("Line rejected - using original")
                                            }}
                                            className="h-5 w-5 p-0 bg-red-600 hover:bg-red-700 text-white hover:text-white"
                                            title="Reject - use original"
                                          >
                                            <X className="h-3 w-3" />
                                          </Button>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                )
                              })}
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex justify-center">
                        <Button
                          onClick={() => {
                            setContent(finalContent)
                            setHasUnsavedChanges(true)
                            setShowDiffView(false)
                            setEnhancementResult(null)
                            toast.success("Changes applied!")
                          }}
                          className="bg-blue-600 hover:bg-blue-700"
                        >
                          Apply Changes
                        </Button>
                      </div>
                      
                      <div className="bg-blue-50 p-4 rounded-lg">
                        <h4 className="font-medium text-blue-900 mb-2">Simple Two-Column Review</h4>
                        <p className="text-sm text-blue-700">
                          <strong>Left:</strong> Original content. <strong>Right:</strong> AI enhanced content (final result).
                          Use ✓ to accept AI suggestions or ✗ to reject and use original content instead.
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {activeTab === "ai" && (
                <div className="space-y-6">
                  <div className="text-center py-8">
                    <Sparkles className="h-16 w-16 mx-auto text-blue-500 mb-4" />
                    <h3 className="text-xl font-semibold mb-2">AI-Generated Curriculum</h3>
                    <p className="text-gray-600 mb-6 max-w-md mx-auto">
                      Let AI create a comprehensive curriculum for "{course.name}" based on best practices and educational standards.
                    </p>
                    <Button
                      onClick={handleAIGenerate}
                      disabled={isGenerating}
                      size="lg"
                    >
                      {isGenerating ? (
                        <>
                          <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                          Generating Curriculum...
                        </>
                      ) : (
                        <>
                          <Sparkles className="h-5 w-5 mr-2" />
                          Generate Curriculum
                        </>
                      )}
                    </Button>
                  </div>
                  
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <h4 className="font-medium text-blue-900 mb-2">What will be generated:</h4>
                    <ul className="text-sm text-blue-700 space-y-1">
                      <li>• Course overview and objectives</li>
                      <li>• Detailed weekly schedule (12-16 weeks)</li>
                      <li>• Learning outcomes for each week</li>
                      <li>• Assessment methods and criteria</li>
                      <li>• Required resources and materials</li>
                    </ul>
                  </div>
                </div>
              )}
            </div>

            {/* Navigation */}
            <div className="flex justify-between pt-6 border-t">
              <Button
                variant="outline"
                onClick={() => router.push(`/courses/create?edit=${courseId}`)}
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back
              </Button>
              <Button
                onClick={handleContinue}
                disabled={!content.trim() || isSaving}
              >
                {isSaving ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    Next: Pedagogy
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}
