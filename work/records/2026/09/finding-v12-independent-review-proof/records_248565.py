"""Claim-248565 dossier entries: the live verdict re-derived, and R2's fix."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

CHECKPOINT = """# Checkpoint -- W239533

Concise per AGENTS.md "Delivery continuity and bounded context". FINDING keeps
the history.

## Current disposition

The owner executed `independent-review-248377` under claim 248377: one bounded
live review, settled in 55.409s, `accepted`, runtime destroyed, cleanup
`retained`, zero corrections. Review 2026-09-23T14:45:57Z retained its evidence
and raised two items, **both of which are now done**.

## Done under claim 248565

### R1 -- the attribution, derived rather than believed

The supported opener that refused for the reviewer OPENED here, on the same
store through the same call, and served every read. `attribution.py` reads the
line, checkpoint, attachment, frozen output, result manifest, cleanup and
producer writer inside ONE snapshot through public readers, and derives the
verdict with `review_driver.review_verdict_from_result`.

`ATTRIBUTION-248565.json`: verdict `accepted`, agreeing with the published
outcome on all eight compared members; the reviewer's worker, participant and
principal all differing from the producer's; cleanup `retained`, runtime
`absent`; the result manifest's assignment matching the attachment's generation
and participant and the packet's Authority and Work. Bound to the executed
packet's digest, the outcome's digest, the deployment configuration's digest
and the retention policy.

NO raw SQLite, copied database, `immutable=` handle or write-capable fallback.
**The refusal's cause remains UNKNOWN** and no product defect is claimed.

### R2 -- the two template defects

`review_bindings.without_documentation` removes `_`-prefixed members
recursively at composition, so neither entry point ever sees prose again.
NEITHER WAS LOOSENED: `compose` still has no `_manager_source_note` operand and
`held_packet` still requires exactly five bounds members. An unknown member
that is not documentation is now refused BY NAME instead of reaching Python as
a `TypeError`.

`TheACTUALShippedTemplateComposesAndStarts` runs the shipped
`SELECTIONS-239533.json` through the real CLI and `held_packet`, asserts the
notes are still in the file, asserts the written packet carries no
documentation member anywhere, and pins BOTH defects as still defects without
the normalization.

## Also true now, and recorded

**The subject has moved.** The line is `accepted` and its attachment `ended`,
so step 1 and the composer now REFUSE this packet. That is correct: a retained
proposal is reviewed once. The operator page says so rather than leaving a
future operator to read the refusal as a defect.

## Next

Independent review of R1 and R2. Then, per the reviewer, accepted delivery goes
to baton.decide for closure.

## Owned paths

This dossier in full, plus one product path under owner selection 247421:
`v12/python/tools/stage_execution.py`, at
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801` and
UNCHANGED this claim. Outside the checkout:
`/home/sl/baton-runs/independent-review-247947/manager-source`, read only.

## Latest review, evidence and positions read

`review-2026-09-23T14-45-57Z.md`; receipt `verification-19.json`; export
`ATTRIBUTION-248565.json`. Last discussion position read: T239533 message
247805. Last event read: 248562.

## Blockers

None.
"""

PROGRESS_ENTRY = """
## 2026-09-23 -- baton.claude, claim 248565

The owner ran the packet. Review 2026-09-23T14:45:57Z retained the evidence and
left two items; both are done.

### R1 -- the reader that refused, and what it holds

The supported `ControlStore.open_readonly` that answered the reviewer with an
`OperationalError` OPENED here -- same store, same path, same call, same pinned
source -- and served every read. **The cause of the earlier refusal is
UNKNOWN.** It is not permissions: the store and its directory are uid 1000 and
writable. Opening it recreated the `-shm` and a zero-length `-wal`, which a
cleanly closed store does not carry, and a `mode=ro` connection that cannot
create them is one known way to get that error -- A HYPOTHESIS, NOT A
DIAGNOSIS. I claim no product defect, and an intermittent refusal on the
managed read boundary is worth an owner's attention even though the attribution
it blocked has since been derived.

`attribution.py` then did what R1 asked. Inside one snapshot, through public
readers only: the line, the checkpoint, the attachment, the frozen output, the
retained result manifest, the cleanup and the producer's writer; the verdict
through `review_driver.review_verdict_from_result`. No raw SQLite, no copied
database, no `immutable=` handle, no write-capable fallback.

`ATTRIBUTION-248565.json` holds it: verdict **`accepted`**, agreeing with the
published outcome on all eight compared members; cleanup `retained` with the
runtime `absent`; the manifest's assignment matching the attachment's
generation and participant and the packet's Authority and Work; bound to the
executed packet, outcome, deployment-configuration digests and the retention
policy.

**One correction I had to make to my own export.** The first version read the
reviewer's identities off the attachment as `worker_id`/`participant`/
`principal`; the row names them `reviewer_*`, so all three came back `None`,
nothing could equal anything, and it reported `independent: true` having
compared NOTHING. A comparison over missing values is the most expensive kind
of false pass, because it looks exactly like a real one. It now refuses when
either side is empty, and the case asserting it checks that both sides are
populated rather than only that the shared set is empty.

### R2 -- the two template defects

Both were the same shape: documentation metadata reaching an execution
boundary. `review_bindings.main` splatted `selections["compose"]`, so
`_manager_source_note` raised `TypeError` before `compose` was entered; and
`compose` copied `bounds` verbatim, so `bounds._note` made `held_packet` refuse
at startup.

`without_documentation` now removes `_`-prefixed members recursively at
composition. **Neither entry point was loosened** -- a packet is an execution
document, and `held_packet` is right to require exactly five bounds members.
An unknown member that is NOT documentation is refused by name, so stripping
prose cannot swallow a typo.

Why the suite missed both: every case wrote its own selections through
`written_selections`, and a document this suite invents has no prose in it.
`TheACTUALShippedTemplateComposesAndStarts` reads the SHIPPED file, keeps its
notes, and drives the real CLI and `held_packet`. It also asserts the notes are
still there -- without that, the class would pass by proving nothing, which is
exactly what its first version did until that case caught it.

### The subject has moved

The line is now `accepted` and its attachment `ended`, so step 1 and the
composer REFUSE this packet. That is the arrangement working: a retained
proposal is reviewed once. The operator page records it so a future operator
does not read that refusal as a defect.

Verification: 151 focused deterministic checks, 0 failures, measured
37.4308637320064s, receipt `verification-19.json` with `verification-19.log`;
38 are new (6 template, 32 packet -- the packet module grew by 7 live-run
cases and had 4 rewritten because the live run made their old assertions
false).

Cumulative MEASURED (suite receipts only) for W239533: 379.725992589 +
37.430863732 = **417.156856321s**. Separately and not folded in: the
preliminary 242-second `main` run under claim 248032, and the OWNER's live run
at 55.409s, which is theirs. Unmeasured ad-hoc driving remains UNKNOWN and is
not estimated; the retained receipts now sum to 219.971773171s in
`EVIDENCE-239533.json`.

The reviewers' independent measurements are theirs and are preserved
separately; claim 248523's probes were each under 0.1s and its wall time was
not measured.

State: returned for independent review. Ordinary continuation per M247805.
"""

OWNERSHIP = """
## Claim 248565 -- the live attribution and the template fix

Edited in this dossier: `review_bindings.py`, `test_review_bindings.py`,
`test_packet.py`, `packet.py`, `OPERATOR-239533.md`, `verify.py`, `PLAN.md`,
`PROGRESS.md`, this file. Added: `attribution.py`, `ATTRIBUTION-248565.json`,
`records_248565.py`, `verification-19.json/.log`, and `EVIDENCE-239533.json`
regenerated.

**NOT edited, and deliberately:** every file under `live-review-248377/` is the
reviewer's retained evidence and was READ ONLY -- the attribution export is a
new file at the dossier's top level rather than an addition to their directory.
`SELECTIONS-239533.json` still ships all twelve `<OWNER: ...>` choices
unresolved; the owner's resolved values live in that run's own documents and
are not copied back. No file under `v12/` was edited and the successor snapshot
was not modified.

**The deployed store WAS OPENED, read-only and through the supported opener.**
That is what R1 asked for and what the owner's 248520 pass authorized
("verify retained subject/result attribution ... through supported readers").
It wrote nothing; SQLite recreated `control.sqlite3-shm` and a zero-length
`control.sqlite3-wal` beside the store, as it did at claim 244629, and they are
left in place.

The product path stays at
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`, W239528's
`baseline.py` at
`f27f3cd766f9271c4b3eddb6c657bca4770d18c11a74f377e717bef23df18fd5`, its
producer snapshot unchanged, both images unchanged, and every reviewer file in
this dossier is append-only history that was not modified.
"""


def main():
    (HERE / "PLAN.md").write_text(CHECKPOINT, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 248565" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS_ENTRY,
                            encoding="utf-8")
    owner = HERE / "OWNERSHIP-239533.md"
    body = owner.read_text(encoding="utf-8")
    if "Claim 248565" not in body:
        owner.write_text(body.rstrip("\n") + "\n" + OWNERSHIP, encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
