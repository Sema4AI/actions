"""
Type definitions for work items.

Based on robocorp-workitems (Apache 2.0 License).
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# JSON-compatible types
JSONType = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]

# Path type for file operations
PathType = Union[Path, str]


class State(str, Enum):
    """Work item processing states."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    FAILED = "FAILED"
    # Alias for robocorp compatibility
    COMPLETED = "DONE"

    @classmethod
    def _missing_(cls, value):
        """Handle COMPLETED -> DONE mapping."""
        if isinstance(value, str) and value.upper() == "COMPLETED":
            return cls.DONE
        return None


class ExceptionType(str, Enum):
    """Types of exceptions that can occur during work item processing."""

    # Business exception - expected failure that should not be retried
    BUSINESS = "BUSINESS"
    # Application exception - unexpected failure that may be retried
    APPLICATION = "APPLICATION"


@dataclass
class Address:
    """Email address with optional display name."""

    address: str
    name: Optional[str] = None

    def __str__(self) -> str:
        if self.name:
            return f"{self.name} <{self.address}>"
        return self.address


@dataclass
class Email:
    """
    Parsed email message from work item attachment.

    Provides structured access to email fields commonly used
    in email-triggered automation workflows.
    """

    sender: Optional[Address] = None
    recipients: List[Address] = field(default_factory=list)
    cc: List[Address] = field(default_factory=list)
    bcc: List[Address] = field(default_factory=list)
    subject: Optional[str] = None
    date: Optional[datetime] = None
    body: Optional[str] = None
    html: Optional[str] = None
    reply_to: Optional[Address] = None
    message_id: Optional[str] = None
    errors: List[str] = field(default_factory=list)

    @classmethod
    def from_bytes(cls, content: bytes) -> "Email":
        """
        Parse email from raw bytes content.

        Args:
            content: Raw email bytes (RFC 822 format).

        Returns:
            Parsed Email object.
        """
        import email
        from email.header import decode_header
        from email.utils import parseaddr, parsedate_to_datetime

        errors = []
        msg = email.message_from_bytes(content)

        def decode_str(value: Optional[str]) -> Optional[str]:
            if not value:
                return None
            try:
                decoded_parts = decode_header(value)
                result = []
                for part, charset in decoded_parts:
                    if isinstance(part, bytes):
                        result.append(part.decode(charset or "utf-8", errors="replace"))
                    else:
                        result.append(part)
                return "".join(result)
            except Exception as e:
                errors.append(f"Header decode error: {e}")
                return value

        def parse_address(value: Optional[str]) -> Optional[Address]:
            if not value:
                return None
            name, addr = parseaddr(value)
            if addr:
                return Address(address=addr, name=decode_str(name) if name else None)
            return None

        def parse_addresses(value: Optional[str]) -> List[Address]:
            if not value:
                return []
            addresses = []
            for part in value.split(","):
                addr = parse_address(part.strip())
                if addr:
                    addresses.append(addr)
            return addresses

        def get_body(msg) -> tuple:
            body = None
            html = None
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain" and body is None:
                        try:
                            body = part.get_payload(decode=True).decode(
                                part.get_content_charset() or "utf-8", errors="replace"
                            )
                        except Exception as e:
                            errors.append(f"Body decode error: {e}")
                    elif content_type == "text/html" and html is None:
                        try:
                            html = part.get_payload(decode=True).decode(
                                part.get_content_charset() or "utf-8", errors="replace"
                            )
                        except Exception as e:
                            errors.append(f"HTML decode error: {e}")
            else:
                content_type = msg.get_content_type()
                try:
                    payload = msg.get_payload(decode=True).decode(
                        msg.get_content_charset() or "utf-8", errors="replace"
                    )
                    if content_type == "text/html":
                        html = payload
                    else:
                        body = payload
                except Exception as e:
                    errors.append(f"Payload decode error: {e}")
            return body, html

        date = None
        date_str = msg.get("Date")
        if date_str:
            try:
                date = parsedate_to_datetime(date_str)
            except Exception as e:
                errors.append(f"Date parse error: {e}")

        body, html = get_body(msg)

        return cls(
            sender=parse_address(msg.get("From")),
            recipients=parse_addresses(msg.get("To")),
            cc=parse_addresses(msg.get("Cc")),
            bcc=parse_addresses(msg.get("Bcc")),
            subject=decode_str(msg.get("Subject")),
            date=date,
            body=body,
            html=html,
            reply_to=parse_address(msg.get("Reply-To")),
            message_id=msg.get("Message-ID"),
            errors=errors,
        )
