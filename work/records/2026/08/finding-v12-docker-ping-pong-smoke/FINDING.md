# Finding: run the first v12 Docker ping-pong proof

High-priority checkpoint for the v12 local OCI campaign. This record is
top-level because the W5 dossier is already at maximum nesting depth. It is a
bounded precursor to W6636, not a replacement for that Job's lifecycle matrix
or W6's independent conformance certification.

## Confirmed boundary — 2026-08-26

Prove the smallest honest end-to-end v12 lifecycle with one deterministic
scripted worker and a real Docker engine. The operator supplies a ping through
the approved artifact-neutral input contract; a consent container accepts the
assignment; the manager commits the claim and positively destroys consent; a
fresh execution container emits the correlated pong through the approved
output contract; and the manager quiesces, seals, collects and destroys the
attempt.

This proof uses the Python v12 platform only. It does not use the retired Node
proof, modify the v11 product path, depend on a live model/provider or network,
or claim the broader restart, race, fault, cancellation and portability
coverage owned by W6636 and W6.

The direct prerequisites are W6633 (reference worker image) and W6634 (sealed
output and assignment credentials). W6633 already carries the transitive
artifact-neutral input dependency. W6636 consumes this checkpoint after it
passes.

## Acceptance

- One documented operator command, preferably `just ping-pong` from
  `v12/python/`, runs the proof against a real Docker daemon.
- The proof uses a disposable v12 authority/state and a deterministic scripted
  worker; it never relies on an external AI service.
- Read-only `/input/input.json` carries a stable request and correlation
  identity for `ping`.
- The worker writes `/output/output.json` last with the same correlation
  identity and a deterministic `pong` result.
- Consent and execution are separate containers. Consent is positively absent
  before execution receives the private workspace.
- The manager records the offer, accepted claim, activation, quiescence,
  immutable output seal/collection, terminal result and positive cleanup.
- Completion leaves no worker container, live assignment credential or
  writable private workspace.
- Docker absence or an unmet prerequisite fails clearly; the proof never
  silently skips itself and reports success.
- Durable evidence names the assignment, runtime attempt, image, input,
  output, result and cleanup observations needed to reproduce the run.

The implementer creates and exclusively owns `PROGRESS.md` after claiming the
canonical Work.

## Supersession — 2026-08-26 tracer-bullet first

The earlier requirement that this Work wait for W6633 and W6634, use the final
two-container consent/execution topology, and exercise the full manager claim
lifecycle is superseded. Waiting for the production components would prevent
this Job from answering its first question: whether the Docker worker concept
is practical enough to justify that investment.

W17110 is now a disposable vertical spike. It may use a clearly named
spike-only image, a deterministic temporary worker, direct Python orchestration
and narrowly scoped glue that is not yet a public v12 contract. It must still
run a real Docker container, mount staged input read-only, expose a separate
writable output directory, carry one correlation identity from `ping` to
`pong`, publish `output.json` last, validate the result on the host, and prove
container and temporary-resource cleanup. Prefer existing reviewed v12 Python
components where that shortens the path, but do not distort or delay the spike
to make unfinished production components reusable.

The spike may omit the consent container, durable authority, assignment-token
security, immutable output sealing, restart recovery and the full lifecycle
state machine. It never handles real credentials, modifies the v11 product
path, depends on a live model/provider, or writes outside its explicit
temporary/output roots. Docker absence and a malformed or missing pong fail
visibly.

All spike-only code and evidence are labelled as such. A successful demo proves
only build/run, isolation, input/output exchange, host validation and cleanup.
W6633, W6634 and W6636 later decide what to reuse and must not silently promote
the spike as production implementation or conformance evidence. W6636 still
depends on W17110 so the broader composition incorporates what the demo taught
us; W17110 no longer depends on W6633 or W6634.

## Supersession — 2026-08-26 real agent trials

The earlier deterministic fake-worker and no-live-provider boundary is
superseded. The purpose of W17110 is specifically to discover whether real
Claude and Codex agent runtimes can be wrapped in Docker and complete even the
smallest assignment. A scripted echo worker cannot answer that question.

Run two ordered trials:

1. package and launch a real Claude agent runtime inside Docker, deliver
   `ping`, and capture its `pong` result;
2. after the Claude trial has produced a durable success or actionable failure
   report, package and launch a real Codex agent runtime inside Docker through
   the same outer spike shape, deliver `ping`, and capture its `pong` result.

The trials may use provider-specific spike images, native CLIs, ACP adapters or
small temporary drivers. They need not share an internal SDK or prove the final
worker-control protocol. The comparable outer evidence is what matters:
provider and wrapper version, image identity, container creation, read-only
input, mounted credential source, request/correlation identity, provider
response, exit state, output collection and positive cleanup. An exact textual
`pong` is sufficient Work for this experiment.

Credentials are supplied at runtime from an operator-controlled read-only
provider such as `/run/baton/credentials`; they are never copied into an image,
repository, result, evidence file or log. Evidence records only the credential
provider/method and redacted failure category. If authentication, provider
network access, packaging or container execution fails, preserve the exact
redacted boundary failure rather than weakening isolation or moving the agent
onto the host and calling the trial successful.

Codex runs second so the Claude result can refine only shared spike mechanics,
not erase the independent Codex outcome. A provider-specific failure does not
silently skip the other trial unless it proves a shared prerequisite—such as
Docker or credential mounting—is unavailable. W17110 closes satisfying only
when both real agents return the correlated pong from inside their containers
and both containers clean up. A partial result remains valuable experiment
evidence but is not a satisfying two-provider proof.

## Independent review outcome — 2026-08-27

**Confirmed useful partial result:** both exact-version provider runtimes
package and start in unprivileged Docker images; the recorded runs exercise the
shared input/output/correlation wrapper and expose real Claude/Codex state-
directory differences relevant to W6634 and W6636. Neither returns pong, so the
result is correctly non-satisfying. Declining to select personal credentials
without operator nomination was correct.

**Observed, P0:** raw provider stdout is copied into `output.json` and then the
printed host report. Heuristic token redaction does not establish the pinned
rule that a mounted credential never enters a result, evidence file or log.

**Observed, P1:** a worker-authored truthy `pong` plus matching correlation is
accepted even for malformed text and a nonzero container exit. Cleanup can
also report `clean: true` after image removal is refused or the staged root
survives.

**Observed, P1 operational:** the offered personal credential files are
`1000:1000 0600`, while both images run as `65532:65532`; direct read-only
mounting does not make those files readable by the image user. A dedicated,
operator-nominated provider or explicit identity/delivery ruling is required.

Four additive daemon-free regressions reproduce the output, verdict and
cleanup defects. Full analysis: `review-2026-08-27T04-25-44Z.md`.

## Independent correction re-review outcome — 2026-08-27

**Confirmed corrected:** the original arbitrary-output, malformed/nonzero
pong, refused-image-removal and surviving-staged-root regressions are green.
Provider text no longer enters the durable host report, and the personal
credential files remain unmounted.

**Observed, P1:** allowlisting unknown result members is not validating the
closed result. A valid exact-pong document carrying the old raw `result` and
`pong` members is silently filtered and accepted.

**Observed, P1:** failed `docker ps` and `docker image ls` cleanup queries are
treated as empty survivor lists and still yield `clean: true`. Timeout kill and
removal statuses are recorded but likewise absent from the cleanup verdict.

**Observed, P1:** preflight reports nominated-provider readability but gates
READY only on presence. It also omits execute permission on a directory
provider itself, so a non-traversable directory can be reported readable.

The expanded nine-case daemon-free review gate has the retained four green and
five new failures. Full analysis: `review-2026-08-27T04-37-23Z.md`.

## Independent third-review outcome — 2026-08-27

**Confirmed corrected:** all nine retained reviewer regressions and six
implementer separation/control cases are green. Closed member names, cleanup
query outcomes, timeout cleanup, nominated-root readability and directory
traversal now fail closed as far as those cases reach.

**Observed, P1:** `_closed_shape()` validates names but not fact types or
exclusive branches. A textual byte count and a zero-exit exact pong carrying a
failure category both retain `closed_result_shape: true` and can satisfy.

**Observed, P1:** preflight collects exact Claude/Codex child-path descriptions
but gates READY only on the readable nominated root. A readable empty root
returns READY while neither provider path exists.

The twelve-case reviewer gate has the retained nine green and three new
failures. Full analysis: `review-2026-08-27T04-45-37Z.md`.

## Independent fourth-review outcome — 2026-08-27

**Confirmed corrected:** all twelve retained reviewer regressions and twelve
implementer separation/control cases are green. Published fact values and
exclusive branches are held, and readiness requires both exact provider
paths.

**Observed, P1:** the provider fact predicate performs dictionary membership
before holding the JSON value to a string. A JSON array raises `TypeError`
instead of refusing the closed shape and preserving a structured failure
report.

**Observed, P1:** cleanup removes and queries only the unique image tag. A
successful untag can leave the recorded immutable image identity under another
reference while `clean` and `satisfying` remain true. The identity must be
queried after every removal attempt.

The expanded fourteen-case reviewer gate retains twelve green and isolates one
failure plus one error. Full analysis:
`review-2026-08-27T04-55-30Z.md`.

## Independent fifth-review outcome — 2026-08-27

**Confirmed corrected:** all fourteen retained reviewer regressions and
fifteen implementer separation/control cases are green. The validator is total
over the reviewed arbitrary JSON case, and an image surviving by recorded
identity is detected after successful untagging.

**Observed, P1:** the new identity query treats every nonzero `docker image
inspect` result as absence, hard-codes its query status true, and omits that
status from `clean`. A query execution failure therefore produces satisfying
clean success when every other outcome is green.

The expanded fifteen-case reviewer gate retains fourteen green and isolates
one failure. Full analysis: `review-2026-08-27T05-04-38Z.md`.

## Independent sixth-review outcome — 2026-08-27

**Confirmed corrected:** all fifteen retained reviewer regressions and sixteen
implementer separation/control cases are green. Identity-query status 125 now
fails closed and participates in `clean`.

**Observed, P1:** the correction treats `docker image inspect` status 1 as a
successful observation of absence. The installed Docker CLI also returns 1
when it cannot connect to an explicit daemon socket, so query failure still
passes for absence and permits satisfying clean success.

The expanded sixteen-case reviewer gate retains fifteen green and isolates one
failure. Full analysis: `review-2026-08-27T05-12-00Z.md`.

## Independent seventh-review outcome — 2026-08-27

**Correction accepted:** all sixteen retained reviewer regressions and nineteen
implementer separation/control cases are green. The identity check distinguishes
the engine's narrow not-found diagnostic from observed reachability/permission
failures, and a successful full-id inventory can only add a survivor.

**No remaining source-visible harness defect** was found within the disposable
spike boundary. This signs off the harness, not W17110's satisfying outcome.
Neither real provider has returned pong and no operator credential was selected.

The remaining decision belongs to the operator: nominate providers readable by
uid 65532 and run Claude then Codex, or explicitly retain the current useful
partial result without claiming the two-provider proof. Full analysis:
`review-2026-08-27T05-20-04Z.md`.

## Approver credential-exposure decision — 2026-08-27

Authorize the two live W17110 trials through one operator-staged volatile
provider at `/run/baton/credentials`. The operator, not an agent, copies only
the existing Claude and Codex authentication files into exact entries `claude`
and `codex`. The provider root is tmpfs-backed; its directories are root-owned
and traverse-only, and each entry is owned by the fixed container identity
`65532:65532` with mode `0400`.

Each trial bind-mounts only its one entry, read-only, at the provider's native
credential-file path. The surrounding `.claude` or `.codex` state directory
remains private, writable and ephemeral inside that container. The personal
source files retain their ownership and mode. No credential is carried in an
environment variable, argv, image, repository, result, evidence or log, and no
whole personal state directory is mounted.

This authorization is limited to W17110, ordered Claude then Codex, through
the signed-off harness without `--keep`. A runtime that must rewrite or rotate
the read-only credential fails as an observed pilot result; it does not gain a
writable credential mount. After both trials stop and the engine proves cleanup,
the operator unlinks the two exact volatile entries and removes the now-empty
provider directories. No recursive deletion is authorized.

## Live preflight contradiction — 2026-08-27

**Observed:** the operator-staged provider has a root-owned `0711` carrier
directory and two `0400`, `65532:65532` exact credential files. The preflight
correctly reports both provider files present and readable by the container
identity, and sets both `usable_per_provider` values true. It nevertheless
prints `NOT READY` because its final predicate also requires uid 65532 to read
and list the carrier directory itself.

**Confirmed defect:** exact-file mode does not mount or consume the carrier
directory as a credential provider. It needs ancestor traversal, not directory
listing. Requiring the directory read bit contradicts the approved traverse-only
boundary and the preflight's own provider-specific observations. Do not work
around this by widening the carrier directory to `0755`.

The preflight must distinguish a directory mounted as the provider from a
directory that merely carries separately mounted exact files. For the approved
W17110 layout, readiness requires the engine plus both exact files readable by
uid 65532 and every ancestor traversable; the carrier directory need not be
listable. A non-traversable ancestor must still fail closed.

## Live access-probe clarification — 2026-08-27

For this bounded spike, a one-byte read inside the disposable container is an
approved empirical readability probe. `test -r` is aesthetically preferable,
but `head -c 1` is acceptable because it proves effective access after the
container engine's identity mapping rather than inferring access from the
host's metadata view. The byte must be discarded: it is never printed,
persisted, hashed, logged, returned, or semantically inspected, and the probe
container is removed. This authorizes no broader credential reading and does
not by itself define the eventual v12 production preflight contract.

## Full end-to-end proof remains mandatory — 2026-08-27

The earlier option to close or park W17110 as a useful partial result is
**superseded**. W17110 is the campaign's live proof gate and remains open until
both a real Claude container and a real Codex container return the correlated
exact `pong` through the approved input/output boundary, followed by proved
clean teardown. A categorized provider failure is valuable evidence and may
create corrective or follow-up Work, but it does not discharge this Work.

The current `credential-refresh-blocked` Claude result and `network` Codex
result therefore require correction and another bounded live trial. The proof
must exercise the real runtimes; substituting a fake agent, shell echo, host
runtime, or mere endpoint-reachability probe does not satisfy it.

## Independent eighth-review outcome — 2026-08-27

**Confirmed useful live result:** the operator approved and staged the exact
volatile files; preflight reached READY; Claude then Codex ran in order; both
closed reports are clean and correctly non-satisfying. Claude reported an
expired/refresh-related authentication failure and Codex a network failure.

**Observed, P1:** empirical file readability overrides rather than joins the
required ancestor-traversal gate. A `0700` carrier with observed-readable exact
files returns READY. A failed probe also falls back to positive host metadata
and returns READY, contrary to “a probe that did not run concludes nothing.”

**Observed, P1 evidence:** `credential-refresh-blocked` is inferred from
expiry/refresh wording without a write-denied signal, so the record has not
proved the read-only mount caused Claude's failure. Codex's network result also
does not prove exact-file credential delivery insufficient. Raw Codex wording
was persisted despite the closed-category rule.

**Observed, P1 operational:** `OPERATOR.md` retains recursive cleanup although
the approved decision permits only exact file unlinking followed by removal of
empty directories.

The expanded eighteen-case reviewer gate retains sixteen green and isolates
two preflight failures. Full analysis:
`review-2026-08-27T13-09-43Z.md`.

## Independent ninth-review outcome — 2026-08-27

**Confirmed:** the two preflight gates now compose correctly, a failed probe
cannot fall back to metadata, the prior causal and provider-text overclaims are
explicitly corrected, exact cleanup is documented, and all eighteen reviewer
plus twenty separation cases pass.

**Observed, P1 evidence:** the replacement `credential-write-denied` category
is still causal beyond its classifier. Generic `EACCES`, `permission denied`,
`cannot write`, and failed write/save/persist wording do not identify the
credential mount rather than input, output, workspace, HOME or another path.
Use a descriptive write-denied category unless a fixed credential-specific
signal exists.

**Observed, P1 operational:** `OPERATOR.md` still says no provider is nominated
and nomination is the only remaining cause, although the exact provider is
staged and two real rounds have run. `PLAN.md` also retains the superseded
decline/partial-close choice as an unmarked live action. The current truth is
the operator-designated refreshed-Claude retry, bounded Codex diagnosis, and
the mandatory two-pong closure gate.

**Observed, P2 evidence:** the new transcript says no repository state was
mutated while documenting source and dossier changes. Narrow that statement to
the actual trial boundary rather than retaining a false repository-wide claim.

Full analysis: `review-2026-08-27T13-21-40Z.md`.

## Independent tenth-review outcome — 2026-08-27

**Observed successful summary:** both real-provider rows report every host
verdict clause true, satisfying true, clean true and no provider text. The CA
bundle correction is present in both images, and all eighteen reviewer plus
twenty-four separation cases pass.

**Observed, P1 proof gap:** the durable proof retains only rendered booleans and
abbreviated image ids. It omits the safe exact `trial.py` reports carrying the
actual correlation ids, digest, exit statuses, closed publication, full image
identity, cleanup outcomes and survivor lists. Persist the exact stdout JSON
from the successful runs or repeat them; do not reconstruct values.

**Observed, P1 operational:** `OPERATOR.md` still says neither trial returned a
pong and directs both retries. The current operator action is only exact
volatile credential withdrawal. The files remain staged, and the approved
decision requires operator unlink/rmdir after proof and clean engine teardown
before terminal closure.

**Observed, P1 classifier:** credential-path and write-denied matches are over
aggregate stdout plus stderr. Separate diagnostics can therefore combine into
a false credential-causation label. Make the relation diagnostic-local or use
the descriptive category, with a cross-line negative control.

The managed reviewer could not query the Docker socket and did not escalate.
Full analysis: `review-2026-08-27T13-36-53Z.md`.

## Independent proof signoff — 2026-08-27

**Confirmed:** the exact provider-text-free stdout reports are durable and
independently recompute to satisfying for both real providers. Each host
correlation equals its published correlation, each digest equals independently
derived `sha256("pong")`, both exit layers are zero, both publications have the
closed nine-member shape, full image identities are present, every cleanup
command/query succeeded, survivor lists are empty, and every host verdict
clause plus `clean` and `satisfying` is true.

All eighteen reviewer and twenty-six separation cases pass. The classifier is
diagnostic-local and the operator document exposes only exact withdrawal as
live. Full analysis: `review-2026-08-27T13-41-07Z.md`.

The proof gate is discharged. The only remaining action is operator-owned
withdrawal of the two exact staged credential files and empty-directory
removal; terminal satisfying closure follows that confirmation. No recursive
deletion is authorized.

## Private-development credential retention — approver decision 2026-08-27

**Confirmed:** on this private, operator-owned development box, the exact
`/run/baton/credentials/claude` and `/run/baton/credentials/codex` files may
remain after W17110 for later trials. This explicitly supersedes the earlier
W17110 requirement to unlink those entries and remove their empty carrier
directories before satisfying closure. The completed two-provider proof, not
credential withdrawal, is the terminal gate.

This is a narrow development-fixture exception, not the production credential
lifecycle. The entries remain operator-managed, owner-only (`0400`), and
read-only to each explicitly launched trial. They are never copied into an
image or into Baton durable state, results, events, labels, command lines, or
logs. A later trial must still run preflight and restage or refresh an expired
credential when necessary. Multi-user and production runtimes do not inherit
this retention policy.
