import logging
from datetime import datetime, timezone

import wmill
from openai import OpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)

VALID_SEVERITIES = {"critical", "warning", "info"}

# When dry_run = True, don't use API
_DRY_RUN_STUB = {
    "service": "payments-api",
    "severity": "critical",
    "message": "Redis connection pool exhausted, blocking payments-api requests.",
    "summary": (
        "Redis connection pool exhaustion is causing HTTP 500 errors in payments-api."
    ),
    "probable_cause": (
        "Pool size too small for current traffic; increase max_connections or add a "
        "circuit breaker."
    ),
}

class AlertClassification(BaseModel):
    service: str
    severity: str
    message: str
    summary: str
    probable_cause: str

def _classify_with_llm(raw_message: str, host: str) -> dict:
    api_key = wmill.get_variable("u/ianebcondon/honorable_openai")
    client = OpenAI(api_key=api_key)
    
    # Short task so cheaper model
    resp = client.responses.parse(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "system",
                "content": (
                    "You are an SRE assistant that classifies infrastructure alerts from raw log or stack-trace text."
                    "Infer the affected service, a severity of exactly 'critical', 'warning', or 'info', a short human-readable one-line message replacing the raw text, a one-sentence summary, and a one-sentence probable cause."
                ),
            },
            {"role": "user", "content": f"Host: {host}\nRaw log:\n{raw_message}"},
        ],
        text_format=AlertClassification,
    )
    return resp.output_parsed.model_dump()

def main(payload: dict, dry_run: bool = False) -> dict:
    # Skip LLM call for dry run
    if dry_run:
        logger.info("DRY RUN: skipping LLM call for alert_id=%s", payload["alert_id"])
        classification = dict(_DRY_RUN_STUB)
    else:
        classification = _classify_with_llm(payload["message"], payload["host"])

    # Validation
    if classification["severity"] not in VALID_SEVERITIES:
        raise ValueError(f"Model returned invalid severity.")

    logger.info(
        "classified alert_id=%s service=%s severity=%s",
        payload["alert_id"], classification["service"], classification["severity"],
    )

    triggered_at_iso = (
        datetime.fromtimestamp(payload["triggered_at"], tz=timezone.utc)
        .strftime("%Y-%m-%dT%H:%M:%SZ")
    )

    return {
        "alert_id": payload["alert_id"],
        "host": payload["host"],
        "triggered_at": triggered_at_iso,
        **classification,
        "dry_run": dry_run,
    }
    