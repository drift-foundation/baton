# Finding: the Python contracts package needs its own receiving-boundary inventory

Canonical Baton Work: W6782 (`2b077949-W6782`), created atomically with this
record and contained by W3.

## Origin

M6776 corrects the W6592 decomposition: public manager composition and the
contracts-package receiving inventory are independently reviewable deliverables
and therefore require separate Work identities, claims, evidence, reviews and
outcomes. W6592 is narrowed to public composition. This record owns the
contracts inventory as a separate Job contained by W3 (`V12 M2: Prove local
isolated execution`).

## Scope

Inventory every receiving boundary on the real public surface of
`baton_v12.contracts`: derive the universe from the package's actual exported
operations and every parameter of each operation, then require one declared
owner and one non-vacuous probe per entry. Pin private-body delegation
structurally so a public composite cannot quietly stop invoking the rule it
claims to compose.

This Job does not alter the public manager composition, repair W6592's exact
handshake type findings, implement §13, or implement retention. It consumes the
current contracts package and must revalidate its surface before implementation.

## Acceptance boundary

- The inventory universe exists independently of the ownership declarations.
- Every actual public-operation parameter appears exactly once or has a checked,
  specific non-entry rationale.
- Every owned entry names one owner and has one probe that reaches that owner;
  vacuous or earlier refusals fail the inventory.
- Delegated/private-body rules are tied structurally to their public composite.
- Focused and full source/locked verification pass under this Job's own claim.

## Independent review — 2026-08-25

Disposition: **changes requested and blocked on W7079**.

**Confirmed:** the universe is genuinely derived from the public `__all__`
callables and their signatures. Private-body delegation is structurally pinned.
The added label witnesses confirm every `what` probe carries the hostile label
through `label_of` into the refusal rather than passing on an earlier invalid
operand alone.

**Observed [P1]:** the completeness test counts an `OWNERS` key whose value is
`UNOWNED` as an owner. `ContractRefusal.message` and `.durable` therefore make
`test_every_entry_has_exactly_one_stated_owner` pass precisely while the table
says neither has an owner. This is a tracked discovery, not inventory
completion. The additive `test_no_receiving_entry_is_marked_unowned` closes the
loophole and fails with exactly those two entries.

The coupled constructor defect is recorded and routed to implementation as
W7079, bound to
`work/records/2026/08/finding-contract-refusal-unowned-inputs`. W6782 must
remain blocked until W7079 owns both values and this inventory replaces the
two exemptions with real rules and non-vacuous probes.

Review: `review-2026-08-25T00-22-54Z.md`.

## Unblocked inventory re-review — 2026-08-25

Disposition: **implementation accepted; durable progress correction required**.

W7079 closed satisfying. The two former `UNOWNED` entries now name their
constructor assertions and have direct non-vacuous witnesses. The contracts
inventory passes 15/15, including reviewer-added coverage tying public
`MESSAGE_LIMIT` to the exact 4,096/4,097 constructor edge.

`PROGRESS.md` remains stale: it still says the gaps are uncorrected and the
suite has 11 methods. Append the actual completion and attributed gate state;
no code change is requested. Review: `review-2026-08-25T00-57-12Z.md`.

## Final-record re-review — 2026-08-25

The requested completion append is present and the focused inventory remains
15/15, but its carried-forward universe count is stale: the current derived
surface is 18 exported callables and **39**, not 40, receiving entries. Append
that one correction to `PROGRESS.md`; no code or test change is requested.
Review: `review-2026-08-25T01-02-30Z.md`.

## Final independent review — 2026-08-25

Disposition: **signed off**. `PROGRESS.md` now supersedes the stale count with
the recomputed 18-callable/39-entry universe. The derived inventory remains
15/15, no `UNOWNED` entry remains, and broader manager failures are attributed
to W6631/W6632. Review: `review-2026-08-25T01-04-54Z.md`.
