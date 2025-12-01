# Email Sending via AWS SES or Local SMTP
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.utils.logger import get_logger

logger = get_logger(__name__)

class EmailService:
    @staticmethod
    def send_email(to_email: str, subject: str, body: str):
        smtp_server = os.getenv('SMTP_SERVER', 'localhost')
        smtp_port = int(os.getenv('SMTP_PORT', 25))
        from_email = os.getenv('FROM_EMAIL', 'noreply@fastapp.dev')

        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.send_message(msg)
            logger.info(f"Email sent to {to_email}")
        except Exception as e:
            logger.error(f"Email sending failed: {e}")