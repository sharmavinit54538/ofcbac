import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config.settings import settings
from app.core.logging import logger


class EmailService:
    @staticmethod
    def _send_email_sync(to_email: str, subject: str, html_content: str) -> bool:
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            logger.warning(
                f"SMTP_USER/SMTP_PASSWORD not set in environment. Skipping email dispatch to {to_email}. "
                f"Subject: {subject}"
            )
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
            msg["To"] = to_email

            html_part = MIMEText(html_content, "html")
            msg.attach(html_part)

            if settings.SMTP_PORT == 465:
                with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.sendmail(settings.EMAILS_FROM_EMAIL, [to_email], msg.as_string())
            else:
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                    server.starttls()
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.sendmail(settings.EMAILS_FROM_EMAIL, [to_email], msg.as_string())

            logger.info(f"Email sent successfully to {to_email}. Subject: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    @classmethod
    async def send_verification_email(cls, to_email: str, first_name: str, otp_code: str) -> bool:
        subject = "OFC HR - Verify Your Email Address"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; margin: 0; padding: 20px; }}
                .card {{ max-width: 500px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }}
                .header {{ text-align: center; border-bottom: 2px solid #4F46E5; padding-bottom: 15px; margin-bottom: 20px; }}
                .header h1 {{ color: #4F46E5; font-size: 24px; margin: 0; }}
                .otp-box {{ background: #EEF2FF; border: 2px dashed #4F46E5; border-radius: 8px; text-align: center; padding: 15px; margin: 25px 0; font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #4F46E5; }}
                .footer {{ text-align: center; color: #6B7280; font-size: 12px; margin-top: 25px; }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="header">
                    <h1>OFC HR Platform</h1>
                </div>
                <p>Hello <strong>{first_name}</strong>,</p>
                <p>Welcome to OFC HR! Please use the 6-digit email verification code below to verify your account:</p>
                
                <div class="otp-box">{otp_code}</div>
                
                <p>This code will expire in <strong>15 minutes</strong>. If you did not register for an account, please ignore this email.</p>
                
                <div class="footer">
                    <p>&copy; 2026 OFC HR Enterprise Platform. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return await asyncio.to_thread(cls._send_email_sync, to_email, subject, html_content)

    @classmethod
    async def send_password_reset_email(cls, to_email: str, first_name: str, reset_token: str) -> bool:
        subject = "OFC HR - Reset Your Password"
        reset_url = f"{settings.ALLOWED_ORIGINS[0]}/reset-password?token={reset_token}"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; margin: 0; padding: 20px; }}
                .card {{ max-width: 500px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }}
                .header {{ text-align: center; border-bottom: 2px solid #EF4444; padding-bottom: 15px; margin-bottom: 20px; }}
                .header h1 {{ color: #EF4444; font-size: 24px; margin: 0; }}
                .btn {{ display: block; width: 200px; margin: 25px auto; padding: 12px; background: #EF4444; color: #ffffff; text-align: center; text-decoration: none; border-radius: 6px; font-weight: bold; }}
                .footer {{ text-align: center; color: #6B7280; font-size: 12px; margin-top: 25px; }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>
                <p>Hello <strong>{first_name}</strong>,</p>
                <p>We received a request to reset your OFC HR password. Click the button below to proceed:</p>
                
                <a href="{reset_url}" class="btn">Reset Password</a>
                
                <p style="word-break: break-all; font-size: 12px; color: #6B7280;">Token: {reset_token}</p>
                <p>This password reset token will expire in <strong>1 hour</strong>.</p>
                
                <div class="footer">
                    <p>&copy; 2026 OFC HR Enterprise Platform. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return await asyncio.to_thread(cls._send_email_sync, to_email, subject, html_content)
