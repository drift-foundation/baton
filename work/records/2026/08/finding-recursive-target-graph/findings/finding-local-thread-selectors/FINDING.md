# Visible local Thread identifiers are not accepted by commands

## 2026-08-17 — observed during the projection-6.1 cutover trial

**Observed.** The fresh authority displayed the born discussion as `T2` in
the v11 TUI. Entering the command shown below from that same TUI refused it
with `No thread 'T2'`:

```text
say thread=T2 body="v11 cutover test: acknowledge through v11" request=baton.feat on=W2
```

The canonical Thread id is `92c57e47-T2`; using it is a possible short-term
workaround, but the human cannot construct that value from the displayed
local id alone.

**Confirmed boundary.** Authority-local `Wn` selectors are deliberately
supported for every Work-valued operand. The existing selector contract does
not cover Thread-valued operands even though the TUI presents Threads with
the analogous `Tn` label. This is therefore not a failure of the Work
selector implementation; it is a missing Thread-selector contract exposed by
the live messaging trial.

**Product defect.** A stable identifier presented as the way to distinguish a
Thread must be accepted wherever a command asks for that Thread, or the TUI
must expose a usable accepted identifier. Requiring an undisplayed canonical
authority prefix makes the command surface non-self-contained.

**Proposed correction.** Add one strict authority-local Thread resolver. Every
Thread-valued operand accepts either the canonical
`<authority>-T<positive-sequence>` identity or exact local
`T<positive-sequence>` spelling. Missing, malformed, and foreign selectors
must fail closed by name. Resolution occurs before operation fingerprinting,
so canonical and local spellings are the same operation identity. JSON keeps
canonical identity and exposes the local spelling explicitly; no title or
cursor inference is allowed.

## Acceptance boundary

- The live refused command succeeds with `thread=T2` in its owning authority.
- `say`, `thread`, `label`, `unlabel`, and `mark-seen` share the resolver; any
  other Thread-valued input discovered in the grammar is included.
- Canonical and local spellings have parity, including effectively-once
  retries.
- Malformed, missing, and foreign selectors refuse without mutation.
- TUI assistance and examples use a spelling the public command accepts.
- CLI/JSON and packaged-TUI regressions cover the observed cutover path.

## 2026-08-17 — implementation-start revalidation

**Confirmed.** `src/baton_work/cli.py` has one central
`_resolve_work_operands` pass backed by
`transitions.resolve_work_selector`, but no corresponding Thread pass or
resolver. The current public grammar has exactly five Thread-valued operands:
`say thread=`, `thread thread=`, `label thread=`, `unlabel thread=`, and
`mark-seen thread=`. They reach projections/transitions with the raw spelling;
the resulting exact lookup produces the observed `No thread 'T2'` refusal.

The proposed boundary remains current: introduce one strict resolver and one
central pre-dispatch operand pass for those five verbs. Do not broaden this
into fuzzy identifiers, title lookup, cursor inference, or a database-schema
change.

## 2026-08-17 — pinned resolver contract (pre-implementation)

**Confirmed and pinned.** The resolver is `T<positive-sequence>` against the
opened authority — exactly the Work discipline: local qualifies with the
authority prefix, canonical must already carry it (foreign refuses by name),
anything else refuses naming both accepted spellings. Resolution happens in
the ONE central pre-dispatch operand pass in `cli.py`, before the transitions
compute the WS-5 operation fingerprint, so both spellings are one operation
identity; the TUI command bar reaches the same pass through `_cli.main`.

**Necessary supersession discovered during revalidation.** The TUI Threads
pane labelled rows `T{ordinal}` — the thread's LABEL-ORDER position within
the selected Work (an R63 pagination fact), not its identity. The two
numberings coincide on simple histories and silently diverge once label
order differs from creation order, which would present a `T<n>` the resolver
maps to a DIFFERENT thread. Superseded: the pane label renders the
authority-local selector (the canonical id's own sequence, now projected as
`local_id` at 6.2); `ordinal` stays in the work-threads projection unchanged
for pagination. JSON exposure is additive — projection 6.2.
