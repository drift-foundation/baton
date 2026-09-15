# B: convert hours to seconds

Implement this complete request on B's private line from the same frozen
original base as A. Change only `demo/units.py`, add `tests/test_hours.py`,
and add `check_hours.py` at the repository root.

Add `hours_to_seconds(n)` returning `n * 3600`. Cover 0, 1 and 2 hours in the
new unittest module. Preserve `minutes_to_seconds` and the existing tests.

The new `check_hours.py` must be self-contained apart from importing
`demo.units`: import both conversion functions and assert the hours results
0, 3600 and 7200 and minutes results 0 and 120. Print a clear success line
only after every assertion passes. It must not import `tests.test_hours`,
create files, install dependencies, repair missing functions, catch an import
or assertion failure, or depend on a changed test module. The configured
causal observer carries this one script into the original base; the missing
hours function there must produce a real nonzero exit. The same script must
pass on B's isolated candidate and the separately merged result.

Required verification argv: `["python3", "check_hours.py"]`.
Submission `test_scope`: `[]` (only additive test files).

Do not copy A's result into B's original line or change its declared base.
