"""Claim-251064: the preflight runs in the pinned process, before the effects."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 251064

Review 2026-09-23T21:06:44Z accepted the bootstrap chain, the `lexists` target
refusal and the repeat wording, and left one bounded item. It is done.

## The correction

**My rationale was false and the reviewer traced it three lines.** I wrote that
`tools` only answers in the composer subprocess. `main` called
`two_jobs.composed` → `held` → `from tools import stage_execution` →
`held_configuration` IN PROCESS, so the package I had explicitly tolerated was
the one validating the packet — and under this suite's own imports that was the
checkout's.

**The fix is not a stricter filter**; filtering is what produced the wrong
claim. `two_jobs.py --check` now performs the digest pins, the import
provenance and the entire composition and writes nothing, and the preparation
runs it in a subprocess bound to the pinned source with `cwd` at the root —
the same program, environment and directory as the composition that follows.
So the bytes that validate are the bytes that compose by construction, and the
pins are checked before any Authority act.

What remains in process is the derivation of the manifests and their
`job_input_identity`, so `baton_v12` there must be the pinned one; that is a
refusal by name.

## Also under this claim

  * `--check` mode on the composer: validates, reports what it checked, writes
    nothing.
  * Three cases: `--check` writes nothing and reports `_pins_agree`; a drifted
    digest is refused in the pinned subprocess, driven against a COPY of this
    dossier so no pinned artifact is touched; and a refused preflight leaves
    exactly the two task documents — no selections, no composed target, and
    neither Work in the Authority.
  * A first version of the pin case drove the composer IN PROCESS and never
    reached the pin gate, because the provenance gate fired first. That is the
    same finding arriving from the other side, and the case was rewritten to
    run where the preflight runs.

## Evidence

`verification-24.json` — 83 checks, 0 failures, 72.13213025999721s, pins agree.

## REMAINING

The operator's own steps, then — separately — the run. The container boundary
and the live provider under concurrency stay unproved.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. baton.claude owns the rest of this dossier.
"""

PROGRESS = """
## 2026-09-23 — baton.claude, claim 251064

### I reasoned about where the composer runs and never read three lines

I wrote that `tools` only answers in the composer subprocess, and filtered it
out of the preflight refusal on that basis. The reviewer followed
`two_jobs.composed` → `held` → `from tools import stage_execution` →
`held_configuration` and found it running IN PROCESS, before the Authority
acts. So the package I had explicitly tolerated was the validator, and under
this suite's imports it was the checkout's.

The wrong part was not the filter's threshold; it was that I answered a
question about which bytes validate by reasoning rather than by following the
call. A tighter filter would have been the same mistake with a better guess in
it.

### So the preflight moved to where the composition is

`two_jobs.py --check` runs the digest pins, the import provenance and the whole
composition, and writes nothing. The preparation invokes it through the same
helper that invokes the real write — same program, same `PYTHONPATH` bound to
the pinned source, same `cwd` — so the bytes that validate are the bytes that
compose by construction rather than by argument. The pins are part of that
check, which is the pre-effect digest boundary the reviewer asked for; they
used to be checked only by the composer, after the Authority acts.

What is still in process is the derivation of the two input manifests and their
`job_input_identity`. Those use `baton_v12.contracts`, so that package must be
the pinned one, and it is a refusal by name.

### The same finding, from the other side

My first pin-negative case drove `two_jobs.main` in process with a pinned
digest changed. It never reached the pin gate: the provenance gate fired first,
because under this runner `tools` is the checkout's. That is the reviewer's
finding again, and it is why the case now runs `--check` as a subprocess
against a COPY of this dossier whose pinned digest was altered. No pinned
artifact is touched and the copy is removed.

### What a refused preflight leaves

Exactly the two task documents, because the validator opens them. No resolved
selections, no composed target, and neither Work in the Authority — asserted by
reading the directory and by asking the Authority for both Work ids.

### Verification spending

**`verification-24.json` — 83 checks, 0 failures, 72.13213025999721s**, pins
agree.

Named suite subtotal: 757.331067393s + 72.13213025999721s =
**829.463197653s**.

Also measured this claim and NOT in that subtotal: five suite runs at 71.366s,
71.719s, 72.196s, 71.673s and 72.583s while the new cases were being corrected,
plus two that failed to load from the dossier rather than the distribution; and
two single-case runs under a fifth of a second. Earlier disclosed costs and the
~120s timeout overlap stand unchanged.

State: passed for independent review.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 251064" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
