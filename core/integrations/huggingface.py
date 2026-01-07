"""
Hugging Face Integration

Flattened module containing Hugging Face API client and models for AI/ML services.
"""

import os
import httpx
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
from core.utils.logger import get_logger

logger = get_logger(__name__)


# ===== MODELS =====

@dataclass
class HuggingFaceConfig:
    """Hugging Face API configuration"""
    api_key: str
    base_url: str = "https://api-inference.huggingface.co"
    timeout: int = 30


@dataclass
class ModelInfo:
    """Hugging Face model information"""
    id: str
    task: str
    pipeline_tag: Optional[str] = None
    tags: Optional[List[str]] = None
    downloads: int = 0
    likes: int = 0
    model_type: Optional[str] = None
    library_name: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelInfo':
        """Create from API response"""
        return cls(
            id=data["id"],
            task=data.get("task", ""),
            pipeline_tag=data.get("pipeline_tag"),
            tags=data.get("tags", []),
            downloads=data.get("downloads", 0),
            likes=data.get("likes", 0),
            model_type=data.get("model_type"),
            library_name=data.get("library_name")
        )


@dataclass
class TextGenerationRequest:
    """Text generation request"""
    inputs: str
    model: str
    parameters: Optional[Dict[str, Any]] = None
    options: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
        if self.options is None:
            self.options = {}


@dataclass
class TextGenerationResponse:
    """Text generation response"""
    generated_text: str
    model: str
    score: Optional[float] = None
    finish_reason: Optional[str] = None
    token_count: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], model: str) -> 'TextGenerationResponse':
        """Create from API response"""
        if isinstance(data, list) and data:
            data = data[0]
        
        generated_text = data.get("generated_text", "")
        score = data.get("score")
        finish_reason = data.get("finish_reason")
        
        # Estimate token count (rough approximation)
        token_count = len(generated_text.split()) if generated_text else 0
        
        return cls(
            generated_text=generated_text,
            model=model,
            score=score,
            finish_reason=finish_reason,
            token_count=token_count
        )


@dataclass
class ClassificationRequest:
    """Text classification request"""
    inputs: Union[str, List[str]]
    model: str
    parameters: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


@dataclass
class ClassificationResponse:
    """Text classification response"""
    label: str
    score: float
    model: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], model: str) -> 'ClassificationResponse':
        """Create from API response"""
        if isinstance(data, list) and data:
            data = data[0]
        
        return cls(
            label=data.get("label", ""),
            score=data.get("score", 0.0),
            model=model
        )


# ===== CLIENT =====

class HuggingFaceClient:
    """Hugging Face API client for AI/ML services"""
    
    def __init__(self, config: Optional[HuggingFaceConfig] = None):
        if config is None:
            config = HuggingFaceConfig(
                api_key=os.getenv("HUGGINGFACE_API_KEY", "")
            )
        
        self.config = config
        self.client = httpx.Client(
            base_url=config.base_url,
            headers={"Authorization": f"Bearer {config.api_key}"},
            timeout=config.timeout
        )
        
        if not config.api_key:
            logger.warning("Hugging Face API key not configured")
    
    def list_models(self, task: Optional[str] = None, limit: int = 100) -> List[ModelInfo]:
        """List available models"""
        try:
            params = {"limit": limit}
            if task:
                params["task"] = task
            
            response = self.client.get("/models", params=params)
            response.raise_for_status()
            
            data = response.json()
            models = [ModelInfo.from_dict(model_data) for model_data in data]
            
            logger.info(f"Retrieved {len(models)} models")
            return models
            
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            raise
    
    def get_model_info(self, model_id: str) -> ModelInfo:
        """Get information about a specific model"""
        try:
            response = self.client.get(f"/models/{model_id}")
            response.raise_for_status()
            
            data = response.json()
            model = ModelInfo.from_dict(data)
            
            logger.info(f"Retrieved model info: {model_id}")
            return model
            
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            raise
    
    def generate_text(self, request: TextGenerationRequest) -> TextGenerationResponse:
        """Generate text using a language model"""
        try:
            payload = {
                "inputs": request.inputs,
                "parameters": request.parameters,
                "options": request.options
            }
            
            response = self.client.post(f"/models/{request.model}", json=payload)
            response.raise_for_status()
            
            data = response.json()
            result = TextGenerationResponse.from_dict(data, request.model)
            
            logger.info(f"Generated text using model: {request.model}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate text: {e}")
            raise
    
    def classify_text(self, request: ClassificationRequest) -> List[ClassificationResponse]:
        """Classify text using a classification model"""
        try:
            payload = {
                "inputs": request.inputs,
                "parameters": request.parameters
            }
            
            response = self.client.post(f"/models/{request.model}", json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            # Handle both single and multiple inputs
            if isinstance(request.inputs, str):
                # Single input
                if isinstance(data, list) and data:
                    result = [ClassificationResponse.from_dict(data[0], request.model)]
                else:
                    result = [ClassificationResponse.from_dict(data, request.model)]
            else:
                # Multiple inputs
                result = []
                for item in data:
                    if isinstance(item, list) and item:
                        result.append(ClassificationResponse.from_dict(item[0], request.model))
                    else:
                        result.append(ClassificationResponse.from_dict(item, request.model))
            
            logger.info(f"Classified text using model: {request.model}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to classify text: {e}")
            raise
    
    def translate_text(self, model: str, inputs: Union[str, List[str]], **kwargs) -> List[str]:
        """Translate text using a translation model"""
        try:
            payload = {
                "inputs": inputs,
                "parameters": kwargs
            }
            
            response = self.client.post(f"/models/{model}", json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract translated text
            if isinstance(data, list):
                translations = []
                for item in data:
                    if isinstance(item, dict) and "translation_text" in item:
                        translations.append(item["translation_text"])
                    elif isinstance(item, str):
                        translations.append(item)
                return translations
            elif isinstance(data, dict) and "translation_text" in data:
                return [data["translation_text"]]
            else:
                return [str(data)]
            
        except Exception as e:
            logger.error(f"Failed to translate text: {e}")
            raise
    
    def summarize_text(self, model: str, inputs: Union[str, List[str]], **kwargs) -> List[str]:
        """Summarize text using a summarization model"""
        try:
            payload = {
                "inputs": inputs,
                "parameters": kwargs
            }
            
            response = self.client.post(f"/models/{model}", json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract summary text
            if isinstance(data, list):
                summaries = []
                for item in data:
                    if isinstance(item, dict) and "summary_text" in item:
                        summaries.append(item["summary_text"])
                    elif isinstance(item, str):
                        summaries.append(item)
                return summaries
            elif isinstance(data, dict) and "summary_text" in data:
                return [data["summary_text"]]
            else:
                return [str(data)]
            
        except Exception as e:
            logger.error(f"Failed to summarize text: {e}")
            raise
    
    def answer_question(self, model: str, question: str, context: Optional[str] = None, **kwargs) -> str:
        """Answer a question using a QA model"""
        try:
            payload = {"question": question}
            if context:
                payload["context"] = context
            payload.update(kwargs)
            
            response = self.client.post(f"/models/{model}", json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract answer
            if isinstance(data, list) and data:
                answer = data[0].get("answer", "")
            elif isinstance(data, dict):
                answer = data.get("answer", "")
            else:
                answer = str(data)
            
            logger.info(f"Answered question using model: {model}")
            return answer
            
        except Exception as e:
            logger.error(f"Failed to answer question: {e}")
            raise
    
    def close(self):
        """Close the HTTP client"""
        self.client.close()


# Factory function
def create_huggingface_client(config: Optional[HuggingFaceConfig] = None) -> HuggingFaceClient:
    """Create a Hugging Face client instance"""
    return HuggingFaceClient(config)


# Convenience functions
def generate_text(model: str, prompt: str, **kwargs) -> str:
    """Convenience function to generate text"""
    client = HuggingFaceClient()
    try:
        request = TextGenerationRequest(
            inputs=prompt,
            model=model,
            parameters=kwargs
        )
        response = client.generate_text(request)
        return response.generated_text
    finally:
        client.close()


def classify_text(model: str, text: Union[str, List[str]], **kwargs) -> List[ClassificationResponse]:
    """Convenience function to classify text"""
    client = HuggingFaceClient()
    try:
        request = ClassificationRequest(
            inputs=text,
            model=model,
            parameters=kwargs
        )
        return client.classify_text(request)
    finally:
        client.close()


def translate_text(model: str, text: Union[str, List[str]], **kwargs) -> List[str]:
    """Convenience function to translate text"""
    client = HuggingFaceClient()
    try:
        return client.translate_text(model, text, **kwargs)
    finally:
        client.close()


__all__ = [
    # Models
    'HuggingFaceConfig',
    'ModelInfo',
    'TextGenerationRequest',
    'TextGenerationResponse',
    'ClassificationRequest',
    'ClassificationResponse',
    
    # Client
    'HuggingFaceClient',
    'create_huggingface_client',
    
    # Convenience
    'generate_text',
    'classify_text',
    'translate_text',
]
