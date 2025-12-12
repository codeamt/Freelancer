"""
AI Service - Base class for HuggingFace and AI model interactions

Provides foundational AI functionality that can be extended by add-ons
for specific use cases (chatbots, content generation, image analysis, etc.)
"""

from typing import Optional, Dict, Any, List, Union
from core.utils.logger import get_logger
from core.exceptions import AIServiceError
from core.integrations.huggingface.models import (
    TextGenerationRequest,
    TextGenerationResponse,
    TextClassificationRequest,
    TextClassificationResponse,
    SummarizationRequest,
    SummarizationResponse,
    QuestionAnsweringRequest,
    QuestionAnsweringResponse,
    SentimentAnalysisRequest,
    SentimentAnalysisResponse
)
import os
import httpx

logger = get_logger(__name__)


class HuggingFaceClient:
    """
    HuggingFace client for AI model interactions
    
    Features:
    - Text generation (GPT-style models)
    - Text classification
    - Sentiment analysis
    - Question answering
    - Text summarization
    - Image generation (Stable Diffusion)
    - Image classification
    - Embeddings generation
    
    Usage:
        # With context manager (recommended)
        async with HuggingFaceClient(api_key="your-hf-token") as client:
            response = await client.generate_text("Write a story about...")
        
        # Or manual cleanup
        client = HuggingFaceClient(api_key="your-hf-token")
        response = await client.generate_text("Write a story about...")
        await client.close()
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = "gpt2"
    ):
        """
        Initialize AI service
        
        Args:
            api_key: HuggingFace API token
            default_model: Default model to use
        """
        self.api_key = api_key or os.getenv("HUGGINGFACE_API_KEY")
        self.default_model = default_model
        self.base_url = "https://api-inference.huggingface.co/models"
        self._client = None
        
        logger.info(f"HuggingFaceClient initialized with model: {default_model}")
    
    def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=60.0)
        return self._client
    
    async def close(self):
        """Close the HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
        return False
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API request headers"""
        if not self.api_key:
            logger.warning("No HuggingFace API key configured")
            return {}
        
        return {"Authorization": f"Bearer {self.api_key}"}
    
    async def generate_text(
        self,
        request: TextGenerationRequest
    ) -> TextGenerationResponse:
        """
        Generate text using a language model
        
        Args:
            request: Text generation request with prompt and parameters
            
        Returns:
            TextGenerationResponse with generated text
        """
        try:
            model = request.model or self.default_model
            url = f"{self.base_url}/{model}"
            
            payload = {
                "inputs": request.prompt,
                "parameters": {
                    "max_length": request.max_length,
                    "temperature": request.temperature,
                    "top_p": request.top_p,
                    "num_return_sequences": request.num_return_sequences,
                    "return_full_text": False
                }
            }
            
            client = self._get_client()
            response = await client.post(
                url,
                headers=self._get_headers(),
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if request.num_return_sequences == 1:
                    generated = result[0]["generated_text"]
                    logger.info(f"Text generated successfully ({len(generated)} chars)")
                    return TextGenerationResponse(
                        generated_text=generated,
                        model=model,
                        prompt_length=len(request.prompt),
                        generated_length=len(generated)
                    )
                else:
                    generated = [r["generated_text"] for r in result]
                    logger.info(f"Generated {len(generated)} text sequences")
                    return TextGenerationResponse(
                        generated_text=generated,
                        model=model,
                        prompt_length=len(request.prompt),
                        generated_length=sum(len(g) for g in generated)
                    )
            else:
                logger.error(f"Text generation failed: {response.status_code}")
                raise AIServiceError(
                    f"Text generation failed with status {response.status_code}",
                    model=model
                )
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error generating text: {e}")
            raise AIServiceError(f"HTTP error: {str(e)}", model=model)
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise AIServiceError(str(e), model=model)
    
    async def classify_text(
        self,
        request: TextClassificationRequest
    ) -> TextClassificationResponse:
        """
        Classify text into categories
        
        Args:
            request: Text classification request with text and optional labels
            
        Returns:
            TextClassificationResponse with classification results
        """
        try:
            model = request.model or "distilbert-base-uncased-finetuned-sst-2-english"
            url = f"{self.base_url}/{model}"
            
            if request.labels:
                # Zero-shot classification
                payload = {
                    "inputs": request.text,
                    "parameters": {"candidate_labels": request.labels}
                }
            else:
                # Standard classification
                payload = {"inputs": text}
            
            client = self._get_client()
            response = await client.post(
                url,
                headers=self._get_headers(),
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Text classified successfully")
                
                # Convert to ClassificationResult models
                from core.integrations.huggingface.models import ClassificationResult
                results = [
                    ClassificationResult(label=r["label"], score=r["score"])
                    for r in result[0]
                ]
                
                return TextClassificationResponse(
                    results=results,
                    model=model
                )
            else:
                logger.error(f"Classification failed: {response.status_code}")
                raise AIServiceError(
                    f"Classification failed with status {response.status_code}",
                    model=model
                )
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error classifying text: {e}")
            raise AIServiceError(f"HTTP error: {str(e)}", model=model)
        except Exception as e:
            logger.error(f"Error classifying text: {e}")
            raise AIServiceError(str(e), model=model)
    
    async def analyze_sentiment(
        self,
        text: str,
        model: str = "distilbert-base-uncased-finetuned-sst-2-english"
    ) -> Dict[str, Any]:
        """
        Analyze sentiment of text
        
        Args:
            text: Text to analyze
            model: Sentiment analysis model
            
        Returns:
            Sentiment result with label and score
        """
        try:
            result = await self.classify_text(text, model)
            
            if result and len(result) > 0:
                sentiment = result[0][0]  # Top result
                logger.info(f"Sentiment: {sentiment['label']} ({sentiment['score']:.2f})")
                return sentiment
            
            raise AIServiceError("No sentiment results returned", model=model)
            
        except AIServiceError:
            raise
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            raise AIServiceError(f"Sentiment analysis failed: {str(e)}", model=model)
    
    async def answer_question(
        self,
        question: str,
        context: str,
        model: str = "distilbert-base-cased-distilled-squad"
    ) -> Dict[str, Any]:
        """
        Answer a question based on context
        
        Args:
            question: Question to answer
            context: Context containing the answer
            model: QA model
            
        Returns:
            Answer with score and span
        """
        try:
            url = f"{self.base_url}/{model}"
            
            payload = {
                "inputs": {
                    "question": question,
                    "context": context
                }
            }
            
            client = self._get_client()
            response = await client.post(
                url,
                headers=self._get_headers(),
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Question answered: {result.get('answer', 'N/A')}")
                return result
            else:
                logger.error(f"QA failed: {response.status_code}")
                raise AIServiceError(
                    f"Question answering failed with status {response.status_code}",
                    model=model
                )
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error answering question: {e}")
            raise AIServiceError(f"HTTP error: {str(e)}", model=model)
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            raise AIServiceError(str(e), model=model)
    
    async def summarize_text(
        self,
        request: SummarizationRequest
    ) -> SummarizationResponse:
        """
        Summarize text
        
        Args:
            request: Summarization request with text and parameters
            
        Returns:
            SummarizationResponse with summary
        """
        try:
            model = request.model or "facebook/bart-large-cnn"
            url = f"{self.base_url}/{model}"
            
            payload = {
                "inputs": request.text,
                "parameters": {
                    "max_length": request.max_length,
                    "min_length": request.min_length
                }
            }
            
            client = self._get_client()
            response = await client.post(
                url,
                headers=self._get_headers(),
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                summary = result[0]["summary_text"]
                logger.info(f"Text summarized ({len(summary)} chars)")
                return SummarizationResponse(
                    summary=summary,
                    original_length=len(request.text),
                    summary_length=len(summary),
                    model=model
                )
            else:
                logger.error(f"Summarization failed: {response.status_code}")
                raise AIServiceError(
                    f"Summarization failed with status {response.status_code}",
                    model=model
                )
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error summarizing text: {e}")
            raise AIServiceError(f"HTTP error: {str(e)}", model=model)
        except Exception as e:
            logger.error(f"Error summarizing text: {e}")
            raise AIServiceError(str(e), model=model)
    
    async def generate_image(
        self,
        prompt: str,
        model: str = "stabilityai/stable-diffusion-2-1",
        negative_prompt: Optional[str] = None,
        num_inference_steps: int = 50
    ) -> bytes:
        """
        Generate image from text prompt
        
        Args:
            prompt: Text description of image
            model: Image generation model
            negative_prompt: What to avoid in image
            num_inference_steps: Number of denoising steps
            
        Returns:
            Image bytes
        """
        try:
            url = f"{self.base_url}/{model}"
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "num_inference_steps": num_inference_steps
                }
            }
            
            if negative_prompt:
                payload["parameters"]["negative_prompt"] = negative_prompt
            
            client = self._get_client()
            response = await client.post(
                url,
                headers=self._get_headers(),
                json=payload
            )
            
            if response.status_code == 200:
                logger.info(f"Image generated successfully")
                return response.content
            else:
                logger.error(f"Image generation failed: {response.status_code}")
                raise AIServiceError(
                    f"Image generation failed with status {response.status_code}",
                    model=model
                )
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error generating image: {e}")
            raise AIServiceError(f"HTTP error: {str(e)}", model=model)
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            raise AIServiceError(str(e), model=model)
    
    async def classify_image(
        self,
        image_path: str,
        model: str = "google/vit-base-patch16-224"
    ) -> List[Dict[str, Any]]:
        """
        Classify image content
        
        Args:
            image_path: Path to image file
            model: Image classification model
            
        Returns:
            List of classification results
        """
        try:
            url = f"{self.base_url}/{model}"
            
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            client = self._get_client()
            response = await client.post(
                url,
                headers=self._get_headers(),
                content=image_data
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Image classified successfully")
                return result
            else:
                logger.error(f"Image classification failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error classifying image: {e}")
            return None
    
    async def get_embeddings(
        self,
        text: Union[str, List[str]],
        model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ) -> Optional[Union[List[float], List[List[float]]]]:
        """
        Generate text embeddings
        
        Args:
            text: Text or list of texts
            model: Embedding model
            
        Returns:
            Embedding vector(s)
        """
        try:
            url = f"{self.base_url}/{model}"
            
            payload = {"inputs": text}
            
            client = self._get_client()
            response = await client.post(
                url,
                headers=self._get_headers(),
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Embeddings generated successfully")
                return result
            else:
                logger.error(f"Embedding generation failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return None
    
    async def translate_text(
        self,
        text: str,
        source_lang: str = "en",
        target_lang: str = "fr",
        model: Optional[str] = None
    ) -> Optional[str]:
        """
        Translate text between languages
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            model: Translation model (auto-selected if None)
            
        Returns:
            Translated text
        """
        try:
            if not model:
                model = f"Helsinki-NLP/opus-mt-{source_lang}-{target_lang}"
            
            url = f"{self.base_url}/{model}"
            
            payload = {"inputs": text}
            
            client = self._get_client()
            response = await client.post(
                url,
                headers=self._get_headers(),
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                translated = result[0]["translation_text"]
                logger.info(f"Text translated ({source_lang} → {target_lang})")
                return translated
            else:
                logger.error(f"Translation failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error translating text: {e}")
            return None
