# W161234 implementation-readiness pre-work

Advisory Work W173921, claim 173925, baton.claude via baton.impl.
**Read-only pass. Nothing was executed:** no test, probe, provider, model,
engine, image build, Git mutation or worker. No product, test or original
dossier file was edited. Everything here is advice for the future execution
owner of W161234 and requires revalidation before use.

Source of record revalidated: `ADOPTION-AND-PROOF-161434.md` in
`baton:work/records/2026/09/finding-v12-correction-restart-proof/`.

## 1. Revalidation of the pinned baseline — 8 of 10 hashes still hold

`ADOPTION-AND-PROOF-161434.md` pins ten file hashes. Re-measured now:

| File | Pinned hash still current |
| --- | --- |
| `tools/single_worker.py` | **same** |
| `src/baton_v12/worker_manager/sessions.py` | **same** |
| `src/baton_v12/worker_manager/launch.py` | **same** |
| `src/baton_v12/worker_manager/schema.py` | **same** |
| `v12/worker/claude_agent.py` | **same** |
| `v12/worker/baton_worker.py` | **same** |
| `tests/tools/scheduler_trace.py` | **same** |
| `tests/tools/test_scheduler_trace.py` | **same** |
| `src/baton_v12/worker_manager/oci.py` | **DRIFTED** -> `b842e605671b222d…` |
| `tools/stage_execution.py` | **DRIFTED** -> `abf0bb2d89aee039…` |

**The `oci.py` drift does not disturb the packet's claim about it.** The whole
diff is `+7` lines adding `OciAdapter.destroy_deadline`, a deadline-authorized
removal. `ROOT_NAMES`, `POSTURES` and the two-generic-root rule the packet
relies on are untouched, so row "oci.py mount and delivery owners" still stands:
a private context root remains an explicit mount/custody extension, not an
existing capability.

**The `stage_execution.py` drift is large and is the one to re-read.** That file
is under continuous change by W161230's children (W170380/W170382 accepted or
in flight, W170385 active under baton.tuner). Any claim the packet makes about
it should be re-derived rather than trusted.

## 2. Implementation-readiness map

### Missing — nothing from slices A, B or C exists

All seven proposed new paths are **absent** from the tree:

    src/baton_v12/worker_manager/provider_context.py      absent
    src/baton_v12/worker_manager/context_delivery.py      absent
    tests/manager/test_provider_context.py                absent
    tests/manager/test_provider_context_delivery.py       absent
    tests/manager/test_claude_context.py                  absent
    tests/tools/correction_restart_trace.py               absent
    tests/tools/test_correction_restart.py                absent

So W161234 is **entirely unstarted at the implementation level**. The packet is
a plan, and no part of it has been quietly overtaken.

### Implemented and still true — the assumptions the plan rests on

Each of these is the packet's premise, re-confirmed now:

| Premise | Current fact |
| --- | --- |
| Launch versions are 1/2/3, so a closed v4 is free | `launch.py` carries exactly `baton.worker-launch/1`, `/2`, `/3` |
| ControlStore schema is at 18; v19 is the next additive migration | `worker_manager/schema.py:117` `SCHEMA_VERSION = 18` |
| The provider argv has no continuity flag | `claude_agent.py:195` `PROVIDER_ARGUMENTS = ("--print", "--dangerously-skip-permissions", "--output-format", "json")` — no `--resume`, no `--session-id` |
| The three session owners exist and are unchanged | `sessions.py:304 open_agent_session`, `:450 adopt_provider_session`, `:619 handle_transport_loss` |
| Generic execution roots are two, not three | `oci.py:220-223`, W15232's closed set |

**Consequence worth stating plainly:** every one of the packet's "this does not
exist yet" claims is still accurate. The design work was not invalidated by six
weeks of adjacent change — only `stage_execution.py` moved under it.

### Superseded — historical wording that should not be carried forward

1. **The A/B/C cumulative cap table is superseded.** The packet proposes
   author/reviewer caps (120s/30s, 300s/75s, 420s/105s) and a "persist each
   pre-command cap … refuse if expected+margin cannot fit" protocol. `AGENTS.md`
   line 95 records the owner ruling of 2026-09-14: *cumulative stopwatch budgets
   are not approval*, superseding earlier cumulative gates, and work is not
   refused because an allowance is exhausted or historically unknown. **Proposed
   correction:** keep the numbers as *expectations for sizing focused runs*,
   delete the refusal protocol, and record measured durations honestly instead.
   This is a wording correction for the future owner to make in its own dossier;
   I did not edit the original.
2. **The packet's "W161234 measured verification starts and remains 0" framing**
   is fine as a fact but should not be read as a budget to be defended.
3. **`RELEASE-CHECKLIST-167877.md` row for W63255 is superseded by M167954.**
   The checklist offers a conditional: *"Require correction before advertising
   it as supported recovery, or explicit positive release-surface exclusion
   evidence."* The owner decision of 2026-09-14T11:40:26Z in the
   `finding-v12-isolated-agent-workers` FINDING selected **keeping `--abandon`
   supported and implementing W63255's fence**, and says so explicitly:
   "This supersedes the conditional … choice above and in
   RELEASE-CHECKLIST-167877.md / RELEASE-GATE-COMMANDS-167877.md." **Proposed
   correction:** that checklist row should read as decided, not conditional.
   It is not W161234 work either way.

### Uncertain — I could not settle these read-only

- Whether the packet's `stage_execution.py` rows still describe the file (see §1).
- Whether the `ClaudeAgent.work` Git-line profile still uses the mounted durable
  private repository as candidate at `OUTPUT_ROOT` in exactly the way the packet
  describes; `claude_agent.py` is byte-identical, so the claim is *probably*
  intact, but the profile's callers live in the drifted file.
- The exact provider-state layout and credential-slot mapping. The packet itself
  defers this to design review, and nothing I read decides it.

## 3. The scheduling fact that dominates everything else

`ADOPTION-AND-PROOF-161434.md` closes with: *"record the mandatory W161230
dependency … When ready, revalidate its final interfaces, obtain focused
independent DESIGN review of this packet, and then owner exact-slice/budget
selection before implementation."*

**W161230 is `phase: block`, seq 170418, next `baton.ops`.** Its children are
still moving: W170380 closed satisfying, W170382 is iterating through
implementation review, W170385 is active under baton.tuner. So *"revalidate its
final interfaces"* is not yet possible — there are no final interfaces.

**Advice: do not open slice A on the assumption that B and C follow soon.**
Slice A (`provider_context.py`, schema/store/documents, its own tests) is the
only one whose paths do **not** overlap W161230's moving surface. Slices B and C
touch `stage_execution.py`, `single_worker.py`, `launch.py` and `oci.py`, which
is exactly the serialization the packet warns about. A is genuinely startable
after design review; B and C are not, and saying so early is cheaper than
discovering it mid-slice.

## 4. Small ordered implementation sequence

For the three required outcomes. Each step is meant to be separately reviewable
and to leave the tree honest if it stops there.

**Healthy context reuse**

1. `provider_context.py` + schema v19: the context row (Authority/Work/line/
   repository pin, participant/principal, role, provider/model, policy) and the
   per-attempt *use* row. Single active-or-recovery-required use; concurrent
   admission refuses. No delivery, no runtime claim.
2. Bind an admitted use to the actual claim, writer generation, attempt, input
   and profile digest — compare against **manager-held** facts, never values
   read back from a delivery.
3. `context_delivery.py` + a closed launch `/4` carrying context-use identity and
   open-versus-restore mode. Old readers unchanged; a context-free legacy
   delivery keeps its old schema.
4. Worker side: validate the fixed private mount, then `--session-id` on first
   use or `--resume` on later healthy use, through `ClaudeAgent`'s existing run
   boundary. Read only the bounded conversation identity and terminal status.

**Useful code correction**

5. Reuse `test_scheduler_trace.py:test_a_correction_opens_a_second_episode_on_the_same_line`
   as the starting point — it already correlates a real changes-requested
   verdict, settled review and routed new attempt, and stops at revised-attempt
   preparation. Extend past that stop rather than rebuilding it.
6. Preserve `test_a_same_line_correction_keeps_its_worker_and_not_its_session`
   as **legacy-path evidence**. The packet is right that its universal
   impossibility claim is too broad; it should not be deleted to make room for
   the new contract, and it should not be cited as the new contract either.

**Counted durable restart without duplicate execution**

7. Count at two independent seams, as the packet specifies: the `ClaudeAgent`
   run seam (admitted use, command identity, prompt digest, open/resume mode,
   conversation identity, result) and the fake engine seam (launch inputs by
   attempt/operation). Require a positive baseline count **before** reopen.
8. Persist use intent before delivery/start, invocation/result identity before
   scheduling a successor, custody ending before reuse.

**The boundaries to hold while doing all of it** — all three are in the packet
and all three are the kind of thing that erodes quietly:

- Private state and credentials never become retained context content, never
  reach ordinary result artifacts or public traces, and runtime credentials stay
  freshly delivered through the existing credential owner.
- Restoration happens **after confirmed shutdown**. This is restored
  conversation, not live-process detach; W105982's closure explicitly does not
  adopt production detach.
- `handle_transport_loss`'s `resume=false/reprompt=false` rule is preserved. A
  healthy completed correction and a replayed uncertain turn are different
  things, and the second is not in scope.

## 5. Consumer reconciliation (M167954 and RELEASE-CHECKLIST-167877.md)

The checklist assigns W161234 nine consumer questions. **None of them should
become a prerequisite Work**; each is a bounded check against evidence that
already exists. My reading of what each actually asks for:

| Row | What W161234 owes | Reconciliation now |
| --- | --- | --- |
| W7 | check actual selected replay/context cases | Becomes a *case list* inside slice C, not separate work. Preserve older unmet evidence as unmet. |
| W44342 | compare ordinary start-intent/activation replay under W161230 | This is exactly the `request_runtime_start` journal-then-adapter boundary W170382 has been exercising. **Reuse that evidence**; open a bounded correction only if a duplicate-execution gap is demonstrated. |
| W61981 | verification command/input/environment identity vs current job limits | Overlaps W156162's limits evidence. Read, do not re-derive. |
| W62098 | import base/private-line/review checkpoint vs current managed candidate custody | W161230's accepted preparation custody evidence answers most of this. |
| W62535 | supported entry preflight/stranded-attempt using retained fixtures | Retained fixtures only; legacy operator ancestry is explicitly not a gate. |
| W110783 | compare checkpoint-fenced consumer with W124784 driver and W122060 consumer | Close/reclassify **only** with attributable supersession evidence; no new restart clone. |
| W114077/W114516 | compare affected ordinary retry/ending paths | No broad engine reproduction. Escalate only a demonstrated current release failure. |
| W144335 | sealed-intake re-entry reason preservation vs actual managed path | Shared with W167896; a surviving defect stays with its existing owner. |
| W144813 | first launch-refusal replay in the new managed path | Shared with W161230; the viewer displays the owner result and does not repair it. |

**The pattern across all nine:** W161234 is being asked to *check and report*,
with any surviving defect staying with its existing owner. Treating any of them
as blocking W161234's own slices would invert that.

## 6. Real design decisions still open

These are decisions, not tasks — someone has to choose:

1. **Provider-state layout and credential-slot mapping.** The packet defers it
   and nothing since decides it. This gates slice B's mount validation.
2. **Which profile is certified.** The packet proposes limiting first adoption
   to the existing private-line Git profile with stable in-container cwd. That
   choice should be recorded explicitly, because "certified for a different
   adapter" is called out as not a valid shortcut.
3. **Whether the context receipt is collected through ordinary declared output.**
   The packet requires mapping it without exporting private state; how is open.
4. **Schema 19 reservation.** The packet deliberately reserves no number. Someone
   must, and must confirm 18 is still current at that moment (it is, today).
5. **Whether "failed apply with a target publication" style manual-inspection
   outcomes need their own observable state** — the same shape of question I
   raised for W170385 — applies here to a held context with unknown turn state.

## 7. Suggested acceptance methods — proposed, not executed

Focused and deterministic only. **I did not run any of these.**

- Slice A: temporary-store owner/constraint/replay cases with no engine or
  provider process. Selector shape:
  `python3 -m unittest tests.manager.test_provider_context` from `v12/python`
  with `PYTHONPATH=src:tools:.`.
- Slice B: `tests.manager.test_provider_context_delivery` and
  `tests.manager.test_claude_context`, using the existing
  `test_stage_execution.py:turn`/`provider` subprocess seam rather than a
  synthetic session row.
- Slice C: the two scenarios, with both counters and their duplicate-injection
  negatives.
- **For every one of them, pair the positive with the reversal that would catch
  a vacuous case** — delete the guard or the counter and confirm the case fails.
  In W170382 I had three cases that passed their own reversals (two wrong-owner
  placements and one restart that was never taken); each looked like evidence
  and was not. The counters in slice C are exactly the shape that fails this way.
- Run experiments under the same supervision as final runs, with a per-run
  timeout, an own process group and TERM-then-KILL escalation, and record every
  run — including failures — rather than only the green one.

## 8. Assumptions and limits

- Everything above is a live-tree observation of 2026-09-15 under claim 173925
  and is provisional. Line numbers and hashes will move.
- I read `ADOPTION-AND-PROOF-161434.md`, the two checklist/decision documents,
  `AGENTS.md`, and the specific source symbols cited. I did **not** audit the
  predecessor evidence bundles (W103525 traces, W106673 review, the 18 exported
  schedules) — the packet already accepted them and re-auditing was not asked.
- I did not read or alter anything owned by W170385, whose tuner claim is live.
- No original dossier was mutated. The two superseded-wording items in §2 are
  proposals for their owners, not changes I made.
- This is advice. It is not acceptance of W161234, not a release gate, and not
  authority for any downstream implementation.
