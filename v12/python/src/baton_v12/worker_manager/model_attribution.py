"""Immutable model selection and attribution, owned beside frozen results.

No current deployment defaults can upgrade a missing producer record. Legacy
attempts have no selected contract and take their original ending unchanged.
"""
from ..contracts import ContractRefusal, digest
from .. import provider_policy
from ..provider_policy import attribution
from .store import manager_signature
from . import attempts, attempt_logs, image_receipts


def _id(kind, attempt):
    return kind + ":" + digest(attempt)[7:]


def _read(control, kind, attempt):
    operation = _id(kind, attempt)
    row = control.operation_record(operation)
    if row is None:
        return None
    if row["kind"] != kind or row["state"] != "committed":
        raise ContractRefusal("integrity", "schema", "model attribution owner record disagrees")
    return control.replay(operation, row["signature"], kind=kind)[1]


def _write(control, kind, attempt, value):
    return control.transact(_id(kind, attempt), kind, manager_signature(kind, value), lambda connection: value)


def select(control, delivery, *, phase, logs_root, home_root=None):
    attempt = delivery["attempt_id"]
    row = attempts.attempt_runtime_of(control, attempt)
    if row is None or row["execution_runtime"] not in ("not-started", "start-requested"):
        previous = selection_of(control, attempt)
        if previous != {"delivery": delivery, "phase": phase, "logs_root": logs_root, "home_root": home_root}:
            raise ContractRefusal("integrity", "schema", "model selection cannot change after runtime start")
        return previous
    return _write(control, "provider.selection", attempt,
                  {"delivery": delivery, "phase": phase, "logs_root": logs_root, "home_root": home_root})


def selection_of(control, attempt):
    return _read(control, "provider.selection", attempt)


def assessment_of(control, attempt):
    return _read(control, "provider.attribution", attempt)


def assess(control, attempt, frozen=None):
    from . import frozen_output_of, load_manifest
    selected = selection_of(control, attempt)
    if selected is None:
        return None
    frozen = frozen if frozen is not None else frozen_output_of(control, attempt)
    if frozen is None:
        raise ContractRefusal("integrity", "schema", "attribution requires a frozen producer result")
    result = load_manifest(control, frozen["manifest_digest"], "resultManifest")
    claims = [value if type(value) is dict and value.get("schema") == key else None for one in result["outputs"] if one.get("status") == "present"
              for key, value in one.get("result_metadata", {}).items()
              if key.startswith("baton.model-attribution/")]
    raw = attempt_logs.complete_record(attempt_logs.AttemptLogs(root=selected["logs_root"], attempt_id=attempt),
                                       "provider.stdout", limit=attribution.MAX_OUTPUT)
    claim = claims[0] if len(claims) == 1 else None
    # W385853: the execution-context label the worker says it prefixed is
    # recomputed from the admitted adapter and launch role. It is judged
    # first: a turn that ran under the wrong or no label is held for that.
    labels = [one["result_metadata"][provider_policy.LABEL_SCHEMA]
              for one in result["outputs"] if one.get("status") == "present"
              and provider_policy.LABEL_SCHEMA in one.get("result_metadata", {})]
    try:
        expected_label = provider_policy.context_record(selected["delivery"]["contract"]["adapter"], selected["phase"])
    except (ValueError, KeyError, TypeError, IndexError):
        expected_label = None
    label_cause = ("context-label-missing" if len(labels) != 1 else
                   None if expected_label is not None and labels[0] == expected_label else "context-label-mismatch")
    cause = "model-attribution-missing"
    accepted = None
    if claim is not None and raw is not None:
        try:
            accepted = attribution.validate(claim, selected["delivery"], phase=selected["phase"], raw=raw,
                invocation_raw=_invocation_receipt(selected, attempt))
            cause = None if attribution.acceptable(accepted) else "model-attribution-" + accepted["outcome"]
        except ValueError:
            cause = "model-attribution-invalid"
    image_receipt, image_cause = image_receipts.evidence(control, attempt, selected)
    cause = label_cause or cause or image_cause
    account = {"attempt_id": attempt, "job_id": selected["delivery"]["home_identity"]["job_id"],
               "result_id": frozen["result_id"], "manifest_digest": frozen["manifest_digest"],
               "selection_digest": digest(selected["delivery"]), "attribution": accepted,
               "context_label": expected_label if label_cause is None else None,
               "outcome": "matched" if cause is None else "held", "cause": cause}
    if image_receipts.required(selected):
        account["launched_image"] = image_receipt
        account["launched_image_receipt"] = image_receipts.reference(attempt, image_receipt)
    previous = assessment_of(control, attempt)
    if previous is not None and previous != account:
        # The frozen decision is not silently upgraded after a log is replaced.
        raise ContractRefusal("integrity", "digest", "retained model attribution evidence changed")
    return previous or _write(control, "provider.attribution", attempt, account)


def held(account):
    if account is None or account["outcome"] == "matched":
        return None
    return {"attempt_id": account["attempt_id"], "outcome": "held",
            "reason": account["cause"], "held_reason": account["cause"],
            "cleaned_up": False, "result_id": account["result_id"],
            "manifest_digest": account["manifest_digest"], "model_attribution": account,
            "published": None, "checkpoint_id": None, "verdict_id": None}


def bind_ending(control, attempt, answer):
    account = assessment_of(control, attempt)
    if selection_of(control, attempt) is None:
        return answer
    if account is None or account["outcome"] != "matched":
        raise ContractRefusal("integrity", "schema", "ending lacks matched attribution")
    selected = selection_of(control, attempt)
    if image_receipts.required(selected):
        receipt, cause = image_receipts.evidence(control, attempt, selected)
        if cause is not None or receipt != account.get("launched_image"):
            raise ContractRefusal("integrity", "digest", "launched-image binding changed before ending")
    binding = {"attempt_id": attempt, "result_id": account["result_id"],
               "manifest_digest": account["manifest_digest"], "assessment_digest": digest(account),
               "checkpoint_id": answer.get("checkpoint_id"), "verdict_id": answer.get("verdict_id")}
    _write(control, "provider.attribution-ending", attempt, binding)
    return dict(answer, model_attribution={**account, **binding})


def recovery_evidence(control, attempt, *, candidate, tree_digest, result_digest, claim):
    """Read the ORIGINAL producer's evidence; inspection has no write effect."""
    selected = selection_of(control, attempt)
    if selected is None:
        return None
    raw = attempt_logs.complete_record(attempt_logs.AttemptLogs(root=selected["logs_root"], attempt_id=attempt),
                                       "provider.stdout", limit=attribution.MAX_OUTPUT)
    if claim is None or raw is None:
        raise ContractRefusal("refused", "precondition", "model-attribution-missing: original producer")
    try:
        checked = attribution.validate(claim, selected["delivery"], phase=selected["phase"], raw=raw,
                invocation_raw=_invocation_receipt(selected, attempt))
    except ValueError as failure:
        raise ContractRefusal("integrity", "digest", "model-attribution-invalid: original producer") from failure
    if not attribution.acceptable(checked):
        raise ContractRefusal("refused", "precondition", "model-attribution-" + checked["outcome"] + ": original producer")
    image_receipt, image_cause = image_receipts.evidence(control, attempt, selected)
    if image_cause is not None:
        raise ContractRefusal("refused", "precondition", image_cause + ": original producer")
    return {**({"launched_image": image_receipt, "launched_image_receipt": image_receipts.reference(attempt, image_receipt)} if image_receipts.required(selected) else {}),
            "attempt_id": attempt, "job_id": selected["delivery"]["home_identity"]["job_id"],
            "candidate": candidate, "tree_digest": tree_digest, "result_digest": result_digest,
            "selection_digest": digest(selected["delivery"]), "attribution": checked}


def bind_recovery(control, binding):
    if binding is not None:
        # One original attempt has one retained candidate. A retry cannot
        # substitute either evidence or candidate under the admitted record.
        return _write(control, "provider.recovery-attribution", binding["attempt_id"], binding)
    return None


def require_recovery(control, binding):
    if binding is None:
        raise ContractRefusal("integrity", "schema", "model-attribution-missing: recovery binding")
    previous = _read(control, "provider.recovery-attribution", binding["attempt_id"])
    if previous != binding:
        raise ContractRefusal("integrity", "digest", "original producer recovery binding disagrees")
    selected = selection_of(control, binding["attempt_id"])
    if image_receipts.required(selected):
        receipt, cause = image_receipts.evidence(control, binding["attempt_id"], selected)
        if cause is not None or receipt != binding.get("launched_image"):
            raise ContractRefusal("integrity", "digest", "original producer launched-image binding changed")
    return binding


def diagnostic_of(control, attempt):
    selected = selection_of(control, attempt)
    if selected is None:
        return attribution.diagnostic(None)
    account = assessment_of(control, attempt)
    value = account.get("attribution") if account else None
    if value is None:
        value = attribution.record(selected["delivery"], phase=selected["phase"], evidenced_build=None, raw=None)
    from . import provider_home
    state = provider_home.status_of(selected.get("home_root"), selected["delivery"]["home_identity"])
    try:
        label = provider_policy.context_record(selected["delivery"]["contract"]["adapter"], selected["phase"])
        context = ("; Native worker role: " + label["role"] + "; context label: " + label["context_label_digest"]
                   + "; worker instructions: " + label["worker_instructions_digest"]
                   + "; label reported: " + ("no evidence" if account is None else
                                             "yes" if account.get("context_label") == label else "no"))
    except (ValueError, KeyError, TypeError, IndexError):
        context = "; Native worker role: unlabelled"
    image_text = ""
    if image_receipts.required(selected):
        receipt, cause = image_receipts.evidence(control, attempt, selected)
        observed = receipt.get("observation", {}).get("image_id") if receipt else None
        image_text = "; host acceptance: " + ("held" if cause is not None else account["outcome"] if account else "not assessed") + "; engine-observed image: " + (observed or "unknown") + "; launched-image binding: " + (cause or "matched")
        if receipt is not None:
            image_text += "; image receipt: " + image_receipts.reference(attempt, receipt)["operation_id"]
    return attribution.diagnostic(value) + image_text + context + "; Provider home: " + state["state"] + "; worker: " + state["worker_id"] + "; holder: " + (state["holder"] or "unknown")


def observed_exchange(control, attempt, document):
    if document is None:
        return None
    return dict(document, model_attribution=diagnostic_of(control, attempt))


def _invocation_receipt(selected, attempt):
    if selected["delivery"]["contract"]["selection"]["provider"] != "codex":
        return None
    return attempt_logs.complete_record(attempt_logs.AttemptLogs(root=selected["logs_root"], attempt_id=attempt),
                                        "provider.invocation", limit=attribution.MAX_OUTPUT)
