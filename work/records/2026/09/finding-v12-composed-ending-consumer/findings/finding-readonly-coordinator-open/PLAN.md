# Implement the coordinator read-only opener

W126887, owner126833 as amended by owner128249/128251. Claim before execution; read FINDING and the exact parent
READ-ONLY-OPENING-ALLOCATION-2026-09-09.md. Handler baton.claude via baton.impl;
independent return baton.bug.

Current state: independently accepted review128347 in
`review-2026-09-09T14-06-23Z.md` under owner128249/128251. Full accepted bytes
and hashes are in evidence/accepted-128347. No further provider implementation
is queued. Close satisfying; W122060 reuses IntegrationStore.open_readonly and
the independently accepted Authority opener for its remaining consumer join.

The two scheduled sidecar-only refusal cases were converted, one absent-store
control added, and other assertions preserved. All19 focused controls and the
separate-process committed read pass. Charged implementation usage remains
16.106s/20s with the original carry-in evidence limitation preserved. No reset.

The accepted path boundary and completed verification requirements remain:

Only these paths relative to v12/python, plus this dossier's attributable
PROGRESS/evidence:

- src/baton_v12/integration/store.py
- tests/integration/test_coordinator.py — additive tests plus the bounded sidecar-expectation conversion above

1. Revalidate and implement the pinned public API. Open an existing recognized
   coordinator only, checking its actual returned connection in a coherent
   snapshot. Preserve owner/schema/history validation and applicable path rules.
   No initialization, migration, write lock, persistent PRAGMA, checkpoint,
   permissions change or write-capable fallback. Refuse mutations through the
   read-only handle using the owner's public refusal boundary. Preserve normal
   serving opening, creation and transaction semantics.
2. Add public controls for readable committed entry/lease/history data, absent
   path without creation, empty/foreign/incompatible files unchanged, mutation
   refusal, read-only storage where supported, and coherent committed WAL reads
   during concurrent serving with the amended SQLite-sidecar exception. Reuse
   existing public fixtures; only scheduled sidecar-effect expectations may
   change, preserving all other assertions.
3. Declare the evidence question before execution and enforce cumulative20s
   across iterative test/probe processes. Retain exact commands/logs/results and
   elapsed time; stop at the limit. No unrelated full-suite or accepted-provider
   rerun. Capture actual claim-start/final bytes and modes.
4. Return for independent acceptance with hashes and limitations. Do not edit
   the Authority sibling, consumer, schema/version, package exports or any path
   beyond these two. W122060 later consumes both independently accepted openers.

No dependency on W126880 is invented: each owner can be accepted independently.
This implementation Work gates only the final read-only consumer acceptance,
not the already authorized ordinary execution or a new planning phase.
