# Deterministic v12 assertion rendering

## Trigger

W10265 was filed from the W9707 parallel-runner parity work after currently
failing v12 tests appeared to reorder collection values between independent
single-process runs. This is an output-determinism defect, not evidence of a
parallel execution defect: reported failing test ids, counts, and verdicts
remain stable.

## Evidence status

**Observed:** Python's `unittest` assertion helpers include `repr()` of their
operands in failure text. A failing `assertIn(member, unordered_set)` or direct
comparison of unequal sets can therefore expose hash-seed-dependent iteration
order when elements contain salted types such as strings or tuples of strings.

**Observed limitation of the filing repro:** the two whole-output MD5 values
also cover `unittest`'s elapsed-time line. They prove that the complete byte
streams differ, but do not by themselves prove which bytes differ. Focused
fixed-`PYTHONHASHSEED` output comparison is required to isolate collection
ordering from ordinary duration variance.

**Reported candidate sites:**

- `v12/python/tests/manager/test_boundary_inventory.py`;
- `v12/python/tests/manager/test_oci.py`;
- `v12/python/tests/manager/test_secrets.py`.

## Independent reproduction — 2026-08-25

**Confirmed:** comparing the parsed failure blocks from two completed W9707
default-worker runs on the same tree finds exactly three differing blocks, all
from two assertion sites in `test_boundary_inventory.py`:

1. line 4069,
   `self.assertEqual(wanted - declared, set())`, renders the nine elements of
   the nonempty set difference in hash order;
2. line 3919, `self.assertIn(entry, entries)`, renders the full `entries` set
   for each of the two stale `base_revision.algorithm` and
   `base_revision.hex` subtests.

All other parsed failure/error blocks are byte-identical between those runs,
including the current `test_oci.py` and `test_secrets.py` blocks. Those two
reported modules are therefore not in the present patch boundary. Their test
ids and semantic failures remain relevant to W9707, but their diagnostics do
not reproduce this defect on the reviewed tree.

**Confirmed fixed-seed witness:** running

```text
env PYTHONPATH=src PYTHONHASHSEED=1 python3 -m unittest tests.manager.test_boundary_inventory.EveryProbeProvesItArrived.test_the_missing_probe_check_can_actually_fail
env PYTHONPATH=src PYTHONHASHSEED=2 python3 -m unittest tests.manager.test_boundary_inventory.EveryProbeProvesItArrived.test_the_missing_probe_check_can_actually_fail
```

produces the same nine missing elements and the same failing test id, but in
different orders. Seed 1 begins with the two persisted-session `work_id` and
`generation` entries; seed 2 begins with the OCI `identity` entry and the
persisted-session `authority_uuid` entry. Both runs fail only that one test.

**Corrected filing repro:** the originally named
`test_every_receiving_entry_has_an_owning_validator` assertion compares a
sorted list at line 3855. Its complete `unittest` byte stream changes because
the `Ran 1 test in ...s` duration changes, not because that assertion renders
an unordered set. It is not a diagnostic-order witness.

## Proposed bounded correction

Subject to the required case-specific approval, change only the two existing
assertion sites above:

- line 3919: assert membership against `sorted(entries)` so `assertIn`
  preserves membership semantics while its failure container has stable
  order;
- line 4069: compare `sorted(wanted - declared)` with `[]`, matching the
  already-stable empty-difference assertions at lines 4046-4047.

No runner normalization, global hash seed, product code, OCI test, or secrets
test belongs in this patch. Focused verification compares parsed assertion
diagnostics rather than whole `unittest` output, whose duration is expected to
vary.

## Confirmed ruling — 2026-08-25

**Approved by Slawomir in T10265 at message 10719:** edit only the two
identified existing assertions in
`v12/python/tests/manager/test_boundary_inventory.py` so their set-derived
diagnostics render through sorted collections:

- `test_no_declared_owner_is_stale`: preserve membership semantics while
  changing the `assertIn` container from `entries` to `sorted(entries)`;
- `test_the_missing_probe_check_can_actually_fail`: preserve the empty-
  difference verdict while changing `assertEqual(wanted - declared, set())` to
  compare `sorted(wanted - declared)` with `[]`.

The approval explicitly excludes OCI assertions, secrets assertions, elapsed-
time output, and any general promise that whole-suite output is byte-identical.
The current tree was revalidated after the ruling: both approved assertions
remain present in the researched form, and no implementation edit has yet been
made.

## Review clarification required — 2026-08-25

**Observed after the approved implementation:** the two assertions now render
deterministically and preserve their verdicts, but
`assertEqual(sorted(wanted - declared), [])` dispatches to unittest's list
comparison and its default `maxDiff` truncates the diagnostic. The current
nine-entry difference renders the first entry followed by `Diff is 1133
characters long. Set self.maxDiff to None to see it.`; the other eight missing
entries are no longer visible in that test's failure block.

This consequence was not part of the approval request and conflicts with the
acceptance boundary below to preserve failure context. It is not silently
folded into the prior ruling. The narrow proposed correction is one additional
test-local line, `self.maxDiff = None`, inside
`test_the_missing_probe_check_can_actually_fail` before the approved sorted-list
comparison. That keeps stable order and restores the complete list, but it is
an additional edit to existing test behavior and therefore requires a new
case-specific ruling. The alternative is an explicit supersession accepting
truncated context for this diagnostic.

## Confirmed follow-up ruling — 2026-08-25

**Approved by Slawomir in T10265 at message 11462:** Option A supersedes the
unresolved alternatives above. Add test-local `self.maxDiff = None`
immediately before the already approved sorted-list comparison in
`test_the_missing_probe_check_can_actually_fail`, and add a focused additive
regression proving complete deterministic rendering.

The correction must preserve the existing verdict and remain confined to
that diagnostic. No other assertion or output normalization is authorized.

## Acceptance boundary

- Inventory every currently failing assertion whose diagnostic renders an
  unordered collection; do not patch only the first observed test.
- Preserve the assertion's membership/equality semantics and failure context.
  Stabilize diagnostic operands at the assertion site rather than setting a
  global `PYTHONHASHSEED`, which would mask other order dependencies and would
  not make ordinary elapsed-time text byte-identical.
- Prove the affected diagnostic fragments are identical under at least two
  distinct fixed hash seeds while the test ids, counts, and verdicts remain
  unchanged.
- Keep output normalization out of the parallel runner: serial and parallel
  execution must expose the same underlying test diagnostics.
- Editing existing test assertions or expected behavior requires Slawomir's
  explicit, case-specific confirmation under repository policy. That
  confirmation is recorded above: message 10719 covers the exact two sorted-
  collection assertion edits, and message 11462 additionally covers only the
  test-local `maxDiff` correction and its additive focused regression.

## Independent final review — 2026-08-26

**Confirmed:** The follow-up correction stays inside both rulings. The two
approved assertion operands remain sorted, the one `self.maxDiff = None`
assignment is test-local and precedes only the approved missing-probe
comparison, and no OCI, secrets, runner-output or global hash-seed
normalization was introduced.

**Confirmed:** The additive regression proves the ruled form over a synthetic
failure that remains available after the live inventory gaps close. Six hash
seeds produce one elapsed-line-normalized diagnostic; all eighteen operands
render in sorted order without a truncation notice; the old set form still
varies; and both forms retain the same failing verdict. The regression module
and exhaustive parallel-runner registry are green.

**Confirmed:** Independent live runs under seeds 1 and 2 retain
`FAILED (failures=3)`, show the complete current eight-entry missing-probe
difference in sorted order, and contain no `maxDiff` truncation notice. No
review finding remains. Final review:
`review-2026-08-26T01-11-56Z.md`.
