# Trusted managed controller entry boundary

Work W339972, parent W339626; reviewer baton.rvpc, claim340017.

## 2026-10-20 — owner selection339985 and bounded research

Owner reroute339985 selects a complete reusable trusted managed execution boundary
for the reviewed v12 controller: validate exact arguments and source bytes,
preserve confinement, reject alternate child-entry arguments, prepare smallest
repair and operator installation, identify concrete execution prerequisites.
No second authoring invocation selected. This supersedes inspection-only delivery
and the operator-run alternative in the parent's POLICY-PREPARATION-339937.md;
that earlier file remains historical preparation, not the current selected plan.

Confirmed installed-state evidence remains in parent's evidence/policy-339937/:
the nominated policy allows direct Docker inspections, not the enclosing Python
controller. Prior actual codxpc invocation339894 failed before manager child
creation on Docker socket permission. No new installation or engine operation
occurred under this claim. Parent remains blocked by canonical edge339973.

Confirmed source gaps:

- tools/codex-event-bridge/src/config.mjs:103-119 explicitly treats policy as
  deployment-owned, rejects arbitrary per-thread override as the solution.
  src/exec_policy.mjs supplies Baton operation/direct inspection prefix rules;
  it is not a trusted controller admission service.
- v12/python/tools/authoring_enforcement.py:21-27 imports manager/tools code
  before main validates the packet at511-514. Its argument parser accepts
  --child-of, --lock-fd and --status-path; a full parent command PREFIX still
  admits appended child-entry operands. Existing child checks do not turn a
  prefix rule into an exact command boundary.
- baseline.py:398 held_packet validates digests from the packet after baseline
  is loaded. baseline.py:548 verify_imported_sources imports modules itself
  before examining locations. These are useful existing integrity checks, but
  neither can be the first check of untrusted executable inputs outside the
  managed sandbox. Trusting a caller-modifiable packet to specify its own new
  source digests also cannot establish reviewed provenance.
- Parent run code/configuration is under /tmp, a managed writable root. A hash
  check followed by import from that mutable path has a replacement race.
  chmod alone is insufficient custody where the caller can replace a parent
  path or restore writes. The boundary must retain protected bytes throughout
  loading/execution, not merely observe them once.

Relevant specification: DESIGN HOST-2 preserves exact attempt/token/object
recovery and no redispatch; HOST-3 requires closed trusted configuration and
bound image/profile/mount/network/limits; HOST-4 preserves container confinement.
No specification adjustment is proposed.

Existing capabilities to reuse: held_packet and imported-source/controller
validation AFTER trusted loading; unchanged authoring_enforcement deadline,
lock and child ownership; generated ENFORCED-COMMANDS environment/argv;
operator-owned prefix-rule installation and supervised infra stop/start. Source
search of tools and v12/python/tools found no existing entry that combines
pre-import trusted custody, closed arguments and reviewed launch admission.
This is a scoped search finding, not proof that no external service exists.

## Proposed smallest repair

One reusable deployment entry with closed check / inspect / start operations
and a registered selection identifier. No arbitrary command, packet path,
Python expression, source directory, environment overlay or controller child
argument is accepted from the managed caller. The operator-installed selection
binds reviewed bytes and exact parent argv/environment/cwd/packet/run/limits.
A prefix rule may authorize this fixed installed entry because its own parser
rejects every extra argument before any image, store, manager or process effect.
No bare interpreter/env/shell grant and no socket permission change.

The trusted entry and its selection registry must be outside managed writable
roots and protected from managed replacement through ancestors/symlinks. It
loads only protected reviewed source/configuration bytes; reject unlisted import
sources, injected Python startup/search paths and changed/linked inputs. Preserve
this protection across validation and child imports. Do not claim atomic trust
from a preflight hash followed by use of mutable originals. The implementer
chooses the smallest supported custody mechanism and demonstrates it, including
host-engine mount-path semantics if a namespace is used. Do not silently rebind
an existing sealed packet to a new source location: any necessary successor
needs explicit provenance review while the original packet/lock remain intact.

Reuse the controller's execution semantics unchanged. check performs no engine
or Job action. inspect reaches the actual staged image-verification subprocess
through this same trusted loading path, without manager creation. start admits
only an explicitly selected run and exact fixed parent entry; installation and
check/inspect do not arm it. Consumed selection or restart must not imply a new
invocation. Keep cancellation/unknown holds and existing lease/cleanup limits.
No new coordination authority, scheduler, Docker adapter or credential interface.

A minimal product-independent deterministic fixture can establish entry dispatch
and refusal behavior without authoring. Such fixture substitution is test-only,
never a caller-controlled production bypass. Actual managed check/inspect after
operator installation establishes effective loaded policy; static matching alone
does not. No live authoring call is selected by that validation.

## Concrete unresolved execution prerequisite

This requires executable launcher/installer code and deterministic verification;
a policy-file edit alone cannot deliver it. AGENTS.md's v11-preparation/v12-
execution rule forbids implementing it directly under this research claim.
The failing managed launch boundary is precisely the capability needed to run
its implementation through the present prepared v12 path. Owner339985 selects
the outcome and preparation, but neither an isolated v12 authoring invocation
nor a direct implementation exception. Do not infer either.

Recommended finite owner exception, ready for decision: assign baton.codxpc via
baton.codx to implement only this trusted-entry/custody/selection boundary plus
installer and focused deterministic tests in an isolated /tmp candidate at the
current accepted base. Allow host-local deterministic verification of that
candidate; no real Docker operation, provider, credential read, installation,
existing instance mutation, controller semantic change or Git mutation. Deliver
exact base/path/digest-bound candidate and operator commands to independent
review. Exception expires on independent candidate acceptance, before operator
installation; effective managed inspection has its separate bounded operational
selection under this Work. No parent authoring retry is included. If owner
prefers a v12 Job, explicitly select its viable launching context instead.

No executable candidate exists yet, so inventing its digest or giving commands
that purport to install it would be misleading. The implementation handoff MUST
supply concrete digest-bound install/check/policy/reload/rollback commands before
operator approval. Historical inspection-only install commands are not a
complete repair and should not be used as its substitute.

## 2026-10-20 — owner implementation exception340055 pinned

Owner reroute340055 approves the finite exception proposed above: baton.codxpc
implements only the trusted entry, source custody, selection boundary and
installer with focused host-local deterministic tests in an isolated /tmp
candidate at accepted base bc925cf5c62d69426ed5862af4d41f4d2a967b0f.
No real engine/provider operations, credential reads, installation, existing
instance mutation, controller semantic changes or Git mutation. Independent
base/path/digest-bound review precedes installation; exception expires at
independent candidate acceptance. No second parent invocation selected.
This supersedes the unresolved implementation-authority state, not installation
or effective managed-runtime acceptance. Claim340058 owns only new candidate
files and PROGRESS; existing controller and parent packet remain unchanged.

## 2026-10-20T16:17:06Z — candidate340058 review requires operational custody

Reviewer340142 verifies candidate manifest4bb826c3..., three source files/five
operator artifacts/206 bundle members.23 deterministic tests pass; actual pinned
controller/baseline import and packet validation pass in a disposable relocated
fixture. Seven successor packet deltas match its explicit declaration.

Blocking finding: root-protected source custody does not protect mutable
operational path resolution under the caller-writable /tmp run. The outside-
sandbox same-uid controller follows an output temporary symlink in baseline
_publish: actual producer canary changes a file outside the configured output
tree. Source and proof are in review-2026-10-20T16-17-06Z.md and evidence/review-
340142-output.json. The operator disclaimer is not confinement evidence.

Correct entry/custody successor within340055 so managed callers cannot redirect
operational effects before or after validation. Preserve controller semantics;
no actual installation, state migration, existing-instance mutation or second
parent invocation. Candidate not accepted, so the finite exception remains
applicable to this bounded correction. No new slice: one trusted boundary needs
joined source/argument/operational-path acceptance. Parent dependency remains.

## 2026-10-20T16:32:48Z — candidate340184 accepted, installation unselected

Independent reviewer340257 accepts exact candidate manifest f136eba332c455130687261c9af1fa867b82d1d7971ec022fe8f82ade5af5a50; see review-2026-10-20T16-32-48Z.md and evidence/review-340257-seals.json.31 focused tests pass, including actual producer canaries under real Landlock. Dedicated private operational custody plus inherited write confinement resolves the prior340142 candidate defect. This supersedes the prior correction milestone, preserving its evidence.

Owner340055 finite implementation exception expires at this acceptance. Installation, account/storage/credential provisioning and actual managed check/inspect are still unselected/unproved. Existing authority identity must be preserved through an explicitly selected quiescent provisioning method. Pass to owner for this concrete operational selection; do not repeat implementation or launch by inference. W339972 remains open; parent W339626 remains blocked and no second invocation is selected.

## 2026-10-20T19:36:18Z — concrete provisioning procedure completed

Continuation341496 supersedes the earlier wait-for-procedure-selection posture. Reviewer341498 completed provisioning-341498/OPERATOR.md and digest-bound credential-copy helper; review-2026-10-20T19-36-18Z.md. Proposed cold transfer fences the original run, preserves existing authority bytes/lock under private service custody, and never bootstraps a replacement authority. Identity/source/credential checks, exact ordered commands, effective managed check/inspect and admission-disable rollback are specified. Source home traversal and credential uid/private-mode requirements were confirmed from metadata and pinned code. No required provisioning design placeholder remains.

No changes executed outside reviewer records; helper AST and9 shell-block syntax checks pass. Operator must now select the concrete privileged operations (account/ACL/cold-copy/credential/install), which341496 expressly excluded from execution. Candidate340184 remains unchanged and unarmed; parent blocked.

## 2026-10-20 — owner provisioning selection342404 and receipt342555

Owner342404 explicitly selected provisioning-341498/OPERATOR.md and its pinned
helper, subject to its checks, with actual managed check/inspect and independent
receipt review required. Operator342555 reports provisioning complete, cold-copy
comparisons passed, original fenced, credential modes/source pins/selection
digest/policies verified, and restarted codxpc services healthy. This supersedes
the prior unselected/unexecuted provisioning posture; the operator report is not
yet independent installed-runtime acceptance. No arm or start is authorized.

Claim342558 is limited to the two installed managed check/inspect calls and
retaining their receipts for baton.bug. The implementation exception remains
expired. Installed entry source was read and confirms check returns after
selection validation; inspect drops identity, restricts writes, and invokes the
pinned image verifier without entering controller main. No source repair,
credential access, store inspection, or parent invocation is part of this claim.

Actual managed check under342558 refused at sudo authentication with exit1:
`sudo-rs: interactive authentication is required`. No check JSON returned;
inspect was not attempted because the selected procedure stops on failed checks.
Evidence: evidence/managed-342558.json. Effective noninteractive admission is
therefore still unproved and blocked despite operator342555 provisioning report.
No fallback or stronger invocation was attempted. Operator/reviewer diagnosis
must establish the effective rule/caller mismatch before another managed probe.

## 2026-10-20T22-09-30Z — effective sudo admission diagnosis required

Review342573 (review-2026-10-20T22-09-30Z.md) confirms incomplete managed receipt. Installed entry and mapped rules match accepted hashes; active sudoers files cannot be read by reviewer (permission denied), so rule inclusion/precedence/caller cause remains open. DIAGNOSIS-342573.md supplies bounded operator read-only checks and conditional narrow repair/managed receipt handoff. Do not infer failed-command namespace from reviewer namespace or expand privileges from the error text. Current milestone remains effective check/inspect, not new source implementation or authoring. Parent339973 gate remains.

## 2026-10-21 — operator correction343603

Operator reports replacing sudoers argument wildcards with exact
w339626-custody-v2 arguments for sudo-rs compatibility; full visudo validation
and host sudo -n check passed with the accepted selection digest. This supersedes
the pending operator-diagnosis milestone, not the prior failure receipt or the
requirement for managed validation. Installed entry hash rechecked under343612
and still matches7547b27f88873e240f1a0666e6c1cdd7dfc5d2a9064974264aea4be6fcdf1d15.
Selected continuation is exact managed check, then inspect only on success,
retaining receipts for independent review. No arm/start or source repair.

## 2026-10-21T00-46-29Z — installed managed boundary independently accepted

Review343619 (review-2026-10-21T00-46-29Z.md) accepts actual managed343612 check/inspect receipts joined with candidate340184, provisioning342404/342555 and exact-argument sudoers correction343603. Selection/image digests and installed entry/rules hashes match. This supersedes the unresolved effective-admission milestone; prior denial remains history. No arm/start or parent second invocation selected. Accepted delivery passes to owner for closure/disposition and human Git checkpoint; dependency339973 remains until canonical closure. Active sudoers correction is operator-attested, not independently read; no private-store census or provider-authentication proof claimed.
