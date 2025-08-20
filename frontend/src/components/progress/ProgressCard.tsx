"use client"

import { useState, useEffect } from "react"
import { CheckCircle, Clock, Loader2 } from "lucide-react"

export type ProgressStatus = 'pending' | 'active' | 'complete'

interface ProgressCardProps {
  title: string
  description?: string
  status: ProgressStatus
  duration?: string
  progress?: number
  icon?: React.ReactNode
  className?: string
}

export function ProgressCard({ 
  title, 
  description, 
  status, 
  duration, 
  progress = 0,
  icon,
  className = "" 
}: ProgressCardProps) {
  const [animateIn, setAnimateIn] = useState(false)

  useEffect(() => {
    setAnimateIn(true)
  }, [])

  const getStatusIcon = () => {
    switch (status) {
      case 'complete':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'active':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />
      case 'pending':
        return <Clock className="h-5 w-5 text-gray-400" />
    }
  }

  const getStatusStyles = () => {
    switch (status) {
      case 'complete':
        return "bg-green-50 border-green-200 shadow-green-100"
      case 'active':
        return "bg-blue-50 border-blue-200 shadow-blue-100 animate-pulse"
      case 'pending':
        return "bg-gray-50 border-gray-200 shadow-gray-100"
    }
  }

  return (
    <div 
      className={`
        relative overflow-hidden rounded-lg border-2 p-4 transition-all duration-500 ease-out
        ${getStatusStyles()}
        ${animateIn ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}
        ${className}
      `}
    >
      {/* Background gradient for active state */}
      {status === 'active' && (
        <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 to-purple-500/5" />
      )}
      
      <div className="relative flex items-start gap-3">
        <div className="flex-shrink-0 mt-0.5">
          {icon || getStatusIcon()}
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <h3 className={`
              font-medium text-sm
              ${status === 'complete' ? 'text-green-900' : 
                status === 'active' ? 'text-blue-900' : 'text-gray-600'}
            `}>
              {title}
            </h3>
            
            {duration && status === 'complete' && (
              <span className="text-xs text-green-600 font-medium">
                {duration}
              </span>
            )}
          </div>
          
          {description && (
            <p className={`
              text-xs mt-1
              ${status === 'complete' ? 'text-green-700' : 
                status === 'active' ? 'text-blue-700' : 'text-gray-500'}
            `}>
              {description}
            </p>
          )}
          
          {/* Progress bar for active items */}
          {status === 'active' && progress > 0 && (
            <div className="mt-2">
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="text-blue-700">Progress</span>
                <span className="text-blue-600 font-medium">{progress}%</span>
              </div>
              <div className="w-full bg-blue-200 rounded-full h-1.5">
                <div 
                  className="bg-blue-500 h-1.5 rounded-full transition-all duration-300 ease-out"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Completion celebration effect */}
      {status === 'complete' && (
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute inset-0 bg-green-400/20 rounded-lg animate-ping" 
               style={{ animationDuration: '1s', animationIterationCount: '1' }} />
        </div>
      )}
    </div>
  )
}
