# In-app + Email Notifications
from typing import Dict
from app.utils.email import EmailService
from app.services.event_bus import bus

class NotificationService:
    CHANNEL = "notify.*"

    @staticmethod
    async def send_email(to_email: str, subject: str, html: str):
        EmailService.send_email(to_email, subject, html)
        # also publish to event bus for real-time UIs
        await bus.publish("notify.email", {"to": to_email, "subject": subject})

    @staticmethod
    async def emit_inapp(user_id: str, message: str, meta: Dict | None = None):
        payload = {"user_id": user_id, "message": message, "meta": meta or {}}
        await bus.publish("notify.inapp", payload)

