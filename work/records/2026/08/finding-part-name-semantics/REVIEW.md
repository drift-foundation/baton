# Stage 2.1 plan review — changes requested before `_impl.py`

## Accepted inventory boundary

The four-category inventory is the right way to constrain this rename.
In particular, `baton_tui/drafts.py::filename(participant)` names a real file
on a real filesystem and must remain `filename`; a regression should protect
that exclusion. Path/filename prose unrelated to part metadata must likewise
not be swept mechanically.

No shipping `_impl.py` change has been made while the oracle ruling is open,
which is correct.

## R1 — the plan contradicts the ruled fresh-authority cutover

The finding already pins the deployment boundary: keep the protocol-9
authority live during development, then retire it intact and initialize a
fresh protocol-10 authority before any optional history work. The plan instead
introduces `migrate_instance` and `ALTER TABLE parts RENAME COLUMN ...` as
stage-2.1 work. That is an unruled in-place migration and changes the outage,
recovery, and evidence contract.

Remove the in-place migration from this implementation plan. Build and review
the protocol-10 schema as the schema of a fresh authority. Optional history
porting or a later in-place migration needs its own explicit contract and must
not hold communications cutover hostage.

## R2 — a future migration cannot be a column rename alone

`manifest_digest()` serializes the metadata key itself. Replacing `filename`
with `part_name` therefore changes the digest for every named-part message,
notice, and disposition even when all semantic values and bytes are identical.
Simply renaming the column leaves stored `manifest_sha256` values in the old
domain, after which protocol-10 `doctor` recomputation reports damage and
retry/disposition equality compares unlike identities.

Any future migration/port must choose and audit one complete strategy:

- rederive every affected owner manifest under the protocol-10 canonical form
  in one guarded ceremony, including dependent disposition/retry invariants;
  or
- preserve and explicitly version a legacy digest domain for imported rows.

A retry spanning the boundary does not automatically need to fail merely
because the public field spelling changed. The semantic part name did not
change. Whether imported rows retain or rederive identity is a contract choice
for Slawomir, not an implementation consequence to state as settled. Under the
currently ruled fresh-authority cutover there is no cross-boundary live retry
at all, so stage 2.1 should not invent one.

## R3 — `test_baton_v6.py` is not a core test corpus

The inventory labels its 29 sites “core tests,” but that file imports and tests
the frozen `baton_v6` implementation. If the oracle is retired, still-valid
properties must be ported to protocol-10 core conformance before the old suite
is removed from the active gate. Correct the inventory and make that coverage
transfer part of the oracle-retirement gate; do not count old-oracle tests as
shipping-core coverage.

## Re-review gate

Revise the plan only; do not touch `_impl.py` until the oracle choice is ruled.
The revision should:

1. target a fresh protocol-10 schema, not an in-place migration;
2. park manifest conversion/cross-boundary retry under a separate explicit
   future history-port/migration decision;
3. identify the oracle tests that need protocol-10 core equivalents; and
4. retain the accepted real-filename exclusions and their regression.

## References

- `work/finding-part-name-semantics/FINDING.md`
- `work/finding-part-name-semantics/PLAN.md`
- `work/finding-protocol-10-umbrella/FINDING.md`
- `baton_core/_impl.py`
- `baton_tui/drafts.py`
- `test_core_parity.py`
- `test_baton_v6.py`

## Stage 2.1 implementation review — changes requested

The fresh protocol-10 schema and the mechanical `filename` -> `part_name`
conversion are internally consistent. The schema, manifest, stored rows,
delivery, dump, core method parameters, CLI option, authoring translation and
TUI rendering all use the new field, while `drafts.filename()` and projection
filenames correctly retain their filesystem vocabulary. The reported 2,079
tests and clean diff establish a useful baseline.

The implementation is not yet approved for the following reasons.

### R4 — `validate_part_name` still gives a part filename semantics

The pinned contract says a part name is an uninterpreted label, never a path,
and that the recipient decides whether and how it becomes a filename. The
implementation renamed `validate_filename` but retained its filesystem rules:
it rejects `/`, `\\`, `.`, `..`, and leading `-`, and says its 255-byte bound
exists because a filesystem enforces it. Directly calling
`validate_part_name("../diagram")` still fails with “contains a path
separator.” That is the old concept under a new key.

Accept path-looking labels losslessly: `/`, `\\`, `.`, `..`, and leading `-`
have no path meaning inside Baton. Continue to reject empty/control-bearing
labels and keep a bounded protocol field; a 255-byte bound may remain, but it
must be justified as a Baton storage/display/DoS bound, not a filesystem
limit. `materialize` must continue ignoring the label for output-path choice,
and the TUI must continue passing it through safe-text rendering. Add
round-trip and safe-materialization regressions for path-looking labels.

### R5 — both public version boundaries stayed at their old values

This is a breaking public core API change: Store keyword parameters and
delivery/preview dictionaries changed from `filename` to `part_name`.
`CORE_API_VERSION` nevertheless remains 1, and the TUI still declares
`REQUIRES_CORE_API = 1`. An old TUI and the new core therefore appear
compatible at startup and fail only when they touch the renamed field.

Bump the core API to 2, make the TUI require 2, and pin startup refusal for an
incompatible API rather than relying only on a `>=` check that cannot detect a
breaking higher version. If the compatibility contract is an exact API major,
check equality; if ranges are intended, declare and test the supported range.

The agent CLI also removed `--filename` and introduced `--part-name`, yet still
reports `baton 5.2.0`. Stage 1B correctly treated additive options as a minor
bump; removing/renaming a public option is a major break. Use tool 6.0.0 for
protocol 10. The TUI binary likewise cannot remain 0.1.0 while moving from a
protocol-9/core-1 bundle to protocol-10/core-2; bump it to 0.2.0. Rebuild both
artifacts and manifests after the version fixes.

### R6 — “no protocol surface says filename” tests only three surfaces

The new regression checks schema text, one delivery, and dump. Its name and
the finding claim every public surface, but it does not inspect core method
signatures, source normalization, CLI help, packaged CLI parsing, or the four
authoring verbs.

Broaden the pin to cover:

- Store/content public signatures contain `part_name` and no `filename`;
- `send`, `send-notice`, `reply`, and `close` help expose `--part-name` and not
  `--filename`;
- the built executable accepts `--part-name`, rejects `--filename`, and still
  accepts descriptor `name=`;
- schema, delivery, dump and retry identity remain covered as they are now.

Also correct the surviving stale text: `test_core_authoring.py` still teaches
legacy `--filename`; `_authored_parts` spells a nonexistent `--part_name`;
and `_part_header` says the wire rename “is protocol-10 work” after landing it.

### R7 — the prior oracle-retirement review remains unconsumed

The earlier response “Oracle retirement: three accepted; items 4–6 remain” is
still pending to `baton.implementer`, and the files confirm those items were
not applied:

- `baton_core/__init__.py` still describes a live differential oracle and
  names the deleted parity harness;
- the conformance header still says “one import” instead of four, and a nearby
  distribution comment still calls the oracle active;
- `test_nothing_imports_the_retired_oracle` still line-matches source instead
  of inspecting `ast.Import` and `ast.ImportFrom` nodes.

Apply those bounded corrections in this rework. The full handoff does not need
an explanatory note beside every mechanically renamed assertion: the named
protocol-10 finding, the conformance header, and unchanged property assertions
are sufficient.

### R8 — README misattributes `part_name` to RFC 2183

The README currently says disposition is inline/attachment “with an optional
`part_name` (RFC 2183).” RFC 2183 defines content disposition and its filename
parameter; Baton’s `part_name` is its own advisory metadata. State those as
separate facts so the documentation does not invent an RFC field.

### R9 — future handoffs must carry a references part

This handoff named paths in prose but did not include the mailbox convention’s
`text/vnd.baton.references` part. Future implementation/re-review handoffs must
list the exact repo-relative review surface in references, especially while
several unstaged protocol-10 stages accumulate.

## Stage 2.1 re-review — two corrections remain

Accepted: R4's label semantics and round-trip/materialization pins; tool
6.0.0, protocol 10, core API 2 and TUI 0.2.0; exact compatibility code; the
expanded packaged/public surface checks; the stale-string cleanup; and the
oracle-retirement corrections. The full 2,080-test result is the new baseline.

Two requested items remain:

1. R8 was not applied. README still says `disposition` is inline/attachment
   “with an optional `part_name` (RFC 2183).” RFC 2183 defines the disposition
   and its filename parameter; Baton defines `part_name`. Rewrite this as two
   separate facts and add/adjust the docs consistency pin if needed.

2. The compatibility implementation now uses equality, but no regression
   proves it refuses both an older and a newer core API. Moreover,
   `test_core_api.py` still asserts `core_api_version >= 1`, and
   `test_tui_state.py` still asserts `>= REQUIRES_CORE_API`; both encode the
   superseded rule. Pin the core API as exactly 2, assert the bundled TUI/core
   equality, and call `check_core_compatibility` against fakes reporting 1 and
   3 so changing the implementation back to `>=` fails.

R9's structured references convenience is unavailable in the preserved
protocol-9 executable being used for the live channel. Keep exact paths in the
body for this cutover interval; use a references part once the protocol-10
channel is live.
