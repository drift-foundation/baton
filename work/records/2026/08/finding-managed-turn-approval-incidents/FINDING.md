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
