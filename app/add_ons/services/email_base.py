"""
Email Service Base Class

Abstract base class for email service implementations.
Implementations can use AWS SES, SendGrid, Mailgun, SMTP, etc.

Example implementations:
- SESEmailService (AWS SES)
- SendGridEmailService (SendGrid)
- MailgunEmailService (Mailgun)
- SMTPEmailService (Local SMTP)
"""
from abc import ABC, abstractmethod
from typing import Optional, List


class EmailServiceBase(ABC):
    """Base class for email service implementations"""
    
    @abstractmethod
    def send_email(
        self, 
        to_email: str, 
        subject: str, 
        body: str,
        from_email: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[dict]] = None
    ) -> bool:
        """
        Send an email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (HTML or plain text)
            from_email: Sender email (optional, uses default if not provided)
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
            attachments: List of attachment dicts with 'filename' and 'content' (optional)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def send_template_email(
        self,
        to_email: str,
        template_name: str,
        template_data: dict,
        from_email: Optional[str] = None
    ) -> bool:
        """
        Send an email using a template.
        
        Args:
            to_email: Recipient email address
            template_name: Name of the email template
            template_data: Data to populate the template
            from_email: Sender email (optional)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def verify_email(self, email: str) -> bool:
        """
        Verify an email address is valid and deliverable.
        
        Args:
            email: Email address to verify
            
        Returns:
            bool: True if email is valid, False otherwise
        """
        pass