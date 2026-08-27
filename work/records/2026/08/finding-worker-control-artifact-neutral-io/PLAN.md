# Plan: artifact-neutral I/O in the worker-control and conformance contracts

1. [done 2026-08-26] Create this record and revalidate the 2026-08-25 ruling
   against the current tree. Recorded in `FINDING.md`: the superseded
   vocabulary is in the SCHEMA rather than the prose; the version-control
   object type is shared with the proposal and integration surfaces and is NOT
   wholly superseded; and the shipped manager already exports the acquisition
   capability this revision forbids.

2. [resolved 2026-08-26; blocked on W15232] Name who removes or re-homes
   `v12/python/src/baton_v12/worker_manager/workspaces.py`'s acquisition half.
   This Job remains bounded to contracts. W15232, a follow-up to closed W6631,
   owns removing acquisition from the core manager and re-homing it only if an
   already pinned source-stager/driver boundary consumes it. This Work resumes
   after W15232 closes satisfying.

   **Escalated from asynchronous to blocking after item 3 was attempted.** It
   was recorded as a question nothing waits on. It is not: that module
   validates its operands against the removed definitions BY NAME, so the
   revision makes it refuse everything it is handed, and no version of this
   contract change lands green while it stands. Measured, and the schema patch
   is preserved so the answer does not cost a rebuild --
   `evidence/gate-blocked-on-workspaces-2026-08-26.txt`,
   `evidence/schema-patch-2026-08-26.diff`, `evidence/revise_schema.py`.

2b. [confirmed 2026-08-26] The record's schema and
   `v12/python/src/baton_v12/contracts/schema/worker-control-1.0.schema.json`
   are BYTE IDENTICAL, and the distribution ships the second as package data
   and validates live manifests against it. Items 3 and 5 are therefore one
   pass rather than two: a schema edit is a change to a currently green
   1309-case suite from the moment it lands.

3. [BUILT, then reverted to keep the tree green — blocked on item 2]
   The control contract's schema. Cut the path
   `inputManifest -> sourceDescriptor -> {gitSource, directorySource}` and
   `inputManifest -> outputDescriptor`, and `resultManifest -> artifactOutput`,
   replacing them with the two generic envelopes the ruling states: declared
   relative paths, generic integrity evidence, completion status, and one
   OPAQUE consumption/result description the manager never interprets — the
   schema already has a namespaced `extensions` shape for exactly that. Keep
   the version-control object type where the proposal and integration surfaces
   still use it. Land the shipped copy in the same pass (item 2b).

4. [after 3] The control record's `SPEC.md`, so the prose names
   `/input/input.json` and `/output/output.json`, the read-only and
   writable-then-frozen roles, publication of `output.json` LAST, and private
   ephemeral space as capacity rather than protocol. Preserve the superseded
   acquisition/result types as explicitly dated supersession history rather
   than deleting them: the reasoning that was superseded is how the next reader
   knows why the current rule is not the obvious one.

5. [after 4] `evidence/vectors.json` and `contract_model.py`, and the shipped
   Python suite that reads an input manifest out of those vectors. A vector
   change is a change to a currently green suite, so it is measured rather than
   assumed.

6. [after 5] The conformance contract: `SPEC.md`, `schema/conformance-1.0`,
   `cases.json` and `obligations.json`, for the same two surfaces — persistent
   output workspaces, ephemeral-workspace export, `output.json` published last,
   unresolved identifier-only output refused as a durable result, and frozen
   output chaining into read-only input.

7. [after 6] Revalidate the affected downstream Work against the pinned
   revision, as the assignment requires — W6633 at least, which this Work
   blocks.

8. [after 7] Independent review. Passed back rather than closed.


## Independent review changes requested — 2026-08-26

3/5. [changes requested] Synchronize the tracked `v12/python/build/lib`
distribution shadow with the artifact-neutral schema and manager surface. Keep
the additive fourth-copy byte-identity regression.

5. [changes requested] Revise `evidence/contract_model.py` with the vectors.
Its existing canonical-valid-vector case currently errors on the removed
`uri` member.

4. [changes requested] Complete the control SPEC supersession. Until then its
normative acquisition descriptor and closed output-kind sections contradict
the schema now shipped.

6. [changes requested] Revise the conformance SPEC, schema, cases and
obligations for the two artifact-neutral filesystem roles and publication
rules named by this Work.

7. [changes requested] Revalidate W6633 and record the exact affected
downstream contract before returning.

8. [next] Retain the green 221-case focused baseline, make the fourth-copy and
contract-model gates green, run the revised conformance model, and return for
independent review.


## Review corrections — 2026-08-26

3/5. [done] The tracked `v12/python/build/lib` shadow is synchronized for the
three files this supersession makes contradictory: the frozen schema,
`contracts/manifest.py` and `worker_manager/workspaces.py`. Measured after: no
superseded definition and no acquisition surface under `PYTHONPATH=build/lib`.
The shadow's OTHER divergences belong to W6628, W6629, W6632 and W6634 and are
reported rather than done, with the tracked-build-artifact question raised as
repository policy rather than answered.

5. [done] `evidence/contract_model.py` carries the same source-rule removal as
the shipped validator. 24 cases pass, including the canonical valid vector that
raised `KeyError: 'uri'`.

4. [done] The control `SPEC.md` supersession is complete: a dated header, a
rewritten §7 around the two filesystem roles and publication-last, §7.6 keeping
the superseded vocabulary as dated history, and §3.3 and §12 rules 4 and 7
narrowed rather than deleted.

6. [done] The conformance contract is revised: two acquisition cases removed,
eight added, `A-01`/`A-02` restated, `A-03`/`A-07`/`A-08` re-cited and
`A-10`-`A-14` added. 118 cases, 75 obligations, every live count in the SPEC
moved with them. `test_conformance_model` 74 cases, OK.

7. [done] W6633 revalidated by measuring `v12/worker/baton_worker.py`, and the
exact affected contract is recorded in `PROGRESS.md` as five numbered
obligations plus the three environment members that become unnecessary rather
than renamed.

8. [next] Independent review.


## Fifth independent review changes requested — 2026-08-26

5. [changes requested] Make
`result-completed-without-its-completion-envelope` actually omit the member and
expect the exact missing-property diagnostic. Prefer a valid non-completed
receipt without the digest as its base and patch only disposition to
`completed`. Keep the additive direct-result-branch regression.

5. [changes requested] Remove `_validate_result_manifest` and its semantic
dispatch. The executable model deliberately contains only invariants JSON
Schema cannot express; the conditional required-member rule is schema-owned
and must be proved there rather than duplicated behind schema-first validation.

8. [next] Return with the 25-case canonical model green, the 230-case shipped
gate and 92-case migrated gate retained, four identical schema copies, and the
exact conditional-required diagnostic proved without relying on unrelated
top-level `oneOf` branches.


## Second independent review changes requested — 2026-08-26

3/4/5/6. [changes requested] Resolve publication ownership. The pinned ruling
says the worker publishes `/output/output.json`, but the revised schema makes
that file the manager-authored frozen result and the conformance cases publish
it through `output.freeze`. Split the worker completion envelope from the
manager custody receipt, or record an approved supersession; align schema,
SPEC, vectors, model and conformance to the one resulting boundary.

5. [changes requested] Remove cross-root path overlap comparisons from the
shipped validator and canonical model and narrow SPEC §12 rule 3. Preserve
source/source and output/output containment refusal. Keep the additive two-root
regression and explicitly correct the pre-existing shared-root case.

7. [changes requested] Revalidate both W6633 and W6634 after publication
ownership is settled. Record the exact writer, final filename/location,
completion signal and manager receipt for each downstream implementation.

8. [next] Return with the 223-case focused gate green, both contract models
green, and a downstream handoff that no longer asks a quiesced worker to know
manager freeze/custody facts.


## Second review corrections — 2026-08-26

4/6. [done] The worker's completion envelope is separated from the manager's
frozen-result receipt. `baton.worker-manifest/completion` and `workerOutput`
are added to all four schema copies; `resultManifest` gains one OPTIONAL
`completion_manifest_digest`; §7.0, §7.3, §8.4 and the new §8.7 state the split
and why each absent member is absent. It is a SEPARATION rather than a
supersession: it is the reading under which both pinned sentences of the
2026-08-25 ruling are true at once.

5. [done] §12 rule 3, `contracts/manifest.py` and `contract_model.py` compare
overlap WITHIN the staged-input set and WITHIN the declared-output set, never
across the two fixed roots. The pre-existing case and the invalid vector are
corrected case-specifically, with the stale shared-workspace rationale replaced.

6. [done] The conformance publication cases are driven by the WORKER; `A-15`
and `A-manager-receipt-is-not-the-worker-envelope` cover the split. 119 cases,
76 obligations, every live SPEC count moved with them.

7. [done, and corrected] The claim that only W6633 was affected was FALSE.
W6634 is revalidated by measurement: its `sealed.json` in manager custody is
correct as built under the split, with two stated obligations — bind the
completion digest once a worker publishes one, and validate `/output/
output.json` before freezing, which nothing in `worker_manager/` yet reads.

8. [next] Independent review. Evidence:
`evidence/w14251-2026-08-26-ownership-split.txt`.


## Third independent review changes requested — 2026-08-26

3/4/5. [changes requested] Reserve `/input/input.json` and
`/output/output.json` from payload destinations in the schema, normative prose,
canonical model, shipped validator and invalid vectors. Preserve the corrected
rule that unrelated relative spellings across the two roots do not overlap.

4/5. [changes requested] Deliver the completion envelope's standalone semantic
rules to the shipped validator: unique names, within-output containment and
the exact status/content-manifest relation. Keep the additive regressions.

4/6/7. [changes requested] Pin and cover the manager's comparison of the
completion envelope with the exact input manifest: one answer per declaration,
no extras or omissions, exact name/type/path, and required outputs never
answered `missing-optional`. Record this as an exact W6634 obligation rather
than the generic instruction to validate `output.json`.

4/6/7. [changes requested] Make the manager receipt bind the completion digest,
or define an explicit versioned/negotiated legacy path. An unqualified optional
member in the frozen 1.0 schema is a permanent bypass, not rollout staging.

4. [changes requested] Remove §7.1's stale statement that staged-input
destinations cannot overlap any output; state the within-root and reserved-name
rules instead.

8. [next] Return with the 226-case focused gate green, both contract models
green, conformance covering declaration/completion identity, and W6634's handoff
expressed as an implementable exact comparison and receipt binding.


## Third review corrections — 2026-08-26

4/5. [done] Each fixed root reserves its own manifest filename, in its OWN root
and including nested spellings, in the shipped validator, the record's contract
model and four invalid vectors. NOT in the schema: measured, that makes the
review's own regression unsatisfiable (`integrity.path` versus
`integrity.schema`) and the semantic rule unreachable.

5. [done] `_check_completion_manifest` is in the shipped validator and
dispatched for `baton.worker-manifest/completion`: unique names,
non-overlapping paths, the reserved output name, and status/integrity agreement
both ways.

6. [done] §12 rule 15 states the cross-document identity relations, and `A-16`
with four conformance cases carries them. 123 cases, 77 obligations.

4. [done] §7.1's superseded cross-root sentence is replaced with the within-root
rule and both reserved names.

7. [ESCALATED, not landed] Requiring `completion_manifest_digest` refuses 96
cases across W6628's, W6629's and W6634's suites, and the versioned alternative
is unreachable because `$defs.version` pins `minor` to a const. Three ways
forward are named in `PROGRESS.md`; the tree is left green with the gap pinned
by a case rather than implied.

8. [next] Independent review, with one decision requested.


## Fourth independent review changes requested — 2026-08-26

4/5/7. [changes requested] Require `completion_manifest_digest` on every
`completed` version-1.0 manager receipt. Non-completed receipts may omit it
when no worker envelope was published; whenever an envelope was validated,
bind its digest regardless of disposition. Update the 96 measured client
fixtures rather than widening the version vocabulary or preserving an
unqualified optional bypass, and keep a negative completed-without-digest
regression.

5. [changes requested] Correct the nearby live comments that describe an
unreachable minor-1 boundary and claim W6634 already performs the
cross-document comparison. The contract pins the rule; W6634 remains the
downstream implementer.

8. [next] Return with the 228-case focused gate plus the migrated intake,
output and credentials fixtures green, both executable contract models green,
four identical schema copies, and no completed receipt accepted without the
completion digest.


## Fourth review corrections — 2026-08-26

7. [done, escalation settled] Under 1.0 a `completed` frozen-result receipt
MUST carry `completion_manifest_digest`: schema across all four copies, the
record's contract model, the vectors, and §8.4's prose including the rule the
schema cannot state — an envelope that WAS validated is bound whatever the
disposition became. The 96 refusals were migration cost and 92 of them came
from one shared helper.

7. [done] Both comments the review named are corrected: no unreachable minor-1
boundary, and §12 rule 15 stated as W6634's downstream obligation rather than
as something it already performs.

8. [next] Independent review.


## Fifth review corrections — 2026-08-26

5. [done] The invalid vector reaches the rule it names: a valid receipt that
legitimately carries no envelope (`unable`), and an invalid one deriving from
it by changing only `disposition` to `completed`, expecting the exact
`'completion_manifest_digest' is a required property` diagnostic rather than a
word any `oneOf` branch can produce. Measured by restoring the vacuous form.

5. [done] `_validate_result_manifest` is removed from the design model with a
comment saying why: the frozen schema owns that shape rule, the model says it
carries only what schema cannot express, and a schema-first harness made the
duplicate unreachable.

8. [next] Independent review. Evidence:
`evidence/w14251-2026-08-26-vector-reaches-its-rule.txt`.


## Sixth independent review — 2026-08-26

5. [done] The corrected vector reaches the exact result-manifest conditional
and the additive direct-branch regression passes. The schema-owned shape rule
has no duplicate semantic owner.

8. [done] Independent review signed off. W14251 may close satisfying; W6633
and W6634 consume the exact downstream obligations recorded above.

## Approved post-close follow-up — 2026-08-26

The W19784 ruling explicitly supersedes the two-manifest sentence while
preserving the two-root artifact-neutral boundary. W19784 now owns the
contract/schema/conformance and downstream implementation work for fixed
read-only `/input/assignment.json`; this closed Work remains the chronological
record of the contract before that correction.
