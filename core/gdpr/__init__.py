"""
GDPR Compliance

Provides GDPR compliance features for handling personal data.
"""

from .consent_manager import ConsentManager
from .data_subject_rights import DataSubjectRights
from .anonymizer import DataAnonymizer
from .retention_manager import RetentionManager
from .cookie_consent import CookieConsent

# Note: GDPRAuditLogger has been consolidated into core.services.audit_service
# Use core.services.audit_service.get_audit_service() for GDPR audit logging

__all__ = [
    'ConsentManager',
    'DataSubjectRights',
    'DataAnonymizer',
    'RetentionManager',
    'CookieConsent'
]
