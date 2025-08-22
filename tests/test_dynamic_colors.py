#!/usr/bin/env python3
"""
Test script to demonstrate the dynamic color generation functionality
for course cover images.
"""

import asyncio
import sys
import os
import json

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.application.agents.image_generation_agent import ImageGenerationAgent


class MockOpenAIService:
    """Mock OpenAI service for testing color generation without API calls"""
    pass


class MockR2Storage:
    """Mock R2 storage for testing color generation without storage calls"""
    pass


async def test_dynamic_colors():
    """Test the dynamic color generation functionality"""
    
    # Create mock services
    openai_service = MockOpenAIService()
    r2_storage = MockR2Storage()
    
    # Create image generation agent
    agent = ImageGenerationAgent(openai_service, r2_storage)
    
    print("🎨 Testing Dynamic Color Generation for Course Covers\n")
    print("=" * 60)
    
    # Test courses with different subjects
    test_courses = [
        {
            "name": "Machine Learning Fundamentals",
            "description": "Learn the basics of artificial intelligence and neural networks",
            "style": "tech_focused"
        },
        {
            "name": "Python Programming Bootcamp",
            "description": "Complete guide to Python development and coding best practices",
            "style": "professional_educational"
        },
        {
            "name": "Digital Marketing Strategy",
            "description": "Master social media marketing and brand promotion techniques",
            "style": "colorful"
        },
        {
            "name": "Data Science with R",
            "description": "Statistical analysis and big data processing using R programming",
            "style": "modern"
        },
        {
            "name": "UI/UX Design Principles",
            "description": "Creative design thinking and user experience optimization",
            "style": "minimalist"
        },
        {
            "name": "Business Leadership",
            "description": "Strategic management and entrepreneurship fundamentals",
            "style": "professional_educational"
        }
    ]
    
    # Test color palette generation for each course
    for i, course in enumerate(test_courses, 1):
        print(f"\n{i}. Course: {course['name']}")
        print(f"   Description: {course['description']}")
        print(f"   Style: {course['style']}")
        print("-" * 50)
        
        # Preview color palette
        palette_preview = await agent.preview_color_palette(
            course['name'], 
            course['description'], 
            course['style']
        )
        
        print(f"   🎯 Detected Subject: {palette_preview['detected_subject']}")
        print(f"   🎨 Primary Color: {palette_preview['color_palette']['primary']}")
        print(f"   🎨 Secondary Color: {palette_preview['color_palette']['secondary']}")
        print(f"   🌈 Accent Colors: {', '.join(palette_preview['color_palette']['accents'])}")
        print(f"   🌡️  Temperature: {palette_preview['color_palette']['temperature']}")
        print(f"   ⚡ Contrast: {palette_preview['color_palette']['contrast']}")
        
        # Show gradient options
        gradients = palette_preview['color_palette']['gradients']
        if gradients:
            print(f"   📐 Gradients:")
            for j, gradient in enumerate(gradients, 1):
                print(f"      {j}. {gradient['from']} → {gradient['to']} ({gradient['direction']})")
    
    print("\n" + "=" * 60)
    print("🎨 Testing Subject-Based Color Themes")
    print("=" * 60)
    
    # Test subject color themes
    themes = await agent.get_subject_color_themes()
    for theme_name, theme_data in themes.items():
        print(f"\n📚 {theme_name.replace('_', ' ').title()}")
        print(f"   Colors: {', '.join(theme_data['colors'])}")
        print(f"   Description: {theme_data['description']}")
        print(f"   Keywords: {', '.join(theme_data['keywords'][:3])}...")
    
    print("\n" + "=" * 60)
    print("🎨 Testing Seasonal Color Palettes")
    print("=" * 60)
    
    # Test seasonal palettes
    seasons = ["spring", "summer", "autumn", "winter", "current"]
    for season in seasons:
        seasonal_palette = await agent.generate_seasonal_color_palette(season)
        print(f"\n🌸 {season.title()} Palette:")
        print(f"   Primary: {seasonal_palette['primary_color']}")
        print(f"   Secondary: {seasonal_palette['secondary_color']}")
        print(f"   Accents: {', '.join(seasonal_palette['accent_colors'][:3])}")
        if 'description' in seasonal_palette:
            print(f"   Description: {seasonal_palette['description']}")
    
    print("\n" + "=" * 60)
    print("🎨 Testing Custom Color Palette Generation")
    print("=" * 60)
    
    # Test custom color generation
    custom_colors = ["#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", "#feca57"]
    styles = ["professional_educational", "modern", "colorful", "minimalist", "tech_focused"]
    
    for color, style in zip(custom_colors, styles):
        custom_palette = agent.generate_custom_color_palette(color, style)
        print(f"\n🎨 Custom Palette (Base: {color}, Style: {style}):")
        print(f"   Primary: {custom_palette['primary_color']}")
        print(f"   Secondary: {custom_palette['secondary_color']}")
        print(f"   Accents: {', '.join(custom_palette['accent_colors'][:3])}")
        print(f"   Temperature: {custom_palette['color_temperature']}")
        print(f"   Contrast: {custom_palette['contrast_level']}")
    
    print("\n" + "=" * 60)
    print("✅ Dynamic Color Testing Complete!")
    print("=" * 60)
    
    print("\n📋 Summary of Dynamic Color Features:")
    print("   • Subject-based color detection (16 categories)")
    print("   • Style-specific accent color generation")
    print("   • Dynamic gradient combinations")
    print("   • Seasonal color palettes")
    print("   • Custom color palette generation")
    print("   • Color temperature and contrast control")
    print("   • Intelligent keyword-based subject detection")
    
    print("\n🚀 Benefits:")
    print("   • Each course gets unique, contextually relevant colors")
    print("   • Colors match the subject matter and style preference")
    print("   • Automatic variety prevents repetitive cover designs")
    print("   • Professional color harmony and accessibility")
    print("   • Seasonal and custom options for additional variety")


if __name__ == "__main__":
    asyncio.run(test_dynamic_colors())
