"use client"

import { useState, useEffect } from "react"
import { Search, Globe, BookOpen, Users, TrendingUp, Target, Clock, Sparkles } from "lucide-react"
import { ProgressCard, ProgressStatus } from "./ProgressCard"
import { AnimatedProgressBar } from "./AnimatedProgressBar"

interface ResearchSource {
  id: string
  title: string
  description: string
  status: ProgressStatus
  duration?: string
  progress?: number
  icon?: React.ReactNode
}

interface ResearchProgressData {
  completed: number
  total: number
  currentTask?: string
  estimatedTimeRemaining?: string
  sources: ResearchSource[]
}

interface ResearchProgressDashboardProps {
  data: ResearchProgressData
  className?: string
}

const sourceTemplates = [
  {
    title: 'Industry Standards',
    description: 'Current methodologies and frameworks',
    icon: <Target className="h-5 w-5 text-blue-500" />
  },
  {
    title: 'Latest Tools',
    description: 'Modern technologies and platforms',
    icon: <Sparkles className="h-5 w-5 text-purple-500" />
  },
  {
    title: 'Teaching Methods',
    description: 'Pedagogical approaches and strategies',
    icon: <BookOpen className="h-5 w-5 text-green-500" />
  },
  {
    title: 'Assessment Trends',
    description: 'Evaluation methods and rubrics',
    icon: <Users className="h-5 w-5 text-orange-500" />
  },
  {
    title: 'Market Demands',
    description: 'Skills requirements and job trends',
    icon: <TrendingUp className="h-5 w-5 text-red-500" />
  },
  {
    title: 'Best Practices',
    description: 'Leading institutions and companies',
    icon: <Globe className="h-5 w-5 text-indigo-500" />
  },
  {
    title: 'Emerging Trends',
    description: 'Future developments and innovations',
    icon: <TrendingUp className="h-5 w-5 text-pink-500" />
  },
  {
    title: 'Case Studies',
    description: 'Real-world applications and examples',
    icon: <Search className="h-5 w-5 text-cyan-500" />
  },
  {
    title: 'Academic Research',
    description: 'Scholarly articles and publications',
    icon: <BookOpen className="h-5 w-5 text-teal-500" />
  },
  {
    title: 'Technology Trends',
    description: 'Latest technological developments',
    icon: <Sparkles className="h-5 w-5 text-violet-500" />
  }
]

export function ResearchProgressDashboard({ data, className = "" }: ResearchProgressDashboardProps) {
  const [animateIn, setAnimateIn] = useState(false)
  const [displaySources, setDisplaySources] = useState<ResearchSource[]>([])

  useEffect(() => {
    setAnimateIn(true)
  }, [])

  // Generate dynamic sources based on backend data
  useEffect(() => {
    if (data.sources && data.sources.length > 0) {
      setDisplaySources(data.sources)
    } else {
      // Generate sources dynamically based on total from backend
      const dynamicSources: ResearchSource[] = []
      
      for (let i = 0; i < data.total; i++) {
        const template = sourceTemplates[i % sourceTemplates.length]
        let status: ProgressStatus = 'pending'
        
        if (i < data.completed) {
          status = 'complete'
        } else if (i === data.completed) {
          status = 'active'
        }

        dynamicSources.push({
          id: `source-${i}`,
          title: template.title,
          description: template.description,
          status,
          icon: template.icon
        })
      }
      
      setDisplaySources(dynamicSources)
    }
  }, [data])

  const formatTimeRemaining = (timeString?: string) => {
    if (!timeString) return null
    return timeString.replace(/(\d+)m\s*(\d+)s/, '$1m $2s')
  }

  return (
    <div className={`w-full max-w-4xl mx-auto p-6 ${className}`}>
      {/* Header */}
      <div className={`
        text-center mb-8 transition-all duration-700 ease-out
        ${animateIn ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}
      `}>
        <div className="flex items-center justify-center gap-3 mb-4">
          <div className="relative">
            <Search className="h-8 w-8 text-blue-500" />
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full animate-ping" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">
            AI Research in Progress
          </h1>
        </div>
        
        <p className="text-gray-600 text-sm max-w-2xl mx-auto">
          Analyzing the latest trends, technologies, and best practices to create a cutting-edge course design for 2025
        </p>
      </div>

      {/* Overall Progress */}
      <div className={`
        mb-8 transition-all duration-700 ease-out delay-200
        ${animateIn ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}
      `}>
        <AnimatedProgressBar
          progress={data.completed}
          total={data.total}
          label="Overall Research Progress"
          color="blue"
          size="lg"
          className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm"
        />
        
        {/* Current task and time remaining */}
        <div className="flex items-center justify-between mt-4 text-sm">
          <div className="flex items-center gap-2">
            {data.currentTask && (
              <>
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                <span className="text-blue-700 font-medium">
                  {data.currentTask}
                </span>
              </>
            )}
          </div>
          
          {data.estimatedTimeRemaining && (
            <div className="flex items-center gap-2 text-gray-600">
              <Clock className="h-4 w-4" />
              <span>
                Est. {formatTimeRemaining(data.estimatedTimeRemaining)} remaining
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Research Sources Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {displaySources.map((source, index) => (
          <div
            key={source.id}
            className={`
              transition-all duration-500 ease-out
              ${animateIn ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}
            `}
            style={{ transitionDelay: `${300 + index * 100}ms` }}
          >
            <ProgressCard
              title={source.title}
              description={source.description}
              status={source.status}
              duration={source.duration}
              progress={source.progress}
              icon={source.icon}
              className="h-full"
            />
          </div>
        ))}
      </div>

      {/* Research Stats */}
      <div className={`
        mt-8 grid grid-cols-1 md:grid-cols-3 gap-4 transition-all duration-700 ease-out delay-1000
        ${animateIn ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}
      `}>
        <div className="bg-blue-50 rounded-lg p-4 text-center border border-blue-200">
          <div className="text-2xl font-bold text-blue-600">
            {data.completed}
          </div>
          <div className="text-sm text-blue-700">
            Sources Analyzed
          </div>
        </div>
        
        <div className="bg-purple-50 rounded-lg p-4 text-center border border-purple-200">
          <div className="text-2xl font-bold text-purple-600">
            {data.total - data.completed}
          </div>
          <div className="text-sm text-purple-700">
            Sources Remaining
          </div>
        </div>
        
        <div className="bg-green-50 rounded-lg p-4 text-center border border-green-200">
          <div className="text-2xl font-bold text-green-600">
            2025
          </div>
          <div className="text-sm text-green-700">
            Current Standards
          </div>
        </div>
      </div>

      {/* Completion Message */}
      {data.completed === data.total && (
        <div className={`
          mt-8 text-center transition-all duration-700 ease-out delay-1200
          ${animateIn ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}
        `}>
          <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-6 border border-green-200">
            <div className="flex items-center justify-center gap-2 mb-2">
              <Sparkles className="h-6 w-6 text-green-500 animate-bounce" />
              <h3 className="text-lg font-bold text-green-800">
                Research Complete!
              </h3>
              <Sparkles className="h-6 w-6 text-green-500 animate-bounce" />
            </div>
            <p className="text-green-700 text-sm">
              All sources analyzed successfully. Ready to generate your cutting-edge course design.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
