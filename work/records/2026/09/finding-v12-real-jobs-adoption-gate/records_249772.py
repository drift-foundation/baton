"""Claim-249772: main could not open a store; now it does, and a case proves it."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 249772

## Done under claim 249772

  * **`main` could not open a store at all.** Both `JobStore.open` and
    `ControlStore.open` require a `clock` and it passed none — so the one
    command this packet tells an operator to type would have failed at its
    first act. It now passes `baseline._moment`, the instant source the
    accepted supervisor uses.
  * **Acquisition is inside the `try`.** It was above it, so a failure opening
    the control store or composing the operations leaked the handles already
    taken. Handles are appended as each one succeeds and closed newest-first.
  * **A case CALLS `main`.** It reaches the real composition over the
    composer's own documents and both stores exist on disk afterwards. The
    production credential provider then refuses, because this fixture's
    deployment carries `credential_sources: null` — that refusal is the
    product working, and the case says so rather than claiming a full run. A
    `TypeError` there would be the clock defect again.

43 focused checks, 0 failures, measured 11.520278754003812s,
`verification-9.json`; 1 is new.

## REMAINING

1. **Success through the generated documents**: four attempts, BOTH frozen
   verdicts, positive cleanup, with success required from RESULTS rather than
   admission counts and a final cleanup read after the last sweep. It needs a
   turn seam on `supervise` the witness fills with the fixture's deterministic
   turn, and a credential registry the production provider accepts.
2. **The `main` no-result, deadline, failure and interruption checks**, which
   depend on 1.
3. **Operator step 7** still shows the old `supervise` snippet with undefined
   variables, and step 4 still serves unbounded; both must be replaced by the
   one tested `main` command.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. baton.claude owns the rest of this dossier.
"""

PROGRESS = """
## 2026-09-23 — baton.claude, claim 249772

### The command could not open a store

Both openers require a `clock` keyword and `main` passed none, so the one
command the packet tells an operator to type would have failed at its first
act. I wrote it without reading the signatures. It now passes
`baseline._moment` — the instant source the accepted supervisor uses, not a
second clock — and a case CALLS `main` rather than describing it.

Acquisition also sat above the `try`, so a failure opening the control store
or composing the operations leaked whatever was already open. Handles are
appended as each succeeds and closed newest-first: a composition closed after
its stores would be closing over handles that are already gone.

### What the new case proves, and what it does not

`main` opens both stores and reaches the real composition; both store files
exist on disk afterwards. The PRODUCTION credential provider then refuses,
because this fixture's deployment carries `credential_sources: null` and that
path requires an absolute private registry. That refusal is the product
working, and the case asserts exactly it — a `TypeError` there would be the
clock defect again.

It is not a completed run, and the case name and docstring say so.

### Verification spending

43 focused deterministic checks, 0 failures, measured 11.520278754003812s,
receipt `verification-9.json` with `verification-9.log`; 1 is new. The receipt
was bumped rather than overwriting `-8`.

Cumulative MEASURED for W247941, every retained invocation preserved:
1.678180975 + 2.122556141 + 2.145897528 + 2.868183810 + 2.876618006 +
3.646601886 + 3.682941216 + 6.941682081 + 10.885859361 + 10.943187142 +
10.857 + 11.135997740 + 11.183168619 + 11.520278754 = **92.488153259s**.

State: returned INCOMPLETE through baton.bug.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 249772" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
