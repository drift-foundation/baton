"""Claim-249551: composition validated and bound; R3/R4 still unstarted."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 249551

**R1 is closed and now self-checking. R3's frozen verdicts and R4's supervisor
are STILL unstarted.**

## Done under claim 249551

  * **The composition validates its own submission.** `held_submission` runs
    the public `owned_submission` reader — the same judgment `submit` makes,
    without a store — so an invalid `terminal_policy` is refused AT
    COMPOSITION rather than later, at submission, where an operator meets it.
  * **The composition is bound to the bytes the pins were checked against.**
    `imported_from` refuses a run whose `tools`/`baton_v12` resolved outside
    the pinned snapshot. A pin check about one source and a composition by
    another said nothing.
  * **The fixture-root requirement is explicit and checkable.**
    `held_configuration` derives "the checkout" from the source that imported
    it, so bound to the pinned snapshot under `/home/sl/baton-runs/...` that
    directory IS the checkout and a disposable root beneath it is denied. The
    guard is not weakened: `verify_247941.py --pins` reports `fixture_root`
    findings and names the exact setup, `/var/tmp/baton-w247941`, and the
    packet records it.

26 focused checks, 0 failures, measured 3.646601885993732s,
`verification-4.json`. Two are new: a composition bound to the checkout is
refused, and an invalid terminal policy is refused at composition.

## Still NOT started

  * **R3's rest — two FROZEN attributed verdicts.**
  * **R4 — the bounded four-admission supervisor**, stop, positive cleanup for
    all four attempts, published outcome.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
every `review-*.json`/`.log` beside them. baton.claude owns two_jobs.py,
test_two_jobs.py, ADOPTION-247941.md, CONTINUITY-247941.md,
SELECTIONS-247941.json, verify_247941.py, the `align_template.py`,
`add_roundtrip.py` and `apply_249551*.py` edit records, verification-*.json/.log,
PROGRESS.md, records_*.py and PLAN.md.
"""

PROGRESS = """
## 2026-09-23 — baton.claude, claim 249551

Review 2026-09-23T17:25:40Z found three things in work I had just called
finished, and all three were the same mistake in different places: a check that
was about something other than what actually ran.

### The composer wrote a document its own reader refuses

`composed` accepted any `terminal_policy` and the serialized reader rejected
it afterwards. That moves the failure from composition, where the composer can
say exactly what is wrong, to submission, where an operator meets it. It now
runs `owned_submission` — the same judgment `submit` makes, and it needs no
store — before returning the document.

### The pin check and the composition were about different bytes

`--pins` hashed the snapshot while the subprocess imported the checkout. Both
passed; together they proved nothing. `imported_from` now refuses a
composition whose `tools` and `baton_v12` did not resolve inside the pinned
source, and a case asserts a checkout-bound run is refused by name.

### The fixture root, and a guard I was told not to weaken

Three of my five roundtrip cases refused for the reviewer because
`held_configuration` denies mutable state "inside the checkout" — and the
checkout it detects is derived from THE SOURCE THAT IMPORTED IT. Bound to the
pinned snapshot under `/home/sl/baton-runs/...`, that directory becomes the
checkout, so a disposable root beneath it is denied even though it is nowhere
near the repository.

The guard is correct. What was missing was the setup that satisfies it, so it
is now named, checked and printed: `/var/tmp/baton-w247941`, reported by
`verify_247941.py --pins` as `fixture_root` findings with the exact command.

### Verification spending

26 focused deterministic checks, 0 failures, measured 3.646601885993732s,
receipt `verification-4.json` with `verification-4.log`; 2 are new.

Cumulative MEASURED for W247941, every retained invocation preserved:
1.678180975 + 2.122556141 + 2.145897528 + 2.868183810 + 2.876618006 +
3.646601886 = **15.338038346s**. The pin checks are separate and their elapsed
times were not measured and are not estimated. The reviewer's own 36.584s run
of 62 inherited cases and their corrected 0.775s run of 5 are theirs and are
preserved in their evidence, not folded in here.

State: returned INCOMPLETE through baton.bug. R3's frozen verdicts and R4's
four-admission supervisor remain, with no work started on either.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 249551" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
