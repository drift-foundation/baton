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
