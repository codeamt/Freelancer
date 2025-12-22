"""
Instagram API Client Integration

This module provides a client for interacting with the Instagram Basic Display API
and Instagram Graph API for media management, user data, and business features.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import httpx
from core.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class InstagramConfig:
    """Instagram configuration"""
    app_id: str
    app_secret: str
    redirect_uri: str
    access_token: Optional[str] = None
    long_lived_token: Optional[str] = None
    timeout: int = 30


@dataclass
class MediaItem:
    """Instagram media item"""
    id: str
    media_type: str  # "IMAGE", "VIDEO", "CAROUSEL_ALBUM"
    media_url: str
    permalink: str
    timestamp: datetime
    caption: Optional[str] = None
    media_count: Optional[int] = None  # For carousel albums
    thumbnail_url: Optional[str] = None  # For videos


@dataclass
class UserProfile:
    """Instagram user profile"""
    id: str
    username: str
    account_type: str  # "PERSONAL", "BUSINESS", "CREATOR"
    media_count: int
    followers_count: Optional[int] = None
    follows_count: Optional[int] = None


@dataclass
class MediaInsight:
    """Media insights/analytics"""
    media_id: str
    impressions: int
    reach: int
    engagement: int
    likes: int
    comments: int
    shares: int
    saves: int


@dataclass
class UserInsight:
    """User account insights"""
    user_id: str
    impressions: int
    reach: int
    profile_views: int
    website_clicks: int
    follower_count: int
    follower_growth: int


class InstagramClient:
    """Instagram API client"""
    
    def __init__(self, config: InstagramConfig):
        self.config = config
        self.base_url = "https://graph.instagram.com"
        self.graph_url = "https://graph.facebook.com/v18.0"
        self.headers = {
            "Content-Type": "application/json"
        }
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                          use_graph_api: bool = False) -> Dict:
        """Make HTTP request to Instagram API"""
        base = self.graph_url if use_graph_api else self.base_url
        url = f"{base}/{endpoint}"
        
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=self.headers, params=data)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=self.headers, json=data)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=self.headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Instagram API error: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Instagram client error: {str(e)}")
                raise
    
    # Authentication
    def get_authorization_url(self, scope: List[str] = None) -> str:
        """Get OAuth authorization URL"""
        if scope is None:
            scope = ["user_profile", "user_media"]
        
        params = {
            "client_id": self.config.app_id,
            "redirect_uri": self.config.redirect_uri,
            "scope": " ".join(scope),
            "response_type": "code"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"https://api.instagram.com/oauth/authorize?{query_string}"
    
    async def exchange_code_for_token(self, code: str) -> Dict:
        """Exchange authorization code for access token"""
        try:
            data = {
                "client_id": self.config.app_id,
                "client_secret": self.config.app_secret,
                "grant_type": "authorization_code",
                "redirect_uri": self.config.redirect_uri,
                "code": code
            }
            
            response = await self._make_request("POST", "oauth/access_token", data)
            return response
            
        except Exception as e:
            logger.error(f"Failed to exchange code for token: {str(e)}")
            raise
    
    async def get_long_lived_token(self, short_lived_token: str) -> Dict:
        """Exchange short-lived token for long-lived token"""
        try:
            data = {
                "grant_type": "ig_exchange_token",
                "client_secret": self.config.app_secret,
                "access_token": short_lived_token
            }
            
            response = await self._make_request("GET", "access_token", data)
            return response
            
        except Exception as e:
            logger.error(f"Failed to get long-lived token: {str(e)}")
            raise
    
    async def refresh_long_lived_token(self) -> Dict:
        """Refresh long-lived token"""
        try:
            if not self.config.long_lived_token:
                raise ValueError("No long-lived token available")
            
            data = {
                "grant_type": "ig_refresh_token",
                "access_token": self.config.long_lived_token
            }
            
            response = await self._make_request("GET", "refresh_access_token", data)
            return response
            
        except Exception as e:
            logger.error(f"Failed to refresh long-lived token: {str(e)}")
            raise
    
    # User Profile
    async def get_user_profile(self, user_id: str = None) -> Optional[UserProfile]:
        """Get user profile information"""
        try:
            token = self.config.long_lived_token or self.config.access_token
            if not token:
                raise ValueError("No access token available")
            
            endpoint = f"{user_id}" if user_id else "me"
            params = {
                "fields": "id,username,account_type,media_count",
                "access_token": token
            }
            
            response = await self._make_request("GET", endpoint, params)
            
            return UserProfile(
                id=response["id"],
                username=response["username"],
                account_type=response["account_type"],
                media_count=response["media_count"]
            )
            
        except Exception as e:
            logger.error(f"Failed to get user profile: {str(e)}")
            return None
    
    async def get_user_media(self, user_id: str = None, limit: int = 25, 
                           fields: List[str] = None) -> List[MediaItem]:
        """Get user media items"""
        try:
            token = self.config.long_lived_token or self.config.access_token
            if not token:
                raise ValueError("No access token available")
            
            if fields is None:
                fields = ["id", "media_type", "media_url", "permalink", "timestamp", 
                         "caption", "media_count", "thumbnail_url"]
            
            endpoint = f"{user_id}/media" if user_id else "me/media"
            params = {
                "fields": ",".join(fields),
                "limit": limit,
                "access_token": token
            }
            
            response = await self._make_request("GET", endpoint, params)
            
            media_items = []
            for item in response.get("data", []):
                media_item = MediaItem(
                    id=item["id"],
                    media_type=item["media_type"],
                    media_url=item["media_url"],
                    permalink=item["permalink"],
                    timestamp=datetime.fromisoformat(item["timestamp"]),
                    caption=item.get("caption"),
                    media_count=item.get("media_count"),
                    thumbnail_url=item.get("thumbnail_url")
                )
                media_items.append(media_item)
            
            return media_items
            
        except Exception as e:
            logger.error(f"Failed to get user media: {str(e)}")
            return []
    
    async def get_media_item(self, media_id: str, 
                           fields: List[str] = None) -> Optional[MediaItem]:
        """Get specific media item"""
        try:
            token = self.config.long_lived_token or self.config.access_token
            if not token:
                raise ValueError("No access token available")
            
            if fields is None:
                fields = ["id", "media_type", "media_url", "permalink", "timestamp", 
                         "caption", "media_count", "thumbnail_url"]
            
            params = {
                "fields": ",".join(fields),
                "access_token": token
            }
            
            response = await self._make_request("GET", media_id, params)
            
            return MediaItem(
                id=response["id"],
                media_type=response["media_type"],
                media_url=response["media_url"],
                permalink=response["permalink"],
                timestamp=datetime.fromisoformat(response["timestamp"]),
                caption=response.get("caption"),
                media_count=response.get("media_count"),
                thumbnail_url=response.get("thumbnail_url")
            )
            
        except Exception as e:
            logger.error(f"Failed to get media item {media_id}: {str(e)}")
            return None
    
    # Media Publishing (Business/Creator accounts only)
    async def create_media_container(self, image_url: str, caption: str = None, 
                                  user_id: str = None) -> Dict:
        """Create media container for publishing"""
        try:
            token = self.config.long_lived_token or self.config.access_token
            if not token:
                raise ValueError("No access token available")
            
            endpoint = f"{user_id}/media" if user_id else "me/media"
            data = {
                "image_url": image_url,
                "access_token": token
            }
            
            if caption:
                data["caption"] = caption
            
            response = await self._make_request("POST", endpoint, data, use_graph_api=True)
            return response
            
        except Exception as e:
            logger.error(f"Failed to create media container: {str(e)}")
            raise
    
    async def publish_media(self, creation_id: str, user_id: str = None) -> Dict:
        """Publish media container"""
        try:
            token = self.config.long_lived_token or self.config.access_token
            if not token:
                raise ValueError("No access token available")
            
            endpoint = f"{user_id}/media_publish" if user_id else "me/media_publish"
            data = {
                "creation_id": creation_id,
                "access_token": token
            }
            
            response = await self._make_request("POST", endpoint, data, use_graph_api=True)
            return response
            
        except Exception as e:
            logger.error(f"Failed to publish media: {str(e)}")
            raise
    
    # Insights (Business/Creator accounts only)
    async def get_media_insights(self, media_id: str, 
                               metrics: List[str] = None) -> Optional[MediaInsight]:
        """Get media insights/analytics"""
        try:
            token = self.config.long_lived_token or self.config.access_token
            if not token:
                raise ValueError("No access token available")
            
            if metrics is None:
                metrics = ["impressions", "reach", "engagement", "likes", "comments", 
                          "shares", "saves"]
            
            params = {
                "metric": ",".join(metrics),
                "access_token": token
            }
            
            response = await self._make_request("GET", f"{media_id}/insights", params, 
                                             use_graph_api=True)
            
            # Parse insights data
            insights_data = {}
            for metric in response.get("data", []):
                insights_data[metric["name"]] = metric["values"][0]["value"]
            
            return MediaInsight(
                media_id=media_id,
                impressions=insights_data.get("impressions", 0),
                reach=insights_data.get("reach", 0),
                engagement=insights_data.get("engagement", 0),
                likes=insights_data.get("likes", 0),
                comments=insights_data.get("comments", 0),
                shares=insights_data.get("shares", 0),
                saves=insights_data.get("saves", 0)
            )
            
        except Exception as e:
            logger.error(f"Failed to get media insights {media_id}: {str(e)}")
            return None
    
    async def get_user_insights(self, user_id: str = None, 
                              metrics: List[str] = None, 
                              period: str = "day") -> Optional[UserInsight]:
        """Get user account insights"""
        try:
            token = self.config.long_lived_token or self.config.access_token
            if not token:
                raise ValueError("No access token available")
            
            if metrics is None:
                metrics = ["impressions", "reach", "profile_views", "website_clicks", 
                          "follower_count"]
            
            endpoint = f"{user_id}/insights" if user_id else "me/insights"
            params = {
                "metric": ",".join(metrics),
                "period": period,
                "access_token": token
            }
            
            response = await self._make_request("GET", endpoint, params, use_graph_api=True)
            
            # Parse insights data
            insights_data = {}
            for metric in response.get("data", []):
                insights_data[metric["name"]] = metric["values"][0]["value"]
            
            return UserInsight(
                user_id=user_id or "me",
                impressions=insights_data.get("impressions", 0),
                reach=insights_data.get("reach", 0),
                profile_views=insights_data.get("profile_views", 0),
                website_clicks=insights_data.get("website_clicks", 0),
                follower_count=insights_data.get("follower_count", 0),
                follower_growth=insights_data.get("follower_growth", 0)
            )
            
        except Exception as e:
            logger.error(f"Failed to get user insights: {str(e)}")
            return None
    
    # Hashtag Search (Business/Creator accounts only)
    async def search_hashtag(self, hashtag: str) -> Dict:
        """Search for hashtag"""
        try:
            token = self.config.long_lived_token or self.config.access_token
            if not token:
                raise ValueError("No access token available")
            
            params = {
                "q": hashtag,
                "access_token": token
            }
            
            response = await self._make_request("GET", "ig_hashtag_search", params, 
                                             use_graph_api=True)
            return response
            
        except Exception as e:
            logger.error(f"Failed to search hashtag {hashtag}: {str(e)}")
            raise
    
    async def get_hashtag_media(self, hashtag_id: str, limit: int = 25) -> List[Dict]:
        """Get media for specific hashtag"""
        try:
            token = self.config.long_lived_token or self.config.access_token
            if not token:
                raise ValueError("No access token available")
            
            params = {
                "limit": limit,
                "access_token": token
            }
            
            response = await self._make_request("GET", f"{hashtag_id}/recent_media", params, 
                                             use_graph_api=True)
            return response.get("data", [])
            
        except Exception as e:
            logger.error(f"Failed to get hashtag media {hashtag_id}: {str(e)}")
            return []
    
    # Comments
    async def get_media_comments(self, media_id: str, limit: int = 25) -> List[Dict]:
        """Get comments for media"""
        try:
            token = self.config.long_lived_token or self.config.access_token
            if not token:
                raise ValueError("No access token available")
            
            params = {
                "limit": limit,
                "access_token": token
            }
            
            response = await self._make_request("GET", f"{media_id}/comments", params, 
                                             use_graph_api=True)
            return response.get("data", [])
            
        except Exception as e:
            logger.error(f"Failed to get media comments {media_id}: {str(e)}")
            return []
    
    async def reply_to_comment(self, comment_id: str, message: str) -> Dict:
        """Reply to a comment"""
        try:
            token = self.config.long_lived_token or self.config.access_token
            if not token:
                raise ValueError("No access token available")
            
            data = {
                "message": message,
                "access_token": token
            }
            
            response = await self._make_request("POST", f"{comment_id}/replies", data, 
                                             use_graph_api=True)
            return response
            
        except Exception as e:
            logger.error(f"Failed to reply to comment {comment_id}: {str(e)}")
            raise
    
    # Health Check
    async def ping(self) -> bool:
        """Test API connection"""
        try:
            if not self.config.access_token and not self.config.long_lived_token:
                return False
            
            await self.get_user_profile()
            return True
            
        except Exception as e:
            logger.error(f"Instagram API ping failed: {str(e)}")
            return False
