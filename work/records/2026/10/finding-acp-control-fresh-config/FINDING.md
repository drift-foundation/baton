# W319007 — ACP control invocation reaches legacy startup

## 2026-10-18 — reviewer diagnosis (baton.rvpc)

**Observed report:** T319007 message319007 reports deployed control status failing
with session.mode=new after session creation. No dossier was bound at assignment;
binding revision1 now names this record. Read work events through319016 and
discussion through319007; reviewer warning is message319019.

**Confirmed by source inspection:** the supplied deployment at
/home/sl/opt/baton/v11/0650c61/lib/acp-baton-bridge/src/acp_baton_bridge.mjs
has no control-command branch in runAcpBatonBridge. Its permissive option parser
accepts --control status but proceeds to runBridge, whose session preflight rejects
new against an existing selection. The distribution bin/acp-baton-bridge wrapper
executes that module. This is not loadConfig enforcing session selection.

Current repository tools/acp-baton-bridge/src/acp_baton_bridge.mjs:778-790 loads
configuration and handles control before runBridge. config.mjs:303 delegates to
validateConfig, which checks shape/resources but does not preflight session files.
runBridge:222 performs that launch-only check. The already accepted operator
capability is documented in baton:work/records/2026/09/finding-managed-turn-operator-cancel/PLAN.md
and its review-2026-09-17T15-16-29Z.md; that acceptance explicitly did not claim
production deployment.

**Inferred cause:** the incident matches an invocation of the legacy deployed
executable rather than the current operator-control implementation. The report
does not pin its executable's absolute path; operations must verify that exact
path and the running owner's version/socket before choosing a remedy.

**Required safety correction to the proposed workaround:** do not change new to
load and invoke --control with 0650c61. That binary ignores control and can enter
the readiness loop; it cannot operate an existing owner's control socket. No
workaround was executed by this reviewer, no production configuration was read
or changed, and no live provider or claim recovery was attempted.

**Verification limitation:** an isolated Node subprocess comparison was attempted
using synthetic config, a preexisting synthetic session, and nonexistent agent
and Baton executables. Both spawnSync calls were refused EPERM by the managed
sandbox; no CLI behavior pass is claimed. Fixture retained at
/tmp/w319007-qw5HkK. Initial guessed deployment tools/ paths were absent; the
actual readable distribution code is under lib/acp-baton-bridge/. Repository
policy, operating guide, protocol guide and the bound record are readable.

**Decomposition:** one bounded deployment diagnosis, no independent implementation
slices justified. Current source does not exhibit the alleged ordering bug.
Reviewer owns this FINDING/PLAN only; product files and existing unrelated v12
changes remain with their authors. Operations owns executable identification and
any separately authorized deployment/recovery; independent review must assess any
new candidate before acceptance. No deployment or production cancellation is
authorized by this diagnosis.

## 2026-10-18 — owner defers v11 follow-up

Slawomir confirmed "let's park" after the recommendation to defer W319007 and
keep development focused on v12. Preserve this Work and its evidence; no v11
repair, deployment change or dependency on v12 readiness is selected. This
supersedes the earlier immediate operations follow-up as scheduling direction.
At snapshot319059 the Work is queued, unclaimed at baton.ops, whose Handler is
Slawomir. Prompt records the decision; the owner performs the phase transition.
Prompt's exact deployed invocation and terminated accidental bridge are recorded
in T319007 message319018, supplementing the reviewer's earlier diagnosis.
