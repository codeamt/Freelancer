"""
AI Service - Base class for HuggingFace and AI model interactions

Provides foundational AI functionality that can be extended by add-ons
for specific use cases (chatbots, content generation, image analysis, etc.)
"""

from typing import Optional, Dict, Any, List, Union
from core.utils.logger import get_logger
import os

logger = get_logger(__name__)


class AIService:
    """
    Base AI service for HuggingFace model interactions
    
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
        ai_service = AIService(api_key="your-hf-token")
        response = await ai_service.generate_text("Write a story about...")
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
        
        logger.info(f"AIService initialized with model: {default_model}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API request headers"""
        if not self.api_key:
            logger.warning("No HuggingFace API key configured")
            return {}
        
        return {"Authorization": f"Bearer {self.api_key}"}
    
    async def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_length: int = 100,
        temperature: float = 0.7,
        top_p: float = 0.9,
        num_return_sequences: int = 1
    ) -> Optional[Union[str, List[str]]]:
        """
        Generate text using a language model
        
        Args:
            prompt: Input text prompt
            model: Model to use (default: self.default_model)
            max_length: Maximum length of generated text
            temperature: Sampling temperature (0.0-1.0)
            top_p: Nucleus sampling parameter
            num_return_sequences: Number of sequences to generate
            
        Returns:
            Generated text or list of texts
        """
        try:
            import requests
            
            model = model or self.default_model
            url = f"{self.base_url}/{model}"
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_length": max_length,
                    "temperature": temperature,
                    "top_p": top_p,
                    "num_return_sequences": num_return_sequences
                }
            }
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if num_return_sequences == 1:
                    generated = result[0]["generated_text"]
                    logger.info(f"Text generated successfully ({len(generated)} chars)")
                    return generated
                else:
                    generated = [r["generated_text"] for r in result]
                    logger.info(f"Generated {len(generated)} text sequences")
                    return generated
            else:
                logger.error(f"Text generation failed: {response.status_code} - {response.text}")
                return None
                
        except ImportError:
            logger.error("requests library not installed. Install with: pip install requests")
            return None
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return None
    
    async def classify_text(
        self,
        text: str,
        model: str = "distilbert-base-uncased-finetuned-sst-2-english",
        labels: Optional[List[str]] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Classify text into categories
        
        Args:
            text: Text to classify
            model: Classification model
            labels: Optional custom labels for zero-shot classification
            
        Returns:
            List of classification results with labels and scores
        """
        try:
            import requests
            
            url = f"{self.base_url}/{model}"
            
            if labels:
                # Zero-shot classification
                payload = {
                    "inputs": text,
                    "parameters": {"candidate_labels": labels}
                }
            else:
                # Standard classification
                payload = {"inputs": text}
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Text classified successfully")
                return result
            else:
                logger.error(f"Classification failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error classifying text: {e}")
            return None
    
    async def analyze_sentiment(
        self,
        text: str,
        model: str = "distilbert-base-uncased-finetuned-sst-2-english"
    ) -> Optional[Dict[str, Any]]:
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
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return None
    
    async def answer_question(
        self,
        question: str,
        context: str,
        model: str = "distilbert-base-cased-distilled-squad"
    ) -> Optional[Dict[str, Any]]:
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
            import requests
            
            url = f"{self.base_url}/{model}"
            
            payload = {
                "inputs": {
                    "question": question,
                    "context": context
                }
            }
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Question answered: {result.get('answer', 'N/A')}")
                return result
            else:
                logger.error(f"QA failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return None
    
    async def summarize_text(
        self,
        text: str,
        model: str = "facebook/bart-large-cnn",
        max_length: int = 130,
        min_length: int = 30
    ) -> Optional[str]:
        """
        Summarize text
        
        Args:
            text: Text to summarize
            model: Summarization model
            max_length: Maximum summary length
            min_length: Minimum summary length
            
        Returns:
            Summary text
        """
        try:
            import requests
            
            url = f"{self.base_url}/{model}"
            
            payload = {
                "inputs": text,
                "parameters": {
                    "max_length": max_length,
                    "min_length": min_length
                }
            }
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                summary = result[0]["summary_text"]
                logger.info(f"Text summarized ({len(summary)} chars)")
                return summary
            else:
                logger.error(f"Summarization failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error summarizing text: {e}")
            return None
    
    async def generate_image(
        self,
        prompt: str,
        model: str = "stabilityai/stable-diffusion-2-1",
        negative_prompt: Optional[str] = None,
        num_inference_steps: int = 50
    ) -> Optional[bytes]:
        """
        Generate image from text prompt
        
        Args:
            prompt: Text description of image
            model: Image generation model
            negative_prompt: What to avoid in image
            num_inference_steps: Number of denoising steps
            
        Returns:
            Image bytes or None
        """
        try:
            import requests
            
            url = f"{self.base_url}/{model}"
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "num_inference_steps": num_inference_steps
                }
            }
            
            if negative_prompt:
                payload["parameters"]["negative_prompt"] = negative_prompt
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                logger.info(f"Image generated successfully")
                return response.content
            else:
                logger.error(f"Image generation failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return None
    
    async def classify_image(
        self,
        image_path: str,
        model: str = "google/vit-base-patch16-224"
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Classify image content
        
        Args:
            image_path: Path to image file
            model: Image classification model
            
        Returns:
            List of classification results
        """
        try:
            import requests
            
            url = f"{self.base_url}/{model}"
            
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                data=image_data,
                timeout=30
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
            import requests
            
            url = f"{self.base_url}/{model}"
            
            payload = {"inputs": text}
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
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
            import requests
            
            if not model:
                model = f"Helsinki-NLP/opus-mt-{source_lang}-{target_lang}"
            
            url = f"{self.base_url}/{model}"
            
            payload = {"inputs": text}
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
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
