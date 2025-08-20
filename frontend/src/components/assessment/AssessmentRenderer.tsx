"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { CheckCircle, XCircle, RotateCcw } from "lucide-react"

// Assessment data types
interface AssessmentOption {
  id: string
  text: string
  correct: boolean
}

interface AssessmentQuestion {
  text: string
  options: AssessmentOption[]
  correct_answer: string
  explanation: string
  difficulty: "beginner" | "intermediate" | "advanced"
  scenario?: string // For scenario-choice format
  left_items?: Array<{id: string, text: string}> // For matching format
  right_items?: Array<{id: string, text: string}> // For matching format
  correct_matches?: Record<string, string> // For matching format
  items?: Array<{id: string, text: string}> // For ranking format
  correct_order?: string[] // For ranking format
  ranking_criteria?: string // For ranking format
  blanks?: Array<{position: number, correct_answer: string, alternatives?: string[]}> // For fill_in_blank
}

interface AssessmentData {
  type: "assessment"
  format: "multiple_choice" | "true_false" | "scenario_choice" | "matching" | "fill_in_blank" | "ranking"
  question: AssessmentQuestion
  difficulty: string
  learning_objective: string
}

interface AssessmentRendererProps {
  assessmentData: AssessmentData
  onComplete?: (isCorrect: boolean, userAnswer: unknown) => void
}

export function AssessmentRenderer({ assessmentData, onComplete }: AssessmentRendererProps) {
  const [userAnswer, setUserAnswer] = useState<unknown>(null)
  const [showFeedback, setShowFeedback] = useState(false)
  const [isCorrect, setIsCorrect] = useState(false)

  const handleSubmit = () => {
    if (!userAnswer) return

    let correct = false
    
    // Check correctness based on format
    switch (assessmentData.format) {
      case "multiple_choice":
      case "true_false":
      case "scenario_choice":
        correct = userAnswer === assessmentData.question.correct_answer
        break
      case "matching":
        if (assessmentData.question.correct_matches && typeof userAnswer === 'object' && userAnswer !== null) {
          const correctMatches = assessmentData.question.correct_matches
          const userAnswerObj = userAnswer as Record<string, string>
          correct = Object.keys(correctMatches).every(
            key => userAnswerObj[key] === correctMatches[key]
          )
        }
        break
      case "ranking":
        if (assessmentData.question.correct_order) {
          correct = JSON.stringify(userAnswer) === JSON.stringify(assessmentData.question.correct_order)
        }
        break
      case "fill_in_blank":
        if (assessmentData.question.blanks && typeof userAnswer === 'object' && userAnswer !== null) {
          const userAnswerObj = userAnswer as Record<number, string>
          correct = assessmentData.question.blanks.every(blank => {
            const userInput = userAnswerObj[blank.position]?.toLowerCase().trim()
            const correctAnswer = blank.correct_answer.toLowerCase().trim()
            const alternatives = blank.alternatives?.map(alt => alt.toLowerCase().trim()) || []
            
            return userInput === correctAnswer || alternatives.includes(userInput)
          })
        }
        break
    }

    setIsCorrect(correct)
    setShowFeedback(true)
    onComplete?.(correct, userAnswer)
  }

  const handleReset = () => {
    setUserAnswer(null)
    setShowFeedback(false)
    setIsCorrect(false)
  }


  const renderQuestion = () => {
    switch (assessmentData.format) {
      case "multiple_choice":
      case "true_false":
        return <MultipleChoiceQuestion 
          question={assessmentData.question}
          userAnswer={userAnswer}
          onAnswerChange={setUserAnswer}
          showFeedback={showFeedback}
          isCorrect={isCorrect}
        />
      
      case "scenario_choice":
        return <ScenarioChoiceQuestion
          question={assessmentData.question}
          userAnswer={userAnswer}
          onAnswerChange={setUserAnswer}
          showFeedback={showFeedback}
          isCorrect={isCorrect}
        />
      
      case "matching":
        return <MatchingQuestion
          question={assessmentData.question}
          userAnswer={userAnswer}
          onAnswerChange={setUserAnswer}
          showFeedback={showFeedback}
          isCorrect={isCorrect}
        />
      
      case "ranking":
        return <RankingQuestion
          question={assessmentData.question}
          userAnswer={userAnswer}
          onAnswerChange={setUserAnswer}
          showFeedback={showFeedback}
          isCorrect={isCorrect}
        />
      
      case "fill_in_blank":
        return <FillInBlankQuestion
          question={assessmentData.question}
          userAnswer={userAnswer}
          onAnswerChange={setUserAnswer}
          showFeedback={showFeedback}
          isCorrect={isCorrect}
        />
      
      default:
        return <div>Unsupported assessment format: {assessmentData.format}</div>
    }
  }

  return (
    <Card className="w-full border-0 shadow-none bg-transparent">
      <CardContent className="space-y-6 pt-0 pb-5 px-0">
        {renderQuestion()}
        
        <div className="flex items-center gap-3">
          {!showFeedback ? (
            <Button 
              onClick={handleSubmit}
              disabled={!userAnswer}
            >
              Submit Answer
            </Button>
          ) : (
            <Button 
              onClick={handleReset}
              variant="outline"
              className="flex items-center gap-2"
            >
              <RotateCcw className="h-4 w-4" />
              Try Again
            </Button>
          )}
        </div>

        {showFeedback && (
          <div className={`p-4 rounded-lg border-l-4 ${
            isCorrect 
              ? 'bg-green-50 border-green-500 dark:bg-green-950 dark:border-green-400' 
              : 'bg-red-50 border-red-500 dark:bg-red-950 dark:border-red-400'
          }`}>
            <div className="flex items-center gap-2 mb-2">
              {isCorrect ? (
                <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400" />
              ) : (
                <XCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
              )}
              <span className={`font-semibold ${
                isCorrect ? 'text-green-800 dark:text-green-200' : 'text-red-800 dark:text-red-200'
              }`}>
                {isCorrect ? 'Correct!' : 'Incorrect'}
              </span>
            </div>
            <p className={`text-sm ${
              isCorrect ? 'text-green-700 dark:text-green-300' : 'text-red-700 dark:text-red-300'
            }`}>
              {assessmentData.question.explanation}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// Individual question components
interface QuestionProps {
  question: AssessmentQuestion
  userAnswer: unknown
  onAnswerChange: (answer: unknown) => void
  showFeedback: boolean
  isCorrect: boolean
}

function MultipleChoiceQuestion({ question, userAnswer, onAnswerChange, showFeedback, isCorrect }: QuestionProps) {
  // Ensure question and options are properly formatted
  const questionText = typeof question?.text === 'string' ? question.text : 'Question text not available'
  const options = Array.isArray(question?.options) ? question.options : []
  
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-bold">{questionText}</h3>
      <div className="space-y-2">
        {options.map((option: AssessmentOption) => (
          <label
            key={option.id}
            className={`flex items-center p-3 rounded-lg border cursor-pointer transition-colors ${
              showFeedback
                ? option.correct
                  ? 'bg-green-50 border-green-200 dark:bg-green-950 dark:border-green-800'
                  : userAnswer === option.id && !option.correct
                  ? 'bg-red-50 border-red-200 dark:bg-red-950 dark:border-red-800'
                  : 'bg-muted border-border'
                : userAnswer === option.id
                ? 'bg-primary/10 border-primary'
                : 'hover:bg-muted border-border'
            }`}
          >
            <input
              type="radio"
              name="answer"
              value={option.id}
              checked={userAnswer === option.id}
              onChange={(e) => onAnswerChange(e.target.value)}
              disabled={showFeedback}
              className="mr-3"
            />
            <span className="flex-1">{typeof option.text === 'string' ? option.text : 'Option text not available'}</span>
            {showFeedback && option.correct && (
              <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400 ml-2" />
            )}
          </label>
        ))}
      </div>
    </div>
  )
}

function ScenarioChoiceQuestion({ question, userAnswer, onAnswerChange, showFeedback, isCorrect }: QuestionProps) {
  return (
    <div className="space-y-4">
      {question.scenario && (
        <div className="p-4 bg-primary/5 rounded-lg border-l-4 border-primary">
          <h4 className="font-semibold text-primary mb-2">Scenario:</h4>
          <p className="text-primary/80">{question.scenario}</p>
        </div>
      )}
      <h3 className="text-lg font-medium">{question.text}</h3>
      <div className="space-y-2">
        {question.options.map((option: AssessmentOption) => (
          <label
            key={option.id}
            className={`flex items-center p-3 rounded-lg border cursor-pointer transition-colors ${
              showFeedback
                ? option.correct
                  ? 'bg-green-50 border-green-200 dark:bg-green-950 dark:border-green-800'
                  : userAnswer === option.id && !option.correct
                  ? 'bg-red-50 border-red-200 dark:bg-red-950 dark:border-red-800'
                  : 'bg-muted border-border'
                : userAnswer === option.id
                ? 'bg-primary/10 border-primary'
                : 'hover:bg-muted border-border'
            }`}
          >
            <input
              type="radio"
              name="answer"
              value={option.id}
              checked={userAnswer === option.id}
              onChange={(e) => onAnswerChange(e.target.value)}
              disabled={showFeedback}
              className="mr-3"
            />
            <span className="flex-1">{option.text}</span>
            {showFeedback && option.correct && (
              <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400 ml-2" />
            )}
          </label>
        ))}
      </div>
    </div>
  )
}

function MatchingQuestion({ question, userAnswer, onAnswerChange, showFeedback, isCorrect }: QuestionProps) {
  const handleMatchChange = (leftId: string, rightId: string) => {
    const currentAnswer = (typeof userAnswer === 'object' && userAnswer !== null) ? userAnswer as Record<string, string> : {}
    const newAnswer = { ...currentAnswer, [leftId]: rightId }
    onAnswerChange(newAnswer)
  }

  const userAnswerObj = (typeof userAnswer === 'object' && userAnswer !== null) ? userAnswer as Record<string, string> : {}

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-medium">{question.text}</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h4 className="font-semibold mb-3">Match these items:</h4>
          <div className="space-y-2">
            {question.left_items?.map((item: {id: string, text: string}) => (
              <div key={item.id} className="p-3 bg-muted rounded-lg">
                <span className="font-medium">{item.id}.</span> {item.text}
              </div>
            ))}
          </div>
        </div>
        <div>
          <h4 className="font-semibold mb-3">With these options:</h4>
          <div className="space-y-2">
            {question.left_items?.map((leftItem: {id: string, text: string}) => (
              <div key={leftItem.id} className="flex items-center gap-2">
                <span className="font-medium w-6">{leftItem.id}.</span>
                <select
                  value={userAnswerObj[leftItem.id] || ''}
                  onChange={(e) => handleMatchChange(leftItem.id, e.target.value)}
                  disabled={showFeedback}
                  className={`flex-1 p-2 border rounded ${
                    showFeedback
                      ? userAnswerObj[leftItem.id] === question.correct_matches?.[leftItem.id]
                        ? 'bg-green-50 border-green-200 dark:bg-green-950 dark:border-green-800'
                        : 'bg-red-50 border-red-200 dark:bg-red-950 dark:border-red-800'
                      : 'border-input bg-background'
                  }`}
                >
                  <option value="">Select...</option>
                  {question.right_items?.map((rightItem: {id: string, text: string}) => (
                    <option key={rightItem.id} value={rightItem.id}>
                      {rightItem.id}. {rightItem.text}
                    </option>
                  ))}
                </select>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function RankingQuestion({ question, userAnswer, onAnswerChange, showFeedback, isCorrect }: QuestionProps) {
  const [items, setItems] = useState(question.items || [])

  const moveItem = (fromIndex: number, toIndex: number) => {
    if (showFeedback) return
    
    const newItems = [...items]
    const [movedItem] = newItems.splice(fromIndex, 1)
    newItems.splice(toIndex, 0, movedItem)
    setItems(newItems)
    onAnswerChange(newItems.map((item: {id: string, text: string}) => item.id))
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-medium">{question.text}</h3>
      {question.ranking_criteria && (
        <p className="text-sm text-muted-foreground">
          <strong>Ranking Criteria:</strong> {question.ranking_criteria}
        </p>
      )}
      <div className="space-y-2">
        {items.map((item: {id: string, text: string}, index: number) => (
          <div
            key={item.id}
            className={`flex items-center p-3 rounded-lg border ${
              showFeedback
                ? question.correct_order?.[index] === item.id
                  ? 'bg-green-50 border-green-200 dark:bg-green-950 dark:border-green-800'
                  : 'bg-red-50 border-red-200 dark:bg-red-950 dark:border-red-800'
                : 'bg-muted border-border'
            }`}
          >
            <span className="font-bold text-lg mr-3">{index + 1}.</span>
            <span className="flex-1">{item.text}</span>
            {!showFeedback && (
              <div className="flex gap-1">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => moveItem(index, Math.max(0, index - 1))}
                  disabled={index === 0}
                >
                  ↑
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => moveItem(index, Math.min(items.length - 1, index + 1))}
                  disabled={index === items.length - 1}
                >
                  ↓
                </Button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function FillInBlankQuestion({ question, userAnswer, onAnswerChange, showFeedback, isCorrect }: QuestionProps) {
  const handleBlankChange = (position: number, value: string) => {
    const currentAnswer = (typeof userAnswer === 'object' && userAnswer !== null) ? userAnswer as Record<number, string> : {}
    const newAnswer = { ...currentAnswer, [position]: value }
    onAnswerChange(newAnswer)
  }

  const userAnswerObj = (typeof userAnswer === 'object' && userAnswer !== null) ? userAnswer as Record<number, string> : {}

  // Parse the text to identify blanks
  const renderTextWithBlanks = () => {
    const text = question.text
    const blanks = question.blanks || []
    
    return (
      <div className="text-lg leading-relaxed">
        {text.split('_____').map((part: string, index: number) => (
          <span key={index}>
            {part}
            {index < blanks.length && (
              <input
                type="text"
                value={userAnswerObj[blanks[index].position] || ''}
                onChange={(e) => handleBlankChange(blanks[index].position, e.target.value)}
                disabled={showFeedback}
                className={`inline-block mx-1 px-2 py-1 border-b-2 bg-transparent text-center min-w-[100px] ${
                  showFeedback
                    ? (() => {
                        const userInput = userAnswerObj[blanks[index].position]?.toLowerCase().trim()
                        const correctAnswer = blanks[index].correct_answer.toLowerCase().trim()
                        const alternatives = blanks[index].alternatives?.map((alt: string) => alt.toLowerCase().trim()) || []
                        const isCorrect = userInput === correctAnswer || alternatives.includes(userInput)
                        return isCorrect ? 'border-green-500 text-green-700 dark:border-green-400 dark:text-green-300' : 'border-red-500 text-red-700 dark:border-red-400 dark:text-red-300'
                      })()
                    : 'border-primary/30 focus:border-primary focus:outline-none'
                }`}
                placeholder="..."
              />
            )}
          </span>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-medium mb-4">Fill in the blanks:</h3>
      {renderTextWithBlanks()}
    </div>
  )
}
