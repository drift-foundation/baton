"""Closed review-report observations and their operator words; no decisions."""

# Mirrored by the dependency-free tools.job_observation renderer; tests bind
# the closed words so standalone status readers need no manager imports.
REPORT_STATES = ("missing", "empty", "malformed", "unclassified", "usable", "not-read")


def review_report_sentence(observation):
    """Unknown evidence never supplies a sentence; historical evidence is classified upstream."""
    if not isinstance(observation, dict) or observation.get("known") is not True:
        return ""
    state = observation.get("value")
    if state in ("missing", "empty", "malformed"):
        return "Review held: review report " + state
    if state == "unclassified":
        return "Review held: no usable report"
    return ""
