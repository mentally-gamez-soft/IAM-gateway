"""Mail configuration and utilities for sending emails."""

import logging

from flask import current_app, url_for
from flask_mail import Mail, Message

mail = Mail()
logger = logging.getLogger(__name__)


def send_password_reset_email(user, token):
    """
    Send password reset email to user.

    Dispatches the email asynchronously via Celery when the application is
    configured with ``USE_ASYNC_EMAIL=True`` (the default for non-testing
    environments).  Falls back to a direct synchronous send otherwise.

    Args:
        user: GwUser instance
        token: Password reset token
    """
    try:
        reset_url = url_for(
            "users.reset_password",
            token=token,
            _external=True,
        )

        subject = current_app.config.get(
            "PASSWORD_RESET_EMAIL_SUBJECT", "Reset Your Password"
        )

        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                    <h2 style="color: #2c3e50;">Password Reset Request</h2>

                    <p>Hello {user.username},</p>

                    <p>We received a request to reset your password. Click the button below to set a new password.</p>

                    <p style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" style="background-color: #3498db; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            Reset Password
                        </a>
                    </p>

                    <p>Or copy and paste this link in your browser:</p>
                    <p style="background-color: #f4f4f4; padding: 10px; border-radius: 3px; word-break: break-all;">
                        {reset_url}
                    </p>

                    <p style="color: #e74c3c; font-weight: bold;">&#9200; This link expires in 30 minutes.</p>

                    <hr style="border: 0; border-top: 1px solid #ddd; margin: 20px 0;">

                    <p style="color: #7f8c8d; font-size: 12px;">
                        <strong>Security Notice:</strong> If you did not request a password reset, please ignore this email. Your account remains secure.
                    </p>

                    <p style="color: #7f8c8d; font-size: 12px;">
                        Best regards,<br>
                        The IAM Gateway Team
                    </p>
                </div>
            </body>
        </html>
        """

        text_body = f"""
        Password Reset Request

        Hello {user.username},

        We received a request to reset your password. Click the link below to set a new password.

        Reset Link:
        {reset_url}

        This link expires in 30 minutes.

        ---

        Security Notice: If you did not request a password reset, please ignore this email. Your account remains secure.

        Best regards,
        The IAM Gateway Team
        """

        if current_app.config.get("USE_ASYNC_EMAIL", True):
            # Dispatch asynchronously via Celery
            from core.tasks.email_tasks import send_email_task

            send_email_task.delay(
                to=user.email,
                subject=subject,
                body=text_body,
                html_body=html_body,
            )
            logger.info(
                "Password reset email queued asynchronously for %s",
                user.email,
            )
        else:
            # Synchronous fallback (used in testing)
            msg = Message(
                subject=subject,
                recipients=[user.email],
                html=html_body,
                body=text_body,
            )
            mail.send(msg)
            logger.info("Password reset email sent to %s", user.email)

    except Exception as e:
        logger.error(
            "Failed to send password reset email to %s: %s",
            user.email,
            str(e),
        )
