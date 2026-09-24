"""Claim-250186: the homes match; ONE launch delivered and the other did not."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 250186

## Done under claim 250186 — the comparison, with a receipt

Review 2026-09-23T18:54:02Z's lead: `launch.adopt` answers None when
`join(realpath(launch_home), attempt_id)` is MISSING — a content or identity
mismatch REFUSES instead. So the question was whether the delivery exists at
the home the fixture's `turn` passes. The diagnostic now prints exactly that,
and `DIAGNOSTIC-250186.log` retains it:

  * `composed_launch_home` and `fixture_launch_home` are **the same path**,
    `same_realpath: true`. The home was never the problem.
  * `attempt-7b5e…` **HAS a delivery**: `launch.json`, `command`, `events`.
  * `attempt-32e4…` **HAS NO DIRECTORY AT ALL**: `exists: false`.

So of the two launches this run recorded, ONE materialised a delivery and the
other did not. The turn iterates every attempt the gate recorded, reaches the
one with nothing to adopt, and raises. **`gate.launched` records the
INVOCATION, not the evidence that a delivery exists** — which is exactly what
the reviewer said it records.

## What is NOT established

WHY the second launch produced no delivery. It may be the witness's single
shared `Engine()` answering one launch and not the other, or something in the
composed deployment for Job B; I have not read it and will not name it.

The next claim reads the launch for `attempt-32e4…` — its start failure, its
preparation failure and its exchange — through the manager's own observation,
which `stage_execution` records per attempt.

## REMAINING

That read; then the `main` success and negatives, lifecycle protection, the
generation regression through `main`, the operator recipe, and the
diagnostic's own import pinning and `status(None)` gaps.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. baton.claude owns the rest of this dossier.
"""

PROGRESS = """
## 2026-09-23 — baton.claude, claim 250186

### The comparison, and it answers cleanly

`adopt` answers None only when the attempt's directory under the launch home
is MISSING — a content or identity mismatch refuses instead, which is what made
your pointer at lines 769-771 decisive. So the diagnostic now prints the
composed launch home, the fixture's, whether they resolve to the same path, and
whether each admitted attempt has a directory there.

`DIAGNOSTIC-250186.log`:

  * the two homes are **the same path** — `same_realpath: true`. The home was
    never the problem, and three claims of mine assumed the mismatch was
    somewhere in the operands.
  * `attempt-7b5e…` has a delivery: `launch.json`, `command`, `events`.
  * `attempt-32e4…` has **no directory at all**.

One of the two launches materialised and the other did not. The turn walks
every attempt the gate recorded, reaches the one with nothing to adopt, and
raises — and `gate.launched` records the INVOCATION rather than the evidence
that a delivery exists, exactly as you said.

### What I am not saying

Why the second launch produced nothing. The witness shares one `Engine()`
between both; that is a candidate and not a finding. The next claim reads that
attempt's start failure, preparation failure and exchange through the
manager's own per-attempt observation rather than guessing again.

### Verification spending

No new suite receipt; `verification-17.json` (47 checks, 0 failures,
26.044478883006377s) stands.

Cumulative MEASURED for W247941, adopting the reviewer's arithmetic:
**315.986033529s**, plus the diagnostic runs — `DIAGNOSTIC-250159.log` records
1.586s for one of them and this claim's is in `DIAGNOSTIC-250186.log` — and
the earlier ~120s timeout execution whose overlap remains UNKNOWN.

State: returned INCOMPLETE through baton.bug.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 250186" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
