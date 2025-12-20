"""Base Email Service - Abstract Base Class"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from enum import Enum


class EmailPriority(Enum):
    """Email priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class BaseEmailService(ABC):
    """
    Abstract base class for email services.
    Add-ons can extend this to implement custom email logic
    with templates, providers, and tracking.
    """

    @abstractmethod
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        reply_to: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        priority: EmailPriority = EmailPriority.NORMAL
    ) -> bool:
        """
        Send a plain text or HTML email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (HTML or plain text)
            from_email: Optional sender email (uses default if not provided)
            reply_to: Optional reply-to address
            cc: Optional CC recipients
            bcc: Optional BCC recipients
            priority: Email priority level
            
        Returns:
            True if sent successfully, False otherwise
        """
        pass

    @abstractmethod
    def send_template_email(
        self,
        to_email: str,
        template_name: str,
        context: Dict[str, Any],
        from_email: Optional[str] = None,
        subject: Optional[str] = None
    ) -> bool:
        """
        Send an email using a template.
        
        Args:
            to_email: Recipient email address
            template_name: Name of email template
            context: Template context variables
            from_email: Optional sender email
            subject: Optional subject (if not in template)
            
        Returns:
            True if sent successfully, False otherwise
        """
        pass

    @abstractmethod
    def send_bulk_email(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        batch_size: int = 50
    ) -> Dict[str, int]:
        """
        Send bulk emails to multiple recipients.
        
        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            body: Email body
            from_email: Optional sender email
            batch_size: Number of emails per batch
            
        Returns:
            Dict with 'sent' and 'failed' counts
        """
        pass

    @abstractmethod
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render an email template with context.
        
        Args:
            template_name: Name of template
            context: Template variables
            
        Returns:
            Rendered HTML string
        """
        pass

    @abstractmethod
    def validate_email(self, email: str) -> bool:
        """
        Validate email address format.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass

    @abstractmethod
    def get_template_path(self, template_name: str) -> str:
        """
        Get the full path to an email template.
        Add-ons can organize templates in their own directories.
        
        Args:
            template_name: Name of template
            
        Returns:
            Full template path
        """
        pass

    # Optional tracking methods
    def track_email_sent(
        self,
        to_email: str,
        subject: str,
        template_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Track that an email was sent (for analytics).
        Default implementation does nothing - override to enable tracking.
        
        Args:
            to_email: Recipient email
            subject: Email subject
            template_name: Optional template name
            metadata: Optional metadata
        """
        pass

    def track_email_opened(self, email_id: str):
        """
        Track that an email was opened.
        Default implementation does nothing - override to enable tracking.
        
        Args:
            email_id: Unique email identifier
        """
        pass

    def track_email_clicked(self, email_id: str, link_url: str):
        """
        Track that a link in an email was clicked.
        Default implementation does nothing - override to enable tracking.
        
        Args:
            email_id: Unique email identifier
            link_url: URL that was clicked
        """
        pass

    @abstractmethod
    def get_default_from_email(self) -> str:
        """
        Get the default sender email address for this module.
        
        Returns:
            Default from email address
        """
        pass
