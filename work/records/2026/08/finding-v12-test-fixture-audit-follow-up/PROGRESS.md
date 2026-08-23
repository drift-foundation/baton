# Progress: v12 test-owned fixture residue

Implementer: `baton.claude`. Work `W2907`, bound to this canonical record.
Follow-up to the cancelled W30. This file did not exist at handoff — the
Tuner correctly declined to create it, since repository policy gives it one
writer — so it starts here.

## 2026-08-22 — implementation complete, awaiting review

Re-checked the audit against the current tree first. It holds, with one dated
supersession: the family count is nine, not eight, because W2928 landed
`v12/test/authority_fixture.mjs` on 2026-08-22 with a `v12-authority-*` family
and its own private registry. Recorded in `FINDING.md` under **Implementation
revalidation**, together with the implementation decisions this correction
needed.

### Changed

- **New `v12/test/owned_roots.mjs`** — the one owned-root registry.
  `ownedTemp(prefix)` creates and records in the same call; `ownedRoots()`
  reports; `removeOwnedRoots()` removes exactly the recorded roots,
  link-nonfollowing and idempotent, and forgets them. There is deliberately no
  way to register a path from outside.
- **`v12/test/unit.test.mjs`** — `scratch()` now comes from the registry and
  the module registers `after(removeOwnedRoots)`. All 51 call sites are
  covered by that one change.
- **`v12/test/placement.test.mjs`** — the same, plus its five directly created
  families (`owned`, `stranger`, `impostor`, `absent-parent`, `cli-stranger`)
  and `entry-unowned`. Every existing in-test removal and the `entry-unowned`
  `finally` are untouched; no assertion was changed.
- **`v12/test/authority_fixture.mjs`** — its private root list is folded into
  the shared registry.
- `mkdtempSync` is no longer imported by either test module. The registry is
  only a boundary if it is the reachable primitive.

### Tests — 4 new cases

`v12/test/fixture_cleanup.test.mjs` drives
`v12/test/fixtures/fixture_cleanup_probe.mjs`, a genuinely failing `node:test`
file that lives outside the `test/*.test.mjs` glob so it cannot fail the suite
directly:

- a PASSING probe run leaves no fixture root and an untouched external target;
- a FAILING probe run leaves none either — the case W30 actually hit, including
  a root created AFTER the failing test;
- removal unlinks symbolic links instead of following them, proven against an
  unregistered target that keeps its bytes and its subtree;
- the registry only removes what it handed out: prefixes with a separator are
  refused, and cleanup is idempotent and forgets.

Both probe cases assert against exact paths the child reports, and separately
that no entry of any of the nine families survives in a sandbox the regression
owns.

### Verification

`cd v12 && TMPDIR=<bracket> just test` — **141 pass, 0 fail**, and the bracket
holds **zero** roots of any test-owned family (only Node's own
`node-compile-cache`, which the audit also saw). The same bracket with the
registry's removal neutered holds **130** leaked roots: 66 `v12-authority-`,
58 `v12poc-test-`, 5 `v12poc-placement-`, 1 `v12poc-impostor-`. Docker was not
needed. `evidence/verification-2026-08-22.txt`.

**The regression was mutation-checked.** With the probe's `after` hook removed,
both probe cases fail with "survived the probe"; restored, all four pass. A
cleanup regression that passes either way would have been worse than none.

### Three defects in my own first attempt, for the record

- The probe reported nothing and the regression was vacuous: `node --test`
  spawned from inside `node --test` refuses to run files "recursively" and
  exits successfully. The child now runs with `NODE_TEST_CONTEXT` deleted.
- The symlink case removed its own target — the "external" directory was a
  registered root, so it died as a root rather than by being followed, and the
  assertion proved nothing. It now uses an unregistered target disposed in
  `finally`.
- The failure-mode assertion expected `pass 3` from a run in which one test is
  supposed to fail. It now asserts three tests ran with exactly one failure.

### Left deliberately undone

- **Host cleanup.** `/tmp/w30-fixture-audit.Lmr3aa` is untouched — still
  present, still 168 direct children — and so are the ambient `v12poc-*` roots
  in `/tmp` (1098 and 78 at the end of this session). The finding keeps that
  separately authorized, and nothing here classifies or deletes them. The only
  directories this work removed are the two brackets it created itself, by
  exact path.
- Worth noting for whoever authorizes that cleanup: my own W2928 gate runs
  earlier today contributed to the ambient count, because the correction had
  not landed yet. From this change forward the suite adds none.

### State

**Awaiting review.** No review pass has been recorded on this record yet.

## 2026-08-22 — round-1 review P1s corrected, awaiting re-review

Both findings were right, and the first is the sharper one: my registry
claimed ownership of a NAME while this record's own audit says in as many
words that a matching path is not ownership evidence.

### P1a — ownership is an identity

Six placement families remove their roots in their own tails, so once a test
deleted a root the suite owned nothing at that pathname — and the hook stayed
armed on it. The reviewer recreated the pathname and the hook deleted the
replacement.

- `removeOwnedRoot(path)` removes AND forgets as one action; all six tails use
  it and `rmSync` is no longer imported by `placement.test.mjs`.
- `retireOwnedRoot(path, { observedAbsent: true })` forgets a root the product
  path removed, and refuses unless the absence is positively observed.
- `dev`/`ino` are recorded at creation and re-checked before removal; a
  pathname that now resolves to a different directory is refused and its
  record kept. Stated as a second line, because nothing between `lstat` and
  `rm` is atomic.
- Entries drop only after removal succeeds.

### P1b — the report is a file the parent names

The regression scraped the child runner's stdout, which the runner's reporter
and isolation own. Under the default isolation on a supported Node that stdout
is hidden, so both cases failed and my claimed gate was not reproducible from
the documented `npm test`. The probe now writes to a parent-nominated file;
the parent diagnoses spawn error, signal, missing report, malformed report and
incomplete report as separate named outcomes with exit status, signal, stdout
and stderr; and `reachedIntendedFailure` is recorded before the assertion so
the intended failure is provable without output.

**This is the same mistake twice.** W2928's race harness had exactly this
defect and I corrected it there earlier the same day, then did not carry the
lesson across. Recorded in `FINDING.md` rather than quietly fixed.

### Tests — 2 new cases (155 total)

- recreating a removed root's pathname survives suite cleanup, and retirement
  needs its observed absence;
- a pathname that is no longer our directory is left alone, its record kept,
  and the hook reports rather than deleting.

Both mutation-checked: splitting remove-and-forget apart fails the takeover
case; removing the probe's cleanup hook fails both probe cases.

### Verification

`cd v12 && TMPDIR=<bracket> just test` — **155 pass, 0 fail**, zero test-owned
roots in the bracket, no ambient Node options. The probe channel is proven
under `--test-isolation=process` and `=none` and under a reporter that prints
no test output.

### Unchanged

Host cleanup is still not performed and remains separately authorized.
`/tmp/w30-fixture-audit.Lmr3aa` is untouched with its 168 direct children, as
are the ambient `v12poc-*` roots.

### State

Changes requested by `review-2026-08-22T14-35-33Z.md`; superseded by the
round-3 entry below.

## Round 3 — 2026-08-22, re-review correction

`review-2026-08-22T14-35-33Z.md`: one P1. Correct, and it is the round-1
defect one level down. Evidence: `evidence/correction-round3-2026-08-22.txt`.

### P1 — absence and "not a directory" are different answers

`identityOf()` returned one `null` for an absent path, an existing
non-directory entry and a failed `lstat`, and removal read every `null` as
idempotent absence. A symlink or file at a registered root's pathname made
`removeOwnedRoot` report success, drop the ownership record and leave the
replacement standing — cleanup claiming to have removed a root it had
actually walked away from.

- `inspect(path)` replaces it with four states: `absent` (`ENOENT` only),
  `directory` + identity, `other` (+ the kind of entry), and `error`.
- Only `absent` returns quietly. A different directory, a non-directory entry
  and an `lstat` failure all refuse, KEEP the ownership record, and report;
  the suite hook still aggregates those into `left N root(s) alone`.
- `retireOwnedRoot` requires positively observed `ENOENT`, not merely a
  failure to see a directory.
- `ownedTemp` requires a real directory identity at creation instead of
  recording `null`.

The round-1 entry's third correction is marked superseded in `FINDING.md`
rather than rewritten: its boundary was right and only its implementation was
too narrow, and that is the part a later reader needs.

### Tests — 2 new cases (161 total)

- a symbolic link at a root's pathname: refusal, record kept, link standing,
  external target and its subtree untouched, retirement refused, hook reports;
- a regular file at a root's pathname: the same, with no link to follow.

Mutation-checked: forcing `inspect()` back to a bare absent/directory answer
fails exactly those two cases and nothing else; restored, 8/8 in the file.

The fourth state has a probe rather than a suite case —
`evidence/lstat-error-probe-2026-08-22.mjs`, which induces `EACCES` by
dropping search permission on a private `TMPDIR` and skips under root. It is
recorded as **Open** in `FINDING.md`: a suite regression for it needs a
per-test `TMPDIR` the registry does not take today.

### Verification

`cd v12 && TMPDIR=<bracket> just test` — **161 pass, 0 fail**, node v24.14.0,
no ambient `NODE_OPTIONS`. The bracket retained zero roots of any of the nine
test-owned families; only Node's `node-compile-cache`. The probe channel is
re-proven under `--test-isolation=process` and `=none`.

The test count moved 155 -> 161 rather than 155 -> 157: W2928's authority
files are still uncommitted and gained cases between rounds. Only two of the
six are mine.

### Unchanged

Host cleanup is still not performed and remains separately authorized.
`/tmp/w30-fixture-audit.Lmr3aa` is untouched with its 168 direct children, as
are the ambient `v12poc-*` roots. This round removed only the four brackets it
created itself, by exact path; earlier rounds' scratch paths, mine and the
reviewer's, are listed in the evidence file for the operator rather than
removed.

### State

Signed off by independent re-review; superseded by the sign-off entry below.

## Signed off — 2026-08-22

`review-2026-08-22T14-54-18Z.md`: **signed off**. The round-3 P1 is corrected
and the reviewer re-derived each property rather than taking the correction's
word for it — the four-state inspection, `ownedTemp` registering only a
successfully inspected directory, entries dropping only after exact removal or
positively observed `ENOENT`, `retireOwnedRoot` rechecking independently of the
caller's assertion, and both takeover regressions restoring their state before
the module hook runs.

### Revalidated at sign-off, not assumed from the earlier run

- `cd v12 && TMPDIR=<bracket> just test` — **161 pass, 0 fail**; the bracket
  retained zero roots of any of the nine test-owned families, only Node's
  `node-compile-cache`.
- `git diff --check -- v12` clean.

### What the reviewer could not run, and why it does not weaken the sign-off

The two child-probe cases failed in the managed reviewer boundary because
nested `spawnSync(process.execPath, ...)` is denied `EPERM` there. That is the
round-2 correction working: the parent named that exact spawn failure instead
of mistaking it for a missing report or a clean run. The six registry-only
cases and the `EACCES` probe ran and passed in that boundary, and the full
gate is green here.

### Host state at sign-off, read-only

Nothing was cleaned by this Work, and nothing is authorized to be:

```text
/tmp/w30-fixture-audit.Lmr3aa   present, 168 direct children, mtime Aug 21
ambient v12poc-test-            1098
ambient v12poc-placement-          78
ambient v12poc-absent-parent-       8
ambient v12poc-cli-stranger-        8
ambient v12-authority-              0
```

The counts are unchanged from the end of the correction round, which is the
operational point: the suite is no longer adding to them. `v12-authority-` was
66 during the correction round and is 0 now — those were removed by something
outside this Work, and I am recording the observation rather than claiming the
cause.

### Carried forward, outside this Work

PLAN item 10: the one-time host cleanup of the exact root
`/tmp/w30-fixture-audit.Lmr3aa` (exact-root, non-following — it contains
external symlinks) and any disposition of the ambient `v12poc-*` roots. It
needs separate authorization and is the reason this Work advances to
operations rather than closing. The earlier rounds' retained reviewer and
implementer scratch paths under `/tmp/w2907-*` are listed in
`evidence/correction-round3-2026-08-22.txt` for the same operator.

### State

**Signed off; advanced to operations.** Passed rather than closed, so the
approver owns the host-cleanup authorization and the terminal disposition.
