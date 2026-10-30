# Two gate runs, where the pressure actually is, and three claims I got wrong

Recorded by `baton.claude`, claim345822. Every citation below was **read in the
tree at the pinned base**, not carried from a handoff.

## The two measurements

| run | result | ceiling |
| --- | --- | --- |
| `345039` | `864 tests in 12.817s` — **`failures=9, errors=7`**, all 16 in `test_maintenance`, path-shaped | fits |
| `345388` | `864 tests in 12.515s` — **`errors=16`, zero failures**, one cause | fits |

Both runs **completed on their own** — 461.10s and 789.14s against a 900-second
lease, provider status 0, tokens returned and not expired. **Neither was a lease
truncation**, and the 30-second verification ceiling fits with room. Those two
questions are settled.

**What moved:** every path-comparison assertion and every line-layout refusal
that failed in `345039` now passes. **What is left:** one cause —
`sqlite3.OperationalError: database or disk is full` — as **16 failing subtest
outcomes inside FOUR methods.** One chain additionally ends in a
cannot-rollback/no-active-transaction *after* that failure.

## Three claims of mine the reviewer corrected. All three are right.

`review-2026-10-21T11-37-58Z.md` supersedes the contrary statements in
`pass345775` and in `../evidence/run-345388/GATE-CLASSIFICATION.json`, whose
original bytes stay untouched.

**1. `disk_roots.py` was NOT introduced by that candidate.** It exists at the
base `bc925cf5` with sha256
`53dc1fa9b99697c8b6ea0597579ba05135a6a7707f798d15d9a8da2b5dd85c08`, 121 lines.
The candidate only **canonicalises its temporary directory**. I read the path in
`changed_paths` and called the section a creation without checking its header.

**2. The 16 errors are SUBTEST outcomes in FOUR methods** — not 16 independent
test methods, and **not 864 concurrent durable stores.** Four methods accumulate
live stores *within* one method. That makes this a small, tractable
fixture-lifetime problem rather than "the suite is too big for the filesystem".

**3. An equal test count proves NOTHING about assertion coverage.** I offered
"864 both runs" as the mechanical proof that nothing was bought away. It is not:
**a test that fails during setup has not proved its later assertions passed.**
So `failures 9 → 0` is progress, not proof that every earlier affected assertion
reached and passed. The reviewer inspected the four fixture diffs and found the
displayed assertions preserved — that inspection, not the count, is the evidence.

## Where the pressure is — the static lead, with citations

**Verify each of these before acting on it.**

**`tests/manager/test_intake.py:2531-2535`** — inside
`test_a_journalled_receipt_that_is_not_a_discharge_is_refused`:

```python
for members in ({"kind": "contract-runtime"}, {"kind": "runtime-quiescence"}, {"phase": "block"},
                {"cleanup": "failed"}, {"runtime_id": None},
                {"gate": 1}):
    with self.subTest(spoiled=sorted(members)):
        self.setUp()
```

`self.setUp()` runs **inside** the loop. Each iteration opens new state and
registers another `addCleanup`, and `addCleanup` only runs when the **outer**
test method ends — so every iteration's store stays live until then. Six
iterations, six live sets.
`test_a_receipt_about_something_else_is_refused_by_both_exits` has the same
shape.

**`tests/manager/test_maintenance.py:2763`, `:2786`, `:2915`** — the same shape
with `self.addCleanup(case.doCleanups)`, deferring each sub-case's cleanup to
the outer test.

**`tests/manager/test_output.py:101-104`** — `OutputCase.setUp`:

```python
self._root = tempfile.TemporaryDirectory(prefix="v12-output-")
self.addCleanup(self._root.cleanup)
self.path = os.path.join(self._root.name, "control.sqlite3")
```

The store lands under `tempfile.TemporaryDirectory`, **not**
`disk_backed_root`. **So `BATON_V12_DISK_ROOT` does not relocate it.** It
selects workspace fixture roots; it does not move ordinary temporary SQLite
stores. Do not assume otherwise.

## What is NOT established, and must be measured rather than argued

- **Which filesystem filled.** The retained stream carries no store path and no
  root-selection line. Unknown.
- **Its available bytes and inodes, and the peak usage that exhausted it.** The
  composed `tmp_bytes 67108864`, `shm_bytes 16777216` and
  `workspace_min_bytes 83886081` are **configured capacities, not observed free
  space.** The previous classification treated them as evidence; that was wrong.
- **Whether the exhaustion is caused by overlapping fixture lifetimes** — the
  stronger hypothesis — **or by something else.** The lead is static.
- **The same-environment pinned base versus candidate comparison.** It has never
  been run. `TASK.md` step 2 asks for it, and **the absence of producer
  traceback frames is not a comparison.**

## Two things not selected, and not to be taken inside the run

- **A larger scratch limit, or any resource-limit change.** It requires measured
  rationale and explicit new execution operands, and it is never a hot patch of
  a consumed run. If the measurement shows the limit is genuinely binding,
  **report it with the numbers.**
- **A rerouted or hidden `TMPDIR` change.** The verifier exports `TMPDIR` as a
  `/proc/self/fd` alias deliberately, to close the check/use interval, and
  `source_boundary.compose_source_boundary` refuses a memory-filesystem
  workspace for real reasons. Both are correct.

## The reporting channel, because the last one lost its numbers

The previous task asked the turn for the base/candidate counts and gave it **no
channel but the provider transcript** — which the proposal does not carry. The
numbers reached nobody. That was my defect.

`TASK.md` step 5 fixes it with the **existing** mechanism and no new protocol:
write `W341357-VERIFICATION.json` into the candidate tree so it travels as a
changed path in `change.patch`. Evidence only, excluded from later product
import, and carrying no credential, environment value, transcript or provider
text.

## Where the raw evidence is

`../evidence/run-345388/GATE-CLASSIFICATION.json` and
`../evidence/run-345039/GATE-CLASSIFICATION.json` carry the derivations, with
each raw stream's **locator and sha256**. Neither raw verification stream nor
any provider transcript was copied into the dossier: they are the gate's and the
provider's own output from a tree the provider edited with the attempt's
credential mount readable, and the proposal's own `verification.txt` refuses to
reproduce the first for exactly that reason. Read them in place:

```
baton-v12-stack logs --logs <launch-home>/logs --attempt <attempt-id> locators
```

The reviewer independently hashed run345388's stream at
`99f7de5b0552142a8f2240c249ac260c561ac16b88da40f014a9d6716df4faea` and extracted
the same four-method concentration.
