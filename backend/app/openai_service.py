import openai
from typing import Optional, Dict, Any
from decouple import config
import difflib
import json
import ssl
import certifi
import httpx
import urllib3

# Disable SSL warnings for development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class OpenAIService:
    def __init__(self):
        # Create a custom HTTP client with SSL verification disabled for development
        http_client = httpx.Client(
            verify=False,  # Disable SSL verification for development
            timeout=60.0
        )
        
        self.client = openai.OpenAI(
            api_key=config("OPENAI_API_KEY"),
            http_client=http_client
        )
        self.model = "gpt-4o"

    def generate_curriculum(self, course_name: str) -> str:
        """Generate curriculum content based on course name"""
        print(f"OpenAI service - generating curriculum for: {course_name}")
        print(f"OpenAI client initialized: {self.client is not None}")
        print(f"Model: {self.model}")
        
        prompt = f"""
        Create a detailed curriculum for a course titled "{course_name}".
        
        Please structure the curriculum as a markdown document with the following format:
        
        # {course_name} - Curriculum
        
        ## Course Overview
        Brief description of the course and its objectives.
        
        ## Learning Outcomes
        List of specific learning outcomes students will achieve.
        
        ## Weekly Schedule
        
        ### Week 1: [Topic]
        - Learning objectives
        - Key concepts
        - Activities/assignments
        
        ### Week 2: [Topic]
        - Learning objectives
        - Key concepts
        - Activities/assignments
        
        [Continue for 12-16 weeks]
        
        ## Assessment Methods
        Description of how students will be evaluated.
        
        ## Required Resources
        List of textbooks, materials, and resources needed.
        
        Make sure the curriculum is comprehensive, well-structured, and appropriate for the course level.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert curriculum designer with extensive experience in creating comprehensive educational programs."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"Failed to generate curriculum: {str(e)}")

    def generate_pedagogy(self, course_name: str, curriculum_content: Optional[str] = None) -> str:
        """Generate pedagogy content based on course name and curriculum"""
        context = f"Course: {course_name}"
        if curriculum_content:
            context += f"\n\nCurriculum Context:\n{curriculum_content[:1000]}..."  # Limit context length
        
        prompt = f"""
        Create a comprehensive pedagogy document for the following course:
        
        {context}
        
        Please structure the pedagogy as a markdown document with the following format:
        
        # {course_name} - Pedagogy & Learning Approach
        
        ## Teaching Philosophy
        Describe the overall teaching approach and philosophy for this course.
        
        ## Learning Styles Accommodation
        How the course will accommodate different learning styles:
        - Visual learners
        - Auditory learners
        - Kinesthetic learners
        - Reading/writing learners
        
        ## Instructional Methods
        Detailed description of teaching methods to be used:
        - Lectures
        - Interactive sessions
        - Group work
        - Practical exercises
        - Case studies
        - Projects
        
        ## Student Engagement Strategies
        Specific strategies to keep students engaged and motivated.
        
        ## Assessment Philosophy
        Approach to assessment and feedback:
        - Formative assessment
        - Summative assessment
        - Peer assessment
        - Self-assessment
        
        ## Technology Integration
        How technology will be used to enhance learning.
        
        ## Differentiated Instruction
        How to adapt instruction for students with different needs and abilities.
        
        ## Learning Environment
        Description of the optimal learning environment for this course.
        
        Make sure the pedagogy is research-based and practical for implementation.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert educational pedagogy specialist with deep knowledge of learning theories and instructional design."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"Failed to generate pedagogy: {str(e)}")

    def enhance_content(self, content: str, content_type: str) -> Dict[str, Any]:
        """Enhance existing content and return suggestions with diff"""
        content_label = "curriculum" if content_type == "curriculum" else "pedagogy"
        
        prompt = f"""
        Please enhance and improve the following {content_label} content. 
        Make it more comprehensive, better structured, and pedagogically sound.
        
        Original Content:
        {content}
        
        Please provide an enhanced version that:
        1. Improves clarity and structure
        2. Adds missing important elements
        3. Enhances educational value
        4. Maintains the original intent and scope
        5. Uses proper markdown formatting
        
        Return only the enhanced content without any explanations or meta-commentary.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"You are an expert {content_label} designer focused on creating high-quality educational content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=2500
            )
            
            enhanced_content = response.choices[0].message.content.strip()
            
            # Generate diff between original and enhanced content
            diff = self._generate_diff(content, enhanced_content)
            
            return {
                "enhanced_content": enhanced_content,
                "diff": diff,
                "has_changes": len(diff) > 0
            }
        except Exception as e:
            raise Exception(f"Failed to enhance content: {str(e)}")

    def _generate_diff(self, original: str, enhanced: str) -> list:
        """Generate a structured diff between original and enhanced content"""
        original_lines = original.splitlines(keepends=True)
        enhanced_lines = enhanced.splitlines(keepends=True)
        
        diff = list(difflib.unified_diff(
            original_lines, 
            enhanced_lines, 
            fromfile='original', 
            tofile='enhanced',
            lineterm=''
        ))
        
        # Convert diff to a more structured format for frontend consumption
        structured_diff = []
        current_chunk = None
        
        for line in diff:
            if line.startswith('@@'):
                if current_chunk:
                    structured_diff.append(current_chunk)
                current_chunk = {
                    "header": line.strip(),
                    "changes": []
                }
            elif line.startswith('-') and not line.startswith('---'):
                if current_chunk:
                    current_chunk["changes"].append({
                        "type": "removed",
                        "content": line[1:].rstrip('\n')
                    })
            elif line.startswith('+') and not line.startswith('+++'):
                if current_chunk:
                    current_chunk["changes"].append({
                        "type": "added",
                        "content": line[1:].rstrip('\n')
                    })
            elif line.startswith(' '):
                if current_chunk:
                    current_chunk["changes"].append({
                        "type": "unchanged",
                        "content": line[1:].rstrip('\n')
                    })
        
        if current_chunk:
            structured_diff.append(current_chunk)
        
        return structured_diff

# Global instance
openai_service = OpenAIService()
