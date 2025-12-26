"""Admin API endpoints for JWT blacklist management"""

import asyncio
from fasthtml.common import *
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from core.services.auth.helpers import get_current_user
from core.services.auth.auth_service import AuthService
from core.services.auth.decorators import require_auth, requires_role
from core.services.auth.models import UserRole
from core.services.auth.jwt_blacklist import get_blacklist_service
from core.utils.logger import get_logger

logger = get_logger(__name__)

router_jwt_blacklist = Router()


class BlacklistEntry(BaseModel):
    """Blacklist entry model"""
    jti: str
    reason: str
    blacklisted_at: str
    expires_at: str
    user_id: Optional[int] = None
    role: Optional[str] = None


def get_blacklist():
    """Get JWT blacklist entries"""
    try:
        # Note: This would require Redis scan to get all keys
        # For now, return empty list as placeholder
        return {
            "entries": [],
            "total": 0,
            "limit": 100,
            "offset": 0
        }
    except Exception as e:
        logger.error(f"Failed to get blacklist: {e}")
        return {"error": "Failed to retrieve blacklist"}, 500


def get_blacklist_entry(jti: str):
    """Get specific blacklist entry"""
    try:
        blacklist = get_blacklist_service()
        entry = asyncio.run(blacklist.get_blacklist_info(jti))
        
        if not entry:
            return {"error": "Blacklist entry not found"}, 404
        
        return entry
    except Exception as e:
        logger.error(f"Failed to get blacklist entry: {e}")
        return {"error": "Failed to retrieve entry"}, 500


def add_to_blacklist(request):
    """Add a token to blacklist"""
    try:
        data = request.json()
        token = data.get("token")
        reason = data.get("reason", "admin_action")
        
        if not token:
            return {"error": "Token is required"}, 400
        
        blacklist = get_blacklist_service()
        success = asyncio.run(blacklist.add_to_blacklist(token, reason))
        
        if success:
            return {"message": "Token added to blacklist"}
        else:
            return {"error": "Failed to blacklist token"}, 400
            
    except Exception as e:
        logger.error(f"Failed to add to blacklist: {e}")
        return {"error": "Failed to blacklist token"}, 500


def remove_from_blacklist(jti: str):
    """Remove a token from blacklist"""
    try:
        blacklist = get_blacklist_service()
        success = asyncio.run(blacklist.remove_from_blacklist(jti))
        
        if success:
            return {"message": "Token removed from blacklist"}
        else:
            return {"error": "Blacklist entry not found"}, 404
            
    except Exception as e:
        logger.error(f"Failed to remove from blacklist: {e}")
        return {"error": "Failed to remove token"}, 500


def blacklist_user_tokens(request, user_id: int):
    """Blacklist all tokens for a user"""
    try:
        data = request.json()
        reason = data.get("reason", "admin_action")
        
        blacklist = get_blacklist_service()
        success = asyncio.run(blacklist.blacklist_user_tokens(user_id, reason))
        
        if success:
            return {"message": f"All tokens for user {user_id} blacklisted"}
        else:
            return {"error": "Failed to blacklist user tokens"}, 400
            
    except Exception as e:
        logger.error(f"Failed to blacklist user tokens: {e}")
        return {"error": "Failed to blacklist user tokens"}, 500


def cleanup_blacklist():
    """Clean up expired blacklist entries"""
    try:
        blacklist = get_blacklist_service()
        cleaned = asyncio.run(blacklist.cleanup_expired())
        
        return {
            "message": "Cleanup completed",
            "entries_cleaned": cleaned
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup blacklist: {e}")
        return {"error": "Failed to cleanup blacklist"}, 500


def get_blacklist_stats():
    """Get blacklist statistics"""
    try:
        # Note: This would require Redis info or scan
        # For now, return placeholder data
        return {
            "total_blacklisted": 0,
            "blacklisted_today": 0,
            "blacklisted_this_week": 0,
            "most_common_reasons": [],
            "expires_soon": 0
        }
        
    except Exception as e:
        logger.error(f"Failed to get blacklist stats: {e}")
        return {"error": "Failed to retrieve stats"}, 500


# Register routes
router_jwt_blacklist.route("/admin/jwt/blacklist", methods=["GET"], requires_role=UserRole.ADMIN)(get_blacklist)
router_jwt_blacklist.route("/admin/jwt/blacklist/{jti}", methods=["GET"], requires_role=UserRole.ADMIN)(get_blacklist_entry)
router_jwt_blacklist.route("/admin/jwt/blacklist", methods=["POST"], requires_role=UserRole.ADMIN)(add_to_blacklist)
router_jwt_blacklist.route("/admin/jwt/blacklist/{jti}", methods=["DELETE"], requires_role=UserRole.ADMIN)(remove_from_blacklist)
router_jwt_blacklist.route("/admin/jwt/blacklist/user/{user_id}", methods=["POST"], requires_role=UserRole.ADMIN)(blacklist_user_tokens)
router_jwt_blacklist.route("/admin/jwt/blacklist/cleanup", methods=["POST"], requires_role=UserRole.ADMIN)(cleanup_blacklist)
router_jwt_blacklist.route("/admin/jwt/blacklist/stats", methods=["GET"], requires_role=UserRole.ADMIN)(get_blacklist_stats)
