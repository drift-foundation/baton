# Implement the Authority read-only opener

W126880, owner126833 as amended by owner128249. Claim before execution; read FINDING and the exact parent
READ-ONLY-OPENING-ALLOCATION-2026-09-09.md. Handler baton.claude via baton.impl;
independent return baton.bug.

Current state: independently accepted by review128304 in
`review-2026-09-09T14-00-25Z.md`, under owner128249's amendment. Accepted full
bytes and hashes are in evidence/accepted-128304. No further implementation is
queued for this provider. Close satisfying and let W122060 reuse its public
Authority.open_readonly API after W126887 is independently accepted.

The completed test conversion was bounded to the three scheduled sidecar-only
refusal cases and the fixture's sidecar snapshot expectations; other assertions
remained unchanged. All50 store tests and the independent exited-writer WAL
probe passed. Charged implementation usage is3.464s/20s, with the reconciliation
and reviewer arithmetic correction preserved in the newest review. No reset.

The accepted source/test boundary remains:

Paths relative to v12/python:

- src/baton_v12/authority/api.py
- src/baton_v12/authority/store.py
- tests/authority/test_store.py — additive tests plus the bounded sidecar-expectation conversion above

1. Revalidate and implement the pinned public API. Read an existing recognized
   store only; validate the returned connection's own identity/schema in a
   coherent snapshot and honor expected UUID. Reuse owner validation, preserving
   applicable path/non-adoption rules. No schema initialization, migration,
   write lock, persistent PRAGMA, checkpoint, permissions change or write-capable
   fallback. Prevent mutations through the new handle using the owner's refusal
   boundary, preserving current serving open/create/transaction semantics.
2. Add public controls for matching/mismatching UUID, absent/empty/foreign/
   incompatible stores unchanged, committed receipt/operation reads, mutation
   refusal, readable read-only storage where supported, and coherent committed
   WAL visibility during concurrent serving with the amended SQLite-sidecar
   exception. Reuse existing fixtures; only scheduled sidecar-effect
   expectations may change, preserving all other assertions.
3. Declare the verification question before execution and enforce cumulative20s
   across every iterative test/probe process. Record actual commands, logs,
   return codes and elapsed time; stop at the limit. No unrelated full-suite or
   accepted-provider rerun. Retain actual claim-start/final bytes and modes.
4. Return for independent acceptance with exact candidate hashes and limitations.
   W122060 consumes the accepted API later; do not edit its two paths, the
   coordinator provider, any schema, package export or broader source path.

This independently acceptable owner capability is one half of the final
read-only consumer join, not a new planning Job or ordinary-execution gate.
