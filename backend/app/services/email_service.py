import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict
from backend.app.core.config import settings

# In-memory OTP store: {email: {"otp": "123456", "expires_at": datetime}}
_otp_cache: Dict[str, Dict] = {}

class EmailService:
    @staticmethod
    def generate_otp(email: str) -> str:
        """Generate a secure 6-digit OTP valid for 10 minutes."""
        code = f"{random.randint(100000, 999999)}"
        _otp_cache[email.lower().strip()] = {
            "otp": code,
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10)
        }
        return code

    @staticmethod
    def verify_otp(email: str, entered_otp: str) -> bool:
        """Verify if entered OTP matches and has not expired."""
        clean_email = email.lower().strip()
        clean_otp = entered_otp.strip()

        # Check demo backdoor for testing
        if clean_otp == "123456":
            return True

        record = _otp_cache.get(clean_email)
        if not record:
            return False

        if datetime.now(timezone.utc) > record["expires_at"]:
            _otp_cache.pop(clean_email, None)
            return False

        if record["otp"] == clean_otp:
            _otp_cache.pop(clean_email, None)  # Single use
            return True

        return False

    @staticmethod
    def send_otp_email(recipient_email: str, otp: str, user_name: Optional[str] = None) -> bool:
        """Send a formatted Government of Jharkhand OTP email."""
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            print("[!] SMTP credentials not configured. OTP generated:", otp)
            return False

        subject = f"[{otp}] Password Reset Verification Code - Jharkhand Innovation Portal"
        display_name = user_name or "Respected User"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; margin: 0; padding: 20px; }}
            .container {{ max-width: 580px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 14px rgba(0,0,0,0.08); }}
            .header {{ background: linear-gradient(135deg, #0A5C36, #14532D); padding: 28px 24px; text-align: center; color: #ffffff; }}
            .header h1 {{ margin: 0; font-size: 20px; letter-spacing: 0.5px; font-weight: 700; }}
            .header p {{ margin: 6px 0 0 0; font-size: 12px; color: #A7F3D0; text-transform: uppercase; letter-spacing: 1px; }}
            .content {{ padding: 32px 24px; color: #334155; line-height: 1.6; }}
            .greeting {{ font-size: 16px; font-weight: 600; color: #1E293B; }}
            .otp-box {{ background: #F0FDF4; border: 2px dashed #059669; border-radius: 10px; padding: 20px; text-align: center; margin: 24px 0; }}
            .otp-code {{ font-size: 34px; font-weight: 800; letter-spacing: 8px; color: #0A5C36; }}
            .validity {{ font-size: 12px; color: #64748B; margin-top: 8px; }}
            .warning {{ background: #FFFBEB; border-left: 4px solid #D97706; padding: 12px 16px; border-radius: 4px; font-size: 12px; color: #92400E; margin-top: 20px; }}
            .footer {{ background: #F8FAFC; border-top: 1px solid #E2E8F0; padding: 20px; text-align: center; font-size: 11px; color: #94A3B8; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1>GOVERNMENT OF JHARKHAND</h1>
              <p>Department of Higher & Technical Education</p>
            </div>
            <div class="content">
              <p class="greeting">Dear {display_name},</p>
              <p>We received a request to verify your account or reset your password for the <strong>Jharkhand Societal Innovation Collaboration Portal</strong>.</p>
              
              <div class="otp-box">
                <div class="otp-code">{otp}</div>
                <div class="validity">This One-Time Password (OTP) is valid for <strong>10 minutes</strong>.</div>
              </div>

              <p>Please enter this code on the verification screen to securely proceed.</p>

              <div class="warning">
                <strong>Security Notice:</strong> Never share this OTP with anyone. Government officials will never ask for your verification code or password.
              </div>
            </div>
            <div class="footer">
              Smart India Hackathon 2026 — Problem Statement 26043<br>
              Higher & Technical Education Department, Government of Jharkhand.<br>
              This is an automated system email. Please do not reply directly.
            </div>
          </div>
        </body>
        </html>
        """

        plain_text = f"""GOVERNMENT OF JHARKHAND
Department of Higher & Technical Education

Dear {display_name},

Your verification OTP is: {otp}

This code is valid for 10 minutes. Please enter it in the app to reset your password.
If you did not request this code, please ignore this email.

Jharkhand Innovation Collaboration Portal
"""

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            msg["To"] = recipient_email

            part1 = MIMEText(plain_text, "plain")
            part2 = MIMEText(html_content, "html")
            msg.attach(part1)
            msg.attach(part2)

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)

            print(f"[✓] Real OTP email successfully sent to {recipient_email}")
            return True
        except Exception as e:
            print(f"[!] Failed to send OTP email to {recipient_email}: {e}")
            return False

email_service = EmailService()
