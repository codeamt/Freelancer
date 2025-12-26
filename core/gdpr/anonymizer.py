"""
Data Anonymizer

Provides data anonymization and pseudonymization capabilities.
"""

import hashlib
import secrets
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
import faker

from core.utils.logger import get_logger

logger = get_logger(__name__)


class DataAnonymizer:
    """Anonymizes personal data while preserving structure"""
    
    def __init__(self):
        self.fake = faker.Faker()
        self.pseudonym_map = {}  # Maps original values to pseudonyms
        self.salt = secrets.token_bytes(32)  # For consistent hashing
    
    async def anonymize_user(self, user_id: int, postgres_adapter) -> bool:
        """
        Anonymize all user data while keeping referential integrity
        
        Args:
            user_id: User ID to anonymize
            postgres_adapter: Database adapter
            
        Returns:
            True if successful
        """
        try:
            # Get user data first
            user_data = await postgres_adapter.fetch_one("""
                SELECT email, first_name, last_name, phone, address, bio
                FROM users WHERE id = $1
            """, user_id)
            
            if not user_data:
                return False
            
            # Anonymize personal data
            anonymized = {
                'email': self.anonymize_email(user_data['email']),
                'first_name': self.fake.first_name(),
                'last_name': self.fake.last_name(),
                'phone': self.anonymize_phone(user_data['phone']),
                'address': self.fake.address().replace('\n', ', '),
                'bio': '[REDACTED]'
            }
            
            # Update user table
            await postgres_adapter.execute("""
                UPDATE users 
                SET email = $1, first_name = $2, last_name = $3,
                    phone = $4, address = $5, bio = $6
                WHERE id = $7
            """, anonymized['email'], anonymized['first_name'],
                  anonymized['last_name'], anonymized['phone'],
                  anonymized['address'], anonymized['bio'], user_id)
            
            # Anonymize device information
            await postgres_adapter.execute("""
                UPDATE devices 
                SET device_name = 'Anonymized Device ' || substr(md5(random()::text), 1, 8),
                    ip_address = '0.0.0.0'
                WHERE user_id = $1
            """, user_id)
            
            # Anonymize session tokens (invalidate them)
            await postgres_adapter.execute("""
                UPDATE user_sessions 
                SET session_token = 'ANONYMIZED-' || substr(md5(random()::text), 1, 32)
                WHERE user_id = $1
            """, user_id)
            
            # Keep refresh tokens but anonymize device info
            await postgres_adapter.execute("""
                UPDATE refresh_tokens 
                SET device_name = 'Anonymized Device',
                    ip_address = '0.0.0.0'
                WHERE user_id = $1
            """, user_id)
            
            logger.info(f"Anonymized data for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to anonymize user {user_id}: {e}")
            return False
    
    def anonymize_email(self, email: str) -> str:
        """Anonymize email address"""
        if not email:
            return None
        
        local, domain = email.split('@', 1) if '@' in email else (email, 'example.com')
        
        # Create consistent pseudonym for local part
        pseudonym = self.create_pseudonym(local)
        
        return f"{pseudonym}@{domain}"
    
    def anonymize_phone(self, phone: str) -> str:
        """Anonymize phone number"""
        if not phone:
            return None
        
        # Keep format but replace digits
        digits = re.findall(r'\d', phone)
        if not digits:
            return phone
        
        # Create consistent pseudonym
        pseudonym = self.create_pseudonym(''.join(digits))
        
        # Replace digits while preserving format
        result = phone
        digit_index = 0
        for i, char in enumerate(phone):
            if char.isdigit():
                if digit_index < len(pseudonym):
                    result = result[:i] + pseudonym[digit_index] + result[i+1:]
                    digit_index += 1
        
        return result
    
    def anonymize_address(self, address: str) -> str:
        """Anonymize address"""
        if not address:
            return None
        
        # Replace with fake address
        return self.fake.address().replace('\n', ', ')
    
    def anonymize_name(self, name: str) -> str:
        """Anonymize person name"""
        if not name:
            return None
        
        # Create consistent pseudonym
        pseudonym = self.create_pseudonym(name)
        
        # Generate fake name with same length pattern
        words = name.split()
        fake_words = []
        
        for word in words:
            if len(word) <= 3:
                fake_words.append(self.fake.word()[:len(word)])
            else:
                fake_name = self.fake.first_name() if len(fake_words) == 0 else self.fake.last_name()
                fake_words.append(fake_name[:len(word)])
        
        return ' '.join(fake_words)
    
    def anonymize_text(self, text: str, preserve_length: bool = True) -> str:
        """Anonymize free text while preserving structure"""
        if not text:
            return None
        
        # Replace PII patterns
        text = self._anonymize_emails_in_text(text)
        text = self._anonymize_phones_in_text(text)
        text = self._anonymize_urls_in_text(text)
        
        # Replace names (simple heuristic)
        words = text.split()
        for i, word in enumerate(words):
            # Check if it looks like a name (capitalized, not a common word)
            if word.istitle() and len(word) > 2 and word.lower() not in self._get_common_words():
                if preserve_length:
                    words[i] = 'X' * len(word)
                else:
                    words[i] = '[NAME]'
        
        return ' '.join(words)
    
    def pseudonymize_value(self, value: str, namespace: str = "default") -> str:
        """
        Create consistent pseudonym for a value
        
        Args:
            value: Original value
            namespace: Namespace for pseudonym (to avoid collisions)
            
        Returns:
            Consistent pseudonym
        """
        if not value:
            return None
        
        key = f"{namespace}:{value}"
        
        if key not in self.pseudonym_map:
            # Create hash-based pseudonym
            hash_input = value.encode() + self.salt + namespace.encode()
            hash_value = hashlib.sha256(hash_input).hexdigest()
            
            # Take first 16 characters for readability
            pseudonym = f"PS_{hash_value[:16]}"
            self.pseudonym_map[key] = pseudonym
        
        return self.pseudonym_map[key]
    
    def create_pseudonym(self, value: str) -> str:
        """Create a pseudonym that's consistent for the same input"""
        if not value:
            return None
        
        # Use HMAC for consistent pseudonymization
        import hmac
        
        hmac_obj = hmac.new(self.salt, value.encode(), hashlib.sha256)
        pseudonym = hmac_obj.hexdigest()[:12]
        
        # Ensure it starts with a letter
        return f"p{pseudonym}"
    
    def anonymize_json(self, data: Dict[str, Any], 
                      sensitive_fields: List[str] = None) -> Dict[str, Any]:
        """
        Anonymize JSON data
        
        Args:
            data: JSON data to anonymize
            sensitive_fields: List of field names to anonymize
            
        Returns:
            Anonymized JSON
        """
        if not sensitive_fields:
            sensitive_fields = ['email', 'phone', 'address', 'name', 'ssn', 
                             'credit_card', 'bank_account', 'personal_info']
        
        result = {}
        
        for key, value in data.items():
            if any(field in key.lower() for field in sensitive_fields):
                if isinstance(value, str):
                    result[key] = self.anonymize_text(value)
                elif isinstance(value, dict):
                    result[key] = self.anonymize_json(value, sensitive_fields)
                elif isinstance(value, list):
                    result[key] = [
                        self.anonymize_json(item, sensitive_fields) if isinstance(item, dict)
                        else self.anonymize_text(item) if isinstance(item, str)
                        else item
                        for item in value
                    ]
                else:
                    result[key] = '[REDACTED]'
            else:
                result[key] = value
        
        return result
    
    def _anonymize_emails_in_text(self, text: str) -> str:
        """Anonymize email addresses in text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        def replace_email(match):
            email = match.group()
            return self.anonymize_email(email)
        
        return re.sub(email_pattern, replace_email, text)
    
    def _anonymize_phones_in_text(self, text: str) -> str:
        """Anonymize phone numbers in text"""
        phone_pattern = r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'
        
        def replace_phone(match):
            phone = match.group()
            return self.anonymize_phone(phone)
        
        return re.sub(phone_pattern, replace_phone, text)
    
    def _anonymize_urls_in_text(self, text: str) -> str:
        """Anonymize URLs in text"""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        
        def replace_url(match):
            url = match.group()
            # Keep domain but anonymize path
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return f"{parsed.scheme}://{parsed.netloc}/[REDACTED]"
        
        return re.sub(url_pattern, replace_url, text)
    
    def _get_common_words(self) -> set:
        """Get list of common words to avoid anonymizing"""
        return {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'under', 'over', 'above',
            'is', 'am', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
            'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may',
            'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you',
            'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
            'my', 'your', 'his', 'her', 'its', 'our', 'their', 'mine', 'yours',
            'hers', 'ours', 'theirs', 'a', 'an', 'what', 'which', 'who', 'when',
            'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more',
            'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
            'same', 'so', 'than', 'too', 'very', 'just', 'now'
        }
    
    def generate_masked_data(self, original: str, mask_char: str = '*', 
                           visible_chars: int = 4) -> str:
        """
        Generate masked version of data
        
        Args:
            original: Original data
            mask_char: Character to use for masking
            visible_chars: Number of characters to keep visible at end
            
        Returns:
            Masked data
        """
        if not original or len(original) <= visible_chars:
            return original
        
        mask_length = len(original) - visible_chars
        return mask_char * mask_length + original[-visible_chars:]
    
    def tokenize_text(self, text: str) -> str:
        """
        Replace text with tokens while preserving structure
        
        Args:
            text: Text to tokenize
            
        Returns:
            Tokenized text
        """
        if not text:
            return None
        
        # Split into words
        words = text.split()
        tokens = []
        
        for i, word in enumerate(words):
            # Create token based on position
            token = f"TOKEN_{i}_{len(word)}"
            tokens.append(token)
        
        return ' '.join(tokens)
