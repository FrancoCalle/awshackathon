"""
Utility functions for the PDF processing pipeline.
"""
import logging
import hashlib
import shutil
from pathlib import Path
from typing import Optional
import json
from datetime import datetime

from .config import LOG_DIR, LOG_FORMAT, TEMP_IMAGES_DIR


def setup_logger(name: str) -> logging.Logger:
    """
    Set up a logger with both file and console handlers.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler(
            LOG_DIR / f'pdf_processor_{datetime.now().strftime("%Y%m%d")}.log'
        )
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(LOG_FORMAT)
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger


def generate_job_id(filename: str) -> str:
    """
    Generate a unique job ID based on filename and timestamp.
    
    Args:
        filename: PDF filename
        
    Returns:
        8-character job ID
    """
    timestamp = str(datetime.now().timestamp())
    content = f"{filename}_{timestamp}"
    return hashlib.md5(content.encode()).hexdigest()[:8]


def clean_temp_images(job_id: str):
    """
    Clean up temporary images for a specific job.
    
    Args:
        job_id: Job identifier
    """
    job_temp_dir = TEMP_IMAGES_DIR / job_id
    if job_temp_dir.exists():
        shutil.rmtree(job_temp_dir)


def save_json_output(data: dict, output_path: Path):
    """
    Save processed data as formatted JSON.
    
    Args:
        data: Dictionary to save
        output_path: Path to save the JSON file
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def estimate_expected_components(page_count: int, avg_components_per_page: int = 8) -> int:
    """
    Estimate the expected number of components based on page count.
    
    Args:
        page_count: Number of pages in the document
        avg_components_per_page: Average components expected per page
        
    Returns:
        Estimated total components
    """
    return page_count * avg_components_per_page


def calculate_bbox_area(bbox: list) -> int:
    """
    Calculate the area of a bounding box.
    
    Args:
        bbox: Bounding box coordinates [x1, y1, x2, y2]
        
    Returns:
        Area of the bounding box
    """
    if len(bbox) != 4:
        return 0
    return abs(bbox[2] - bbox[0]) * abs(bbox[3] - bbox[1])


def validate_pdf_path(pdf_path: Path) -> bool:
    """
    Validate that the PDF path exists and is a PDF file.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        True if valid, False otherwise
    """
    return pdf_path.exists() and pdf_path.suffix.lower() == '.pdf'


def format_component_id(page_num: int, component_idx: int) -> str:
    """
    Format a component ID.
    
    Args:
        page_num: Page number (1-indexed)
        component_idx: Component index on the page (0-indexed)
        
    Returns:
        Formatted component ID
    """
    return f"{page_num}_{component_idx}"


def parse_table_content(raw_table: str) -> str:
    """
    Parse and format table content from raw text.
    
    Args:
        raw_table: Raw table text
        
    Returns:
        Formatted table in markdown style
    """
    # This is a simplified version - you might want to enhance this
    # based on the actual table formats you encounter
    lines = raw_table.strip().split('\n')
    if not lines:
        return raw_table
    
    # Simple markdown table formatting
    formatted_lines = []
    for i, line in enumerate(lines):
        if i == 1:  # Add separator after header
            cells = line.split('|')
            separator = '|' + '|'.join(['---' for _ in cells if cells]) + '|'
            formatted_lines.append(separator)
        formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)
