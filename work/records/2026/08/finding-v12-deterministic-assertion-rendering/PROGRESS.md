# Progress: deterministic v12 assertion rendering

Implementer: `baton.claude`. Work `W10265`, claimed 2026-08-25.

## First, corrections to my own filing

I filed W10265 from the W9707 parity work, and the reviewer's research
corrected it in three ways. Recording them here because the finding record
should not preserve my errors as though they were evidence:

1. **My repro was weaker than I claimed.** The two whole-output MD5 values also
   cover `unittest`'s elapsed-time line, so they proved the byte streams
   differed without proving WHICH bytes did. A fixed-seed comparison of parsed
   diagnostics was the right instrument and I did not use it.
2. **The test I named was not a witness.** I cited
   `test_every_receiving_entry_has_an_owning_validator`, whose assertion at
   line 3855 already compares a SORTED list. Its output varies only because the
   duration varies. Independently re-confirmed here: stable across seeds.
3. **`test_oci.py` and `test_secrets.py` do not reproduce this.** I asserted
   they showed "the same reordering". They do not, on this tree. Independently
   re-confirmed here: every OCI and secrets failure block is byte-identical
   across seeds.

The underlying defect was real and the two sites the reviewer isolated are
genuine. The supporting evidence I attached to it was partly wrong.

## Revalidation before implementing

Both approved sites were re-read against the current tree and are present in
the researched form: `test_no_declared_owner_is_stale` asserting membership
against the `entries` set, and `test_the_missing_probe_check_can_actually_fail`
comparing `wanted - declared` against `set()`.

## Inventory (acceptance boundary: every currently failing assertion)

All 14 currently failing tests — the 11 parallel-source failures, 2 errors and
the 3 serial-registry failures — were run under `PYTHONHASHSEED=1` and `=2`
with the elapsed-time line filtered out, and their diagnostics compared:

    SEED-DEPENDENT : test_boundary_inventory … test_no_declared_owner_is_stale
    SEED-DEPENDENT : test_boundary_inventory … test_the_missing_probe_check_can_actually_fail
    SEED-DEPENDENT : test_worker_container   … test_two_independent_builds_have_one_pinnable_image_identity
    stable         : the other eleven, including every OCI and secrets block

The first two are exactly the approved sites. **The third is not this defect**
and was classified rather than patched: its difference is two Docker image
digests, which differ between any two builds regardless of hash seed. That is
W6633's image-reproducibility failure.

**A measurement error of mine, corrected rather than buried.** My first pass at
this comparison reported the missing-probe site as *stable* and I nearly
reported the reviewer's fixed-seed witness as unreproducible. The comparison
had raced the probe: the shell creates each output file at process start and
fills it at the end, so "28/28 files exist" was not "28/28 complete", and I had
diffed partial files. Re-run after completion, the result matches the pinned
research exactly.

**Latent sites, reported not patched.** Three other assertions use the same
`assertEqual(..., set())` idiom — one in `tests/authority/test_boundary.py`,
two in `tests/authority/test_session.py` — and one more `assertIn(entry,
entries)` at `test_boundary_inventory.py` line 4039. All of those tests PASS
today, so nothing renders and the defect is latent rather than active. They are
outside the approved boundary and outside the acceptance boundary's wording
("every currently FAILING assertion"). Flagging them so the decision to leave
them is visible.

## What changed

Exactly the two ruled assertions in
`v12/python/tests/manager/test_boundary_inventory.py`, each with a comment
saying why:

- `test_no_declared_owner_is_stale`: `assertIn(entry, entries)` ->
  `assertIn(entry, sorted(entries))`. Membership in a sorted list is the same
  question as membership in the set it came from.
- `test_the_missing_probe_check_can_actually_fail`:
  `assertEqual(wanted - declared, set())` ->
  `assertEqual(sorted(wanted - declared), [])`, matching the already-stable
  sibling two tests above.

Added `v12/python/tests/manager/test_diagnostic_rendering.py` (3 cases) and
registered it in the runner's parallel registry in the same edit, so registry
completeness never had a transitional exception. It pins the SHAPE of the two
ruled assertions via `ast`, deliberately not their output: the real property
needs two interpreters, and the diagnostics it would compare only exist while
those tests are failing — so an output-based regression would evaporate exactly
when the underlying gaps get closed. It checks only the two ruled functions,
so it cannot go red on the unapproved latent sites.

## Verification

- **Stable across three seeds.** Both fixed tests, run together under
  `PYTHONHASHSEED` 1, 2 and 3, produce byte-identical output once the
  elapsed-time line is filtered: md5 `079b873ca108f83d212a11cfd214b66c` for all
  three. Verdict unchanged in each: `FAILED (failures=3)` — the two stale-owner
  subtests plus the probe check.
- **Verdicts and ids unchanged suite-wide.** Full parallel phase 115.16s at
  464%: 204 shards, 1128 tests, 11 failures + 2 errors + 1 skip, and the
  failing-id set is byte-identical to the pre-change run.
- **Coverage parity.** Runner + serial registry = 1172 ids; `unittest
  discover` = 1172; diff empty. The count moved from 1168 by exactly +3 (this
  Work's regressions) and +1 (the runner test the tuner added during W9707's
  polish).
- The new regression module and the runner's own 36 cases both pass.
- `git diff --check` clean.

## Known consequence of the ruled form, reported not fixed

`assertEqual(sorted(...), [])` renders through `assertListEqual`, which
TRUNCATES: the nonempty difference now shows one element plus `Diff is 1133
characters long. Set self.maxDiff to None to see it.`, where the old set
comparison listed all nine entries one per line. Determinism was bought at some
loss of visible context.

I am NOT treating this as a blocker, because it is the existing house form
rather than something this change introduced: the already-stable sibling at
line 4046 produces byte-identical truncated output and did so before this Work.
The ruling explicitly asked this site to match that sibling.

If the full listing is wanted, `self.maxDiff = None` restores it for both sites
and keeps them deterministic. That is a third edit to an existing test and is
outside the approval, so it is proposed here rather than applied.

I also record that my own first check of this — "all 9 entries still present"
— was a FALSE POSITIVE: it searched the whole output file, and those entries
also appear in the other failing test's diagnostic. Scoped to this test's own
block the count is zero.

## Review state

**Awaiting review.** Passing to `baton.feat` (rview). Not closed by the
implementer. The approval covered exactly two assertion sites and exactly two
were changed.

## The approved `maxDiff` correction — 2026-08-25

Second claim, answering review R1 under the follow-up ruling in T10265 message
11462. Exactly what was approved and nothing beside it.

**Revalidated first.** Both approved sites are present in the ruled form and
no `maxDiff` assignment existed anywhere in the module. The tree has moved
since the previous correction: the difference this site renders is now EIGHT
entries rather than the nine the review measured, because W6632's correction
added a probe. That changes a count in the diagnostic and nothing about the
defect.

**One line.** `self.maxDiff = None` immediately before
`assertEqual(sorted(wanted - declared), [])`, with a comment saying why it is
test-local: a module or class default would change every other diagnostic in
that file, none of which was reviewed for it, and that is the output
normalization the same ruling excludes. A case pins that no other function in
the module sets it.

**R1 is closed.** All eight entries render — one as `First extra element 0`
and seven in the diff — and `Set self.maxDiff to None` appears zero times.
Both ruled sites under seeds 1, 2 and 3 are byte-identical once the elapsed
line is filtered, md5 `73d119727e9992cb3f7358e3cafc6398`, with the verdict
unchanged at `FAILED (failures=3)`.

## The regression, and an argument I had to answer honestly

The existing module pins the SHAPE of the two ruled sites through `ast`, and
its docstring argues that an output comparison would evaporate when those
tests stop failing. **That argument is right about those sites and it does not
excuse never proving the property** — which is what the ruling asked for.

So the new cases prove it over a failing assertion this module OWNS: a
synthetic file carrying the ruled form character for character, over eighteen
tuples of strings shaped like the real operands, run in a subprocess under six
hash seeds. Determinism, completeness, sorted order and the unchanged verdict
are each their own case, and none of them depends on the boundary inventory
still being red.

**And a control**, because a determinism check whose subject cannot vary
passes for the wrong reason. The same harness is pointed at
`assertEqual(MISSING, set())` — the idiom this Work removed — and required to
produce more than one rendering across those seeds. If a future interpreter
renders set differences stably, that case fails and says so.

**The completeness check can actually fail — measured.** With the `maxDiff`
line removed from the synthetic form and nothing else changed, it reports the
truncation notice and fails. The file was restored byte for byte.

## One defect of mine in the harness

The first version made a fresh temporary directory per run. A traceback names
the file it came from, so six runs disagreed on a path and the determinism
case failed for a reason with nothing to do with hashing. **A harness has to
hold everything but the variable still or it measures itself** — which is the
same mistake as my original filing, whose whole-output md5 also covered the
elapsed-time line. One directory per case now, with the reason at the site.

## Verification

`evidence/gate-after-maxdiff-correction-2026-08-25.txt`.

- Both ruled sites, seeds 1/2/3: identical, verdict unchanged, no truncation.
- `test_diagnostic_rendering` **10** (was 3); `test_parallel_runner` **36**,
  the module still registered.
- Full source suite **1219, twelve failures**; locked installed-layout build
  **1219, the same twelve**.
- **The failing-id set is unchanged** against the run immediately before this
  change, except for two additions and no removals — both regressions W6633's
  reviewer added to `tests/tools/test_worker_image_build.py` mid-correction.
  That set staying still is the property this Work exists to protect.

## Reported and not fixed

Four of the twelve belong to Work this claim does not hold; all four are
reviewer regressions posted after this participant passed that Work back.

- **W6633**, `tests.tools.test_worker_image_build`:
  `test_a_partial_base_layer_match_refuses` and
  `test_concurrent_builds_for_one_destination_have_distinct_stages`, posted
  with `review-2026-08-26T00-41-16Z.md`.
- **W6632**, `tests.manager.test_oci`: the traversal and stale-policy cases
  from `review-2026-08-26T00-03-30Z.md`.
- **W6630**, `tests.manager.test_secrets`: the substitute-substring case.

The remaining seven are the boundary inventory's long-standing seven, two of
which are the sites this Work renders deterministically. Making them PASS is
other Work's; making them render the same twice is this one's.

## Still latent, still unpatched

The four sites the first correction reported — one `assertEqual(…, set())` in
`tests/authority/test_boundary.py`, two in `tests/authority/test_session.py`,
and one `assertIn(entry, entries)` at `test_boundary_inventory.py` line 4039.
Those tests pass, so nothing renders, and they are outside both the approval
and the acceptance boundary's wording. The synthetic control is now standing
evidence that the idiom itself is the defect, if a later ruling wants them.

## State

**Awaiting independent review.** The claim is not released and no Git
operation was performed.
