"""
Email Service for QualCheck
Handles SMTP email sending for account creation, password reset, and notifications
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


class EmailService:
    """SMTP email service for QualCheck"""
    
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_email = os.getenv("SMTP_EMAIL")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.smtp_from_name = os.getenv("SMTP_FROM_NAME", "QualCheck")
        self.use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        
        # Validate configuration
        if not all([self.smtp_host, self.smtp_email, self.smtp_password]):
            print("Warning: SMTP configuration incomplete. Email sending may fail.")
    
    def _create_message(self, to_email: str, subject: str, body: str, html: bool = False) -> MIMEMultipart:
        """Create email message with proper headers"""
        msg = MIMEMultipart('alternative')
        msg['From'] = formataddr((self.smtp_from_name, self.smtp_email))
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Attach body
        mime_type = 'html' if html else 'plain'
        msg.attach(MIMEText(body, mime_type))
        
        return msg
    
    def _send_smtp(self, msg: MIMEMultipart, to_email: str) -> bool:
        """Send email via SMTP"""
        try:
            if self.use_tls:
                context = ssl.create_default_context()
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls(context=context)
                    server.login(self.smtp_email, self.smtp_password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.login(self.smtp_email, self.smtp_password)
                    server.send_message(msg)
            
            print(f"Email sent successfully to {to_email}")
            return True
        except Exception as e:
            print(f"Email send failed to {to_email}: {e}")
            return False
    
    def send_email(self, to_email: str, subject: str, body: str, html: bool = False) -> bool:
        """
        Send a generic email
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body content
            html: Whether body is HTML (True) or plain text (False)
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            msg = self._create_message(to_email, subject, body, html)
            return self._send_smtp(msg, to_email)
        except Exception as e:
            print(f"Failed to create/send email: {e}")
            return False
    
    def send_password_reset(self, to_email: str, reset_link: str, user_name: str = "", reset_code: str = "") -> bool:
        """
        Send password reset email
        
        Args:
            to_email: Recipient email address
            reset_link: Unused - kept for backward compatibility with callers
            user_name: Optional user name for personalization
            reset_code: 6-digit reset code
        
        Returns:
            bool: True if email sent successfully
        """
        subject = "QualCheck - Password Reset Request"
        
        greeting = f"Hello {user_name}," if user_name else "Hello,"
        
        # Add access code if provided
        code_section = ""
        if reset_code:
            code_section = f"""
                    <p>Use this 6-digit reset code in the application:</p>
                    <div class="password-box">{reset_code}</div>
            """
        
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1e3a8a; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9fafb; padding: 30px; border-radius: 8px; }}
                .password-box {{ 
                    background-color: #e5e7eb; 
                    padding: 15px; 
                    border-radius: 6px; 
                    text-align: center;
                    font-family: monospace;
                    font-size: 16px;
                    margin: 20px 0;
                }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>QualCheck</h1>
                </div>
                <div class="content">
                    <p>{greeting}</p>
                    <p>We received a request to reset your password for your QualCheck account.</p>
                    {code_section}
                    <p><strong>This code expires in 5 minutes.</strong></p>
                    <p>If you didn't request this password reset, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>&copy; 2026 QualCheck. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, body, html=True)
    
    def send_welcome_email(self, to_email: str, user_name: str, temporary_password: str, login_url: str = "", access_code: str = "") -> bool:
        """
        Send welcome email with account credentials
        
        Args:
            to_email: Recipient email address
            user_name: User's name
            temporary_password: Temporary password for first login
            login_url: Unused - kept for backward compatibility with callers
            access_code: 6-digit access code for the user
        
        Returns:
            bool: True if email sent successfully
        """
        subject = "Welcome to QualCheck - Your Account is Ready"
        
        # Build credentials section
        credentials_section = f"""
                    <h3>Your Account Details:</h3>
                    <p><strong>Email:</strong> {to_email}</p>
        """
        
        # Add access code if provided
        if access_code:
            credentials_section += f"""
                    <p><strong>6-Digit Access Code:</strong></p>
                    <div class="password-box">{access_code}</div>
            """
        
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1e3a8a; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9fafb; padding: 30px; border-radius: 8px; }}
                .password-box {{ 
                    background-color: #e5e7eb; 
                    padding: 15px; 
                    border-radius: 6px; 
                    text-align: center;
                    font-family: monospace;
                    font-size: 16px;
                    margin: 20px 0;
                }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>QualCheck</h1>
                </div>
                <div class="content">
                    <p>Hello {user_name},</p>
                    <p>Welcome to QualCheck! Your account has been successfully created.</p>
                    
                    {credentials_section}
                    
                    <p><strong>Important:</strong></p>
                    <ul>
                        <li>Keep your credentials secure</li>
                        <li>Contact support if you have any issues</li>
                    </ul>
                </div>
                <div class="footer">
                    <p>&copy; 2024 QualCheck. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, body, html=True)
    
    def send_notification(self, to_email: str, user_name: str, notification_type: str, details: str = "") -> bool:
        """
        Send notification email
        
        Args:
            to_email: Recipient email address
            user_name: User's name
            notification_type: Type of notification
            details: Additional notification details
        
        Returns:
            bool: True if email sent successfully
        """
        subject = f"QualCheck - {notification_type}"
        
        greeting = f"Hello {user_name}," if user_name else "Hello,"
        
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1e3a8a; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9fafb; padding: 30px; border-radius: 8px; }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>QualCheck</h1>
                </div>
                <div class="content">
                    <p>{greeting}</p>
                    <h3>{notification_type}</h3>
                    <p>{details}</p>
                    <p>Please log in to your QualCheck account for more information.</p>
                </div>
                <div class="footer">
                    <p>&copy; 2024 QualCheck. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, body, html=True)
    
    def send_admin_notification(self, to_email: str, notification_type: str, details: str = "") -> bool:
        """
        Send admin notification email
        
        Args:
            to_email: Admin email address
            notification_type: Type of notification
            details: Additional notification details
        
        Returns:
            bool: True if email sent successfully
        """
        subject = f"QualCheck Admin - {notification_type}"
        
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #dc2626; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9fafb; padding: 30px; border-radius: 8px; }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>QualCheck Admin</h1>
                </div>
                <div class="content">
                    <h3>{notification_type}</h3>
                    <p>{details}</p>
                    <p>Please review this in your admin dashboard.</p>
                </div>
                <div class="footer">
                    <p>&copy; 2024 QualCheck. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, body, html=True)


# Global email service instance
_email_service = None

def get_email_service() -> EmailService:
    """Get or create the email service singleton"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service