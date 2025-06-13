"""
Claude API integration for OCR processing using AWS Bedrock.
"""
import base64
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import boto3
from botocore.exceptions import ClientError

from .config import CLAUDE_MODEL, MAX_RETRIES, RETRY_DELAY, AWS_REGION
from .models import Component, Page
from .utils import setup_logger, format_component_id


logger = setup_logger(__name__)


class ClaudeOCR:
    """Handle OCR processing using Claude via AWS Bedrock."""
    
    def __init__(self, aws_region: str = AWS_REGION):
        """
        Initialize Claude OCR client using AWS Bedrock.
        
        Args:
            aws_region: AWS region for Bedrock service
        """
        self.bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=aws_region
        )
        self.model_id = CLAUDE_MODEL
        
        # Log available Claude models in Bedrock
        logger.info(f"Using Claude model: {self.model_id} in region: {aws_region}")
    
    def process_image(self, image_path: Path, page_number: int) -> Optional[Page]:
        """
        Process a single image using Claude for OCR.
        
        Args:
            image_path: Path to the image file
            page_number: Page number in the document
            
        Returns:
            Page object with extracted components
        """
        logger.info(f"Processing page {page_number} with Claude OCR via Bedrock")
        
        # Read and encode image
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Encode to base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Prepare the prompt
            prompt = self._create_ocr_prompt(page_number)
            
            # Make API call with retries
            for attempt in range(MAX_RETRIES):
                try:
                    response = self._call_bedrock_claude(base64_image, prompt, image_path.suffix[1:])
                    
                    # Parse response
                    page_data = self._parse_claude_response(response, page_number)
                    
                    if page_data:
                        logger.info(f"Successfully processed page {page_number} with {len(page_data.components)} components")
                        return page_data
                    
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    if error_code == 'ThrottlingException':
                        logger.warning(f"Rate limited on attempt {attempt + 1}, retrying...")
                        time.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff
                    else:
                        logger.error(f"AWS Bedrock error: {str(e)}")
                        raise
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY)
                    else:
                        logger.error(f"Failed to process page {page_number} after {MAX_RETRIES} attempts")
                        raise
            
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {str(e)}")
            return None
    
    def _create_ocr_prompt(self, page_number: int) -> str:
        """
        Create the prompt for Claude OCR.
        
        Args:
            page_number: Current page number
            
        Returns:
            Formatted prompt string
        """
        return f"""You are an expert OCR system analyzing page {page_number} of a procurement document. 
        Extract ALL text and structured content from this image and return it in a specific JSON format.

        Identify and extract:
        1. All text blocks (headers, paragraphs, lists, etc.)
        2. Tables with their structure preserved
        3. Any form fields or structured data
        4. Headers and footers

        For each component found, provide:
        - component_id: String in format "{page_number}_{{index}}" (e.g., "{page_number}_0", "{page_number}_1")
        - type: One of ["text", "table", "header", "footer"]
        - content: The extracted text content. For tables, use markdown table format.
        - confidence: Float between 0 and 1 indicating extraction confidence
        - bbox: Approximate bounding box [x1, y1, x2, y2] in pixels (estimate based on position)

        Return ONLY a valid JSON object with this structure:
        {{
            "components": [
                {{
                    "component_id": "{page_number}_0",
                    "type": "text",
                    "content": "Extracted text here",
                    "confidence": 0.95,
                    "bbox": [100, 100, 800, 200]
                }}
            ]
        }}

        Be thorough and extract ALL visible text. For tables, preserve the structure using markdown format.
        """
    
    def _call_bedrock_claude(self, base64_image: str, prompt: str, image_format: str) -> str:
        """
        Make the actual API call to Claude via AWS Bedrock.
        
        Args:
            base64_image: Base64 encoded image
            prompt: OCR prompt
            image_format: Image format (png, jpeg, etc.)
            
        Returns:
            Claude's response text
        """
        # Prepare the request body for Bedrock
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "temperature": 0.5,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": f"image/{image_format}",
                                "data": base64_image
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        
        # Convert to JSON string
        body = json.dumps(request_body)
        
        # Make the API call
        try:
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=body
            )
            
            # Parse the response
            response_body = json.loads(response['body'].read())
            
            # Extract the text from Claude's response
            if 'content' in response_body and len(response_body['content']) > 0:
                return response_body['content'][0]['text']
            else:
                raise ValueError("No content in response")
                
        except ClientError as e:
            logger.error(f"Bedrock API error: {e}")
            raise
    
    def _parse_claude_response(self, response: str, page_number: int) -> Optional[Page]:
        """
        Parse Claude's response into a Page object.
        
        Args:
            response: Raw response from Claude
            page_number: Page number
            
        Returns:
            Page object or None if parsing fails
        """
        try:
            # Extract JSON from response
            # Claude might add explanatory text, so we need to find the JSON
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response[json_start:json_end]
            data = json.loads(json_str)
            
            # Create Component objects
            components = []
            for comp_data in data.get('components', []):
                try:
                    component = Component(
                        component_id=comp_data['component_id'],
                        type=comp_data['type'],
                        content=comp_data['content'],
                        confidence=comp_data.get('confidence', 0.9),
                        bbox=comp_data.get('bbox', [0, 0, 0, 0])
                    )
                    components.append(component)
                except Exception as e:
                    logger.warning(f"Failed to parse component: {str(e)}")
            
            # Create Page object
            page = Page(
                page_number=page_number,
                component_count=len(components),
                components=components
            )
            
            return page
            
        except Exception as e:
            logger.error(f"Error parsing Claude response: {str(e)}")
            logger.debug(f"Response was: {response[:500]}...")  # Log first 500 chars
            return None


def create_ocr_client(aws_region: str = AWS_REGION) -> ClaudeOCR:
    """
    Factory function to create a Claude OCR client using AWS Bedrock.
    
    Args:
        aws_region: AWS region for Bedrock service
        
    Returns:
        Configured ClaudeOCR instance
    """
    return ClaudeOCR(aws_region)
