import logging
import random
import time

logger = logging.getLogger(__name__)


class SlackDeliveryError(Exception):
    """Raised by the stubbed POST call to simulate a failure."""


def _post_to_slack_stub(channel: str, body: dict) -> dict:
    """Stand-in for a POST to Slack's chat.postMessage endpoint."""
    if random.random() < 0.3:
        raise SlackDeliveryError("simulated transient network error")
    return {"ok": True}


def main(event: dict, dry_run: bool = False) -> dict:
    if event is None:
        raise ValueError("event is required and cannot be None")

    channel = event["channel"]

    body = {
        "channel": channel,
        "text": f"[{event['severity'].upper()}] {event['service']}: {event['message']}",
        "alert_id": event["alert_id"],
        "service": event["service"],
        "severity": event["severity"],
        "message": event["message"],
        "host": event["host"],
    }

    # Optional notification fields from AI
    if event.get("summary"):
        body["summary"] = event["summary"]

    if event.get("probable_cause"):
        body["probable_cause"] = event["probable_cause"]

    if dry_run:
        logger.info(
            "DRY RUN: would POST to Slack channel=%s body=%s",
            channel,
            body,
        )
        return {
            "alert_id": event["alert_id"],
            "channel": channel,
            "ok": True,
            "attempts": 1,
            "dry_run": True,
        }

    max_attempts = 3
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            _post_to_slack_stub(channel, body)

            return {
                "alert_id": event["alert_id"],
                "channel": channel,
                "ok": True,
                "attempts": attempt,
                "dry_run": False,
            }

        except SlackDeliveryError as e:
            last_error = e

            logger.warning(
                "Slack delivery attempt %d/%d failed: %s",
                attempt,
                max_attempts,
                e,
            )

            if attempt < max_attempts:
                time.sleep(2 ** (attempt - 1))

    return {
        "alert_id": event["alert_id"],
        "channel": channel,
        "ok": False,
        "attempts": max_attempts,
        "dry_run": False,
        "error": str(last_error),
    }