# Activity document — completed design packet

Recorded 2026-09-15 by baton.claude, claim 174572, per owner selection M174565.
**Design only.** No product or test file edited, nothing executed. Completes
`ACTIVITY-SOURCE-DESIGN-174521.md` (which it supersedes; both remain as
history) against the owner's selected shape.

## 0. The selected shape, restated

One separate optional `activity.json`; **temp file then atomic rename over the
published file, never renaming the published file away first**; one publisher
with a bounded latest-count slot; exact **attempt / operation / sequence /
command** binding; missing activity preserves **unknown or last-observed**.

## 1. Native session-file identification — now derived, not open

The previous revision left this open. It is resolvable from source.

**`_scratch` is a per-container private directory:**
`tempfile.mkdtemp(prefix="dogfood-", dir=PRIVATE_ROOT)` with `PRIVATE_ROOT =
"/tmp"` — the tmpfs — cached on the agent instance
(`claude_agent.py:1490-1513`). **`_prepared_home` builds `$HOME` beneath it:**
`home = scratch/home`, `state = home/.claude` created `0o700`, containing
exactly one entry — the credential **symlink** `.credentials.json`
(`:1983-1990`, `PROVIDER_HOME_STATE`, `PROVIDER_CREDENTIAL`).

**So the private `.claude` starts empty of provider state and no other writer
owns it.** Anything the provider writes beneath it during a turn was written by
this container's own invocation. That is the identification, and it needs no
vendor path knowledge.

**Rules, all derived from the above:**

- **Discovery:** regular files matching `*.jsonl` beneath the private `.claude`
  directory. Bounded: fixed maximum depth and a fixed maximum number of entries
  examined; exceeding either leaves activity **unknown** rather than sampling.
- **Type and link:** regular files only, `O_NOFOLLOW`; the credential entry is
  a symlink **and** is `.credentials.json`, so it is excluded twice over. No
  credential file, and no other home growth, is ever counted.
- **Layout independence:** the vendor's directory layout beneath `.claude` is
  **not** hardcoded. I did not read a live provider home and will not invent
  `projects/<slug>/<id>.jsonl` as a contract.
- **Per-operation baseline, because the scratch is per-CONTAINER, not
  per-operation.** `_scratch` caches `self._home`, so a `describe` and a `work`
  in one container share it. At the start of each operation record the set of
  matching files and each one's size. Report **growth relative to that
  baseline** — sum over files of `max(0, current - baseline)`, with files
  appearing after the baseline counted in full. A file present at baseline
  contributes nothing for the bytes it already had.
- **Replacement, truncation, rotation:** a file that **shrinks** below its
  baseline, or whose inode changes, makes the source **ambiguous**. Ambiguity
  yields **unknown** for the rest of the operation; it never yields a smaller
  count and never restarts a total.
- **Restored history fabricates nothing**, because the baseline is taken inside
  the operation and only growth past it is reported.

**A missing or ambiguous source leaves activity unknown. That is not a provider
failure and must not be reported as one.**

## 2. The document

`activity.json`, schema `baton.worker-exchange.activity/1`, added to the closed
`EVENT_DOCUMENTS` vocabulary so a foreign entry stays foreign.

| Member | Meaning |
| --- | --- |
| `schema` | exactly `baton.worker-exchange.activity/1` |
| `session` | the exchange session |
| `attempt_id` | this attempt |
| `sequence_id` | this command's sequence, as `RECEIPT_MEMBERS`/`STATE_MEMBERS` carry it |
| `command_digest` | this command's digest, likewise |
| `operation` / `operation_id` | the operation this count belongs to |
| `bytes_observed` | non-negative integer, growth since this operation's baseline |

**Exact limits.** The document is bounded by the existing
`MAX_EXCHANGE_BYTES = 65536` and `MAX_EXCHANGE_VALUE = 4096` that already govern
this mount. `bytes_observed` is validated in **this document's own parser**: an
integer, `0 <= n <= 2**53 - 1`, rejecting `bool`, float, string and any value
outside that range. **No existing event parser is relaxed**, and the lifecycle
documents are byte-unchanged.

**Binding is what makes late writes safe.** A consumer reads the document only
if `attempt_id`, `session`, `sequence_id`, `command_digest`, `operation` and
`operation_id` all match the exchange it is observing. A document from a dead
turn or a superseded command **is discarded**, so it cannot freshen a
replacement.

## 3. Publication — write pattern, exactly as selected

    write  <event_root>/.activity.json.tmp     (fsync)
    rename <event_root>/.activity.json.tmp  ->  <event_root>/activity.json
    fsync  <event_root>

**The published file is never renamed away, never unlinked, and never truncated
in place.** A reader therefore sees either the previous complete document or the
next one — never absence caused by the publisher, and never a partial file. This
is the selected pattern and it differs from `_publish`'s staging only in that it
must not perform the remove-then-rename variant.

## 4. Publisher lifetime, and cleanup when publication stalls

**One publisher per operation**, started with it and owned by it.

- **Bounded latest-count slot:** a single integer plus its binding. Last value
  wins; no queue, no per-tick publisher, no per-attempt thread accumulation.
- **Cadence:** at most one write a second.
- **Stop:** the operation sets a stop flag and waits a **finite** bound.
- **When publication stalls** — a wedged fsync is the case that matters — the
  writer is **abandoned without joining**. That is safe because of §2's binding:
  anything it eventually writes names a command that is over, and every consumer
  discards it. **No daemon-thread claim substitutes for that**; the binding is
  the proof.
- **Stale temporary files:** exactly one `.activity.json.tmp` can be
  outstanding, because there is one publisher and one slot. The delivery
  teardown removes the event root wholesale, so a stalled writer's temp file
  cannot accumulate across attempts.
- **A lost final count is acceptable** and is reported as last observed. The
  publisher never gates mandatory reads, provider completion, the terminal
  document or runtime cleanup.

## 5. Manager ingestion — nonblocking, and separated from the projection

Two hooks, deliberately distinct:

- **Read-only projection.** `single_worker.observed_exchange`
  (`tools/single_worker.py:1660`, supplied as `observe_exchange` at `:2540`)
  may **read** the document and surface the count. **It gains no writes.**
- **Serving-loop ingestion.** A separate hook on the sweep calls
  `observe_activity`. It is the only writer and sits on the path that already
  writes.

**Nonblocking, concretely:** the ingestion hook does the file read and the store
write **inside the sweep step it already owns**, and a slow store delays that
step alone. It is not on the stderr drain, not on a mandatory read, and not on
provider completion. If the read finds no document, or one whose binding does
not match, the hook **does nothing** — preserving unknown or last-observed
rather than writing a zero. `dogfood_operator._Channel` stops calling the
observer entirely.

## 6. Old-reader compatibility, stated accurately

| Pairing | Behaviour |
| --- | --- |
| **old manager, new worker** | `activity.json` is outside the old closed `EVENT_DOCUMENTS` vocabulary, so the old manager does not read it. **But it is a real entry in a namespace the old manager counts**, so the implementation must confirm the existing entry-count limit still admits it, and say so with the measured limit — not assume invisibility. Lifecycle documents are byte-unchanged. |
| **new manager, old worker** | No document is ever written; absence means **unknown**, the same answer a never-observed attempt already gets. |
| **retained old state documents after a manager restart** | Unaffected; nothing was added to `state/1`. |

**A new file fitting an existing mount is not backward compatibility.** The
entry-count question above is the part that could actually bite, and it is named
rather than waved past.

## 7. Freshness

`observe_activity` unchanged — refuses a regression, ignores a repeat, keeps the
column pair consistent. The ingestion hook publishes **only a positive total**,
so a stream that produced nothing leaves the projection absent. The two
already-ruled assertions still change; **no causal or credential-exclusion
assertion is weakened.**

## 8. Path ownership

**Source:** `v12/worker/claude_agent.py` (session-file identification and
size observation), `v12/worker/baton_worker.py` (publisher lifetime, slot,
cadence, stop, write pattern), `v12/python/src/baton_v12/worker_manager/exchange.py`
(the document, its own parser, its vocabulary entry),
`v12/python/tools/single_worker.py` (read-only projection **and** the separate
ingestion hook), `v12/python/tools/dogfood_operator.py` (`_Channel` stops being
the source). `worker_manager/attempts.py` unchanged.

**Tests:** `tests/manager/test_claude_agent.py`, `tests/manager/test_exchange.py`,
`tests/tools/test_single_worker.py`, `tests/tools/test_dogfood_operator.py`; and
`tests/job_manager/test_exchange.py` or `tests/manager/test_attempts.py` only
where composition or owner behaviour actually changes.

## 9. Acceptance

1. A deterministic provider at the **normal adapter boundary** grows the
   selected native source and public activity changes **before completion** —
   **labelled simulated-provider coverage**, not live-provider evidence.
2. Unrelated stderr and a zero-byte EOF create no activity; repeated totals do
   not move the receipt time; never-observed stays unknown; reopen preserves
   last-observed partial state.
3. **Exact binding and hostile counts:** a document naming another attempt,
   session, sequence, command or operation is discarded; negative, boolean,
   float, oversized and non-integer counts are refused by the new parser.
4. **Both compatibility pairings**, including the entry-count check of §6.
5. **Final/fault versus delayed publisher:** a late write cannot overwrite a
   terminal or freshen a replacement.
6. **Blocked store and blocked worker publication**, with output **larger than
   pipe capacity**, proving bounded completion and cleanup — not an exception
   and not a tiny payload.
7. **Baseline, replacement, truncation and missing files fabricate no growth**,
   and a shrinking or replaced file yields unknown.
8. **The write pattern itself:** a reader concurrent with publication never
   observes absence or a partial document.

**A counter is not proof of useful work**, and nothing here claims otherwise.

## 10. What remains genuinely unknown

- **The vendor's layout beneath `.claude`.** §1 is deliberately
  layout-independent so the design does not depend on it; if implementation
  finds `*.jsonl` is the wrong shape for the supported profile, that is a narrow
  provider-specific question to raise then, not a gap in this packet.
- Follow, sink expansion, colour, pause, search/filter, retention and raw
  stream UX remain W39649/v13 material, not W61599 gates.
