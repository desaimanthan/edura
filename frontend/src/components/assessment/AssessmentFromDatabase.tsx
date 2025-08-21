"use client"

import { useState, useEffect } from "react"
import { AssessmentRenderer } from "./AssessmentRenderer"
import { Badge } from "@/components/ui/badge"

interface FileData {
  id: string
  name: string
  type: 'file' | 'folder' | 'progress'
  content?: string
  fileType?: 'markdown' | 'image' | 'pdf' | 'slide-template' | 'research-progress' | 'generation-progress'
  isR2File?: boolean
  url?: string
  status?: 'generating' | 'saved' | 'error'
  displayTitle?: string
}

interface AssessmentFromDatabaseProps {
  selectedFile: FileData
}

interface AssessmentData {
  type: "assessment"
  format: "multiple_choice" | "true_false" | "scenario_choice" | "matching" | "fill_in_blank" | "ranking"
  question: {
    text: string
    options: Array<{
      id: string
      text: string
      correct: boolean
    }>
    correct_answer: string
    explanation: string
    difficulty: "beginner" | "intermediate" | "advanced"
    scenario?: string
    left_items?: Array<{id: string, text: string}>
    right_items?: Array<{id: string, text: string}>
    correct_matches?: Record<string, string>
    items?: Array<{id: string, text: string}>
    correct_order?: string[]
    ranking_criteria?: string
    blanks?: Array<{position: number, correct_answer: string, alternatives?: string[]}>
  }
  difficulty: string
  learning_objective: string
  databaseTitle?: string
}

export function AssessmentFromDatabase({ selectedFile }: AssessmentFromDatabaseProps) {
  const [assessmentData, setAssessmentData] = useState<AssessmentData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>("")

  useEffect(() => {
    const fetchAssessmentData = async () => {
      try {
        setLoading(true)
        setError("")

        // Get course ID from URL
        const pathParts = window.location.pathname.split('/')
        const courseId = pathParts[pathParts.indexOf('create') + 1]
        
        if (!courseId) {
          throw new Error('Course ID not found in URL')
        }

        // Extract material ID from the selected file - use materialId if available, otherwise fallback
        const materialId = (selectedFile as FileData & { materialId?: string }).materialId || selectedFile.id || selectedFile.name
        
        // Check if we have a valid MongoDB ObjectId
        if (!materialId || typeof materialId !== 'string' || materialId.length !== 24) {
          throw new Error('Invalid or missing material ID for assessment. This assessment may not be fully generated yet.')
        }

        // Get auth token
        const token = localStorage.getItem('auth_token')
        if (!token) {
          throw new Error('Authentication required. Please sign in again.')
        }

        // Fetch assessment data from the API
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/courses/${courseId}/assessment/${materialId}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          }
        })

        if (!response.ok) {
          if (response.status === 404) {
            throw new Error('Assessment data not found. This file may not be an assessment or may not have been generated yet.')
          }
          const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
          throw new Error(errorData.detail || `HTTP ${response.status}`)
        }

        const data = await response.json()
        
        // Transform the API response to match AssessmentRenderer expectations
        const assessmentData = data.assessment_data || {}
        
        // Extract the question text from the nested question object
        const questionText = assessmentData.question?.text || 
                           assessmentData.text || 
                           'Assessment question not available'
        
        // Extract options from the nested question object
        const options = Array.isArray(assessmentData.question?.options) ? assessmentData.question.options : 
                       Array.isArray(assessmentData.options) ? assessmentData.options : []
        
        // Ensure we have proper question structure
        const transformedData: AssessmentData = {
          type: 'assessment' as const,
          format: (data.assessment_format || 'multiple_choice') as AssessmentData['format'],
          question: {
            text: String(questionText), // Ensure it's a string
            options: options,
            correct_answer: String(assessmentData.question?.correct_answer || assessmentData.correct_answer || ''),
            explanation: String(assessmentData.question?.explanation || assessmentData.explanation || 'No explanation available'),
            difficulty: (data.question_difficulty || assessmentData.question?.difficulty || assessmentData.difficulty || 'intermediate') as "beginner" | "intermediate" | "advanced",
            // Include optional fields for different assessment formats
            scenario: (assessmentData.question?.scenario || assessmentData.scenario) ? String(assessmentData.question?.scenario || assessmentData.scenario) : undefined,
            left_items: assessmentData.question?.left_items || assessmentData.left_items,
            right_items: assessmentData.question?.right_items || assessmentData.right_items,
            correct_matches: assessmentData.question?.correct_matches || assessmentData.correct_matches,
            items: assessmentData.question?.items || assessmentData.items,
            correct_order: assessmentData.question?.correct_order || assessmentData.correct_order,
            ranking_criteria: (assessmentData.question?.ranking_criteria || assessmentData.ranking_criteria) ? String(assessmentData.question?.ranking_criteria || assessmentData.ranking_criteria) : undefined,
            blanks: assessmentData.question?.blanks || assessmentData.blanks
          },
          difficulty: String(data.question_difficulty || 'intermediate'),
          learning_objective: String(data.learning_objective || selectedFile.displayTitle || selectedFile.name),
          // Store the database title for display
          databaseTitle: data.material_title ? String(data.material_title) : undefined
        }
        
        // Validate that we have the minimum required data
        if (!transformedData.question.text || transformedData.question.text === 'Assessment question not available') {
          throw new Error('Assessment question text is missing or invalid')
        }
        
        if (!Array.isArray(transformedData.question.options) || transformedData.question.options.length === 0) {
          throw new Error('Assessment options are missing or invalid')
        }
        

        setAssessmentData(transformedData)
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load assessment data'
        setError(errorMessage)
        console.error('Failed to fetch assessment data:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchAssessmentData()
  }, [selectedFile.id, selectedFile.name, selectedFile.displayTitle])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading assessment data...</p>
          <p className="text-sm text-gray-400 mt-2">Fetching from database</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center text-red-600">
          <div className="mb-4">
            <svg className="h-12 w-12 mx-auto text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 19.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <p className="font-medium mb-2">Failed to load assessment</p>
          <p className="text-sm text-gray-500 mb-4">{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!assessmentData) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center text-gray-500">
          <p>No assessment data available</p>
          <p className="text-sm text-gray-400 mt-2">This file may not contain assessment content</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-5">
      {/* Assessment Title */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          {assessmentData.databaseTitle || selectedFile.displayTitle || selectedFile.name}
        </h1>
        <p className="text-sm text-gray-600">
          Assessment • {assessmentData.format.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} • {assessmentData.question.difficulty}
        </p>
      </div>
      
      {/* Assessment Content */}
      <AssessmentRenderer assessmentData={assessmentData} />
    </div>
  )
}
