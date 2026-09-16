# Activity source and transport — revised design

Recorded 2026-09-15 by baton.claude, claim 174521, per owner selection M174518.
**Design only.** No product or test file edited, nothing executed. This
supersedes `ACTIVITY-SOURCE-DESIGN-174354.md`, which remains as history, and
answers the four P1 gaps in `review-2026-09-15T03-16-10Z.md`.

## 0. What I got wrong, corrected first

**"Nobody has made that observation in this tree" was too broad.** This
dossier's own FINDING already records the W52821 observation: native JSONL
showed ongoing message and tool activity while container stdout did not supply
useful incremental output. That is retained evidence and I should have reused it
instead of proposing an experiment to rediscover it.

**And the experiment I proposed could not have decided anything.** A scripted
provider emits on its script; its arrival times say nothing about the real
Claude CLI. Worse, several 4096-byte reads can all be slices of one final JSON
payload, so "more than one arrival" would not have meant incremental output.
Candidate A is withdrawn on the evidence, not deferred.

## 1. Source — private native-JSONL metadata

**Selected: file metadata of the adapter's own native session file, observed
inside the container.** Size only; no line, record or content read. A length is
content-free by construction, which is the property that made the original
count safe and is the only reason this may cross at all.

### Open, and stated as open rather than assumed

**How the adapter identifies its own session file before completion.**
`claude_agent._prepared_home` (`:1941`) establishes a private `.claude`
directory under per-turn scratch; it establishes **no session-file identity**.
That binding is genuinely unresolved and this design does not invent it.

What the implementation must specify when it resolves it:

- **Bounded discovery** under the prepared home only, with a fixed depth and a
  fixed maximum number of entries considered.
- **Type and link checks** — a regular file, opened `O_NOFOLLOW`; a symlink,
  directory or special file is not a source.
- **Binding to this invocation** — the file must have appeared or grown after
  this turn's baseline, so restored history cannot read as fresh growth.
- **Baseline handling** — record the size at start; report growth relative to
  it, never absolute size.
- **Replacement, truncation and rotation** — a file that shrinks or is replaced
  makes the source **ambiguous**, not smaller. Ambiguity means unknown.
- **Never counted:** credential files, arbitrary home growth, or any path
  outside the identified session file.

**A missing or ambiguous source leaves activity unknown. That is not a provider
failure and must not be reported as one.**

## 2. Transport — a separate, separately versioned diagnostic document

**Not `state-<operation>.json`.** The review is right on both counts and the
code confirms them:

- `serve_exchange` publishes `dispatched`, runs the operation **synchronously**,
  then publishes `answered` — or `_faulted` publishes `faulted` — before the
  terminal. **There is no periodic writer today.** A periodic writer racing
  those publications can overwrite `answered`/`faulted` and destroy terminal
  causality; `_publish`'s atomic replacement orders bytes, not publishers.
- `STATE_SCHEMA` is `baton.worker-exchange.state/1`; `_decoded` rejects missing
  **and extra** members and permits bounded text, lists of text or null — it
  rejects an integer even once the name is added, and `_event` checks exact
  schema equality. So "one bounded member" is a **wire and type change**, not a
  compatible seam.

**Selected: one new optional document, `activity.json`, carrying its own schema
`baton.worker-exchange.activity/1`**, written into the existing manager-owned
event mount. Lifecycle documents are untouched, so their meaning and their
causal and hostile-input tests stand unchanged.

- **Members:** schema, session, attempt_id, the operation and operation_id it is
  bound to, and a single non-negative integer `bytes_observed`.
- **Its own parser**, validating the integer in that parser alone. **No existing
  event parser is relaxed.**
- **Namespace:** the document name is added to the closed `EVENT_DOCUMENTS`
  vocabulary so a foreign entry in the mount stays foreign and is not read.

### Compatibility, both directions, stated rather than assumed

| Pairing | Behaviour |
| --- | --- |
| **old manager, new worker** | The extra file is outside the old closed vocabulary and is ignored; lifecycle documents are byte-unchanged, so the old manager behaves exactly as before. |
| **new manager, old worker** | No `activity.json` is ever written; absence means **unknown**, which is the same answer a never-observed attempt already gets. |
| **retained old state documents after a manager restart** | Unaffected — nothing was added to `state/1`. |

**A new file fitting an existing mount is not backward compatibility**, which is
why each pairing is named.

## 3. Consumer — the ordinary serving path, named explicitly

The ordinary file-exchange consumer is **`single_worker.observed_exchange`**
(`tools/single_worker.py:1660`), supplied as `observe_exchange` to the Job
composition (`:2540`). My earlier path list omitted it; that was the gap.

**Two distinct hooks, deliberately separated:**

- **Read-only projection.** `observed_exchange` may *read* the activity
  document and surface the count. **It gains no writes.** A status read that
  acquired a side effect would be the defect this Work is trying to remove.
- **Serving-loop ingestion.** A separate hook on the sweep calls
  `observe_activity`. It is the only writer, and it is on the path that already
  expects to write.

`dogfood_operator._Channel` stops calling the observer entirely; its outer
stderr is not an activity source.

## 4. Bounded publication, stop and teardown

The review is right that a background thread proves only that the drain does not
call the publisher. Ownership, stated per side:

**In the container.** One publisher, started with the operation and owned by it.

- **Single-slot coalescing:** one integer slot, last value wins. No queue, no
  per-tick publisher, no per-attempt thread accumulation.
- **Cadence:** at most one write a second.
- **Stop:** the operation sets a stop flag and waits a **finite** bound. If the
  writer has not finished, it is **abandoned without joining** — and this is
  safe only because of the binding below.
- **A delayed write cannot freshen a replacement.** Every document carries the
  `attempt_id` and `operation_id` it was produced for; a consumer that reads one
  bound to an attempt other than the one it is observing **discards it**. A late
  write from a dead turn therefore cannot move a successor's instant.
- **Staging files:** `_publish` stages then replaces. Stale staging files from
  an abandoned writer are bounded by the single-slot rule — at most one
  outstanding — and the delivery teardown removes the event root wholesale.
- **A lost final count is acceptable** and is reported as last observed. The
  publisher must never gate mandatory reads, provider completion or runtime
  cleanup.

**On the manager.** The serving-loop ingestion reads the file and calls
`observe_activity`. A slow store delays that sweep step only — it is not on the
stderr drain and not on a mandatory read.

## 5. Freshness, unchanged from the prior design

`observe_activity` stays as it is: it refuses a regression, ignores a repeat,
and keeps the column pair consistent. The caller publishes **only a positive
total**, so a stream that produced nothing leaves the projection absent.

The two existing assertions already ruled superseded still change —
`test_every_byte_is_counted_including_the_ones_discarded` and
`test_a_silent_worker_is_observed_as_silent_and_not_as_unobserved`. **No causal
or credential-exclusion assertion is weakened.**

## 6. Path ownership

**Source:**

| Path | Change |
| --- | --- |
| `v12/worker/claude_agent.py` | identify the native session file; observe its size |
| `v12/worker/baton_worker.py` | own the publisher's start, coalescing slot, cadence, stop and finite shutdown |
| `v12/python/src/baton_v12/worker_manager/exchange.py` | the new document, its own parser, its entry in the closed vocabulary |
| `v12/python/tools/single_worker.py` | read-only projection **and** the separate serving-loop ingestion hook |
| `v12/python/tools/dogfood_operator.py` | `_Channel` stops being the activity source |

`worker_manager/attempts.py` stays unchanged. Any further lifecycle hook that
turns out to be needed must be enumerated before implementation, not discovered
inside it.

**Tests:** `tests/manager/test_claude_agent.py`, `tests/manager/test_exchange.py`,
`tests/tools/test_single_worker.py`, `tests/tools/test_dogfood_operator.py`; and
`tests/job_manager/test_exchange.py` or `tests/manager/test_attempts.py` only
where composition or owner behaviour actually changes.

## 7. Acceptance

The minimum subset, unchanged, plus what the review added:

1. A deterministic provider at the **normal adapter boundary** grows the
   selected native source, and public activity changes **before completion**.
   **Labelled simulated-provider coverage** — it is not live-provider evidence.
2. Unrelated stderr and a zero-byte EOF create no activity; repeated totals do
   not move the receipt time; never-observed stays unknown; reopen preserves
   last-observed partial state.
3. **Exact binding and hostile counts** — a document bound to another attempt or
   operation is discarded; a negative, non-integer or absurd count is refused by
   the new parser.
4. **Old/new compatibility**, both pairings from §2.
5. **Final/fault versus delayed publisher** — a late write cannot overwrite a
   terminal or freshen a replacement.
6. **Blocked store and blocked worker publication**, with output **larger than
   pipe capacity**, proving bounded completion and cleanup — not an exception
   and not a tiny payload.
7. **Restored, replaced or missing native files fabricate no growth.**

**A counter is not proof of useful work**, and nothing here claims otherwise.

## 8. Still open for implementation selection

- **The session-file binding** (§1). This is the one genuinely unresolved fact;
  everything else above is decided. It should be settled from source and
  retained evidence if possible, and only escalated as a narrow
  provider-specific question if it cannot be.
- Follow, sink expansion, colour, pause, search/filter, retention and raw
  stream UX remain W39649/v13 material, not W61599 gates.
