"""
Configuration settings for the PDF processing pipeline.
"""
import os
from pathlib import Path

# Base paths - automatically detect the project root
# First try environment variable, then use relative path from this file
if os.environ.get("AWSHACKATHON_DIR"):
    BASE_DIR = Path(os.environ.get("AWSHACKATHON_DIR"))
else:
    # Get the directory where this config file is located
    CONFIG_FILE = Path(__file__).resolve()
    # Go up one level to get the project root (awshackathon directory)
    BASE_DIR = CONFIG_FILE.parent.parent
PROCUREMENT_DOCS_DIR = BASE_DIR / "procurement_docs"
OUTPUT_DIR = BASE_DIR / "processed_json"
TEMP_IMAGES_DIR = BASE_DIR / "temp_images"

# Ensure directories exist with parent directories
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
TEMP_IMAGES_DIR.mkdir(exist_ok=True, parents=True)

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
LOG_DIR.mkdir(exist_ok=True, parents=True)
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Component types expected in OCR results
COMPONENT_TYPES = ["text", "table", "image", "header", "footer"]
