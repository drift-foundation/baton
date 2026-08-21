# Make managed-turn approval failures actionable

## Observed — 2026-08-20

The `baton.codex` readiness producer forwarded review episodes and the
dispatcher successfully started their Codex turns. The turns then attempted
canonical Baton operations through `/bin/bash -lc`, even though the accepted
allow rule names the Baton executable directly. Codex consequently requested
interactive command approval.

The dispatcher correctly denied the request because dispatcher-owned
readiness turns are non-interactive. It published
`waiting-input(approval)`, ended the turn, and returned the runner to `idle`.
The Work remained unclaimed. The useful final explanation stayed only in the
background Codex rollout, so the operator saw no durable indication of why
the review was not picked up.

This happened repeatedly at `2026-08-20T17:47:48Z`,
`2026-08-20T18:04:09Z`, and `2026-08-20T18:40:10Z`. The runtime journal
retains the transitions, but each actionable Inbox row disappeared when the
runner returned to `idle`; the reports also lacked Work and episode
correlation.

## Observed mechanism superseded — 2026-08-20

The first paragraph's attribution to `/bin/bash -lc` and raw-executable rule
matching is superseded by the completed rollout trace. Nineteen read-only
Baton invocations through the same shell completed without escalation. The
nine operations that requested approval were the mutating verbs
(`mark-seen`, `phase`, `say`, and `claim`). The managed Codex turn had
`workspace-write` access to `/home/sl/src/baton`, while the coordination home
was outside its writable roots. The shell wrapper and exec-policy rule were
therefore not the differentiator; filesystem write authority was.

The confirmed product decision and acceptance boundary below remain current.
In particular, correcting the mechanism must not turn write access to the
coordination store itself into a general shell capability: managed turns may
perform the configured canonical Baton operations, while raw store/config
mutation and unrelated commands remain outside that narrow authority.

## Confirmed decision — 2026-08-20

- A managed readiness turn is non-interactive. Its narrow canonical Baton
  operations must be pre-authorized and must execute without asking a human
  for approval. An unexpected approval request is an operational defect, not
  an approval prompt to relay or auto-approve.
- Keep live runner state honest: the adapter may publish
  `waiting-input(approval)` while the request exists and must return to
  `idle` after the failed turn ends.
- Separately create a durable operational incident for the configured action
  owner. Returning the runner to `idle`, restarting a process, refreshing the
  TUI, or marking related discussion seen does not clear the incident.
- The incident remains sticky in `[Inbox*]` until the action owner explicitly
  dismisses it. No `Approve` action is offered: the corrective action is to
  repair the deployment/rule mismatch or deliberately reroute the Work.
- Correlate the incident with the participant, adapter/session, Work,
  assignment episode/action key, safe command category, cause, and observed
  instant. Do not persist command bodies, credentials, environment values, or
  other unsafe approval payloads.
- Repeated reports for the same participant, Work episode, and approval cause
  coalesce into one open incident while retaining a count and latest observed
  instant. A new episode or a recurrence after dismissal creates a new
  incident.

Live runtime state answers what the runner is doing now. The sticky incident
answers what failed and still needs operator attention. Neither substitutes
for the other.

## Acceptance boundary

- A managed reviewer turn can perform its configured canonical Baton
  `claim`, message, pass, and close operations through the exact narrow allow
  rule without an interactive approval request or a broad shell allowance.
- Any other command that requires approval still fails closed; the dispatcher
  never approves it.
- An unexpected managed-turn approval produces both the transient runtime
  transition and one durable, Work-correlated action-owner incident.
- The incident remains visible through later `idle` transitions, refreshes,
  and managed-stack restarts until explicit dismissal.
- `[Inbox*]` attracts attention while the incident is open, and its details
  explain that the Work remains unclaimed and identify the safe remediation
  boundary.
- Dismissal is authoritative and journaled. It does not claim, reroute, close,
  or otherwise mutate the affected Work.
- Regressions cover the allowed raw Baton path, refused non-Baton commands,
  correlation, coalescing, restart persistence, explicit dismissal, and
  secret-safe rendering.

## Confirmed execution-policy clarification — 2026-08-20

The mediated-MCP recommendation in
`review-2026-08-20T23-42-34Z.md` is superseded. W415 does not introduce an
arbitrary `thread/start` configuration override or a new general tool proxy.
The narrower route is the deployment-owned Codex command policy already
intended by the acceptance boundary:

- The managed app-server deployment owns an exact allow rule. The model cannot
  supply or alter that rule through a turn.
- The rule matches the exact installed Baton executable, exact accepted config
  path, exact participant identity, and only the ruled mutating verbs:
  `claim`, `say`, `pass`, and `close`.
- The model invokes that executable directly. Shell wrappers, alternate
  executables/configs/participants, unlisted Baton verbs, and unrelated
  commands do not match.
- The managed turn receives no writable root containing the authority. A
  matching Baton operation may cross the filesystem sandbox through the exact
  command allow rule; arbitrary shell or direct SQLite/config mutation remains
  sandboxed and the non-interactive dispatcher refuses any approval request.
- Baton's grammar and authority continue to validate the operands and workflow
  mutation. The command rule is only the execution boundary; it does not grant
  protocol authority the participant does not have.

The decisive live proof uses the deployment rule, not an arbitrary per-thread
override: an exact raw `claim` commits without an approval request, while a
shell-wrapped Baton invocation, another participant or config, an unlisted
Baton verb, direct SQLite/file mutation, and an unrelated command all fail
closed. If the installed Codex execution policy cannot establish that result,
implementation stops and returns evidence rather than falling back to a
writable authority directory.

## Exact-set clarification — 2026-08-20

"Only the ruled mutating verbs" and "unlisted Baton verbs do not match" mean
the nominated participant policy is the exact approved set, not merely a file
that happens to contain that set. An allow rule for the same executable,
config, and participant but any other Baton verb makes the preflight fail.
The bridge does not need a second list of Baton's mutating verbs: read-only
commands need no sandbox-crossing allow rule, and the nominated deployment
policy is deliberately dedicated to these four managed mutations. Exact rules
for other configured participants remain independent and valid.

## Relationship to earlier work

`finding-readiness-target-wedged-turn` established that the dispatcher must
deny and terminate an approval-blocked non-interactive turn rather than wedge
the readiness queue. This finding preserves that ruling and adds the missing
execution-policy correction and durable operator feedback; it does not reopen
automatic approval or indefinite waiting.

## Cross-Work continuation recurrence — observed 2026-08-21

After the fresh schema-27 deployment, the managed `baton.codex` session began
W30 and requested interactive approval to run the v12 test suite with Docker
access. The dispatcher correctly denied and interrupted that non-interactive
turn, producing incident I1 for W30. The next readiness turn was for W28, but
before acting on W28 the same session attempted the unfinished W30 cleanup:
`rm -rf /tmp/w30-fixture-audit.Lmr3aa`. The dispatcher again refused it and
produced incident I2 correlated to W28 because W28 was the current readiness
episode.

**Confirmed defect.** A denied/interrupted managed turn may leave semantic
intent in the persistent agent context. A later Work wake can therefore resume
an operation belonging to the preceding Work, while incident correlation names
the new readiness episode. The command refusal remains correct; broad shell,
Docker, or destructive-command approval is not an acceptable correction.

The managed dispatcher must establish a Work-scoped execution boundary after
an interrupted turn. Before delivering another Work, it must either prove that
the prior turn and its pending intent are settled, or replace/reset the managed
context so no later Work can continue the prior Work's actions. Incident
correlation must identify both the active readiness episode and, when known,
the originating Work intent rather than presenting the later Work as the
source. Regression coverage must reproduce an approval-blocked Work A followed
by Work B and prove that no Work-A command is issued during Work B.

## Reviewer revalidation — 2026-08-21

**Observed.** `EventBridge.#denyAndRecover` records a live `blocked` condition,
but both an `idle` status notification and `#turnCompleted` call
`#clearBlocked`. That method discards the only delivery fence, and `#drain`
then starts the next retained readiness event on the same configured
`state.threadId`. The existing regression named "the turn ending drains
everything that queued behind it" requires this exact transition.

**Confirmed.** Turn termination proves that no command from that turn is still
executing; it does not prove that the persistent agent context discarded the
interrupted Work's intent. The W30-to-W28 recurrence is direct counterevidence.
The v11 ruling in
`work/records/2026/08/finding-readiness-target-wedged-turn/FINDING.md` currently
requires retained events to drain when the target becomes idle, so it and this
new boundary cannot both remain authoritative without a scoped supersession.

**Observed.** Incident correlation is selected from
`state.activeTurn?.event?.action` at request time. The approval request's
authoritative `params.turnId` is used only later for interruption. A request
that races the `turn/start` continuation can therefore file without the Work
locator even though the dispatcher still holds the queued event, and a turn-id
disagreement does not prevent attribution to the locally recorded action.

**Proposed v11 boundary.** An unexpected approval request taints its configured
managed context immediately. Denial and bounded interruption still end the
live turn, but idle/completion clears only the live-turn blockage; it does not
make the tainted context deliverable. Retain queued actions, report the target
unhealthy with the failed Work/action locator, and require the documented full
managed-stack stop/start that mints a fresh context. Do not create a replacement
context inside the v11 dispatcher; automatic replacement remains owned by the
v12 worker supervisor.

Capture an immutable delivery attempt before awaiting `turn/start`, including
the event/action and eventual turn id, and use the approval request's turn id
to select that origin. If the request and local turn disagree, file the active
request safely without guessing a Work origin. Command bodies remain outside
all logs and incidents. Under the proposed fence there is no Work B turn in
which Work A intent can run; any late request remains associated with the
tainted attempt when that association is observed, rather than with a queued
but undelivered Work B.

**Open ruling.** Confirm that an approval-tainted v11 context remains
undeliverable until a full managed-stack restart, and supersede only the
same-thread drain clause of the earlier W3243 ruling for this case. The
alternative is to add in-process context minting, durability, lifecycle-state
replacement, and cwd/instruction ownership to v11, duplicating the worker
supervisor already planned for v12.

## Approval-tainted context ruling — confirmed 2026-08-21

Slawomir approved the proposed v11 boundary above. An unexpected approval
request permanently quarantines that managed context for the remainder of the
current managed-stack start. Ending or interrupting the live turn clears only
the live-turn blockage; it never makes that context deliverable and never
drains queued Work onto it. Recovery requires a full managed-stack stop/start,
which mints a fresh context. Automatic in-process context replacement remains
v12 Worker Manager work.

Incident attribution is bound to an immutable delivery attempt and the
approval request's authoritative turn id. A turn-id mismatch is reported
without guessing a Work origin. Command bodies, argv, environment values, and
filesystem operands remain outside incidents and logs. This ruling authorizes
the bounded v11 implementation and regression boundary in
`review-2026-08-21T15-46-43Z.md`; it does not authorize Docker access, broad
shell approval, destructive-command approval, or automatic v11 replacement.
