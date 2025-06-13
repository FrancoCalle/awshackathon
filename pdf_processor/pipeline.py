"""
Main processing pipeline that orchestrates the entire workflow.
"""
import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import json

from .config import PROCUREMENT_DOCS_DIR, OUTPUT_DIR, AWS_REGION
from .models import ProcessedDocument, ComponentStatistics
from .utils import (
    setup_logger, generate_job_id, clean_temp_images, 
    save_json_output, estimate_expected_components, validate_pdf_path
)
from .pdf_converter import PDFConverter
from .claude_ocr import ClaudeOCR


logger = setup_logger(__name__)


class PDFProcessor:
    """Main pipeline for processing PDFs with OCR."""
    
    def __init__(self, aws_region: str = AWS_REGION):
        """
        Initialize the PDF processor.
        
        Args:
            aws_region: AWS region for Bedrock service
        """
        self.pdf_converter = PDFConverter()
        self.ocr_client = ClaudeOCR(aws_region)
    
    def process_single_pdf(self, pdf_path: Path) -> Optional[ProcessedDocument]:
        """
        Process a single PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            ProcessedDocument object or None if processing fails
        """
        if not validate_pdf_path(pdf_path):
            logger.error(f"Invalid PDF path: {pdf_path}")
            return None
        
        job_id = generate_job_id(pdf_path.name)
        logger.info(f"Starting processing job {job_id} for: {pdf_path.name}")
        
        try:
            # Get PDF info
            pdf_info = self.pdf_converter.get_pdf_info(pdf_path)
            total_pages = pdf_info['page_count']
            
            # Convert PDF to images
            image_paths = self.pdf_converter.convert_pdf_to_images(pdf_path, job_id)
            
            # Process each page with OCR
            pages = []
            total_components = 0
            confidence_sum = 0
            confidence_count = 0
            component_stats = ComponentStatistics()
            
            for page_num, image_path in image_paths:
                logger.info(f"Processing page {page_num}/{total_pages}")
                
                page = self.ocr_client.process_image(image_path, page_num)
                
                if page:
                    pages.append(page)
                    total_components += page.component_count
                    
                    # Update statistics
                    for component in page.components:
                        # Update component type statistics
                        if hasattr(component_stats, component.type):
                            current_value = getattr(component_stats, component.type)
                            setattr(component_stats, component.type, current_value + 1)
                        
                        # Update confidence statistics
                        confidence_sum += component.confidence
                        confidence_count += 1
                else:
                    logger.warning(f"Failed to process page {page_num}")
            
            # Calculate average confidence
            avg_confidence = confidence_sum / confidence_count if confidence_count > 0 else 0
            
            # Create ProcessedDocument
            expected_components = estimate_expected_components(total_pages)
            
            processed_doc = ProcessedDocument(
                job_id=job_id,
                filename=pdf_path.name,
                compilation_time=datetime.now(),
                total_pages=total_pages,
                total_components=total_components,
                expected_components=expected_components,
                completeness=total_components / expected_components if expected_components > 0 else 1.0,
                component_statistics=component_stats,
                average_confidence=avg_confidence,
                pages=pages
            )
            
            # Save to JSON
            output_filename = pdf_path.stem + '.json'
            output_path = OUTPUT_DIR / output_filename
            save_json_output(processed_doc.dict(), output_path)
            
            logger.info(f"Successfully processed {pdf_path.name} -> {output_path}")
            
            return processed_doc
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path.name}: {str(e)}")
            return None
        
        finally:
            # Clean up temporary images
            clean_temp_images(job_id)
    
    def process_directory(self, directory: Path = PROCUREMENT_DOCS_DIR, 
                         pattern: str = "*.pdf") -> List[ProcessedDocument]:
        """
        Process all PDFs in a directory.
        
        Args:
            directory: Directory containing PDFs
            pattern: File pattern to match
            
        Returns:
            List of ProcessedDocument objects
        """
        pdf_files = list(directory.glob(pattern))
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        processed_docs = []
        
        for i, pdf_path in enumerate(pdf_files, 1):
            logger.info(f"Processing file {i}/{len(pdf_files)}: {pdf_path.name}")
            
            doc = self.process_single_pdf(pdf_path)
            if doc:
                processed_docs.append(doc)
            
            # Log progress
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{len(pdf_files)} files processed")
        
        logger.info(f"Completed processing. Successfully processed {len(processed_docs)}/{len(pdf_files)} files")
        
        return processed_docs
    
    def process_batch(self, pdf_paths: List[Path]) -> List[ProcessedDocument]:
        """
        Process a batch of specific PDF files.
        
        Args:
            pdf_paths: List of PDF file paths
            
        Returns:
            List of ProcessedDocument objects
        """
        logger.info(f"Processing batch of {len(pdf_paths)} PDFs")
        
        processed_docs = []
        
        for i, pdf_path in enumerate(pdf_paths, 1):
            logger.info(f"Processing {i}/{len(pdf_paths)}: {pdf_path.name}")
            
            doc = self.process_single_pdf(pdf_path)
            if doc:
                processed_docs.append(doc)
        
        return processed_docs
    
    def get_processing_summary(self, processed_docs: List[ProcessedDocument]) -> dict:
        """
        Generate a summary of the processing results.
        
        Args:
            processed_docs: List of processed documents
            
        Returns:
            Summary dictionary
        """
        if not processed_docs:
            return {"error": "No documents processed"}
        
        total_docs = len(processed_docs)
        total_pages = sum(doc.total_pages for doc in processed_docs)
        total_components = sum(doc.total_components for doc in processed_docs)
        avg_confidence = sum(doc.average_confidence for doc in processed_docs) / total_docs
        avg_completeness = sum(doc.completeness for doc in processed_docs) / total_docs
        
        # Aggregate component statistics
        total_stats = ComponentStatistics()
        for doc in processed_docs:
            for comp_type in ['text', 'table', 'image', 'header', 'footer']:
                current = getattr(total_stats, comp_type)
                doc_value = getattr(doc.component_statistics, comp_type)
                setattr(total_stats, comp_type, current + doc_value)
        
        return {
            "total_documents": total_docs,
            "total_pages": total_pages,
            "total_components": total_components,
            "average_confidence": round(avg_confidence, 4),
            "average_completeness": round(avg_completeness, 4),
            "component_breakdown": total_stats.dict(),
            "processing_time": datetime.now().isoformat()
        }


def create_processor(aws_region: str = AWS_REGION) -> PDFProcessor:
    """
    Factory function to create a PDF processor.
    
    Args:
        aws_region: AWS region for Bedrock service
        
    Returns:
        Configured PDFProcessor instance
    """
    return PDFProcessor(aws_region)
