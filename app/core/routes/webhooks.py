from fastapi import APIRouter

router_webhooks = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Add webhook routes here as needed