"""
Mailchimp Integration

Flattened module containing Mailchimp API client and models for email marketing campaigns,
audience management, and automation.
"""

import os
import httpx
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from core.utils.logger import get_logger

logger = get_logger(__name__)


# ===== MODELS =====

@dataclass
class MailchimpConfig:
    """Mailchimp configuration"""
    api_key: str
    server_prefix: str  # e.g., "us1", "us2", etc.
    timeout: int = 30


@dataclass
class Contact:
    """Mailchimp contact"""
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    tags: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Mailchimp API format"""
        merge_fields = {}
        if self.first_name:
            merge_fields["FNAME"] = self.first_name
        if self.last_name:
            merge_fields["LNAME"] = self.last_name
        if self.phone:
            merge_fields["PHONE"] = self.phone
        
        data = {
            "email_address": self.email,
            "status": "subscribed",
            "merge_fields": merge_fields
        }
        
        if self.tags:
            data["tags"] = self.tags
        
        return data


@dataclass
class Audience:
    """Mailchimp audience (list)"""
    id: str
    name: str
    member_count: int
    created_date: datetime
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Audience':
        """Create from API response"""
        return cls(
            id=data["id"],
            name=data["name"],
            member_count=data["stats"]["member_count"],
            created_date=datetime.fromisoformat(data["date_created"].replace("Z", "+00:00"))
        )


@dataclass
class Campaign:
    """Mailchimp campaign"""
    id: str
    title: str
    status: str
    audience_id: str
    send_time: Optional[datetime] = None
    create_time: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Campaign':
        """Create from API response"""
        send_time = None
        if data.get("send_time"):
            send_time = datetime.fromisoformat(data["send_time"].replace("Z", "+00:00"))
        
        create_time = None
        if data.get("create_time"):
            create_time = datetime.fromisoformat(data["create_time"].replace("Z", "+00:00"))
        
        return cls(
            id=data["id"],
            title=data["settings"]["title"],
            status=data["status"],
            audience_id=data["recipients"]["list_id"],
            send_time=send_time,
            create_time=create_time
        )


@dataclass
class CampaignContent:
    """Campaign content"""
    html: str
    plain_text: Optional[str] = None


# ===== CLIENT =====

class MailchimpClient:
    """Mailchimp API client for email marketing"""
    
    def __init__(self, config: Optional[MailchimpConfig] = None):
        if config is None:
            api_key = os.getenv("MAILCHIMP_API_KEY", "")
            server_prefix = api_key.split("-")[-1] if api_key and "-" in api_key else "us1"
            
            config = MailchimpConfig(
                api_key=api_key,
                server_prefix=server_prefix
            )
        
        self.config = config
        self.base_url = f"https://{config.server_prefix}.api.mailchimp.com/3.0"
        self.client = httpx.Client(
            base_url=self.base_url,
            auth=("apikey", config.api_key),
            timeout=config.timeout
        )
        
        if not config.api_key:
            logger.warning("Mailchimp API key not configured")
    
    def get_audiences(self) -> List[Audience]:
        """Get all audiences (lists)"""
        try:
            response = self.client.get("/lists")
            response.raise_for_status()
            
            data = response.json()
            audiences = [Audience.from_dict(list_data) for list_data in data["lists"]]
            
            logger.info(f"Retrieved {len(audiences)} audiences")
            return audiences
            
        except Exception as e:
            logger.error(f"Failed to get audiences: {e}")
            raise
    
    def get_audience(self, audience_id: str) -> Audience:
        """Get a specific audience"""
        try:
            response = self.client.get(f"/lists/{audience_id}")
            response.raise_for_status()
            
            data = response.json()
            audience = Audience.from_dict(data)
            
            logger.info(f"Retrieved audience: {audience.name}")
            return audience
            
        except Exception as e:
            logger.error(f"Failed to get audience: {e}")
            raise
    
    def add_contact(self, audience_id: str, contact: Contact) -> Dict[str, Any]:
        """Add a contact to an audience"""
        try:
            contact_data = contact.to_dict()
            
            response = self.client.post(
                f"/lists/{audience_id}/members",
                json=contact_data
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Added contact {contact.email} to audience {audience_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to add contact: {e}")
            raise
    
    def update_contact(self, audience_id: str, email: str, contact: Contact) -> Dict[str, Any]:
        """Update a contact in an audience"""
        try:
            # Get subscriber hash (MD5 of lowercase email)
            import hashlib
            subscriber_hash = hashlib.md5(email.lower().encode()).hexdigest()
            
            contact_data = contact.to_dict()
            
            response = self.client.put(
                f"/lists/{audience_id}/members/{subscriber_hash}",
                json=contact_data
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Updated contact {email} in audience {audience_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to update contact: {e}")
            raise
    
    def remove_contact(self, audience_id: str, email: str) -> bool:
        """Remove a contact from an audience"""
        try:
            # Get subscriber hash
            import hashlib
            subscriber_hash = hashlib.md5(email.lower().encode()).hexdigest()
            
            response = self.client.delete(f"/lists/{audience_id}/members/{subscriber_hash}")
            response.raise_for_status()
            
            logger.info(f"Removed contact {email} from audience {audience_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove contact: {e}")
            return False
    
    def get_campaigns(self, status: Optional[str] = None) -> List[Campaign]:
        """Get campaigns"""
        try:
            params = {}
            if status:
                params["status"] = status
            
            response = self.client.get("/campaigns", params=params)
            response.raise_for_status()
            
            data = response.json()
            campaigns = [Campaign.from_dict(campaign_data) for campaign_data in data["campaigns"]]
            
            logger.info(f"Retrieved {len(campaigns)} campaigns")
            return campaigns
            
        except Exception as e:
            logger.error(f"Failed to get campaigns: {e}")
            raise
    
    def create_campaign(self, audience_id: str, title: str, subject: str, from_name: str, reply_to: str) -> Campaign:
        """Create a campaign"""
        try:
            campaign_data = {
                "type": "regular",
                "recipients": {"list_id": audience_id},
                "settings": {
                    "subject_line": subject,
                    "title": title,
                    "from_name": from_name,
                    "reply_to": reply_to,
                    "auto_footer": False,
                    "inline_css": True
                }
            }
            
            response = self.client.post("/campaigns", json=campaign_data)
            response.raise_for_status()
            
            data = response.json()
            campaign = Campaign.from_dict(data)
            
            logger.info(f"Created campaign: {campaign.title}")
            return campaign
            
        except Exception as e:
            logger.error(f"Failed to create campaign: {e}")
            raise
    
    def set_campaign_content(self, campaign_id: str, content: CampaignContent) -> Dict[str, Any]:
        """Set campaign content"""
        try:
            content_data = {
                "html": content.html
            }
            
            if content.plain_text:
                content_data["plain_text"] = content.plain_text
            
            response = self.client.put(f"/campaigns/{campaign_id}/content", json=content_data)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Set content for campaign {campaign_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to set campaign content: {e}")
            raise
    
    def send_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Send a campaign"""
        try:
            response = self.client.post(f"/campaigns/{campaign_id}/actions/send")
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Sent campaign {campaign_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to send campaign: {e}")
            raise
    
    def get_campaign_report(self, campaign_id: str) -> Dict[str, Any]:
        """Get campaign report"""
        try:
            response = self.client.get(f"/reports/{campaign_id}")
            response.raise_for_status()
            
            report = response.json()
            logger.info(f"Retrieved report for campaign {campaign_id}")
            return report
            
        except Exception as e:
            logger.error(f"Failed to get campaign report: {e}")
            raise
    
    def close(self):
        """Close the HTTP client"""
        self.client.close()


# Factory function
def create_mailchimp_client(config: Optional[MailchimpConfig] = None) -> MailchimpClient:
    """Create a Mailchimp client instance"""
    return MailchimpClient(config)


# Convenience functions
def add_contact_to_list(audience_id: str, email: str, **kwargs) -> Dict[str, Any]:
    """Convenience function to add a contact to a list"""
    client = MailchimpClient()
    try:
        contact = Contact(email=email, **kwargs)
        return client.add_contact(audience_id, contact)
    finally:
        client.close()


def create_and_send_campaign(audience_id: str, title: str, subject: str, html_content: str, **kwargs) -> Campaign:
    """Convenience function to create and send a campaign"""
    client = MailchimpClient()
    try:
        # Create campaign
        campaign = client.create_campaign(audience_id, title, subject, **kwargs)
        
        # Set content
        content = CampaignContent(html=html_content)
        client.set_campaign_content(campaign.id, content)
        
        # Send campaign
        client.send_campaign(campaign.id)
        
        return campaign
    finally:
        client.close()


__all__ = [
    # Models
    'MailchimpConfig',
    'Contact',
    'Audience',
    'Campaign',
    'CampaignContent',
    
    # Client
    'MailchimpClient',
    'create_mailchimp_client',
    
    # Convenience
    'add_contact_to_list',
    'create_and_send_campaign',
]
