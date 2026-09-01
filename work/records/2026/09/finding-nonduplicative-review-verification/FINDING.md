# Review verification must add information

## Finding

Repeating the implementer's exact test commands during review spends a second
Handler turn to reproduce evidence that is already recorded. It delays the
verdict without increasing confidence or exercising an independent boundary.

## Decision history

### 2026-09-01 — confirmed

Implementation and review have different verification responsibilities. The
implementer runs the focused regressions for the change and one appropriate
broad regression sweep before handoff, preserving the exact commands, results,
and known baseline failures as review evidence.

The reviewer audits the change, its assertions, and that recorded evidence.
The reviewer does not rerun the same commands merely to repeat the
implementer's result. Reviewer execution must add information: a novel,
narrowly targeted probe for a specifically identified uncovered risk, an
independent reproduction that exercises a different boundary, or a missing
gate whose absence prevents a verdict. If the existing evidence is sufficient,
the reviewer proceeds directly to a verdict.

This is not a ban on reviewer testing. It is a ban on ceremonial duplication.
When environmental independence itself is the acceptance claim, a repeated
command can be justified, but the reviewer records why that second environment
or identity is the evidence being tested.

## Acceptance boundary

`docs/EFFECTIVE-BATON.md` states this division next to the two-stage
verification cadence and distinguishes targeted independent review from
duplicating the implementer's suite.
