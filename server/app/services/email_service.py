"""
Centralized Platform Email Service.
Exposes reusable HTML email dispatching methods across the entire platform:
- send_otp()
- send_password_reset()
- send_welcome_email()
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config.settings import settings
from app.utils.logger import logger


class EmailService:
    """
    Centralized Email Dispatcher.
    Connects to SMTP servers (e.g., Gmail SMTP smtp.gmail.com:587) using STARTTLS and App Passwords.
    """

    @staticmethod
    def _send_email_html(to_email: str, subject: str, html_content: str) -> bool:
        """
        Sends HTML formatted email via SMTP server (Gmail, SendGrid, etc.).
        """
        clean_email = to_email.lower().strip()
        logger.info(f"📧 [EMAIL DISPATCH] To: {clean_email} | Subject: '{subject}'")

        # Resolve SMTP Server & Credentials
        smtp_host = getattr(settings, "SMTP_HOST", None) or getattr(settings, "SMTP_SERVER", None)
        smtp_port = getattr(settings, "SMTP_PORT", 587)
        smtp_user = getattr(settings, "SMTP_EMAIL", None) or getattr(settings, "SMTP_USER", None)
        raw_password = getattr(settings, "SMTP_PASSWORD", None)
        
        # Clean App Password (remove spaces if pasted like 'flrd qdhq wuis teqq')
        smtp_password = raw_password.replace(" ", "") if raw_password else None
        
        from_name = getattr(settings, "SMTP_FROM_NAME", "AI Recruitment Platform")
        from_address = getattr(settings, "FROM_EMAIL", None) or smtp_user or "noreply@airecruitment.com"
        from_header = f"{from_name} <{from_address}>"

        if not (smtp_host and smtp_user and smtp_password):
            logger.info(f"ℹ️ SMTP credentials incomplete. Simulated email delivery to {clean_email} successful.")
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = from_header
            msg["To"] = clean_email
            msg.attach(MIMEText(html_content, "html"))

            logger.info(f"Connecting to SMTP server {smtp_host}:{smtp_port} as {smtp_user}...")
            
            if smtp_port == 465:
                with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as server:
                    server.login(smtp_user, smtp_password)
                    server.sendmail(from_address, clean_email, msg.as_string())
            else:
                with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(smtp_user, smtp_password)
                    server.sendmail(from_address, clean_email, msg.as_string())

            logger.info(f"✅ Real Gmail SMTP Email delivered successfully to {clean_email}!")
            return True
        except Exception as err:
            logger.error(f"❌ Failed to dispatch SMTP email to {clean_email}: {str(err)}")
            # Raise exception so client receives clear status message if SMTP fails
            raise err

    @classmethod
    def send_otp(cls, email: str, name: str, otp_code: str, purpose: str = "REGISTER") -> bool:
        """
        Dispatches 6-digit OTP verification code HTML email.
        """
        subject = f"Your Verification Code: {otp_code} - AI Recruitment Platform"
        title_text = "Verify Your Email Address" if purpose == "REGISTER" else "Security Verification Code"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; }}
                .container {{ max-width: 560px; margin: 0 auto; background: #ffffff; border-radius: 16px; padding: 32px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
                .logo {{ font-size: 20px; font-weight: 800; color: #4f46e5; margin-bottom: 24px; }}
                .title {{ font-size: 22px; font-weight: 700; color: #0f172a; margin-bottom: 12px; }}
                .text {{ font-size: 14px; color: #475569; line-height: 1.6; margin-bottom: 24px; }}
                .otp-box {{ background: #f1f5f9; border: 2px dashed #6366f1; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 24px; }}
                .otp-code {{ font-size: 38px; font-weight: 800; letter-spacing: 8px; color: #4f46e5; font-family: monospace; }}
                .note {{ font-size: 12px; color: #94a3b8; line-height: 1.5; }}
                .footer {{ margin-top: 32px; pt: 16px; border-top: 1px solid #e2e8f0; font-size: 11px; color: #94a3b8; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">⚡ AI Recruitment Intelligence Platform</div>
                <div class="title">{title_text}</div>
                <p class="text">Hello {name or 'Recruiter'},</p>
                <p class="text">Please use the following 6-digit security code to complete your email verification. This code is valid for <strong>10 minutes</strong>.</p>
                <div class="otp-box">
                    <div class="otp-code">{otp_code}</div>
                </div>
                <p class="note">If you did not request this verification code, please ignore this email. Never share your verification code with anyone.</p>
                <div class="footer">
                    &copy; 2026 AI Recruitment Intelligence Platform. All rights reserved.
                </div>
            </div>
        </body>
        </html>
        """
        logger.info(f"🔑 [OTP DISPATCH] Email: {email} | Code: {otp_code} | Purpose: {purpose}")
        return cls._send_email_html(email, subject, html_body)

    @classmethod
    def send_password_reset(cls, email: str, name: str, otp_code: str) -> bool:
        """
        Dispatches password reset OTP email.
        """
        subject = f"Password Reset Code: {otp_code} - AI Recruitment Platform"
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; }}
                .container {{ max-width: 560px; margin: 0 auto; background: #ffffff; border-radius: 16px; padding: 32px; border: 1px solid #e2e8f0; }}
                .logo {{ font-size: 20px; font-weight: 800; color: #dc2626; margin-bottom: 24px; }}
                .title {{ font-size: 22px; font-weight: 700; color: #0f172a; margin-bottom: 12px; }}
                .text {{ font-size: 14px; color: #475569; line-height: 1.6; margin-bottom: 24px; }}
                .otp-box {{ background: #fef2f2; border: 2px dashed #ef4444; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 24px; }}
                .otp-code {{ font-size: 38px; font-weight: 800; letter-spacing: 8px; color: #dc2626; font-family: monospace; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">⚡ AI Recruitment Platform Security</div>
                <div class="title">Reset Your Recruiter Password</div>
                <p class="text">Hello {name or 'Recruiter'},</p>
                <p class="text">We received a request to reset your password. Enter the 6-digit code below to set your new password. Valid for <strong>10 minutes</strong>.</p>
                <div class="otp-box">
                    <div class="otp-code">{otp_code}</div>
                </div>
                <p class="text" style="font-size: 12px; color: #64748b;">If you did not request a password reset, your account is safe and no further action is required.</p>
            </div>
        </body>
        </html>
        """
        logger.info(f"🔑 [RESET OTP] Email: {email} | Code: {otp_code}")
        return cls._send_email_html(email, subject, html_body)

    @classmethod
    def send_welcome_email(cls, email: str, name: str) -> bool:
        """
        Dispatches welcome email after successful recruiter account verification.
        """
        subject = "Welcome to AI Recruitment Platform - Recruiter Account Verified!"
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; }}
                .container {{ max-width: 560px; margin: 0 auto; background: #ffffff; border-radius: 16px; padding: 32px; border: 1px solid #e2e8f0; }}
                .logo {{ font-size: 20px; font-weight: 800; color: #4f46e5; margin-bottom: 24px; }}
                .title {{ font-size: 22px; font-weight: 700; color: #0f172a; margin-bottom: 12px; }}
                .text {{ font-size: 14px; color: #475569; line-height: 1.6; margin-bottom: 24px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">⚡ AI Recruitment Platform</div>
                <div class="title">Welcome, {name}!</div>
                <p class="text">Your recruiter account has been successfully verified.</p>
                <p class="text">You can now sign in to your Recruiter Workspace and complete your Company Profile setup.</p>
            </div>
        </body>
        </html>
        """
        return cls._send_email_html(email, subject, html_body)
