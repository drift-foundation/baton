# Activity observation — the implementation

Recorded 2026-09-15 by baton.claude, claim 177898, per owner reroute M177542,
which selects `ACTIVITY-DOCUMENT-DESIGN-175025.md`
`sha256:014be97ecf91807fde86d1d84c0d05ede70b3bdd12790a23e3abc3ee57e99906` as
consolidated by `review-2026-09-15T04-29-53Z.md`
`sha256:1b9968b2eb7fb79e5c44e7c1d9ff385e1d2293b71c1689ea34c4bd6175b58ec1`.

**Both pinned documents were revalidated by hash before any edit, and all six
selected source paths were still byte-identical to
`review-evidence-175051.json`.** Nothing in the accepted design had drifted.

## 1. What an operator can now be told, and by which program

| Where | What it owns |
| --- | --- |
| `v12/worker/claude_agent.py` | the baseline, the bounded metadata scan, the monotonic total and every way it becomes **unknown** |
| `v12/worker/baton_worker.py` | the `work`-only publisher: one slot, 1 s cadence, 2 s stop, exclusive staging, rename **over** |
| `worker_manager/exchange.py` | `activity.json`, its own schema and parser, its vocabulary entry, and the six identities a reader holds it to |
| `tools/single_worker.py` | the module-owned admission slot, the off-loop helper, the `refresh_runtime` enqueue, the bootstrap unwind |
| `tools/stage_execution.py` | the staged deployment's admission and its `_closers` entry |
| `tools/dogfood_operator.py` | `_Channel` **stops being an activity source** |

`worker_manager/attempts.py` is unchanged: `observe_activity` and
`attempt_activity_of` already did exactly what this needed, and the count now
reaches them from the right stream.

## 2. The baseline is proved, never measured

`_bound_activity` records **one boolean this adapter already knows** — whether
`_scratch` was uninjected, and therefore a `tempfile.mkdtemp` this process just
created. That directory's `.claude` is provably empty of native files at that
instant, **with no scan and no stat**, which is a true pre-launch zero admitted
without the launch waiting for anything.

An **injected, reused or restored home is `unknown` for the whole operation.**
Nothing is estimated, no scan reconstructs a baseline, and no restored history
is subtracted.

The mtime rule of the fourth revision stayed withdrawn, for the counterexample
that killed it: 1000 bytes with 10 appended has 1010 bytes *and* a new mtime,
so that rule counted 1010 when the answer is 10.

## 3. The total is monotonic, and freezes rather than falling

Per file, its **identity** `(st_dev, st_ino)` and its **last observed size**.
Each scan adds `max(0, current - last)` per surviving file of unchanged
identity; a file first seen after the proved-empty baseline contributes its
whole size once. **Shrink, disappearance and identity change freeze it**: the
total stops advancing, is never reduced, and does not resume.

Every bound fails toward unknown: depth 4, 256 entries examined, 64 tracked
identities, `2**53 - 1` bytes. Regular files only, `follow_symlinks=False`,
nothing opened. The credential entry is excluded twice over — it is a symlink
and it is not a native file name.

## 4. The document, and what is compared

`activity.json`, schema `baton.worker-exchange.activity/1`, eight closed
members. Six of them are the identities, and `observed_activity` compares every
one. **Three travel and three are derived and one is read back:** the attempt
and the session travel in the ingestion request with the **local** event-root
capability; the sequence, operation and operation id are derived by rule; and
`command_digest` is read off the manager's own published command, in the
namespace the container holds read-only, **on the helper's thread and not on
the sweep's**.

This is the one place the implementation makes the accepted design's "the
enqueue carries the six identities" more precise rather than following it
literally. The pinned property the design states twice — *no file read and no
`launch.adopt` on the enqueue path* — cannot hold while the sweep also produces
`command_digest`, because that digest is the digest of a file. Moving that one
read onto the helper keeps every identity manager-held and takes the last read
off the serving thread. **Nothing is taken from the activity document, and the
root is never a wire field.** Flagged here rather than left for a reviewer to
find.

`ACTIVITY_DOCUMENT` is in the closed `EVENT_DOCUMENTS` vocabulary, so a
conforming worker's own diagnostic is not reported as a foreign entry. The
entry budget is asserted rather than assumed: four lifecycle documents plus
`activity.json` plus the one staging temporary is **six of 64**.

`_decoded` gained one opt-in keyword, `numeric`, shaped exactly like the
existing `nested`. **No existing caller names it**, so the receipt, state and
terminal documents are read by the identical rule as before — and that is now
asserted against the decoder directly, because every lifecycle member has a
second guard that would have hidden a wide-open decoder.

## 5. The publisher, and what it may never do

Started after `dispatched` is published and stopped before any outcome is, on
every path out of `handle`. One integer slot, last value wins. **Only a
positive integer total is published**; `None` and `0` are different answers
from a count and neither is written. An observer fault is an unknown count, not
the publisher's death and not the turn's. An over-bound stop **abandons without
joining**, and the binding is what makes that safe.

Staging is the one fixed name `.activity.json.tmp`, created
`O_CREAT|O_EXCL|O_NOFOLLOW`. An existing entry **suppresses the write** — it is
never unlinked, truncated or written through — which keeps at most one
temporary and therefore keeps the namespace inside the entry budget. The
published file is replaced by rename **over** it and never renamed away.

`describe` runs no publisher: it invokes no provider.

## 6. Exclusion — one helper per held store, and no attempt in the key

A module-level registry in `single_worker`, acquired by an atomic nonblocking
compare-and-set **before** the helper starts, by the **same primitive from both
factories**. The key is the file the held control store actually has open,
asked of the handle because neither factory is given a path.

An occupied slot means the replacement **starts no helper and ingests
nothing**. The slot is held until **positive termination**; a timed-out stop
leaves it occupied indefinitely and leaves the handle open, and the fact is
reported — through `release`'s collected refusal for the staged path and out of
`dispose` for bootstrap. Construction failure releases it **only if the helper
never started**.

The owning ingestion thread opens its handle on first use and **closes its own
handle during its own finalization**; that exit is what frees the slot. No
other thread ever touches it.

## 7. `_Channel` stops being the source

The outer `docker exec` stderr was never the provider's. `ClaudeAgent` runs the
provider with stdout on a private anonymous pipe it reads inside the container
and stderr on `DEVNULL`, so what that loop counted was the worker's transport
noise — a liveness number about the wrong process. The counting, the cadence
and `_activity_observer` are gone; the drain keeps the one job it always had.

## 8. Verification

Five full v12 suite runs — one at the selected baseline, one part-way
through implementation which is **not** offered as evidence, and three at this
candidate — plus twenty-two reversal probes and the focused re-runs.

- **Baseline** (the six pinned sources restored byte-exactly, hashes
  re-verified): 7259 tests, **89 failures/errors**.
- **Candidate**, final run: 7333 tests (74 new), and the failure set is the
  **identical 89 minus one** — declaring the `expected` operand also satisfied
  a pre-existing `context_delivery.py` case. The two earlier candidate runs
  agree.
- **This implementation introduces no new failure.** The 88 that remain are
  pre-existing at the pinned baseline and belong to the untracked
  `context_delivery.py` / `provider_context.py` work in this tree and to
  thirteen `test_stage_execution` errors that fail identically with the
  original product files. **They are reported, not fixed: they are not this
  Work's.**

**Twenty-two reversal probes**, each one reverting a single guard, confirming
that exactly the intended case fails, and restoring the file with its hash
compared before and after. Nineteen confirmed on the first attempt.

**Three were non-evidence and are reported as such**, because a probe that
passes with its guard removed is a test that was not testing it:

1. **The shrink freeze.** `test_truncation_freezes_the_total` asserted only
   that the number had not fallen, which is also true of a total that simply
   carried on from the smaller size. Corrected to append after the truncation
   and assert the total does not resume.
2. **Only a positive total is published.** The `None` case was caught by the
   publisher's own last-value dedup rather than by the guard, so a **zero**
   would have been published. Corrected to drive `None`, `0`, `False`, a float
   and a string, each over its own delivery.
3. **The observer-fault containment.** The turn survives regardless — the
   publisher is a separate thread — so "never stops the turn" proved nothing
   about the guard. Corrected with a case where one scan fails and the next
   succeeds, asserting the publisher still publishes.

A fourth probe, over `_decoded`'s bounded-text rule, exposed that **no
lifecycle member is guarded by the decoder alone**: every one has a vocabulary,
grammar or correlation check behind it, so a wide-open decoder failed nothing.
The case now asks the decoder directly, which is the only honest way to state
"no existing parser is relaxed".

A fifth, over the 256-entry scan bound, passed because the overflow files were
not native files and the answer was unknown either way. Corrected to place a
real native file the unbounded walk would have counted.

**Measured verification spending this claim: 2,776 s of full-suite runs
(550 + 553 + 558 + 555 + 559 s), plus roughly 190 s of focused module runs and
reversal probes — about 2,966 s total.** No live provider, no engine run, no
container and no Git operation.

## 9. What this does not deliver

- **No viewer path is edited.** Historical-after-terminal display remains
  W167896's follow-through, and its current `unknown` stays the honest display
  until that owner takes it up. Visible counts are not claimed delivered.
- **No live-provider evidence.** The growth-before-completion case runs a
  deterministic provider at the normal adapter boundary and is labelled
  simulated-provider coverage.
- **The vendor layout beneath `.claude` is still not known.** The scan is
  deliberately layout-independent; if `*.jsonl` turns out to be the wrong shape
  for the supported profile, that is a narrow provider-specific question for
  the first live turn, not a gap in this change set.
- Follow, sink expansion, colour, pause, search/filter, retention and raw
  stream UX remain W39649/v13 material.
