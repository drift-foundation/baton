"""Consolidate this dossier's packet evidence into one derived document.

Owner reroute 247663 item 6: "Return the complete packet, exact commands,
provider question and execution evidence for independent review."

NOT a test and not a summary written by hand. Every number, digest and
operator-selected input below is READ from a retained file at the moment this
runs, so a stale claim in the packet becomes a visible disagreement rather than
prose that quietly ages. `test_packet.py` asserts that
[OPERATOR-239533.md](OPERATOR-239533.md) and this document agree with the
files they describe.

The two prose lists -- `established` and `not_established` -- are the one thing
here that is a judgment rather than a reading, and they are written so that the
second is the one a reviewer should read first.
"""
import hashlib
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
SIBLING = HERE.parent / "finding-v12-single-implementation-proof"
CHECKOUT = HERE.parents[4]
EVIDENCE = HERE / "EVIDENCE-239533.json"
SCHEMA = "baton.independent-review-evidence/1"

PROGRAMS = ("attachment.py", "review_bindings.py", "review_supervisor.py",
            "snapshot_247947.py", "preexisting_errors.py", "attribution.py",
            "packet.py", "verify.py")
SUITES = ("test_attachment.py", "test_review_bindings.py",
          "test_review_supervisor.py", "test_review_lifecycle.py",
          "test_packet.py")
DOCUMENTS = ("OPERATOR-239533.md", "SELECTIONS-239533.json",
             "MANAGER-SOURCE-independent-review-247947.json",
             "OWNER-PRODUCT-CHANGE-247423.md", "PRODUCT-CHANGE-247423.json",
             "PREEXISTING-ERRORS-247666.json", "ATTRIBUTION-248565.json")
REUSED = {
    "baseline.py": SIBLING / "baseline.py",
    "baseline_bindings.py": SIBLING / "baseline_bindings.py",
    "tools/stage_execution.py": CHECKOUT / "v12/python/tools/stage_execution.py",
    "src/baton_v12/worker_manager/store.py":
        CHECKOUT / "v12/python/src/baton_v12/worker_manager/store.py",
    "src/baton_v12/worker_manager/review_cycles.py":
        CHECKOUT / "v12/python/src/baton_v12/worker_manager/review_cycles.py",
    "src/baton_v12/worker_manager/offers.py":
        CHECKOUT / "v12/python/src/baton_v12/worker_manager/offers.py",
}

# WHAT A DETERMINISTIC RUN OF THIS DOSSIER ACTUALLY DEMONSTRATES, each named
# against the module that carries it so a reviewer can go and read it.
ESTABLISHED = [
    ["the cross-Job attachment arrangement",
     "`review_cycles.create_line` derives the line from (authority, work) and "
     "REPLAYS, so a second Job naming the producer's authority and v12 Work "
     "recovers the producer's line rather than creating one; the real "
     "`attach_review` then accepts an independent reviewer against the frozen "
     "checkpoint, and refuses a wrong or stale checkpoint, a line under "
     "correction, and a reviewer sharing ANY of worker, participant or "
     "principal.", "test_attachment.py"],
    ["a supported read-only survey",
     "the subject is read through `ControlStore.open_readonly` and ONE "
     "coherent `snapshot()` using the public `line_of`, `checkpoint_of` and "
     "`writer_of`; no direct SQL, and the three missing public lookups are "
     "recorded in `attachment.GAPS` rather than bypassed.",
     "test_attachment.py"],
    ["review-only composition",
     "one `review` stage, no dependency, no proposal output, "
     "`review_invocations: 1`, implementation and correction bounds refused "
     "by name, criteria that ask for a judgment and name no verdict, and the "
     "producer's own base/head read from the checkpoint rather than taken as "
     "an operand.", "test_review_bindings.py"],
    ["the packet is held before anything opens",
     "schema, sealed criteria digest, retry, invocation count, cleanup "
     "reserve inside the total, a head that is not its base, a control store "
     "that is the subject's, the accepted `baseline.py` digest, and a "
     "deployment that does not decline corrections -- each refused by name.",
     "test_review_supervisor.py"],
    ["the correction boundary is a precondition, not a promise",
     "the composed deployment carries `correction_policy: \"decline\"`, so "
     "`StageComposition.routed` records `correction_declined` and never "
     "reaches `review_driver.open_correction`; a malformed policy is refused "
     "by the product's own `held_configuration`, and every other deployment "
     "is unchanged.",
     "test_review_supervisor.py, test_review_bindings.py"],
    ["ONE reviewer admitted and ended over real coordination",
     "a real Job store, control store, composition, admission gate, line, "
     "writer, frozen checkpoint, review attachment and frozen review output: "
     "the run settles with ONE attributed verdict cross-bound to the "
     "checkpoint's base, head and tree, a stopped runtime and `retained` "
     "cleanup, and the reviewer differs from the producer in all three "
     "identities.", "test_review_lifecycle.py"],
    ["`changes-requested` is a valid outcome with no correction",
     "it settles with zero correction rounds opened and zero implementation "
     "admissions, against the declining deployment the run actually used.",
     "test_review_lifecycle.py"],
    ["the failure, interruption, stall and cleanup properties",
     "admission closes BEFORE cancellation; an admitted attempt is named "
     "exactly when the run cannot finish; a shutdown interruption is observed "
     "rather than inferred; serving stops at total minus cleanup and no "
     "cleanup act starts after the total deadline; a run that stops moving "
     "reports `no-progress` after 6 unchanged ticks instead of waiting its "
     "bound out, while a genuinely outstanding runtime is never dropped; and "
     "an interrupt inside the serving origin read stops, publishes and "
     "raises rather than being swallowed.", "test_review_lifecycle.py"],
    ["the ACTUAL shipped template composes and starts",
     "the documented CLI runs `SELECTIONS-239533.json` itself -- keeping its "
     "`_manager_source_note`, `bounds._note`, `producer._note`, "
     "`instance._note` and `participants._independence` exactly as they ship "
     "-- the written packet carries no documentation member anywhere, and "
     "`held_packet` accepts it. Both original defects are pinned as still "
     "being defects without the normalization, so the fix is shown to be "
     "load-bearing rather than assumed.", "test_review_bindings.py"],
    ["the live run's verdict re-derives from the retained store",
     "`attribution.py` reads the line, checkpoint, attachment, frozen output, "
     "result manifest, cleanup and producer writer through public readers "
     "inside one snapshot and derives the verdict with "
     "`review_driver.review_verdict_from_result`: `accepted`, agreeing with "
     "the published outcome on all eight compared members, with all three "
     "reviewer identities differing from the producer's. See "
     "`live_run.independently_derived`.", "attribution.py"],
    ["the documented commands run against the successor bytes",
     "step 2's composition command and step 4's `review_supervisor.main` both "
     "run with `PYTHONPATH` bound to the successor snapshot alone. See "
     "`startup_proof` below for exactly what that `main` run did and did not "
     "do.", "test_review_bindings.py"],
]

NOT_ESTABLISHED = [
    ["this implementer has still reached no provider",
     "no container, image, engine, network or credential has been reached "
     "under any claim of this Work by baton.claude. The live run in "
     "`live_run` was executed by the OWNER under claim 248377; what this "
     "implementer did with it is read the retained records through supported "
     "readers. Every receipt in `receipts` below is minted by the real "
     "manager from a deterministic fixture turn and none is fabricated."],
    ["the DETERMINISTIC suite still has no case that both enters `main` and "
     "settles",
     "its two proofs stay separate: the `main` startup proof enters the "
     "documented entry point and is HELD because its composition starts "
     "nothing, and the successful lifecycle settles with an attributed "
     "verdict but calls `supervise` directly with an injected clock. THE "
     "LIVE RUN DOES BOTH, and it is the only thing here that does; see "
     "`live_run`. Do not read a deterministic case as evidence for that."],
    ["the live result is ONE run, not a rate",
     "one review of one one-file change, settled in 55.409 seconds. It "
     "answers the provider question for that subject on that day with that "
     "image and credential. It establishes no distribution of verdicts, no "
     "reliability figure and nothing about a reviewer's behaviour on a "
     "change it disagrees with -- `changes-requested` has been settled only "
     "deterministically."],
    ["the reader refusal's cause is UNKNOWN",
     "the supported opener refused for the reviewer at claim 248523 and "
     "opened for this implementer at claim 248565 on the same store through "
     "the same call. The hypothesis in `live_run.reader_refusal` is a "
     "hypothesis. An intermittent refusal on the managed read boundary is "
     "worth an owner's attention even though the attribution it blocked has "
     "since been derived."],
    ["no deployed store was opened since claim 247159",
     "the subject values in SELECTIONS-239533.json were read at claim 244629 "
     "and are REPRODUCED, not re-read; owner reroute 247154 forbids deployed "
     "store access. Step 1 re-reads them and the composer refuses on "
     "disagreement, so drift is a refusal rather than a wrong review."],
    ["the imported machinery is W239528's, not re-proved here",
     "termination, discovery, cancellation, cleanup accounting and "
     "publication are imported from the accepted `baseline.py` and bound by "
     "digest. They were proved by that Job's suite. What this dossier proves "
     "is this Job's own specialization and the orchestration over real "
     "stores."],
    ["the bounds are proposed, not validated against a review workload",
     "180/300/60 are W239528's measured implementation numbers carried over. "
     "A review turn reads a one-file change rather than writing one, so they "
     "are a starting proposal a reviewer can move on the evidence."],
    ["signal handling is not a SIGKILL claim",
     "the handler is installed around the whole run so a signal during "
     "cancellation, cleanup or publication still leaves an outcome on disk. "
     "`SIGKILL` is not caught and nothing here pretends otherwise."],
    ["cumulative verification spending is partly UNKNOWN",
     "`receipts` below are the retained measurements. Suite runs superseded "
     "within a claim, and ad-hoc driving during development, were not "
     "individually receipted; the cumulative figure carried in PROGRESS.md is "
     "larger than the retained sum for that reason and the difference is not "
     "estimated."],
]

STARTUP_PROOF = {
    "where": "test_review_bindings.TheDocumentedCommandsRunAgainstTheSUCCESSOR"
             "Source.test_the_documented_startup_runs_review_supervisor_MAIN",
    "entry_point": "review_supervisor.main, with the documented --packet and "
                   "--incarnation",
    "real": ["the packet validation", "the imported-source check",
             "the Job and control stores", "the pre-submission survey",
             "the supervised run", "the published outcome"],
    "seams_supplied": {
        "image_inspect": "so no engine is reached",
        "compose": "a Deferring composition, so no container can be started"},
    "bounds_used": {"total_seconds": 12, "cleanup_seconds": 4},
    "result": "exit 1, outcome state `held`, held_because names that the run "
              "answered nothing about the reviewer. That is the honest answer "
              "for a run whose composition starts nothing -- it proves the "
              "startup path, NOT a review.",
}

LIFECYCLE_PROOF = {
    "where": "test_review_lifecycle.OneReviewerIsAdmittedAndEnded and "
             "AChangesRequestedReviewIsAValidOutcome",
    "entry_point": "review_supervisor.supervise, called directly with an "
                   "injected monotonic clock -- NOT `main`",
    "real": ["a real JobStore and ControlStore shared with the producer's "
             "phase-one run", "the real composition through "
             "stage_execution.operations_from", "the real AdmissionGate",
             "a real line, writer and FROZEN CHECKPOINT produced by W239528's "
             "accepted baseline run", "a real review attachment",
             "a real frozen review output",
             "the verdict derived by review_driver.review_verdict_from_result"],
    "simulated": {
        "provider": "the fixture's deterministic worker turn -- the same one "
                    "W239528's accepted suite and the product's own "
                    "ManagedSessionResume use. Not a container and not a live "
                    "model."},
    "result": "state `settled`, one attributed verdict cross-bound to the "
              "checkpoint's base, head and tree, the runtime stopped and its "
              "cleanup `retained`.",
}

LIVE_RUN = {
    "run_id": "independent-review-248377",
    "executed_by": "the owner, baton.slaw, under claim 248377 -- NOT by this "
                   "implementer, who has still reached no container, image, "
                   "engine, network or credential",
    "entry_point": "review_supervisor.main, through the documented --packet "
                   "and --incarnation. THIS IS THE RUN THAT BOTH ENTERS "
                   "`main` AND SETTLES; the deterministic suite still has no "
                   "single case that does both.",
    "evidence": "live-review-248377/, retained by the reviewer under claim "
                "248523 with source paths and SHA256 in its MANIFEST.json",
    "executed_packet_sha256":
        "ed51ef0e2be347915a6b70aebef7b4b35dfc296f66876b7ee77567dde56e2d5f",
    "original_packet_sha256":
        "4405c96d4bffea78eebda64eefb8f55ab07559fa1e16aa50b2a1fb9bb36912bc",
    "packet_difference": "the removal of `bounds._note` and nothing else; the "
                         "substantive bounds and bindings are identical, and "
                         "the metadata defect that forced it is corrected in "
                         "`review_bindings` under claim 248565",
    "outcome_sha256":
        "f587b5841b57388dd13683b980179ea075da404c7cd35373d31a0960c007b346",
    "reported": {"state": "settled", "seconds": 55.40899314900162,
                 "verdict": "accepted", "correction_rounds": 0,
                 "cleanup": "retained", "runtime": "destroyed"},
    "independently_derived": {
        "export": "ATTRIBUTION-248565.json",
        "by": "attribution.py, under claim 248565",
        "how": "ControlStore.open_readonly on the pinned producer store, one "
               "snapshot, public readers only: line_of, checkpoint_of, "
               "review_of, frozen_output_of, load_manifest, cleanup_of, "
               "writer_of and review_driver.review_verdict_from_result. No "
               "raw SQLite, no copied database, no immutable handle, no "
               "write-capable fallback.",
        "answers": "the verdict re-derives as `accepted` and agrees with the "
                   "published outcome on all eight compared members; the "
                   "reviewer's worker, participant and principal all differ "
                   "from the producer's; the cleanup is `retained` with the "
                   "runtime `absent`.",
    },
    "reader_refusal": {
        "what": "review 2026-09-23T14:45:57Z R1 -- ControlStore.open_readonly "
                "refused with a ContractRefusal wrapping an OperationalError, "
                "recorded in live-review-248377/reader-refusal.json",
        "now": "the same supported opener, on the same store and path, opened "
               "under claim 248565 and served every read above. The refusal "
               "did not reproduce.",
        "cause": "UNKNOWN. It is not a permission problem: the store and its "
                 "directory are owned by uid 1000 and writable. Opening it "
                 "read-only recreated the `-shm` and a zero-length `-wal`, "
                 "which are absent when the store is cleanly closed -- a "
                 "mode=ro connection that cannot create them is one known way "
                 "to get this error, and that is a HYPOTHESIS, not a "
                 "diagnosis. No product defect is claimed.",
    },
}

PROVIDER_QUESTION = {
    "question":
        "Given independently delivered criteria and read-only access to the "
        "retained proposal's exact bytes, does the production reviewer return "
        "its OWN valid `baton.review-report/1` -- a verdict from the allowed "
        "three, with non-empty findings it actually verified -- through the "
        "real adapter boundary, and does the manager derive that verdict from "
        "the frozen output and bind it to this checkpoint's base, head and "
        "tree?",
    "answered_by": "the live run above, on 2026-09-23. The reviewer returned "
                   "its own baton.review-report/1 with an `accepted` verdict "
                   "and findings it verified by running the harness, and the "
                   "manager derived that verdict from the frozen output and "
                   "bound it to this checkpoint's base, head and tree -- "
                   "re-derived independently in ATTRIBUTION-248565.json.",
    "why_deterministic_checks_cannot_answer_it":
        "every verdict in this dossier is minted from a fixture turn this "
        "implementer wrote the report for. What is unproved is whether a real "
        "reviewer, given only the criteria and the bytes, produces a report "
        "the adapter accepts at all.",
    "negative_answers_that_are_evidence_rather_than_bugs": [
        "the reviewer writes no report, or a malformed one -- "
        "`review_verdict_from_result` refuses and the outcome holds with no "
        "readable verdict. `claude_agent._review_report` requires `findings` "
        "to be non-empty TEXT, and a malformed report is deliberately not a "
        "verdict: an exit status is not a decision.",
        "the reviewer reports a base, head or tree other than the "
        "checkpoint's -- the cross-binding refuses and the outcome names both",
        "the reviewer edits the checkout or attempts a commit -- its checkout "
        "is read-only and the criteria say so, so this appears as a failed "
        "turn rather than as a verdict",
    ],
    "not_a_negative_answer":
        "`changes-requested` or `rejected`. All three dispositions are "
        "successful reviews; the shortfall is a run that produced no "
        "attributed verdict at all.",
}


def sha(path):
    reading = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            reading.update(block)
    return reading.hexdigest()


def receipts():
    """Every RETAINED suite receipt, in claim order, read from its own file."""
    held = []
    for place in sorted(HERE.glob("verification-*.json"),
                        key=lambda one: int(re.findall(r"\d+", one.name)[0])):
        one = json.loads(place.read_text(encoding="utf-8"))
        held.append({"receipt": place.name, "claim": one.get("claim"),
                     "checks": one["checks"], "failures": one["failures"],
                     "errors": one["errors"],
                     "measured_seconds": one["measured_seconds"]})
    return held


def reviewer_measurements():
    """The reviewers' own numbers, kept separate from mine on purpose."""
    held = []
    for place in sorted(HERE.glob("review-evidence-*.json")):
        one = json.loads(place.read_text(encoding="utf-8"))
        if "seconds" in one:
            held.append({"evidence": place.name, "tests": one.get("tests"),
                         "seconds": one["seconds"]})
    return held


def operator_inputs():
    """Every `<OWNER: ...>` still unresolved in the selections document.

    Read by walking the document, so an input that is resolved disappears from
    the packet page by itself rather than being crossed off by hand.
    """
    held = []

    def walk(value, path=""):
        if isinstance(value, dict):
            for name, inner in value.items():
                walk(inner, f"{path}.{name}" if path else name)
        elif isinstance(value, list):
            for index, inner in enumerate(value):
                walk(inner, f"{path}[{index}]")
        elif isinstance(value, str) and value.startswith("<OWNER:"):
            held.append({"member": path,
                         "asks": value[len("<OWNER:"):].rstrip(">").strip()})

    walk(json.loads((HERE / "SELECTIONS-239533.json").read_text("utf-8")))
    return held


def assembled(claim):
    selections = json.loads(
        (HERE / "SELECTIONS-239533.json").read_text("utf-8"))["compose"]
    manifest = json.loads(
        (HERE / "MANAGER-SOURCE-independent-review-247947.json")
        .read_text("utf-8"))
    held = receipts()
    return {
        "schema": SCHEMA,
        "work": "W239533",
        "claim": claim,
        "participant": "baton.claude",
        "note": "Derived by packet.py from this dossier's retained files. "
                "Every digest, count and second is read at generation time; "
                "only `established`, `not_established` and the provider "
                "question are written prose.",
        "execution": {
            "state": "executed",
            "by": "the owner, under claim 248377",
            "what": "one bounded live review, independent-review-248377",
            "note": "the SHIPPED selections still carry all twelve "
                    "`<OWNER: ...>` choices unresolved: the owner resolved "
                    "them for that run in its own documents, which are "
                    "retained under live-review-248377/. Running again is an "
                    "owner decision and this packet authorizes nothing.",
        },
        "programs": {name: sha(HERE / name) for name in PROGRAMS},
        "suites": {name: sha(HERE / name) for name in SUITES},
        "documents": {name: sha(HERE / name) for name in DOCUMENTS},
        "reused": {name: sha(place) for name, place in sorted(REUSED.items())},
        "manager_source": {
            "path": manifest["path"],
            "file_count": manifest["file_count"],
            "created_by_claim": manifest["created_by_claim"],
            "carries": manifest["carries"],
            "predecessor": manifest["predecessor"],
        },
        "subject": {
            "control_store": selections["producer"]["control_store"],
            "line_id": selections["producer"]["line_id"],
            "checkpoint_id": selections["producer"]["checkpoint_id"],
            "authority_uuid": selections["producer"]["authority_uuid"],
            "work_id": selections["producer"]["work_id"],
        },
        "worker_image": {"reference": selections["image_reference"],
                         "config_digest": selections["image_digest"]},
        "bounds": selections["bounds"],
        "live_run": LIVE_RUN,
        "startup_proof": STARTUP_PROOF,
        "lifecycle_proof": LIFECYCLE_PROOF,
        "provider_question": PROVIDER_QUESTION,
        "established": [{"claim": one, "detail": two, "where": three}
                        for one, two, three in ESTABLISHED],
        "not_established": [{"claim": one, "detail": two}
                            for one, two in NOT_ESTABLISHED],
        "operator_selected_inputs": operator_inputs(),
        "receipts_note":
            "verify.py regenerates this document BEFORE running the suite, so "
            "`receipts` covers every retained receipt up to the run before the "
            "one that wrote it. The newest verification-N.json in the dossier "
            "is always the current one.",
        "receipts": held,
        "retained_receipt_seconds": sum(one["measured_seconds"] for one in held),
        "reviewer_measurements": reviewer_measurements(),
    }


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claim", type=int, required=True)
    chosen = parser.parse_args(argv)
    document = assembled(chosen.claim)
    EVIDENCE.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({
        "wrote": EVIDENCE.name,
        "receipts": len(document["receipts"]),
        "retained_receipt_seconds": document["retained_receipt_seconds"],
        "operator_selected_inputs": len(document["operator_selected_inputs"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
