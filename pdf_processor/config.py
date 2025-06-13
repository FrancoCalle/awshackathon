"""
Configuration settings for the PDF processing pipeline.
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(r"C:\Users\franc\OneDrive\Documents\GitHub\awshackathon")
PROCUREMENT_DOCS_DIR = BASE_DIR / "procurement_docs"
OUTPUT_DIR = BASE_DIR / "processed_json"
TEMP_IMAGES_DIR = BASE_DIR / "temp_images"

# Ensure directories exist
OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_IMAGES_DIR.mkdir(exist_ok=True)

# AWS Bedrock Claude settings
CLAUDE_MODEL = "anthropic.claude-3-opus-20240229"  # Claude Opus 3 in Bedrock
# Alternative: "anthropic.claude-3-sonnet-20240229" for Sonnet
# Alternative: "anthropic.claude-3-5-sonnet-20241022" for Sonnet 3.5
AWS_REGION = "us-east-1"  # Change to your preferred region

# PDF processing settings
DPI = 300  # Resolution for PDF to image conversion
IMAGE_FORMAT = "PNG"
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Logging settings
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Component types expected in OCR results
COMPONENT_TYPES = ["text", "table", "image", "header", "footer"]
