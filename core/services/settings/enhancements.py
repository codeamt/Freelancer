"""
Settings Service Enhancements - Caching, Versioning, and Validation

This module enhances the existing SettingsService with:
- Intelligent caching layer
- Version tracking and rollback
- Enhanced validation system
- Performance optimizations

These enhancements are designed to work with the existing settings architecture
without breaking current functionality.
"""

import asyncio
import json
import hashlib
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from core.utils.cache import cache
from core.utils.logger import get_logger
from .service import settings_service
from .registry import settings_registry, SettingDefinition, SettingType, SettingSensitivity

logger = get_logger(__name__)


# ============================================================================
# Enhanced Data Classes
# ============================================================================

@dataclass
class SettingVersion:
    """Version information for a setting"""
    version_id: str
    key: str
    value: Any
    previous_value: Optional[Any]
    changed_by: str
    changed_at: datetime
    change_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version_id": self.version_id,
            "key": self.key,
            "value": self.value,
            "previous_value": self.previous_value,
            "changed_by": self.changed_by,
            "changed_at": self.changed_at.isoformat(),
            "change_reason": self.change_reason,
            "metadata": self.metadata
        }


@dataclass
class ValidationResult:
    """Enhanced validation result"""
    is_valid: bool
    error_message: Optional[str] = None
    warning_message: Optional[str] = None
    normalized_value: Optional[Any] = None
    validation_rules_applied: List[str] = field(default_factory=list)


class ValidationRule(Enum):
    """Built-in validation rules"""
    REQUIRED = "required"
    TYPE_CHECK = "type_check"
    RANGE_CHECK = "range_check"
    PATTERN_CHECK = "pattern_check"
    LENGTH_CHECK = "length_check"
    CUSTOM_VALIDATOR = "custom_validator"
    SECURITY_CHECK = "security_check"
    BUSINESS_RULE = "business_rule"


# ============================================================================
# Enhanced Settings Service
# ============================================================================

class EnhancedSettingsService:
    """
    Enhanced settings service with caching, versioning, and validation.
    
    This class wraps the existing SettingsService to add advanced features
    while maintaining backward compatibility.
    """
    
    def __init__(self, base_service=None):
        self.base_service = base_service or settings_service
        self.cache = {}
        self.cache_ttl = {
            "default": timedelta(minutes=15),
            "static": timedelta(hours=1),
            "user": timedelta(minutes=30),
            "sensitive": timedelta(minutes=5)
        }
        
        # Version tracking
        self.versions = {}  # key -> list[SettingVersion]
        self.version_history_limit = 50
        
        # Validation rules registry
        self.validation_rules = {}
        self._register_builtin_validation_rules()
        
        # Performance metrics
        self.metrics = {
            "cache_hits": 0,
            "cache_misses": 0,
            "validations": 0,
            "version_creations": 0,
            "rollbacks": 0
        }
    
    # ========================================================================
    # Enhanced Get Operations with Caching
    # ========================================================================
    
    async def get_setting_cached(
        self,
        key: str,
        user_roles: List[str],
        context: Optional[Dict[str, Any]] = None,
        decrypt: bool = False,
        use_cache: bool = True,
        cache_ttl: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """
        Get setting with intelligent caching.
        
        Args:
            key: Setting key
            user_roles: User roles
            context: Context for scoping
            decrypt: Whether to decrypt encrypted values
            use_cache: Whether to use cache
            cache_ttl: Custom cache TTL
            
        Returns:
            Enhanced result with caching metadata
        """
        cache_key = self._generate_cache_key(key, user_roles, context, decrypt)
        
        # Check cache first
        if use_cache and cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if not self._is_cache_expired(cache_entry):
                self.metrics["cache_hits"] += 1
                return {
                    **cache_entry["data"],
                    "cached": True,
                    "cache_hit": True
                }
            else:
                # Remove expired entry
                del self.cache[cache_key]
        
        self.metrics["cache_misses"] += 1
        
        # Get from base service
        result = await self.base_service.get_setting(
            key=key,
            user_roles=user_roles,
            context=context,
            decrypt=decrypt
        )
        
        # Cache the result
        if use_cache and result["success"]:
            ttl = cache_ttl or self._determine_cache_ttl(key, result)
            self.cache[cache_key] = {
                "data": result,
                "cached_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + ttl
            }
        
        return {
            **result,
            "cached": False,
            "cache_hit": False
        }
    
    async def get_settings_batch_cached(
        self,
        keys: List[str],
        user_roles: List[str],
        context: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get multiple settings with batch optimization and caching.
        """
        results = {}
        
        # Separate cached and uncached keys
        cached_results = {}
        uncached_keys = []
        
        if use_cache:
            for key in keys:
                cache_key = self._generate_cache_key(key, user_roles, context, False)
                if cache_key in self.cache and not self._is_cache_expired(self.cache[cache_key]):
                    cached_results[key] = {
                        **self.cache[cache_key]["data"],
                        "cached": True,
                        "cache_hit": True
                    }
                    self.metrics["cache_hits"] += 1
                else:
                    uncached_keys.append(key)
        else:
            uncached_keys = keys
        
        # Batch fetch uncached settings
        if uncached_keys:
            batch_results = await self._batch_get_settings(uncached_keys, user_roles, context)
            
            # Cache the batch results
            for key, result in batch_results.items():
                if result["success"] and use_cache:
                    cache_key = self._generate_cache_key(key, user_roles, context, False)
                    ttl = self._determine_cache_ttl(key, result)
                    self.cache[cache_key] = {
                        "data": result,
                        "cached_at": datetime.utcnow(),
                        "expires_at": datetime.utcnow() + ttl
                    }
        
        # Combine results
        results.update(cached_results)
        results.update(batch_results)
        
        return results
    
    # ========================================================================
    # Enhanced Set Operations with Versioning
    # ========================================================================
    
    async def set_setting_with_version(
        self,
        key: str,
        value: Any,
        user_roles: List[str],
        context: Optional[Dict[str, Any]] = None,
        encrypt: bool = False,
        change_reason: Optional[str] = None,
        changed_by: Optional[str] = None,
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        Set setting with version tracking and enhanced validation.
        
        Args:
            key: Setting key
            value: Setting value
            user_roles: User roles
            context: Context
            encrypt: Whether to encrypt
            change_reason: Reason for change
            changed_by: Who made the change
            validate: Whether to validate
            
        Returns:
            Enhanced result with version information
        """
        # Enhanced validation
        if validate:
            validation_result = await self.validate_setting_value(key, value, context)
            if not validation_result.is_valid:
                return {
                    "success": False,
                    "error": f"Validation failed: {validation_result.error_message}",
                    "validation_warnings": validation_result.warning_message
                }
            
            # Use normalized value if provided
            if validation_result.normalized_value is not None:
                value = validation_result.normalized_value
        
        # Get current value for version tracking
        current_result = await self.base_service.get_setting(
            key=key,
            user_roles=user_roles,
            context=context,
            decrypt=True
        )
        
        current_value = current_result.get("value") if current_result["success"] else None
        
        # Set the value
        set_result = await self.base_service.set_setting(
            key=key,
            value=value,
            user_roles=user_roles,
            context=context,
            encrypt=encrypt
        )
        
        if set_result["success"]:
            # Create version record
            version = SettingVersion(
                version_id=self._generate_version_id(),
                key=key,
                value=value,
                previous_value=current_value,
                changed_by=changed_by or "system",
                changed_at=datetime.utcnow(),
                change_reason=change_reason,
                metadata={
                    "user_roles": user_roles,
                    "context": context,
                    "encrypt": encrypt
                }
            )
            
            await self._add_version(version)
            
            # Invalidate cache
            await self._invalidate_key_cache(key)
            
            self.metrics["version_creations"] += 1
            
            return {
                **set_result,
                "version_id": version.version_id,
                "previous_value": current_value,
                "change_reason": change_reason
            }
        
        return set_result
    
    # ========================================================================
    # Version Management
    # ========================================================================
    
    async def get_setting_history(
        self,
        key: str,
        user_roles: List[str],
        context: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get version history for a setting.
        """
        if key not in self.versions:
            return {
                "success": True,
                "history": [],
                "total": 0
            }
        
        # Check permissions
        current_result = await self.base_service.get_setting(key, user_roles, context)
        if not current_result["success"]:
            return {
                "success": False,
                "error": "Permission denied or setting not found"
            }
        
        history = self.versions[key][-limit:]  # Get most recent versions
        return {
            "success": True,
            "history": [version.to_dict() for version in history],
            "total": len(self.versions[key])
        }
    
    async def rollback_setting(
        self,
        key: str,
        version_id: str,
        user_roles: List[str],
        context: Optional[Dict[str, Any]] = None,
        changed_by: Optional[str] = None,
        change_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Rollback a setting to a specific version.
        """
        if key not in self.versions:
            return {
                "success": False,
                "error": "No version history found for setting"
            }
        
        # Find the target version
        target_version = None
        for version in self.versions[key]:
            if version.version_id == version_id:
                target_version = version
                break
        
        if not target_version:
            return {
                "success": False,
                "error": "Version not found"
            }
        
        # Rollback to the target version value
        rollback_result = await self.set_setting_with_version(
            key=key,
            value=target_version.value,
            user_roles=user_roles,
            context=context,
            change_reason=change_reason or f"Rollback to version {version_id}",
            changed_by=changed_by or "system",
            validate=False  # Skip validation for rollback
        )
        
        if rollback_result["success"]:
            self.metrics["rollbacks"] += 1
            rollback_result["rollback_version_id"] = version_id
        
        return rollback_result
    
    # ========================================================================
    # Enhanced Validation System
    # ========================================================================
    
    async def validate_setting_value(
        self,
        key: str,
        value: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Enhanced validation with multiple rule types.
        """
        definition = settings_registry.get(key)
        if not definition:
            return ValidationResult(
                is_valid=False,
                error_message="Setting definition not found"
            )
        
        applied_rules = []
        warnings = []
        
        # 1. Required check
        if definition.required and (value is None or value == ""):
            return ValidationResult(
                is_valid=False,
                error_message="This setting is required",
                validation_rules_applied=[ValidationRule.REQUIRED.value]
            )
        applied_rules.append(ValidationRule.REQUIRED.value)
        
        # Skip further validation if value is empty and not required
        if value is None or value == "":
            return ValidationResult(
                is_valid=True,
                validation_rules_applied=applied_rules
            )
        
        # 2. Type validation
        type_result = self._validate_type(definition.type, value)
        if not type_result["valid"]:
            return ValidationResult(
                is_valid=False,
                error_message=type_result["error"],
                validation_rules_applied=applied_rules + [ValidationRule.TYPE_CHECK.value]
            )
        applied_rules.append(ValidationRule.TYPE_CHECK.value)
        
        # Use normalized type value if provided
        if "normalized" in type_result:
            value = type_result["normalized"]
        
        # 3. Custom validator
        if definition.validation:
            custom_result = await self._run_custom_validator(definition.validation, value, context)
            if not custom_result["valid"]:
                return ValidationResult(
                    is_valid=False,
                    error_message=custom_result["error"],
                    warning_message=custom_result.get("warning"),
                    validation_rules_applied=applied_rules + [ValidationRule.CUSTOM_VALIDATOR.value]
                )
            applied_rules.append(ValidationRule.CUSTOM_VALIDATOR.value)
            
            if "warning" in custom_result:
                warnings.append(custom_result["warning"])
        
        # 4. Security validation
        security_result = self._validate_security(definition.sensitivity, value)
        if not security_result["valid"]:
            return ValidationResult(
                is_valid=False,
                error_message=security_result["error"],
                validation_rules_applied=applied_rules + [ValidationRule.SECURITY_CHECK.value]
            )
        applied_rules.append(ValidationRule.SECURITY_CHECK.value)
        
        # 5. Business rules (if any registered)
        business_result = await self._validate_business_rules(key, value, context)
        if not business_result["valid"]:
            return ValidationResult(
                is_valid=False,
                error_message=business_result["error"],
                validation_rules_applied=applied_rules + [ValidationRule.BUSINESS_RULE.value]
            )
        applied_rules.append(ValidationRule.BUSINESS_RULE.value)
        
        return ValidationResult(
            is_valid=True,
            warning_message="; ".join(warnings) if warnings else None,
            normalized_value=value,
            validation_rules_applied=applied_rules
        )
    
    def register_validation_rule(
        self,
        rule_name: str,
        validator: Callable[[str, Any, Optional[Dict]], Dict[str, Any]]
    ):
        """Register a custom validation rule"""
        self.validation_rules[rule_name] = validator
        logger.info(f"Registered validation rule: {rule_name}")
    
    # ========================================================================
    # Cache Management
    # ========================================================================
    
    async def clear_cache(self, pattern: Optional[str] = None):
        """
        Clear settings cache.
        
        Args:
            pattern: Optional pattern to clear selective cache entries
        """
        if pattern:
            # Clear cache entries matching pattern
            keys_to_remove = [
                key for key in self.cache.keys()
                if pattern in key
            ]
            for key in keys_to_remove:
                del self.cache[key]
            logger.info(f"Cleared {len(keys_to_remove)} cache entries matching pattern: {pattern}")
        else:
            # Clear all cache
            cache_size = len(self.cache)
            self.cache.clear()
            logger.info(f"Cleared all settings cache ({cache_size} entries)")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        hit_rate = (self.metrics["cache_hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_size": len(self.cache),
            "cache_hits": self.metrics["cache_hits"],
            "cache_misses": self.metrics["cache_misses"],
            "hit_rate": round(hit_rate, 2),
            "total_requests": total_requests
        }
    
    # ========================================================================
    # Performance Metrics
    # ========================================================================
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        return {
            "cache_stats": self.get_cache_stats(),
            "validation_stats": {
                "total_validations": self.metrics["validations"]
            },
            "version_stats": {
                "total_versions": sum(len(versions) for versions in self.versions.values()),
                "version_creations": self.metrics["version_creations"],
                "rollbacks": self.metrics["rollbacks"]
            },
            "settings_with_versions": len(self.versions)
        }
    
    # ========================================================================
    # Private Methods
    # ========================================================================
    
    def _generate_cache_key(
        self,
        key: str,
        user_roles: List[str],
        context: Optional[Dict[str, Any]],
        decrypt: bool
    ) -> str:
        """Generate cache key"""
        cache_data = {
            "key": key,
            "roles": sorted(user_roles),
            "context": context or {},
            "decrypt": decrypt
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return f"enhanced_setting:{hashlib.md5(cache_str.encode()).hexdigest()}"
    
    def _is_cache_expired(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired"""
        return datetime.utcnow() > cache_entry["expires_at"]
    
    def _determine_cache_ttl(self, key: str, result: Dict[str, Any]) -> timedelta:
        """Determine cache TTL based on setting characteristics"""
        # Sensitive settings have shorter TTL
        if result.get("sensitive") == SettingSensitivity.SECRET.value:
            return self.cache_ttl["sensitive"]
        
        # User-specific settings have moderate TTL
        if "user" in key:
            return self.cache_ttl["user"]
        
        # Static settings have longer TTL
        if result.get("source") == "static":
            return self.cache_ttl["static"]
        
        return self.cache_ttl["default"]
    
    async def _batch_get_settings(
        self,
        keys: List[str],
        user_roles: List[str],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Batch fetch settings from base service"""
        results = {}
        
        # Use asyncio.gather for parallel requests
        tasks = [
            self.base_service.get_setting(key, user_roles, context)
            for key in keys
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        for key, response in zip(keys, responses):
            if isinstance(response, Exception):
                results[key] = {
                    "success": False,
                    "error": str(response)
                }
            else:
                results[key] = response
        
        return results
    
    def _generate_version_id(self) -> str:
        """Generate unique version ID"""
        return f"v_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hashlib.uuid4().hex[:8]}"
    
    async def _add_version(self, version: SettingVersion):
        """Add version to history"""
        if version.key not in self.versions:
            self.versions[version.key] = []
        
        self.versions[version.key].append(version)
        
        # Limit history size
        if len(self.versions[version.key]) > self.version_history_limit:
            self.versions[version.key] = self.versions[version.key][-self.version_history_limit:]
    
    async def _invalidate_key_cache(self, key: str):
        """Invalidate all cache entries for a key"""
        keys_to_remove = [
            cache_key for cache_key in self.cache.keys()
            if key in cache_key
        ]
        
        for cache_key in keys_to_remove:
            del self.cache[cache_key]
    
    # ========================================================================
    # Validation Methods
    # ========================================================================
    
    def _register_builtin_validation_rules(self):
        """Register built-in validation rules"""
        
        def validate_url(key: str, value: Any, context: Optional[Dict]) -> Dict[str, Any]:
            """Validate URL format"""
            if "url" in key.lower() and value:
                import re
                url_pattern = re.compile(
                    r'^https?://'  # http:// or https://
                    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
                    r'localhost|'  # localhost...
                    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                    r'(?::\d+)?'  # optional port
                    r'(?:/?|[/?]\S+)$', re.IGNORECASE)
                
                if not url_pattern.match(value):
                    return {"valid": False, "error": "Invalid URL format"}
            
            return {"valid": True}
        
        def validate_email(key: str, value: Any, context: Optional[Dict]) -> Dict[str, Any]:
            """Validate email format"""
            if "email" in key.lower() and value:
                import re
                email_pattern = re.compile(r'^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$', re.IGNORECASE)
                
                if not email_pattern.match(value):
                    return {"valid": False, "error": "Invalid email format"}
            
            return {"valid": True}
        
        def validate_port(key: str, value: Any, context: Optional[Dict]) -> Dict[str, Any]:
            """Validate port number"""
            if "port" in key.lower() and value is not None:
                try:
                    port = int(value)
                    if not (1 <= port <= 65535):
                        return {"valid": False, "error": "Port must be between 1 and 65535"}
                except ValueError:
                    return {"valid": False, "error": "Port must be a number"}
            
            return {"valid": True}
        
        # Register built-in rules
        self.register_validation_rule("url", validate_url)
        self.register_validation_rule("email", validate_email)
        self.register_validation_rule("port", validate_port)
    
    def _validate_type(self, setting_type: SettingType, value: Any) -> Dict[str, Any]:
        """Validate and normalize setting type"""
        try:
            if setting_type == SettingType.BOOLEAN:
                if isinstance(value, str):
                    normalized = value.lower() in ('true', '1', 'yes', 'on')
                    return {"valid": True, "normalized": normalized}
                return {"valid": bool(isinstance(value, bool))}
            
            elif setting_type == SettingType.INTEGER:
                normalized = int(value)
                return {"valid": True, "normalized": normalized}
            
            elif setting_type == SettingType.JSON:
                if isinstance(value, str):
                    json.loads(value)  # Validate JSON
                elif not isinstance(value, (dict, list)):
                    return {"valid": False, "error": "JSON must be object or array"}
                return {"valid": True}
            
            elif setting_type == SettingType.ARRAY:
                if isinstance(value, str):
                    normalized = value.split(',')
                    return {"valid": True, "normalized": normalized}
                elif not isinstance(value, list):
                    return {"valid": False, "error": "Array must be a list"}
                return {"valid": True}
            
            # STRING and ENCRYPTED types accept any value
            return {"valid": True}
        
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            return {"valid": False, "error": f"Type validation failed: {str(e)}"}
    
    async def _run_custom_validator(
        self,
        validator: Callable,
        value: Any,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Run custom validator function"""
        try:
            if asyncio.iscoroutinefunction(validator):
                result = await validator(value, context)
            else:
                result = validator(value, context)
            
            if isinstance(result, bool):
                return {"valid": result}
            elif isinstance(result, dict) and "valid" in result:
                return result
            else:
                return {"valid": bool(result)}
        
        except Exception as e:
            return {"valid": False, "error": f"Custom validator error: {str(e)}"}
    
    def _validate_security(self, sensitivity: SettingSensitivity, value: Any) -> Dict[str, Any]:
        """Validate security constraints"""
        if sensitivity == SettingSensitivity.SECRET:
            # Secret values should not be too short or common
            if isinstance(value, str):
                if len(value) < 8:
                    return {"valid": False, "error": "Secret values must be at least 8 characters"}
                
                # Check for common weak secrets
                weak_secrets = ["password", "123456", "admin", "secret", "changeme"]
                if value.lower() in weak_secrets:
                    return {"valid": False, "error": "Secret value is too common"}
        
        return {"valid": True}
    
    async def _validate_business_rules(
        self,
        key: str,
        value: Any,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate business rules"""
        # Apply registered validation rules
        for rule_name, validator in self.validation_rules.items():
            try:
                result = await self._run_custom_validator(validator, key, context)
                if not result["valid"]:
                    return result
            except Exception as e:
                logger.warning(f"Validation rule {rule_name} failed: {e}")
        
        return {"valid": True}


# ============================================================================
# Global Enhanced Instance
# ============================================================================

enhanced_settings = EnhancedSettingsService()


# ============================================================================
# Convenience Functions
# ============================================================================

async def get_setting_cached(
    key: str,
    user_roles: List[str],
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Get setting with caching"""
    return await enhanced_settings.get_setting_cached(key, user_roles, context)


async def set_setting_with_version(
    key: str,
    value: Any,
    user_roles: List[str],
    context: Optional[Dict[str, Any]] = None,
    change_reason: Optional[str] = None
) -> Dict[str, Any]:
    """Set setting with version tracking"""
    return await enhanced_settings.set_setting_with_version(
        key, value, user_roles, context, change_reason=change_reason
    )


async def get_setting_history(
    key: str,
    user_roles: List[str],
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Get setting version history"""
    return await enhanced_settings.get_setting_history(key, user_roles, context)


__all__ = [
    "EnhancedSettingsService",
    "enhanced_settings",
    "SettingVersion",
    "ValidationResult",
    "ValidationRule",
    "get_setting_cached",
    "set_setting_with_version",
    "get_setting_history"
]
