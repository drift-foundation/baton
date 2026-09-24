"""Claim-250376: the continuation input, read rather than assumed."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 250376

Owner reroute 250274 routed the remaining resume proof to implementation with
prerequisites W239528 and W239533 closed satisfying, and asked for the real
continuation input and any additional selection it needs. This claim read it
rather than assuming it.

## What the retained subject actually leaves

[CONTINUATION-250376.md](CONTINUATION-250376.md) is the finding;
`RESUME-STATE-250376.json` is the read-only receipt and `test_resume_state.py`
asserts it in 10 checks.

  * **The context to resume EXISTS and is ready.** The producer attempt's
    provider context is finalized at generation 0 with status `ready` — the
    exact predecessor a generation-1 restore requires. It survived the
    runtime's destruction and the `retained` cleanup.
  * **The verdict that would open a correction DOES NOT EXIST.** The line is
    `accepted`, its accepted verdict is its integration eligibility, no
    correction operation exists for the frozen checkpoint, and
    `correction_feedback_of` refuses by name.
  * **The subject cannot be reopened.** `attach_review` admits `review-ready`
    only; `changes-requested` is the sole disposition producing
    `correction-ready`; and the restore reader holds both the verdict and the
    retained report to `changes-requested`.
  * **The acceptance was honest.** The executed review criteria say every one
    of the three verdicts is valid and that none is better for the reviewer.

## The pinned product seam is retired

PLAN pinned an `v12/worker/claude_agent.py` change as unavoidable for
stage-specific requirements. The owner's split retires it: W239533's review Job
carried its own task document with review criteria the implementation Job never
saw. It was the COMBINED-Job shape that needed a seam. Asserted against the
executed criteria. No product byte was changed and none is proposed.

## THE SELECTION THIS JOB NEEDS — for the owner

A new subject whose review honestly asks for a correction, because no packet
can guarantee its own precondition. Recommended: a new implementation + review
pair under neutral criteria, with a packet that treats `accepted` as a valid
end state and records that no correction was required rather than manufacturing
one. It also needs a fresh run identity — the old grant is consumed — and a
bounded one-restore correction Job. The three options and their costs are in
CONTINUATION-250376.md.

## REMAINING

The owner's selection. After it: compose the bounded correction packet, and the
live question this Job exists to ask — whether the production CLI restores a
real conversation, which is the one seam the deterministic evidence stands in
for.

## Ownership

Reviewer-owned and immutable: every `review-*.md`, `review-*.json`/`.log` and
`review-checks-*`. baton.claude owns the rest of this dossier.
"""

PROGRESS = """
## 2026-09-23 — baton.claude, claim 250376

### I read the subject instead of assuming what it held

The owner asked for the real continuation input. `resume_state.py` opens
W239528's retained control and Job stores READ-ONLY, through the pinned
snapshot `/home/sl/baton-runs/independent-review-247947/manager-source`, and
prints every answering module's `__file__` and digest — `not_from_snapshot` is
empty. Nothing was written, started or reached.

Two halves, and they came out opposite ways.

**The context to resume is there.** `context_use_of` reports the producer
attempt's provider context finalized at generation 0, status `ready`, reason
`None` — the exact predecessor a generation-1 restore requires. That status is
not cosmetic: the same reader answers `held`/`generation-damaged` when the
retained generation stops validating. The container was destroyed and cleanup
recorded `retained`, and the context survived both. I had expected this to be
the fragile half and it is the sound one.

**The verdict that would open a correction is not there and cannot be made to
be.** The line is `accepted`; `integration_checkpoint` names its verdict and
`verdict_of` proves the row against its committed act — `accepted`. No
correction operation exists for the frozen checkpoint, asked by derived
identity rather than by scanning. And `correction_feedback_of` refuses in the
product's own words: `serving feedback belongs to a restore invocation`.

Three gates close it: `record_verdict` produces `correction-ready` from
`changes-requested` alone; `attach_review` admits `review-ready` only, so no
second review can attach; and the restore reader holds BOTH the verdict's
disposition and the retained report's own `verdict` member to
`changes-requested`, from frozen custody.

### The acceptance was a judgement

Worth checking before recommending a new subject, because if the criteria had
steered the reviewer the answer would be to fix the packet. They did not: the
executed criteria say every one of the three verdicts is valid and that no
outcome is better for the reviewer than another. The reviewer read a change
that met its stated requirement and said so.

### A seam I had pinned as unavoidable is not

PLAN pinned a `claude_agent.py` change for stage-specific requirements,
reasoned from one Job carrying one digest-sealed input manifest so both roles
read the same task string. That reasoning was correct for the COMBINED Job and
the owner's split retires it — W239533's review Job carried its own task
document with review criteria the implementation Job never saw, and it is
retained and readable. So the constraint I recorded as a product gap was a
property of the shape the owner had already replaced. Asserted against the
executed criteria rather than argued.

### What I am NOT claiming

That the production CLI restores a real conversation. The deterministic
evidence drives open → restore through the real manager, review cycles,
verdicts and provider-context readers with the provider subprocess as its one
seam. That seam is the live question this Job exists to ask.

### Verification spending

`verification-22.json` — the existing suite, 90 tests, status 0,
25.897337019006955s, on the environment its own earlier receipts name so it is
comparable with verification-18 and -20.
`verification-23.json` — this claim's checks, 10 tests, status 0,
0.274530970986234s, bound to the pinned snapshot.

Author cumulative for W236087: 415.934725242s + 25.897337019006955s +
0.274530970986234s = **442.106592232s**. One earlier read-only probe run of
`resume_state.py` is not measured separately.

State: passed for independent review.
"""

FINDING = """
## 2026-09-23 -- claim 250376, the continuation input, read rather than assumed

Owner reroute 250274 routed the remaining resume proof to implementation and
asked for the real continuation input. Reading W239528's retained stores
read-only, through the pinned manager snapshot, answers it in two opposite
halves.

**The context to resume exists and is sound.** The producer attempt's provider
context is finalized at generation 0 with status `ready` -- the exact
predecessor a generation-1 restore requires -- and it survived the runtime's
destruction and the `retained` cleanup.

**The verdict that would open a correction does not exist, and this subject
cannot produce one.** The line is `accepted` and that acceptance is its
integration eligibility; no owner-committed correction exists for the frozen
checkpoint; `correction_feedback_of` refuses because the only context use is an
`open` invocation. `attach_review` admits `review-ready` alone, so no second
review can attach; `changes-requested` is the only disposition that yields
`correction-ready`; and the restore reader holds both the verdict and the
retained report to `changes-requested` from frozen custody. The acceptance was
a judgement rather than an artefact of the criteria, which say in terms that
all three verdicts are valid and none is better for the reviewer.

So this Job needs a NEW SUBJECT, not a repair, and the selection is the
owner's. [CONTINUATION-250376.md](CONTINUATION-250376.md) sets out three
options and recommends one: a new implementation and review pair under neutral
criteria, with a packet that treats `accepted` as a valid end state rather than
manufacturing a correction. It also needs a fresh run identity, since the old
qualification grant is consumed.

**The product seam this dossier pinned as unavoidable is retired.** Separate
Jobs already carry their own task documents -- W239533's review Job did -- so
stage-specific requirements need no change to `claude_agent.py`. It was the
combined-Job shape that needed one. No product byte was changed under this
claim and none is proposed.

What remains unproved is what it has always been: that the production CLI
restores a real conversation. The provider subprocess is the one seam the
deterministic evidence stands in for.
"""


def main():
    # PLAN AND FINDING ARE NEWEST-FIRST HERE, and the history below them is
    # every earlier claim's account. Overwriting either would delete evidence
    # the reviewer's preservation handoff explicitly kept, so the new entry is
    # PREPENDED and nothing already written is touched.
    plan = HERE / "PLAN.md"
    body = plan.read_text(encoding="utf-8")
    if "claim 250376" not in body:
        plan.write_text(PLAN + "\n---\n\n" + body, encoding="utf-8")

    finding = HERE / "FINDING.md"
    body = finding.read_text(encoding="utf-8")
    if "claim 250376" not in body:
        title, _, rest = body.partition("\n")
        if not title.startswith("# "):
            raise SystemExit("REFUSED: FINDING.md does not open with a title")
        finding.write_text(title + "\n" + FINDING + rest, encoding="utf-8")

    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 250376" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
