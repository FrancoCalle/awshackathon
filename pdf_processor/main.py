"""
Main script to run the PDF processing pipeline.
"""
import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
import boto3
from botocore.exceptions import NoCredentialsError, ProfileNotFound

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from pdf_processor.pipeline import create_processor
from pdf_processor.config import PROCUREMENT_DOCS_DIR, OUTPUT_DIR, AWS_REGION
from pdf_processor.utils import setup_logger


# Load environment variables
load_dotenv()

logger = setup_logger(__name__)


def verify_aws_credentials():
    """Verify that AWS credentials are properly configured."""
    try:
        # Try to create a boto3 session
        session = boto3.Session()
        credentials = session.get_credentials()
        
        if credentials is None:
            logger.error("No AWS credentials found. Please configure your AWS credentials.")
            logger.info("You can configure credentials by:")
            logger.info("1. Running 'aws configure' in your terminal")
            logger.info("2. Setting AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
            logger.info("3. Using IAM roles if running on EC2/Lambda")
            return False
        
        # Test if we can access Bedrock
        bedrock = boto3.client('bedrock', region_name=AWS_REGION)
        try:
            # Try to list foundation models to verify access
            bedrock.list_foundation_models()
            logger.info("AWS credentials verified successfully")
            return True
        except Exception as e:
            logger.error(f"Unable to access AWS Bedrock: {str(e)}")
            logger.info("Make sure your AWS account has access to Bedrock and the correct permissions")
            return False
            
    except NoCredentialsError:
        logger.error("AWS credentials not found")
        return False
    except Exception as e:
        logger.error(f"Error verifying AWS credentials: {str(e)}")
        return False


def main():
    """Main entry point for the PDF processing pipeline."""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Process PDF documents with OCR using Claude via AWS Bedrock"
    )
    parser.add_argument(
        "--region",
        type=str,
        default=os.getenv("AWS_REGION", AWS_REGION),
        help=f"AWS region for Bedrock (default: {AWS_REGION})"
    )
    parser.add_argument(
        "--profile",
        type=str,
        default=os.getenv("AWS_PROFILE"),
        help="AWS profile to use (optional)"
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=PROCUREMENT_DOCS_DIR,
        help="Directory containing PDF files to process"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Directory to save processed JSON files"
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Process a single PDF file"
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="*.pdf",
        help="File pattern to match (default: *.pdf)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of files to process"
    )
    parser.add_argument(
        "--model",
        type=str,
        choices=[
            "anthropic.claude-3-opus-20240229",
            "anthropic.claude-3-sonnet-20240229",
            "anthropic.claude-3-5-sonnet-20241022"
        ],
        help="Claude model to use in Bedrock"
    )
    
    args = parser.parse_args()
    
    # Set AWS profile if provided
    if args.profile:
        os.environ['AWS_PROFILE'] = args.profile
        logger.info(f"Using AWS profile: {args.profile}")
    
    # Verify AWS credentials
    if not verify_aws_credentials():
        logger.error("Failed to verify AWS credentials. Exiting.")
        sys.exit(1)
    
    # Override model if specified
    if args.model:
        from pdf_processor import config
        config.CLAUDE_MODEL = args.model
        logger.info(f"Using Claude model: {args.model}")
    
    # Create processor
    processor = create_processor(args.region)
    
    # Process files
    try:
        if args.file:
            # Process single file
            logger.info(f"Processing single file: {args.file}")
            doc = processor.process_single_pdf(args.file)
            
            if doc:
                logger.info(f"Successfully processed: {doc.filename}")
                logger.info(f"Total components extracted: {doc.total_components}")
                logger.info(f"Average confidence: {doc.average_confidence:.2%}")
            else:
                logger.error("Failed to process file")
                sys.exit(1)
        
        else:
            # Process directory
            pdf_files = list(args.input_dir.glob(args.pattern))
            
            if args.limit:
                pdf_files = pdf_files[:args.limit]
            
            logger.info(f"Found {len(pdf_files)} files to process")
            
            processed_docs = processor.process_batch(pdf_files)
            
            # Print summary
            summary = processor.get_processing_summary(processed_docs)
            
            logger.info("\n" + "="*50)
            logger.info("PROCESSING SUMMARY")
            logger.info("="*50)
            logger.info(f"Total documents processed: {summary['total_documents']}")
            logger.info(f"Total pages: {summary['total_pages']}")
            logger.info(f"Total components extracted: {summary['total_components']}")
            logger.info(f"Average confidence: {summary['average_confidence']:.2%}")
            logger.info(f"Average completeness: {summary['average_completeness']:.2%}")
            logger.info("\nComponent breakdown:")
            for comp_type, count in summary['component_breakdown'].items():
                logger.info(f"  - {comp_type}: {count}")
            
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
