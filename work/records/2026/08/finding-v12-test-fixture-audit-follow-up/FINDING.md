# Finding: audit v12 test-owned fixture residue

Canonical Baton Work: W2907.

This is the explicit follow-up to the cancelled fixture cleanup Work W30. The
original record remains at
`work/records/2026/08/finding-v12-test-fixture-leaks/`.

## Observed — 2026-08-21

The partial W30 audit found repeated `v12poc-test-*` and
`v12poc-placement-*` scratch roots and left the exact audit directory
`/tmp/w30-fixture-audit.Lmr3aa` after its cleanup request was correctly denied.
W30 closed cancelled without accepting a repository correction and explicitly
requires fresh Work before the audit continues.

## Confirmed scope — 2026-08-21

`baton.tuner` owns a bounded, read-only fixture-ownership audit:

- inventory fixture roots created by the v12 tests and distinguish them from
  ambient or merely name-matching paths;
- identify the creating tests and the missing lifetime/cleanup boundaries;
- record whether the exact W30 audit directory is wholly test-owned and safe
  for a separately authorized cleanup;
- recommend the smallest failure-safe regression and implementation boundary.

The Tuner does not delete the residual tree and does not modify Baton
application or test code under this assignment. If code changes are required,
it passes the implementation-ready result to `baton.impl`.

## Acceptance boundary

- The audit identifies every relevant fixture family and its ownership proof.
- The report separates repository correction from one-time host cleanup.
- No ambient, fixed, or name-matching-only path is proposed for deletion.
- A code correction, if needed, has a focused positive/failure-path regression
  and a complete v12 verification recommendation ready for implementation.

## Audit result — 2026-08-21

### Confirmed fixture inventory

Only `v12/test/unit.test.mjs` and `v12/test/placement.test.mjs` call
`mkdtempSync` under `v12/test/`.

- `unit.test.mjs` defines `scratch()` with the `v12poc-test-*` prefix and has
  51 static call sites. It imports no cleanup primitive and registers no
  suite cleanup, so every dynamically created root survives both success and
  assertion failure. One isolated W30 invocation created 162 such roots
  because several call sites execute more than once.
- `placement.test.mjs` defines `scratch()` with the
  `v12poc-placement-*` prefix and has three call sites. Those roots have no
  cleanup path.
- The placement ownership cases directly create `v12poc-owned-*`,
  `v12poc-stranger-*`, `v12poc-impostor-*`,
  `v12poc-absent-parent-*`, and `v12poc-cli-stranger-*`. Their successful
  paths remove the roots only at the tail of each test, so an earlier failed
  assertion leaks them. The W30 failure left one absent-parent root and one
  CLI-stranger root, which confirms that failure-path gap.
- `v12poc-entry-unowned-*` is also test-owned, but its case already removes
  the exact root in `finally`. It is the existing correct lifetime boundary
  and did not survive the W30 run.

The fixed paths named in assertions, including `/tmp/baton-v12-poc`,
`/tmp/disposable`, `/tmp/elsewhere`, and
`/tmp/somewhere-else/attempts`, are not fixtures created by these tests.
Likewise, a host path matching a fixture prefix is not ownership evidence.
At audit time `/tmp` held 603 top-level `v12poc-test-*` directories and 51
top-level `v12poc-placement-*` directories dated between 2026-08-21 07:27
and 23:21 local time; this audit does not classify or authorize deletion of
any of them individually.

### Confirmed W30 audit-root ownership

The exact root `/tmp/w30-fixture-audit.Lmr3aa` is mode 0700, owned by
`sl:sl`, was created at 2026-08-21 09:33:35 local time, and was last modified
ten seconds later. W30's canonical message records that it created this
confined `TMPDIR` for the reproduction and that the denied run placed only
test-owned data beneath it. Its 168 direct children are:

- 162 `v12poc-test-*` roots;
- three `v12poc-placement-*` roots;
- one `v12poc-absent-parent-*` root;
- one `v12poc-cli-stranger-*` root; and
- one Node compile-cache directory created by that invocation.

The tree is 1.1 MiB and contains test-constructed symbolic links to other
fixture roots and to external targets including this checkout,
`/etc/passwd`, and a production-shaped Baton home. Those targets are not
owned by W30. The links themselves are entries in W30's owned tree.

Therefore the exact literal audit root is wholly W30-owned and is safe for a
separately authorized cleanup that removes the root without following
symbolic links. No parent directory, glob, prefix scan, resolved link target,
or other name-matching path is included in that conclusion. This Work did
not delete it.

### Proposed repository correction

The smallest safe implementation is a test-only owned-root registry shared
by the two test modules (or duplicated locally if that keeps the change
smaller):

1. Register every path returned directly by `mkdtempSync`, including all
   eight fixture families above, at creation time.
2. Register a `node:test` `after` hook in each module that recursively removes
   only those exact recorded roots with link-nonfollowing filesystem
   semantics. Keep existing in-test removals and the
   `v12poc-entry-unowned-*` `finally`; final cleanup is deliberately
   idempotent.
3. Never discover cleanup targets by prefix, directory scan, fixed path, or
   assertion input. Tests that deliberately remove a root or retain it long
   enough to assert refusal keep those semantics because suite cleanup runs
   only after the module's tests finish.

The focused regression should spawn a deliberately failing `node:test`
fixture beneath an exact parent owned by the regression, verify the child
process fails for its intended assertion, and then verify its registered
roots are absent while an external symlink target remains unchanged. A
positive case should make the same absence/target-preservation assertions
after success. The child fixture must live outside the normal `*.test.mjs`
glob so it cannot fail the main suite directly.

Complete verification is `just test` from `v12/` (equivalently
`just -f v12/justfile test` from the repository root), bracketed by an exact
before/after inventory of roots created by that invocation. The gate must be
green and add zero surviving roots from every test-owned family on both the
success probe and the deliberate-failure regression. Docker is not required
for this correction's unit gate.

### Operational finding

The canonical W2907 dossier was created without `PROGRESS.md`. Repository
policy assigns that file exclusively to `baton.claude`, so the Tuner did not
invent or edit implementer progress; implementation starts from this finding
and plan after the handoff.

## Implementation revalidation — 2026-08-22 (baton.claude, W2907)

Every claim in the audit was re-checked against the current tree before
acting. Two are corrected below; the rest hold exactly as written, and the
correction the audit specified is what was implemented.

**Confirmed unchanged.** `unit.test.mjs` still has 51 `scratch()` call sites
with no cleanup primitive and no suite hook. `placement.test.mjs` still has
three `scratch()` sites plus five directly created families whose removals sit
on the successful tail of each case. `v12poc-entry-unowned-*` still removes its
exact root in `finally`. The fixed paths named in assertions are still not
fixtures. The exact tree `/tmp/w30-fixture-audit.Lmr3aa` is still present, mode
0700, `sl:sl`, with its 168 direct children; this Work did not touch it.

**Superseded 2026-08-22 — the family count is nine, not eight.** The audit's
"Only `v12/test/unit.test.mjs` and `v12/test/placement.test.mjs` call
`mkdtempSync` under `v12/test/`" was true on 2026-08-21 and is no longer.
W2928 landed the disposable v12 assignment authority on 2026-08-22 and added
`v12/test/authority_fixture.mjs`, whose `scratch()` creates a ninth family,
`v12-authority-*`. That module already registered its roots and removed them
in a `node:test` `after` hook — the shape this finding recommends — but it kept
a SECOND private registry. The correction folds it into the one shared
registry, so this suite has a single answer to "which paths may it remove". The
audit's inventory and its conclusions are otherwise unaffected: the ninth
family is test-owned, created by `mkdtemp` under the temporary directory, and
governed by the same boundary. The measured pre-correction residue below
counts it.

**Confirmed by measurement, not assumed.** The audit inferred the leak from
call-site inspection. Running the complete gate with the registry's removal
neutered, under an owned `TMPDIR` bracket, leaves 130 test-owned roots — 66
`v12-authority-`, 58 `v12poc-test-`, 5 `v12poc-placement-`, 1
`v12poc-impostor-`. With the correction the same bracket leaves zero. The five
families carrying in-test removals do not appear in that measurement because
every test passed; their gap is a FAILURE-path gap, which is why the
regression spawns a run that fails.

### Pinned implementation decisions

- **The registry hands out roots; it cannot be told about one.** `ownedTemp`
  creates and records in the same call, and there is no exported way to
  register an arbitrary path. That is what makes "this suite created it" a
  fact rather than an inference from the name — the same distinction
  `placement.mjs` spends four cases enforcing. A prefix must be one path
  component, and the created root is re-checked to be a direct child of the
  temporary directory.
- **`mkdtempSync` is no longer imported by either test module.** Leaving the
  unregistered primitive in scope would keep the leak one convenient call
  away; the registry is only a boundary if it is the reachable thing. The one
  deliberate exception is inside the regression that TESTS the registry, which
  needs an unregistered target to link at and disposes of it in `finally`.
- **Removal is by exact path and link-nonfollowing**, which `fs.rmSync`'s
  recursive semantics give. The regression proves it rather than trusting it:
  an owned root carrying links to an external directory, an external file and
  a dangling path is removed while the target keeps its bytes and its subtree.
- **The failing probe lives at `v12/test/fixtures/fixture_cleanup_probe.mjs`**,
  outside the `test/*.test.mjs` glob, and is spawned with `NODE_TEST_CONTEXT`
  deleted from its environment. Without that deletion `node --test` refuses to
  run files "recursively", reports success, and executes nothing — the
  regression would have passed while proving nothing. Its intended failure is
  asserted by marker, and the parent checks the child ran all three of its
  tests with exactly one failure, so a probe that died early cannot be mistaken
  for the case under test.
- **Suite cleanup is additive.** Every existing in-test removal and the
  `entry-unowned` `finally` are untouched; removal is idempotent and forgets
  what it removed, so a second pass is a no-op rather than a second attempt on
  a name something else may since have taken.

### Host cleanup is still not authorized here, and was not performed

The residual `/tmp/w30-fixture-audit.Lmr3aa` tree and the ambient
`v12poc-test-*` / `v12poc-placement-*` roots in `/tmp` are untouched, exactly
as the audit left them. The only directories this verification removed are the
two bracket roots it created itself, by exact path.

## Correction after independent review — 2026-08-22 (baton.claude)

`review-2026-08-22T06-23-08Z.md` requested changes with two P1s. Both were
right. Evidence: `evidence/correction-2026-08-22.txt`.

### [P1] Ownership is an identity, not a pathname

The registry recorded path strings, and six placement families are removed by
their own test tails before the suite hook runs. Once a test deletes a root
the suite owns nothing at that pathname — yet the hook stayed armed on it. The
reviewer created a root, deleted it the way those tails do, recreated the same
pathname with a replacement marker, and the hook deleted the replacement.

**That is the exact path-identity ABA this finding's own boundary forbids.**
"A host path matching a fixture prefix is not ownership evidence" was written
into the audit, and the registry then claimed ownership of a name.

Three corrections, in order of what actually protects:

1. **Removal and forgetting are ONE action.** `removeOwnedRoot(path)` is what
   a test tail calls instead of `rmSync`, so the registry never holds a
   pathname it no longer owns. All six placement tails now use it, and
   `rmSync` is no longer imported by that module.
2. **A root the PRODUCT path removed is retired**, not removed:
   `retireOwnedRoot(path, { observedAbsent: true })` forgets it and refuses
   unless the absence is positively observed — retiring a root that is still
   there would strand it.
3. **`dev`/`ino` are recorded at creation and re-checked immediately before
   removal.** A pathname that now resolves to a different directory is refused
   rather than removed, and the ownership record is KEPT rather than silently
   discarded. This narrows the window rather than closing it — nothing between
   `lstat` and `rm` is atomic — so it is stated as a second line, not the
   first.

An entry is also dropped only AFTER its removal succeeds, so a removal error
cannot discard the ownership record.

### [P1] The probe's report must not travel on a channel the runner owns

The regression scraped `W2907-ROOTS` from the child test runner's stdout.
Under the default test isolation on a supported Node the probe file's own
stdout is hidden behind the file-level result, so both cases failed with "the
probe reported no roots" — and the claimed gate was not reproducible from the
documented `npm test`. A DENIED spawn looked identical, because nothing
diagnosed spawn error, signal or empty output.

- The probe now writes its report to a file the PARENT nominates,
  synchronously. Proven independent of `--test-isolation=process|none` and of
  a reporter that prints no test output at all.
- The parent diagnoses spawn error, signal, a missing report, a malformed
  report and an incomplete one as SEPARATE named outcomes, each carrying exit
  status, signal, stdout and stderr.
- "It failed for the intended reason" no longer depends on output: the probe
  records `reachedIntendedFailure` immediately BEFORE the assertion, so
  "reached it and died there" is distinguishable from "died elsewhere".

**Recorded because it is the same mistake twice.** W2928's real-process race
harness had this exact defect — a child reporting through a pipe the parent
then failed to diagnose — and I corrected it there earlier the same day. I did
not carry the lesson across to this Work's probe. Both now report through a
parent-nominated file.

## Re-review round 2 — 2026-08-22T14:35:33Z

`review-2026-08-22T14-35-33Z.md` requested one remaining correction. It was
right, and it is the round-1 defect's own shadow. Evidence:
`evidence/correction-round3-2026-08-22.txt`.

### [P1] Absence is not the same question as "not a directory"

The round-1 fix recorded a directory identity and re-checked it before
removal, but the function that answered that question returned a single
`null` for three incompatible states: an absent path, an existing
non-directory entry, and an `lstat` that failed. `removeExactly()` read every
`null` as idempotent absence, so a symbolic link or a regular file left at a
registered root's pathname made `removeOwnedRoot()` report success, DROP the
ownership record, and leave the replacement entry standing.
`retireOwnedRoot()` made the same conflation.

**Superseding the round-1 text above:** correction 3 of the previous section
("`dev`/`ino` are recorded at creation and re-checked immediately before
removal") stated the boundary correctly but did not hold for a takeover by
anything other than a directory. The boundary is unchanged; its
implementation is replaced.

`inspect(path)` now returns four distinct states, and only the first is
treated as already-done:

| state | meaning | what removal does |
| --- | --- | --- |
| `absent` | `ENOENT`, and nothing else | returns quietly — this is what makes cleanup idempotent |
| `directory` + matching identity | the exact directory this suite created | removes it, link-nonfollowing |
| `directory` + different identity | somebody else's directory at our name | refuses, keeps the record, reports |
| `other` | a symlink, file, FIFO, socket or device | refuses, keeps the record, reports |
| `error` | `lstat` failed for any non-`ENOENT` reason | fails closed: refuses, keeps the record, reports |

A root also enters the registry only with a REAL directory identity;
recording `null` would have put an entry in the map that removal had no way
to check.

**Why the same class of defect twice.** Round 1 established that a matching
PATHNAME is not ownership evidence. This is the same sentence one level down:
a matching pathname that is *not a directory at all* is not evidence of
absence either. Both times the registry answered a narrow question with a
value that could not represent the answer.

### Regressions

- a symbolic link at a registered root's pathname: `removeOwnedRoot` refuses,
  the record is kept, the link stands, the external directory it points at
  and that directory's subtree are untouched, retirement is refused, and the
  suite hook reports rather than deleting;
- a regular file at a registered root's pathname: the same, without a link to
  follow.

Both mutation-checked against the pre-correction semantics: forcing
`inspect()` back to a bare absent/directory answer fails exactly these two
cases and no others.

The `error` state is proven by `evidence/lstat-error-probe-2026-08-22.mjs`
rather than by a suite case, because inducing `EACCES` requires a `chmod` on
the temporary directory itself, which no other test in the file could
tolerate, and because running as root defeats the permission. **Open:** if
that state is ever worth a suite regression, it needs a per-test `TMPDIR`
that the registry does not currently take.
