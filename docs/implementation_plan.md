# Implementation Plan

## Overview
Implement real-time file/folder updates in the Course Files tree during CourseStructureAgent execution to eliminate the loading icon delay and provide immediate visual feedback as content materials are generated.

The current issue is that when CourseStructureAgent generates course structure, the frontend shows a loading icon for an extended period, and the content folder only appears after completion and manual reload. This creates a poor user experience where users feel the system is stuck. The solution involves implementing real-time streaming updates from the backend agent to the frontend file store, similar to how research.md and course-design.md files appear in real-time.

## Types
Type system changes for real-time content material streaming.

**Backend Types:**
- Add streaming event types for content material creation: `material_created`, `folder_created`, `material_progress`
- Extend CourseStructureAgent streaming events to include file system updates
- Add incremental material saving events with file path information

**Frontend Types:**
- Extend FileNode interface to support pending/generating states for content materials
- Add streaming event handlers for content material creation in courseFileStore
- Update CourseFileTreeSnapshot to handle incremental updates during generation

**Event Stream Types:**
```typescript
interface ContentMaterialStreamEvent {
  type: 'material_created' | 'folder_created' | 'material_progress'
  file_path: string
  material_type: 'slide' | 'assessment' | 'quiz'
  title: string
  status: 'pending' | 'generating' | 'saved'
  module_number: number
  chapter_number: number
  slide_number?: number
}
```

## Files
File modifications for real-time content material streaming.

**New Files:**
- None required - using existing streaming infrastructure

**Modified Files:**
- `backend/app/application/agents/agent_4_course_structure_agent.py`: Add streaming events during incremental material saving
- `frontend/src/lib/courseFileStore.ts`: Add event handlers for content material streaming events
- `frontend/src/app/courses/create/components/chat-interface.tsx`: Handle content material streaming events in SSE processing
- `frontend/src/app/courses/create/[courseId]/page.tsx`: Remove manual polling, rely on real-time events

**Configuration Updates:**
- No configuration changes required

## Functions
Function modifications for real-time streaming.

**New Functions:**
- `CourseStructureAgent._emit_material_created_event()`: Emit streaming event when material is saved
- `CourseStructureAgent._emit_folder_created_event()`: Emit streaming event when folder structure is created
- `courseFileStore.handleContentMaterialEvent()`: Process incoming content material events

**Modified Functions:**
- `CourseStructureAgent._save_chapter_materials_immediately()`: Add streaming event emission after each material save
- `CourseStructureAgent.stream_structure_generation()`: Emit folder creation events at start
- `chat-interface.tsx.handleStreamingResponse()`: Add content material event processing
- `courseFileStore.loadContentMaterials()`: Optimize for real-time updates, reduce aggressive polling

**Removed Functions:**
- Remove polling-based material loading in page.tsx
- Remove manual refresh mechanisms that cause UI delays

## Classes
Class modifications for streaming support.

**Modified Classes:**
- `CourseStructureAgent`: Add streaming event emission during material generation
- `CourseFileStore`: Add real-time event processing for content materials
- `ChatInterface`: Extend SSE event handling for content material events

**New Methods:**
- `CourseStructureAgent.emit_streaming_event()`: Generic method to emit streaming events
- `CourseFileStore.processContentMaterialStream()`: Handle incoming content material stream events
- `CourseFileStore.createMaterialInRealTime()`: Create file nodes as materials are generated

## Dependencies
Dependency modifications for streaming implementation.

**Backend Dependencies:**
- No new dependencies required - using existing streaming infrastructure
- Leverage existing SSE (Server-Sent Events) implementation in FastAPI routes

**Frontend Dependencies:**
- No new dependencies required - using existing courseFileStore and SSE handling
- Utilize existing useSyncExternalStore for reactive updates

**Integration Requirements:**
- Ensure streaming events are properly formatted for existing SSE parser
- Maintain backward compatibility with existing file loading mechanisms

## Testing
Testing approach for real-time streaming functionality.

**Backend Tests:**
- Unit tests for CourseStructureAgent streaming event emission
- Integration tests for material creation with streaming events
- Test incremental saving with proper event sequencing

**Frontend Tests:**
- Unit tests for courseFileStore event handling
- Integration tests for real-time file tree updates
- Test SSE event processing in chat interface

**End-to-End Tests:**
- Test complete course structure generation with real-time file appearance
- Verify no loading delays or manual refresh requirements
- Test error handling during streaming failures

**Manual Testing:**
- Verify files appear immediately as they're generated
- Confirm loading icon disappears quickly
- Test folder structure creation in real-time

## Implementation Order
Sequential implementation steps to minimize conflicts.

**Step 1: Backend Streaming Events**
- Modify `CourseStructureAgent._save_chapter_materials_immediately()` to emit streaming events
- Add folder creation events in `stream_structure_generation()`
- Test streaming event emission during material generation

**Step 2: Frontend Event Handling**
- Add content material event handlers to `courseFileStore.ts`
- Implement real-time file node creation for materials
- Test file store updates with mock streaming events

**Step 3: SSE Integration**
- Extend `chat-interface.tsx` SSE processing for content material events
- Add event routing to courseFileStore from chat interface
- Test end-to-end streaming from backend to file store

**Step 4: UI Optimization**
- Remove polling mechanisms from `page.tsx`
- Optimize file tree rendering for real-time updates
- Add loading state management for individual materials

**Step 5: Testing and Refinement**
- Comprehensive testing of real-time file appearance
- Performance optimization for rapid event processing
- Error handling and fallback mechanisms

**Step 6: Cleanup and Documentation**
- Remove deprecated polling code
- Update documentation for real-time streaming
- Add monitoring for streaming event performance
