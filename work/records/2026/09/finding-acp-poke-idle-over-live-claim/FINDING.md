# An ACP poke can publish idle over a surviving claim

Follow-up to:
`work/records/2026/08/finding-acp-turn-teardown-strands-live-worker/`

## Observed recurrence — 2026-09-04

W85500 remained active under `baton.claude`, assignment episode 85563, after
its delivered Work turn returned with implementation still unfinished. A later
poke, sequence 85773, reached the same ACP session. The agent re-read the
candidate, repaired displaced changes, removed one invalid cross-Work change,
ran focused tests, answered the poke as `working`, and named the remaining
work. The poke delivery then ended normally.

Canonical `detail work=W85500` still reports the live claim. Runtime state
instead reports `idle`, with no Work or action owner, and canonical `incidents`
reports zero open incidents. The ACP log ends the second turn with:

```text
acp process domain torn down after delivering poke:85773
v11 action delivered: poke:85773 -> baton.claude's configured session
```

The already-presented Work action key is not delivered again, so W85500 stays
claimed while no model turn is executing it.

## Confirmed defect

The correction owned by the earlier ACP teardown finding does not preserve its
claim-settlement invariant across a later non-Work delivery. A poke turn can
overwrite the required failed/stranded projection with `idle` while the same
participant still holds a canonical claim, and it can do so without producing
the required actionable incident.

The exact internal cause is not yet established. The evidence is consistent
with post-turn settlement being scoped to the delivered action rather than to
the participant's canonical claim slot, or with the poke completion path
publishing idle after settlement. That distinction must be verified in source
before implementation.

## Required correction

- Before ANY ACP turn publishes `idle`, reconcile the participant's canonical
  claim slot, independently of whether the delivered action was Work, a poke,
  an obligation, or another supported action.
- A surviving claim after the turn means no model is executing that claim.
  Preserve/publish the stranded failure state and one actionable incident;
  never publish idle merely because the non-Work action completed.
- Preserve the accepted distinction between an unspent failed Work wake and a
  returned/presented Work wake. This finding does not authorize an automatic
  replay, claim release, acceptance, or transfer.
- A later poke may deliberately resume the same claimed Work as an operator
  stopgap, but if that turn also ends without a terminal Work transition the
  claim remains stranded and the failure/incident invariant still applies.

## Immediate recovery boundary

Poking `baton.claude` to finish W85500 in one live turn is an explicit stopgap,
not the fix. That turn must either pass, block, or close the Work before ending.
If it cannot, preserve the candidate and use exact claimed-episode recovery;
do not infer completion from the existing edits or passing focused tests.

## Reviewer source and deployment revalidation — 2026-09-04

**Confirmed deployment fact:** The recurrence did not run the W55705
correction. The live `baton.claude` service is process 1169458 executing
`/home/sl/opt/baton/v11/8af006f/lib/acp-baton-bridge/src/acp_baton_bridge.mjs`.
That immutable release is Git commit
`8af006f733befbcea6147fb485892ab283fb7a4f`, dated 2026-08-29, while W55705's
settlement implementation landed later in commits
`b34b270b867926e54953aa9f7773e11346d510e5` and
`7f8051b22d104546649156b9b20902fd3f7a1ad2` on 2026-08-31/09-01. The installed
bridge has no `acp_settlement.mjs`, no `AcpSettlement`, and its returned-prompt
path calls `runtime.state("idle")` immediately after process-domain teardown.
Every immutable v11 release currently present below `/home/sl/opt/baton/v11/`
likewise lacks the settlement import.

**Confirmed deployment configuration fact:** The live rendered Claude ACP
configuration has no `runtime.actionOwner`, and canonical Teams at snapshot
85902 reported `action_owner: null`. The current source correction refuses
that configuration before runtime publication or the first wait. The live
service accepting it is independent confirmation that the old package, not
the reviewed W55705 source, produced the recurrence.

**Superseded diagnosis:** The earlier Confirmed defect section says W55705's
correction failed specifically on a later non-Work delivery. That remains an
accurate description of the RUNNING PRODUCT, but source inspection does not
support a new action-kind hole in the reviewed correction. Current
`runBridge` calls `AcpSettlement.settle(action)` after every returned or failed
ACP prompt without branching on Work versus poke. `classifySlot` deliberately
classifies a non-Work action beside a canonical claimed Work as `held`, which
publishes `failed`, persists the fence, files the incident, and returns
`stranded`; the caller therefore cannot reach its later `idle` publication.
The primary defect is release/cutover drift: production remained on a commit
that predates the accepted fix.

**Observed source-completeness gap:** Productionizing the existing correction
still requires a bounded repository change. `runBridge` now requires a
nonblank, non-self `runtime.actionOwner`, but the config loader still describes
that member as optional, the README's complete example omits it, all three
shipped ACP lifecycle templates omit it, and both co-deployed example configs
omit it. A release made from the present tree would therefore carry a bridge
that correctly refuses the deployment inputs shipped beside it. The active
rendered configuration demonstrates the same omission. This is not a reason
to weaken the W55705 startup refusal; the configuration/documentation surfaces
must catch up to the accepted incident-ownership contract.

**Observed regression gap:** The current 127-case ACP suite passes, including
the generic exact-Work surviving-claim case and neighboring-poke retention,
but it does not name the recurrence directly: a poke is the delivered action,
an independently read canonical slot still contains a claimed Work, and the
bridge must publish `failed` with that Work/episode, persist one `held` fence,
file one incident, never publish `idle`, and not replay or release the claim.
Add that integration-level case so later action-specific refactors cannot
mistake W55705's generic settlement call for a Work-only contract.

## Required correction after revalidation

1. Preserve W55705's current settlement state machine and add the exact
   poke-over-pre-existing-claim regression above. Do not add a poke-specific
   settlement implementation and do not release, accept, transfer, or replay
   the surviving Work.
2. Make `runtime.actionOwner`'s required, non-self contract visible at config
   validation and in the README, generic/Claude/Gemini lifecycle templates,
   and co-deployed examples. Baton-owned templates name the configured
   recovery participant explicitly; generic examples use an explicit
   `TEAM.MEMBER` placeholder. No owner is inferred from the runner, Route,
   role, session, or telemetry.
3. Build and independently verify a NEW immutable v11 release containing the
   already-reviewed W55705 implementation plus this bounded regression/config
   completion. Prove the installed candidate contains `acp_settlement.mjs`,
   runs the shipped ACP suite without the checkout or npm/network, and refuses
   a missing or self-addressed action owner before opening a runtime lease.
4. Do not interrupt W85500's current claimed execution merely to cut over the
   bridge. After that exact claim reaches a canonical terminal/pass/block
   transition, render the deployment configuration with its explicit recovery
   owner, start the new release through the ordinary lifecycle controller, and
   verify the service executable, action owner, runtime state and incident
   path all report the new deployment. An operator recovery of W85500 remains
   separately fenced and is never inferred from this Work.

## Bounded patch and test authority

Production/configuration scope is limited to the ACP bridge's configuration
validation and documentation, the three `conf/acp-*.template.json` lifecycle
templates, the two `examples/acp-bridge-*.json` inert examples, and the
existing deployment/template contract tests that cover those files. Test
authority includes additive recurrence coverage in
`tools/acp-baton-bridge/test/acp_baton_bridge.test.mjs` and the necessary
expectation additions in `tests/work/test_w459_fresh_contexts.py` and
`tests/work/test_w163_deploy_bridge.py`. It does not authorize weakening any
existing assertion, changing settlement/replay semantics, editing Baton core,
or changing Work state automatically. Independent review must enumerate every
actual existing test path and evaluate its changed assertions against this
scope.

## Implementation packaging gate — 2026-09-04

**Observed:** The scoped configuration, template, example, documentation, and
regression changes pass the 129-case ACP suite. The focused deployment/template
run passes 48 of 49 cases; its one failure is the existing no-checkout release
gate. The staged release contains `acp_settlement.mjs` because the deployer
copies the ACP bridge tree, but that module imports the shared
`tools/codex-event-bridge/src/quarantine_store.mjs` and `tools/deploy_work.py`'s
closed `SOURCE_SHARED_GATE` list does not copy it. The deployed entry point
therefore exits with `ERR_MODULE_NOT_FOUND` before `--help`, and the shipped
suite cannot run.

**Confirmed implication:** A new release cannot satisfy required correction 3
from the current tree merely by integrating the already-authorized ACP paths.
The assembler must also carry the exact shared quarantine-store source, with a
deployment assertion that the installed file exists, or the settlement module
must stop importing it. Reimplementing or inlining the store would duplicate
the accepted W55705 persistence boundary and is not proposed.

**Open scope decision:** The current bounded patch authority does not name
`tools/deploy_work.py`; no packaging edit is made without an explicit scope
extension. Either authorize adding only the shared source entry plus its
existing deployment-test assertion to W85873, or split that packaging repair
into a dependency Work. The no-checkout release gate and broader `test-v11`
sweep remain blocked until one branch is recorded.

## Packaging scope ruling — confirmed 2026-09-04

Keep the release-completeness correction inside W85873. Its bounded authority
now includes only adding
`tools/codex-event-bridge/src/quarantine_store.mjs` to
`tools/deploy_work.py`'s `SOURCE_SHARED_GATE` and adding the corresponding
installed-file existence assertion to
`tests/work/test_w163_deploy_bridge.py`. This is the missing packaged
dependency of the already-accepted settlement module, not a separate product
change. The ruling does not authorize an assembler redesign, an exhaustive
packaging audit, duplicated or inlined quarantine-store code, or weakened
deployment assertions.

## Co-deployed `pc.code` release dependency — confirmed 2026-09-04

Independent review `review-2026-09-04T19-20-16Z.md` found that the ordinary
mailbox lifecycle starts both `claude-acp` and `pc-code-acp`. The active
deployment input
`/home/sl/baton-v11.14aecfb/acp-pc-code.template.json` and its canonical
repository successor at
`work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/acp-pc-code.template.json`
both omit the now-required `runtime.actionOwner`. Revalidation confirms the
omission in both files and the two services in the same active `infra.json`.

The new bridge correctly refuses this configuration before opening a runtime
lease. Therefore an all-service cutover cannot start from the current inputs,
and leaving `pc.code` on release `8af006f` would preserve the unsafe pre-W55705
settlement path this Work exists to retire. This is an explicit release gate,
not permission to weaken validation, disable a service, infer an owner, or edit
live configuration as a workaround.

The authorized recovery owner for `pc.code` and the exact path ownership are
open decisions. The owner must be supplied explicitly by the operator; it is
not derived from neighboring targets, participant names, roles, routes,
sessions, or telemetry. Proposal packaging and release remain blocked until
the operator either extends W85873's scope to the deployment-owned successor
and its verification or creates a separate blocking Work for that migration.

## `pc.code` owner and bounded scope ruling — confirmed 2026-09-04

The accepted `pc` team configuration explicitly grants `pc.slaw` the
`recover` capability and names that participant as the team's approver.
Therefore `pc.slaw` is the authorized non-self `runtime.actionOwner` for
`pc.code`; this is an operator-supplied deployment decision, not an inference
performed by the bridge.

Keep the co-deployed correction inside W85873. Its bounded authority extends
to the canonical successor
`work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/acp-pc-code.template.json`
and the exact existing deployment/configuration verification needed to prove
that it renders `runtime.actionOwner` as `pc.slaw`. The active file at
`/home/sl/baton-v11.14aecfb/acp-pc-code.template.json` is an operational
cutover target, not proposal source: update it only through the accepted
deployment procedure after the repository candidate is reviewed and released.
This ruling does not authorize a broader multi-team template sweep, inferred
owners, weakening validation, or an unrelated lifecycle redesign.
