# Admit one accepted candidate into integration

Ledger Work: W101491

Parent: `work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-serialized-integration/`

## Confirmed scope

Implement the bounded admission leaf between accepted Authority/custody
evidence and the target-global coordinator's enqueue operation. One immutable
account must prove that the final checkpoint, candidate/artifact digest,
independent review, approval, target revision, assignment generation and
approved path/scope describe the same candidate before it receives a queue
rank.

This is tuner-suitable work behind K's recorded shared boundary. It owns a
disjoint admission implementation and focused tests; it does not change the
coordinator schema, common profile/runtime interface, exports or shared
registries. If the accepted boundary proves insufficient, the finding returns
to K rather than changing the seam from the tuner side. Git-shaped evidence may
travel as generic Work input or output, but this leaf neither names nor
interprets Git concepts.

## Acceptance boundary

- Complete, mutually consistent accepted evidence enqueues exactly one
  immutable candidate account.
- Exact replay returns the same entry and rank.
- Missing, stale, mismatched or differently scoped evidence refuses before
  enqueue and leaves the coordinator unchanged.
- The admission result is Authority-namespaced while target serialization
  remains global across permitted Authorities.
- Tests cover digest/identity/scope cross-wiring and concurrent duplicate
  admission without modifying shared-boundary files.

## 2026-09-06 — revalidation found a missing shared boundary

**Observed:** `baton_v12.integration.queue.enqueue` deliberately accepts an
already-proved eligibility account. Its module contract assigns construction
and cross-validation of that account to the admission layer, so storing a
well-shaped document is not evidence that the candidate was eligible.

**Observed:** the accepted Authority surface can re-resolve a proposal and its
verification, review and approval receipts. Those documents bind the proposal
assignment, candidate digest and expected target revision, and the receipts
prove the required `passed`, `accepted` and `approved` dispositions. W71918's
accepted checkpoint surface independently proves the exact accepted checkpoint,
verdict, checkpoint digest and checkpoint evidence; its related line,
checkpoint and writer projections can recover the Authority, Work and writer
assignment generation.

**Observed blocking gap:** no accepted surface binds those two families to the
coordinator's generic profile and approved-scope operands. In the current
source tree, `scope_digest` and `profile_account_digest` are only consumed by
the integration coordinator schema/queue and fabricated by its focused test
fixture. The worker-control contract contains no path-set or approved-scope
member, while the Authority approval receipt binds candidate digest and target
revision but no path-set or scope digest. `proposal_manifest_digest` exists in
the frozen worker-control schema, but no accepted admission/profile operation
cross-binds that document to the checkpoint path set and approved scope without
interpreting its source-specific members.

**Confirmed consequence:** this leaf cannot prove the acceptance boundary by
assembling the missing values from caller operands. Doing so would allow an
arbitrary `scope_digest` or `profile_account_digest` to receive a queue rank,
and the required differently-scoped refusal would test only equality between
two caller claims rather than accepted evidence. That is precisely the
insufficient-shared-boundary case this dossier says must return to K.

**Required shared-boundary correction:** K's owned generic integration boundary
must expose one closed, re-resolvable candidate/profile account that binds the
Authority/Work/assignment, proposal and candidate digest, expected target
revision, checkpoint identity/digest, proposal-manifest digest, profile
kind/version/account digest, reviewed path-set digest and approved scope digest.
The producer must validate that account from accepted evidence; the admission
leaf may then cross-bind it to fresh Authority and W71918 reads before calling
`enqueue`. This record does not prescribe the shared interface's spelling and
does not change shared code, schemas, exports or registries from the tuner side.

No production or test byte was written. Baton message M101589 requested K's
exact interface and the Work is returned to `baton.impl` for that owner-level
correction.
