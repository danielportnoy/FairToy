import logging

from fairtoy.observability import (
    get_logger,
    log_event,
    reset_request_id,
    set_request_id,
)


def test_log_event_includes_request_context(caplog) -> None:
    token = set_request_id("request-123")
    try:
        with caplog.at_level(logging.INFO, logger="fairtoy.test"):
            log_event(
                get_logger("test"),
                "example_event",
                item_count=3,
            )
    finally:
        reset_request_id(token)

    message = next(
        record.getMessage()
        for record in caplog.records
        if record.name == "fairtoy.test"
    )
    assert "event=example_event" in message
    assert "item_count=3" in message
    assert 'request_id="request-123"' in message
