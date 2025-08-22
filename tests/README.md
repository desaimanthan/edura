# Tests

This directory contains test files for various components and features of the Edura platform.

## Test Files

- `test_agent_intelligence.py` - Tests for AI agent intelligence and functionality
- `test_course_structure_analysis.py` - Tests for course structure analysis features
- `test_curriculum_fix.py` - Tests for curriculum-related fixes and functionality
- `test_dynamic_colors.py` - Tests for dynamic color features
- `test_dynamic_structure_generation.py` - Tests for dynamic structure generation

## Running Tests

To run these tests, make sure you have the required dependencies installed:

```bash
cd backend
pip install -r requirements.txt
python -m pytest ../tests/
```

Or run individual test files:

```bash
python tests/test_agent_intelligence.py
```

## Organization

All test files have been moved from the root directory to maintain a clean project structure and follow Python testing conventions.
