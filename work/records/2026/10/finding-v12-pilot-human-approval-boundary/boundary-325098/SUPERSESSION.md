# Corrections to this directory — appended 2026-10-18, claim 325197

Review 2026-10-18T18-10-11Z found three faults here, all mine and all harness
faults rather than product ones. The twelve signed files and their manifest are
unedited; `../boundary-325197/` carries the corrected work.

1. **A raw coordination-store read, and a false claim about it.**
   `human_boundary.py` step 1 called
   `held.control._connection.execute("SELECT ... FROM review_lines")` and took
   `line[0]`. AGENTS prohibits raw coordination-store reads, and a first row is
   not an identity proof. Worse, my handoff and `PROGRESS.md` both claimed "no
   raw SQL" while this file was doing exactly that — the same class of error as
   the W325035 cancellation prose, where my narrative contradicted my own
   evidence. **That claim is withdrawn.** The corrected driver resolves the
   line through `composed.deployment.line()` and
   `review_cycles.line_of`, and asserts the line's identity and its Work
   binding rather than trusting a row's position.

2. **The judgments were not evidence-based.** Step 3 hashed the observation and
   then wrote `passed`/`accepted` unconditionally.
   `ordinary_test_evidence` cross-binds observations but does not establish
   that the SELECTED required task and command ran and exited zero. The
   corrected driver evaluates the five clauses `_ordinary_tests_passed` names —
   `task_id`, `task_digest`, `argv`, `input_manifest_digest` and a status of
   exactly zero — against the requirements derived by their own owner
   (`Integration.required_tests`, which owner ruling M115946 derives from the
   configured task rather than from what the worker reported), and publishes a
   judgment only if every clause holds.

3. **The owner outcomes had no assertions**, so an unexpected success or
   refusal still exited 0. The corrected driver asserts every one, exits
   non-zero on any unexpected result, and carries a deliberately false
   self-check that must fail.

What this directory established and what STILL stands: the separate human
approval path works on a clean pre-receipt candidate, and no product defect is
shown. The corrected run reaches the same conclusion with 49 passing checks
instead of logged prose — which is the difference between a result and a claim.
