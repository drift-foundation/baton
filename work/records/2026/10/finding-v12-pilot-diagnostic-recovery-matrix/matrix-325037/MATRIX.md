# The joined diagnostic and recovery matrix — observed

Claim 325037, 2026-10-18. Driven by `matrix.py` on the composed native Job
fixture lineage W321690 used, imported with provenance and not modified.
Seven scenarios, all observed, 2.197s total; each has its own JSON answer with
exact identities, injected inputs, assertions and measured duration, and
`MANIFEST.json` binds every file by SHA-256.

Simulated and labelled per scenario: the ENGINE answers `run`/`inspect`/`ps`
with no daemon, and the PROVIDER is injected at the adapter's own process
seam. Nothing here claims live isolation or engine evidence. No owner receipt,
candidate or verdict was fabricated — every durable fact below was written by
the product's own operations, driven by the manager's own `sweep`.

## 1. A failed or empty provider turn cannot falsely complete

| Scenario | Injected | Settles at | Candidate |
| --- | --- | --- | --- |
| `1a-provider-failed` | provider exits 1, writes nothing | `exceptional` | none |
| `1b-no-candidate` | provider exits 0, writes nothing | `exceptional` | none |

Both settle the implementation stage at **`exceptional`** after ordinary
ticks, with no proposal published and the review and integration stages left
`blocked`. So neither outcome can be mistaken for a completion and neither
produces something an owner could approve.

**Where the diagnostic owner actually is, stated precisely:** it is the
stage's own `exceptional` state in `baton_v12.job_manager.status` — the same
projection `baton-v12-stack manager status` serves — and NOT a
`pending_endings` row, which was empty in both cases. That is a correction to
how I would have described it from the seam names alone:
`job_manager/ending.py pending_endings` answers for endings awaiting
settlement, which is a different class from a turn that produced nothing.

## 2. Restart does not duplicate review ownership

`2-restart-no-duplicate`: after the implementation stage completed, a FRESH
serving composition over the same stores — which is what an ordinary manager
restart is — carried the review stage from `queued` to `waiting` with the
implementation attempt unchanged (`attempt-7b5e070a…`) and exactly one review
attempt (`attempt-9e961a44…`). No second reviewer, no second correction.

## 3. A stale episode and a wrong principal both refuse

`3-stale-and-wrong-principal`, asked through real sessions while an assignment
was live, with the authority's own sentences:

- stale generation: `stale assignment`
- another participant: `this session acts for 'baton.gemini'; the assignment
  names 'baton.claude'`

## 4. A correction stays bound to its own candidate and attempt

`4-correction-binding`: a `changes-requested` verdict reopens the
implementation stage (`waiting`) and blocks the review, rather than completing
the review. The reopened stage gets a SECOND attempt
(`attempt-965a8ab8…`) while the first (`attempt-7b5e070a…`) is retained, and
the Work, Job and submission identities are unchanged. The published proposal
from the first round is still there (one proposal), so the correction adds a
round rather than rewriting the candidate.

## 5. Cancellation and a non-satisfying ending stay honest

`5-cancellation-and-non-satisfying`: cancelling the live assignment through the
public session left the Work `open`, `queued`, with no handler and no outcome —
a cancelled assignment is not a cancelled Work. The owner's
`disposition close --outcome non-satisfying` through the installed command then
closed it with that outcome and the operator's own rationale, and the proposal
survived the closure (`evidence_preserved`). No acceptance was implied anywhere.

## 6. One writable authority — what that actually means here

`6-one-writable-authority`, three observations:

- A second WRITABLE handle on the same store file is **accepted**. That is
  SQLite's own behaviour and `session.py`'s stated trust boundary — "whoever
  can open the store file is the deployment".
- What is refused is the thing that matters: two handles racing one claim give
  `first_claim` an assignment and the second **`refused: Work is already
  claimed`**. One writable authority is enforced by the claim's
  compare-and-swap, not by the file handle.
- A read-only handle refuses every transition (`a read-only handle answers the
  committed record and performs no transition`), and an open naming the wrong
  authority UUID refuses with the exact identity mismatch.

So the packet may claim one writable authority per Work, and should say that
the enforcement is the claim rather than the file.

## What this matrix does not cover

Disposable recovery-set verification (`record recovery-manifest` /
`recovery-check`) is W321688's accepted surface and is not re-proved here;
held-unknown RUNTIME quiescence needs the engine-absence vector rather than
this provider seam, and interrupted-provider-session recovery is deferred under
324905. The human-approval positive path belongs to W325034 and the parent.
