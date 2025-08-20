# 🚀 Agent Development Quick Reference

## 📋 New Agent Checklist

### 1. Backend Agent Setup
```python
class YourAgent:
    def __init__(self, openai_service, database_service, message_service, context_service):
        # Standard dependencies
        
    def get_function_definitions(self) -> List[Dict[str, Any]]:
        # Define your functions with clear descriptions
        
    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        # ✅ Trust LLM intelligence - no rigid rules!
        
    async def process_message(self, course_id, user_id, user_message):
        # Standard OpenAI + function calling flow
```

### 2. System Prompt Template
```python
return f"""You are a [ROLE] for [CONTEXT] (ID: {id}).

Use your natural language understanding to help users. When users provide clear instructions with all necessary information, act on them immediately.

Available functions:
- function_name: Description (requires: param1, param2)

Examples of intelligent behavior:
- "change X to Y" → Extract Y and call update_function
- "create Z with A" → Call create_function with extracted details

Be conversational, helpful, and act on clear requests immediately."""
```

### 3. Function Implementation Pattern
```python
async def _your_function(self, param1: str) -> Dict[str, Any]:
    try:
        result = await self.db.do_something(param1)
        return {
            "success": True,
            "data": result,
            "message": "Success message"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

## 🎨 Frontend Integration

### Quick Action Buttons
```typescript
{showQuickActions && 
 message.sender === 'ai' && 
 index === messages.length - 1 && 
 message.content.toLowerCase().includes("trigger-keyword") && (
  <div className="flex gap-2 mt-3">
    <Button onClick={() => handleQuickAction('action1')}>
      <Icon className="h-4 w-4" />
      Action 1
    </Button>
  </div>
)}
```

### Streaming Handler
```typescript
const handleStreaming = async (courseId: string) => {
  const response = await fetch(`/api/courses/${courseId}/stream-endpoint`)
  const reader = response.body?.getReader()
  
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    
    // Process streaming data
    const data = JSON.parse(line.slice(6))
    if (data.type === 'content') {
      setContent(prev => prev + data.content)
    }
  }
}
```

## ⚡ Do's and Don'ts

### ✅ DO
- Trust LLM intelligence for natural language understanding
- Use consistent error handling with try/catch
- Return structured responses: `{success, data/error, message}`
- Let backend handle message persistence
- Add comprehensive logging for debugging
- Use clear, descriptive function names

### ❌ DON'T
- Write rigid pattern-matching rules in system prompts
- Add frontend success messages that get persisted (creates duplicates)
- Let exceptions bubble up without handling
- Use inconsistent response formats across functions
- Over-constrain the LLM with "DO NOT" rules

## 🔧 Route Handler Template
```python
@router.post("/{course_id}/your-endpoint")
async def your_endpoint(
    course_id: str,
    request: YourRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    # Verify course ownership
    # Call agent or service
    # Return response
```

## 🌊 Streaming Template
```python
async def stream_content(self, course_id: str):
    try:
        yield {"type": "start", "content": "Starting..."}
        
        # Your streaming logic
        async for chunk in openai_stream:
            yield {"type": "content", "content": chunk}
            
        yield {"type": "complete", "content": "Done!"}
    except Exception as e:
        yield {"type": "error", "content": str(e)}
```

## 🧪 Testing Checklist
- [ ] Test natural language understanding with various phrasings
- [ ] Test all function success and error cases  
- [ ] Test streaming if implemented
- [ ] Test frontend integration and quick actions
- [ ] Verify no duplicate messages on page reload
- [ ] Check error handling and logging

## 📚 Reference Examples
- `CourseCreationAgent`: Basic CRUD operations with LLM intelligence
- `CourseDesignAgent`: Complex streaming with multiple functions
- `chat-interface.tsx`: Frontend integration patterns

---

**Key Principle**: Trust the LLM's intelligence. Provide clear context and functions, then let GPT-4 do what it does best - understand and act on natural language requests.
