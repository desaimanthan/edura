# 🤖 Agent Development Guide

## 📋 Table of Contents
1. [Agent Architecture Overview](#agent-architecture-overview)
2. [Backend Agent Development](#backend-agent-development)
3. [Frontend Integration](#frontend-integration)
4. [Quick Action Buttons](#quick-action-buttons)
5. [Streaming Implementation](#streaming-implementation)
6. [Best Practices](#best-practices)
7. [Common Pitfalls](#common-pitfalls)
8. [Testing Guidelines](#testing-guidelines)

---

## 🏗️ Agent Architecture Overview

### Core Components
```
Agent System
├── Backend Agent (Python)
│   ├── Function Definitions
│   ├── System Prompt (LLM Intelligence)
│   ├── Message Processing
│   └── Function Implementations
├── Frontend Integration (TypeScript/React)
│   ├── Chat Interface
│   ├── Quick Action Buttons
│   ├── Streaming Handlers
│   └── Success Message Management
└── Route Handlers
    ├── Chat Endpoints
    ├── Streaming Endpoints
    └── Function-Specific Endpoints
```

---

## 🔧 Backend Agent Development

### 1. Agent Class Structure

```python
class YourAgent:
    """Agent specialized in [specific domain]"""
    
    def __init__(self, openai_service, database_service, message_service, context_service):
        self.openai = openai_service
        self.db = database_service
        self.messages = message_service
        self.context = context_service
        self.model = "gpt-5-nano-2025-08-07"
    
    def get_function_definitions(self) -> List[Dict[str, Any]]:
        """Define functions that this agent can call"""
        return [
            {
                "name": "your_function",
                "description": "Clear description of what this function does",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "param1": {
                            "type": "string",
                            "description": "Clear parameter description"
                        }
                    },
                    "required": ["param1"]
                }
            }
        ]
    
    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        """Generate LLM-intelligence based system prompt"""
        # ✅ DO: Trust LLM intelligence
        # ❌ DON'T: Use rigid pattern matching
        
    async def process_message(self, course_id, user_id, user_message) -> Dict[str, Any]:
        """Main message processing logic"""
        # Standard processing flow
```

### 2. System Prompt Best Practices

#### ✅ DO: LLM-Intelligence Approach
```python
def get_system_prompt(self, context: Dict[str, Any]) -> str:
    return f"""You are a [Agent Role] for [context].

Use your natural language understanding to help users. When users provide clear instructions with all necessary information, act on them immediately.

Available functions:
- function_name: Description (requires: param1, param2)

Examples of intelligent behavior:
- "change X to Y" → Extract Y and call update_function
- "create a new Z" → Call create_function with extracted details

Be conversational, helpful, and act on clear requests immediately."""
```

#### ❌ DON'T: Rigid Pattern Matching
```python
# BAD - Don't do this
"""
CRITICAL INSTRUCTIONS:
- When user says "change X", DO NOT call functions
- Instead, ask them: "What would you like to change it to?"
- ONLY call function when user provides specific value
"""
```

### 3. Function Implementation Pattern

```python
async def _your_function(self, param1: str, param2: str) -> Dict[str, Any]:
    """Implement your function logic"""
    try:
        # Your business logic here
        result = await self.db.update_something(param1, param2)
        
        if result:
            return {
                "success": True,
                "data": result,
                "message": "Operation completed successfully"
            }
        else:
            return {
                "success": False,
                "error": "Operation failed"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

### 4. Response Generation

```python
async def _generate_response_with_context(self, base_response: Optional[str], function_results: Dict[str, Any]) -> str:
    """Generate contextual responses based on function results"""
    if not function_results:
        return base_response or "Default helpful message"
    
    if "your_function_result" in function_results:
        result = function_results["your_function_result"]
        if result.get("success"):
            return f"✅ **Success!** {result.get('message')}"
        else:
            return f"❌ **Error:** {result.get('error')}"
    
    return base_response or "I've processed your request."
```

---

## 🎨 Frontend Integration

### 1. Chat Interface Integration

```typescript
// In your page component
const handleCurriculumStreaming = async (courseId: string, focus?: string) => {
  try {
    const response = await fetch(`/api/courses/${courseId}/your-streaming-endpoint`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ focus })
    })

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6))
          
          if (data.type === 'content') {
            // Update your UI with streaming content
            setFileContent(prev => prev + data.content)
          } else if (data.type === 'complete') {
            // Handle completion
            setSuccessMessage(data.content)
          }
        }
      }
    }
  } catch (error) {
    console.error('Streaming error:', error)
  }
}
```

### 2. Success Message Handling

```typescript
// ✅ DO: Let backend handle message persistence
useEffect(() => {
  if (successMessage && successMessageTimestamp) {
    // Only show in UI, don't persist to database
    // Backend already saves the proper response
    console.log('Success:', successMessage)
  }
}, [successMessage, successMessageTimestamp])

// ❌ DON'T: Add additional messages that get persisted
// This creates duplicates when page reloads
```

---

## ⚡ Quick Action Buttons

### 1. Implementation Pattern

```typescript
const handleQuickAction = async (action: 'generate' | 'upload') => {
  setShowQuickActions(false)
  
  const actionMessage = action === 'generate' ? 'Generate for me' : 'I have one'
  
  // Add user message to chat
  const userMessage: Message = {
    id: Date.now().toString(),
    content: actionMessage,
    sender: 'user',
    timestamp: new Date()
  }
  setMessages(prev => [...prev, userMessage])
  
  // Send to backend (same as regular chat)
  await sendMessageToBackend(actionMessage)
}
```

### 2. Button Visibility Logic

```typescript
// Show quick actions after specific AI messages
{showQuickActions && 
 message.sender === 'ai' && 
 index === messages.length - 1 && 
 message.content.toLowerCase().includes("your-trigger-keyword") && (
  <div className="flex gap-2 mt-3">
    <Button onClick={() => handleQuickAction('generate')}>
      <Sparkles className="h-4 w-4" />
      Generate for me
    </Button>
    <Button onClick={() => handleQuickAction('upload')}>
      <Upload className="h-4 w-4" />
      I have one
    </Button>
  </div>
)}
```

---

## 🌊 Streaming Implementation

### 1. Backend Streaming Function

```python
async def stream_your_content(self, course_id: str, params: Optional[str] = None):
    """Stream content generation in real-time"""
    try:
        # Send start signal
        yield {"type": "start", "content": "🔄 Starting generation..."}
        
        # Your streaming logic here
        client = await self.openai.get_client()
        response = await client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": your_prompt}],
            stream=True
        )
        
        content = ""
        async for chunk in response:
            if chunk.choices[0].delta.content:
                chunk_content = chunk.choices[0].delta.content
                content += chunk_content
                
                yield {
                    "type": "content",
                    "content": chunk_content,
                    "full_content": content
                }
        
        # Save to storage/database
        yield {"type": "progress", "content": "💾 Saving..."}
        # Your save logic here
        
        # Send completion
        yield {
            "type": "complete",
            "content": "✅ Generation complete!",
            "full_content": content
        }
        
    except Exception as e:
        yield {"type": "error", "content": f"Error: {str(e)}"}
```

### 2. Route Handler for Streaming

```python
@router.post("/{course_id}/your-streaming-endpoint")
async def your_streaming_endpoint(
    course_id: str,
    request: YourRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """Stream your content generation"""
    return StreamingResponse(
        stream_your_content(course_id, request.params),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )
```

### 3. Frontend Streaming Handler

```typescript
const handleStreaming = async (courseId: string) => {
  const response = await fetch(`/api/courses/${courseId}/your-streaming-endpoint`)
  const reader = response.body?.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const chunk = decoder.decode(value)
    const lines = chunk.split('\n')

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const jsonStr = line.slice(6).trim()
          
          // Skip empty lines
          if (!jsonStr) {
            continue
          }
          
          // Skip malformed JSON lines
          if (jsonStr === '{}' || !jsonStr.startsWith('{') || !jsonStr.endsWith('}')) {
            continue
          }
          
          // Validate JSON before parsing
          let data
          try {
            data = JSON.parse(jsonStr)
          } catch (parseError) {
            console.warn('Skipping malformed JSON chunk:', jsonStr.substring(0, 100) + '...')
            continue
          }
          
          switch (data.type) {
            case 'start':
              setIsGenerating(true)
              break
            case 'content':
              setStreamingContent(prev => prev + data.content)
              break
            case 'complete':
              setIsGenerating(false)
              setSuccessMessage(data.content)
              break
            case 'error':
              setError(data.content)
              break
          }
        } catch (e) {
          console.error('Streaming error:', e)
        }
      }
    }
  }
}
```

---

## ✅ Best Practices

### 1. Agent Design Principles

- **Trust LLM Intelligence**: Let GPT-4 understand natural language instead of rigid patterns
- **Single Responsibility**: Each agent should have a clear, focused purpose
- **Stateless Functions**: Functions should be independent and reusable
- **Error Handling**: Always return structured error responses
- **Logging**: Add comprehensive logging for debugging

### 2. System Prompt Guidelines

```python
# ✅ Good System Prompt
"""You are a [Role] for [Context].

Use your natural language understanding to help users. Act on clear requests immediately.

Available functions:
- function_name: Description (params: x, y)

Examples:
- "do X with Y" → Call function_name(x=X, y=Y)
"""

# ❌ Bad System Prompt  
"""
CRITICAL RULES:
- If user says X, DO NOT do Y
- Always ask Z before doing W
- ONLY do A when B and C and D
"""
```

### 3. Function Naming Conventions

- Use clear, descriptive names: `update_course_name` not `update_name`
- Follow consistent patterns: `get_`, `create_`, `update_`, `delete_`
- Include entity in name: `course_info` not just `info`

### 4. Response Patterns

```python
# ✅ Consistent Response Structure
{
    "success": bool,
    "data": any,           # On success
    "error": str,          # On failure
    "message": str         # Human-readable message
}
```

---

## ❌ Common Pitfalls

### 1. Over-Constraining the LLM

```python
# ❌ DON'T: Rigid rules that fight LLM intelligence
"""
CRITICAL: When user says "change X to Y":
1. DO NOT call update_function
2. Ask "What would you like to change it to?"
3. ONLY call function after they respond
"""

# ✅ DO: Trust LLM to understand
"""
Available functions:
- update_function: Updates X to new value

Use your intelligence to extract parameters from user requests.
"""
```

### 2. Duplicate Message Handling

```typescript
// ❌ DON'T: Add success messages that get persisted
useEffect(() => {
  if (successMessage) {
    const msg = { content: successMessage, sender: 'ai' }
    setMessages(prev => [...prev, msg])  // This creates duplicates!
  }
}, [successMessage])

// ✅ DO: Let backend handle persistence
// Frontend only shows real-time updates
```

### 3. Poor Error Handling

```python
# ❌ DON'T: Let exceptions bubble up
async def your_function(self, param):
    result = await self.db.update(param)  # Can throw exception
    return {"success": True}

# ✅ DO: Handle all exceptions
async def your_function(self, param):
    try:
        result = await self.db.update(param)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### 4. Inconsistent Function Results

```python
# ❌ DON'T: Inconsistent return formats
def function_a(): return True
def function_b(): return {"status": "ok"}
def function_c(): return "success"

# ✅ DO: Consistent structure
def function_a(): return {"success": True, "data": result}
def function_b(): return {"success": True, "data": result}
def function_c(): return {"success": False, "error": "message"}
```

---

## 🧪 Testing Guidelines

### 1. Agent Intelligence Tests

```python
# Test natural language understanding
test_cases = [
    ("change name to RAG", should_extract_name_and_update),
    ("rename it to Python", should_extract_name_and_update),
    ("what's the current info?", should_call_get_info),
]
```

### 2. Function Testing

```python
async def test_your_function():
    # Test success case
    result = await agent._your_function("valid_param")
    assert result["success"] == True
    
    # Test error case
    result = await agent._your_function("invalid_param")
    assert result["success"] == False
    assert "error" in result
```

### 3. Integration Testing

```python
async def test_message_processing():
    # Test complete flow
    result = await agent.process_message(course_id, user_id, "change name to Test")
    
    assert "function_results" in result
    assert result["function_results"]["name_updated"]["success"] == True
```

---

## 📚 Example: Complete Agent Implementation

See `CourseCreationAgent` and `CourseDesignAgent` for complete examples of:
- LLM-intelligence based system prompts
- Proper function definitions and implementations
- Streaming integration
- Frontend quick action handling
- Error handling and response generation

---

## 🚀 Quick Start Checklist

When creating a new agent:

- [ ] Define clear agent purpose and scope
- [ ] Create function definitions with clear descriptions
- [ ] Write LLM-intelligence based system prompt
- [ ] Implement functions with consistent error handling
- [ ] Add streaming support if needed
- [ ] Create route handlers for endpoints
- [ ] Integrate with frontend chat interface
- [ ] Add quick action buttons if applicable
- [ ] Test natural language understanding
- [ ] Document agent capabilities

---

**Remember**: Trust the LLM's intelligence. Your job is to provide clear context and available functions, not to micromanage every decision with rigid rules.
