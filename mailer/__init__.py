"""Mailer package."""
from .renderer import DigestRenderer
from .sender import EmailSender

__all__ = ["DigestRenderer", "EmailSender"]
