import wmill
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = {"alert_id", "service", "severity", "message", "host", "triggered_at"}
VALID_SEVERITIES = {"critical", "warning", "info"}


def main(payload: dict, dry_run: bool = False) -> dict:
    """Validate and normalize an incoming alert webhook payload.

    Args:
        payload: Raw JSON body from the monitoring webhook.
        dry_run: When True, validate and log but skip all side-effects.

    Returns:
        Normalized alert dict with ``triggered_at`` converted to ISO-8601.
    """

    # Validation
    if not isinstance(payload, dict):
        raise ValueError(
            f"payload must be a dictionary"
        )

    missing = REQUIRED_FIELDS - payload.keys()

    if missing:
        raise ValueError(
            f"Missing required fields: {missing}"
        )

    if payload["severity"] not in VALID_SEVERITIES:
        raise ValueError(
            f"Invalid severity: {payload['severity']}"
        )

    if not isinstance(payload["triggered_at"], int):
        raise ValueError(
            f"triggered_at must be an integer Unix timestamp"
        )

    #Logging
    logger.info(
        "Processing alert_id=%s service=%s severity=%s",
        payload["alert_id"],
        payload["service"],
        payload["severity"],
    )
    # Logger.info not printing in Logs section so added print
    print(
        f"INFO: Processing alert_id={payload['alert_id']} "
        f"service={payload['service']} "
        f"severity={payload['severity']}"
    )

    # Dry run
    if dry_run:
         # Logger.info not printing in Logs section so added print

        print(
            f"INFO: DRY RUN - skipping downstream side effects "
            f"for alert_id={payload['alert_id']}"
        )
        logger.info(
            "DRY RUN: skipping downstream side effects for alert_id=%s",
            payload["alert_id"],
        )
        return {**payload, "dry_run": True}

    # Timestamp conversion
    timestamp = datetime.fromtimestamp(
        payload["triggered_at"],
        tz = timezone.utc,
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        **payload,
        "triggered_at": timestamp,
        "dry_run": False,
    }