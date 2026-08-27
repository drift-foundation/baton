# Finding: seal OCI output and assignment-scoped credentials

Promoted implementation record for the fourth bounded child of W5. Its ledger
Work is contained by W5; this dossier is top-level under the maximum-depth
promotion rule.
Canonical Work: W6634.

## Confirmed boundary

Implement the worker-side/adapter-side sealed artifact collector and ephemeral
credential delivery that the manager-owned output and section-13 receivers can
consume. Credentials are assignment-scoped, non-persistent, absent from image
layers, argv, labels, logs, durable store and collected output. Output is read
only after quiescence, never overlaps an input or another output, contains only
declared bounded regular files, and is copied into immutable staging before its
manifest/count/bytes/digest observation is emitted.

The manager remains the only authority that accepts an observation, settles an
attempt, applies retention or authorizes cleanup. This component neither
invents manager envelopes nor equates engine status with sealed output.

## Acceptance

- Missing, undeclared, linked, special, changing, over-count and over-byte
  outputs refuse without an accepted partial artifact.
- Freeze/copy/hash is ordered after quiescence and detects replacement races.
- Credential injection and teardown leave no value in diagnostic/durable or
  artifact surfaces, including failure and cancellation paths.
- Restart/retry is idempotent by manager operation/artifact identity.
- Handoff uses only the separately owned manager output/security contracts.

The implementer creates and exclusively owns `PROGRESS.md` when claimed.

## Independent review — 2026-08-26

**Observed:** `sealed_result` does not copy an output into immutable staging.
It measures the declared directory under the live assignment workspace, chmods
that same directory, measures it again, and publishes the workspace path as
the artifact locator. `collected_result` later measures that live path again
and publishes it again as the custody locator. Host authority can therefore
rewrite the bytes after freeze, changing the digest and byte count returned by
collection. The accepted boundary above explicitly requires the copy to
immutable staging before the observation is emitted; chmod on the source is
not that custody boundary.

**Confirmed:** the additive regression
`test_collection_uses_immutable_custody_not_the_live_workspace` rewrites the
workspace after a successful freeze. Collection returns a different digest
from the frozen artifact. This also disproves the implementation comment that
collection measures nothing new and leaves restart/retry dependent on mutable
assignment state.

**Observed:** declarations are made unique only by output name. Their paths
are accepted as unrelated text at construction, so two names can declare the
same directory or one can declare a directory nested inside the other. That
violates the confirmed rule that an output never overlaps another output and
can freeze one tree while a later declaration still expects to traverse part
of it.

**Confirmed:** the additive regression
`test_two_names_cannot_alias_or_nest_the_same_output_tree` demonstrates both
same-path and ancestor/descendant declarations are accepted.

**Open:** no credential source/reference, delivery target, lifecycle owner, or
teardown mechanism is frozen in this record or in W6630. The current OCI
adapter deliberately has no secret-bearing environment, argv or mount
surface. The implementer must not invent that security boundary while filling
in code.

**Proposed for decision:** materialize credential bytes only in a
manager-owned, assignment-private ephemeral file, bind-mount that file
read-only at one fixed container path, and keep the live-secret registry in
force from materialization through output leak checks and teardown. Teardown
must cover success, failure, cancellation and restart without persisting the
bearer value. This is decision support, not an approved mechanism; it also
requires explicit ownership of the new ephemeral root and orphan cleanup.

## Approver decision — 2026-08-26

The proposal above is approved with a fixed read-only provider root at
`/run/baton/credentials` and the following closed boundary:

- An assignment names one or more authorized logical credential slots. It
  never carries bearer bytes, a host path or an arbitrary provider reference.
- The trusted runtime profile maps each slot to a credential provider and its
  opaque reference. The manager resolves that mapping for the assignment and
  materializes one assignment-private file per slot under manager-owned
  volatile storage. The adapter exposes only the fixed
  `/run/baton/credentials` root to the container, read-only; closed slot names
  determine its entries.
- Bearer bytes are absent from argv, environment, image layers, labels, logs,
  durable state, protocol Events and output metadata. Durable state may name
  the logical slot, provider identity and lifecycle state, but never the
  bearer or a reusable bearer digest.
- The manager registers the live bearer before worker access and retains that
  registry through quiescence, immutable output staging, leak checks,
  container removal and credential-root cleanup. It discards the in-memory
  bearer only after teardown is proved.
- Success, failure and cancellation use the same ordered teardown. A manager
  restart may recover the assignment only when it proves the attempt,
  container, mount and ephemeral-root identities agree. Otherwise it fails
  closed, accepts no output, stops the worker and performs bounded orphan
  cleanup without reading or publishing bearer bytes.
- Cleanup uncertainty cannot be reported as successful settlement or a free
  worker slot. The frozen output may remain quarantined for an operator, but
  the credential lifecycle stays unresolved until teardown is proved.


## Credential delivery boundary — decided 2026-08-26

The review asked for this to be CHOSEN and PINNED before implementation rather
than raised again, and it is right that a third round of asking would be worse
than a decision somebody can overrule. This is the decision, with the
constraints it had to satisfy stated so a reviewer can attack the reasoning
rather than the outcome.

**What constrained it.** `run_vector` composes no environment and no secret;
the sandbox is `--read-only` with one writable mount; §13 bars the value from
argv, labels, logs, the durable store and the collected output; and the
container runs as a fixed non-root user with every capability dropped.

- **argv is out.** Every process on the host can read another's command line,
  and the vector is a golden test fixture besides.
- **Labels are out.** Anything that can list containers can read them, and
  reconciliation reads them back after a restart, which is exactly the
  durability §13 forbids.
- **The image is out.** A layer is content-addressed and shared.
- **An environment variable is out**, and this is the one worth arguing.
  `--env` puts the value in the engine's own container inspection, which
  `observe` reads and which any operator with engine access can dump; the
  value then outlives the process in the engine's metadata store.

**Decided: a private ephemeral file, bind-mounted read-only, removed at
teardown.**

1. The manager writes the value to a file it owns under the assignment's
   private storage, mode `0600`, on a filesystem the worker cannot otherwise
   reach.
2. `run_vector` gains one `--mount type=bind,...,readonly=true` naming that
   file at a FIXED in-container path. The path is a constant of this contract,
   not an operand: a per-assignment path would be one more thing a context
   could infer wrongly, and the worker is told where to look by the input
   manifest's own conventions.
3. The mount source is the file, not its directory, so nothing else in that
   directory is reachable.
4. **Teardown owns removal**, and cleanup already exists: the value is deleted
   when the runtime is destroyed, and the deletion is not conditional on the
   worker having behaved. `authorize_cleanup` is the owner because it is the
   one act that runs on every ending, including a cancellation.
5. **Nothing reads it back.** This manager writes the file and deletes it; it
   never re-reads the value, never puts it in an observation, and never
   compares it. §13's walk covers the write.

**What this deliberately does not do.** It does not add a credential operand to
any frozen worker-control body, because no frozen body has one and inventing
one is the boundary violation the intake Job already refused for retention
policy. The credential is a RUNTIME delivery fact, not protocol vocabulary.

**Open to being overruled on one point.** The fixed in-container path is a
convention this record invents, and a reviewer may prefer it named in the
runtime profile instead. I chose the constant because a path an assignment can
vary is a path a context can be pointed at wrongly, which is the same class of
defect as W14828's launcher drift.

## Supersession clarification — approver message 16691, 2026-08-26

The preceding "Credential delivery boundary — decided" section records the
implementer's pre-approval proposal. **It is superseded wherever it conflicts
with the later approver ruling in message 16691 and the earlier "Approver
decision" section.** In particular:

- delivery is not one unnamed bearer file at one file target; an assignment
  names closed logical slots, the trusted runtime profile maps each slot to a
  provider and opaque reference, and the manager materializes one private file
  per authorized slot;
- the fixed container contract is the read-only directory root
  `/run/baton/credentials`, whose entries are determined by those closed slot
  names; assignments carry neither bearer bytes, host paths nor arbitrary
  provider references; and
- teardown is the ordered credential lifecycle through output leak checks,
  container removal and volatile-root cleanup. `authorize_cleanup` alone is not
  permission to discard the live-secret registry before those facts are
  proved. Restart adopts only an exact attempt/container/mount/root match and
  otherwise fails closed into bounded orphan cleanup.

The old proposal remains as chronological decision history; it is not an
alternative live mechanism.

## Second independent re-review — 2026-08-26

**Confirmed corrected:** declared output paths now receive the frozen
canonical-relative-path rule at construction; an exact retry of a present
output can replay custody after the live workspace is gone; and the sealing
receivers now have declared boundary probes. The 23 pre-existing sealing cases
pass, as do the focused OCI and dependency modules. The prior W6634
owned-but-unprobed entries are absent from the inventory's remaining set; the
aggregate gate remains red on concurrent handshake, intake and OCI changes.

**Confirmed P1:** custody has no committed-result marker. `sealed_result`
treats `os.path.isdir(custody/output-name)` as proof that the output settled.
A restart after only one file was copied therefore publishes that partial
directory as the complete artifact instead of completing or refusing the
ambiguous staging. The additive
`test_a_partial_custody_directory_is_not_a_settled_replay` reproduces a
two-file live output being answered as a one-file result.

**Confirmed P1:** a `missing-optional` answer has no custody representation at
all. If the same freeze operation is retried after that output appears in the
workspace, the adapter changes the settled answer from `missing-optional` to
`present`. The additive
`test_an_exact_retry_preserves_a_missing_optional_answer` reproduces it.
Together these show that an artifact directory is neither necessary nor
sufficient proof of a committed result response. Restart/retry needs one
operation-bound committed answer above all current workspace and partial
staging reads.

**Confirmed P1 remains:** the approved credential lifecycle is still wholly
absent. The current test contract states that credential delivery is not
present, and source has no logical slots, profile/provider resolution,
assignment-private volatile credential root, fixed
`/run/baton/credentials` mount, live-secret registration through artifact
content checks and proved teardown, restart adoption, or bounded orphan
cleanup.

Exact review and evidence:
`review-2026-08-26T14-16-08Z.md` and
`evidence/review-2026-08-26T14-16-08Z.txt`.

## Third independent re-review — 2026-08-26

**Confirmed corrected:** a publish-last `sealed.json` now represents the whole
answer, including missing-optional outputs. Partial artifact directories are
restaged rather than replayed, and the prior two retry regressions plus the new
frozen-custody/no-record window case pass. All 26 pre-existing sealing cases
pass.

**Confirmed P1:** publication is last but not atomic. `_commit` opens the final
`sealed.json` path directly and writes into it. A stopped writer can therefore
leave an existing empty or partial record; `_committed_result` treats existence
as settlement and passes the bytes to raw JSON decoding. The additive
`test_an_incomplete_committed_record_is_not_replay_evidence` gets an unhandled
`JSONDecodeError` from a zero-byte interrupted record. A final record must
become visible atomically only after its complete bytes exist, and replay must
own and validate the adopted record rather than trust file existence.

**Confirmed P1:** replay is selected by attempt custody alone, not by an exact
freeze operation. After one successful seal, a request carrying a different
operation id and signature receives the first operation's answer instead of a
contract refusal. The additive `test_replay_requires_the_same_freeze_operation`
reproduces this. The committed response must be bound and compared to the
incoming operation and immutable assignment/result identity before replay.

**Confirmed P1 remains:** the approved credential lifecycle is still wholly
absent, as the implementer's latest progress explicitly records. No logical
slots, profile/provider resolution, volatile credential files, fixed
`/run/baton/credentials` root mount, live-secret lifecycle through output leak
checks and proved teardown, or restart/orphan handling exists.

Exact review and evidence:
`review-2026-08-26T14-32-27Z.md` and
`evidence/review-2026-08-26T14-32-27Z.txt`.

## Fourth independent re-review — 2026-08-26

**Confirmed corrected:** the committed sealed-result record is now atomically
published, owned, digest-validated and bound to the exact freeze operation and
immutable result identity. Both prior replay regressions pass, as do all 30
sealing cases and the 357-case adjacent focused set.

**Confirmed P1:** restart recovery is not connected to engine mount facts.
`CredentialHome.adopt` compares a self-authored lifecycle record with caller
ids and local paths, while `OciAdapter.observe` reads only runtime identity and
state. No production path calls adoption or orphan cleanup. The implementation
therefore cannot prove that the live container's mount sources/targets and
ephemeral root agree, or execute the approved stop-worker and bounded cleanup
path on disagreement.

**Confirmed P1:** three driven lifecycle gaps remain. An engine-declined start
strands its root and live-secret registration; a later-slot adoption refusal
leaves earlier bearers registered without a returned owner; and a single short
`os.write` is treated as complete credential delivery. Three additive
regressions reproduce these failures.

Exact review and evidence:
`review-2026-08-26T16-33-05Z.md` and
`evidence/review-2026-08-26T16-33-05Z.txt`.

## Fifth independent review — 2026-08-26

**Confirmed corrected:** the three prior credential regressions pass. Complete
writes, transactional adoption registration, declined-start cleanup and
engine-observed exact single/multi-slot recovery are present. The prior 61-case
credential module and 357-case adjacent set are green.

**Confirmed P1:** a Delivery for attempt-1 can start a runtime labelled as
attempt-2; a pre-engine `run_vector` refusal still strands its root and registry
entry; observed mount agreement accepts a bind shadowing the fixed credential
root and duplicate binds to one recorded target; and per-attempt recovery calls
broad orphan cleanup with an empty live set, deleting another attempt's live
root. Five additive regressions reproduce these gaps.

**Confirmed unresolved dependency:** W14251's active review found the output
publication contract contradictory and explicitly requires W6634 revalidation.
The worker-published `/output/output.json`, schema `resultManifest`, and this
Work's manager-custody `sealed.json` are not yet one coherent writer/name/
completion/receipt contract.

Exact review and evidence:
`review-2026-08-26T18-20-01Z.md` and
`evidence/review-2026-08-26T18-20-01Z.txt`.

## Sixth independent review — 2026-08-26

**Confirmed corrected:** all five prior credential regressions pass; the
67-case credential baseline and 359-case adjacent gate are green.

**Confirmed P1:** the manager does not validate `/output/output.json`.
W6634 accepts an optional caller-supplied `completion_manifest_digest` and
binds that claim into its receipt, but it neither owns the worker document nor
compares it with the input manifest. W14251 assigns that manager-side duty here
and remains open with changes requested.

**Confirmed P1:** post-engine answer and runtime-identity refusals occur outside
the guarded start block and bypass the explicit credential lifecycle decision.
An additive regression leaves the root and bearer live while returning a
refusal that does not say the lifecycle is unresolved.

**Confirmed P1:** proved failed recovery removes the volatile root but leaves
its live lifecycle record, so later recovery cannot converge to absence.

**Confirmed P1:** the fifth evidence's boundary inventory still identifies six
orphan owners in W6634's own `sealing.py`, despite claiming zero outstanding
entries.

Review and evidence:
`review-2026-08-26T19-35-17Z.md` and
`evidence/review-2026-08-26T19-35-17Z.txt`.

## Seventh independent review — 2026-08-26

**Confirmed corrected:** the manager now opens and validates the worker
completion envelope, holds its output answers against the declarations,
derives the digest bound into the manager receipt, routes post-create start
refusals through the credential lifecycle, removes the lifecycle record with a
proved stale root, and resolves this Work's six boundary-inventory orphans.
All 105 pre-existing sealing and credential cases pass; the 432-case adjacent
focused gate is green with one skip.

**Observed P1:** exact committed replay reads the live worker completion
envelope first. Removing `/output/output.json` after successful manager custody
makes the same freeze operation refuse instead of returning its committed
receipt. The receipt already binds the validated completion digest; transient
worker state is not a new operand of an exact retry.

**Observed P1:** the completion reader uses `os.path.isfile` followed by
ordinary `open`, both of which follow a worker-created symlink. A valid
completion document planted outside the writable root is accepted through an
`output.json` symlink, turning the fixed worker path into a host-side arbitrary
path read and violating the no-linked-output boundary.

**Observed P1:** the completion document's `assignment_ref` is validated only
for standalone shape. A valid envelope naming generation 2 is accepted while
the freeze request and adapter settle generation 1. Holding the completion
envelope against the exact input assignment requires this identity relation,
not only output declaration equality.

**Observed P1:** credential recovery with a live lifecycle record and zero
matching runtimes cannot converge. `_recovery_failed` defines proved absence as
`bool(stopped) and all(stopped)`, so an empty exact engine result is treated as
uncertainty; the stale volatile root and lifecycle record remain and every
later recovery repeats the same unresolved answer.

Four additive regressions reproduce these findings. Review and evidence:
`review-2026-08-26T22-22-53Z.md` and
`evidence/review-2026-08-26T22-22-53Z.txt`.

## Operator-requested design checkpoint — 2026-08-26

Stop after the seventh-review corrections and return W6634 for approver design
review before any eighth implementation/review cycle. This is not an assertion
that the active turn is wedged; it is a scope-control decision after repeated
P1 discovery showed that the Work's boundary is too broad to keep repairing by
iteration without re-examining the design.

W6634 currently couples two independently difficult systems:

1. immutable output validation, staging, replay and custody; and
2. assignment-scoped credential materialization, Docker mount agreement,
   leak prevention, teardown, restart adoption and orphan recovery.

Those systems then cross at quiescence and settlement, multiplying every
success, refusal, retry, cancellation, restart and uncertain-engine path. The
current implementation/test surface is approximately 6,668 lines across
`sealing.py`, `credentials.py`, `oci.py` and their three focused test modules;
the dossier itself has accumulated seven independent review rounds in one day.
That is evidence that the nominally bounded child is carrying multiple Jobs.

Before more implementation, the approver will decide:

- whether output custody and credential delivery/recovery become separate
  independently reviewable Work;
- the minimum credential/authentication boundary needed for the immediate
  real-Claude and real-Codex Docker spike;
- which restart, reconciliation and orphan-recovery guarantees belong to the
  later W6636 lifecycle matrix rather than this component; and
- whether the current seventh-correction tree is retained as provisional
  evidence, narrowed for acceptance, or replaced behind a cleaner interface.

The implementer records a concise current-contract and residual-risk summary,
then passes W6634 to `baton.ops`. No opportunistic repair of the standing shared
boundary-inventory baseline and no eighth code iteration is authorized before
that ruling. W17110 no longer depends on W6634 and may proceed independently
once its obsolete dependency edge is removed.

## Reviewer design-checkpoint packet — 2026-08-26

This is coordination evidence for the requested approver checkpoint, **not an
eighth independent review** and not sign-off on the seventh correction.

The implementer supplied complete seventh-correction evidence but did not add
a separate concise checkpoint summary to `PROGRESS.md`. Rather than reopen an
implementation/review cycle, the reviewer has distilled the existing progress
and evidence in `evidence/design-checkpoint-2026-08-26.md` and routes that
packet unchanged to `baton.ops`.

The current tree remains **provisional evidence**. The focused report is 110
sealing/credential cases green and 437 adjacent cases green with one skip;
the aggregate remains red only on six standing shared-inventory failures and
eleven W6633 worker-image/container failures. These are implementer-reported
results from `evidence/w6634-2026-08-26-seventh-review.txt`, not a new reviewer
execution.

**Reviewer recommendation for the ruling:** split future acceptance into an
output-custody Work and a credential-delivery Work, and put restart adoption,
engine reconciliation and orphan convergence into W6636's lifecycle matrix.
Retain the current code as provisional material for those Works rather than
deleting or declaring it accepted. The immediate Docker spike should require:

- worker completion validation, exact assignment/declaration comparison,
  immutable staging, atomic manager receipt and exact replay;
- fresh-run authorized credential-slot materialization, fixed read-only mount,
  live-secret registration through output leak checks, and teardown that fails
  closed unless container and volatile-root absence are proved; and
- no claim that manager restart/adoption or broad orphan recovery is certified
  by the spike. Those paths remain fail-closed and move to W6636 for systematic
  lifecycle verification.

The newly approved W19784 `/input/assignment.json` contract is an upstream
integration, not an alternate identity source here. W6634 must continue to
compare the worker completion identity with the manager-owned exact assignment
before custody mutation.

**Operational finding:** the checkpoint directs removal of W17110's obsolete
dependency on W6634, but `baton.codex` cannot mutate a `baton.impl` consumer.
The canonical `unblock work=W17110 on=W6634 ...` operation refused because the
reviewer is not a resolved handler of `baton.impl`. The approver or implementer
must remove that edge; no store or source workaround was attempted.

## Approver closure ruling — 2026-08-27

W6634 closes **unsatisfying**. Seven implementation/review cycles did not
produce an independently accepted deliverable, and continuing the combined
output-custody, credential-delivery and recovery boundary would not advance the
immediate Docker proof. The current source and focused evidence may remain as
provisional material, but neither is certified by this Work and no downstream
Work may treat W6634's terminal state as acceptance of that implementation.

There is no eighth correction or review round. If the spike later proves that
one of these capabilities is necessary, new narrowly bounded Work must
revalidate and deliberately adopt or replace the provisional code. Restart,
reconciliation and orphan recovery remain W6636 concerns. W17110 is independent
of W6634.

## Post-spike successor authorization — 2026-08-27

The W17110 proof and W6636 integration round have now established that both
capabilities are required. The earlier “future only if required by the spike”
condition is satisfied. Authorize two NEW, independently reviewed successor
Works: one for output custody and one for fresh-run credential delivery.

W6634 remains terminal non-satisfying and is never reopened or reinterpreted
as acceptance. Each successor revalidates and deliberately adopts, replaces,
or removes provisional W6634 code within its own boundary. Output custody owns
completion validation, exact assignment/declaration comparison, immutable
staging, atomic receipt publication and replay. Credential delivery owns
authorized slot materialization, fixed read-only mounts, live-secret leak
checks and fail-closed teardown of its volatile material.

Their shared start/destroy settlement crossing belongs explicitly to W6636,
the lifecycle integration Work. W6636 also retains restart adoption, engine
reconciliation and orphan convergence. Neither successor may silently certify
that shared integration surface.
