import openai
from typing import Optional, Dict, Any
from decouple import config
import httpx
import urllib3
from datetime import datetime

# Disable SSL warnings for development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class DeepResearchService:
    def __init__(self):
        # Create a custom HTTP client with SSL verification disabled for development
        http_client = httpx.Client(
            verify=False,  # Disable SSL verification for development
            timeout=3600.0  # Extended timeout for deep research
        )
        
        self.client = openai.OpenAI(
            api_key=config("OPENAI_API_KEY"),
            http_client=http_client
        )
        self.model = "o3-deep-research"

    def start_deep_research(self, course_data: Dict[str, Any]) -> str:
        """Start o3-deep-research task with course data"""
        print(f"Starting deep research for course: {course_data.get('course_name', 'Unknown')}")
        
        input_text = self._construct_research_prompt(course_data)
        
        try:
            response = self.client.responses.create(
                model=self.model,
                input=input_text,
                background=True,  # Run in background mode
                store=True,  # Required for background mode
                tools=[
                    {"type": "web_search_preview"},
                    {"type": "code_interpreter", "container": {"type": "auto"}}
                ]
            )
            
            print(f"Deep research task started with ID: {response.id}, Status: {response.status}")
            return response.id
            
        except Exception as e:
            print(f"Error starting deep research: {str(e)}")
            raise Exception(f"Failed to start deep research: {str(e)}")

    def check_research_status(self, task_id: str) -> Dict[str, Any]:
        """Poll research task status from OpenAI"""
        try:
            response = self.client.responses.retrieve(task_id)
            
            result = {
                "status": response.status,
                "output": None,
                "error": None
            }
            
            # Map OpenAI statuses to our expected statuses
            if response.status == "completed":
                result["output"] = response.output_text
            elif response.status == "failed":
                result["error"] = getattr(response, 'error', 'Research task failed')
            elif response.status == "cancelled":
                result["error"] = "Research task was cancelled"
            
            print(f"Research status for {task_id}: {response.status}")
            return result
            
        except Exception as e:
            print(f"Error checking research status for task {task_id}: {str(e)}")
            return {
                "status": "failed",
                "output": None,
                "error": f"Failed to check status: {str(e)}"
            }

    def cancel_research(self, task_id: str) -> Dict[str, Any]:
        """Cancel a running research task"""
        try:
            response = self.client.responses.cancel(task_id)
            
            print(f"Research task {task_id} cancelled, Status: {response.status}")
            return {
                "status": response.status,
                "message": "Research task cancelled successfully"
            }
            
        except Exception as e:
            print(f"Error cancelling research task {task_id}: {str(e)}")
            return {
                "status": "failed",
                "error": f"Failed to cancel task: {str(e)}"
            }

    def _construct_research_prompt(self, course_data: Dict[str, Any]) -> str:
        """Construct the research prompt for o3-deep-research"""
        course_name = course_data.get('course_name', 'Unknown Course')
        description = course_data.get('description', 'No description provided')
        curriculum_content = course_data.get('curriculum_content', '')
        pedagogy_content = course_data.get('pedagogy_content', '')
        
        # Format curriculum content
        curriculum_section = ""
        if curriculum_content:
            curriculum_section = f"""
**Curriculum Outline:**
{curriculum_content[:2000]}...  # Limit to prevent token overflow
"""
        
        # Format pedagogy content
        pedagogy_section = ""
        if pedagogy_content:
            pedagogy_section = f"""
**Pedagogical Approach:**
{pedagogy_content[:1500]}...  # Limit to prevent token overflow
"""
        
        prompt = f"""
You are tasked with researching for a university-level course titled **{course_name}**.

**Course Description:** {description}

{curriculum_section}

{pedagogy_section}

Your goal is to conduct deep, multi-source research to support the creation of a complete slide-based course. For each module or topic identified in the curriculum, provide:

## Research Requirements:

1. **Key Concepts and Definitions**
   - Academic definitions with authoritative sources
   - Historical context and evolution of concepts
   - Current understanding and debates in the field

2. **Real-World Examples and Case Studies**
   - Industry applications and implementations
   - Success stories and failure analyses
   - Current trends and emerging practices

3. **Academic Foundation**
   - Relevant research papers and studies
   - Theoretical frameworks and models
   - Expert opinions and scholarly perspectives

4. **Common Misconceptions**
   - Frequent student misunderstandings
   - How to address and correct these misconceptions
   - Clear explanations and analogies

5. **Assessment and Learning Activities**
   - Questions aligned to different Bloom's taxonomy levels
   - Practical exercises and projects
   - Discussion prompts and critical thinking challenges

6. **Visual and Multimedia Concepts**
   - Descriptions of diagrams, charts, and infographics
   - Suggested animations or interactive elements
   - Visual metaphors and conceptual illustrations

## Output Format:

Structure your research as a comprehensive markdown document with:

# Deep Research Report: {course_name}

## Executive Summary
Brief overview of key findings and recommendations

## Module-by-Module Research

### Module 1: [Module Name]
- **Core Concepts**: [Detailed research with citations]
- **Real-World Applications**: [Examples and case studies]
- **Academic Sources**: [Key papers and references]
- **Common Misconceptions**: [Issues and solutions]
- **Assessment Ideas**: [Questions and activities]
- **Visual Concepts**: [Diagram descriptions]

[Continue for each module...]

## Supporting Materials Recommendations
- Textbooks and academic resources
- Online resources and databases
- Multimedia content suggestions
- Guest speaker recommendations

## Implementation Notes
- Sequencing recommendations
- Prerequisite knowledge requirements
- Time allocation suggestions
- Technology requirements

## Citations and References
[Comprehensive bibliography with proper academic citations]

## Requirements:
- Include inline citations (e.g., [Author, Year] or [Source Name])
- Use authoritative academic and industry sources
- Provide actionable insights for slide creation
- Be comprehensive but focused on practical application
- Include current (2020-2024) research and developments
- Structure content for easy conversion to presentation slides

Be analytical, thorough, and avoid surface-level responses. Think like an expert instructional researcher preparing comprehensive materials for course developers and slide authors.
"""
        
        return prompt

    def _format_curriculum_modules(self, curriculum_content: str) -> str:
        """Extract and format curriculum modules from markdown content"""
        if not curriculum_content:
            return "No curriculum modules specified"
        
        lines = curriculum_content.split('\n')
        modules = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('#') and ('module' in line.lower() or 'week' in line.lower() or 'chapter' in line.lower()):
                modules.append(line.replace('#', '').strip())
            elif line.startswith('-') and len(line) > 10:  # Bullet points that might be modules
                modules.append(line.replace('-', '').strip())
        
        if modules:
            return '\n'.join([f"- {module}" for module in modules[:10]])  # Limit to 10 modules
        else:
            return curriculum_content[:500] + "..." if len(curriculum_content) > 500 else curriculum_content

# Global instance
deep_research_service = DeepResearchService()
