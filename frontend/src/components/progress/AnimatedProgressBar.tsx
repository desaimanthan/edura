"use client"

import { useState, useEffect } from "react"

interface AnimatedProgressBarProps {
  progress: number
  total: number
  label?: string
  showPercentage?: boolean
  showFraction?: boolean
  color?: 'blue' | 'green' | 'purple' | 'orange'
  size?: 'sm' | 'md' | 'lg'
  animated?: boolean
  className?: string
}

export function AnimatedProgressBar({
  progress,
  total,
  label,
  showPercentage = true,
  showFraction = true,
  color = 'blue',
  size = 'md',
  animated = true,
  className = ""
}: AnimatedProgressBarProps) {
  const [displayProgress, setDisplayProgress] = useState(0)
  const percentage = Math.round((progress / total) * 100)

  useEffect(() => {
    const timer = setTimeout(() => {
      setDisplayProgress(percentage)
    }, 100)
    return () => clearTimeout(timer)
  }, [percentage])

  const getColorClasses = () => {
    switch (color) {
      case 'green':
        return {
          bg: 'bg-green-200',
          fill: 'bg-green-500',
          text: 'text-green-700'
        }
      case 'purple':
        return {
          bg: 'bg-purple-200',
          fill: 'bg-purple-500',
          text: 'text-purple-700'
        }
      case 'orange':
        return {
          bg: 'bg-orange-200',
          fill: 'bg-orange-500',
          text: 'text-orange-700'
        }
      default:
        return {
          bg: 'bg-blue-200',
          fill: 'bg-blue-500',
          text: 'text-blue-700'
        }
    }
  }

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'h-1.5'
      case 'lg':
        return 'h-3'
      default:
        return 'h-2'
    }
  }

  const colors = getColorClasses()

  return (
    <div className={`w-full ${className}`}>
      {/* Header with label and stats */}
      {(label || showPercentage || showFraction) && (
        <div className="flex items-center justify-between text-sm mb-2">
          {label && (
            <span className={`font-medium ${colors.text}`}>
              {label}
            </span>
          )}
          
          <div className="flex items-center gap-2 text-xs">
            {showFraction && (
              <span className={colors.text}>
                {progress} of {total}
              </span>
            )}
            {showPercentage && (
              <span className={`font-medium ${colors.text}`}>
                {displayProgress}%
              </span>
            )}
          </div>
        </div>
      )}

      {/* Progress bar */}
      <div className={`w-full ${colors.bg} rounded-full ${getSizeClasses()} overflow-hidden`}>
        <div 
          className={`
            ${colors.fill} ${getSizeClasses()} rounded-full transition-all duration-700 ease-out
            ${animated ? 'transform-gpu' : ''}
          `}
          style={{ 
            width: `${displayProgress}%`,
            transition: animated ? 'width 0.7s cubic-bezier(0.4, 0, 0.2, 1)' : 'none'
          }}
        >
          {/* Shimmer effect for active progress */}
          {animated && displayProgress > 0 && displayProgress < 100 && (
            <div className="h-full w-full relative overflow-hidden">
              <div className="absolute inset-0 -skew-x-12 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer" />
            </div>
          )}
        </div>
      </div>

      {/* Completion celebration */}
      {displayProgress === 100 && (
        <div className="mt-2 text-center">
          <span className={`text-xs font-medium ${colors.text} animate-bounce`}>
            ✨ Complete!
          </span>
        </div>
      )}
    </div>
  )
}
