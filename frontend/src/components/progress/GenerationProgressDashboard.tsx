"use client"

import { useState, useEffect } from "react"
import { Bot, FileText, BookOpen, CheckSquare, Target, Sparkles, Clock, Zap } from "lucide-react"
import { ProgressCard, ProgressStatus } from "./ProgressCard"
import { AnimatedProgressBar } from "./AnimatedProgressBar"

interface GenerationPhase {
  id: string
  title: string
  description: string
  status: ProgressStatus
  progress?: number
  wordsGenerated?: number
  icon?: React.ReactNode
}

interface GenerationProgressData {
  completed: number
  total: number
  currentPhase?: string
  totalWords?: number
  totalSections?: number
  overallProgress?: number
  phases: GenerationPhase[]
}

interface GenerationProgressDashboardProps {
  data: GenerationProgressData
  className?: string
}

const defaultPhases: GenerationPhase[] = [
  {
    id: 'overview',
    title: 'Course Overview',
    description: 'Prerequisites, tools, and structure',
    status: 'pending',
    icon: <FileText className="h-5 w-5 text-blue-500" />
  },
  {
    id: 'module-1',
    title: 'Module 1: Foundations',
    description: 'Learning outcomes and pedagogy',
    status: 'pending',
    icon: <BookOpen className="h-5 w-5 text-green-500" />
  },
  {
    id: 'module-2',
    title: 'Module 2: Core Concepts',
    description: 'Advanced topics and examples',
    status: 'pending',
    icon: <Target className="h-5 w-5 text-purple-500" />
  },
  {
    id: 'module-3',
    title: 'Module 3: Applications',
    description: 'Practical implementations',
    status: 'pending',
    icon: <Zap className="h-5 w-5 text-orange-500" />
  },
  {
    id: 'assessments',
    title: 'Assessments & Rubrics',
    description: 'Evaluation methods and criteria',
    status: 'pending',
    icon: <CheckSquare className="h-5 w-5 text-red-500" />
  },
  {
    id: 'final-project',
    title: 'Final Project',
    description: 'Capstone project and rubric',
    status: 'pending',
    icon: <Sparkles className="h-5 w-5 text-indigo-500" />
  }
]

export function GenerationProgressDashboard({ data, className = "" }: GenerationProgressDashboardProps) {
  const [animateIn, setAnimateIn] = useState(false)
  const [displayPhases, setDisplayPhases] = useState<GenerationPhase[]>(defaultPhases)
  const [typingText, setTypingText] = useState("")

  useEffect(() => {
    setAnimateIn(true)
  }, [])

  // Update phases with data from props
  useEffect(() => {
    if (data.phases && data.phases.length > 0) {
      setDisplayPhases(data.phases)
    } else {
      // Update default phases based on progress
      const updatedPhases = defaultPhases.map((phase, index) => {
        if (index < data.completed) {
          return { ...phase, status: 'complete' as ProgressStatus }
        } else if (index === data.completed) {
          return { ...phase, status: 'active' as ProgressStatus }
        }
        return phase
      })
      setDisplayPhases(updatedPhases)
    }
  }, [data])

  // Typing animation for current phase
  useEffect(() => {
    if (data.currentPhase) {
      const text = `Generating ${data.currentPhase}...`
      let index = 0
      setTypingText("")
      
      const timer = setInterval(() => {
        if (index < text.length) {
          setTypingText(text.slice(0, index + 1))
          index++
        } else {
          clearInterval(timer)
        }
      }, 50)
      
      return () => clearInterval(timer)
    }
  }, [data.currentPhase])

  return (
    <div className={`w-full max-w-4xl mx-auto p-6 ${className}`}>
      {/* Header */}
      <div className={`
        text-center mb-8 transition-all duration-700 ease-out
        ${animateIn ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}
      `}>
        <div className="flex items-center justify-center gap-3 mb-4">
          <div className="relative">
            <Bot className="h-8 w-8 text-purple-500" />
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-purple-500 rounded-full animate-ping" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">
            Generating Course Design
          </h1>
        </div>
        
        <p className="text-gray-600 text-sm max-w-2xl mx-auto">
          Creating comprehensive course content with learning objectives, pedagogy strategies, and assessment frameworks
        </p>
      </div>

      {/* Typing Animation */}
      {typingText && (
        <div className={`
          text-center mb-6 transition-all duration-500 ease-out
          ${animateIn ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}
        `}>
          <div className="bg-purple-50 rounded-lg p-4 border border-purple-200 inline-block">
            <div className="flex items-center gap-2">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
              <span className="text-purple-700 font-medium text-sm">
                {typingText}
                <span className="animate-pulse">|</span>
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Overall Progress */}
      <div className={`
        mb-8 transition-all duration-700 ease-out delay-200
        ${animateIn ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}
      `}>
        <AnimatedProgressBar
          progress={data.overallProgress || data.completed}
          total={data.overallProgress ? 100 : data.total}
          label="Course Generation Progress"
          color="purple"
          size="lg"
          className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm"
        />
      </div>

      {/* Generation Stats */}
      <div className={`
        mb-8 grid grid-cols-1 md:grid-cols-3 gap-4 transition-all duration-700 ease-out delay-300
        ${animateIn ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}
      `}>
        <div className="bg-blue-50 rounded-lg p-4 text-center border border-blue-200">
          <div className="text-2xl font-bold text-blue-600">
            {data.totalWords || 0}
          </div>
          <div className="text-sm text-blue-700">
            Words Generated
          </div>
        </div>
        
        <div className="bg-green-50 rounded-lg p-4 text-center border border-green-200">
          <div className="text-2xl font-bold text-green-600">
            {data.totalSections || 0}
          </div>
          <div className="text-sm text-green-700">
            Sections Created
          </div>
        </div>
        
        <div className="bg-purple-50 rounded-lg p-4 text-center border border-purple-200">
          <div className="text-2xl font-bold text-purple-600">
            {Math.round(data.overallProgress || (data.completed / data.total) * 100)}%
          </div>
          <div className="text-sm text-purple-700">
            Completion
          </div>
        </div>
      </div>

      {/* Generation Phases */}
      <div className="space-y-4">
        {displayPhases.map((phase, index) => (
          <div
            key={phase.id}
            className={`
              transition-all duration-500 ease-out
              ${animateIn ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}
            `}
            style={{ transitionDelay: `${400 + index * 100}ms` }}
          >
            <ProgressCard
              title={phase.title}
              description={phase.description}
              status={phase.status}
              progress={phase.progress}
              icon={phase.icon}
              className="w-full"
            />
          </div>
        ))}
      </div>

      {/* Completion Message */}
      {data.completed === data.total && (
        <div className={`
          mt-8 text-center transition-all duration-700 ease-out delay-1000
          ${animateIn ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}
        `}>
          <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-6 border border-purple-200">
            <div className="flex items-center justify-center gap-2 mb-2">
              <Sparkles className="h-6 w-6 text-purple-500 animate-bounce" />
              <h3 className="text-lg font-bold text-purple-800">
                Course Design Complete!
              </h3>
              <Sparkles className="h-6 w-6 text-purple-500 animate-bounce" />
            </div>
            <p className="text-purple-700 text-sm">
              Your comprehensive course design is ready with curriculum, pedagogy, and assessments.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
