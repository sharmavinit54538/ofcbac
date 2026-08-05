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
        subject = f"{otp_code} is your OFC HR email verification code"
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>OFC HR Verification</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                    background-color: #F8FAFC;
                    margin: 0;
                    padding: 0;
                    -webkit-font-smoothing: antialiased;
                }}
                .wrapper {{
                    width: 100%;
                    table-layout: fixed;
                    background-color: #F8FAFC;
                    padding: 40px 0;
                }}
                .container {{
                    max-width: 560px;
                    margin: 0 auto;
                    background-color: #FFFFFF;
                    border-radius: 16px;
                    overflow: hidden;
                    box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.08), 0 8px 10px -6px rgba(15, 23, 42, 0.04);
                    border: 1px solid #E2E8F0;
                }}
                .header {{
                    background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 50%, #312E81 100%);
                    padding: 36px 32px;
                    text-align: center;
                }}
                .brand-title {{
                    color: #FFFFFF;
                    font-size: 26px;
                    font-weight: 800;
                    letter-spacing: -0.5px;
                    margin: 0;
                    text-transform: uppercase;
                }}
                .brand-sub {{
                    color: #A5B4FC;
                    font-size: 11px;
                    font-weight: 600;
                    letter-spacing: 2px;
                    margin-top: 4px;
                    text-transform: uppercase;
                }}
                .body-content {{
                    padding: 40px 36px;
                    color: #334155;
                }}
                .greeting {{
                    font-size: 20px;
                    font-weight: 700;
                    color: #0F172A;
                    margin-top: 0;
                    margin-bottom: 12px;
                }}
                .intro-text {{
                    font-size: 15px;
                    line-height: 1.6;
                    color: #475569;
                    margin-top: 0;
                    margin-bottom: 28px;
                }}
                .otp-card {{
                    background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%);
                    border: 1px solid #C7D2FE;
                    border-radius: 14px;
                    padding: 28px 20px;
                    text-align: center;
                    margin-bottom: 28px;
                }}
                .otp-label {{
                    font-size: 12px;
                    font-weight: 700;
                    color: #4338CA;
                    letter-spacing: 1.5px;
                    text-transform: uppercase;
                    margin-bottom: 12px;
                }}
                .otp-code {{
                    font-family: 'Courier New', Consolas, Monaco, monospace;
                    font-size: 42px;
                    font-weight: 800;
                    letter-spacing: 10px;
                    color: #312E81;
                    margin: 0;
                    text-shadow: 0 1px 2px rgba(49, 46, 129, 0.1);
                }}
                .timer-badge {{
                    display: inline-block;
                    margin-top: 14px;
                    padding: 4px 12px;
                    background-color: #E0E7FF;
                    color: #3730A3;
                    font-size: 12px;
                    font-weight: 600;
                    border-radius: 20px;
                }}
                .security-note {{
                    background-color: #FEF3C7;
                    border-left: 4px solid #F59E0B;
                    border-radius: 6px;
                    padding: 14px 16px;
                    font-size: 13px;
                    color: #92400E;
                    line-height: 1.5;
                    margin-bottom: 28px;
                }}
                .footer {{
                    background-color: #F1F5F9;
                    padding: 24px 32px;
                    text-align: center;
                    border-top: 1px solid #E2E8F0;
                }}
                .footer-text {{
                    font-size: 12px;
                    color: #64748B;
                    margin: 0 0 8px 0;
                }}
                .footer-links a {{
                    color: #4F46E5;
                    text-decoration: none;
                    font-size: 12px;
                    margin: 0 8px;
                    font-weight: 500;
                }}
            </style>
        </head>
        <body>
            <div class="wrapper">
                <div class="container">
                    <div class="header">
                        <h1 class="brand-title">OFC HR</h1>
                        <div class="brand-sub">Enterprise Management Suite</div>
                    </div>
                    
                    <div class="body-content">
                        <div class="greeting">Hello {first_name},</div>
                        <p class="intro-text">
                            Thank you for joining <strong>OFC HR</strong>. To complete your account setup and verify your email address, please use the secure verification code below:
                        </p>
                        
                        <div class="otp-card">
                            <div class="otp-label">Security Verification Code</div>
                            <div class="otp-code">{otp_code}</div>
                            <div class="timer-badge">⏱ Expires in 15 minutes</div>
                        </div>
                        
                        <div class="security-note">
                            <strong>Security Tip:</strong> Never share this code with anyone. OFC HR staff will never ask for your verification code over phone or email.
                        </div>
                        
                        <p class="intro-text" style="margin-bottom: 0;">
                            If you did not request this email, please ignore it or contact our security team if you have concerns.
                        </p>
                    </div>
                    
                    <div class="footer">
                        <p class="footer-text">&copy; 2026 OFC HR Enterprise Platform. All rights reserved.</p>
                        <div class="footer-links">
                            <a href="#">Security Center</a> &bull;
                            <a href="#">Privacy Policy</a> &bull;
                            <a href="#">Support</a>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        return await asyncio.to_thread(cls._send_email_sync, to_email, subject, html_content)

    @classmethod
    async def send_password_reset_email(cls, to_email: str, first_name: str, reset_token: str) -> bool:
        subject = "OFC HR - Password Reset Request"
        reset_url = f"{settings.ALLOWED_ORIGINS[0]}/reset-password?token={reset_token}"
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>OFC HR Password Reset</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                    background-color: #F8FAFC;
                    margin: 0;
                    padding: 0;
                    -webkit-font-smoothing: antialiased;
                }}
                .wrapper {{
                    width: 100%;
                    table-layout: fixed;
                    background-color: #F8FAFC;
                    padding: 40px 0;
                }}
                .container {{
                    max-width: 560px;
                    margin: 0 auto;
                    background-color: #FFFFFF;
                    border-radius: 16px;
                    overflow: hidden;
                    box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.08), 0 8px 10px -6px rgba(15, 23, 42, 0.04);
                    border: 1px solid #E2E8F0;
                }}
                .header {{
                    background: linear-gradient(135deg, #0F172A 0%, #451A03 50%, #7C2D12 100%);
                    padding: 36px 32px;
                    text-align: center;
                }}
                .brand-title {{
                    color: #FFFFFF;
                    font-size: 26px;
                    font-weight: 800;
                    letter-spacing: -0.5px;
                    margin: 0;
                    text-transform: uppercase;
                }}
                .brand-sub {{
                    color: #FDBA74;
                    font-size: 11px;
                    font-weight: 600;
                    letter-spacing: 2px;
                    margin-top: 4px;
                    text-transform: uppercase;
                }}
                .body-content {{
                    padding: 40px 36px;
                    color: #334155;
                }}
                .greeting {{
                    font-size: 20px;
                    font-weight: 700;
                    color: #0F172A;
                    margin-top: 0;
                    margin-bottom: 12px;
                }}
                .intro-text {{
                    font-size: 15px;
                    line-height: 1.6;
                    color: #475569;
                    margin-top: 0;
                    margin-bottom: 28px;
                }}
                .btn-container {{
                    text-align: center;
                    margin: 32px 0;
                }}
                .btn {{
                    display: inline-block;
                    padding: 14px 32px;
                    background: linear-gradient(135deg, #EA580C 0%, #C2410C 100%);
                    color: #FFFFFF;
                    text-decoration: none;
                    border-radius: 10px;
                    font-size: 16px;
                    font-weight: 700;
                    box-shadow: 0 4px 12px rgba(234, 88, 12, 0.25);
                }}
                .token-box {{
                    background-color: #F1F5F9;
                    border: 1px solid #CBD5E1;
                    border-radius: 8px;
                    padding: 12px;
                    font-family: monospace;
                    font-size: 12px;
                    color: #475569;
                    word-break: break-all;
                    margin-top: 16px;
                }}
                .footer {{
                    background-color: #F1F5F9;
                    padding: 24px 32px;
                    text-align: center;
                    border-top: 1px solid #E2E8F0;
                }}
                .footer-text {{
                    font-size: 12px;
                    color: #64748B;
                    margin: 0 0 8px 0;
                }}
            </style>
        </head>
        <body>
            <div class="wrapper">
                <div class="container">
                    <div class="header">
                        <h1 class="brand-title">OFC HR</h1>
                        <div class="brand-sub">Account Recovery</div>
                    </div>
                    
                    <div class="body-content">
                        <div class="greeting">Hello {first_name},</div>
                        <p class="intro-text">
                            We received a request to reset your password for your <strong>OFC HR</strong> account. Click the button below to set a new password:
                        </p>
                        
                        <div class="btn-container">
                            <a href="{reset_url}" class="btn">Reset My Password</a>
                        </div>
                        
                        <p class="intro-text">This link will expire in <strong>1 hour</strong>.</p>
                        
                        <div class="token-box">
                            <strong>Reset Token:</strong> {reset_token}
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p class="footer-text">&copy; 2026 OFC HR Enterprise Platform. All rights reserved.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        return await asyncio.to_thread(cls._send_email_sync, to_email, subject, html_content)
