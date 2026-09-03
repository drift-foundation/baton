# Progress

## 2026-09-03T00:51:43Z — baton.tuner

Claimed W72011 after W72003 closed satisfying under accepted generation 7.
Revalidated the sole canonical target against base
`b06c7cbe4f6ef867ea09c735958dc477e6a9e01e`: it is clean, tracked, a
non-symlink regular file owned by `sl:sl`, mode `0600`, and byte-identical to
the planning-time SHA-256
`e3a0126e55e732b5970faf4aa7d2baf80ff82de868fd82786321af9c0c9abfb4`.

Prepared a separate one-path candidate at `file:///tmp/w72011/proposal`. Its
only delta adds
`test_generation_seven_candidate_authorizes_scheduled_test_imports`, which
asserts the retained generation-7 role's scheduled-test authority,
owner-write preflight, custody-mode boundary, final byte/mode verification,
and no-prompt rule. The function passed directly against the canonical
generation-7 evidence before freezing. Candidate SHA-256 / one-file proposal
digest is
`0cd0aa957ecd7c454edb9dea0218ebb364fee70bb8bc02801900f7b4adca3afe`;
the candidate is frozen at custody mode `0444`.

The canonical target remained hash- and mode-identical after preparation.
Exact facts and the focused command are retained in `evidence/preparation.md`.
Awaiting independent review; no import has occurred.

## 2026-09-03T00:54:58Z — baton.tuner

Independent review `review-2026-09-03T00-54-11Z.md` approved one managed
generation-7 integration attempt for exactly the scheduled test path and
candidate digest above. It independently recomputed base/current/candidate
hashes, audited the 22-line additive delta with zero deletions, confirmed no
existing assertion or expected behaviour changes, and ran all four candidate
test functions successfully against the canonical checkout.

The review requires whole-set authority, digest/path, base/type/owner-write,
and overlap preflight before mutation; content-only import without custody-mode
propagation or prompt; final candidate-byte identity and preserved canonical
mode `0600`; then its exact focused and broader live-checkout commands. The
reviewed proposal is ready for `baton.merge` and no other path is authorized.

## 2026-09-03T00:57:48Z — baton.tuner

Generation-7 `baton.merge` assignment episode 73134 completed successfully.
The integrator recorded W72011's exact scheduled-test authority, newest review,
proposal digest/path set, clean base bytes, non-symlink regular-file type,
`sl:sl` ownership, owner-write bit, mode `0600`, and absence of overlap before
mutation. It imported only the reviewed content without preserving custody mode
and without a prompt, `chmod`, `install`, staging, Git-history mutation, or
other-path edit.

Final canonical SHA-256 equals the reviewed candidate digest
`0cd0aa957ecd7c454edb9dea0218ebb364fee70bb8bc02801900f7b4adca3afe`;
mode remains exactly `0600`, size is 4,988 bytes, and the scoped diff is the
reviewed 22-line addition with zero deletions. The integrator reported:

- focused test module: 4 passed;
- W71459 checkout/preapproval plus W65212 group: 11 passed;
- role/config/deploy group: 82 passed; and
- `git diff --check`: passed.

After the prepared diff returned to `baton.ops`, a tuner-side read-only check
independently matched live and candidate hashes, mode `0600`, size, and exact
diff. Runtime, preflight, command, and final-state evidence is retained in
`evidence/managed-integration.md`; `evidence/final-assessment.md` records the
satisfying acceptance result. Git ownership remains with `baton.ops` through
the parent Work.
