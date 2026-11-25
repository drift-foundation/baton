"""Durable owner items for ordinary-review uncertainty, never verdicts.

Uses the Job store's owner-item journal mechanism. Evidence is re-read through
control owners outside the transaction; no worker text enters the owner item.
"""
import json
from ..contracts import ContractRefusal
from ..worker_manager import attempts, boundaries, frozen_output_of, model_attribution
from . import episodes, review_driver, submission
from .store import job_signature

__all__ = ["KIND", "deliver", "items_of"]
KIND = "review.uncertainty-owner-item"

def deliver(store, control, *, stage, attachment_id, destination, recovery_digest=None):
    boundaries.identity(destination, "the configured review decision recipient")
    claim = review_driver.review_verdict_from_result(control, attachment_id=attachment_id,
        recovery_digest=recovery_digest, _allow_uncertain=True)
    if claim.get("outcome") != "uncertain":
        raise ContractRefusal("refused", "precondition", "only explicit uncertainty delivers this owner item")
    actual = next((row for row in submission.stages_of(store, stage["job_id"])
                   if row["stage_id"] == stage["stage_id"]), None)
    episode = episodes.episode_of(store, stage["stage_id"], stage["episode"])
    fixed = attempts.assignment_of(control, claim["attempt_id"])
    if (actual is None or actual["kind"] != "review" or episode is None
            or episode["attempt_id"] != claim["attempt_id"]
            or actual["work_id"] != fixed["work_id"]
            or store.authority_uuid != fixed["authority_uuid"]
            or destination == fixed["participant"]):
        raise ContractRefusal("integrity", "schema", "uncertainty requires this Job's exact independent review and a distinct owner")
    frozen = frozen_output_of(control, claim["attempt_id"])
    if model_attribution.held(model_attribution.assess(control, claim["attempt_id"], frozen)) is not None:
        raise ContractRefusal("refused", "precondition", "review attribution remains held")
    record = dict(schema="baton.review-uncertainty-owner-item/1", job_id=stage["job_id"],
        stage_id=stage["stage_id"], episode=stage["episode"], destination=destination,
        evidence=claim, verdict=None, automatic_retry=None, state="held-for-owner")
    # Cross-store evidence is already immutable. Recheck the owned episode in
    # the commit, so a concurrent episode change cannot redirect delivery.
    def commit(connection):
        if episodes.episode_of(store, stage["stage_id"], stage["episode"]) != episode:
            raise ContractRefusal("refused", "precondition", "review episode changed before owner delivery")
        return dict(record, delivered_at=store._now())
    return store.transact(KIND + ":" + claim["attempt_id"], KIND,
                          job_signature(KIND, record), commit)

def items_of(store):
    """Read the retained owner queue without any execution capability."""
    rows = store._connection.execute("SELECT result FROM operations WHERE kind = ? AND state = 'committed' ORDER BY rowid", (KIND,)).fetchall()
    return [json.loads(row["result"]) for row in rows]
