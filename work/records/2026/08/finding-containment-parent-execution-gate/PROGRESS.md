# Progress

## 2026-08-21 — implemented, one boundary departure for review

**State: awaiting review.** The pinned boundary was revalidated against the
current tree before acting. It held everywhere except the schema question
below, which is the one thing I need a reviewer decision on.

### Implementation

`src/baton_work/transitions.py`

- `_open_gates` is renamed `_open_dependency_gates` and counts only open
  explicit blockers. The rename is deliberate: the meaning changed, and a
  reader who trusts the old name is exactly the failure mode. Five call sites
  (`_unclaimed_state`, the wake sweep's two, `claim_work`, `set_phase
  wait=gates`) keep their semantics intact once the helper means what its name
  says.
- `_displayed_gate` no longer searches open children, so the `UNION` collapses
  to the blocker query alone.
- `_recompute_ready` drops `open_children` from the conjunction and reuses the
  helper for the blocker half.
- Both child-creation paths (`create_work` and `accept create=true`) no longer
  recompute the parent, and `close_work` no longer recomputes the parent of a
  closing child. The `FINDING.md` boundary allowed a harmless retained
  recomputation; I removed all three instead, so "a child never moves its
  parent" is structural rather than incidental. `close_work`'s in-lock read
  drops the now-unused `parent` column.
- Unchanged, as required: both open-child checks in `close_work`, the
  containment half of the `_would_cycle` union walk, the obligation gate path,
  and every dependency behavior.
- Refusal wording: `unmet dependency/child gate(s)` -> `unmet dependency
  gate(s)`; `no open required child or blocker` -> `no open blocker`.

`src/baton_work/authority.py` and `src/baton_work/projection.py`: the
`gate_kind` schema comment and the blocker-preference comment. The latter left
the containment question explicitly open ("an open acceptance question in
`FINDING.md`"); W1477 answers it.

`docs/EFFECTIVE-BATON.md`: the quoted refusal text, plus a paragraph under
"Containment versus dependency" making "a parent may proceed" exact. The
contract sentence itself was already correct — the code contradicted the
document, not the other way round — so the addition says what "may proceed"
means for readiness, phase, Handler and gate, which is precisely what was
loose enough for the code to drift.

### The one departure: this DOES need a schema rollover

`FINDING.md` records "No authority table or persisted field must change, so
this Work does **not** require a schema rollover." The shape reasoning is
correct and the conclusion does not follow, so I bumped `SCHEMA_VERSION` 26 ->
27 and am flagging it rather than quietly following or quietly ignoring the
pinned line.

`work.ready`, `work.phase` and the `gate_*` episode are persisted DERIVED
values, every one computed under the rule this Work replaces. An authority
written by a schema-26 build holds `ready=0` on every parent with an open
child, and nothing in the new code recomputes those rows — the child-driven
parent recomputation that would have healed them is exactly what W1477
removes.

Reproduced against a throwaway authority in `/tmp` (never the deployment), by
writing the row state a pre-change build leaves and running the new code:

```text
stale row:  ready=0 phase=block  gate_kind=work gate_work=<child>
offered by wait, before:   [child only — the parent is invisible]
after any transaction that sweeps: ready=0 phase=queued gate_kind=None
offered by wait, after:    [child only — still invisible]
claim by id:               SUCCEEDS
```

So the parent lands `queued` with `ready=0` — the self-contradiction
`_recompute_ready`'s own comments call out — claimable by whoever knows its
id and permanently absent from every readiness projection, because
`_first_actionable` and `_BLOCKING_PREDICATE` both filter on `ready=1`. The
global wake sweep moves the phase and does not touch `ready`.

This project has no migration mechanism by design ("Fresh-authority
evolution: no alias, no migration"), and the version guard exists so a build
never guesses across versions. A behavior change that invalidates persisted
derived state is a version change even when no column moves, so refusing the
old file is the fail-closed answer and matches every earlier schema cutover.

The cost is real and is the reviewer's call, not mine: a rollover means a
fresh authority, and the live ledger carrying this very Work does not survive
it. If the reviewer prefers to keep the ledger, the alternative is an
explicit one-off readiness backfill, which this codebase currently has no
place to put. Reversing the bump is a one-line change plus three test
constants.

### Tests

Rewritten where they encoded the superseded rule, never deleted:

- `test_transitions.py` — `test_children_gate_the_parent_level_triggered`
  becomes `test_children_do_not_gate_parent_execution`, plus
  `test_a_late_child_does_not_release_the_parent_claimant` (the W2/W1466
  incident) and `test_a_dependency_still_gates_a_parent_that_has_open_children`
  (composed case 4). `test_every_transition_is_one_audited_event` loses the
  fabricated `wake`. New:
  `test_wf09_a_child_created_between_close_pre_read_and_lock_refuses` — the
  in-lock recheck had no case of its own, and it is now the whole of
  containment's enforcement, so it earns a race regression.
- `test_w108_active_claim.py` — an open child is no longer a claim
  precondition; the dependency, parked and terminal preconditions are
  untouched.
- `test_w49_assignment_episodes.py` — only the dependency unblock mints; a
  child neither un-mints nor mints. This is also the `wait`-projection
  regression: the assertion is that the parent's action key is unchanged.
- `test_w78_typed_timed_gates.py` — the three child-gate cases become
  "an open child holds its parent back from nothing", "opening and closing
  children never moves the parent gate", and an oldest-open-blocker ordering
  case that also proves a child cannot inherit a cleared blocker's gate.
- `test_w71_navigation.py` — the mixed-tree proof parked the interloper
  because a root with open children could not be parked. It now parks the
  ROOT mid-read, which is the sharper proof and restores a phase assertion
  that actually discriminates pre- from post-commit.
- `test_wf06.py` — the release root is claimable while both legs are open;
  the dependency conjunction moves to the externally blocked child, where it
  always belonged.
- `test_soak.py` — the independent readiness re-derivation drops children,
  and a new invariant asserts no closed Work holds an open child. Worth adding
  precisely because enforcement narrowed to one refusal point.
- `test_authority.py`, `test_w92_schema15.py`, `test_w93_runtime_state.py` —
  schema constant.

`test_edges.py`, `test_parity.py`, `test_tui.py` and
`test_w47_event_phase_intervals.py` were named in the finding as likely to
encode the rule. They do not, and all pass unchanged.

### Verification

- `pytest -n $(nproc) -m "not serial" tests/work`: 2812 passed, 1 failed.
- `pytest -m serial tests/work`: 52 passed.
- `tools/acp-baton-bridge` npm test: 55 passed.

**The one failure is not this Work's.**
`test_w459_fresh_contexts.py::test_the_example_manifest_mints_a_context_per_codex_participant`
fails because `conf/infra.example.json` gained a `prompt` context at 08:19
today, from the concurrent uncommitted
`finding-interactive-prompt-participant` work. That test reads only that
manifest; nothing in this patch boundary touches it, and the same suite passed
green at 2813 before that edit landed. Left alone: it is another
participant's in-flight file.

Concurrent edits by that other participant also cover `AGENTS.md`, `conf/`,
`docs/BATON-SETUP.md`, `docs/CODEX-APP-SERVER-EVENT-CONNECTIVITY.md`,
`tools/codex-event-bridge/README.md` and `v12/README.md`. My files are
disjoint from all of them.
