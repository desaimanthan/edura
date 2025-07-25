'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ChevronLeft, ChevronRight, Play, Pause, RotateCcw, Download } from 'lucide-react'
import { courseAPI } from '@/lib/api'

interface SlideContent {
  main_content: string
  supporting_text: string
  table_data?: {
    headers: string[]
    rows: string[][]
  }
}

interface SlideImage {
  url: string
  alt_text: string
  prompt: string
}

interface Slide {
  slide_number: number
  title: string
  content: SlideContent
  template_type: string
  images: SlideImage[]
  layout_config: any
}

interface SlideDeck {
  slides: Slide[]
  deck_info?: {
    title: string
    description: string
    total_slides: number
    created_at: string
  }
  conversation_log?: any[]
  generation_metadata?: any
}

const TEMPLATE_STYLES = {
  GEOMETRIC_ABSTRACT: 'bg-gradient-to-br from-blue-50 to-indigo-100 border-l-4 border-blue-500',
  SPLIT_IMAGE_TEXT: 'bg-gradient-to-r from-gray-50 to-white border-l-4 border-gray-400',
  DATA_TABLE: 'bg-gradient-to-br from-green-50 to-emerald-100 border-l-4 border-green-500',
  PIE_CHART: 'bg-gradient-to-br from-purple-50 to-violet-100 border-l-4 border-purple-500',
  BAR_CHART: 'bg-gradient-to-br from-orange-50 to-amber-100 border-l-4 border-orange-500',
  KEY_METRICS: 'bg-gradient-to-br from-red-50 to-rose-100 border-l-4 border-red-500',
  THREE_POINT_GRID: 'bg-gradient-to-br from-teal-50 to-cyan-100 border-l-4 border-teal-500',
  FOUR_POINT_GRID: 'bg-gradient-to-br from-pink-50 to-rose-100 border-l-4 border-pink-500',
  TEXT_HEAVY: 'bg-gradient-to-br from-slate-50 to-gray-100 border-l-4 border-slate-500',
  BULLET_LIST: 'bg-gradient-to-br from-yellow-50 to-amber-100 border-l-4 border-yellow-500',
  CASE_STUDY: 'bg-gradient-to-br from-emerald-50 to-green-100 border-l-4 border-emerald-500',
  TIMELINE: 'bg-gradient-to-br from-indigo-50 to-blue-100 border-l-4 border-indigo-500',
  QUOTE: 'bg-gradient-to-br from-purple-50 to-indigo-100 border-l-4 border-purple-500',
  VIDEO_EMBED: 'bg-gradient-to-br from-red-50 to-pink-100 border-l-4 border-red-500',
  FULL_IMAGE: 'bg-gradient-to-br from-gray-50 to-slate-100 border-l-4 border-gray-500',
  SPLIT_VISUAL: 'bg-gradient-to-br from-cyan-50 to-blue-100 border-l-4 border-cyan-500',
  DUAL_POINT: 'bg-gradient-to-br from-lime-50 to-green-100 border-l-4 border-lime-500',
  SCATTER_PLOT: 'bg-gradient-to-br from-violet-50 to-purple-100 border-l-4 border-violet-500'
}

const formatContent = (content: string) => {
  // Handle bullet points
  if (content.includes('•') || content.includes('-')) {
    const lines = content.split('\n')
    return lines.map((line, index) => {
      if (line.trim().startsWith('•') || line.trim().startsWith('-')) {
        return (
          <li key={index} className="ml-4 mb-2">
            {line.replace(/^[•-]\s*/, '')}
          </li>
        )
      }
      return line && <p key={index} className="mb-2">{line}</p>
    })
  }

  // Handle numbered steps
  if (content.match(/^\d+\./m)) {
    const lines = content.split('\n')
    return lines.map((line, index) => {
      if (line.trim().match(/^\d+\./)) {
        return (
          <div key={index} className="mb-3 p-3 bg-blue-50 rounded-lg border-l-3 border-blue-400">
            <span className="font-semibold text-blue-800">{line}</span>
          </div>
        )
      }
      return line && <p key={index} className="mb-2">{line}</p>
    })
  }

  // Regular paragraphs
  return content.split('\n').map((paragraph, index) => 
    paragraph.trim() && <p key={index} className="mb-3 leading-relaxed">{paragraph}</p>
  )
}

const renderTable = (tableData: { headers: string[], rows: string[][] }) => {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse border border-gray-300 rounded-lg overflow-hidden shadow-sm">
        <thead>
          <tr className="bg-gray-100">
            {tableData.headers.map((header, index) => (
              <th key={index} className="border border-gray-300 px-4 py-3 text-left font-semibold text-gray-700">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {tableData.rows.map((row, rowIndex) => (
            <tr key={rowIndex} className={rowIndex % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              {row.map((cell, cellIndex) => (
                <td key={cellIndex} className="border border-gray-300 px-4 py-3 text-gray-600">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function SlidesPage() {
  const params = useParams()
  const courseId = params.id as string
  
  const [slideDeck, setSlideDeck] = useState<SlideDeck | null>(null)
  const [currentSlide, setCurrentSlide] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [autoPlayInterval, setAutoPlayInterval] = useState<NodeJS.Timeout | null>(null)

  useEffect(() => {
    fetchSlides()
  }, [courseId])

  useEffect(() => {
    if (isPlaying && slideDeck) {
      const interval = setInterval(() => {
        setCurrentSlide(prev => {
          if (prev >= slideDeck.slides.length - 1) {
            setIsPlaying(false)
            return prev
          }
          return prev + 1
        })
      }, 5000) // 5 seconds per slide
      setAutoPlayInterval(interval)
    } else {
      if (autoPlayInterval) {
        clearInterval(autoPlayInterval)
        setAutoPlayInterval(null)
      }
    }

    return () => {
      if (autoPlayInterval) {
        clearInterval(autoPlayInterval)
      }
    }
  }, [isPlaying, slideDeck])

  const fetchSlides = async () => {
    try {
      setIsLoading(true)
      const data = await courseAPI.getLatestSlides(courseId)
      setSlideDeck(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load slides')
    } finally {
      setIsLoading(false)
    }
  }

  const nextSlide = () => {
    if (slideDeck && currentSlide < slideDeck.slides.length - 1) {
      setCurrentSlide(currentSlide + 1)
    }
  }

  const prevSlide = () => {
    if (currentSlide > 0) {
      setCurrentSlide(currentSlide - 1)
    }
  }

  const toggleAutoPlay = () => {
    setIsPlaying(!isPlaying)
  }

  const resetPresentation = () => {
    setCurrentSlide(0)
    setIsPlaying(false)
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading slides...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle className="text-red-600">Error Loading Slides</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600 mb-4">{error}</p>
            <Button onClick={fetchSlides} className="w-full">
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!slideDeck || !slideDeck.slides.length) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle>No Slides Available</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600 mb-4">No slides have been generated for this course yet.</p>
            <Button 
              onClick={() => window.location.href = `/courses/create/${courseId}/workspace`}
              className="w-full"
            >
              Go to Workspace to Generate Slides
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  const slide = slideDeck.slides[currentSlide]
  const templateStyle = TEMPLATE_STYLES[slide.template_type as keyof typeof TEMPLATE_STYLES] || TEMPLATE_STYLES.TEXT_HEAVY

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header Controls */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-xl font-semibold text-gray-800">Course Slides</h1>
              <Badge variant="outline">
                {currentSlide + 1} of {slideDeck.slides.length}
              </Badge>
            </div>
            
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={resetPresentation}
                disabled={currentSlide === 0}
              >
                <RotateCcw className="h-4 w-4 mr-1" />
                Reset
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={toggleAutoPlay}
              >
                {isPlaying ? (
                  <>
                    <Pause className="h-4 w-4 mr-1" />
                    Pause
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-1" />
                    Play
                  </>
                )}
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.print()}
              >
                <Download className="h-4 w-4 mr-1" />
                Print
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Slide Display */}
      <div className="max-w-6xl mx-auto px-4 py-8">
        <Card className={`min-h-[600px] ${templateStyle} shadow-lg`}>
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <CardTitle className="text-2xl font-bold text-gray-800">
                {slide.title}
              </CardTitle>
              <Badge variant="secondary" className="text-xs">
                {slide.template_type.replace(/_/g, ' ')}
              </Badge>
            </div>
            {slide.content.supporting_text && (
              <p className="text-lg text-gray-600 mt-2">
                {slide.content.supporting_text}
              </p>
            )}
          </CardHeader>
          
          <CardContent className="space-y-6">
            {/* Main Content */}
            <div className="text-gray-700 text-base leading-relaxed">
              {slide.content.table_data ? (
                renderTable(slide.content.table_data)
              ) : (
                <div className="space-y-2">
                  {formatContent(slide.content.main_content)}
                </div>
              )}
            </div>

            {/* Images */}
            {slide.images && slide.images.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {slide.images.map((image, index) => (
                  <div key={index} className="rounded-lg overflow-hidden shadow-md">
                    <img
                      src={image.url}
                      alt={image.alt_text}
                      className="w-full h-64 object-cover"
                    />
                    {image.prompt && (
                      <div className="p-3 bg-gray-50 text-sm text-gray-600">
                        {image.alt_text}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Navigation Controls */}
      <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2">
        <div className="bg-white rounded-full shadow-lg border px-4 py-2 flex items-center space-x-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={prevSlide}
            disabled={currentSlide === 0}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          
          <span className="text-sm font-medium text-gray-600 min-w-[80px] text-center">
            {currentSlide + 1} / {slideDeck.slides.length}
          </span>
          
          <Button
            variant="ghost"
            size="sm"
            onClick={nextSlide}
            disabled={currentSlide === slideDeck.slides.length - 1}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Slide Thumbnails */}
      <div className="fixed right-4 top-1/2 transform -translate-y-1/2 w-48 max-h-96 overflow-y-auto bg-white rounded-lg shadow-lg border p-2 space-y-2">
        {slideDeck.slides.map((slideItem, index) => (
          <button
            key={index}
            onClick={() => setCurrentSlide(index)}
            className={`w-full p-2 text-left rounded text-xs transition-colors ${
              index === currentSlide
                ? 'bg-blue-100 border-blue-300 border'
                : 'bg-gray-50 hover:bg-gray-100 border border-gray-200'
            }`}
          >
            <div className="font-medium truncate">{slideItem.title}</div>
            <div className="text-gray-500 text-xs mt-1">
              Slide {index + 1}
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
