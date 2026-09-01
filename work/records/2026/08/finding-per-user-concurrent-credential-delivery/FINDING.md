# Make credential delivery per-user and concurrent

Work: W52821

## Finding

The supervised dogfood path currently requires an operator to copy a host
credential into the global path `/run/baton/credentials/<provider>` before a
run. This is unnecessary deployment ceremony and is incompatible with
multiple OS users running Baton concurrently with separate provider accounts.
A shared mutable credential slot must never become a serialization point.

The live W51487 proof also established a separate worker-facing defect: the
manager materializes an attempt slot as `0600` owned by the host manager uid,
then launches the container as uid 65532. The worker sees the path but cannot
read it. A credential-free reproduction shows that the existing supplementary
workspace group plus mode `0640` makes the slot readable without making the
bearer world-readable; worker preflight must test readability rather than path
existence.

## Confirmed direction — 2026-08-31

Credential resolution and materialization are per assignment, keyed by the OS
user, credential profile, assignment generation and attempt id. Each user has
a user-scoped runner under that user's uid. The runner reads only that user's
configured provider source, creates a unique attempt-private credential slot,
and exposes only that slot read-only to the worker container.

The shared Baton configuration does not carry host credential paths. There is
no global credential lock, shared mutable slot or process-global active
attempt. Different users and participants can run concurrently; serialization
comes only from explicit routing, claim limits or provider policy. The fixed
path inside each isolated container may remain
`/run/baton/credentials/<provider>`.

The global manually synchronized `/run/baton/credentials/*` source convention
is superseded for the eventual multi-user path. A local private-box dogfood
workaround may remain until this defect is implemented.

## Scheduling boundary

Do not interrupt or alter the first useful dogfood proof. This defect becomes
the next high-priority implementation concern only after W38956 closes
satisfying. Its Baton Work must be explicitly blocked on W38956 before any
research or implementation begins.

## Scheduling revalidation — 2026-08-31

**Observed:** W38956 closed `non-satisfying` at ledger sequence 57541. That
terminal transition cleared W52821's dependency edge and made it mechanically
ready, because the edge records terminal dependency completion rather than a
required terminal outcome. It did not satisfy this record's stricter scheduling
decision.

**Decision:** the readiness wake is not authorization to research or implement
this defect. Park W52821 without changing its confirmed defect classification,
technical direction or acceptance boundary. Resume only after an explicit
superseding scheduling ruling names this Work independently, or after a later
successful dogfood milestone is recorded as the replacement gate. W38956's
non-satisfying outcome cannot be silently treated as the satisfying close this
record required.

## Scheduling and acceptance supersession — 2026-09-01

Slawomir explicitly resumes W52821 after W55758's independently reviewed
recovery correction. This is a new scheduling authorization; it does not
reinterpret W38956's non-satisfying outcome as satisfying. W52821 is the first
real repository change selected for supervised execution through the v12
worker path. Keep the current private-box credential workaround only long
enough to run this Work; do not interpose more scheduler, TUI, telemetry,
Podman or unrelated hardening before it.

The current slice uses ONE live worker. The earlier acceptance language about
two OS users running live attempts concurrently is superseded for this slice:
future concurrency remains a required supported mode, but a second live worker
is not required now. Establish the property through user-scoped provider
configuration, unique attempt-private slots, absence of a shared mutable
source/slot/lock, and focused tests using two distinct user/provider contexts.
A later integration Work may exercise two live users after the single-worker
path is in ordinary use.

## Acceptance

- No user manually copies or refreshes a provider credential into a shared
  global path before ordinary execution.
- Two distinct OS users with separate credentials can run isolated attempts
  concurrently without sharing a source, slot, lock or mutable state.
- Attempt credential slots are unique, worker-readable, non-world-readable,
  read-only in the container and removed by exact-attempt teardown.
- An unreadable slot refuses before a provider turn with a safe typed cause.
- Shared Baton configuration and durable evidence contain no credential
  content or host-user credential path.

For the first resumed slice, these boundaries are accepted without starting a
second live worker. The implementation must still make a future concurrent
run possible without redesigning credential ownership.

## Reviewer revalidation — 2026-09-01

### Observed current command boundary

The supported Python dogfood command still exposes
`--credential-file PATH`. Its `__main__` closure stores that one pathname,
discards both `provider` and `reference` when the manager asks for a
credential, opens the pathname, and returns its stripped text. The command
therefore does not use the trusted `credential_profile` selection it already
carried into `credentials.resolved_delivery`; any configured provider and
reference receive whichever one file the invocation named.

The path is neither in the grants nor the evidence, which is correct, but the
launcher proves none of the facts that would make it a user-scoped source: it
does not require a regular non-symlink file, current-uid ownership, private
mode, or a match to the requested `(provider, reference)`. A shared
`/run/baton/credentials/claude` convention remains the documented live input,
and changing or refreshing that file is still external ceremony shared by all
invocations that name it. The exact command baseline is preserved at
`evidence/research-2026-09-01/baseline.md`.

### Confirmed current manager boundary

Do not reimplement the manager's attempt-local half:

- `credentials.resolved_delivery` already resolves each authorized slot
  through the trusted profile to an exact `(provider, reference)` pair.
- `_launched` constructs one `CredentialHome` and one lazy `deliver` closure
  per command invocation. Its `materialized` guard is closure-local, not a
  process-global active attempt or global credential lock, and delivery occurs
  after assignment activation and before runtime creation.
- `CredentialHome.volatile_root` is
  `<credential_home>/credentials/<attempt_id>`; materialization refuses an
  existing exact-attempt root, and `tear_down` removes only that delivery's
  slot files, root and lifecycle record.
- W52800 is closed satisfying. Slots are manager-owned `0640` files in the
  configured supplementary workspace group below a manager-owned `0700`
  root; the worker distinguishes missing from unreadable before provider
  launch. The earlier readability defect in this finding is resolved history,
  not work for W52821.

The remaining implementation boundary is therefore the user-side provider
resolver and its command wiring. `credentials.py`, `oci.py` and
`claude_agent.py` are reference context for this slice, not expected patch
targets.

### Proposed bounded source contract — approver ruling required

Use one explicit user-local source-registry file, supplied to the user-scoped
runner as `--credential-sources PATH`; remove `--credential-file` from the
supported ordinary command rather than retaining a bypass around the new
selection. The registry is not shared Baton configuration and is never copied
into grants, evidence, lifecycle state or a worker mount. It has a closed,
bounded shape:

```json
{
  "schema": "baton.user-credential-sources/1",
  "sources": [
    {
      "provider": "claude",
      "reference": "default",
      "path": "/the/current/users/private/provider/source"
    }
  ]
}
```

`reference` is the opaque value already selected by the assignment's trusted
`credential_profile`; no new protocol or grants member is needed. Duplicate
`(provider, reference)` entries refuse. Unknown selections refuse without a
fallback. The registry and selected source are opened without following a
final symlink, proved to be ordinary files owned by the runner's effective uid
with no group/other permission, and read through the proved descriptor under
the manager's existing bearer-size bound. No environment variable, inferred
home path, shared default, cache, singleton or lock participates.

The resolver is constructed once per ordinary command and bound to that
assignment's participant, generation and attempt context; the manager calls it
later with the exact provider and reference. This preserves W55758's lazy
window: source bytes are not read and no attempt slot exists until after
activation. A missing, malformed, mismatched, substituted, non-private or
unreadable source produces a bounded typed refusal before runtime/provider
launch, and `CredentialHome.materialize` retains responsibility for unwinding
the empty attempt root. Recovery and handoff retry neither load this registry
nor read a source; supplying it to those modes should refuse as a contradictory
command.

This slice does not provision operating-system accounts or start a second live
worker. Its concurrency proof uses two independent configured contexts with
distinct registry/source files, trusted provider references, generations,
attempt ids and credential homes. A synchronized focused case must show each
resolver returns only its own harmless canary and each materialization creates
and tears down only its own attempt root. That is structural evidence of no
shared mutable source, slot, cache or lock; the deferred live-two-user Work
remains responsible for host integration.

### Proposed patch and verification boundary

The proposed task is frozen at
`evidence/research-2026-09-01/task.json`; its closed source/edit boundary is
`evidence/research-2026-09-01/source-files.txt`. Prefer one small
standard-library `tools/user_credentials.py` owner for registry parsing,
descriptor proof and exact selection, with `dogfood_operator.py` limited to
command wiring and the existing lazy provider injection. Add a self-contained
focused test module and register it with the parallel test runner. Update
`DEPLOYMENT.md` with per-user setup and removal of the private-box staging
step.

Focused acceptance must cover exact selection, duplicate/unknown refusal,
ownership/type/mode/unreadable refusal, no source read before lazy delivery,
cleanup after resolver failure, two-context overlap and isolation, exact
attempt teardown, command help/mode contradictions, and absence of bearer or
host source path from grants and evidence. Existing credential, secret-sweep,
OCI and dogfood-operator suites remain regression gates after the focused task
passes. A live provider turn and two-live-user execution are not part of this
reviewer task.

### Open approver decisions

1. Approve or reject the explicit user-local `--credential-sources` registry
   as the first runner contract, including removal of the direct-file bypass.
2. Approve or narrow the current-uid, ordinary-file, final-symlink refusal and
   no-group/no-other permission rule for both registry and selected source.
3. Confirm that a host source path is permitted only inside this private
   user-local registry, while shared Baton configuration and every durable
   attempt/evidence document remain path-free.

### Approver ruling — 2026-09-01

Slawomir approved all three source-contract decisions on W52821. The supported
ordinary command replaces `--credential-file` with the closed private
user-local `--credential-sources` registry keyed by the trusted provider and
opaque reference. The registry and selected source must each be an ordinary
non-symlink file owned by the runner's effective uid with no group or other
permissions. A host source path is permitted only in that private user-local
registry; it never enters shared Baton configuration, attempt evidence,
lifecycle state, or worker-visible documents.

This first supervised v12 implementation uses one live worker. Future
concurrency remains a required supported mode, established in this slice by
isolated contexts and focused tests rather than by starting a second live
worker.
