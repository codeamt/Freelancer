"""
Pydantic Models for HuggingFace Client

Type-safe data models for AI/ML operations.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Union
from enum import Enum


class ModelType(str, Enum):
    """HuggingFace model types"""
    TEXT_GENERATION = "text-generation"
    TEXT_CLASSIFICATION = "text-classification"
    QUESTION_ANSWERING = "question-answering"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    IMAGE_GENERATION = "text-to-image"
    IMAGE_CLASSIFICATION = "image-classification"
    EMBEDDINGS = "feature-extraction"


class TextGenerationRequest(BaseModel):
    """Request model for text generation"""
    prompt: str = Field(..., min_length=1, max_length=10000)
    model: Optional[str] = None
    max_length: int = Field(default=100, ge=1, le=2048)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    num_return_sequences: int = Field(default=1, ge=1, le=10)


class TextGenerationResponse(BaseModel):
    """Response model for text generation"""
    generated_text: Union[str, List[str]]
    model: str
    prompt_length: int
    generated_length: int


class TextClassificationRequest(BaseModel):
    """Request model for text classification"""
    text: str = Field(..., min_length=1, max_length=10000)
    model: Optional[str] = None
    labels: Optional[List[str]] = None  # For zero-shot classification


class ClassificationResult(BaseModel):
    """Single classification result"""
    label: str
    score: float = Field(..., ge=0.0, le=1.0)


class TextClassificationResponse(BaseModel):
    """Response model for text classification"""
    results: List[ClassificationResult]
    model: str


class SentimentAnalysisRequest(BaseModel):
    """Request model for sentiment analysis"""
    text: str = Field(..., min_length=1, max_length=10000)
    model: Optional[str] = None


class SentimentAnalysisResponse(BaseModel):
    """Response model for sentiment analysis"""
    label: str  # e.g., "POSITIVE", "NEGATIVE", "NEUTRAL"
    score: float = Field(..., ge=0.0, le=1.0)
    model: str


class QuestionAnsweringRequest(BaseModel):
    """Request model for question answering"""
    question: str = Field(..., min_length=1, max_length=1000)
    context: str = Field(..., min_length=1, max_length=10000)
    model: Optional[str] = None


class QuestionAnsweringResponse(BaseModel):
    """Response model for question answering"""
    answer: str
    score: float = Field(..., ge=0.0, le=1.0)
    start: int
    end: int
    model: str


class SummarizationRequest(BaseModel):
    """Request model for text summarization"""
    text: str = Field(..., min_length=50, max_length=50000)
    model: Optional[str] = None
    max_length: int = Field(default=130, ge=10, le=500)
    min_length: int = Field(default=30, ge=5, le=100)
    
    @validator('min_length')
    def validate_min_max(cls, v, values):
        """Ensure min_length < max_length"""
        if 'max_length' in values and v >= values['max_length']:
            raise ValueError('min_length must be less than max_length')
        return v


class SummarizationResponse(BaseModel):
    """Response model for summarization"""
    summary: str
    original_length: int
    summary_length: int
    model: str


class ImageGenerationRequest(BaseModel):
    """Request model for image generation"""
    prompt: str = Field(..., min_length=1, max_length=1000)
    model: Optional[str] = None
    negative_prompt: Optional[str] = Field(None, max_length=1000)
    num_inference_steps: int = Field(default=50, ge=1, le=150)
    width: int = Field(default=512, ge=128, le=1024)
    height: int = Field(default=512, ge=128, le=1024)


class ImageGenerationResponse(BaseModel):
    """Response model for image generation"""
    image_data: bytes
    format: str = "png"
    width: int
    height: int
    model: str


class ImageClassificationRequest(BaseModel):
    """Request model for image classification"""
    image_path: str
    model: Optional[str] = None


class ImageClassificationResponse(BaseModel):
    """Response model for image classification"""
    results: List[ClassificationResult]
    model: str


class EmbeddingsRequest(BaseModel):
    """Request model for embeddings generation"""
    text: Union[str, List[str]]
    model: Optional[str] = None


class EmbeddingsResponse(BaseModel):
    """Response model for embeddings"""
    embeddings: Union[List[float], List[List[float]]]
    model: str
    dimension: int


class TranslationRequest(BaseModel):
    """Request model for translation"""
    text: str = Field(..., min_length=1, max_length=10000)
    source_lang: str = Field(default="en", min_length=2, max_length=5)
    target_lang: str = Field(default="fr", min_length=2, max_length=5)
    model: Optional[str] = None
    
    @validator('source_lang', 'target_lang')
    def validate_lang_code(cls, v):
        """Validate language code format"""
        if not v.islower():
            raise ValueError('Language code must be lowercase')
        return v


class TranslationResponse(BaseModel):
    """Response model for translation"""
    translated_text: str
    source_lang: str
    target_lang: str
    model: str


class APIError(BaseModel):
    """API error response"""
    error: str
    status_code: int
    details: Optional[str] = None
