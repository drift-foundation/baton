# Progress

## Step 0 — the ordering constraint is now authority state (2026-08-18)

W101 has been claimed and re-woken repeatedly without progress, because
its blocker lived only as prose: the FINDING's dated superseding note and
PLAN steps 3-5 marked "blocked on W102". Nothing in the authority
recorded it, so W101 kept projecting as ready, unclaimed work for
baton.impl and kept waking a handler who then could not act. That is the
stranded-claim failure mode the agent contract explicitly warns about.

Recorded `block work=W101 on=W102` (seq 249). W101 is now `ready: false`
with W102 as its open blocker, and the active claim released as a
consequence rather than by assertion. When W102 closes, W101 becomes
ready again and wakes its handler on a fresh assignment episode.

This changes no ruling. It makes the authority agree with the ruling the
reviewer already wrote.

## Revalidated blocker audit — 2026-08-18

The FINDING's release condition is that W102 "verified that every v10
consumer is gone". That predicate was never written down concretely.
Measured against the live system:

**Still live, and therefore still blocking (11 processes, uptime 13h45m):**

- 10 x `tools/codex-event-bridge/src/baton_source.mjs`, each invoked from
  the WORKING TREE and each pointed at the retired deployment:
  `--baton /home/sl/baton/app/baton-cli/v10/v10.2.0/bin/baton`
  `--config /home/sl/baton/mailbox/v10/baton.json`
- 1 x `tools/codex-event-bridge/src/main.mjs`

`baton_source.mjs` is itself on W101's removal list, so this is the exact
condition the boundary names: an active monitor importing a path queued
for removal. These serve the reviewing Codex session, so removing them
under W101 would cut the reviewer off mid-review.

**No live consumer at all - zero processes, zero open descriptors:**

`src/baton_core/`, `src/baton_tui/`, `compat/`, `tests/core/`,
`tests/tui/`, `tests/packaging/`, and the v10 build/deploy tools. (An
initial scan reported four matches; all four were the audit's own shell
and search processes, not consumers.)

### A split worth the reviewer's ruling, not mine

The FINDING's boundary is written per-path - "refuse removal while any
active ... path imports THEM" - and the superseding note is narrower than
the PLAN: it forbids removing or rewriting "those live paths". Read that
way, the Python v10 surface is removable now and only the Codex bridge
cleanup waits on W102.

PLAN step 3 nevertheless marks the whole step blocked, and it is the
reviewer's step. Splitting it is a scope decision with real cost: it
would leave a large, hard-to-review removal half-done in a tree another
participant is actively working in, for the sake of starting work that
W102's completion may unblock entirely within the same session. So the
split is RECOMMENDED here and left for the reviewer to rule on, rather
than taken unilaterally.

If the split is approved, the safe half is the whole Python surface plus
its Justfile recipes; the unsafe half is exactly the five Codex paths and
the stack-only config fields.

## Re-audit in the recreated authority — 2026-08-18

The trial authority was recreated for the W245 schema change, so the
W101/W102 edge recorded above no longer exists: this item is now W7 and
its gate is W6 (`Retire v10 deployments and mailbox data`, open and
active with baton.ops). W7 woke ready and unclaimed again — the same
stranded-handler shape the section above describes, reintroduced by the
recreation rather than by any ruling.

Recorded `block work=W7 on=W6` (seq 21) with the rationale carrying the
measurement below. W7 is unready again and the claim released as a
consequence.

**The refusal condition is not merely still true; the v10 runtime is in
active use.** Measured immediately before the edge:

- 10 x `tools/codex-event-bridge/src/baton_source.mjs` and 1 x
  `main.mjs`, from the WORKING TREE, uptime 17h12m;
- 1 x `tools/codex-event-bridge/src/stack.mjs` — also on the removal
  list — running against `/home/sl/baton/conf/codex-event-bridge.json`;
- 10 x the deployed v10 CLI,
  `/home/sl/baton/app/baton-cli/v10/v10.2.0/bin/baton`, against
  `/home/sl/baton/mailbox/v10/baton.json`, **started 21 seconds before
  this audit**.

That last group is the important one. Earlier audits found long-lived
leftovers, which could be read as processes nobody had gotten around to
stopping. A v10 stack restarted seconds ago is a live dependency: the
cutover W6 owns has not happened, and removing these paths now would cut
a running participant off mid-session.

The Python v10 surface (`src/baton_core/`, `src/baton_tui/`, `compat/`,
`tests/core/`, `tests/tui/`, `tests/packaging/`, the v10 build tools)
still has no live consumer. The recommended safe/unsafe split from the
earlier audit therefore stands unchanged and still awaits a ruling; it
is recorded above rather than acted on.

## Third re-audit, third recreated authority — 2026-08-18

The authority was recreated again for the W38 schema-19 cutover, so the
dependency edge recorded in the previous instance is gone with it. This
item is now W4 and its gate is W3 (`Retire v10 deployments and mailbox
data`, open and queued with baton.ops).

Measured immediately before recording the edge:

- 1 x `tools/codex-event-bridge/src/stack.mjs` — on the removal list —
  15h53m uptime, against `/home/sl/baton/conf/codex-event-bridge.json`;
- 10 x `tools/codex-event-bridge/src/baton_source.mjs` from the WORKING
  TREE, 15h51m uptime;
- 10 x the deployed v10 CLI at
  `/home/sl/baton/app/baton-cli/v10/v10.2.0/bin/baton` against
  `/home/sl/baton/mailbox/v10/baton.json`, **started 48 seconds before
  this audit**.

The handoff's condition — "after the deployment/data cutover proves no
live v10 consumer remains" — is not met, and the last group says why in
the strongest terms available: the v10 stack is not residue anybody
forgot to stop, it is being restarted.

Recorded `block work=W4 on=W3` (seq 10).

### An unplanned demonstration

Recording that edge on Work I had just claimed released the handler and
moved the row to `waiting` — which is W38's own late-gate correction,
running against live coordination data for the first time. Under the
previous authority this same sequence would have left the row `active`
with nobody executing it: exactly the contradiction W38 R1 closed, and
exactly the shape of the original observation that produced the finding.

### Standing recommendation, unchanged

The Python v10 surface still has no live consumer. The recommended
split — remove that half now, hold the five Codex bridge paths until the
cutover — has been recorded through three authority generations without
a ruling. It is worth one either way, because it is the difference
between this item moving and it being re-audited a fourth time.

## Executed — 2026-08-18

W3 closed satisfying, and the ruling at seq 13 was explicit: do not
split, execute the complete pinned contract. Both conditions the
finding names are now met, and I verified the second one myself rather
than taking the close rationale on faith:

- no `baton_source.mjs`, no `stack.mjs`, no v10 CLI, no v10 mailbox
  process anywhere;
- `/home/sl/baton` is gone entirely;
- the only surviving bridge processes are the RETAINED v11 entry points
  — `bin/codex-event-bridge` and `bin/codex-baton-bridge`, the latter
  pointed at the v11 release and the v11 config.

That is the first time in four audits the refusal condition has cleared.

### Removed

The Python surface (`src/baton_core`, `src/baton_tui`, `compat`), its
suites (`tests/core`, `tests/tui`, `tests/packaging`, `tests/candidate.py`),
the seven v10 build/deploy/guide tools, the tracked artifacts (`dist`,
`schema/`, `examples/baton.json`), and the v10 Codex monitor stack —
`baton_source.mjs`, `stack.mjs`, both bins, and their two focused test
files. 64 paths.

The Justfile lost `codex-baton`, `test`, `build`, `deploy`, the
alias/resolve pair, the three guide recipes, and both verify recipes.
`default` now names `test-v11`, because the recipe it used to name no
longer exists — leaving it would have made the bare `just` refuse.

### The surgical half

`config.mjs` lost exactly the stack-only fields: the `baton` block
(binary/config/waitTimeoutSeconds/retryMs) and the per-target
`participant`, both consumed only by `stack.mjs`. The generic server,
target, socket and capacity configuration is untouched. Three bridge
tests covered those fields; they are replaced by one that asserts the
schema no longer validates them AND that the transport beside them still
does — dead schema that still validates is how a removed feature looks
alive.

`tests/conftest.py` keeps v11 discovery and serial-marker registration.
Its candidate-build warning is gone, because the thing it warned about
(`tests/candidate.py`, `just build`, `just test`) no longer exists.

### Acceptance

`tests/work/test_w4_v10_runtime_removed.py`, 38 checks. It pins both
directions — every removed path stays gone AND every retained path
survives, so the contract cannot be over-applied later by someone
reading only its first half. The import scan is structural (AST, not
grep), the Justfile scan protects the operator's entry surface, and the
distribution check runs against a freshly built artifact rather than the
checkout.

Break-sweeps: reviving `src/baton_core` reds the path check; adding a
recipe that names `build_zipapp` reds the Justfile check.

### Evidence

- Gate: **1142 passed** + 14 serial + acp 38/38 on 32 cores.
- Retained Codex bridge suite: 35/35.
- Fresh distribution: 14 members, `baton_work` present, no `baton_core`,
  no `baton_tui`, no retired bridge modules packaged.
- Surviving `baton_core`/`baton_tui` references are all in guards that
  FORBID them, or in historical records — never an executable path.
- Whitespace check clean.

## Review round 1 — the gap was in my own guard (2026-08-18)

Both findings are the same failure, and it is worth stating plainly: my
38-check regression read TRACKED paths. It passed with a mode-0755
protocol-10 zipapp sitting in `build/` — ignored, absent from the diff,
and runnable. "No executable fallback" is a property of the CHECKOUT,
not of the index, and I tested the index.

**The candidate.** `build/` held `bin/baton` and `bin/baton-tui` from
the 10.2.0 line; I confirmed `bin/baton` really did bundle `baton_core`
before removing anything. Twelve files, nothing referencing them, the
builder that made them already gone. Removed, with the `.gitignore`
rules that hid them — those rules described the removed builder, so
keeping them would quietly re-hide the next one.

**The guidance.** `test-v11`'s own comment told an operator that
"`just build` then `just test` remains the full candidate gate". Both
recipes are deleted by this change. That is current instruction sitting
in the one surviving gate, not history. It now describes the actual
boundary: the gate proves the source, `deploy-v11` produces the
artifact, and neither performs the other.

### The regressions

Four more checks, bounded as the review requires — they pin the RETIRED
shape and do not pre-judge a future v11 staging design:

- the retired candidate marker and its two binaries, by name;
- the general form, which is the one that would actually have caught
  this: any EXECUTABLE zipapp anywhere in the checkout that bundles
  `baton_core` or `baton_tui`, read from the archive rather than
  inferred from its path;
- the ignore file no longer hiding the retired candidate or its
  staging siblings;
- every `` `just X` `` the Justfile mentions must be a recipe it
  actually defines — so removed-command guidance cannot stay plausibly
  actionable while the implementation is absent.

Break-sweeps: staging a fake candidate zipapp reds two; adding a
`just build` reference to a comment reds the third.

### Evidence

- Gate: **1146 passed** + 14 serial + acp 38/38 on 32 cores.
- Retained Codex bridge suite: 35/35.
- `just --list` resolves; `default` runs `test-v11`.
- Whitespace check clean.
