from __future__ import annotations

import json
import logging
import os
import re
import uuid
from contextvars import ContextVar, Token
from typing import Any

REQUEST_ID_HEADER = "X-Request-ID"
_REQUEST_ID = ContextVar[str | None]("fairtoy_request_id", default=None)
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def configure_logging() -> None:
    """Configure readable, key-value application logs once per process."""

    configured_level = os.getenv("FAIRTOY_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, configured_level, logging.INFO)
    if not isinstance(level, int):
        level = logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logging.getLogger("fairtoy").setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """Return a logger in the FairToy namespace."""

    return logging.getLogger(name if name.startswith("fairtoy") else f"fairtoy.{name}")


def request_id_from_header(candidate: str | None) -> str:
    """Accept a safe caller-provided ID or create a new correlation ID."""

    if candidate is not None and _VALID_REQUEST_ID.fullmatch(candidate):
        return candidate
    return uuid.uuid4().hex


def set_request_id(value: str) -> Token[str | None]:
    return _REQUEST_ID.set(value)


def reset_request_id(token: Token[str | None]) -> None:
    _REQUEST_ID.reset(token)


def current_request_id() -> str | None:
    return _REQUEST_ID.get()


def log_event(
    logger: logging.Logger,
    event: str,
    *,
    level: int = logging.INFO,
    **fields: Any,
) -> None:
    """Emit a small logfmt-like event without logging arbitrary payloads."""

    values = {"request_id": current_request_id(), **fields}
    parts = [f"event={event}"]
    parts.extend(
        f"{key}={json.dumps(value, default=str, separators=(',', ':'))}"
        for key, value in sorted(values.items())
        if value is not None
    )
    logger.log(level, " ".join(parts))


__all__ = [
    "REQUEST_ID_HEADER",
    "configure_logging",
    "current_request_id",
    "get_logger",
    "log_event",
    "request_id_from_header",
    "reset_request_id",
    "set_request_id",
]
