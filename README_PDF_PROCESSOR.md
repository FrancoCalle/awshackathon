# PDF OCR Processing Pipeline with AWS Bedrock

A comprehensive Python pipeline for processing PDF documents and performing OCR using Claude via AWS Bedrock.

## Overview

This pipeline:
1. Takes PDF files from the `procurement_docs` folder
2. Converts each page to a high-resolution image
3. Sends images to Claude (Opus or Sonnet) via AWS Bedrock for OCR processing
4. Extracts structured content (text, tables, headers, etc.)
5. Saves the results as JSON files with the same name as the source PDF

## Prerequisites

### 1. AWS Account Setup
- An AWS account with access to Amazon Bedrock
- Bedrock model access enabled for Claude models

### 2. Enable Claude Models in Bedrock
1. Go to the AWS Bedrock console
2. Navigate to "Model access"
3. Request access to the following models:
   - Claude 3 Opus (`anthropic.claude-3-opus-20240229`)
   - Claude 3 Sonnet (`anthropic.claude-3-sonnet-20240229`)
   - Claude 3.5 Sonnet (`anthropic.claude-3-5-sonnet-20241022`)

### 3. AWS Credentials
Configure your AWS credentials using one of these methods:

```bash
# Method 1: AWS CLI
aws configure

# Method 2: Environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1

# Method 3: IAM roles (if running on EC2/Lambda)
# Automatically configured
```

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
# Copy and edit the .env file
cp .env.example .env
# Edit .env to set your preferred AWS region and Claude model
```

## Usage

### Process all PDFs in the procurement_docs folder:
```bash
python pdf_processor/main.py
```

### Process a single PDF:
```bash
python pdf_processor/main.py --file path/to/your.pdf
```

### Process with custom settings:
```bash
# Use a specific AWS region
python pdf_processor/main.py --region us-west-2

# Use a specific AWS profile
python pdf_processor/main.py --profile my-profile

# Use a specific Claude model
python pdf_processor/main.py --model anthropic.claude-3-sonnet-20240229

# Limit processing
python pdf_processor/main.py --limit 10 --pattern "ADP-*.pdf"
```

### Command Line Options:
- `--region`: AWS region for Bedrock (default: us-east-1)
- `--profile`: AWS profile to use (optional)
- `--model`: Claude model to use (opus, sonnet, or sonnet-3.5)
- `--input-dir`: Directory containing PDF files (default: procurement_docs)
- `--output-dir`: Directory to save JSON files (default: processed_json)
- `--file`: Process a single PDF file
- `--pattern`: File pattern to match (default: *.pdf)
- `--limit`: Limit number of files to process

## Available Claude Models in Bedrock

1. **Claude 3 Opus** (`anthropic.claude-3-opus-20240229`)
   - Most capable model
   - Best for complex document understanding
   - Higher cost per request

2. **Claude 3 Sonnet** (`anthropic.claude-3-sonnet-20240229`)
   - Balanced performance and cost
   - Good for most OCR tasks

3. **Claude 3.5 Sonnet** (`anthropic.claude-3-5-sonnet-20241022`)
   - Latest Sonnet version
   - Improved performance over Claude 3 Sonnet

## Project Structure

```
pdf_processor/
├── __init__.py          # Package initialization
├── config.py            # Configuration settings
├── models.py            # Data models (Pydantic)
├── utils.py             # Utility functions
├── pdf_converter.py     # PDF to image conversion
├── claude_ocr.py        # Claude/Bedrock API integration
├── pipeline.py          # Main processing pipeline
└── main.py             # CLI entry point
```

## Output Format

Each PDF is processed into a JSON file with the following structure:

```json
{
  "job_id": "unique_id",
  "filename": "document.pdf",
  "compilation_time": "2025-06-13T12:00:00",
  "total_pages": 2,
  "total_components": 8,
  "expected_components": 16,
  "completeness": 0.5,
  "component_statistics": {
    "text": 7,
    "table": 1,
    "image": 0,
    "header": 0,
    "footer": 0
  },
  "average_confidence": 0.95,
  "pages": [
    {
      "page_number": 1,
      "component_count": 6,
      "components": [
        {
          "component_id": "1_0",
          "type": "text",
          "content": "Extracted text content",
          "confidence": 0.98,
          "bbox": [100, 100, 800, 200]
        }
      ]
    }
  ]
}
```

## Features

- **AWS Bedrock Integration**: Uses AWS Bedrock for secure, scalable access to Claude
- **Multiple Model Support**: Choose between Opus and Sonnet models based on your needs
- **Automatic Credential Handling**: Works with AWS CLI, environment variables, or IAM roles
- **Error Handling**: Comprehensive error handling with retry logic for rate limits
- **Progress Tracking**: Shows progress when processing multiple files
- **Temporary File Cleanup**: Automatically removes temporary images after processing

## Cost Considerations

AWS Bedrock charges based on:
- Number of input tokens (image size affects this)
- Number of output tokens
- Model used (Opus is more expensive than Sonnet)

To minimize costs:
- Use Sonnet models for simpler documents
- Process documents in batches during off-peak hours
- Monitor your AWS billing dashboard

## Troubleshooting

1. **AWS Credentials Issues**:
   ```bash
   aws sts get-caller-identity  # Verify credentials are working
   ```

2. **Bedrock Access Issues**:
   - Ensure your AWS account has Bedrock access enabled
   - Check that you've requested access to Claude models
   - Verify your IAM user/role has the necessary Bedrock permissions

3. **Model Not Found**:
   - Make sure you're using the correct model ID
   - Verify the model is available in your selected region

4. **Rate Limiting**:
   - The pipeline includes automatic retry with exponential backoff
   - Consider adding delays between requests for large batches

## Required IAM Permissions

Your AWS IAM user/role needs these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:ListFoundationModels"
      ],
      "Resource": "*"
    }
  ]
}
```

## License

This project is part of the AWS Hackathon submission.
