# Stage 1B surface review

Proceed with the validation and verb-symmetry work that is independent of
spelling. The general direction is sound: repeatable inline parts, a validated
references convenience, no schema/protocol change, and no attempt to invent a
CLI language for nested multipart trees.

One genuine public-surface choice is escalated to Slawomir before the parser
is frozen: positional colon suffixes versus named `key=value` fields. The
reviewer recommends named fields. Colon fields make omitted middle values,
media-type parameters, POSIX paths containing `:`, and advisory names
ambiguous; named fields are more verbose but self-describing and extensible.

Whichever spelling is selected, pin these points:

1. Do not introduce new user-facing `filename` vocabulary. Protocol 10 will
   rename the stored field to `part_name`; use `name`/`part-name` in this new
   CLI surface now and translate internally while protocol 9 still stores
   `filename`.
2. Define one total leaf order across `--part`, `--attach`, and
   `--references`, because order is part of manifest/retry identity. In part
   mode, preserving heterogeneous option occurrence order is the least
   surprising contract. Existing `--body` + `--attach` ordering must remain
   unchanged.
3. Permit at most one stdin consumer across all repeatable parts and
   references together; refuse the command before reading when more than one
   `-` is present.
4. Reject empty references documents as well as empty lines and invalid
   paths; report the exact input line where applicable.
5. Apply identical construction rules to `send`, `send-notice`, `reply`, and
   `close`, with regression coverage proving parity rather than only parser
   acceptance.

Continue work that does not prejudge the syntax. Wait for Slawomir's ruling
before making the spelling a released contract.

## Progress review

The spelling-independent authoring seam, heterogeneous occurrence ordering,
pre-read stdin collision check, `name` boundary, and no-filesystem references
rule are sound. Focused source/test inspection found two normalization issues
to correct before wiring:

1. Refuse internal blank or whitespace-only reference lines. A normal terminal
   newline is not returned as an empty logical record by `str.splitlines()`,
   so accepting `a.md\n` does not require silently dropping the empty line in
   `a.md\n\n b.md`. Keep the usual terminal newline accepted and name the exact
   internal blank line in the refusal.
2. Do not silently rewrite a path with `raw.strip()`. Leading or trailing
   whitespace is either part of the POSIX filename or an authoring mistake;
   changing it produces a different reference. Refuse surrounding whitespace
   explicitly (with line number and quoted input) instead of storing a
   transformed path.

Add focused pins for both. This remains independent of the pending `--part`
spelling ruling and does not require the full suite.

### Correction verification

Both behavioral corrections pass independent focused testing (31 passed).
Accepted, with one cleanup for the final handoff: after
`line.strip() != line` raises, the following `if not line.strip()` branch is
unreachable. Remove the dead branch (or order the whitespace-only case first
if its distinct diagnostic is intentional) and ensure the surrounding prose
says such legal-but-invisible edge whitespace is *refused*, not that it
"must survive." This is cleanup, not a reason to pause the parser-independent
work.

Cleanup verified: the whitespace-only case now precedes the surrounding-edge
case, the prose matches refusal semantics, the focused suite passes 34/34,
and `git diff --check` is clean. No remaining reviewer issue in the
spelling-independent layer.
