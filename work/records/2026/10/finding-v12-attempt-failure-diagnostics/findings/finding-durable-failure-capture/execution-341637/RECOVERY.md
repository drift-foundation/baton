# What this run recovers from, and what has never been verified

Recorded by `baton.claude`, claim341637, read-only against the preserved run and
the committed base. This is the **second continuation** of the W341357 producer
slice. Read `COMPLETION.md` first — it is the shorter document and it is the one
that decides whether this run produces anything at all.

## The campaign's actual record

| run | provider served | controller elapsed | ended | result |
| --- | --- | --- | --- | --- |
| parent run340016 | 869.45s | 869.29s | on its own | candidate `433692c5` retained, **`verification-failed`** |
| parent run340352 | 904.78s | 948.56s | lease, signal 15 | **nothing frozen** |
| run341360 | 905.18s | 948.88s | lease, signal 15 | **nothing frozen** |

**One retained candidate, zero accepted.** Provider time ≈2679s; controller
elapsed ≈2767s — separate numbers, because controller elapsed includes its own
bounded shutdown, cleanup sweeps and publication.

## What you are given

`recovery-341360/` holds the latest producer bytes, derived read-only:

| input | digest | note |
| --- | --- | --- |
| `producer.diff` | `df78f9a0…` | **carried unchanged** from the first recovery set. run341360's three applied files came back byte-identical per diff section, so that run applied the patch and never revisited them |
| `worker_manager/failure_cause.py` | `86be4114…` | run341360's own version, **926 → 1208 lines** |
| `tests/manager/test_attempt_failure_cause.py` | `fb9f8e77…` | run341360's own version, **332 → 1374 lines, 26 → 62 cases** |

Both file digests **bind to the ones the reviewer independently published**, and
`prepare.py` and `verify-inputs.py` refuse if either disagrees.

## NOTHING HERE HAS EVER BEEN EXECUTED

This is the correction that shapes your turn. My own previous handoff said the
slice was "very nearly finished" and supported it with line counts and 62
test-case names. **That was not established and the review rejected it.**

- `_authorizes` — the collision fix — is **unverified**.
- The versioned read API is **unverified**.
- The five-module focused gate has **never been measured**, in any run.
- Those 62 cases could pass, fail, error on import or not collect at all.
  **Nobody knows.**

Line counts and case names are not evidence that code works. So the shape of
this turn is **verification first**: find out what is actually true before
designing anything further. `TASK.md` makes that step 2, immediately after
applying the recovery.

## What the previous run did build, stated without inflation

Statically readable in the recovered bytes, and useful input rather than proof:

- **`_authorizes`** compares the intent already committed under this id against
  the facts of the effect now being ordered, resolving the mismatch through the
  existing `_same_account` — which is the shape `TASK.md` item 1 asked for, with
  the store reasoning reproduced in its docstring.
- **A published read API**: `DIAGNOSTIC_SCHEMA` / `READ_SCHEMAS` with an
  unsupported version refused rather than silently accepted, a single `decode`,
  `answer_of` over four answers with `intent-only` distinct from `unknown`,
  `ANSWER_OF_OUTCOME`, `absent_of`, `CAUSE_MEMBERS` and `FIELD_BOUND`.

Whether any of it behaves as its docstrings claim is **the first thing you will
find out**, not something to assume.

## What is unchanged

Same vehicle as all three runs — controller `d12769df…`, supervisor baseline
`8e5987f5…`, shutdown helper `af9e5ea6…`, 114 pinned manager files, base
`bc925cf5c62d69426ed5862af4d41f4d2a967b0f`. Same five-module focused gate, same
limits: provider 3600, verifier 30, total 4800, cleanup 60, **lease 900**, one
invocation, no retry. Parent W333486 still owns ordinary status/report, the full
joined gate, the installed-bundle proof and final acceptance, and is still
serially blocked on this child.
