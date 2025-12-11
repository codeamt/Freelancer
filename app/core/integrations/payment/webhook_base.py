from abc import ABC, abstractmethod
import stripe
  
class StripeWebhookHandler(ABC):
    def __init__(self, webhook_secret: str):
        self.webhook_secret = webhook_secret
      
    def verify_and_parse(self, payload: bytes, signature: str):
        """Generic webhook verification"""
        return stripe.Webhook.construct_event(
            payload, signature, self.webhook_secret
        )
      
    @abstractmethod
    async def handle_payment_succeeded(self, event):
        """Domain-specific logic"""
        pass
      
    @abstractmethod
    async def handle_payment_failed(self, event):
        """Domain-specific logic"""
        pass