"""Email service — send verification codes via Tencent Cloud SES SMTP."""

import logging
import random
import string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)


# ── Verification Code Helpers ────────────────────────────────────────────────


def generate_verify_code(length: int = 6) -> str:
    """Generate a numeric verification code."""
    return "".join(random.choices(string.digits, k=length))


# ── Redis Key Helpers ────────────────────────────────────────────────────────


def verify_code_key(email: str) -> str:
    return f"email_verify:{email}"


def verify_rate_key(email: str) -> str:
    return f"email_verify_rate:{email}"


# ── Email Sending ────────────────────────────────────────────────────────────


def _build_verify_html(code: str, name: str = "") -> str:
    greeting = f"您好 {name}，" if name else "您好，"
    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, Arial, sans-serif; background:#f8fafc; margin:0; padding:32px;">
  <div style="max-width:480px; margin:0 auto; background:#fff; border-radius:16px;
              border:1px solid #e2e8f0; padding:40px;">
    <h1 style="font-size:20px; color:#0f172a; margin:0 0 8px;">
      验证您的邮箱地址
    </h1>
    <p style="color:#475569; font-size:15px; line-height:1.7; margin:16px 0;">
      {greeting}感谢注册 <strong>BidAgent</strong>！请使用以下验证码完成邮箱验证：
    </p>
    <div style="background:#f1f5f9; border-radius:12px; padding:24px;
                text-align:center; margin:24px 0;">
      <span style="font-size:40px; font-weight:700; letter-spacing:10px;
                   color:#0f172a; font-family:monospace;">{code}</span>
    </div>
    <p style="color:#64748b; font-size:13px; line-height:1.6;">
      验证码有效期为 <strong>10 分钟</strong>，请尽快完成验证。<br>
      如非本人操作，请忽略此邮件。
    </p>
    <hr style="border:none; border-top:1px solid #e2e8f0; margin:24px 0;">
    <p style="color:#94a3b8; font-size:12px; margin:0;">
      此邮件由系统自动发送，请勿回复。
    </p>
  </div>
</body>
</html>
"""


async def send_verification_email(to_email: str, code: str, name: str = "") -> None:
    """Send a verification code email.

    When EMAIL_ENABLED=False, only log the code (useful for development).
    When EMAIL_ENABLED=True, send via Tencent Cloud SES SMTP.
    """
    if not settings.EMAIL_ENABLED:
        logger.info(
            "[DEV MODE] Verification code for %s: %s (not sent, EMAIL_ENABLED=False)",
            to_email,
            code,
        )
        return

    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("SMTP not configured — verification code %s not sent", code)
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "【BidAgent】邮箱验证码"
    msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.SMTP_USER}>"
    msg["To"] = to_email

    html_body = _build_verify_html(code, name)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_tls=True,
            timeout=10,
        )
        logger.info("Verification email sent to %s", to_email)
    except Exception as exc:
        logger.error("Failed to send verification email to %s: %s", to_email, exc)
        raise
