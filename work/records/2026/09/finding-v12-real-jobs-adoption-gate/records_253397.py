"""Claim-253397: ownership coordinated and the capability specified, not written."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 253397; RETURNED INCOMPLETE

Owner 253388 selected the bounded composition capability and required exclusive
ownership of two product files **before** edits. This claim coordinates that
ownership and pins the design; it does not edit either file.

## Done under claim 253397

[OWNERSHIP-253397.md](OWNERSHIP-253397.md) claims
`v12/python/tools/single_worker.py` and `v12/python/tools/stage_execution.py`
exclusively for W247941, and records the specification the capability is built
against:

  * **the construction to reuse** — `_Worker.ending`'s own adapter recovery,
    `_adopted(stage)` → `attempt_runtime_of` → `_mounted(stage, …)` →
    `_credential(…)` → `_adapter(roots, delivery, orphan, launched)` — with
    the one deliberate difference that abandonment must NOT inherit the
    ending's answered-terminal precondition;
  * **why `cancel_attempt` is the wrong template**: it composes the observing
    adapter, which is right for a stop that reads only a runtime id and wrong
    for a removal that owns deliveries. Claim 172346 measured that cost — a
    member ended with its credential and launch roots still on disk;
  * **three things that must be established before the edit**, and are not:
    how `_adopted` and `_mounted` behave for a FAULTED attempt, whether
    `_credential` can recover a delivery for one, and which `stage` document
    the routing has to supply when `cancel_attempt` routes by allocation
    alone.

`git status` confirms both product files are unedited under this claim.

## Why the pin and not the edit

The adapter is the entire risk, and the ending reaches those three helpers only
after a correlated answered terminal — so their behaviour on the faulted path is
unread. Writing the capability against unread preconditions is precisely the
mistake the 172346 measurement punishes, and it would land in product files two
Works depend on.

## REMAINING

  1. establish the three unread behaviours, then add the `single_worker`
     capability and the `stage_execution` routing that fails closed on unknown
     allocation, absent worker or absent capability;
  2. the supervisor's explicit shutdown declaration, for its own failed or
     stopped attempts only;
  3. the seven deterministic boundaries with a fake adapter: receiptless
     fault, prior cancellation fence, repeat/crash replay, wrong
     allocation/capability, adapter refusal and uncertain absence, positive
     `retained` cleanup including the credential and launch roots, and an
     unaffected successful output;
  4. a new digest-bound manager snapshot, and only then fresh-run commands;
  5. the two operator grants documents with pure and fake-boundary
     validation and readback — independently authorized and not dependent on
     item 1;
  6. the executed-image fault diagnosis — likewise independent.

## Standing constraints

The preserved deployed snapshot is immutable and is not the edit target; the
checkout is. The failed instance stays preserved and read-only. No live rerun,
deployed-store mutation or container deletion.

## Evidence

No suite change this claim — one new document and no code. `verification-27.json`
(85 checks, 0 failures, 72.99730089001241s, pins agree) stands.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. The owner owns the FINDING entries of 2026-09-23 and
2026-09-24. baton.claude owns the rest of this dossier AND, from this claim,
`v12/python/tools/single_worker.py` and `v12/python/tools/stage_execution.py`.
"""

PROGRESS = """
## 2026-09-24 — baton.claude, claim 253397

### Ownership coordinated; the capability specified rather than written

The owner selected the composition capability and required exclusive ownership
of `tools/single_worker.py` and `tools/stage_execution.py` before edits.
OWNERSHIP-253397.md is that artifact, and `git status` confirms neither file has
been touched under this claim.

I did not write the capability, and the reason is specific. The adapter is the
entire risk: abandonment tears down deliveries a start already created, so it
needs the RECOVERED adapter rather than the observing one `cancel_attempt`
composes — and claim 172346 already measured the cost of getting that wrong, a
member ended with its credential root and launch root still on disk.

`_Worker.ending` already recovers exactly the right adapter, and the document
pins that sequence. But the ending reaches `_adopted`, `_mounted` and
`_credential` only after a correlated ANSWERED terminal, and abandonment exists
for the case where there is none. So how those three behave on the faulted path
is unread, and writing a capability against unread preconditions — in product
files two other Works depend on — is the same class of mistake as the one being
corrected.

Three things to establish first, named in the document: whether `_adopted` and
`_mounted` work for a faulted attempt and what they refuse; whether
`_credential` can recover a delivery for one, and what it answers when the
credential root is already gone; and which `stage` document the routing must
supply, since `cancel_attempt` routes by allocation with no stage in hand.

### Verification spending

No suite change: one document, no code. `verification-27.json` — 85 checks,
0 failures, 72.99730089001241s, pins agree — stands.

Named suite subtotal unchanged at **1047.869180986s**. Measured this claim:
sub-second reads of the checkout's `single_worker`, `stage_execution` and
`dogfood_operator`, and one `git status`. Earlier disclosed costs and the ~120s
timeout overlap stand unchanged.

State: returned INCOMPLETE through baton.bug with the remaining scope named.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 253397" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
