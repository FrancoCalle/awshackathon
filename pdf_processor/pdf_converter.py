"""
PDF to image converter module.
"""
import os
from pathlib import Path
from typing import List, Tuple
import fitz  # PyMuPDF
from PIL import Image
import io

from .config import DPI, IMAGE_FORMAT, TEMP_IMAGES_DIR
from .utils import setup_logger, clean_temp_images


logger = setup_logger(__name__)


class PDFConverter:
    """Convert PDF pages to images for OCR processing."""
    
    def __init__(self, dpi: int = DPI, image_format: str = IMAGE_FORMAT):
        """
        Initialize the PDF converter.
        
        Args:
            dpi: Resolution for image conversion
            image_format: Output image format (PNG, JPEG, etc.)
        """
        self.dpi = dpi
        self.image_format = image_format
        self.zoom = dpi / 72.0  # PDF standard is 72 DPI
    
    def convert_pdf_to_images(self, pdf_path: Path, job_id: str) -> List[Tuple[int, Path]]:
        """
        Convert all pages of a PDF to images.
        
        Args:
            pdf_path: Path to the PDF file
            job_id: Job identifier for organizing temp files
            
        Returns:
            List of tuples (page_number, image_path)
        """
        logger.info(f"Starting PDF to image conversion for: {pdf_path.name}")
        
        # Create temp directory for this job
        job_temp_dir = TEMP_IMAGES_DIR / job_id
        job_temp_dir.mkdir(exist_ok=True)
        
        image_paths = []
        
        try:
            # Open PDF
            pdf_document = fitz.open(str(pdf_path))
            total_pages = len(pdf_document)
            
            logger.info(f"Converting {total_pages} pages to images...")
            
            for page_num in range(total_pages):
                # Get page
                page = pdf_document[page_num]
                
                # Convert to image
                mat = fitz.Matrix(self.zoom, self.zoom)
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                
                # Save image
                image_filename = f"page_{page_num + 1:04d}.{self.image_format.lower()}"
                image_path = job_temp_dir / image_filename
                
                if self.image_format.upper() == "PNG":
                    img.save(image_path, "PNG", optimize=True)
                else:
                    # Convert to RGB if saving as JPEG
                    if img.mode in ('RGBA', 'LA'):
                        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                        rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = rgb_img
                    img.save(image_path, self.image_format.upper(), quality=95)
                
                image_paths.append((page_num + 1, image_path))
                
                logger.debug(f"Converted page {page_num + 1}/{total_pages}")
            
            pdf_document.close()
            logger.info(f"Successfully converted {total_pages} pages")
            
            return image_paths
            
        except Exception as e:
            logger.error(f"Error converting PDF to images: {str(e)}")
            # Clean up on error
            clean_temp_images(job_id)
            raise
    
    def get_pdf_info(self, pdf_path: Path) -> dict:
        """
        Get basic information about a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with PDF metadata
        """
        try:
            pdf_document = fitz.open(str(pdf_path))
            info = {
                'page_count': len(pdf_document),
                'metadata': pdf_document.metadata,
                'is_encrypted': pdf_document.is_encrypted,
                'needs_pass': pdf_document.needs_pass
            }
            pdf_document.close()
            return info
        except Exception as e:
            logger.error(f"Error reading PDF info: {str(e)}")
            raise


def convert_single_page(pdf_path: Path, page_num: int, output_path: Path, 
                       dpi: int = DPI) -> Path:
    """
    Convert a single page from a PDF to an image.
    
    Args:
        pdf_path: Path to the PDF file
        page_num: Page number to convert (1-indexed)
        output_path: Path to save the image
        dpi: Resolution for conversion
        
    Returns:
        Path to the saved image
    """
    try:
        pdf_document = fitz.open(str(pdf_path))
        
        if page_num < 1 or page_num > len(pdf_document):
            raise ValueError(f"Page number {page_num} is out of range")
        
        page = pdf_document[page_num - 1]  # Convert to 0-indexed
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        img.save(output_path, "PNG", optimize=True)
        
        pdf_document.close()
        return output_path
        
    except Exception as e:
        logger.error(f"Error converting page {page_num}: {str(e)}")
        raise
