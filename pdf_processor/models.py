"""
Data models for the PDF processing pipeline.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator


class Component(BaseModel):
    """Model for a single component on a page."""
    component_id: str
    type: str
    content: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: List[int] = Field(min_items=4, max_items=4)  # [x1, y1, x2, y2]
    
    @validator('type')
    def validate_type(cls, v):
        allowed_types = ['text', 'table', 'image', 'header', 'footer']
        if v not in allowed_types:
            raise ValueError(f'Component type must be one of {allowed_types}')
        return v


class Page(BaseModel):
    """Model for a single page in the document."""
    page_number: int = Field(ge=1)
    component_count: int = Field(ge=0)
    components: List[Component]
    
    @validator('component_count')
    def validate_component_count(cls, v, values):
        if 'components' in values and v != len(values['components']):
            raise ValueError('component_count must match the number of components')
        return v


class ComponentStatistics(BaseModel):
    """Statistics about component types in the document."""
    text: int = 0
    table: int = 0
    image: int = 0
    header: int = 0
    footer: int = 0


class ProcessedDocument(BaseModel):
    """Model for the complete processed document."""
    job_id: str
    filename: str
    compilation_time: datetime
    total_pages: int = Field(ge=1)
    total_components: int = Field(ge=0)
    expected_components: int = Field(ge=0)
    completeness: float = Field(ge=0.0, le=1.0)
    component_statistics: ComponentStatistics
    average_confidence: float = Field(ge=0.0, le=1.0)
    pages: List[Page]
    
    @validator('total_pages')
    def validate_total_pages(cls, v, values):
        if 'pages' in values and v != len(values['pages']):
            raise ValueError('total_pages must match the number of pages')
        return v
    
    @validator('total_components')
    def validate_total_components(cls, v, values):
        if 'pages' in values:
            actual_total = sum(page.component_count for page in values['pages'])
            if v != actual_total:
                raise ValueError('total_components must match the sum of components across all pages')
        return v
    
    @validator('completeness')
    def calculate_completeness(cls, v, values):
        if 'total_components' in values and 'expected_components' in values:
            if values['expected_components'] > 0:
                return values['total_components'] / values['expected_components']
        return 1.0
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
