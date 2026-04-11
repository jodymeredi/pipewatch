"""Built-in alert notifier implementations for pipewatch."""

from __future__ import annotations

import json
import logging
import smtplib
import urllib.request
from email.message import EmailMessage
from typing import Any

from pipewatch.alerts import register_handler

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Webhook notifier
# ---------------------------------------------------------------------------

def _webhook_handler(alert: dict[str, Any], cfg: dict[str, Any]) -> None:
    """POST alert payload as JSON to a configured webhook URL."""
    url: str = cfg.get("url", "")
    if not url:
        logger.warning("webhook notifier: 'url' not configured, skipping")
        return

    payload = json.dumps(alert).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=cfg.get("timeout", 5)):
            logger.debug("webhook notifier: alert sent to %s", url)
    except Exception as exc:  # noqa: BLE001
        logger.error("webhook notifier: request failed – %s", exc)


# ---------------------------------------------------------------------------
# E-mail notifier
# ---------------------------------------------------------------------------

def _email_handler(alert: dict[str, Any], cfg: dict[str, Any]) -> None:
    """Send alert via SMTP."""
    smtp_host: str = cfg.get("smtp_host", "localhost")
    smtp_port: int = int(cfg.get("smtp_port", 25))
    to_addrs: list[str] = cfg.get("to", [])
    from_addr: str = cfg.get("from", "pipewatch@localhost")

    if not to_addrs:
        logger.warning("email notifier: no 'to' addresses configured, skipping")
        return

    msg = EmailMessage()
    msg["Subject"] = f"[pipewatch] {alert.get('level', 'ALERT').upper()}: {alert.get('pipeline', 'unknown')}"
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)
    msg.set_content(
        f"Pipeline : {alert.get('pipeline')}\n"
        f"Level    : {alert.get('level')}\n"
        f"Metric   : {alert.get('metric')}\n"
        f"Value    : {alert.get('value')}\n"
        f"Threshold: {alert.get('threshold')}\n"
        f"Message  : {alert.get('message')}\n"
    )

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=cfg.get("timeout", 5)) as server:
            server.sendmail(from_addr, to_addrs, msg.as_string())
            logger.debug("email notifier: alert sent to %s", to_addrs)
    except Exception as exc:  # noqa: BLE001
        logger.error("email notifier: send failed – %s", exc)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register_builtin_notifiers() -> None:
    """Register all built-in notifier handlers with the alerts registry."""
    register_handler("webhook", _webhook_handler)
    register_handler("email", _email_handler)
    logger.debug("notifiers: built-in handlers registered (webhook, email)")
