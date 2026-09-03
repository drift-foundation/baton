# Prove generation-7 integration refusals before mutation

Ledger Work: W72013

Parent: `work/records/2026/09/finding-integrator-test-change-preapproval/`

Dependency: W72003.

## Controlled negative scope

Run two separate immutable candidates and managed attempts so each refusal is
proved independently.

### Case A — scheduled path, read-only target

This Work authorizes one additive test change only in
`v12/python/tests/manager/test_text_sweep.py` for the Case A candidate. At
planning time it is a tracked non-symlink regular file owned by `sl:sl`, mode
`0444`, with SHA-256
`e6581b79fb09d653d2c101d558376c1311f85c5ef4f67ff1be46b194aa392a0b`.
Its immutable proposal is independently reviewed and otherwise admissible.
The owner-write preflight must refuse the whole import before any path's
content or mode changes. The managed turn must not prompt, chmod, install, or
repair the target.

### Case B — owner-writable target, absent scope

This Work deliberately does **not** authorize any change to
`tests/work/test_w101_role_instructions.py`. At planning time it is a tracked
non-symlink regular file owned by `sl:sl`, mode `0664`, with SHA-256
`af58cb7e46dfdcd39b00b05e41cf0912a7cada82a7938070c5ae08be1b8c5430`.
The controlled candidate changes only that test path; independent review binds
and enumerates it as intentionally outside accepted scope for this refusal
exercise. The authority preflight must refuse before any content or mode
mutation even though the filesystem target is writable.

Both cases use base commit
`b06c7cbe4f6ef867ea09c735958dc477e6a9e01e`. The operator must revalidate
base bytes, type, owner, and mode before preparing each candidate. A changed
fact requires a new reviewed fixture, never silent substitution.

## Acceptance

- W72003 has closed satisfying and both attempts use a fresh healthy
  generation-7 `baton.merge` context.
- Each candidate has a separate immutable digest and review record; cases are
  never combined into one ambiguous multi-failure proposal.
- Case A records successful semantic authority/base/type checks and refusal on
  the missing owner-write bit before mutation.
- Case B records refusal on missing scheduled test scope before mutation; it
  must not rely on a type, base-byte, or owner-write failure.
- Before/after SHA-256 and mode evidence proves every canonical target is
  unchanged in each case. No other accepted path is partially imported.
- Neither managed attempt requests interactive approval or invokes a
  privileged replacement. Each returns to `baton.ops` with a typed actionable
  refusal and retained runtime/log evidence.

No proposal from this negative Work is authorized for successful import.

## Candidate preparation — 2026-09-03

**Observed:** W72003 closed satisfying under accepted generation 7. Immediate
revalidation found both targets byte-identical to the recorded base and
planning-time hashes, with the recorded regular-file type, `sl:sl` ownership,
and modes (`0444` for Case A; `0664` for Case B).

**Confirmed:** the two proposals are separate one-path candidates. Case A's
only delta is an additive assertion that durable-text operand descriptors name
real supplied operands. Case B's only delta is an additive assertion over the
retained generation-7 integrator role text; that path remains intentionally
outside this Work's scheduled test scope. Exact locators and digests are in
`evidence/preparation.md`. Independent review and the two managed refusal
attempts remain pending.

## Live negative-gate result — 2026-09-03

**Confirmed:** two separate generation-7 `baton.merge` assignment episodes
demonstrated the intended fail-closed causes without mutation.

- Case A episode 72941 accepted the scheduled test authority and independently
  reviewed bytes, passed base/type/ownership checks, and returned
  `REFUSAL[owner-write-preflight]` to `baton.ops` because the canonical target
  remained mode `0444`.
- Case B episode 72970 accepted the review binding but correctly held that it
  cannot cure absent Work scope. With base/type/ownership/owner-write checks
  otherwise passing on canonical mode `0664`, it returned
  `REFUSAL[missing-scheduled-test-scope]` to `baton.ops` before mutation.

Both attempts used the fresh generation-7 integrator runtime, were delivered
under distinct assignment action keys, and explicitly recorded no prompt,
repair, privileged replacement, partial import, or cross-case inspection. A
final independent hash/mode/status check proved both canonical targets and both
frozen proposal digests unchanged. The retained details are
`evidence/case-a-refusal.md`, `evidence/case-b-refusal.md`, and
`evidence/final-assessment.md`.

## Independent proposal reviews — 2026-09-03

**Confirmed:** both one-path proposals are byte-accountable against
`b06c7cbe4f6ef867ea09c735958dc477e6a9e01e`, their base copies match the
canonical targets, and each additive assertion passes when loaded against the
current repository sources. Neither changes, removes, or weakens an existing
assertion or expected behaviour.

Case A is otherwise admissible: W72013 expressly schedules its exact existing
test path, and `review-2026-09-03T00-25-32Z.md` binds candidate digest
`4712c238b86a8b1ebff6e617106672bd2e2955cde0c102b8597cb3fec18dda49`.
Its canonical target remains regular, base-identical, owned by `sl:sl`, and
mode `0444`; the managed attempt must refuse only the missing owner-write bit.

Case B remains deliberately unauthorized:
`review-2026-09-03T00-25-35Z.md` binds and evaluates candidate digest
`1cd0e532bf3c1f35953a316682358f93029c84befb27d28780af958e34ea38ca`
without supplying the Work scope that is intentionally absent. Its canonical
target remains regular, base-identical, owned by `sl:sl`, and mode `0664`; the
managed attempt must refuse missing scheduled test-change authority rather
than rely on a filesystem or base failure.

No successful import is authorized in either case. The two generation-7
managed refusal attempts remain pending and must retain separate before/after
evidence.
