"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Check, X, FileText, Zap } from "lucide-react"

interface DiffPreviewModalProps {
  isOpen: boolean
  onClose: () => void
  onApprove: () => void
  onReject: () => void
  originalContent: string
  modifiedContent: string
  changeDescription: string
  materialTitle?: string
  isProcessing?: boolean
}

interface DiffLine {
  type: 'unchanged' | 'added' | 'removed'
  content: string
  lineNumber?: number
}

export function DiffPreviewModal({
  isOpen,
  onClose,
  onApprove,
  onReject,
  originalContent,
  modifiedContent,
  changeDescription,
  materialTitle,
  isProcessing = false
}: DiffPreviewModalProps) {
  const [viewMode, setViewMode] = useState<'side-by-side' | 'unified'>('side-by-side')

  // Generate diff lines for display
  const generateDiffLines = (): { original: DiffLine[], modified: DiffLine[] } => {
    const originalLines = originalContent.split('\n')
    const modifiedLines = modifiedContent.split('\n')
    
    const originalDiff: DiffLine[] = []
    const modifiedDiff: DiffLine[] = []
    
    // Simple diff algorithm - find the changed lines
    const maxLines = Math.max(originalLines.length, modifiedLines.length)
    
    for (let i = 0; i < maxLines; i++) {
      const originalLine = originalLines[i] || ''
      const modifiedLine = modifiedLines[i] || ''
      
      if (originalLine === modifiedLine) {
        // Unchanged line
        originalDiff.push({
          type: 'unchanged',
          content: originalLine,
          lineNumber: i + 1
        })
        modifiedDiff.push({
          type: 'unchanged',
          content: modifiedLine,
          lineNumber: i + 1
        })
      } else {
        // Changed line
        if (originalLine) {
          originalDiff.push({
            type: 'removed',
            content: originalLine,
            lineNumber: i + 1
          })
        }
        if (modifiedLine) {
          modifiedDiff.push({
            type: 'added',
            content: modifiedLine,
            lineNumber: i + 1
          })
        }
      }
    }
    
    return { original: originalDiff, modified: modifiedDiff }
  }

  const { original: originalDiff, modified: modifiedDiff } = generateDiffLines()

  const renderDiffLine = (line: DiffLine, side: 'original' | 'modified') => {
    const baseClasses = "font-mono text-sm px-3 py-1 border-l-2"
    let lineClasses = baseClasses
    let prefix = ""
    
    switch (line.type) {
      case 'unchanged':
        lineClasses += " bg-gray-50 border-gray-200 text-gray-700"
        prefix = " "
        break
      case 'added':
        lineClasses += " bg-green-50 border-green-400 text-green-800"
        prefix = "+"
        break
      case 'removed':
        lineClasses += " bg-red-50 border-red-400 text-red-800"
        prefix = "-"
        break
    }
    
    return (
      <div key={`${side}-${line.lineNumber}`} className={lineClasses}>
        <span className="text-gray-400 mr-2 select-none">
          {line.lineNumber?.toString().padStart(3, ' ')}
        </span>
        <span className="text-gray-500 mr-2 select-none font-bold">
          {prefix}
        </span>
        <span className="whitespace-pre-wrap">{line.content || ' '}</span>
      </div>
    )
  }

  const renderSideBySideDiff = () => (
    <div className="grid grid-cols-2 gap-4 h-96 overflow-hidden">
      {/* Original Content */}
      <div className="border rounded-lg overflow-hidden">
        <div className="bg-red-100 px-3 py-2 border-b">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            <span className="font-medium text-red-800">Original</span>
          </div>
        </div>
        <div className="overflow-y-auto h-full bg-white">
          {originalDiff.map((line, index) => renderDiffLine(line, 'original'))}
        </div>
      </div>
      
      {/* Modified Content */}
      <div className="border rounded-lg overflow-hidden">
        <div className="bg-green-100 px-3 py-2 border-b">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="font-medium text-green-800">Modified</span>
          </div>
        </div>
        <div className="overflow-y-auto h-full bg-white">
          {modifiedDiff.map((line, index) => renderDiffLine(line, 'modified'))}
        </div>
      </div>
    </div>
  )

  const renderUnifiedDiff = () => {
    // Combine both diffs for unified view
    const unifiedLines: DiffLine[] = []
    const maxLength = Math.max(originalDiff.length, modifiedDiff.length)
    
    for (let i = 0; i < maxLength; i++) {
      const origLine = originalDiff[i]
      const modLine = modifiedDiff[i]
      
      if (origLine?.type === 'removed') {
        unifiedLines.push(origLine)
      }
      if (modLine?.type === 'added') {
        unifiedLines.push(modLine)
      }
      if (origLine?.type === 'unchanged') {
        unifiedLines.push(origLine)
      }
    }
    
    return (
      <div className="border rounded-lg overflow-hidden h-96">
        <div className="bg-gray-100 px-3 py-2 border-b">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-gray-600" />
            <span className="font-medium text-gray-800">Unified Diff</span>
          </div>
        </div>
        <div className="overflow-y-auto h-full bg-white">
          {unifiedLines.map((line, index) => renderDiffLine(line, 'original'))}
        </div>
      </div>
    )
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-blue-600" />
            Review Targeted Changes
            {materialTitle && (
              <Badge variant="outline" className="ml-2">
                {materialTitle}
              </Badge>
            )}
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Change Description */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-medium text-blue-900 mb-2">Proposed Change:</h4>
            <p className="text-blue-800">{changeDescription}</p>
          </div>
          
          {/* View Mode Toggle */}
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-700">View:</span>
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setViewMode('side-by-side')}
                className={`px-3 py-1 text-sm rounded-md transition-colors ${
                  viewMode === 'side-by-side'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Side by Side
              </button>
              <button
                onClick={() => setViewMode('unified')}
                className={`px-3 py-1 text-sm rounded-md transition-colors ${
                  viewMode === 'unified'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Unified
              </button>
            </div>
          </div>
          
          {/* Diff Content */}
          {viewMode === 'side-by-side' ? renderSideBySideDiff() : renderUnifiedDiff()}
        </div>
        
        <DialogFooter className="flex items-center justify-between">
          <div className="text-sm text-gray-500">
            Review the changes above and choose to approve or reject them.
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={onReject}
              disabled={isProcessing}
              className="flex items-center gap-2"
            >
              <X className="w-4 h-4" />
              Reject
            </Button>
            <Button
              onClick={onApprove}
              disabled={isProcessing}
              className="bg-green-600 hover:bg-green-700 flex items-center gap-2"
            >
              <Check className="w-4 h-4" />
              {isProcessing ? 'Applying...' : 'Approve Changes'}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
