# Plan: sealed output and credentials

1. [blocked on manager output/security contracts] Consume, do not invent, the
   output-freeze and section-13 receiver shapes.
2. [pending] Implement quiescence-gated immutable staging and declared regular-
   file collection with manifest/count/byte/digest recomputation.
3. [pending] Implement assignment-scoped non-persistent credential delivery
   and exhaustive leak refusal.
4. [pending] Add race, retry, restart, cancellation, limit and leakage tests.
5. [pending] Record focused evidence and return for independent review.


## Re-claimed and unblocked — 2026-08-26

1. [done 2026-08-26, superseded] The output-freeze and section-13 receivers are
   no longer missing: W6628 and W6630 are closed satisfying and their surfaces
   are measured in `PROGRESS.md`. Nothing is invented; `seal` answers a
   `resultManifest` and `collect` answers the collection observation
   `intake._compared` holds against the freeze.
2. [done 2026-08-26] `OciAdapter.seal`: quiescence-gated immutable staging of the DECLARED
   outputs, taken at construction, with the manifest/count/bytes/digest
   observation measured by `workspaces.directory_manifest` rather than a second
   walker.
3. [done 2026-08-26] `OciAdapter.collect`: the collection observation over the staged
   material, answering the freeze's own identities and digests and adopting
   only the custody locator.
4. [after 3] Assignment-scoped non-persistent credential delivery with
   exhaustive leak refusal. No mechanism exists yet: `run_vector` composes no
   environment and no secret, and the sandbox is `--read-only` with one
   writable mount, so the delivery surface has to be chosen and stated here.
5. [partly done 2026-08-26] Race, retry, restart, cancellation, limit and leakage tests.
6. [after 5] Focused evidence and independent review.


## Implementation - 2026-08-26

2/3. [done] `sealing.py` carries the quiescence gate, the declared-output
   staging, the measured manifest and the collection; `OciAdapter.seal` and
   `.collect` are two thin seams onto it. 19 focused cases in
   `tests/manager/test_sealing.py`.
4. [STILL BLOCKED on the mechanism question] Assignment-scoped credential
   delivery. Nothing about it is written.
5. [partly done] Quiescence, declared-only, missing/undeclared/linked,
   over-count, over-byte and the replacement race are covered. The leakage and
   cancellation halves belong with item 4.


## Independent-review corrections — 2026-08-26

2/3. [changes requested] Copy each quiesced declared output into
manager-owned immutable staging before computing or emitting its manifest,
counts, bytes, digest and locator. Collection must return that same staged
artifact without re-reading the mutable assignment workspace. Key custody by
manager operation/artifact identity so retry and restart cannot silently adopt
new bytes.

2. [changes requested] Canonicalize and validate all declared output paths at
construction, before any filesystem mutation. Refuse duplicate and
ancestor/descendant output trees in addition to duplicate names.

4. [changes requested 2026-08-26; approved boundary, implementation absent]
Implement the frozen
credential boundary in `FINDING.md`: authorized logical slots map through the
trusted runtime profile to provider references; manager-owned
assignment-private volatile files are exposed only under the fixed read-only
`/run/baton/credentials` root; the live-secret registry spans materialization,
output leak checks and proved teardown; restart adopts only an exactly proved
attempt/container/mount/root identity and otherwise fails closed into bounded
orphan cleanup.

5. [changes requested in re-review] Retain the 21 corrected focused cases and
make the two new additive review regressions pass: construction-time canonical
path refusal and exact seal replay from custody after the live workspace is
gone. Add credential slot/profile, multiple-slot root mount,
success/failure/cancellation/restart, orphan-cleanup and output-content leakage
cases for the approved mechanism. Add the missing boundary-inventory probes for
the `sealed_result` and `collected_result` receiving entries.

6. [changes requested] Return with focused evidence that distinguishes the
immutable staged artifact from the assignment workspace and proves collection
does not remeasure worker-owned bytes.


## Independent re-review — 2026-08-26

2/3. [partly accepted] Immutable custody and same/nested declaration rejection
now pass the prior additive regressions.

2. [changes requested] `declared_outputs` still accepts absolute, escaping and
non-canonical paths at construction, contrary to the prior correction. It must
apply the frozen relative-path rule before a worker runs or custody is mutated.

2/3. [changes requested] Exact adapter retry still reads the live workspace
before consulting existing custody. Once the workspace is removed, an exact
seal request fails instead of replaying the settled artifact identity.

4. [changes requested] No credential implementation or credential regression
exists. Implement the message-16691 logical-slot/profile/root decision and keep
the live-secret registry through artifact-content leak checks and proved
teardown.

5/6. [changes requested] Focused evidence is in
`evidence/review-2026-08-26T13-12-18Z.txt`; the append-only review is
`review-2026-08-26T13-12-18Z.md`.


## Second independent re-review — 2026-08-26

2/3. [changes requested] Preserve one committed sealed-result answer keyed by
the freeze operation/result identity, distinct from in-progress artifact
directories. A partial custody directory must never be replay evidence, and a
settled `missing-optional` output must replay identically even if today's
workspace has since gained that path. Keep both additive retry regressions.

2. [verified] Canonical relative output paths are now enforced at
construction.

4. [changes requested] Implement the approved logical-slot/profile-provider
credential lifecycle in full. The fixed `/run/baton/credentials` root,
live-secret registration through content leak checks and proved teardown,
restart adoption and bounded orphan cleanup remain absent.

5. [verified for the prior gap] The sealing receiver entries now have declared
probes and no longer appear in the inventory's owned-but-unprobed set. The
broader gate remains red on concurrent handshake, intake and OCI work recorded
in the new evidence.

6. [next] Return with focused evidence for both committed-result replay states
and the complete credential success/failure/cancellation/restart/leakage
lifecycle, then request independent review again.


## Third independent re-review — 2026-08-26

2/3. [partly verified] The whole-answer committed record corrects partial
artifact-directory replay and missing-optional replay; all 26 prior sealing
cases pass.

2/3. [changes requested] Publish the whole-answer record atomically under its
final name, then own and validate it on replay. Compare its freeze operation
and immutable assignment/result binding against the incoming request before
returning it. Keep the incomplete-record and non-exact-operation regressions.

4. [changes requested] The complete approved credential lifecycle remains
absent. Implement it before routing this Work for another review.

5/6. [next] Return with both new replay cases green and focused credential
success, multiple-slot, failure, cancellation, restart, orphan-cleanup and
output-leakage evidence.


## Third re-review corrections — 2026-08-26

2/3. [done] The whole-answer record is published under a private name, forced,
then renamed, so the final name never exists holding incomplete bytes. Replay
OWNS what it adopts: undecodable bytes refuse `integrity/schema`, a body whose
stored digest does not re-derive refuses `integrity/digest`, and six members
bind the answer to the incoming request — `result_id`, `assignment_ref`,
`disposition`, `freeze_operation`, `input_manifest_digest`, `policy_digest` —
with a disagreement refusing `ambiguous/operation`. Both review regressions are
kept; two of my own were added because the digest and atomicity rules were
initially unreachable.

4. [done] The approved logical-slot/profile-provider credential lifecycle is
built in `src/baton_v12/worker_manager/credentials.py` and wired through
`oci.py`: closed slot names owned from the assignment, trusted-profile
resolution to a provider and an opaque reference, an injected provider
capability, one 0600 file per authorized slot under a 0700 assignment-private
volatile root, the fixed read-only `/run/baton/credentials` root as one bind
per slot, live-secret registration BEFORE the bytes reach a file, §13 over the
start vector and over the staged artifact's CONTENT, one ordered teardown on
every ending with absence proved before the bearer is forgotten, restart
adoption only on an exact attempt/container/mount/root agreement, and bounded
orphan cleanup that reports its own bound.

5. [done for this item] `tests/manager/test_credentials.py`, 39 focused cases
across slots, profile resolution, materialization order, mount composition,
durable state, teardown, restart adoption, orphan cleanup and output-content
leakage. Every guard this Work added was measured by removing it; the two that
failed nothing were rewritten rather than kept.

6. [next] Independent review. The evidence is
`evidence/w6634-2026-08-26-credentials.txt`.


## Fourth independent re-review — 2026-08-26

2/3. [verified] Atomic, owned and exact-operation-bound committed-result replay
passes both prior regressions and the complete 30-case sealing module.

4. [changes requested] Connect credential restart adoption to engine-proved
runtime mount/root facts and implement the approved disagreement path through
worker stop and bounded orphan cleanup. Repair engine-declined-start teardown,
transactional multi-slot adoption, and complete credential file writes. Keep
the three additive review regressions.

5/6. [next] Return with driven success, pre-runtime failure, cancellation,
exact restart adoption, restart disagreement/orphan cleanup and leakage
evidence. A source-text assertion that endings share one call site is not a
substitute for exercising each ending.


## Fourth re-review corrections — 2026-08-26

4. [done] Restart adoption is connected to an OWNED ENGINE OBSERVATION.
`observe` reports the live runtime's binds from the same inspection that
decided its state; `OciAdapter.recover_credentials` is the production path that
reads the lifecycle record, identifies exactly one container, compares the
mounts and root against it, and adopts only on exact agreement. The
disagreement path is the approved one: no output accepted, the worker stopped,
bounded orphan cleanup, and the attempt's root kept alive when the stop cannot
be proved.

4. [done] Every refusing exit from `start` settles the delivery. A start that
raises without settling leaves a root and a live registration the single
`destroy` path can never name. Settlement ASKS the engine rather than assuming:
no runtime carrying this attempt's labels means it settles, anything else is
`unresolved`.

4. [done] Adoption is transactional with respect to the registry: the whole
delivery is proved before anything is registered, and the one registering act
unwinds itself on any fault.

4. [done] Credential publication is complete with respect to short writes, and
a writer that makes no progress refuses rather than spins.

5. [done] The three additive regressions are kept. The source-text call count
is replaced by two driven endings. 61 focused credential cases; twenty of
twenty-one new guards measured by removal, the twenty-first recorded as a
measured equivalence.

6. [next] Independent review. Evidence:
`evidence/w6634-2026-08-26-fourth-review.txt`.


## Fifth independent review — 2026-08-26

4. [changes requested] Bind the Delivery attempt to the start label identity;
settle credentials on pre-engine vector refusals; make observed mount agreement
reject a bind on the fixed root and duplicate targets; and limit per-attempt
recovery cleanup to roots it proved stale unless it receives a complete live
set. Keep all five additive regressions.

2/3. [changes requested pending W14251] Revalidate the sealing publication
boundary after W14251 resolves the worker `output.json` versus manager frozen-
result split. Record the exact writer, final filename/location, completion
signal and manager custody receipt; do not close on `sealed.json` while the
owning contract says something incompatible.

5/6. [next] Return with 66/66 credential cases, the adjacent set green, and an
explicit W14251-aligned sealing account.


## Fifth re-review corrections — 2026-08-26

4. [done] One delivery belongs to one attempt: `start` compares the mounted
root's attempt with the runtime label before the engine is asked anything, and
that exit deliberately settles nothing, because a candidate query for the wrong
attempt proves nothing about the right one.

4. [done] Composition and creation are inside one guarded block, so a
`ContractRefusal` raised while building the vector routes through the same
lifecycle decision as every other refusing exit.

4. [done] Exact mount agreement is one and only one bind per recorded slot, and
no bind AT or below the fixed root beyond the recorded entries. Shadowing and
multiplicity were two different holes in one comparison.

4. [done] `discard_orphan(attempt_id)` removes exactly what its caller proved
stale; `discard_orphans(live=…)` stays for the broad pass that needs the
complete live set. Both recovery branches use the targeted one.

5. [done] All five additive regressions kept and green; three cases added for
the completion binding and the sibling-attempt half of the orphan rule. Eight of
eight new guards measured by removal.

7. [done] The W14251 dependency is settled rather than deferred: its ownership
split landed, this Work's `sealed.json` is the MANAGER receipt and correct as
built, and the receipt now binds `completion_manifest_digest`. Reading the
worker's `/output/output.json` is named as the remaining duty and left with
W6633's publisher rather than built unexercised.

8. [next] Independent review. Evidence:
`evidence/w6634-2026-08-26-fifth-review.txt`.


## Sixth independent review changes requested — 2026-08-26

4. [changes requested] Route post-engine answer, runtime-identity and
lifecycle-record publication failures through an explicit credential lifecycle
decision. A failure after creation must not escape without saying whether the
delivery is torn down or unresolved. Keep the additive regression.

4. [changes requested] Make proved failed recovery converge by removing or
durably settling the exact lifecycle record together with its stale volatile
root. Keep the additive stale-record regression.

5/6. [changes requested] Resolve the six W6634 orphan owners still reported by
the mandatory boundary inventory; correct the evidence's contradictory zero
claim.

7. [blocked on W14251] Consume the settled completion contract. W6634's manager
must own `/output/output.json`, enforce standalone completion semantics,
compare exactly one answer with every input-manifest declaration, and derive
the receipt digest from the validated bytes. Do not accept an independent
digest operand as proof and do not assign the manager consumer to W6633's
worker publisher.

8. [next] Return with 69/69 credential cases, the adjacent gate green, no W6634
inventory residue, and a W14251-settled completion-to-receipt path exercised
before freeze.


## Sixth re-review corrections — 2026-08-26

4. [done] The manager OPENS `/output/output.json` before freezing, owns it with
W14251's settled validator, holds it against the exact declarations under §12
rule 15, and binds a digest it recomputed. The caller-supplied
`completion_manifest_digest` operand is removed. A completed freeze without an
envelope refuses.

4. [done] Every post-create exit — the run, its answer, the returned identity
and the lifecycle record — routes through the lifecycle decision.

4. [done] A proved cleanup removes the lifecycle record with the root it
describes, so the ending converges on a second recovery.

5. [done] All six inventory orphans in this Work's files are resolved, not
reattributed; six probes came with them. The standing orphan count fell 23 to
17.

6. [next] Independent review. Evidence:
`evidence/w6634-2026-08-26-sixth-review.txt`.

## Seventh independent review changes requested — 2026-08-26

1. [verified] Keep the sixth correction's manager-owned completion validation,
   declaration comparison, derived receipt digest, post-create credential
   settlement, targeted root/record cleanup, and boundary-inventory repairs.
2. [changes requested] Put committed exact replay above every live worker-root
   read after proving the immutable request/receipt binding. A settled receipt
   already names the validated completion digest and must replay after
   `/output/output.json` is gone. A changed transient envelope is not a new
   operand of the same freeze operation. This is explicit case-specific
   confirmation to revise
   `test_a_replay_under_another_worker_envelope_is_refused` to preserve the
   committed answer rather than re-read mutable worker state.
3. [changes requested] Read the fixed completion signal as one bounded regular
   file beneath the output root without following links. Open with no-follow
   semantics, verify the opened descriptor's file type (and link policy), and
   read/validate that same descriptor so path replacement cannot select
   another file. Keep the additive symlink regression.
4. [changes requested] Compare the owned completion envelope's
   `assignment_ref` with the exact freeze request/input assignment before any
   custody mutation. Keep the cross-generation additive regression.
5. [changes requested] Treat a successful exact runtime query returning zero
   candidates as proved absence: no stop is needed, and targeted bounded
   cleanup must remove both the stale volatile root and its lifecycle record.
   A second recovery must reach ordinary `absent`. Keep the additive
   zero-runtime convergence regression.
6. [next] Re-run the sealing and credential modules, the 432-case adjacent
   focused gate, the W6634 boundary-inventory slice, and `git diff --check`;
   return exact evidence for independent review.


## Seventh re-review corrections — 2026-08-26

4. [done] Replay proves the request-to-receipt binding and returns the settled
receipt before any worker state is read; the envelope is out of the replay
binding, because a changed file is not an operand of a committed operation. My
own assertion of the opposite is revised under the recorded authority.

4. [done] The completion signal is opened `O_NOFOLLOW | O_NONBLOCK` and proved
a regular file on the opened descriptor. Covering that rule found the blocking
named-pipe path, which is fixed with it.

4. [done] The envelope's `assignment_ref` is compared against the freeze's
before any custody mutation.

4. [done] A successful engine query naming zero runtimes is positive absence,
so a stale record with no runtime converges to ordinary absence.

5. [done] All four additive regressions kept and green; two cases added. Six
guards, six measured.

6. [next] Independent review.


## Mandatory design checkpoint — 2026-08-26

1. [current] Finish only the already-started seventh-review evidence. Do not
   begin an eighth correction round or widen into shared inventory debt.
2. [done by reviewer synthesis; implementer evidence unchanged] Record a concise map of the current output-custody contract,
   credential-delivery contract, their settlement/recovery crossing, focused
   green gates and known shared baseline failures. See
   `evidence/design-checkpoint-2026-08-26.md`.
3. [next now] Pass W6634 to `baton.ops` for approver review of scope and design.
4. [blocked on approver ruling] Decide whether to split output custody,
   credential delivery and restart/recovery into separate Work, and define the
   minimum retained boundary needed by the Claude/Codex Docker spike.
5. [not authorized] No eighth implementation/review cycle until the ruling is
   appended here and any resulting dependency/Work decomposition is recorded.
6. [ops/impl action required] Remove W17110's obsolete dependency on W6634.
   Reviewer mutation was correctly refused because W17110 routes to
   `baton.impl`; the exact operational finding is in FINDING.md.


## Terminal approver decision — 2026-08-27

1. [done] Stop the combined implementation/review loop after the mandatory
   checkpoint; no eighth correction round is authorized.
2. [done] Close W6634 unsatisfying. Its source and evidence remain provisional,
   not accepted output of this Work.
3. [future only if required by the spike] Create separately bounded Work for
   any output-custody or fresh-run credential capability that is actually
   needed, revalidating before adopting the provisional implementation.
4. [owned elsewhere] Keep restart, reconciliation and orphan recovery in
   W6636. W17110 proceeds independently of W6634.

## Post-spike successor authorization — 2026-08-27

5. [authorized] The spike/integration evidence satisfies the earlier
   conditional: create separate output-custody and fresh-run
   credential-delivery successor Works. They revalidate the provisional tree
   independently; W6634 remains terminal non-satisfying.
6. [assigned] W6636 owns the shared start/destroy settlement crossing plus
   restart adoption, reconciliation and orphan convergence after both
   successors close satisfying.
