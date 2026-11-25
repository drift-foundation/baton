"""Host-retained launched-image evidence, separate from cessation and worker claims."""
import re
from datetime import datetime
from ..contracts import digest
from . import attempts

SCHEMA = "baton.launched-image/1"
KIND = "provider.launched-image"


def required(selected):
    return selected is not None and selected["delivery"]["contract"]["selection"]["provider"] == "codex"


def sha(value):
    return type(value) is str and re.fullmatch(r"sha256:[0-9a-f]{64}", value) is not None


def valid(observation):
    if type(observation) is not dict or set(observation) != {"engine", "runtime_id", "image_id", "started_at", "labels", "resolution"}:
        return False
    if observation["engine"] not in ("docker", "podman") or not sha(observation["image_id"]):
        return False
    if type(observation["runtime_id"]) is not str or not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", observation["runtime_id"]):
        return False
    if type(observation["started_at"]) is not str or len(observation["started_at"]) > 40:
        return False
    try:
        started = datetime.fromisoformat(observation["started_at"].replace("Z", "+00:00"))
        if started.year <= 1 or started.utcoffset() is None:
            return False
    except (ValueError, TypeError, AttributeError):
        return False
    resolution = observation["resolution"]
    return resolution is None or (type(resolution) is dict and set(resolution) == {"image_id", "registry_digest"}
        and resolution["image_id"] == observation["image_id"] and sha(resolution["registry_digest"]))


def retain(control, attempt, runtime_id, observation):
    # Called after engine I/O, never in the transaction that asks the engine.
    from . import model_attribution as owner
    selected = owner.selection_of(control, attempt)
    if not required(selected) or not valid(observation):
        return None
    row = attempts._require_attempt(control, attempt)
    if row is None or row["runtime_id"] not in (None, runtime_id) or observation["runtime_id"] != runtime_id:
        return None
    if observation["labels"] != attempts._runtime_labels(row):
        return None
    previous = owner._read(control, KIND, attempt)
    receipt = {"schema": SCHEMA, "attempt_id": attempt, "selection_digest": digest(selected["delivery"]),
               "admitted_image": selected["delivery"]["contract"]["runtime_profile"].get("image_digest"),
               "profile_digest": selected["delivery"]["profile_digest"],
               "recorded_at": previous["recorded_at"] if previous is not None else control._now(),
               "observation": observation}
    if previous is not None and observation["resolution"] is None:
        # A later unavailable image-resolution query is not contradictory
        # evidence and cannot erase an already retained engine binding.
        without_resolution = dict(previous["observation"], resolution=None)
        if observation == without_resolution:
            return previous
    if previous is not None and previous != receipt:
        # Conflicting observations hold acceptance, not cessation or token release.
        owner._write(control, KIND + "-conflict", attempt, {"conflict": True})
        return previous
    return previous or owner._write(control, KIND, attempt, receipt)


def evidence(control, attempt, selected):
    from . import model_attribution as owner
    if not required(selected):
        return None, None
    receipt = owner._read(control, KIND, attempt)
    if receipt is None:
        return None, "launched-image-missing"
    row = attempts._require_attempt(control, attempt)
    if type(receipt) is not dict:
        return receipt, "launched-image-invalid"
    observation = receipt.get("observation")
    if (set(receipt) != {"schema", "attempt_id", "selection_digest", "admitted_image", "profile_digest", "recorded_at", "observation"}
            or receipt["schema"] != SCHEMA or receipt["attempt_id"] != attempt
            or receipt["selection_digest"] != digest(selected["delivery"])
            or receipt["admitted_image"] != selected["delivery"]["contract"]["runtime_profile"].get("image_digest")
            or receipt["profile_digest"] != selected["delivery"]["profile_digest"] or not valid(observation)
            or row is None or row["runtime_id"] != observation["runtime_id"]
            or observation["labels"] != attempts._runtime_labels(row)
            or owner._read(control, KIND + "-conflict", attempt) is not None):
        return receipt, "launched-image-invalid"
    admitted = selected["delivery"]["contract"]["runtime_profile"].get("image_digest")
    resolution = observation["resolution"]
    if admitted != observation["image_id"] and (resolution is None or admitted != resolution["registry_digest"]):
        return receipt, "launched-image-mismatch"
    return receipt, None


def reference(attempt, receipt):
    if receipt is None:
        return None
    from . import model_attribution as owner
    return {"operation_id": owner._id(KIND, attempt), "digest": digest(receipt)}
