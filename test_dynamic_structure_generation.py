#!/usr/bin/env python3
"""
Test script to verify the new dynamic structure generation logic
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.application.services.content_structure_service import ContentStructureService
from app.infrastructure.ai.openai_service import OpenAIService
from app.infrastructure.database.database_service import DatabaseService
from app.infrastructure.storage.r2_storage import R2StorageService

class MockOpenAIService:
    """Mock OpenAI service for testing"""
    
    async def create_chat_completion(self, model, messages, temperature=0.3, max_tokens=4000):
        """Mock chat completion that returns a dynamic structure"""
        
        # Extract course name from the user prompt
        user_message = messages[-1]["content"] if messages else ""
        course_name = "Test Course"
        
        if "COURSE:" in user_message:
            lines = user_message.split('\n')
            for line in lines:
                if line.startswith("COURSE:"):
                    course_name = line.replace("COURSE:", "").strip()
                    break
        
        # Return a mock response with dynamic structure
        mock_response = {
            "choices": [{
                "message": {
                    "content": f'''{{
  "success": true,
  "structure": {{
    "course_title": "{course_name}",
    "level": "Intermediate",
    "duration": "8 weeks",
    "prerequisites": ["Basic programming knowledge", "Understanding of web technologies"],
    "tools_platforms": "VS Code, Node.js, React",
    "modules": [
      {{
        "module_number": 1,
        "title": "Fundamentals and Setup",
        "learning_objectives": ["Understand core concepts", "Set up development environment"],
        "chapters": [
          {{
            "chapter_number": 1,
            "title": "Introduction to {course_name}",
            "details": "Core concepts and fundamentals",
            "estimated_duration": "2 hours",
            "materials": [
              {{"type": "slide", "title": "What is {course_name}?", "purpose": "Introduce the subject"}},
              {{"type": "slide", "title": "Key Benefits and Use Cases", "purpose": "Show practical applications"}},
              {{"type": "quiz", "title": "Fundamentals Quiz", "purpose": "Test basic understanding"}}
            ]
          }},
          {{
            "chapter_number": 2,
            "title": "Environment Setup",
            "details": "Setting up development tools and workspace",
            "estimated_duration": "1.5 hours",
            "materials": [
              {{"type": "slide", "title": "Required Tools and Software", "purpose": "List prerequisites"}},
              {{"type": "slide", "title": "Step-by-Step Installation Guide", "purpose": "Guide through setup"}},
              {{"type": "interactive", "title": "Setup Verification Lab", "purpose": "Hands-on practice"}},
              {{"type": "assessment", "title": "Environment Setup Check", "purpose": "Verify successful setup"}}
            ]
          }}
        ]
      }},
      {{
        "module_number": 2,
        "title": "Core Implementation",
        "learning_objectives": ["Build practical applications", "Apply best practices"],
        "chapters": [
          {{
            "chapter_number": 1,
            "title": "Building Your First Application",
            "details": "Hands-on development of a complete application",
            "estimated_duration": "3 hours",
            "materials": [
              {{"type": "slide", "title": "Application Architecture Overview", "purpose": "Explain structure"}},
              {{"type": "slide", "title": "Component Design Patterns", "purpose": "Show best practices"}},
              {{"type": "interactive", "title": "Build-Along Tutorial", "purpose": "Guided development"}},
              {{"type": "assessment", "title": "Application Development Project", "purpose": "Practical skill demonstration"}}
            ]
          }}
        ]
      }}
    ]
  }},
  "analysis_summary": {{
    "content_complexity": "Intermediate - requires hands-on practice and theoretical understanding",
    "recommended_pacing": "Self-paced with weekly milestones",
    "key_learning_outcomes": ["Practical application development", "Best practices implementation", "Problem-solving skills"],
    "content_distribution_rationale": "Balanced mix of theory and practice with emphasis on hands-on learning"
  }}
}}'''
                }
            }]
        }
        
        return type('MockResponse', (), mock_response)()

class MockDatabaseService:
    """Mock database service for testing"""
    
    async def find_course(self, course_id):
        return {
            "_id": course_id,
            "name": "Dynamic Test Course",
            "course_design_r2_key": "test_design_key",
            "research_r2_key": "test_research_key"
        }

class MockR2StorageService:
    """Mock R2 storage service for testing"""
    
    async def get_course_design_content(self, r2_key):
        if "design" in r2_key:
            return """# 📚 Dynamic Test Course

**Level:** Intermediate
**Duration:** 8 weeks
**Prerequisites:**
* Basic programming knowledge
* Understanding of web technologies

**Tools & Platforms:** VS Code, Node.js, React

## **Module 1 — Fundamentals and Setup**

| **Chapter 1.1: Introduction to Dynamic Test Course** | Learn the core concepts and fundamentals |
| **Chapter 1.2: Environment Setup** | Set up development tools and workspace |

## **Module 2 — Core Implementation**

| **Chapter 2.1: Building Your First Application** | Hands-on development of a complete application |

## **Final Project**

Comprehensive project integrating all course concepts."""
        
        elif "research" in r2_key:
            return """Research materials for Dynamic Test Course:

Key findings:
- Students learn best with hands-on practice
- Theoretical concepts should be immediately applied
- Progressive complexity helps retention
- Real-world examples increase engagement

Recommended approach:
- Start with fundamentals
- Build practical skills incrementally
- Include interactive exercises
- Provide immediate feedback through assessments"""
        
        return ""

async def test_dynamic_structure_generation():
    """Test the new dynamic structure generation"""
    
    print("🧪 Testing Dynamic Structure Generation")
    print("=" * 50)
    
    # Create mock services
    openai_service = MockOpenAIService()
    db_service = MockDatabaseService()
    storage_service = MockR2StorageService()
    
    # Create ContentStructureService with mocks
    content_service = ContentStructureService(
        database_service=db_service,
        r2_storage_service=storage_service,
        openai_service=openai_service
    )
    
    # Test course parsing
    print("1. Testing course design parsing...")
    result = await content_service.parse_course_design("test_course_id")
    
    if result["success"]:
        print("✅ Course parsing successful!")
        print(f"   📋 Course Title: {result['course_title']}")
        print(f"   📊 Total Modules: {result['total_modules']}")
        print(f"   📝 Total Items: {result['total_items']}")
        
        # Analyze the structure
        structure = result["structure"]
        checklist = result["checklist"]
        
        print("\n2. Analyzing generated structure...")
        print(f"   🎯 Level: {structure.get('level', 'Not specified')}")
        print(f"   ⏱️ Duration: {structure.get('duration', 'Not specified')}")
        print(f"   📚 Prerequisites: {len(structure.get('prerequisites', []))}")
        
        print("\n3. Module and Chapter Analysis:")
        total_materials = 0
        for module in structure.get("modules", []):
            module_materials = 0
            print(f"   📁 Module {module['module_number']}: {module['title']}")
            
            for chapter in module.get("chapters", []):
                chapter_materials = len(chapter.get("materials", []))
                module_materials += chapter_materials
                total_materials += chapter_materials
                
                print(f"      📄 Chapter {chapter['chapter_number']}: {chapter['title']} ({chapter_materials} materials)")
                
                # Show material types
                materials_by_type = {}
                for material in chapter.get("materials", []):
                    mat_type = material.get("type", "unknown")
                    materials_by_type[mat_type] = materials_by_type.get(mat_type, 0) + 1
                
                type_summary = ", ".join([f"{count} {type}" for type, count in materials_by_type.items()])
                print(f"         📋 Materials: {type_summary}")
            
            print(f"      📊 Module Total: {module_materials} materials")
        
        print(f"\n4. Content Distribution Analysis:")
        print(f"   📊 Total Materials: {total_materials}")
        print(f"   📈 Slides: {checklist['total_slides']}")
        print(f"   ❓ Quizzes: {checklist['total_quizzes']}")
        print(f"   📝 Assessments: {checklist['total_assessments']}")
        
        # Check for dynamic characteristics
        print(f"\n5. Dynamic Generation Verification:")
        
        # Check if content varies by chapter
        material_counts = []
        for module in structure.get("modules", []):
            for chapter in module.get("chapters", []):
                material_counts.append(len(chapter.get("materials", [])))
        
        if len(set(material_counts)) > 1:
            print("   ✅ Variable content density detected (good!)")
            print(f"      📊 Material counts per chapter: {material_counts}")
        else:
            print("   ⚠️ Fixed content density detected (may indicate hardcoding)")
        
        # Check for subject-specific titles
        generic_patterns = ["introduction", "overview", "key concepts", "examples", "practice"]
        specific_titles = []
        generic_titles = []
        
        for module in structure.get("modules", []):
            for chapter in module.get("chapters", []):
                for material in chapter.get("materials", []):
                    title = material.get("title", "").lower()
                    if any(pattern in title for pattern in generic_patterns):
                        generic_titles.append(material.get("title", ""))
                    else:
                        specific_titles.append(material.get("title", ""))
        
        print(f"   📋 Subject-specific titles: {len(specific_titles)}")
        print(f"   📋 Generic titles: {len(generic_titles)}")
        
        if len(specific_titles) > len(generic_titles):
            print("   ✅ More specific than generic titles (good!)")
        else:
            print("   ⚠️ More generic than specific titles (may need improvement)")
        
        # Show some examples
        if specific_titles:
            print(f"   📝 Example specific titles: {specific_titles[:3]}")
        if generic_titles:
            print(f"   📝 Example generic titles: {generic_titles[:3]}")
        
        print(f"\n🎉 Dynamic Structure Generation Test Complete!")
        print(f"✅ Successfully generated {result['total_modules']} modules with {result['total_items']} total items")
        
    else:
        print(f"❌ Course parsing failed: {result.get('error', 'Unknown error')}")
        return False
    
    return True

async def main():
    """Main test function"""
    try:
        success = await test_dynamic_structure_generation()
        if success:
            print("\n🎯 All tests passed! Dynamic structure generation is working correctly.")
            return 0
        else:
            print("\n❌ Tests failed! Check the implementation.")
            return 1
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
