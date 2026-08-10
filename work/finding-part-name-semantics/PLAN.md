# Stage 2.1 — `filename` → `part_name`, site by site

Written before any code changes, because the rename is mechanical in shape and
not mechanical in effect: the same word appears as a wire field, a schema
column, a manifest input, a CLI option, a display label, and prose about a
different concept entirely. Renaming all of them together is how the ones that
should NOT move get moved.

## The oracle decision, now ruled

RETIRE. Active parity against `baton_v6.py` ends; there is no divergence
registry, no compatibility layer, no migration and no cross-version retry.
Protocol 10 initializes a fresh authority. `baton_v6.py` stays in the tree as
inactive evidence, imported by nothing.

The still-valid coverage moves rather than being re-derived, and it is one
line. `test_baton_v6.py` is 432 tests against the ORACLE; the shipping core
has 23 direct tests plus 7 differential ones. Changing exactly

    -import baton_v6 as b6
    +import baton_core._impl as b6

and running it gives 432 passed, with no other edit, no skips and no xfails —
measured before proposing it, not assumed. The core is a byte-copy of the same
implementation today, so the corpus transfers whole.

That matters beyond convenience: nobody chooses which properties are "still
valid", so nobody can quietly drop an inconvenient one, and the corpus passing
IS the evidence that the transfer was faithful.

Retirement order, so the net is never absent:

1. re-point the corpus at `baton_core._impl` and rename the file to say what
   it now tests;
2. run it — 432 must pass unchanged; any test needing adjustment is a finding,
   not a fixup;
3. only THEN drop `test_core_parity.py` from the gate and the justfile;
4. `baton_v6.py` keeps its hash pin, now guarding evidence rather than a
   measurement.

`_impl.py` is not touched until steps 1-4 are done and reviewed.

## What is actually there

    baton_core/_impl.py    57   the protocol: schema, validation, manifest,
                                delivery JSON, CLI options
    baton_v6.py            51   the frozen oracle — NOT edited under any
                                outcome; retired or diverged-from, never moved
    test_baton_v6.py       29   the ORACLE's corpus, not shipping-core
                                coverage — it imports and exercises
                                `baton_v6`. Corrected: an earlier version of
                                this table called these "core tests", which
                                would have counted retiring the oracle as
                                deleting 29 tests of protocol 10. Still-valid
                                properties must be PORTED to protocol-10
                                conformance before that suite leaves the gate,
                                and that port is part of the retirement, not a
                                consequence of it.
    test_core_authoring.py  9   the CLI's inward translation
    baton_core/authoring.py 8   `name` on the surface, `filename` inward
    test_tui_render.py      8   display
    baton_tui/render.py     6   display
    baton_tui/drafts.py     3   NOT this concept — see below
    baton_core/references.py 3  NOT this concept — see below
    README.md               7   documentation
    AGENTS-MAILBOX-PROTO.md 3   protocol document, hash-pinned

## Four categories, and only two of them move

**1. The protocol field.** Schema column `parts.filename`, `validate_filename`,
`normalize_parts`, the `content_spec` keyword, the delivery JSON, `dump`, and
the manifest identity. These become `part_name` and there is no compatibility
alias: the finding says protocol 10 contains `part_name` only, and must not
accept, emit or retain the old field.

Manifest identity is the part that makes this a bump rather than a rename.
`manifest_digest` serializes the metadata KEY, so replacing `filename` with
`part_name` changes the digest for every named part even when the value and
the bytes are identical.

Under the ruled cutover that has no live consequence: protocol 10 starts on a
FRESH authority, so there are no protocol-9 rows to compare against and no
cross-boundary retry exists. Whether an imported row would retain or rederive
its identity is a contract choice for Slawomir if history porting is ever
wanted — not something this stage settles. An earlier version of this plan
asserted that a boundary-spanning retry "should fail closed"; that was an
implementation opinion presented as a decision, and the semantic part name
does not in fact change.

**2. The CLI and TUI surface.** `--filename` becomes `--part-name`. The
authoring module already accepts `name=` in a `--part` descriptor and
translates inward — that translation is exactly what disappears here, which is
why it was built that way. The TUI part header says "part name".

**3. Prose about the CONCEPT.** README and the protocol document describe an
advisory label with no path semantics. The words change with the field.

**4. THE WORD USED FOR SOMETHING ELSE — do not touch.**

    baton_tui/drafts.py       `filename(participant)` builds a real file name
                              on the real filesystem for draft storage. It IS
                              a filename. Renaming it would be the rename
                              making the exact mistake it exists to fix.
    baton_core/references.py  prose about paths, which are also not part names
    _impl.py:4                "no filename-state" — a statement about the
                              authority not using the filesystem for state
    _impl.py:275              a comparison explaining why SUBJECT is bounded in
                              bytes "for the same reason `filename` is"; the
                              sentence survives, the reference in it moves

A blanket search-and-replace gets all four wrong. The last category is the one
that matters: `drafts.filename()` names a file, and the whole point of this
finding is that a part name does not.

## No in-place migration

REMOVED from this plan. An earlier version proposed `migrate_instance` and
`ALTER TABLE parts RENAME COLUMN`, which contradicts the ruled deployment
boundary: the protocol-9 authority stays live through development, is then
retired intact, and protocol 10 initializes a FRESH authority. An in-place
migration changes the outage, recovery and evidence contract, and nobody ruled
it.

So protocol 10's schema is designed and reviewed as the schema of a new
authority, with `part_name` in it from the start. There is no rename step
because there is nothing to rename.

Optional history porting is a separate contract with its own review. If it is
ever wanted it must choose and audit ONE complete strategy — rederive every
affected owner manifest under the protocol-10 canonical form in one guarded
ceremony including the dependent disposition and retry invariants, or preserve
and explicitly version a legacy digest domain for imported rows. It must not
hold the communications cutover hostage.

## Order

1. schema, written fresh with `part_name`;
2. validation and normalization, including the rename of `validate_filename`;
3. manifest and delivery JSON;
4. CLI option and help;
5. TUI display;
6. documentation and the protocol document, which moves
   `protocol_doc_sha256` and requires a rebuild;
7. rebuild both artifacts, refresh both manifests.

Steps 1-3 are where the parity decision bites. Steps 4-7 are consequences.

Step 1 is a fresh schema, not a migration; see above.

## Verification

Every step break-checked as usual. Two properties are specific to this change
and are the ones to pin first:

- no `filename` appears anywhere in a protocol-10 delivery, dump, or schema —
  asserted by grepping the live surface, not by reading the diff;
- `drafts.filename()` still exists and still names a file, asserted so that a
  future tidy-up does not fold it into the rename.
