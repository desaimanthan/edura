# Scripts

This directory contains utility and migration scripts for the Edura platform.

## Migration Scripts

- `migrate_existing_courses_to_multi_size_images.py` - Migrates existing courses to support multi-size image generation
- `update_existing_courses_to_small_images.py` - Updates existing courses to use smaller image sizes for optimization

## Usage

These scripts are typically run during database migrations or when updating existing data structures. Make sure to:

1. Backup your database before running any migration scripts
2. Test scripts in a development environment first
3. Have the required dependencies installed

```bash
cd backend
pip install -r requirements.txt
python ../scripts/migrate_existing_courses_to_multi_size_images.py
```

## Organization

All utility and migration scripts have been moved from the root directory to maintain a clean project structure and separate operational scripts from core application code.
