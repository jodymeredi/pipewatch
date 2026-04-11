"""Rate-limit tracking for alert channels.

Prevents a single channel (e.g. 'email', 'webhook') from being flooded
by capping the number of alerts dispatched within a rolling time window.
"""
from __future__ import annotations

import time
from collections import deque
from typing import Deque, Dict, Tuple

# channel -> (max_calls, window_seconds)
_limits: Dict[str, Tuple[int, float]] = {}
# channel -> deque of call timestamps
_history: Dict[str, Deque[float]] = {}


def _now() -> float:  # pragma: no cover – patched in tests
    return time.monotonic()


def set_limit(channel: str, max_calls: int, window_seconds: float) -> None:
    """Register a rate-limit rule for *channel*."""
    if max_calls < 1:
        raise ValueError("max_calls must be >= 1")
    if window_seconds <= 0:
        raise ValueError("window_seconds must be > 0")
    _limits[channel] = (max_calls, window_seconds)
    _history.setdefault(channel, deque())


def is_rate_limited(channel: str) -> bool:
    """Return True if *channel* has exhausted its quota for the current window."""
    if channel not in _limits:
        return False
    max_calls, window = _limits[channel]
    now = _now()
    q = _history.setdefault(channel, deque())
    # evict timestamps outside the rolling window
    while q and now - q[0] > window:
        q.popleft()
    return len(q) >= max_calls


def record_dispatch(channel: str) -> None:
    """Record that one alert was dispatched on *channel*."""
    _history.setdefault(channel, deque()).append(_now())


def remaining(channel: str) -> int:
    """Return how many more dispatches are allowed in the current window."""
    if channel not in _limits:
        return -1  # unlimited
    max_calls, window = _limits[channel]
    now = _now()
    q = _history.setdefault(channel, deque())
    while q and now - q[0] > window:
        q.popleft()
    return max(0, max_calls - len(q))


def clear_limit(channel: str) -> bool:
    """Remove the rate-limit rule and history for *channel*."""
    removed = channel in _limits
    _limits.pop(channel, None)
    _history.pop(channel, None)
    return removed


def list_limits() -> Dict[str, Dict]:
    """Return a snapshot of all registered limits."""
    return {
        ch: {"max_calls": mc, "window_seconds": ws}
        for ch, (mc, ws) in _limits.items()
    }
