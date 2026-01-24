"""
Notification service for the Action Server.

Provides webhook and email notifications for schedule executions.
"""

import asyncio
import logging
from typing import Optional

log = logging.getLogger(__name__)


class NotificationService:
    """
    Service for sending notifications via webhook or email.

    Email notifications require SMTP configuration.
    """

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: int = 587,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        smtp_from: Optional[str] = None,
        smtp_use_tls: bool = True,
    ):
        """
        Initialize the notification service.

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port (default 587)
            smtp_user: SMTP username for authentication
            smtp_password: SMTP password for authentication
            smtp_from: Default sender email address
            smtp_use_tls: Use TLS for SMTP connection
        """
        self._smtp_host = smtp_host
        self._smtp_port = smtp_port
        self._smtp_user = smtp_user
        self._smtp_password = smtp_password
        self._smtp_from = smtp_from
        self._smtp_use_tls = smtp_use_tls

    @property
    def email_configured(self) -> bool:
        """Check if email notifications are configured."""
        return bool(self._smtp_host)

    async def send_webhook(
        self,
        url: str,
        payload: dict,
        headers: Optional[dict] = None,
        timeout: float = 30.0,
        retries: int = 3,
    ) -> bool:
        """
        Send a webhook notification.

        Args:
            url: Webhook URL
            payload: JSON payload to send
            headers: Optional additional headers
            timeout: Request timeout in seconds
            retries: Number of retry attempts

        Returns:
            True if successful, False otherwise
        """
        import aiohttp

        all_headers = {"Content-Type": "application/json"}
        if headers:
            all_headers.update(headers)

        last_error = None
        for attempt in range(retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url,
                        json=payload,
                        headers=all_headers,
                        timeout=aiohttp.ClientTimeout(total=timeout),
                    ) as response:
                        if response.status < 400:
                            log.debug(f"Webhook sent successfully to {url}")
                            return True
                        else:
                            last_error = f"HTTP {response.status}"
                            log.warning(
                                f"Webhook to {url} failed with status {response.status}"
                            )
            except asyncio.TimeoutError:
                last_error = "Timeout"
                log.warning(f"Webhook to {url} timed out")
            except Exception as e:
                last_error = str(e)
                log.warning(f"Webhook to {url} failed: {e}")

            if attempt < retries - 1:
                await asyncio.sleep(1.0 * (attempt + 1))

        log.error(f"Webhook to {url} failed after {retries} attempts: {last_error}")
        return False

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        from_addr: Optional[str] = None,
    ) -> bool:
        """
        Send an email notification.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text body
            html_body: Optional HTML body
            from_addr: Sender address (uses default if not provided)

        Returns:
            True if successful, False otherwise
        """
        if not self.email_configured:
            log.warning("Email notifications not configured (no SMTP host)")
            return False

        sender = from_addr or self._smtp_from
        if not sender:
            log.error("No sender email address configured")
            return False

        try:
            # Try async SMTP first
            return await self._send_email_async(to, subject, body, html_body, sender)
        except ImportError:
            # Fall back to sync SMTP
            return await asyncio.get_event_loop().run_in_executor(
                None,
                self._send_email_sync,
                to,
                subject,
                body,
                html_body,
                sender,
            )

    async def _send_email_async(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str],
        sender: str,
    ) -> bool:
        """Send email using aiosmtplib."""
        try:
            import aiosmtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
        except ImportError:
            raise ImportError(
                "aiosmtplib is required for async email notifications. "
                "Install with: pip install aiosmtplib"
            )

        # Build message
        if html_body:
            msg = MIMEMultipart("alternative")
            msg.attach(MIMEText(body, "plain"))
            msg.attach(MIMEText(html_body, "html"))
        else:
            msg = MIMEText(body, "plain")

        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = to

        try:
            await aiosmtplib.send(
                msg,
                hostname=self._smtp_host,
                port=self._smtp_port,
                username=self._smtp_user,
                password=self._smtp_password,
                start_tls=self._smtp_use_tls,
            )
            log.info(f"Email sent to {to}: {subject}")
            return True
        except Exception as e:
            log.exception(f"Failed to send email to {to}: {e}")
            return False

    def _send_email_sync(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str],
        sender: str,
    ) -> bool:
        """Send email using smtplib (synchronous fallback)."""
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        # Build message
        if html_body:
            msg = MIMEMultipart("alternative")
            msg.attach(MIMEText(body, "plain"))
            msg.attach(MIMEText(html_body, "html"))
        else:
            msg = MIMEText(body, "plain")

        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = to

        try:
            if self._smtp_use_tls:
                server = smtplib.SMTP(self._smtp_host, self._smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP(self._smtp_host, self._smtp_port)

            if self._smtp_user and self._smtp_password:
                server.login(self._smtp_user, self._smtp_password)

            server.sendmail(sender, [to], msg.as_string())
            server.quit()

            log.info(f"Email sent to {to}: {subject}")
            return True
        except Exception as e:
            log.exception(f"Failed to send email to {to}: {e}")
            return False

    async def test_connection(self) -> tuple[bool, str]:
        """
        Test the SMTP connection.

        Returns:
            Tuple of (success, message)
        """
        if not self.email_configured:
            return False, "SMTP not configured"

        try:
            import aiosmtplib

            smtp = aiosmtplib.SMTP(
                hostname=self._smtp_host,
                port=self._smtp_port,
            )
            await smtp.connect()
            if self._smtp_use_tls:
                await smtp.starttls()
            if self._smtp_user and self._smtp_password:
                await smtp.login(self._smtp_user, self._smtp_password)
            await smtp.quit()
            return True, "Connection successful"
        except ImportError:
            # Try sync
            import smtplib

            try:
                server = smtplib.SMTP(self._smtp_host, self._smtp_port, timeout=10)
                if self._smtp_use_tls:
                    server.starttls()
                if self._smtp_user and self._smtp_password:
                    server.login(self._smtp_user, self._smtp_password)
                server.quit()
                return True, "Connection successful"
            except Exception as e:
                return False, str(e)
        except Exception as e:
            return False, str(e)


# Global notification service instance
_global_notification_service: Optional[NotificationService] = None


def get_notification_service() -> Optional[NotificationService]:
    """Get the global notification service instance."""
    return _global_notification_service


def set_notification_service(service: Optional[NotificationService]) -> None:
    """Set the global notification service instance."""
    global _global_notification_service
    _global_notification_service = service


def initialize_notification_service(
    smtp_host: Optional[str] = None,
    smtp_port: int = 587,
    smtp_user: Optional[str] = None,
    smtp_password: Optional[str] = None,
    smtp_from: Optional[str] = None,
    smtp_use_tls: bool = True,
) -> NotificationService:
    """
    Initialize the global notification service.

    Returns the created service instance.
    """
    service = NotificationService(
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_user=smtp_user,
        smtp_password=smtp_password,
        smtp_from=smtp_from,
        smtp_use_tls=smtp_use_tls,
    )
    set_notification_service(service)
    return service
