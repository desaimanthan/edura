"use client"

import { useEffect, useState, use } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { BookOpen, Clock, Users, CheckCircle, PlayCircle, FileText, ChevronRight, ChevronDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { PublicCourseData, CourseMaterial } from "@/types/course"
import { toast } from "sonner"
import { cn } from "@/lib/utils"

interface PublicCourseViewProps {
  params: Promise<{ courseId: string }>
}

export default function PublicCourseView({ params }: PublicCourseViewProps) {
  const resolvedParams = use(params)
  const searchParams = useSearchParams()
  const router = useRouter()
  const [course, setCourse] = useState<PublicCourseData | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedMaterial, setSelectedMaterial] = useState<CourseMaterial | null>(null)
  const [expandedModules, setExpandedModules] = useState<Set<number>>(new Set())
  const [expandedChapters, setExpandedChapters] = useState<Set<string>>(new Set())

  useEffect(() => {
    loadPublicCourse()
  }, [resolvedParams.courseId])

  const loadPublicCourse = async () => {
    try {
      const accessKey = searchParams.get('key')
      const url = new URL(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/courses/${resolvedParams.courseId}/public`)
      
      if (accessKey) {
        url.searchParams.set('access_key', accessKey)
      }

      const response = await fetch(url.toString())

      if (!response.ok) {
        if (response.status === 404) {
          toast.error('Course not found or not published')
          router.push('/')
          return
        } else if (response.status === 403) {
          toast.error('Access denied. Invalid access key.')
          router.push('/')
          return
        }
        throw new Error('Failed to load course')
      }

      const data = await response.json()
      setCourse(data.course)

      // Debug: Log the content structure to understand its format
      console.log('Content structure:', data.course.content_structure)
      console.log('Materials:', data.course.materials)

      // Auto-expand first module and select first slide (not assessment)
      if (data.course.materials && data.course.materials.length > 0) {
        // Sort materials to ensure proper order
        const sortedMaterials = [...data.course.materials].sort((a, b) => {
          if (a.module_number !== b.module_number) {
            return a.module_number - b.module_number
          }
          if (a.chapter_number !== b.chapter_number) {
            return a.chapter_number - b.chapter_number
          }
          // Prioritize slides over assessments
          if (a.material_type !== b.material_type) {
            return a.material_type === 'slide' ? -1 : 1
          }
          return (a.slide_number || 0) - (b.slide_number || 0)
        })
        
        // Find the first slide (not assessment)
        const firstSlide = sortedMaterials.find(m => m.material_type === 'slide') || sortedMaterials[0]
        
        if (firstSlide) {
          setExpandedModules(new Set([firstSlide.module_number]))
          setExpandedChapters(new Set([`${firstSlide.module_number}_${firstSlide.chapter_number}`]))
          setSelectedMaterial(firstSlide)
        }
      }

    } catch (error) {
      console.error('Error loading public course:', error)
      toast.error('Failed to load course')
      router.push('/')
    } finally {
      setLoading(false)
    }
  }

  const toggleModule = (moduleNumber: number) => {
    setExpandedModules(prev => {
      const newSet = new Set(prev)
      if (newSet.has(moduleNumber)) {
        newSet.delete(moduleNumber)
      } else {
        newSet.add(moduleNumber)
      }
      return newSet
    })
  }

  const toggleChapter = (chapterKey: string) => {
    setExpandedChapters(prev => {
      const newSet = new Set(prev)
      if (newSet.has(chapterKey)) {
        newSet.delete(chapterKey)
      } else {
        newSet.add(chapterKey)
      }
      return newSet
    })
  }

  // Build tree structure from materials
  const buildCourseTree = () => {
    if (!course || !course.materials) return {}
    
    const tree: Record<number, Record<number, CourseMaterial[]>> = {}
    
    course.materials.forEach((material: CourseMaterial) => {
      const moduleNum = material.module_number
      const chapterNum = material.chapter_number
      
      if (!tree[moduleNum]) {
        tree[moduleNum] = {}
      }
      
      if (!tree[moduleNum][chapterNum]) {
        tree[moduleNum][chapterNum] = []
      }
      
      tree[moduleNum][chapterNum].push(material)
    })
    
    // Sort materials within each chapter by slide_number
    Object.values(tree).forEach(module => {
      Object.values(module).forEach(chapter => {
        chapter.sort((a, b) => {
          // Slides first, then assessments
          if (a.material_type !== b.material_type) {
            return a.material_type === 'slide' ? -1 : 1
          }
          // Then by slide number
          return (a.slide_number || 0) - (b.slide_number || 0)
        })
      })
    })
    
    return tree
  }

  const renderMaterialContent = (material: CourseMaterial) => {
    if (material.material_type === 'assessment' && material.assessment_data) {
      // Render assessment content
      const assessmentData = material.assessment_data
      return (
        <div className="space-y-6">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <div className="flex items-center gap-2 mb-4">
              <FileText className="h-5 w-5 text-blue-600" />
              <h4 className="font-semibold text-blue-900">Assessment</h4>
              <Badge variant="outline" className="ml-auto">
                {material.assessment_format || 'Quiz'}
              </Badge>
            </div>
            
            <p className="text-sm text-blue-800 mb-4">{material.description}</p>
            
            {assessmentData.question && (
              <div className="space-y-4">
                <div className="bg-white rounded-lg p-4 border border-blue-100">
                  <p className="font-medium text-gray-900 mb-3">
                    {typeof assessmentData.question === 'object' ? assessmentData.question.text : assessmentData.question}
                  </p>
                  
                  {typeof assessmentData.question === 'object' && assessmentData.question.options && assessmentData.question.options.length > 0 && (
                    <div className="space-y-2">
                      {assessmentData.question.options.map((option: { id: string; text: string } | string, index: number) => (
                        <div key={index} className="flex items-start gap-3 p-2 rounded hover:bg-gray-50">
                          <div className="w-5 h-5 mt-0.5 border-2 border-gray-300 rounded-full flex-shrink-0"></div>
                          <span className="text-sm text-gray-700">
                            {typeof option === 'object' ? `${option.id}) ${option.text}` : option}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                
                {typeof assessmentData.question === 'object' && assessmentData.question.correct_answer && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                    <p className="text-xs font-medium text-green-800 mb-1">Correct Answer:</p>
                    <p className="text-sm text-green-700">{assessmentData.question.correct_answer}</p>
                  </div>
                )}
                
                {typeof assessmentData.question === 'object' && assessmentData.question.explanation && (
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                    <p className="text-xs font-medium text-gray-700 mb-1">Explanation:</p>
                    <p className="text-sm text-gray-600">{assessmentData.question.explanation}</p>
                  </div>
                )}
              </div>
            )}
            
            <p className="text-xs text-gray-600 mt-4 italic">
              <strong>Note:</strong> This is a preview. Interactive assessments are available in the full course experience.
            </p>
          </div>
        </div>
      )
    } else {
      // Render slide/content material
      return (
        <div className="prose prose-lg max-w-none">
          {material.content ? (
            <div 
              className="space-y-4"
              dangerouslySetInnerHTML={{ 
                __html: material.content
                  .split('\n\n')
                  .map((paragraph: string) => {
                    // Process headers
                    if (paragraph.startsWith('### ')) {
                      return `<h3 class="text-lg font-medium mt-2 mb-1">${paragraph.substring(4)}</h3>`
                    }
                    if (paragraph.startsWith('## ')) {
                      return `<h2 class="text-xl font-semibold mt-3 mb-2">${paragraph.substring(3)}</h2>`
                    }
                    if (paragraph.startsWith('# ')) {
                      return `<h1 class="text-2xl font-bold mt-4 mb-2">${paragraph.substring(2)}</h1>`
                    }
                    
                    // Process lists
                    const listItems = paragraph.split('\n').filter(line => line.startsWith('- '))
                    if (listItems.length > 0) {
                      const items = listItems.map(item => 
                        `<li class="ml-4">${item.substring(2)
                          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                          .replace(/\*(.*?)\*/g, '<em>$1</em>')
                        }</li>`
                      ).join('')
                      return `<ul class="list-disc list-inside space-y-1">${items}</ul>`
                    }
                    
                    // Process tables
                    if (paragraph.includes('|')) {
                      const lines = paragraph.split('\n')
                      if (lines.length >= 3 && lines[1].includes('---')) {
                        const headers = lines[0].split('|').filter(h => h.trim())
                        const rows = lines.slice(2).filter(line => line.includes('|'))
                        
                        let tableHtml = '<table class="min-w-full divide-y divide-gray-200 my-4"><thead class="bg-gray-50"><tr>'
                        headers.forEach(header => {
                          tableHtml += `<th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">${header.trim()}</th>`
                        })
                        tableHtml += '</tr></thead><tbody class="bg-white divide-y divide-gray-200">'
                        
                        rows.forEach(row => {
                          const cells = row.split('|').filter(c => c.trim())
                          tableHtml += '<tr>'
                          cells.forEach(cell => {
                            tableHtml += `<td class="px-4 py-2 text-sm text-gray-900">${cell.trim()}</td>`
                          })
                          tableHtml += '</tr>'
                        })
                        
                        tableHtml += '</tbody></table>'
                        return tableHtml
                      }
                    }
                    
                    // Regular paragraph with bold and italic
                    return `<p>${paragraph
                      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                      .replace(/\*(.*?)\*/g, '<em>$1</em>')
                    }</p>`
                  })
                  .join('')
              }} 
            />
          ) : (
            <p className="text-gray-500 italic">Content not available</p>
          )}
        </div>
      )
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-sm text-gray-600">Loading course content...</p>
        </div>
      </div>
    )
  }

  if (!course) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white flex items-center justify-center">
        <div className="text-center">
          <BookOpen className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h1 className="text-2xl font-semibold text-gray-900 mb-2">Course Not Found</h1>
          <p className="text-gray-600">The course you&apos;re looking for is not available.</p>
          <Button 
            onClick={() => router.push('/')} 
            className="mt-4"
            variant="outline"
          >
            Return to Home
          </Button>
        </div>
      </div>
    )
  }

  const courseTree = buildCourseTree()
  const moduleNumbers = Object.keys(courseTree).map(Number).sort((a, b) => a - b)

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Header */}
      <div className="bg-white border-b shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-4 mb-4">
                {course.cover_image_small_public_url && (
                  <img 
                    src={course.cover_image_small_public_url} 
                    alt={course.name}
                    className="w-20 h-20 rounded-lg object-cover shadow-md"
                  />
                )}
                <div>
                  <h1 className="text-3xl font-bold text-gray-900">{course.name}</h1>
                  <div className="flex items-center gap-2 mt-2">
                    <Badge className="bg-green-100 text-green-800">
                      <CheckCircle className="h-3 w-3 mr-1" />
                      Published Course
                    </Badge>
                    {course.published_at && (
                      <span className="text-sm text-gray-500">
                        Published {new Date(course.published_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>
              </div>
              
              {course.description && (
                <p className="text-gray-600 mb-4 max-w-3xl">{course.description}</p>
              )}
              
              <div className="flex items-center gap-6 text-sm text-gray-500">
                <div className="flex items-center gap-1">
                  <BookOpen className="h-4 w-4" />
                  <span>{course.total_content_items || course.materials?.length || 0} materials</span>
                </div>
                <div className="flex items-center gap-1">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  <span>{course.completed_content_items || 0} completed</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Course Structure Tree */}
          <div className="lg:col-span-1">
            <Card className="sticky top-4">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Course Content</CardTitle>
                <CardDescription className="text-xs">
                  Navigate through modules and materials
                </CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                <div className="max-h-[calc(100vh-200px)] overflow-y-auto">
                  {moduleNumbers.length > 0 ? (
                    <div className="p-4 space-y-2">
                      {moduleNumbers.map((moduleNum) => {
                        const isModuleExpanded = expandedModules.has(moduleNum)
                        const moduleChapters = courseTree[moduleNum]
                        const chapterNumbers = Object.keys(moduleChapters).map(Number).sort((a, b) => a - b)
                        
                        return (
                          <div key={moduleNum} className="border rounded-lg overflow-hidden">
                            <button
                              onClick={() => toggleModule(moduleNum)}
                              className="w-full px-3 py-2 flex items-center gap-2 hover:bg-gray-50 transition-colors"
                            >
                              {isModuleExpanded ? (
                                <ChevronDown className="h-4 w-4 text-gray-500" />
                              ) : (
                                <ChevronRight className="h-4 w-4 text-gray-500" />
                              )}
                              <BookOpen className="h-4 w-4 text-blue-600" />
                              <span className="text-sm font-medium text-left flex-1">
                                Module {moduleNum}
                              </span>
                            </button>
                            
                            {isModuleExpanded && chapterNumbers.length > 0 && (
                              <div className="bg-gray-50 border-t">
                                {chapterNumbers.map((chapterNum) => {
                                  const chapterKey = `${moduleNum}_${chapterNum}`
                                  const isChapterExpanded = expandedChapters.has(chapterKey)
                                  const chapterMaterials = moduleChapters[chapterNum]
                                  
                                  return (
                                    <div key={chapterKey} className="border-b last:border-b-0">
                                      <button
                                        onClick={() => toggleChapter(chapterKey)}
                                        className="w-full px-4 py-2 flex items-center gap-2 hover:bg-gray-100 transition-colors"
                                      >
                                        {isChapterExpanded ? (
                                          <ChevronDown className="h-3 w-3 text-gray-400" />
                                        ) : (
                                          <ChevronRight className="h-3 w-3 text-gray-400" />
                                        )}
                                        <span className="text-xs font-medium text-gray-700 text-left flex-1">
                                          Chapter {moduleNum}.{chapterNum}
                                        </span>
                                        <Badge variant="secondary" className="text-xs px-1 py-0">
                                          {chapterMaterials.length}
                                        </Badge>
                                      </button>
                                      
                                      {isChapterExpanded && chapterMaterials.length > 0 && (
                                        <div className="bg-white">
                                          {chapterMaterials.map((material: CourseMaterial, index: number) => (
                                            <button
                                              key={material._id || `${chapterKey}_${index}`}
                                              onClick={() => setSelectedMaterial(material)}
                                              className={cn(
                                                "w-full px-6 py-2 flex items-center gap-2 text-left hover:bg-blue-50 transition-colors",
                                                selectedMaterial?._id === material._id && "bg-blue-50 border-l-2 border-blue-600"
                                              )}
                                            >
                                              {material.material_type === 'assessment' ? (
                                                <FileText className="h-3 w-3 text-orange-600" />
                                              ) : (
                                                <PlayCircle className="h-3 w-3 text-green-600" />
                                              )}
                                              <span className="text-xs text-gray-700 flex-1 truncate">
                                                {material.material_type === 'slide' && material.slide_number ? 
                                                  `Slide ${material.slide_number}: ${material.title}` : 
                                                  material.title
                                                }
                                              </span>
                                            </button>
                                          ))}
                                        </div>
                                      )}
                                    </div>
                                  )
                                })}
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  ) : (
                    <div className="p-4 text-center text-sm text-gray-500">
                      No course content available
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Main Content Area */}
          <div className="lg:col-span-3">
            {selectedMaterial ? (
              <Card>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-xl">{selectedMaterial.title}</CardTitle>
                      {selectedMaterial.description && (
                        <CardDescription className="mt-2">
                          {selectedMaterial.description}
                        </CardDescription>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={selectedMaterial.material_type === 'assessment' ? 'destructive' : 'default'}>
                        {selectedMaterial.material_type}
                      </Badge>
                      {selectedMaterial.slide_number && (
                        <Badge variant="secondary">
                          Slide {selectedMaterial.slide_number}
                        </Badge>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {renderMaterialContent(selectedMaterial)}
                  
                  {/* Navigation buttons */}
                  <div className="flex justify-between items-center mt-8 pt-4 border-t">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const currentIndex = course.materials.findIndex((m: CourseMaterial) => m._id === selectedMaterial._id)
                        if (currentIndex > 0) {
                          setSelectedMaterial(course.materials[currentIndex - 1])
                        }
                      }}
                      disabled={course.materials.findIndex((m: CourseMaterial) => m._id === selectedMaterial._id) === 0}
                    >
                      Previous
                    </Button>
                    
                    <span className="text-sm text-gray-500">
                      {course.materials.findIndex((m: CourseMaterial) => m._id === selectedMaterial._id) + 1} of {course.materials.length}
                    </span>
                    
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const currentIndex = course.materials.findIndex((m: CourseMaterial) => m._id === selectedMaterial._id)
                        if (currentIndex < course.materials.length - 1) {
                          setSelectedMaterial(course.materials[currentIndex + 1])
                        }
                      }}
                      disabled={course.materials.findIndex((m: CourseMaterial) => m._id === selectedMaterial._id) === course.materials.length - 1}
                    >
                      Next
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardHeader>
                  <CardTitle>Welcome to {course.name}</CardTitle>
                  <CardDescription>
                    Select a material from the course structure to begin learning
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {course.learning_outcomes && course.learning_outcomes.length > 0 && (
                    <div>
                      <h3 className="font-semibold mb-3 flex items-center gap-2">
                        <BookOpen className="h-4 w-4 text-blue-600" />
                        What you&apos;ll learn
                      </h3>
                      <ul className="space-y-2">
                        {course.learning_outcomes.map((outcome: string, index: number) => (
                          <li key={index} className="flex items-start gap-2">
                            <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                            <span className="text-gray-700">{outcome}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {course.prerequisites && course.prerequisites.length > 0 && (
                    <div>
                      <h3 className="font-semibold mb-3">Prerequisites</h3>
                      <ul className="space-y-2">
                        {course.prerequisites.map((prerequisite: string, index: number) => (
                          <li key={index} className="flex items-start gap-2">
                            <div className="w-2 h-2 bg-gray-400 rounded-full mt-2 flex-shrink-0"></div>
                            <span className="text-gray-700">{prerequisite}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  <Separator />
                  
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h4 className="font-medium text-blue-900 mb-2 flex items-center gap-2">
                      <PlayCircle className="h-4 w-4" />
                      Ready to start learning?
                    </h4>
                    <p className="text-sm text-blue-800">
                      Navigate through the course content using the sidebar. Each module contains chapters with learning materials and assessments.
                    </p>
                  </div>
                  
                  {/* Course statistics */}
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                      <div className="text-2xl font-bold text-gray-900">
                        {moduleNumbers.length}
                      </div>
                      <div className="text-xs text-gray-600">Modules</div>
                    </div>
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                      <div className="text-2xl font-bold text-gray-900">
                        {course.materials?.length || 0}
                      </div>
                      <div className="text-xs text-gray-600">Materials</div>
                    </div>
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">
                        {course.completed_content_items || 0}
                      </div>
                      <div className="text-xs text-gray-600">Completed</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
