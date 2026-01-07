"""
Instagram Integration

Flattened module containing Instagram API client and models for media management,
user data, and business features.
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
class InstagramConfig:
    """Instagram API configuration"""
    client_id: str
    client_secret: str
    redirect_uri: str
    access_token: Optional[str] = None
    timeout: int = 30


@dataclass
class UserProfile:
    """Instagram user profile"""
    id: str
    username: str
    account_type: str  # "BUSINESS", "CREATOR", "PERSONAL"
    media_count: int
    follower_count: int
    following_count: int
    biography: Optional[str] = None
    website: Optional[str] = None
    profile_picture_url: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        """Create from API response"""
        return cls(
            id=data["id"],
            username=data["username"],
            account_type=data.get("account_type", "PERSONAL"),
            media_count=data.get("media_count", 0),
            follower_count=data.get("follower_count", 0),
            following_count=data.get("following_count", 0),
            biography=data.get("biography"),
            website=data.get("website"),
            profile_picture_url=data.get("profile_picture_url")
        )


@dataclass
class MediaItem:
    """Instagram media item"""
    id: str
    media_type: str  # "IMAGE", "VIDEO", "CAROUSEL_ALBUM"
    caption: Optional[str]
    media_url: str
    permalink: str
    timestamp: datetime
    like_count: int = 0
    comment_count: int = 0
    thumbnail_url: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MediaItem':
        """Create from API response"""
        timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        
        return cls(
            id=data["id"],
            media_type=data["media_type"],
            caption=data.get("caption"),
            media_url=data["media_url"],
            permalink=data["permalink"],
            timestamp=timestamp,
            like_count=data.get("like_count", 0),
            comment_count=data.get("comment_count", 0),
            thumbnail_url=data.get("thumbnail_url")
        )


@dataclass
class MediaInsight:
    """Media insights"""
    media_id: str
    impressions: int
    reach: int
    engagement: int
    engagement_rate: float
    saved_count: int = 0
    shares: int = 0
    
    @classmethod
    def from_dict(cls, media_id: str, data: Dict[str, Any]) -> 'MediaInsight':
        """Create from API response"""
        metrics = data.get("data", [])
        
        # Extract metrics
        impressions = 0
        reach = 0
        engagement = 0
        saved_count = 0
        shares = 0
        
        for metric in metrics:
            name = metric.get("name")
            values = metric.get("values", [])
            if values:
                value = values[0].get("value", 0)
                
                if name == "impressions":
                    impressions = value
                elif name == "reach":
                    reach = value
                elif name == "engagement":
                    engagement = value
                elif name == "saved":
                    saved_count = value
                elif name == "shares":
                    shares = value
        
        # Calculate engagement rate
        total_impressions = impressions + reach
        engagement_rate = (engagement / total_impressions * 100) if total_impressions > 0 else 0
        
        return cls(
            media_id=media_id,
            impressions=impressions,
            reach=reach,
            engagement=engagement,
            engagement_rate=engagement_rate,
            saved_count=saved_count,
            shares=shares
        )


@dataclass
class UserInsight:
    """User account insights"""
    follower_count: int
    reach: int
    impressions: int
    profile_views: int
    website_clicks: int
    email_contacts: int = 0
    phone_call_clicks: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserInsight':
        """Create from API response"""
        metrics = data.get("data", [])
        
        # Extract metrics
        follower_count = 0
        reach = 0
        impressions = 0
        profile_views = 0
        website_clicks = 0
        email_contacts = 0
        phone_call_clicks = 0
        
        for metric in metrics:
            name = metric.get("name")
            values = metric.get("values", [])
            if values:
                value = values[0].get("value", 0)
                
                if name == "follower_count":
                    follower_count = value
                elif name == "reach":
                    reach = value
                elif name == "impressions":
                    impressions = value
                elif name == "profile_views":
                    profile_views = value
                elif name == "website_clicks":
                    website_clicks = value
                elif name == "email_contacts":
                    email_contacts = value
                elif name == "phone_call_clicks":
                    phone_call_clicks = value
        
        return cls(
            follower_count=follower_count,
            reach=reach,
            impressions=impressions,
            profile_views=profile_views,
            website_clicks=website_clicks,
            email_contacts=email_contacts,
            phone_call_clicks=phone_call_clicks
        )


# ===== CLIENT =====

class InstagramClient:
    """Instagram API client for media and user management"""
    
    def __init__(self, config: Optional[InstagramConfig] = None):
        if config is None:
            config = InstagramConfig(
                client_id=os.getenv("INSTAGRAM_CLIENT_ID", ""),
                client_secret=os.getenv("INSTAGRAM_CLIENT_SECRET", ""),
                redirect_uri=os.getenv("INSTAGRAM_REDIRECT_URI", ""),
                access_token=os.getenv("INSTAGRAM_ACCESS_TOKEN")
            )
        
        self.config = config
        self.base_url = "https://graph.instagram.com"
        self.client = httpx.Client(timeout=config.timeout)
        
        if not config.access_token:
            logger.warning("Instagram access token not configured")
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Get Instagram authorization URL"""
        params = {
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "response_type": "code",
            "scope": "user_profile,user_media"
        }
        
        if state:
            params["state"] = state
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"https://api.instagram.com/oauth/authorize?{query_string}"
    
    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        try:
            data = {
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "grant_type": "authorization_code",
                "redirect_uri": self.config.redirect_uri,
                "code": code
            }
            
            response = self.client.post("https://api.instagram.com/oauth/access_token", data=data)
            response.raise_for_status()
            
            result = response.json()
            
            # Get long-lived token
            if "access_token" in result:
                long_lived_token = self.get_long_lived_token(result["access_token"])
                if long_lived_token:
                    result.update(long_lived_token)
            
            logger.info("Exchanged code for access token")
            return result
            
        except Exception as e:
            logger.error(f"Failed to exchange code for token: {e}")
            raise
    
    def get_long_lived_token(self, short_lived_token: str) -> Optional[Dict[str, Any]]:
        """Exchange short-lived token for long-lived token"""
        try:
            params = {
                "grant_type": "ig_exchange_token",
                "client_secret": self.config.client_secret,
                "access_token": short_lived_token
            }
            
            response = self.client.get(f"{self.base_url}/access_token", params=params)
            response.raise_for_status()
            
            result = response.json()
            logger.info("Obtained long-lived token")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get long-lived token: {e}")
            return None
    
    def get_user_profile(self) -> UserProfile:
        """Get user profile information"""
        if not self.config.access_token:
            raise ValueError("Access token required")
        
        try:
            params = {
                "fields": "id,username,account_type,media_count,follower_count,following_count,biography,website,profile_picture_url",
                "access_token": self.config.access_token
            }
            
            response = self.client.get(f"{self.base_url}/me", params=params)
            response.raise_for_status()
            
            data = response.json()
            profile = UserProfile.from_dict(data)
            
            logger.info(f"Retrieved user profile: {profile.username}")
            return profile
            
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            raise
    
    def get_user_media(self, limit: int = 25) -> List[MediaItem]:
        """Get user's media items"""
        if not self.config.access_token:
            raise ValueError("Access token required")
        
        try:
            params = {
                "fields": "id,media_type,caption,media_url,permalink,timestamp,like_count,comment_count,thumbnail_url",
                "limit": limit,
                "access_token": self.config.access_token
            }
            
            response = self.client.get(f"{self.base_url}/me/media", params=params)
            response.raise_for_status()
            
            data = response.json()
            media_items = [MediaItem.from_dict(item) for item in data.get("data", [])]
            
            logger.info(f"Retrieved {len(media_items)} media items")
            return media_items
            
        except Exception as e:
            logger.error(f"Failed to get user media: {e}")
            raise
    
    def get_media_insights(self, media_id: str) -> MediaInsight:
        """Get insights for a specific media item"""
        if not self.config.access_token:
            raise ValueError("Access token required")
        
        try:
            params = {
                "metric": "impressions,reach,engagement,saved,shares",
                "access_token": self.config.access_token
            }
            
            response = self.client.get(f"{self.base_url}/{media_id}/insights", params=params)
            response.raise_for_status()
            
            data = response.json()
            insights = MediaInsight.from_dict(media_id, data)
            
            logger.info(f"Retrieved insights for media {media_id}")
            return insights
            
        except Exception as e:
            logger.error(f"Failed to get media insights: {e}")
            raise
    
    def get_user_insights(self, period: str = "day") -> UserInsight:
        """Get user account insights"""
        if not self.config.access_token:
            raise ValueError("Access token required")
        
        try:
            params = {
                "metric": "follower_count,reach,impressions,profile_views,website_clicks,email_contacts,phone_call_clicks",
                "period": period,
                "access_token": self.config.access_token
            }
            
            response = self.client.get(f"{self.base_url}/me/insights", params=params)
            response.raise_for_status()
            
            data = response.json()
            insights = UserInsight.from_dict(data)
            
            logger.info(f"Retrieved user insights for period: {period}")
            return insights
            
        except Exception as e:
            logger.error(f"Failed to get user insights: {e}")
            raise
    
    def close(self):
        """Close the HTTP client"""
        self.client.close()


# Factory function
def create_instagram_client(config: Optional[InstagramConfig] = None) -> InstagramClient:
    """Create an Instagram client instance"""
    return InstagramClient(config)


# Convenience functions
def get_user_media(limit: int = 25) -> List[MediaItem]:
    """Convenience function to get user media"""
    client = InstagramClient()
    try:
        return client.get_user_media(limit)
    finally:
        client.close()


def get_user_profile() -> UserProfile:
    """Convenience function to get user profile"""
    client = InstagramClient()
    try:
        return client.get_user_profile()
    finally:
        client.close()


__all__ = [
    # Models
    'InstagramConfig',
    'UserProfile',
    'MediaItem',
    'MediaInsight',
    'UserInsight',
    
    # Client
    'InstagramClient',
    'create_instagram_client',
    
    # Convenience
    'get_user_media',
    'get_user_profile',
]
