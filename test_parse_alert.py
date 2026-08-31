# test: script/u/ianebcondon/parse_alert
import wmill
from u.ianebcondon.parse_alert import main as parse_alert

VALID_PAYLOAD = {
    "alert_id": "ALT-4892",
    "service": "payments-api",
    "severity": "critical",
    "message": "HTTP 5xx error rate exceeded 5% over a 5-minute window",
    "host": "prod-payments-01",
    "triggered_at": 1742046720,
}


def main():
    # Good path, dry_run is True so there are no downstream side effects
    result = parse_alert(payload=VALID_PAYLOAD, dry_run=True)
    assert result["dry_run"] is True
    assert result["alert_id"] == "ALT-4892"
    assert result["severity"] == "critical"

    # Bad payload missing required field
    bad_payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "service"}
    try:
        parse_alert(payload=bad_payload, dry_run=True)
        raise AssertionError("Expected parse_alert to reject a payload missing 'service'")
    except Exception as e:
        print(str(e))
        assert "service" in str(e)

    # Bad path: unrecognized severity. Bad field should fail loudly
    bad_severity = {**VALID_PAYLOAD, "severity": "banana"}
    try:
        parse_alert(payload=bad_severity, dry_run=True)
        raise AssertionError("Expected an exception to be thrown.")
    except Exception as e:
        assert "severity" in str(e).lower()