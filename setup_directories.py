#!/usr/bin/env python3
"""
Setup script to create necessary directories for the PDF processor.
"""
import os
from pathlib import Path

# Get the base directory (where this script is located)
BASE_DIR = Path(__file__).parent

# Define directories to create
directories = [
    "processed_json",
    "temp_images",
    "logs",
    "procurement_docs"  # In case it doesn't exist
]

print("Setting up PDF Processor directories...")
print(f"Base directory: {BASE_DIR}")

for dir_name in directories:
    dir_path = BASE_DIR / dir_name
    try:
        dir_path.mkdir(exist_ok=True, parents=True)
        print(f"✓ Created/verified: {dir_path}")
    except Exception as e:
        print(f"✗ Error creating {dir_path}: {e}")

print("\nSetup complete!")

# Also create a .gitkeep file in temp_images to ensure it's tracked but empty
gitkeep_path = BASE_DIR / "temp_images" / ".gitkeep"
gitkeep_path.touch(exist_ok=True)

# Create .gitignore for processed_json to avoid committing output files
gitignore_content = """# Ignore all JSON output files
*.json

# But keep the directory
!.gitkeep
"""

gitignore_path = BASE_DIR / "processed_json" / ".gitignore"
with open(gitignore_path, 'w') as f:
    f.write(gitignore_content)

# Create .gitkeep for processed_json
gitkeep_json = BASE_DIR / "processed_json" / ".gitkeep"
gitkeep_json.touch(exist_ok=True)

print("\nAdded .gitignore and .gitkeep files for proper git tracking.")
