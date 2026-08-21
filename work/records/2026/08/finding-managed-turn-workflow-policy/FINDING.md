# Authorize the complete managed Work workflow

## Observed — 2026-08-21

The managed `baton.codex` reviewer claimed W126, completed its repository
review, and then attempted the canonical operation:

```text
baton --config /home/sl/baton-v11.d46ab1e/baton.json \
  --participant baton.codex \
  mark-seen thread=T126 up-to=178 op-id=w126-review-r1-seen
```

The deployed exact execution policy allowed only `claim`, `say`, `pass`, and
`close`. `mark-seen` therefore ran inside the ordinary workspace sandbox and
failed because the coordination authority is deliberately outside its
writable roots. The non-interactive dispatcher correctly refused two approval
requests and interrupted the turn. Runtime returned to `idle`, but W126
remained authoritatively claimed by `baton.codex`.

The sticky I1 approval incident surfaced the failure as designed. The defect
is the policy capability set: it permits enough mutation to take Work but not
enough to complete the ordinary managed workflow safely.

## Supersession

The four-verb exact-set ruling in
`work/records/2026/08/finding-managed-turn-approval-incidents/FINDING.md` is
superseded only as to the nominated verb set. Its deployment-owned, exact
binary/config/participant matching, broad-rule refusal, effective-policy live
proof, non-interactive failure behavior, and prohibition on raw authority
filesystem access remain current.

## Confirmed decision

A managed agent receives one exact command rule for every public **Work
workflow mutation** it may need while following repository and Baton policy.
The current profile is:

```text
create accept respond dispose close block unblock mark-seen classify claim
release prioritize pass heartbeat phase try extend report assess abandon revise
start-thread say label unlabel bind poke poke-answer poke-cancel reroute
```

This profile deliberately excludes:

- deployment/configuration mutations: `activate`, `regen`;
- adapter-owned runtime publication: `runtime-start`, `runtime-state`,
  `runtime-end`, `runtime-facts`, `runtime-refresh`;
- dispatcher-owned incident publication and operator disposition: `incident`,
  `dismiss`.

The execution policy grants permission to invoke only the exact canonical CLI
prefix. Baton's authority still decides whether the participant may perform a
particular operation on a particular Work. The policy never grants raw access
to `work.sqlite3`, `baton.json`, or the coordination directory, and never
authorizes shell wrappers, alternate binaries/configs/participants, unknown
verbs, or future mutations implicitly.

The profile is an explicit reviewed set. A newly added public mutation remains
unauthorized until this policy profile is deliberately updated; it must not
appear automatically merely because the CLI's mutation registry changed.

## Acceptance boundary

- The installed generator emits the exact managed-workflow profile above for
  each nominated participant and the dispatcher audits that same set.
- A managed reviewer can claim W126, mark its discussion seen, publish its
  review handoff, and pass or close without interactive approval.
- Directed-obligation handling and safe claim recovery (`respond`, `accept`,
  `dispose`, `heartbeat`, `release`) work through the same exact boundary.
- Broad rules, an extra same-participant verb, an omitted ruled verb, shell
  wrapping, another identity/config/binary, raw store access, and excluded
  deployment/runtime/incident verbs fail closed.
- The durable approval incident remains sticky until the action owner
  dismisses it; correcting policy does not silently dispose history.
- Regression coverage derives expected generator/auditor behavior from one
  named profile and proves the effective app-server boundary, not only the
  nominated rules file.


## Implementer revalidation — 2026-08-21

**Confirmed against the current tree before any edit.**

- `tools/codex-event-bridge/src/exec_policy.mjs` carried
  `RULED_VERBS = ["claim", "say", "pass", "close"]`, and its comment recorded
  the round-4 rejection of `mark-seen` together with the instruction that
  adding it is "a ruling to obtain and pin". This Work is that ruling; the
  comment now records both, because the rejection was right at the time and
  the reasoning is how the next reader understands the current rule.
- `mark-seen` requires `thread=` AND `up-to=`; the escalation the finding
  observed is consistent with a command that reached the coordination home.
- The profile the finding names is exactly
  `baton_work.cli.MUTATIONS` minus `{activate, regen}`, the five `runtime-*`
  verbs, and `{incident, dismiss}` — 30 verbs, verified against the registry
  rather than assumed. Every verb in it is a real public mutation.
- `smoke/exact_policy_matrix.mjs` case 5 used `phase` as its "verb outside
  the ruled set". The confirmed profile authorizes `phase`, so that case had
  to move to a deliberately excluded verb rather than be deleted.

No pinned decision had changed, so nothing needed supersession beyond what
this record already states.

## Implementation decisions — 2026-08-21

**One named profile, written out, not derived.** `POLICY_PROFILE`
(`managed-work-workflow`), `RULED_VERBS` and `EXCLUDED_VERBS` are literals in
`exec_policy.mjs`. The generator, the auditor, the deployed instructions and
every regression read the capability from there. It is deliberately NOT
computed from `baton_work.cli.MUTATIONS`: a new public mutation must stay
unauthorized until somebody adds it here on purpose.

**The drift alarm is a test, not an inclusion rule.**
`tests/work/test_w220_managed_workflow_policy.py` fails when the CLI registry
holds a mutation that is neither in the profile nor in the recorded
exclusions, and when the profile or exclusions name a verb that is no longer
a public mutation. It makes the decision unavoidable; it never makes it
automatically.

**Regressions keep their own copy of the expected set.** Round-4's lesson
survives this ruling: a test that reads the implementation's own list cannot
catch that implementation widening it. Both the Node tests and the deployed
Python matrix carry the 30-verb literal and the exclusion literal.

**Order is part of the profile.** The generator emits rules in the order the
confirmed decision lists them, so an operator diffing a regenerated policy
file against this record sees no reordering noise.

**Upgrade behaviour is fail-closed and documented.** A policy file generated
by an earlier release carries only four rules; the dispatcher now refuses to
start and names the 26 missing verbs. The shipped template says to REGENERATE
the whole file rather than append, so no retired rule survives the upgrade.

## Verification — 2026-08-21

The effective app-server matrix was extended and re-run against a candidate
release, under an isolated `CODEX_HOME` whose policy contains ONLY the 30
generated rules. Full output:
`effective-policy-matrix-2026-08-21.txt`. **13/13 cases pass**, including the
four new ones this ruling requires:

- `mark-seen` commits with no approval request (unread 2 -> 0) — the exact
  operation whose refusal stranded W126;
- `release` recovers a claim, and `respond` discharges a directed obligation
  (phase `block` -> `queued`), both with no approval request;
- the excluded `regen` does not accept a staged configuration proposal, the
  excluded `runtime-state` does not move a live lease's state, and the
  excluded `incident` files nothing — each set up so the command WOULD have
  succeeded had the policy allowed it.

Every negative case W415 established still passes: shell wrapper, wrong
participant, wrong config, direct SQLite write, direct config write, and an
unrelated command in the coordination home.

## Review round 1 — accepted corrections, 2026-08-21

`review-2026-08-21T05-56-05Z.md` recorded two findings. Both were reproduced
exactly as written and are now recorded rulings.

**[P1] Operand-qualified excluded rules passed the exact-set preflight.**
Reproduced with `auditRules` against the changed module: the thirty exact
rules plus

```text
prefix_rule(pattern=[…, "baton.codex", "regen", "op-id=authorized-extra"],
            decision="allow")
```

returned `missing=[]`, `broad=[]`, `extra=[]`, `satisfied=true`. The
same-identity test required a pattern EXACTLY one element longer than the
participant prefix, and a Codex prefix rule may carry operands.

**Ruled.** The exact-set test inspects the VERB SLOT of every allow rule whose
pattern starts with this participant's prefix, whatever follows it. An element
in that slot which is not a ruled verb — an excluded verb, an unknown or future
one, or an operand sitting where a verb should be — is extra capability and
fails the preflight. A RULED verb carrying operands is NOT extra: it authorizes
a subset of a capability the profile already grants, and the ruling is about
which verbs the participant may invoke.

**[P2] Two live negatives used the wrong participant.** Confirmed: the isolated
policy is generated for `poc.ops` alone, and the `runtime-state` and `incident`
cases invoked their commands as `poc.other`. They therefore failed at the
already-covered wrong-participant boundary and established nothing about the
runtime and incident exclusion groups.

**Ruled.** A negative that proves the exclusion must run as the participant the
policy NAMES. Prerequisite state — the runtime lease those two commands
require — is still opened out of band, because the setup is not what is under
test; the command under test runs as `poc.ops`, and the before/after probes are
read for `poc.ops` too.

## Verification — round 1 corrections

`effective-policy-matrix-2026-08-21-r2.txt`: **13/13**, with the two corrected
cases now reading `poc.ops state idle -> idle` and `incidents 0 -> 0` for the
nominated participant.

## Review round 2 — accepted correction, 2026-08-21

`review-2026-08-21T06-42-58Z.md` recorded one finding, and it is about the
in-source explanation of the boundary rather than the boundary itself.

**[P2] The exact-set rationale still stated the superseded scope as current.**
Confirmed: `auditRules`'s comment explained why any same-identity unruled verb
is extra capability and then said the policy file "is deliberately dedicated to
the four managed mutations". The module's historical section correctly framed
the four-verb ruling as superseded, but this sentence presented the old count
as the CURRENT safety argument — and a maintainer following it could
reasonably have concluded that the other twenty-six generated rules were
unintended.

**Ruled.** The in-source rationale names the profile, not a retired count: the
file is dedicated to the approved `managed-work-workflow` profile — the thirty
public Work workflow mutations in `RULED_VERBS` and nothing else — and any
verb outside that profile is extra capability whatever it does. The two points
the reviewer asked to keep are kept: read-only commands need no allow rule
here, and rules for other participants are unaffected.

One further mention of "four" was left in place and DATED rather than removed:
the round-6 W415 note explaining why a broad rule is reported even when exact
rules exist. That sentence is an account of a defect found when the ruled set
genuinely was four verbs, and rewriting it would erase the history that
explains why the check has its current shape. It now says so explicitly.

## Review round 3 — accepted for deployment, 2026-08-21

`review-2026-08-21T07-09-12Z.md` independently verifies the corrected
in-source rationale, re-runs the focused bridge and deployed-policy gates, and
reproduces the qualified-rule boundary. No source or policy finding remains.

The acceptance is for deployment, not terminal closure: the running policy
still has four rules. W220 remains open until the accepted release is deployed,
the deployment-owned policy is regenerated for every configured participant,
and the effective boundary is verified.
