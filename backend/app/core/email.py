"""Email service — send verification codes via Tencent Cloud SES SMTP."""

import logging
import secrets
import string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)


# ── Verification Code Helpers ────────────────────────────────────────────────


def generate_verify_code(length: int = 6) -> str:
    """Generate a numeric verification code."""
    return "".join(secrets.choice(string.digits) for _ in range(length))


# ── Redis Key Helpers ────────────────────────────────────────────────────────


def verify_code_key(email: str) -> str:
    return f"{settings.REDIS_KEY_PREFIX}:email_verify:{email}"


def verify_rate_key(email: str) -> str:
    return f"{settings.REDIS_KEY_PREFIX}:email_verify_rate:{email}"


def pwd_reset_key(token: str) -> str:
    return f"{settings.REDIS_KEY_PREFIX}:pwd_reset:{token}"


def pwd_reset_rate_key(email: str) -> str:
    return f"{settings.REDIS_KEY_PREFIX}:pwd_reset_rate:{email}"


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
        logger.warning("SMTP not configured — verification email not sent")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "【BidAgent】邮箱验证码"
    msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.SMTP_USER}>"
    msg["To"] = to_email

    html_body = _build_verify_html(code, name)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        smtp = aiosmtplib.SMTP(
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            use_tls=True,
            timeout=10,
        )
        await smtp.connect()
        await smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        await smtp.send_message(msg)
        await smtp.quit()
        logger.info("Verification email sent to %s", to_email)
    except Exception as exc:
        logger.error("Failed to send verification email to %s: %s", to_email, exc)
        raise


def _build_reset_html(reset_url: str, name: str = "") -> str:
    greeting = f"您好 {name}，" if name else "您好，"
    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:-apple-system,Arial,sans-serif;background:#f0f4f8;margin:0;padding:32px;">
  <div style="max-width:520px;margin:0 auto;background:#fff;border-radius:16px;
              border:1px solid #e2e8f0;padding:40px;">
    <h1 style="font-size:20px;color:#0f172a;margin:0 0 8px;">Reset Your Password / 重置密码</h1>
    <p style="color:#475569;font-size:14px;line-height:1.8;margin:16px 0;">
      {greeting}您正在申请重置 BidAgent 帐号密码。<br>
      Hi {name or 'there'}, you requested a password reset for your BidAgent account.
    </p>
    <div style="text-align:center;margin:28px 0;">
      <a href="{reset_url}"
         style="display:inline-block;background:#1e40af;color:#fff;font-size:15px;
                font-weight:600;padding:14px 36px;border-radius:10px;text-decoration:none;">
        重置密码 &nbsp;/&nbsp; Reset Password
      </a>
    </div>
    <div style="background:#fffbeb;border-radius:10px;padding:14px 18px;margin:20px 0;">
      <p style="margin:0;font-size:13px;color:#92400e;line-height:1.9;">
        &bull; 链接有效期 30 分钟 &nbsp;/&nbsp; This link expires in 30 minutes.<br>
        &bull; 如非本人操作，请忽略此邮件 &nbsp;/&nbsp; If you didn't request this, please ignore this email.
      </p>
    </div>
    <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0;">
    <p style="color:#94a3b8;font-size:12px;margin:0;text-align:center;">
      此邮件由系统自动发送，请勿回复 &nbsp;&middot;&nbsp; Automated email, do not reply.<br>
      &copy; 2026 BidAgent &nbsp;&middot;&nbsp;
      <a href="https://bid.easudata.com" style="color:#3b82f6;text-decoration:none;">bid.easudata.com</a>
    </p>
  </div>
</body>
</html>
"""


async def send_reset_password_email(to_email: str, reset_url: str, name: str = "") -> None:
    """Send a password reset link email."""
    if not settings.EMAIL_ENABLED:
        logger.info("[DEV MODE] Password reset URL for %s: %s", to_email, reset_url)
        return

    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("SMTP not configured — reset email not sent")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "【BidAgent】密码重置链接 / Password Reset"
    msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.SMTP_USER}>"
    msg["To"] = to_email
    msg.attach(MIMEText(_build_reset_html(reset_url, name), "html", "utf-8"))

    try:
        smtp = aiosmtplib.SMTP(
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            use_tls=True,
            timeout=10,
        )
        await smtp.connect()
        await smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        await smtp.send_message(msg)
        await smtp.quit()
        logger.info("Password reset email sent to %s", to_email)
    except Exception as exc:
        logger.error("Failed to send reset email to %s: %s", to_email, exc)
        raise
