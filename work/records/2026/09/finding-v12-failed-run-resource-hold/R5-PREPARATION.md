# R5 preparation — command and privilege inventory

**DRAFT — NOT EXECUTABLE.** W262061, baton.tuner claim262064,
2026-09-25 UTC. Preparation only; independent review then owner disposition.
Final R5 validation belongs to W257624 after independently accepted R4.
This document neither issues a grant nor selects recovery of a deployed run.
All command templates below retain deliberately unresolved bindings.

Authority: W262061/T262061 message262061 and this dossier's FINDING/PLAN
2026-09-25 parallel-preparation ruling and lightweight-Work clarification.
Read work-events through262064 and thread through262061, both complete.
Only this file is tuner-owned. Claude retains R3, product/test/PROGRESS;
shared FINDING/PLAN and historical evidence are unchanged.

## Evidence baseline and what still needs selection

Preserved parent DIAGNOSIS-252472.md and W257627 DIAGNOSIS.md/EVIDENCE.json
identify `/home/sl/baton-instances/two-jobs-251156` and these two attempts:

- `attempt-79177c237b58a5e1f3fa35a25cf684b3fd9ec91a7323a660795d68623ea971b5`
- `attempt-d514aa479c4d41c3c17ea5ebfab41d89b43c26eba948c87ec66ef850597461ec`

These are historical locators, **not current authority or verified execution
operands**. The reported outcome was held/interrupted with both outstanding
cleanup; describe answered and work faulted. W257627 reproduces the missing
proposal declaration before provider work. Neither diagnosis authorizes cleanup.
Do not equate historical runtime-quiescence observations with present helper
settlement or resource eligibility. LIVE-RUN-RESIDUE-260767.json's separate
nine roots/108 possible helper names remain a distinct unresolved residue
inventory, not targets added to these two attempts' recovery.

Latest available independent recovery review read here:
review-2026-09-24T23-35-12Z.md. R1/R2 accepted; R3 guard implementation/acceptance
and R4 are not established by that review. It calls out physical-resource aliases,
serialization against hold commits, and destination writes. Preparation does
not update that stage status from an author's changing source tree.

## Supported interface inventory

Source symbols below are the inventory baseline, not accepted R4 candidate
bytes. Revalidate every signature and packaged entrypoint against accepted R4.

| Surface | What it actually provides | Authority/effects and packet implication |
| --- | --- | --- |
| `tools.stack_command` → `manager`, `view`, `logs` | Installed `baton-v12-stack` dispatch | There is no `recover`, `grant`, or `clear-custody-hold` subcommand in this dispatcher. Do not invent one. |
| `tools.dogfood_operator.main`, launcher `_for_abandonment` | `--grants FILE --evidence FILE --abandon --abandon-reason TEXT` | Existing single-attempt recovery CLI. Opens ControlStore, compares fixed assignment, then constructs Authority session, engine adapter and cleanup capabilities. No credential-source operand. Compatibility with this pooled two-Job recovery and R4 bounds is **unproved**; not the selected final R5 command. |
| `tools.stage_execution` composed `abandon_attempt(attempt_id, reason, stage, seconds=None, reclaim=None)` | Routes by durable allocation to the worker that launched the attempt | Correct pooled composition boundary to evaluate in R4; typed stage must match allocation. It is a callable, not a shell command. Do not reconstruct an adapter from guessed participant/role. |
| `worker_manager.intake.abandon_attempt` | Records/replays declaration, fences exact generation and performs the abandonment ending | Requires exact fixed assignment/participant, appropriate adapter capabilities and retention policy. Runtime absent-before-attachment is a distinct recovery branch. Existing cancellation must replay its original fence identity. No result is accepted merely by abandonment. |
| `intake.discharge_abandoned_quiescence_gate` | Carries validated committed abandonment absence proof to Authority, journals discharge | Distinct from cleanup. Derives Work/generation/gate/runtime from evidence; operator must not type a gate or absence proof to bypass it. |
| `custody.clear_custody_hold(store, attempt_id, which, episode, observed, helper_identity, settlement)` | Public exact-episode reconciliation API | Mutates manager journal. Requires validated submission-bound settlement, not just prose or helper absence. No operator CLI found in the inspected command surfaces; a selected audited wrapper/binding remains missing. |
| `custody.custody_holds(store, assignment_id, which)` | Validates and reads hold/clearance history | Reader on an already opened store; does not open it, settle helpers, clear holds or prove cleanup. Include every affected physical resource and alias under accepted R3. |
| `intake.abandonment_cleanup_of` and `abandoned_gate_discharge_of` | Separate validated committed receipt readers | Read both; ordinary `cleanup_of` alone misses abandonment-family success. Wrong retention digest must not look like positive cleanup. |
| `Authority.open_readonly`, `ControlStore.open_readonly`, `JobStore.open_readonly` | Public read-only handles | Preferred basis for final authoritative preflight/readback; all supplied identities and handles must be bounded/closed. No direct SQLite. |
| `tools.job_manager ... status` | Job/control projection; optional observation-only factory | Current command uses ordinary writable openers, even though its projection is read-only. Not suitable for a strict no-store-write inspection grant without separate selection. It does not refresh runtime facts. |
| `baton-v12-stack view --status FILE`, `logs --logs ROOT --attempt ID ...` | File-only status presentation and retained stream capture state | Can inspect existing documents without opening a store. Stale/missing documents or absent logs do not establish cleanup. |
| parent `two_job_supervisor.main` | Submission plus serving/shutdown supervisor | Not a dedicated recovery-only CLI. Its parser requires submission, deployment and stores; source contains submission/serving effects. Do not rerun it against the preserved deployment as a recovery shortcut. R4 must select the final bounded composition. |

## Privileges and who supplies them

There are three different meanings of “grant”; none substitutes for another.

1. **Owner execution selection:** exact recovery targets, reason, boundaries,
   process identity, allowed store changes, engine actions and unresolved-hold
   disposition. This preparation supplies none. Final packet validation may use
   disposable stores/fake engine only; actual preserved-run recovery is a
   separate selection after accepted R5.
2. **Authority bootstrap rights:** `Authority` is the trusted configuration face;
   `grant_capability(participant, capability, scope=...)` and `grants_of` are public
   APIs. Grant issuance belongs to the separately authorized deployment operator,
   not the recovery consumer. Scope omission defaults to deployment scope, so
   never omit it in a least-privilege grant recipe. Granting changes policy
   generation; capture post-issuance generation/provenance before consumption.
3. **Manager/OS capabilities:** store write rights and participant-bound session,
   exact allocation/attempt identity, engine socket access, custody capability,
   workspace/result and credential/launch-root access, evidence output directory.
   An editable JSON file does not supply any of these rights.

Authority's enumerated capability names are `verify`, `review`, `approve`,
`integrate`, `close`, `manage-work-labels`. There is no named `cleanup` or
`recover` capability to mint. Assignment-owned cancellation is checked against
exact assignment and the session's participant. The manager discharge path
requires its `satisfy_gate` port and validated proof. Recovery should not acquire
approve/review/integrate/close merely because those names are available.
If accepted R4 needs additional authority, name the actual supported operation
and its narrow scope; do not invent a capability or self-grant broadly.

The dogfood `--grants` document is a closed **operator decision file**, not an
Authority capability grant. `read_grants` rejects extra/missing members and
secrets. Current required members are:

```text
engine attempt_id offer_id source task_path storage launch_home control_store
 authority_store incarnation credential_home credential_slots credential_profile
 image_digest network review_route retention_disposition work_ref participant
 generation now policies record_binding assignment_contract human_contract
 role_instructions_digest runtime_profile_digest toolchain_digest adapter_digest
 adapter_name labels retention_policy_digest
```

Derive any future file through accepted public readback/composition, compare to
fixed assignment before constructing outward capabilities, and retain a hash.
No bearer, credential contents, copied private registry or made-up receipt.
Recovery tears down authorized credential material without requiring a fresh
provider login. Custody may run its bounded privileged helper; “no worker/provider
launch” must not be misreported as “no engine effect.” The engine socket's broad
OS power makes exact helper/image/mount/program/token constraints material.

## Draft command shapes — NOT EXECUTABLE

All `REVIEWED_*`, `VERIFIED_*`, `OWNER_*` and `NEW_*` variables below are unset
placeholders. No environment bindings were prepared. Do not replace them by
current checkout paths or historical IDs until final verification. A fresh
recovery record/incarnation does **not** mean a new identity for an already
committed destructive intent: preserve replay identities and submission tokens.

Existing single-attempt CLI syntax, for compatibility testing only after R4
selects it or explicitly rejects it in favor of a supported pooled wrapper:

```sh
"${REVIEWED_PYTHON:?unbound}" -B -m tools.dogfood_operator \
  --grants "${VERIFIED_ATTEMPT_GRANTS_JSON:?unbound}" \
  --evidence "${NEW_RECOVERY_EVIDENCE_JSON:?unbound}" \
  --abandon --abandon-reason "${OWNER_ABANDON_REASON:?unbound}"
```

The selected source/module import path, dependencies and executed caches must
also be bound. `-B` prevents cache writes, not stale pyc loads. The CLI presently
has no overall recovery-time operand; wrapping it in `timeout` cannot prove
remote settlement. R4 must resolve a decreasing budget including engine calls,
store contention and receipt readback before this can become a final recipe.
Do not use `--retry-handoff` for these receiptless faults or
`--finalize-quiescent` as cleanup; the latter explicitly performs no cleanup.

Grant issuance **API shape**, not an executable shell command or a request for
these attempts to receive a grant:

```python
# On a separately authorized bootstrap handle, only if R4 identifies a need:
bootstrap.grant_capability(verified_participant, selected_supported_capability,
                           scope=verified_scope)
issued = bootstrap.grants_of(verified_participant)
generation = bootstrap.policy_generation()
```

Missing command binding is explicit: no supported grant-issuance CLI was found
in `stack_command`; no audited standalone issuer script is supplied here. The
final packet must name the operator's selected bootstrap interface and verify
principal, Authority UUID, exact scope, provenance and generation separately
from the consuming recovery process. If no new capability is needed, record
that outcome instead of issuing an unnecessary grant.

Hold reconciliation **API shape**, likewise not an executable operator command:

```python
clear_custody_hold(control, attempt_id=verified_attempt, which=verified_root_kind,
                   episode=verified_episode, observed=operator_observation,
                   helper_identity=verified_helper, settlement=verified_settlement)
```

`verified_settlement` must originate in actual supported engine/provider
settlement evidence and match the committed submission token, image, helper,
root and episode. Do not fabricate it from `docker ps`, process exit, elapsed
time or a typed “gone” string. An exact CLI/wrapper and evidence acquisition
path are missing R4/R5 inputs. Reconciliation of one episode permits rechecking
that resource; it is not proof the whole attempt is cleaned or discharged.

File-only presentation shapes after a separately authorized reader produces a
fresh status document:

```sh
"${REVIEWED_STACK_BIN:?unbound}" view --status "${VERIFIED_STATUS_JSON:?unbound}" --ticks 1
"${REVIEWED_STACK_BIN:?unbound}" logs --logs "${VERIFIED_LOG_ROOT:?unbound}" \
  --attempt "${VERIFIED_ATTEMPT_ID:?unbound}" locators
"${REVIEWED_STACK_BIN:?unbound}" logs --logs "${VERIFIED_LOG_ROOT:?unbound}" \
  --attempt "${VERIFIED_ATTEMPT_ID:?unbound}" read --stream worker.stderr --from-byte 0 --limit 65536
```

Repeat each log command for each independently verified attempt as necessary;
select `provider.stderr` separately if relevant. Preserve capture state alongside
bytes. No follow loop is needed for this bounded readback.

Authoritative receipt readback **API shape**, for a selected wrapper using a
public read-only ControlStore handle (not the writable `manager status` opener):

```python
with ControlStore.open_readonly(verified_control_path,
                                incarnation=selected_reader_incarnation,
                                clock=selected_clock) as control:
    cleanup = abandonment_cleanup_of(control, attempt_id=verified_attempt,
                                      retention_policy_digest=verified_policy)
    discharge = abandoned_gate_discharge_of(control, verified_attempt)
    holds = {kind: custody_holds(control, verified_attempt, kind)
             for kind in ("workspace", "result")}
```

The public functions are from `baton_v12.worker_manager.intake` and
`baton_v12.worker_manager.custody`; `ControlStore` is exported by
`baton_v12.worker_manager`. Missing receipts/reader refusals remain unresolved.
A final reader must also compare Authority gate/assignment and accepted R3's
physical-resource mapping; these three reads alone are not the whole acceptance.
No standalone readback wrapper has been authored or run in this preparation.

## Missing R4 inputs and final packet acceptance checklist

Before writing final RECOVERY.md/GRANTS.md and validating test_recovery_packet.py:

- Obtain independently accepted R3/R4 source, test and review digests; select the
  installed executable/module snapshot and prove actual import/cache origins.
  Resolve exact bounded recovery-only entrypoint, halt-admission behavior,
  existing-cancellation/launch-absent branches, overall allowance and honest I/O
  limitations. A source function existing is not command validation.
- Through selected public read-only handles, bind Authority UUID, Job/control
  store identity, original assignment/generation/principal, offer/allocation,
  attempt/runtime, deployment/image/adapter, retention policy, credential/launch
  roots and physical workspace/result device/inode relationships. Revalidate
  both historical IDs; refuse stale/wrong bindings before destructive effects.
- Enumerate every standing hold: root kind/canonical resource, aliases, episode,
  helper, submission token, settlement and clearance provenance. Preserve legacy
  or ambiguous evidence as held. Do not silently widen targets to the separate
  unselected-live-test residue. Select its operational disposition independently.
- Separate bootstrap issuer from consumer. Demonstrate missing/wrong rights,
  wrong principal/scope/Authority/generation/retention/image and forged JSON
  decisions refuse before engine or resource effects. Retain grants readback and
  policy-generation evidence; broad grants are not a substitute for this test.
- In authorized disposable stores and fake engine at its normal port, exercise
  the **literal final argv** and installed source path, not just a hand-built API
  equivalent. Cover two attempts, exact allocation routing, existing cancellation,
  launch-absent recovery, first-call crash, lost receipt, reopen/replay, concurrent
  hold/reuse and aliases, wrong or stale settlement token, store contention,
  interrupted/expired allowance and uncertain engine answer. Count effects and
  preserve root bytes on all refusals; prove no duplicate submission/reclamation.
- Check committed abandonment cleanup **and** committed gate discharge with the
  public family-specific readers. Check holds/resources after each operation,
  retained outputs' custody/retention and no unauthorized intake/publication.
  Replayed receipt must not permit another effect. A cleared hold alone, empty
  ordinary cleanup journal, absent log or exit0 does not establish recovery.
- Verify separate positive-cleanup and held/unresolved results and exit behavior,
  durable outcome on partial failure, exact unresolved-resource inventory and
  bounded readback. Record measured durations and unproved filesystem ceilings;
  never report `timeout` as proof that remote operations stopped.
- Preserve the original deployment/evidence; prove fixture isolation and fake
  provider/engine use before running the final tests. Record cleanup of fixture
  resources only. Final R5 command planned in PLAN.md is a 60s timeout plus5s
  termination grace for `python -B -W error::ResourceWarning -m unittest
  test_recovery_packet`; this preparation creates no module and runs no tests.

Final R5 acceptance stays in W257624, then separately select actual recovery.
A held/unresolved result preserves safety but does not clear adoption. W257627's
fresh packet and W247941's two-Job proof remain downstream of their recorded
prerequisites; this draft accepts neither.

## Preparation verification record

Source/dossier inspection only. No deployed-store or deployment-file access,
engine/provider invocation, test execution, grant issuance, cleanup, recovery,
product/test edit, Git mutation or writes outside this file. Initial searches
for guessed optional filenames returned no match; required handoff/decision
files were readable. The missing executable grant/hold-reconciliation bindings
above are operational findings for final packet preparation, not permission to
substitute raw SQL or an ad-hoc destructive script. Current source can change
under Claude's active claim; this draft's inventories must be rebound after R4.
