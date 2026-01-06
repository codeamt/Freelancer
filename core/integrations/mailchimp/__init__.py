"""
Mailchimp Integration

Provides Mailchimp API integration for email marketing campaigns,
audience management, and automation.
"""

from .client import MailchimpClient, MailchimpConfig, Contact, Campaign, Audience

__all__ = [
    'MailchimpClient',
    'MailchimpConfig',
    'Contact',
    'Campaign', 
    'Audience'
]
