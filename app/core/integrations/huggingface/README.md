# AI Service Documentation

A base service class for HuggingFace AI model interactions that can be extended by add-ons for specific use cases.

## Features

- ✅ **Text Generation** - GPT-style language models
- ✅ **Text Classification** - Categorize and label text
- ✅ **Sentiment Analysis** - Detect positive/negative sentiment
- ✅ **Question Answering** - Extract answers from context
- ✅ **Text Summarization** - Generate concise summaries
- ✅ **Image Generation** - Stable Diffusion models
- ✅ **Image Classification** - Identify image content
- ✅ **Embeddings** - Generate vector representations
- ✅ **Translation** - Multi-language support

## Installation

### Required Dependencies

```bash
pip install requests
```

### Environment Variables

```bash
# .env
HUGGINGFACE_API_KEY=your-hf-token-here
```

Get your API key from: https://huggingface.co/settings/tokens

## Basic Usage

### 1. Initialize Service

```python
from core.services import AIService

# With environment variable
ai_service = AIService()

# Or with explicit API key
ai_service = AIService(
    api_key="your-hf-token",
    default_model="gpt2"
)
```

### 2. Text Generation

```python
# Generate text
response = await ai_service.generate_text(
    prompt="Once upon a time in a magical forest,",
    max_length=100,
    temperature=0.7
)
print(response)

# Generate multiple sequences
responses = await ai_service.generate_text(
    prompt="Write a tagline for a tech startup:",
    num_return_sequences=3,
    max_length=50
)
for i, text in enumerate(responses):
    print(f"{i+1}. {text}")
```

### 3. Sentiment Analysis

```python
# Analyze sentiment
sentiment = await ai_service.analyze_sentiment(
    "I absolutely love this product! It's amazing!"
)
print(f"Sentiment: {sentiment['label']} ({sentiment['score']:.2%})")
# Output: Sentiment: POSITIVE (99.87%)
```

### 4. Text Classification

```python
# Standard classification
result = await ai_service.classify_text(
    "This movie was terrible and boring."
)

# Zero-shot classification with custom labels
result = await ai_service.classify_text(
    "The new iPhone has an amazing camera",
    labels=["technology", "sports", "politics", "entertainment"]
)
```

### 5. Question Answering

```python
# Extract answer from context
answer = await ai_service.answer_question(
    question="What is the capital of France?",
    context="Paris is the capital and most populous city of France."
)
print(f"Answer: {answer['answer']} (confidence: {answer['score']:.2%})")
```

### 6. Text Summarization

```python
# Summarize long text
long_text = """
Your long article or document here...
"""

summary = await ai_service.summarize_text(
    text=long_text,
    max_length=130,
    min_length=30
)
print(f"Summary: {summary}")
```

## Advanced Features

### Image Generation

```python
# Generate image from text
image_bytes = await ai_service.generate_image(
    prompt="A serene mountain landscape at sunset, digital art",
    negative_prompt="blurry, low quality, distorted",
    num_inference_steps=50
)

# Save image
if image_bytes:
    with open("generated_image.png", "wb") as f:
        f.write(image_bytes)
```

### Image Classification

```python
# Classify image content
results = await ai_service.classify_image(
    image_path="/path/to/image.jpg"
)

for result in results[:5]:  # Top 5 predictions
    print(f"{result['label']}: {result['score']:.2%}")
```

### Text Embeddings

```python
# Generate embeddings for semantic search
embedding = await ai_service.get_embeddings(
    "Machine learning is transforming technology"
)
print(f"Embedding dimension: {len(embedding)}")

# Batch embeddings
embeddings = await ai_service.get_embeddings([
    "First sentence",
    "Second sentence",
    "Third sentence"
])
```

### Translation

```python
# Translate text
translated = await ai_service.translate_text(
    text="Hello, how are you?",
    source_lang="en",
    target_lang="fr"
)
print(f"Translation: {translated}")
# Output: Bonjour, comment allez-vous?
```

## Popular Models

### Text Generation
- `gpt2` - Small, fast GPT-2
- `gpt2-large` - Larger GPT-2 model
- `EleutherAI/gpt-neo-2.7B` - Open-source GPT-3 alternative
- `facebook/opt-1.3b` - Meta's OPT model

### Sentiment Analysis
- `distilbert-base-uncased-finetuned-sst-2-english` - Fast sentiment
- `cardiffnlp/twitter-roberta-base-sentiment` - Social media sentiment

### Question Answering
- `distilbert-base-cased-distilled-squad` - Fast QA
- `deepset/roberta-base-squad2` - More accurate QA

### Summarization
- `facebook/bart-large-cnn` - News summarization
- `t5-base` - General summarization

### Image Generation
- `stabilityai/stable-diffusion-2-1` - High quality images
- `runwayml/stable-diffusion-v1-5` - Faster generation

### Image Classification
- `google/vit-base-patch16-224` - Vision Transformer
- `microsoft/resnet-50` - ResNet classifier

## Extending for Add-Ons

### Example: Content Moderation Service

```python
from core.services import AIService

class ModerationService(AIService):
    """Extended service for content moderation"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.toxic_model = "unitary/toxic-bert"
    
    async def check_toxicity(self, text: str) -> Dict[str, float]:
        """Check if text contains toxic content"""
        result = await self.classify_text(
            text=text,
            model=self.toxic_model,
            labels=["toxic", "severe_toxic", "obscene", "threat", "insult"]
        )
        
        # Convert to dict of scores
        scores = {item['label']: item['score'] for item in result}
        return scores
    
    async def is_safe(self, text: str, threshold: float = 0.7) -> bool:
        """Check if text is safe to publish"""
        scores = await self.check_toxicity(text)
        return all(score < threshold for score in scores.values())
```

### Example: Chatbot Service

```python
class ChatbotService(AIService):
    """Extended service for conversational AI"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chat_model = "microsoft/DialoGPT-medium"
        self.conversation_history = []
    
    async def chat(self, message: str) -> str:
        """Have a conversation"""
        # Add user message to history
        self.conversation_history.append(message)
        
        # Generate response
        context = " ".join(self.conversation_history[-5:])  # Last 5 messages
        response = await self.generate_text(
            prompt=context,
            model=self.chat_model,
            max_length=100
        )
        
        # Add response to history
        self.conversation_history.append(response)
        
        return response
    
    def reset_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []
```

### Example: SEO Service

```python
class SEOService(AIService):
    """Extended service for SEO optimization"""
    
    async def generate_meta_description(self, content: str) -> str:
        """Generate SEO-friendly meta description"""
        summary = await self.summarize_text(
            text=content,
            max_length=160,
            min_length=120
        )
        return summary
    
    async def extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from content"""
        # Use zero-shot classification
        result = await self.classify_text(
            text=content,
            labels=["technology", "business", "health", "education", "entertainment"]
        )
        
        # Return top categories as keywords
        return [item['label'] for item in result[:3]]
    
    async def generate_alt_text(self, image_path: str) -> str:
        """Generate alt text for images"""
        results = await self.classify_image(image_path)
        
        if results:
            # Combine top predictions into alt text
            labels = [r['label'] for r in results[:3]]
            return f"Image showing {', '.join(labels)}"
        
        return "Image"
```

## Rate Limiting

HuggingFace Inference API has rate limits:

- **Free tier:** ~30 requests/hour
- **Pro tier:** Higher limits with paid subscription

Handle rate limits gracefully:

```python
import asyncio

async def generate_with_retry(ai_service, prompt, max_retries=3):
    for attempt in range(max_retries):
        result = await ai_service.generate_text(prompt)
        
        if result:
            return result
        
        # Wait before retry (exponential backoff)
        wait_time = 2 ** attempt
        await asyncio.sleep(wait_time)
    
    return None
```

## Error Handling

```python
try:
    result = await ai_service.generate_text(prompt)
    
    if result is None:
        print("Generation failed - check API key and rate limits")
    else:
        print(f"Result: {result}")
        
except Exception as e:
    logger.error(f"AI error: {e}")
```

## Best Practices

### 1. Model Selection
- ✅ Use smaller models for faster responses
- ✅ Use larger models for better quality
- ✅ Test different models for your use case
- ✅ Cache results when possible

### 2. Prompt Engineering
- ✅ Be specific and clear
- ✅ Provide examples when needed
- ✅ Use appropriate temperature settings
- ✅ Iterate and refine prompts

### 3. Cost Optimization
- ✅ Cache frequent queries
- ✅ Use batch processing
- ✅ Implement request throttling
- ✅ Monitor API usage

### 4. Quality Control
- ✅ Validate AI outputs
- ✅ Implement content filtering
- ✅ Add human review for critical content
- ✅ Track accuracy metrics

## Use Cases

### 1. Content Creation
- Blog post generation
- Product descriptions
- Social media posts
- Email templates

### 2. Customer Support
- Chatbots
- FAQ answering
- Ticket classification
- Sentiment analysis

### 3. E-Commerce
- Product recommendations
- Review analysis
- Image tagging
- Search optimization

### 4. Education
- Quiz generation
- Content summarization
- Language learning
- Automated grading

### 5. Marketing
- Ad copy generation
- A/B test variations
- Audience segmentation
- Trend analysis

## Testing

```python
# Test with simple prompts
ai_service = AIService(api_key="your-key")

# Test text generation
result = await ai_service.generate_text("Hello, AI!")
assert result is not None

# Test sentiment
sentiment = await ai_service.analyze_sentiment("I love this!")
assert sentiment['label'] == 'POSITIVE'
```

---

**Note:** This is a base class designed for extension. Add-ons should inherit from `AIService` and implement specific AI functionality for their use cases.
