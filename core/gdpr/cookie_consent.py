"""
Cookie Consent Management

Manages GDPR cookie consent tracking and preferences.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import json
import secrets

from core.utils.logger import get_logger

logger = get_logger(__name__)


class CookieCategory(Enum):
    """Cookie categories for consent"""
    NECESSARY = "necessary"  # Essential cookies
    FUNCTIONAL = "functional"  # Functionality cookies
    ANALYTICS = "analytics"  # Analytics cookies
    MARKETING = "marketing"  # Marketing cookies
    SOCIAL_MEDIA = "social_media"  # Social media cookies


class CookieConsentManager:
    """Manages cookie consent"""
    
    def __init__(self, postgres_adapter):
        self.postgres = postgres_adapter
        self._ensure_tables()
    
    async def _ensure_tables(self):
        """Ensure cookie consent tables exist"""
        await self.postgres.execute("""
            CREATE TABLE IF NOT EXISTS gdpr_cookie_consents (
                id SERIAL PRIMARY KEY,
                consent_id VARCHAR(255) UNIQUE NOT NULL,
                user_id INTEGER,
                session_id VARCHAR(255),
                fingerprint VARCHAR(255),
                preferences JSONB NOT NULL DEFAULT '{}',
                granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address INET,
                user_agent TEXT,
                domain VARCHAR(255),
                version INTEGER DEFAULT 1
            )
        """)
        
        await self.postgres.execute("""
            CREATE INDEX IF NOT EXISTS idx_cookie_consents_user_id 
            ON gdpr_cookie_consents(user_id)
        """)
        
        await self.postgres.execute("""
            CREATE INDEX IF NOT EXISTS idx_cookie_consents_session_id 
            ON gdpr_cookie_consents(session_id)
        """)
        
        await self.postgres.execute("""
            CREATE TABLE IF NOT EXISTS gdpr_cookie_categories (
                id SERIAL PRIMARY KEY,
                category VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                required BOOLEAN DEFAULT false,
                cookies JSONB DEFAULT '[]',
                script_urls TEXT[]
            )
        """)
        
        await self.postgres.execute("""
            CREATE TABLE IF NOT EXISTS gdpr_cookie_log (
                id SERIAL PRIMARY KEY,
                consent_id VARCHAR(255) REFERENCES gdpr_cookie_consents(consent_id),
                action VARCHAR(50) NOT NULL,
                category VARCHAR(50),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details JSONB DEFAULT '{}'
            )
        """)
        
        # Initialize default categories
        await self._initialize_categories()
    
    async def _initialize_categories(self):
        """Initialize default cookie categories"""
        categories = [
            {
                "category": CookieCategory.NECESSARY.value,
                "name": "Essential Cookies",
                "description": "These cookies are necessary for the website to function and cannot be switched off.",
                "required": True,
                "cookies": [
                    {"name": "session", "purpose": "Maintains user session"},
                    {"name": "csrf_token", "purpose": "Security token"},
                    {"name": "auth_token", "purpose": "Authentication"}
                ]
            },
            {
                "category": CookieCategory.FUNCTIONAL.value,
                "name": "Functional Cookies",
                "description": "These cookies enable the website to provide enhanced functionality.",
                "required": False,
                "cookies": [
                    {"name": "preferences", "purpose": "User preferences"},
                    {"name": "language", "purpose": "Language selection"},
                    {"name": "theme", "purpose": "Theme selection"}
                ]
            },
            {
                "category": CookieCategory.ANALYTICS.value,
                "name": "Analytics Cookies",
                "description": "These cookies help us understand how visitors interact with our website.",
                "required": False,
                "cookies": [
                    {"name": "_ga", "purpose": "Google Analytics"},
                    {"name": "_gid", "purpose": "Google Analytics"},
                    {"name": "hotjar", "purpose": "User behavior analytics"}
                ]
            },
            {
                "category": CookieCategory.MARKETING.value,
                "name": "Marketing Cookies",
                "description": "These cookies are used to deliver advertisements that are relevant to you.",
                "required": False,
                "cookies": [
                    {"name": "facebook_pixel", "purpose": "Facebook advertising"},
                    {"name": "google_ads", "purpose": "Google advertising"},
                    {"name": "linkedin", "purpose": "LinkedIn advertising"}
                ]
            },
            {
                "category": CookieCategory.SOCIAL_MEDIA.value,
                "name": "Social Media Cookies",
                "description": "These cookies enable social media functionality.",
                "required": False,
                "cookies": [
                    {"name": "twitter", "purpose": "Twitter integration"},
                    {"name": "instagram", "purpose": "Instagram integration"},
                    {"name": "youtube", "purpose": "YouTube integration"}
                ]
            }
        ]
        
        for cat in categories:
            await self.postgres.execute("""
                INSERT INTO gdpr_cookie_categories 
                (category, name, description, required, cookies)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (category) DO NOTHING
            """, cat["category"], cat["name"], cat["description"],
                  cat["required"], json.dumps(cat["cookies"]))
    
    async def record_consent(self, preferences: Dict[CookieCategory, bool],
                           user_id: int = None, session_id: str = None,
                           fingerprint: str = None, ip_address: str = None,
                           user_agent: str = None, domain: str = None) -> str:
        """
        Record cookie consent
        
        Args:
            preferences: Cookie category preferences
            user_id: User ID if logged in
            session_id: Session ID
            fingerprint: Browser fingerprint
            ip_address: IP address
            user_agent: User agent string
            domain: Domain
            
        Returns:
            Consent ID
        """
        consent_id = secrets.token_urlsafe(32)
        
        # Convert preferences to JSON
        prefs_json = {cat.value: granted for cat, granted in preferences.items()}
        
        await self.postgres.execute("""
            INSERT INTO gdpr_cookie_consents 
            (consent_id, user_id, session_id, fingerprint, preferences,
             ip_address, user_agent, domain)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, consent_id, user_id, session_id, fingerprint,
              json.dumps(prefs_json), ip_address, user_agent, domain)
        
        # Log the consent
        for category, granted in preferences.items():
            await self._log_consent_action(
                consent_id, "granted" if granted else "denied",
                category.value
            )
        
        logger.info(f"Recorded cookie consent: {consent_id}")
        return consent_id
    
    async def update_consent(self, consent_id: str, 
                           preferences: Dict[CookieCategory, bool]) -> bool:
        """
        Update existing consent
        
        Args:
            consent_id: Consent ID
            preferences: New preferences
            
        Returns:
            True if successful
        """
        # Get current preferences
        current = await self.postgres.fetch_one("""
            SELECT preferences FROM gdpr_cookie_consents 
            WHERE consent_id = $1
        """, consent_id)
        
        if not current:
            return False
        
        current_prefs = json.loads(current['preferences'])
        new_prefs = {cat.value: granted for cat, granted in preferences.items()}
        
        # Update
        await self.postgres.execute("""
            UPDATE gdpr_cookie_consents 
            SET preferences = $1, updated_at = $2, version = version + 1
            WHERE consent_id = $3
        """, json.dumps(new_prefs), datetime.utcnow(), consent_id)
        
        # Log changes
        for category, granted in preferences.items():
            old_granted = current_prefs.get(category.value, False)
            if old_granted != granted:
                await self._log_consent_action(
                    consent_id, "updated", category.value,
                    {"old": old_granted, "new": granted}
                )
        
        return True
    
    async def get_consent(self, consent_id: str) -> Optional[Dict]:
        """
        Get consent by ID
        
        Args:
            consent_id: Consent ID
            
        Returns:
            Consent record
        """
        result = await self.postgres.fetch_one("""
            SELECT * FROM gdpr_cookie_consents 
            WHERE consent_id = $1
        """, consent_id)
        
        if not result:
            return None
        
        return {
            "consent_id": result['consent_id'],
            "user_id": result['user_id'],
            "preferences": json.loads(result['preferences']),
            "granted_at": result['granted_at'],
            "updated_at": result['updated_at'],
            "version": result['version']
        }
    
    async def get_user_consent(self, user_id: int) -> Optional[Dict]:
        """
        Get latest consent for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Consent record
        """
        result = await self.postgres.fetch_one("""
            SELECT * FROM gdpr_cookie_consents 
            WHERE user_id = $1 
            ORDER BY updated_at DESC 
            LIMIT 1
        """, user_id)
        
        if not result:
            return None
        
        return {
            "consent_id": result['consent_id'],
            "preferences": json.loads(result['preferences']),
            "granted_at": result['granted_at'],
            "updated_at": result['updated_at'],
            "version": result['version']
        }
    
    async def get_consent_by_session(self, session_id: str) -> Optional[Dict]:
        """Get consent by session ID"""
        result = await self.postgres.fetch_one("""
            SELECT * FROM gdpr_cookie_consents 
            WHERE session_id = $1 
            ORDER BY updated_at DESC 
            LIMIT 1
        """, session_id)
        
        if not result:
            return None
        
        return {
            "consent_id": result['consent_id'],
            "user_id": result['user_id'],
            "preferences": json.loads(result['preferences']),
            "granted_at": result['granted_at'],
            "updated_at": result['updated_at']
        }
    
    async def check_category_consent(self, consent_id: str, 
                                   category: CookieCategory) -> bool:
        """
        Check if consent is granted for a category
        
        Args:
            consent_id: Consent ID
            category: Cookie category
            
        Returns:
            True if consent granted
        """
        result = await self.postgres.fetch_one("""
            SELECT preferences FROM gdpr_cookie_consents 
            WHERE consent_id = $1
        """, consent_id)
        
        if not result:
            return False
        
        preferences = json.loads(result['preferences'])
        return preferences.get(category.value, False)
    
    async def get_cookie_categories(self) -> List[Dict]:
        """Get all cookie categories"""
        results = await self.postgres.fetch_all("""
            SELECT * FROM gdpr_cookie_categories 
            ORDER BY required DESC, name
        """)
        
        categories = []
        for row in results:
            categories.append({
                "category": row['category'],
                "name": row['name'],
                "description": row['description'],
                "required": row['required'],
                "cookies": json.loads(row['cookies'])
            })
        
        return categories
    
    async def withdraw_consent(self, consent_id: str, 
                             categories: List[CookieCategory] = None) -> bool:
        """
        Withdraw consent for specific categories or all
        
        Args:
            consent_id: Consent ID
            categories: Categories to withdraw (None for all)
            
        Returns:
            True if successful
        """
        # Get current preferences
        current = await self.postgres.fetch_one("""
            SELECT preferences FROM gdpr_cookie_consents 
            WHERE consent_id = $1
        """, consent_id)
        
        if not current:
            return False
        
        preferences = json.loads(current['preferences'])
        
        # Update preferences
        if categories:
            for category in categories:
                if category.value in preferences:
                    preferences[category.value] = False
        else:
            # Withdraw all non-essential
            essential = await self.postgres.fetch_one("""
                SELECT category FROM gdpr_cookie_categories 
                WHERE required = true
            """)
            
            for key in list(preferences.keys()):
                if key not in [e['category'] for e in essential]:
                    preferences[key] = False
        
        # Save
        await self.postgres.execute("""
            UPDATE gdpr_cookie_consents 
            SET preferences = $1, updated_at = $2, version = version + 1
            WHERE consent_id = $3
        """, json.dumps(preferences), datetime.utcnow(), consent_id)
        
        # Log withdrawal
        for category in categories or []:
            await self._log_consent_action(consent_id, "withdrawn", category.value)
        
        return True
    
    async def get_consent_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get consent statistics
        
        Args:
            days: Number of days to look back
            
        Returns:
            Consent statistics
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Total consents
        total = await self.postgres.fetch_one("""
            SELECT COUNT(*) as count FROM gdpr_cookie_consents 
            WHERE granted_at >= $1
        """, cutoff)
        
        # By category
        category_stats = await self.postgres.fetch_all("""
            SELECT 
                jsonb_object_keys(preferences) as category,
                COUNT(*) FILTER (WHERE preferences::jsonb ->> jsonb_object_keys(preferences) = 'true') as granted,
                COUNT(*) as total
            FROM gdpr_cookie_consents 
            WHERE granted_at >= $1
            GROUP BY jsonb_object_keys(preferences)
        """, cutoff)
        
        # Recent activity
        recent = await self.postgres.fetch_all("""
            SELECT action, COUNT(*) as count
            FROM gdpr_cookie_log 
            WHERE timestamp >= $1
            GROUP BY action
            ORDER BY count DESC
        """, cutoff)
        
        return {
            "period_days": days,
            "total_consents": total['count'],
            "by_category": [dict(s) for s in category_stats],
            "recent_activity": [dict(r) for r in recent]
        }
    
    async def cleanup_old_consents(self, days: int = 365) -> int:
        """
        Clean up old consent records
        
        Args:
            days: Age in days to keep
            
        Returns:
            Number of records cleaned
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        result = await self.postgres.fetch_one("""
            DELETE FROM gdpr_cookie_consents 
            WHERE granted_at < $1
            AND user_id IS NULL  -- Keep logged-in user consents
            RETURNING COUNT(*) as count
        """, cutoff)
        
        count = result['count']
        logger.info(f"Cleaned up {count} old cookie consent records")
        return count
    
    async def _log_consent_action(self, consent_id: str, action: str,
                                category: str, details: Dict = None):
        """Log consent action"""
        await self.postgres.execute("""
            INSERT INTO gdpr_cookie_log 
            (consent_id, action, category, details)
            VALUES ($1, $2, $3, $4)
        """, consent_id, action, category, json.dumps(details or {}))
    
    def generate_consent_script(self, consent_id: str) -> str:
        """
        Generate JavaScript for managing cookie consent
        
        Args:
            consent_id: Consent ID
            
        Returns:
            JavaScript code
        """
        return f"""
        // GDPR Cookie Consent
        window.GDPR_CONSENT_ID = '{consent_id}';
        
        // Check consent before setting cookies
        function setCookie(name, value, category, options) {{
            // Check if consent is granted for category
            if (!hasConsent(category)) {{
                console.warn('Cookie consent not granted for category:', category);
                return false;
            }}
            
            // Set cookie
            document.cookie = name + '=' + value + '; ' + options;
            return true;
        }}
        
        // Check if consent is granted
        function hasConsent(category) {{
            // This would be implemented based on stored preferences
            return true; // Placeholder
        }}
        
        // Show consent banner if needed
        function showConsentBanner() {{
            // Implementation for showing consent banner
        }}
        
        // Update consent
        function updateConsent(preferences) {{
            // Send update to server
            fetch('/api/gdpr/cookie-consent/' + GDPR_CONSENT_ID, {{
                method: 'PUT',
                headers: {{
                    'Content-Type': 'application/json'
                }},
                body: JSON.stringify({{ preferences }})
            }});
        }}
        """
