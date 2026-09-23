import secrets
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Tuple
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.security import hash_otp
from backend.app.core.database import SessionLocal
from backend.app.models.models import OTPChallenge, utc_now

# In-memory backup cache: {email: {"hash": str, "expires_at": datetime, "attempts": int}}
_otp_cache: Dict[str, Dict] = {}

class EmailService:
    @staticmethod
    def generate_otp(
        email: str,
        db: Optional[Session] = None,
        purpose: str = "PASSWORD_RESET",
        ip_address: Optional[str] = None
    ) -> str:
        """
        Generate a cryptographically secure 6-digit OTP valid for 10 minutes.
        Saves hashed OTP in database with attempt tracking.
        """
        clean_email = email.lower().strip()
        code = "".join(secrets.choice(string.digits) for _ in range(6))
        code_hash = hash_otp(code)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        # Database persistence
        close_session = False
        if db is None:
            db = SessionLocal()
            close_session = True

        try:
            # Invalidate any prior active OTPs for this email & purpose
            db.query(OTPChallenge).filter(
                OTPChallenge.account_identifier == clean_email,
                OTPChallenge.purpose == purpose,
                OTPChallenge.is_used == False
            ).update({"is_used": True}, synchronize_session=False)

            challenge = OTPChallenge(
                account_identifier=clean_email,
                otp_hash=code_hash,
                purpose=purpose,
                attempts=0,
                max_attempts=3,
                delivery_status="PENDING",
                is_used=False,
                expires_at=expires_at,
                created_at=utc_now(),
                ip_address=ip_address
            )
            db.add(challenge)
            db.commit()
        except Exception:
            db.rollback()
            # In-memory fallback
            _otp_cache[clean_email] = {
                "hash": code_hash,
                "expires_at": expires_at,
                "attempts": 0,
                "purpose": purpose
            }
        finally:
            if close_session:
                db.close()

        return code

    @staticmethod
    def verify_otp_detailed(
        account_identifier: str,
        entered_otp: str,
        db: Optional[Session] = None,
        purpose: str = "PASSWORD_RESET"
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify entered OTP against hashed record in database with attempt tracking and lockout.
        Returns (is_valid, error_message).
        """
        clean_id = account_identifier.lower().strip()
        clean_otp = entered_otp.strip()
        now_utc = datetime.now(timezone.utc)
        entered_hash = hash_otp(clean_otp)

        close_session = False
        if db is None:
            db = SessionLocal()
            close_session = True

        try:
            challenge = db.query(OTPChallenge).filter(
                OTPChallenge.account_identifier == clean_id,
                OTPChallenge.purpose == purpose
            ).order_by(OTPChallenge.id.desc()).first()

            if not challenge:
                return False, "Invalid or expired OTP code. Please request a new code."

            # Check if already locked out
            if challenge.attempts >= challenge.max_attempts:
                challenge.is_used = True
                db.commit()
                return False, "Maximum verification attempts exceeded. Challenge locked out. Please request a new code."

            # Check if already used
            if challenge.is_used:
                return False, "OTP code has already been used or expired. Please request a new code."

            # Check expiration
            exp = challenge.expires_at
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)

            if now_utc > exp:
                challenge.is_used = True
                db.commit()
                return False, "OTP code has expired. Please request a new code."

            challenge.attempts += 1

            # Check if entered OTP is correct
            if secrets.compare_digest(challenge.otp_hash, entered_hash):
                challenge.is_used = True
                db.commit()
                return True, None

            # Incorrect attempt
            remaining = challenge.max_attempts - challenge.attempts
            if remaining <= 0:
                challenge.is_used = True
                db.commit()
                return False, "Invalid OTP code. Maximum verification attempts exceeded. Challenge locked out."

            db.commit()
            return False, f"Invalid OTP code. Attempts remaining: {remaining}."
        finally:
            if close_session:
                db.close()

    @staticmethod
    def verify_otp(
        email: str,
        entered_otp: str,
        db: Optional[Session] = None,
        purpose: str = "PASSWORD_RESET"
    ) -> bool:
        """
        Verify entered OTP against hashed record in database.
        Locks out after 3 failed attempts; enforces single-use.
        """
        is_valid, _ = EmailService.verify_otp_detailed(email, entered_otp, db=db, purpose=purpose)
        return is_valid

    @staticmethod
    def send_otp_email(recipient_email: str, otp: str, user_name: Optional[str] = None) -> bool:
        """Send a formatted Government of Jharkhand OTP email."""
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            # Security: Never log the OTP value in production or terminal
            return False

        subject = "Password Reset Verification Code - Jharkhand Innovation Portal"

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
