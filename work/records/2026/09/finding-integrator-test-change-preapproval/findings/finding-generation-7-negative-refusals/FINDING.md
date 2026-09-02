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
