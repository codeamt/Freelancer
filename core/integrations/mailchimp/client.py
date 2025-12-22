"""
Mailchimp API Client Integration

This module provides a client for interacting with the Mailchimp API
for email marketing campaigns, audience management, and automation.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import httpx
from core.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class MailchimpConfig:
    """Mailchimp configuration"""
    api_key: str
    server_prefix: str  # e.g., 'us1', 'us2', etc.
    timeout: int = 30


@dataclass
class Contact:
    """Mailchimp contact/contact member"""
    email_address: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    tags: Optional[List[str]] = None


@dataclass
class Campaign:
    """Mailchimp campaign"""
    id: str
    title: str
    subject_line: str
    preview_text: str
    status: str
    emails_sent: int
    send_time: Optional[str] = None


@dataclass
class Audience:
    """Mailchimp audience/list"""
    id: str
    name: str
    member_count: int
    unsubscribe_count: int
    cleaned_count: int


class MailchimpClient:
    """Mailchimp API client"""
    
    def __init__(self, config: MailchimpConfig):
        self.config = config
        self.base_url = f"https://{config.server_prefix}.api.mailchimp.com/3.0"
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make HTTP request to Mailchimp API"""
        url = f"{self.base_url}/{endpoint}"
        
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=self.headers, params=data)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=self.headers, json=data)
                elif method.upper() == "PUT":
                    response = await client.put(url, headers=self.headers, json=data)
                elif method.upper() == "PATCH":
                    response = await client.patch(url, headers=self.headers, json=data)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=self.headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Mailchimp API error: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Mailchimp client error: {str(e)}")
                raise
    
    # Audience Management
    async def get_audiences(self) -> List[Audience]:
        """Get all audiences/lists"""
        try:
            response = await self._make_request("GET", "lists")
            audiences = []
            for list_data in response.get("lists", []):
                audience = Audience(
                    id=list_data["id"],
                    name=list_data["name"],
                    member_count=list_data["stats"]["member_count"],
                    unsubscribe_count=list_data["stats"]["unsubscribe_count"],
                    cleaned_count=list_data["stats"]["cleaned_count"]
                )
                audiences.append(audience)
            return audiences
        except Exception as e:
            logger.error(f"Failed to get audiences: {str(e)}")
            raise
    
    async def get_audience(self, audience_id: str) -> Optional[Audience]:
        """Get specific audience by ID"""
        try:
            response = await self._make_request("GET", f"lists/{audience_id}")
            list_data = response
            return Audience(
                id=list_data["id"],
                name=list_data["name"],
                member_count=list_data["stats"]["member_count"],
                unsubscribe_count=list_data["stats"]["unsubscribe_count"],
                cleaned_count=list_data["stats"]["cleaned_count"]
            )
        except Exception as e:
            logger.error(f"Failed to get audience {audience_id}: {str(e)}")
            return None
    
    # Contact Management
    async def add_contact(self, audience_id: str, contact: Contact) -> Dict:
        """Add contact to audience"""
        try:
            member_data = {
                "email_address": contact.email_address,
                "status": "subscribed"
            }
            
            if contact.first_name or contact.last_name:
                member_data["merge_fields"] = {}
                if contact.first_name:
                    member_data["merge_fields"]["FNAME"] = contact.first_name
                if contact.last_name:
                    member_data["merge_fields"]["LNAME"] = contact.last_name
            
            if contact.phone:
                member_data["merge_fields"]["PHONE"] = contact.phone
            
            if contact.tags:
                member_data["tags"] = contact.tags
            
            response = await self._make_request("POST", f"lists/{audience_id}/members", member_data)
            return response
            
        except Exception as e:
            logger.error(f"Failed to add contact {contact.email_address}: {str(e)}")
            raise
    
    async def remove_contact(self, audience_id: str, email_address: str) -> bool:
        """Remove contact from audience"""
        try:
            # Get subscriber hash (MD5 of lowercase email)
            import hashlib
            subscriber_hash = hashlib.md5(email_address.lower().encode()).hexdigest()
            
            await self._make_request("DELETE", f"lists/{audience_id}/members/{subscriber_hash}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove contact {email_address}: {str(e)}")
            return False
    
    async def update_contact(self, audience_id: str, email_address: str, updates: Dict) -> Dict:
        """Update contact information"""
        try:
            import hashlib
            subscriber_hash = hashlib.md5(email_address.lower().encode()).hexdigest()
            
            response = await self._make_request("PATCH", f"lists/{audience_id}/members/{subscriber_hash}", updates)
            return response
            
        except Exception as e:
            logger.error(f"Failed to update contact {email_address}: {str(e)}")
            raise
    
    # Campaign Management
    async def get_campaigns(self, status: Optional[str] = None) -> List[Campaign]:
        """Get campaigns, optionally filtered by status"""
        try:
            params = {}
            if status:
                params["status"] = status
            
            response = await self._make_request("GET", "campaigns", params)
            campaigns = []
            for campaign_data in response.get("campaigns", []):
                campaign = Campaign(
                    id=campaign_data["id"],
                    title=campaign_data["settings"]["title"],
                    subject_line=campaign_data["settings"]["subject_line"],
                    preview_text=campaign_data["settings"]["preview_text"],
                    status=campaign_data["status"],
                    emails_sent=campaign_data["emails_sent"],
                    send_time=campaign_data.get("send_time")
                )
                campaigns.append(campaign)
            return campaigns
        except Exception as e:
            logger.error(f"Failed to get campaigns: {str(e)}")
            raise
    
    async def create_campaign(self, campaign_data: Dict) -> Campaign:
        """Create new campaign"""
        try:
            response = await self._make_request("POST", "campaigns", campaign_data)
            return Campaign(
                id=response["id"],
                title=response["settings"]["title"],
                subject_line=response["settings"]["subject_line"],
                preview_text=response["settings"]["preview_text"],
                status=response["status"],
                emails_sent=response["emails_sent"],
                send_time=response.get("send_time")
            )
        except Exception as e:
            logger.error(f"Failed to create campaign: {str(e)}")
            raise
    
    async def send_campaign(self, campaign_id: str) -> Dict:
        """Send campaign immediately"""
        try:
            response = await self._make_request("POST", f"campaigns/{campaign_id}/actions/send")
            return response
        except Exception as e:
            logger.error(f"Failed to send campaign {campaign_id}: {str(e)}")
            raise
    
    # Template Management
    async def get_templates(self) -> List[Dict]:
        """Get all templates"""
        try:
            response = await self._make_request("GET", "templates")
            return response.get("templates", [])
        except Exception as e:
            logger.error(f"Failed to get templates: {str(e)}")
            raise
    
    # Reports and Analytics
    async def get_campaign_report(self, campaign_id: str) -> Dict:
        """Get campaign report/analytics"""
        try:
            response = await self._make_request("GET", f"reports/{campaign_id}")
            return response
        except Exception as e:
            logger.error(f"Failed to get campaign report {campaign_id}: {str(e)}")
            raise
    
    async def get_audience_growth(self, audience_id: str) -> Dict:
        """Get audience growth history"""
        try:
            response = await self._make_request("GET", f"lists/{audience_id}/growth-history")
            return response.get("history", [])
        except Exception as e:
            logger.error(f"Failed to get audience growth {audience_id}: {str(e)}")
            raise
    
    # Automation
    async def get_automations(self) -> List[Dict]:
        """Get all automation workflows"""
        try:
            response = await self._make_request("GET", "automations")
            return response.get("automations", [])
        except Exception as e:
            logger.error(f"Failed to get automations: {str(e)}")
            raise
    
    # Health Check
    async def ping(self) -> bool:
        """Test API connection"""
        try:
            await self._make_request("GET", "ping")
            return True
        except Exception as e:
            logger.error(f"Mailchimp API ping failed: {str(e)}")
            return False
