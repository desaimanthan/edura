interface StreamEvent {
  type: 'metadata' | 'text' | 'complete' | 'research_start' | 'research_progress' | 'generation_start' | 'content' | 'progress' | 'error'
  data: unknown
  sequence?: number
  timestamp?: string
}

interface ParseResult {
  success: boolean
  event?: StreamEvent
  error?: string
}

export class StreamEventParser {
  private lastProcessedSequence = 0
  private eventQueue: StreamEvent[] = []

  parseEvent(line: string): ParseResult {
    try {
      // Remove 'data: ' prefix
      if (!line.startsWith('data: ')) {
        return { success: false, error: 'Invalid SSE format' }
      }

      const jsonStr = line.slice(6).trim()
      
      // Skip empty lines or malformed data
      if (!jsonStr || jsonStr === '{}') {
        return { success: false, error: 'Empty or invalid JSON' }
      }

      // Validate JSON structure
      if (!jsonStr.startsWith('{') || !jsonStr.endsWith('}')) {
        return { success: false, error: 'Malformed JSON structure' }
      }

      const event: StreamEvent = JSON.parse(jsonStr)
      
      // Validate event structure
      if (!this.validateEvent(event)) {
        return { success: false, error: 'Invalid event structure' }
      }

      return { success: true, event }
    } catch (error) {
      return { 
        success: false, 
        error: `JSON parsing failed: ${error instanceof Error ? error.message : 'Unknown error'}` 
      }
    }
  }

  validateEvent(event: StreamEvent): boolean {
    // Check required fields
    if (!event.type) {
      console.warn('Event missing type field:', event)
      return false
    }

    // Validate event types
    const validTypes = [
      'metadata', 'text', 'complete', 'research_start', 'research_progress', 
      'generation_start', 'content', 'progress', 'error'
    ]
    
    if (!validTypes.includes(event.type)) {
      console.warn('Invalid event type:', event.type)
      return false
    }

    return true
  }

  addToQueue(event: StreamEvent): void {
    // Handle sequence ordering if available
    if (event.sequence !== undefined) {
      // Insert in correct sequence order
      const insertIndex = this.eventQueue.findIndex(e => 
        e.sequence !== undefined && e.sequence > event.sequence!
      )
      
      if (insertIndex === -1) {
        this.eventQueue.push(event)
      } else {
        this.eventQueue.splice(insertIndex, 0, event)
      }
    } else {
      // No sequence, add to end
      this.eventQueue.push(event)
    }
  }

  processNextEvent(): StreamEvent | null {
    if (this.eventQueue.length === 0) {
      return null
    }

    const event = this.eventQueue.shift()!
    
    // Update sequence tracking
    if (event.sequence !== undefined) {
      this.lastProcessedSequence = Math.max(this.lastProcessedSequence, event.sequence)
    }

    return event
  }

  hasQueuedEvents(): boolean {
    return this.eventQueue.length > 0
  }

  clearQueue(): void {
    this.eventQueue = []
    this.lastProcessedSequence = 0
  }

  getQueueStatus(): { queued: number, lastSequence: number } {
    return {
      queued: this.eventQueue.length,
      lastSequence: this.lastProcessedSequence
    }
  }
}
