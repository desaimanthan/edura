#!/usr/bin/env python3
"""
Test script to analyze CourseStructureAgent logic and identify structure generation issues
"""

import asyncio
import json
from datetime import datetime
from bson import ObjectId

# Mock classes for testing
class MockOpenAIService:
    async def create_chat_completion(self, model, messages, temperature=0.3, max_tokens=4000):
        # Simulate OpenAI returning excessive structure
        class MockChoice:
            def __init__(self):
                self.message = MockMessage()
        
        class MockMessage:
            def __init__(self):
                # Simulate problematic OpenAI response that generates too much content
                self.content = '''
                {
                  "success": true,
                  "structure": {
                    "course_title": "Test Course",
                    "modules": [
                      {
                        "module_number": 1,
                        "title": "Module 1",
                        "chapters": [
                          {
                            "chapter_number": 1,
                            "title": "Chapter 1",
                            "materials": [
                              {"type": "slide", "title": "Slide 1"},
                              {"type": "slide", "title": "Slide 2"},
                              {"type": "slide", "title": "Slide 3"}
                            ]
                          }
                        ]
                      }
                    ]
                  }
                }
                '''
        
        class MockResponse:
            def __init__(self):
                self.choices = [MockChoice()]
        
        return MockResponse()

class MockDatabaseService:
    async def find_course(self, course_id):
        return {
            "_id": ObjectId(course_id),
            "name": "Test Course",
            "course_design_r2_key": "test-key",
            "research_r2_key": "research-key"
        }
    
    async def insert_document(self, collection, document):
        return str(ObjectId())

class MockR2StorageService:
    async def get_course_design_content(self, r2_key):
        # Simulate course design with 6 modules, 4 chapters each - using the actual format
        return '''
# 📚 Test Course

**Level:** Intermediate  
**Duration:** 8 weeks  
**Prerequisites:**
* Basic understanding of concepts
* Familiarity with tools

**Tools & Platforms:** Various tools and platforms

## **Module 1 — Fundamentals**

| **Chapter 1.1: Introduction** | Basic concepts and overview |
| **Chapter 1.2: Core Principles** | Key principles and foundations |
| **Chapter 1.3: Getting Started** | Initial setup and configuration |
| **Chapter 1.4: First Steps** | Basic operations and workflow |

## **Module 2 — Intermediate Concepts**

| **Chapter 2.1: Advanced Topics** | Complex concepts and theories |
| **Chapter 2.2: Practical Applications** | Real-world use cases |
| **Chapter 2.3: Best Practices** | Industry standards and guidelines |
| **Chapter 2.4: Optimization** | Performance tuning techniques |

## **Module 3 — Advanced Techniques**

| **Chapter 3.1: Expert Methods** | Advanced techniques and strategies |
| **Chapter 3.2: Complex Scenarios** | Challenging situations and solutions |
| **Chapter 3.3: Integration** | System integration approaches |
| **Chapter 3.4: Troubleshooting** | Problem solving methodologies |

## **Module 4 — Professional Development**

| **Chapter 4.1: Industry Standards** | Professional practices and standards |
| **Chapter 4.2: Team Collaboration** | Working effectively with teams |
| **Chapter 4.3: Project Management** | Managing projects and resources |
| **Chapter 4.4: Career Growth** | Professional development strategies |

## **Module 5 — Specialization**

| **Chapter 5.1: Domain Expertise** | Specialized knowledge areas |
| **Chapter 5.2: Advanced Tools** | Professional tools and technologies |
| **Chapter 5.3: Innovation** | Cutting-edge techniques and trends |
| **Chapter 5.4: Research** | Latest developments and research |

## **Module 6 — Mastery**

| **Chapter 6.1: Expert Level** | Mastery concepts and advanced topics |
| **Chapter 6.2: Leadership** | Leading projects and teams |
| **Chapter 6.3: Mentoring** | Teaching and mentoring others |
| **Chapter 6.4: Continuous Learning** | Staying current with developments |

## **Final Project**

Comprehensive capstone project integrating all course concepts and skills.
        '''

class MockMessageService:
    async def store_message(self, course_id, user_id, message, role, function_results=None):
        pass

class MockContextService:
    async def build_context_for_agent(self, course_id, user_id):
        return {
            "course_state": {"name": "Test Course"},
            "current_course_id": course_id
        }

async def test_structure_generation_logic():
    """Test the structure generation logic to identify issues"""
    
    print("🧪 Testing CourseStructureAgent Logic")
    print("=" * 60)
    
    # Import the actual CourseStructureAgent
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
    
    from backend.app.application.agents.course_structure_agent import CourseStructureAgent
    
    # Create mock services
    openai_service = MockOpenAIService()
    db_service = MockDatabaseService()
    r2_service = MockR2StorageService()
    message_service = MockMessageService()
    context_service = MockContextService()
    
    # Create agent
    agent = CourseStructureAgent(
        openai_service=openai_service,
        database_service=db_service,
        message_service=message_service,
        context_service=context_service,
        r2_storage_service=r2_service
    )
    
    # Test course design parsing
    print("1. Testing course design parsing...")
    course_id = "68a1b4fb7aad5d3ec0f227de"
    
    try:
        parse_result = await agent._parse_course_design(course_id)
        
        if parse_result["success"]:
            structure = parse_result["structure"]
            checklist = parse_result["checklist"]
            
            print(f"✅ Parsing successful")
            print(f"   📊 Modules in design: 6 (expected)")
            print(f"   📊 Modules generated: {len(structure.get('modules', []))}")
            print(f"   📊 Total items: {checklist['total_items']}")
            print(f"   📊 Total slides: {checklist['total_slides']}")
            print(f"   📊 Total assessments: {checklist['total_assessments']}")
            
            # Analyze each module
            print("\n2. Analyzing module structure...")
            for i, module in enumerate(structure.get("modules", []), 1):
                chapters = module.get("chapters", [])
                print(f"   Module {i}: {len(chapters)} chapters")
                
                for j, chapter in enumerate(chapters, 1):
                    materials = chapter.get("materials", [])
                    slides = [m for m in materials if m.get("type") == "slide"]
                    assessments = [m for m in materials if m.get("type") in ["quiz", "assessment"]]
                    
                    print(f"     Chapter {i}.{j}: {len(materials)} items ({len(slides)} slides, {len(assessments)} assessments)")
                    
                    # Check for excessive content
                    if len(slides) > 10:
                        print(f"     ⚠️  WARNING: Chapter {i}.{j} has {len(slides)} slides (excessive)")
                    if len(materials) > 15:
                        print(f"     ⚠️  WARNING: Chapter {i}.{j} has {len(materials)} total items (excessive)")
            
            # Check for discrepancies
            print("\n3. Checking for discrepancies...")
            expected_modules = 6
            expected_chapters_per_module = 4
            
            actual_modules = len(structure.get("modules", []))
            if actual_modules != expected_modules:
                print(f"   ❌ Module count mismatch: expected {expected_modules}, got {actual_modules}")
            else:
                print(f"   ✅ Module count correct: {actual_modules}")
            
            # Check chapter distribution
            for i, module in enumerate(structure.get("modules", []), 1):
                chapters = len(module.get("chapters", []))
                if chapters != expected_chapters_per_module:
                    print(f"   ❌ Module {i} chapter count mismatch: expected {expected_chapters_per_module}, got {chapters}")
                else:
                    print(f"   ✅ Module {i} chapter count correct: {chapters}")
            
            # Identify the root cause
            print("\n4. Root cause analysis...")
            
            # Check if OpenAI is generating too much content
            total_slides_per_chapter = []
            for module in structure.get("modules", []):
                for chapter in module.get("chapters", []):
                    materials = chapter.get("materials", [])
                    slides = [m for m in materials if m.get("type") == "slide"]
                    total_slides_per_chapter.append(len(slides))
            
            if total_slides_per_chapter:
                avg_slides = sum(total_slides_per_chapter) / len(total_slides_per_chapter)
                max_slides = max(total_slides_per_chapter)
                min_slides = min(total_slides_per_chapter)
                
                print(f"   📊 Slides per chapter - Avg: {avg_slides:.1f}, Min: {min_slides}, Max: {max_slides}")
                
                if max_slides > 10:
                    print(f"   ❌ ISSUE: Some chapters have excessive slides ({max_slides})")
                    print(f"   🔍 This suggests the generation logic is not constrained properly")
                
                if avg_slides > 6:
                    print(f"   ❌ ISSUE: Average slides per chapter is high ({avg_slides:.1f})")
                    print(f"   🔍 This suggests systematic over-generation")
        
        else:
            print(f"❌ Parsing failed: {parse_result.get('error')}")
    
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

def analyze_generation_approach():
    """Analyze the current generation approach and suggest improvements"""
    
    print("\n" + "=" * 60)
    print("📋 ANALYSIS: Current Structure Generation Approach")
    print("=" * 60)
    
    print("""
🔍 CURRENT ISSUES IDENTIFIED:

1. **OpenAI Over-Generation**:
   - Agent asks OpenAI to generate structure without constraints
   - No validation against original course design specifications
   - OpenAI may interpret "comprehensive" as "excessive"

2. **Fallback Logic Problems**:
   - When OpenAI parsing fails, fallback creates generic structures
   - Hardcoded patterns like 3-4 slides per chapter regardless of content
   - No consideration of actual course design requirements

3. **No Design Adherence**:
   - Generated structure doesn't match original course design
   - 6 modules → 7 modules, 4 chapters → 32 chapters
   - No validation step to ensure consistency

4. **Multiplication Errors**:
   - Possible loop issues or calculation errors
   - 87 slides per chapter suggests systematic multiplication problem

🎯 RECOMMENDED SOLUTIONS:

1. **Constrained Generation**:
   - Parse course design FIRST to extract exact structure
   - Use OpenAI only for content titles and descriptions
   - Enforce original module/chapter counts

2. **Design-First Approach**:
   - Extract structure from course-design.md as ground truth
   - Generate materials within each chapter based on content complexity
   - Validate generated structure against original design

3. **Reasonable Content Limits**:
   - 3-6 slides per chapter (based on content complexity)
   - 1-2 assessments per chapter maximum
   - Total materials per chapter: 4-8 items

4. **Validation Layer**:
   - Compare generated structure with original design
   - Flag discrepancies before saving
   - Allow user approval/modification

🚀 IMPLEMENTATION STRATEGY:

Option A: **Fix Structure First** (Recommended)
- Focus on getting the structure generation right
- Ensure it matches course design specifications
- Then worry about slide content quality

Option B: **Skip Structure, Focus on Slides**
- Generate slides directly from course design
- Skip the intermediate structure generation step
- More direct but less flexible

RECOMMENDATION: Go with Option A - fix the structure generation logic first,
as it provides better organization and user control over the course flow.
    """)

if __name__ == "__main__":
    print("🧪 CourseStructureAgent Analysis Tool")
    print("=" * 60)
    
    # Run the analysis
    analyze_generation_approach()
    
    # Run the test
    asyncio.run(test_structure_generation_logic())
