import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import openai
from openai import OpenAI
from .websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

class AutoGenSlideOrchestrator:
    """
    Multi-agent orchestrator for generating educational slides using OpenAI's models.
    Simulates a conversation between different AI agents with specialized roles.
    """
    
    def __init__(self):
        self.client = None
        # Don't initialize client immediately - wait until needed
        
        # Define agent roles and their responsibilities
        self.agents = {
            "content_strategist": {
                "name": "Content Strategist",
                "role": "Educational Content Strategy",
                "description": "Analyzes course content and creates comprehensive slide outlines",
                "system_prompt": """You are an expert Educational Content Strategist. Your role is to:
1. Analyze course curriculum and pedagogy content
2. Create a comprehensive slide deck outline
3. Determine the optimal number and sequence of slides
4. Ensure educational objectives are met
5. Consider different learning styles and engagement techniques

Always provide structured, educational content that follows best practices in instructional design."""
            },
            "slide_designer": {
                "name": "Slide Designer", 
                "role": "Visual Design & Layout",
                "description": "Creates visually appealing slide layouts and determines content structure",
                "system_prompt": """You are an expert Slide Designer specializing in educational presentations. Your role is to:
1. Design visually appealing and pedagogically effective slide layouts
2. Determine appropriate template types for different content
3. Structure content for maximum readability and engagement
4. Suggest visual elements, diagrams, and images
5. Ensure accessibility and clarity in design

Focus on creating slides that enhance learning and maintain student attention."""
            },
            "content_writer": {
                "name": "Content Writer",
                "role": "Educational Content Creation", 
                "description": "Writes clear, engaging educational content for slides",
                "system_prompt": """You are an expert Educational Content Writer. Your role is to:
1. Write clear, concise, and engaging slide content
2. Adapt complex concepts for the target audience
3. Create compelling headlines and bullet points
4. Ensure content is pedagogically sound
5. Maintain consistency in tone and style

Write content that is educational, accessible, and engaging for students."""
            },
            "reviewer": {
                "name": "Quality Reviewer",
                "role": "Quality Assurance & Review",
                "description": "Reviews and refines slide content for quality and educational effectiveness",
                "system_prompt": """You are an expert Quality Reviewer for educational content. Your role is to:
1. Review slide content for accuracy and clarity
2. Ensure educational objectives are met
3. Check for consistency across slides
4. Suggest improvements for better learning outcomes
5. Validate that content follows instructional design principles

Provide constructive feedback to improve the overall quality of the slide deck."""
            }
        }
    
    def _initialize_client(self):
        """Initialize OpenAI client with API key"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY environment variable is required")
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(api_key=api_key)
        logger.info("OpenAI client initialized successfully")
    
    async def generate_slides_with_conversation(self, course_data: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Generate slides using multi-agent conversation approach
        """
        try:
            logger.info(f"Starting slide generation for session {session_id}")
            
            # Send initial status update
            await websocket_manager.send_status_update(
                session_id, 
                "initializing", 
                "Starting multi-agent slide generation"
            )
            
            conversation_log = []
            agent_decisions = {}
            
            # Step 1: Content Strategy Phase
            await websocket_manager.send_progress_update(session_id, 1, 4, "Content Strategy Phase")
            
            strategy_result = await self._content_strategy_phase(course_data, session_id, conversation_log)
            agent_decisions["content_strategy"] = strategy_result
            
            # Step 2: Slide Design Phase  
            await websocket_manager.send_progress_update(session_id, 2, 4, "Slide Design Phase")
            
            design_result = await self._slide_design_phase(course_data, strategy_result, session_id, conversation_log)
            agent_decisions["slide_design"] = design_result
            
            # Step 3: Content Creation Phase
            await websocket_manager.send_progress_update(session_id, 3, 4, "Content Creation Phase")
            
            slides = await self._content_creation_phase(course_data, strategy_result, design_result, session_id, conversation_log)
            
            # Step 4: Review and Refinement Phase
            await websocket_manager.send_progress_update(session_id, 4, 4, "Review and Refinement Phase")
            
            final_slides = await self._review_phase(slides, session_id, conversation_log)
            agent_decisions["final_slides"] = final_slides
            
            logger.info(f"Slide generation completed for session {session_id}. Generated {len(final_slides)} slides.")
            
            return {
                "slides": final_slides,
                "conversation_log": conversation_log,
                "agent_decisions": agent_decisions,
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Error in slide generation: {str(e)}")
            await websocket_manager.send_status_update(
                session_id, 
                "error", 
                f"Error in slide generation: {str(e)}"
            )
            raise
    
    async def _content_strategy_phase(self, course_data: Dict[str, Any], session_id: str, conversation_log: List) -> Dict[str, Any]:
        """Phase 1: Content Strategist analyzes course and creates outline"""
        
        agent = self.agents["content_strategist"]
        
        await websocket_manager.send_agent_message(
            session_id,
            agent["name"],
            agent["role"], 
            "Analyzing course content and creating slide deck strategy...",
            1
        )
        
        # Prepare prompt for content strategist
        prompt = f"""
Course Information:
- Name: {course_data['name']}
- Description: {course_data.get('description', 'N/A')}

Curriculum Content:
{course_data.get('curriculum_content', 'No curriculum provided')}

Pedagogy Content:
{course_data.get('pedagogy_content', 'No pedagogy provided')}

Research Report:
{course_data.get('research_report', 'No research report available')[:2000]}...

Based on this course information, create a comprehensive slide deck strategy. Provide:
1. Recommended number of slides (typically 15-25 for a complete course)
2. Slide sequence and topics
3. Learning objectives for each section
4. Key concepts to emphasize
5. Suggested slide types (title, content, diagram, summary, etc.)

Format your response as a JSON object with the following structure:
{{
    "total_slides": number,
    "slide_outline": [
        {{
            "slide_number": 1,
            "title": "slide title",
            "type": "title|content|diagram|summary|conclusion",
            "learning_objective": "what students should learn",
            "key_concepts": ["concept1", "concept2"],
            "content_focus": "main content area"
        }}
    ],
    "overall_strategy": "description of the overall approach"
}}
"""
        
        try:
            if not self.client:
                self._initialize_client()
                
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": agent["system_prompt"]},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            strategy_content = response.choices[0].message.content
            
            # Log the conversation
            conversation_log.append({
                "step": 1,
                "agent": agent["name"],
                "role": agent["role"],
                "input": "Course analysis request",
                "output": strategy_content,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            await websocket_manager.send_agent_message(
                session_id,
                agent["name"],
                agent["role"],
                f"Created strategy for {course_data['name']} with comprehensive slide outline",
                1
            )
            
            # Parse JSON response
            try:
                strategy_json = json.loads(strategy_content)
                return strategy_json
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                logger.warning("Failed to parse strategy JSON, using fallback")
                return self._create_fallback_strategy(course_data)
                
        except Exception as e:
            logger.error(f"Error in content strategy phase: {str(e)}")
            return self._create_fallback_strategy(course_data)
    
    async def _slide_design_phase(self, course_data: Dict[str, Any], strategy: Dict[str, Any], session_id: str, conversation_log: List) -> Dict[str, Any]:
        """Phase 2: Slide Designer creates visual layouts and templates"""
        
        agent = self.agents["slide_designer"]
        
        await websocket_manager.send_agent_message(
            session_id,
            agent["name"],
            agent["role"],
            "Designing slide layouts and visual templates...",
            2
        )
        
        prompt = f"""
Based on the content strategy for "{course_data['name']}", design the visual layout and templates for each slide.

Content Strategy:
{json.dumps(strategy, indent=2)}

For each slide in the outline, provide:
1. Template type (title_slide, content_slide, diagram_slide, image_slide, summary_slide)
2. Layout configuration (header, content areas, visual elements)
3. Visual elements needed (images, diagrams, charts)
4. Color scheme and styling suggestions
5. Accessibility considerations

Format your response as a JSON object:
{{
    "design_theme": "overall visual theme",
    "color_scheme": {{"primary": "#color", "secondary": "#color", "accent": "#color"}},
    "slide_designs": [
        {{
            "slide_number": 1,
            "template_type": "title_slide|content_slide|diagram_slide|image_slide|summary_slide",
            "layout_config": {{
                "header_style": "large|medium|small",
                "content_layout": "single_column|two_column|three_column|centered",
                "visual_elements": ["bullet_points", "images", "diagrams", "charts"]
            }},
            "suggested_images": ["description of needed images"],
            "accessibility_notes": "accessibility considerations"
        }}
    ]
}}
"""
        
        try:
            if not self.client:
                self._initialize_client()
                
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": agent["system_prompt"]},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                max_tokens=2000
            )
            
            design_content = response.choices[0].message.content
            
            conversation_log.append({
                "step": 2,
                "agent": agent["name"],
                "role": agent["role"],
                "input": "Design layout request",
                "output": design_content,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            await websocket_manager.send_agent_message(
                session_id,
                agent["name"],
                agent["role"],
                f"Created visual designs and layouts for {strategy.get('total_slides', 'multiple')} slides",
                2
            )
            
            try:
                design_json = json.loads(design_content)
                return design_json
            except json.JSONDecodeError:
                logger.warning("Failed to parse design JSON, using fallback")
                return self._create_fallback_design(strategy)
                
        except Exception as e:
            logger.error(f"Error in slide design phase: {str(e)}")
            return self._create_fallback_design(strategy)
    
    async def _content_creation_phase(self, course_data: Dict[str, Any], strategy: Dict[str, Any], design: Dict[str, Any], session_id: str, conversation_log: List) -> List[Dict[str, Any]]:
        """Phase 3: Content Writer creates actual slide content"""
        
        agent = self.agents["content_writer"]
        
        await websocket_manager.send_agent_message(
            session_id,
            agent["name"],
            agent["role"],
            "Writing educational content for each slide...",
            3
        )
        
        slides = []
        slide_outline = strategy.get("slide_outline", [])
        slide_designs = design.get("slide_designs", [])
        
        # Create a mapping of slide designs by slide number
        design_map = {d.get("slide_number", i+1): d for i, d in enumerate(slide_designs)}
        
        for i, slide_info in enumerate(slide_outline):
            slide_number = slide_info.get("slide_number", i + 1)
            slide_design = design_map.get(slide_number, {})
            
            await websocket_manager.send_agent_message(
                session_id,
                agent["name"],
                agent["role"],
                f"Creating content for slide {slide_number}: {slide_info.get('title', 'Untitled')}",
                3
            )
            
            prompt = f"""
Create detailed content for slide {slide_number} of the "{course_data['name']}" course.

Slide Information:
- Title: {slide_info.get('title', 'Untitled')}
- Type: {slide_info.get('type', 'content')}
- Learning Objective: {slide_info.get('learning_objective', 'N/A')}
- Key Concepts: {slide_info.get('key_concepts', [])}
- Content Focus: {slide_info.get('content_focus', 'N/A')}

Design Specifications:
- Template Type: {slide_design.get('template_type', 'content_slide')}
- Layout: {slide_design.get('layout_config', {})}

Course Context:
{course_data.get('curriculum_content', '')[:500]}...

Create engaging, educational content that:
1. Clearly presents the key concepts
2. Is appropriate for the slide type and layout
3. Engages students and supports learning
4. Follows good instructional design principles

Format as JSON:
{{
    "slide_number": {slide_number},
    "title": "final slide title",
    "content": "main slide content (use markdown formatting)",
    "bullet_points": ["key point 1", "key point 2", "key point 3"],
    "speaker_notes": "additional notes for instructor",
    "key_takeaways": ["main learning point 1", "main learning point 2"]
}}
"""
            
            try:
                if not self.client:
                    self._initialize_client()
                    
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": agent["system_prompt"]},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                
                content_response = response.choices[0].message.content
                
                try:
                    slide_content = json.loads(content_response)
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    slide_content = {
                        "slide_number": slide_number,
                        "title": slide_info.get('title', f'Slide {slide_number}'),
                        "content": content_response,
                        "bullet_points": [],
                        "speaker_notes": "",
                        "key_takeaways": []
                    }
                
                # Combine with design information
                final_slide = {
                    **slide_content,
                    "template_type": slide_design.get('template_type', 'content_slide'),
                    "layout_config": slide_design.get('layout_config', {}),
                    "images": slide_design.get('suggested_images', []),
                    "agent_decisions": {
                        "strategy": slide_info,
                        "design": slide_design,
                        "content": slide_content
                    }
                }
                
                slides.append(final_slide)
                
                # Send progress update
                await websocket_manager.send_slide_generated(
                    session_id,
                    slide_number,
                    slide_content.get('title', f'Slide {slide_number}'),
                    len(slide_outline)
                )
                
            except Exception as e:
                logger.error(f"Error creating content for slide {slide_number}: {str(e)}")
                # Create fallback slide
                fallback_slide = {
                    "slide_number": slide_number,
                    "title": slide_info.get('title', f'Slide {slide_number}'),
                    "content": f"Content for {slide_info.get('title', 'this slide')} will be added here.",
                    "template_type": "content_slide",
                    "layout_config": {},
                    "images": [],
                    "agent_decisions": {}
                }
                slides.append(fallback_slide)
        
        conversation_log.append({
            "step": 3,
            "agent": agent["name"],
            "role": agent["role"],
            "input": "Content creation for all slides",
            "output": f"Created content for {len(slides)} slides",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        await websocket_manager.send_agent_message(
            session_id,
            agent["name"],
            agent["role"],
            f"Completed content creation for {len(slides)} slides",
            3
        )
        
        return slides
    
    async def _review_phase(self, slides: List[Dict[str, Any]], session_id: str, conversation_log: List) -> List[Dict[str, Any]]:
        """Phase 4: Quality Reviewer reviews and refines the slides"""
        
        agent = self.agents["reviewer"]
        
        await websocket_manager.send_agent_message(
            session_id,
            agent["name"],
            agent["role"],
            "Reviewing slide quality and educational effectiveness...",
            4
        )
        
        # For now, we'll do a simple review that ensures consistency
        # In a more advanced implementation, this could involve another AI call
        
        reviewed_slides = []
        for slide in slides:
            # Basic quality checks and improvements
            reviewed_slide = slide.copy()
            
            # Ensure title is properly formatted
            if 'title' in reviewed_slide:
                reviewed_slide['title'] = reviewed_slide['title'].strip()
            
            # Ensure content is properly formatted
            if 'content' in reviewed_slide:
                reviewed_slide['content'] = reviewed_slide['content'].strip()
            
            # Add review metadata
            reviewed_slide['reviewed'] = True
            reviewed_slide['review_timestamp'] = datetime.utcnow().isoformat()
            
            reviewed_slides.append(reviewed_slide)
        
        conversation_log.append({
            "step": 4,
            "agent": agent["name"],
            "role": agent["role"],
            "input": f"Review of {len(slides)} slides",
            "output": f"Completed quality review of {len(reviewed_slides)} slides",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        await websocket_manager.send_agent_message(
            session_id,
            agent["name"],
            agent["role"],
            f"Quality review completed. {len(reviewed_slides)} slides ready for presentation",
            4
        )
        
        return reviewed_slides
    
    def _create_fallback_strategy(self, course_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a fallback strategy if AI generation fails"""
        return {
            "total_slides": 10,
            "slide_outline": [
                {"slide_number": 1, "title": f"Introduction to {course_data['name']}", "type": "title", "learning_objective": "Course overview", "key_concepts": ["introduction"], "content_focus": "course introduction"},
                {"slide_number": 2, "title": "Learning Objectives", "type": "content", "learning_objective": "Understand course goals", "key_concepts": ["objectives"], "content_focus": "learning goals"},
                {"slide_number": 3, "title": "Course Overview", "type": "content", "learning_objective": "Course structure", "key_concepts": ["overview"], "content_focus": "course structure"},
                {"slide_number": 4, "title": "Key Concepts", "type": "content", "learning_objective": "Core concepts", "key_concepts": ["concepts"], "content_focus": "main concepts"},
                {"slide_number": 5, "title": "Module 1", "type": "content", "learning_objective": "First module", "key_concepts": ["module1"], "content_focus": "first module"},
                {"slide_number": 6, "title": "Module 2", "type": "content", "learning_objective": "Second module", "key_concepts": ["module2"], "content_focus": "second module"},
                {"slide_number": 7, "title": "Module 3", "type": "content", "learning_objective": "Third module", "key_concepts": ["module3"], "content_focus": "third module"},
                {"slide_number": 8, "title": "Practical Applications", "type": "content", "learning_objective": "Apply knowledge", "key_concepts": ["applications"], "content_focus": "practical use"},
                {"slide_number": 9, "title": "Summary", "type": "summary", "learning_objective": "Review key points", "key_concepts": ["summary"], "content_focus": "course summary"},
                {"slide_number": 10, "title": "Questions & Discussion", "type": "conclusion", "learning_objective": "Engage students", "key_concepts": ["discussion"], "content_focus": "Q&A"}
            ],
            "overall_strategy": "Comprehensive course introduction with modular content structure"
        }
    
    def _create_fallback_design(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Create a fallback design if AI generation fails"""
        slide_designs = []
        for slide in strategy.get("slide_outline", []):
            slide_designs.append({
                "slide_number": slide.get("slide_number", 1),
                "template_type": "content_slide",
                "layout_config": {
                    "header_style": "medium",
                    "content_layout": "single_column",
                    "visual_elements": ["bullet_points"]
                },
                "suggested_images": [],
                "accessibility_notes": "Standard accessibility features"
            })
        
        return {
            "design_theme": "Professional Educational",
            "color_scheme": {"primary": "#2563eb", "secondary": "#64748b", "accent": "#059669"},
            "slide_designs": slide_designs
        }
    
    async def generate_image_from_prompt(self, prompt: str) -> Optional[str]:
        """Generate an image using OpenAI's image generation model"""
        try:
            if not self.client:
                self._initialize_client()
            
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            
            image_url = response.data[0].url
            logger.info(f"Generated image for prompt: {prompt[:50]}...")
            return image_url
            
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            return None

# Global orchestrator instance
autogen_orchestrator = AutoGenSlideOrchestrator()
