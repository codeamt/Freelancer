"""
Email Integration

Flattened module containing email service base class and implementations.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum


class EmailProvider(str, Enum):
    """Email service providers"""
    SES = "ses"
    SENDGRID = "sendgrid"
    MAILGUN = "mailgun"
    SMTP = "smtp"


@dataclass
class EmailMessage:
    """Email message model"""
    to_email: str
    subject: str
    body: str
    from_email: Optional[str] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    
    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []
        if self.cc is None:
            self.cc = []
        if self.bcc is None:
            self.bcc = []


@dataclass
class TemplateEmail:
    """Template email model"""
    to_email: str
    template_name: str
    template_data: Dict[str, Any]
    from_email: Optional[str] = None


@dataclass
class EmailResponse:
    """Email response model"""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    provider: Optional[str] = None


class EmailServiceBase(ABC):
    """Base class for email service implementations"""
    
    @abstractmethod
    def send_email(self, message: EmailMessage) -> EmailResponse:
        """
        Send an email.
        
        Args:
            message: Email message to send
            
        Returns:
            EmailResponse: Result of the email sending operation
        """
        pass
    
    @abstractmethod
    def send_template_email(self, template: TemplateEmail) -> EmailResponse:
        """
        Send an email using a template.
        
        Args:
            template: Template email to send
            
        Returns:
            EmailResponse: Result of the email sending operation
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
    
    @abstractmethod
    def get_provider(self) -> EmailProvider:
        """Get the email provider type"""
        pass


class MockEmailService(EmailServiceBase):
    """Mock email service for testing and development"""
    
    def __init__(self):
        self.sent_emails = []
    
    def send_email(self, message: EmailMessage) -> EmailResponse:
        """Mock send email - stores in memory"""
        self.sent_emails.append(message)
        return EmailResponse(
            success=True,
            message_id=f"mock_{len(self.sent_emails)}",
            provider="mock"
        )
    
    def send_template_email(self, template: TemplateEmail) -> EmailResponse:
        """Mock send template email"""
        message = EmailMessage(
            to_email=template.to_email,
            subject=f"Template: {template.template_name}",
            body=str(template.template_data),
            from_email=template.from_email
        )
        return self.send_email(message)
    
    def verify_email(self, email: str) -> bool:
        """Mock email verification"""
        return "@" in email and "." in email.split("@")[1]
    
    def get_provider(self) -> EmailProvider:
        return EmailProvider.SMTP  # Mock as SMTP
    
    def clear_sent_emails(self):
        """Clear stored emails (useful for testing)"""
        self.sent_emails.clear()
    
    def get_sent_emails(self) -> List[EmailMessage]:
        """Get all sent emails (useful for testing)"""
        return self.sent_emails.copy()


class SMTPEmailService(EmailServiceBase):
    """SMTP email service implementation"""
    
    def __init__(self, host: str, port: int, username: str, password: str, use_tls: bool = True):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
    
    def send_email(self, message: EmailMessage) -> EmailResponse:
        """Send email via SMTP"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.mime.base import MIMEBase
            from email import encoders
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = message.from_email or self.username
            msg['To'] = message.to_email
            msg['Subject'] = message.subject
            
            # Add body
            msg.attach(MIMEText(message.body, 'html'))
            
            # Add CC/BCC
            if message.cc:
                msg['Cc'] = ", ".join(message.cc)
            if message.bcc:
                msg['Bcc'] = ", ".join(message.bcc)
            
            # Add attachments
            for attachment in message.attachments or []:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment['content'])
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {attachment["filename"]}'
                )
                msg.attach(part)
            
            # Send email
            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                
                recipients = [message.to_email] + (message.cc or []) + (message.bcc or [])
                server.send_message(msg, to_addrs=recipients)
            
            return EmailResponse(
                success=True,
                provider="smtp"
            )
        except Exception as e:
            return EmailResponse(
                success=False,
                error=str(e),
                provider="smtp"
            )
    
    def send_template_email(self, template: TemplateEmail) -> EmailResponse:
        """Send template email via SMTP"""
        # Simple template rendering - in production, use a proper template engine
        body = self._render_template(template.template_name, template.template_data)
        
        message = EmailMessage(
            to_email=template.to_email,
            subject=f"Template: {template.template_name}",
            body=body,
            from_email=template.from_email
        )
        
        return self.send_email(message)
    
    def verify_email(self, email: str) -> bool:
        """Basic email verification"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def get_provider(self) -> EmailProvider:
        return EmailProvider.SMTP
    
    def _render_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """Simple template rendering"""
        # In production, use Jinja2 or similar
        template = f"""
        <html>
        <body>
        <h1>{template_name}</h1>
        <pre>{data}</pre>
        </body>
        </html>
        """
        return template


# Factory function
def create_email_service(provider: EmailProvider = EmailProvider.SMTP, **kwargs) -> EmailServiceBase:
    """Create an email service instance"""
    if provider == EmailProvider.SMTP:
        required_keys = ['host', 'port', 'username', 'password']
        for key in required_keys:
            if key not in kwargs:
                raise ValueError(f"Missing required parameter for SMTP: {key}")
        return SMTPEmailService(**kwargs)
    else:
        # Return mock service for other providers (to be implemented)
        return MockEmailService()


# Convenience functions
def send_email(to_email: str, subject: str, body: str, **kwargs) -> EmailResponse:
    """Convenience function to send email"""
    message = EmailMessage(
        to_email=to_email,
        subject=subject,
        body=body,
        **kwargs
    )
    service = MockEmailService()  # Default to mock
    return service.send_email(message)


def verify_email(email: str) -> bool:
    """Convenience function to verify email"""
    service = MockEmailService()
    return service.verify_email(email)


__all__ = [
    # Enums
    'EmailProvider',
    
    # Models
    'EmailMessage',
    'TemplateEmail',
    'EmailResponse',
    
    # Services
    'EmailServiceBase',
    'MockEmailService',
    'SMTPEmailService',
    
    # Factory
    'create_email_service',
    
    # Convenience
    'send_email',
    'verify_email',
]
