"""Tests for pipewatch.notifiers."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from unittest.mock import MagicMock, patch

import pytest

from pipewatch.alerts import get_handler, _registry
from pipewatch.notifiers import register_builtin_notifiers, _webhook_handler, _email_handler


@pytest.fixture(autouse=True)
def clean_registry():
    """Ensure the handler registry is clean before each test."""
    _registry.clear()
    yield
    _registry.clear()


SAMPLE_ALERT = {
    "pipeline": "etl_daily",
    "level": "critical",
    "metric": "row_count",
    "value": 0,
    "threshold": 100,
    "message": "row_count is below threshold",
}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def test_register_builtin_notifiers_adds_webhook():
    register_builtin_notifiers()
    assert get_handler("webhook") is not None


def test_register_builtin_notifiers_adds_email():
    register_builtin_notifiers()
    assert get_handler("email") is not None


# ---------------------------------------------------------------------------
# Webhook handler
# ---------------------------------------------------------------------------

def test_webhook_handler_skips_when_no_url(caplog):
    import logging
    with caplog.at_level(logging.WARNING, logger="pipewatch.notifiers"):
        _webhook_handler(SAMPLE_ALERT, {})
    assert "url" in caplog.text


def test_webhook_handler_posts_json():
    received: list[bytes] = []

    class _Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            received.append(self.rfile.read(length))
            self.send_response(200)
            self.end_headers()

        def log_message(self, *args):  # silence server logs
            pass

    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = Thread(target=server.handle_request, daemon=True)
    thread.start()

    _webhook_handler(SAMPLE_ALERT, {"url": f"http://127.0.0.1:{port}"})
    thread.join(timeout=2)
    server.server_close()

    assert len(received) == 1
    payload = json.loads(received[0])
    assert payload["pipeline"] == "etl_daily"


def test_webhook_handler_logs_error_on_failure(caplog):
    import logging
    with caplog.at_level(logging.ERROR, logger="pipewatch.notifiers"):
        _webhook_handler(SAMPLE_ALERT, {"url": "http://127.0.0.1:1", "timeout": 1})
    assert "webhook notifier" in caplog.text


# ---------------------------------------------------------------------------
# Email handler
# ---------------------------------------------------------------------------

def test_email_handler_skips_when_no_to(caplog):
    import logging
    with caplog.at_level(logging.WARNING, logger="pipewatch.notifiers"):
        _email_handler(SAMPLE_ALERT, {})
    assert "to" in caplog.text


def test_email_handler_sends_via_smtp():
    mock_smtp = MagicMock()
    with patch("pipewatch.notifiers.smtplib.SMTP") as smtp_cls:
        smtp_cls.return_value.__enter__ = lambda s: mock_smtp
        smtp_cls.return_value.__exit__ = MagicMock(return_value=False)
        _email_handler(SAMPLE_ALERT, {"to": ["ops@example.com"]})
        mock_smtp.sendmail.assert_called_once()
        args = mock_smtp.sendmail.call_args[0]
        assert "ops@example.com" in args[1]
