# Progress

## 2026-08-30 — first round (`baton.claude`, W47225 impl claim)

Created this record at the claim; see FINDING.md for the operational finding
about its absence.

### `launch.adopt` — the seam that was missing

`materialize` refuses an existing root and `discard` removes one, so a
restarted process had nothing to hold a delivery it had already made. `adopt`
proves and recovers it: the root is a real directory this manager made, the
document is a real file of its own name, both modes are the exact ones
`materialize` established, the bytes are within the contract's ceiling, and
the document is held to `LAUNCH_MEMBERS` and this build's schema by the same
owner that authored it.

An absent root answers `None` — ordinary, because an attempt may have had no
delivery. A root that exists and is not the one this manager wrote refuses.

### Composed into the retry

`dogfood_operator._for_retry` now passes `launch.adopt(...)` where it passed
`None`, so a retried cleanup ends the launch delivery it actually made instead
of reporting `not-delivered` and leaving the root behind. The deployment
reconstructs nothing.

### Verification

    PYTHONPATH=src python3 -m unittest tests.manager.test_launch
    -> 28 tests, OK (22 before; six additive).

    ...with test_input_delivery, test_dependencies, test_secrets,
    test_attempts and test_custody
    -> 553 tests, OK (3 skipped).

### Not this Work's, and reported rather than fixed

Two cases in `tests.tools.test_dogfood_operator` fail:
`test_retry_root_proof_refuses_a_symlink_alias` and
`test_the_narrow_retry_requires_a_committed_retention_decision`. Both are the
reviewer's newest additive witnesses for **W39358** — the retry's own root
proof and its trusted-result hold — and both landed while that Work sits with
the reviewer. Neither touches `launch`. I did not act on them under this claim.

## 2026-08-30 — second round (`baton.claude`, W47225 impl claim)

`review-2026-08-30T15-05-35Z.md`. All four P0s and the P1 corrected.

### Shape agreement is not delivery identity

The two document findings are one correction. Holding the document to member
NAMES and schema proves only that it is *a* launch document — a valid
four-member document copied out of another attempt's root passed every check —
and member VALUES were not held at all, so an integer `session` that
`materialize` refuses before writing was adopted after the fact.

Adoption now AUTHORS what this component would have written, through the same
`launch_document` and `_bytes` owners that wrote it, and requires the
canonical bytes to match exactly. One comparison closes identity and value
drift together, and it reuses the authoring rules rather than copying them —
including the whole-document secret check a re-implementation here would have
quietly dropped.

### A widened root authorized deleting a foreign entry

`discard` removes every name in the root it is given, so a sibling entry
accepted at adoption is a file this component would later delete without ever
having written it. The root is now held to exactly the one basename
`materialize` creates.

### Absence is ordinary for the component and contradictory for the caller

`adopt` still answers `None` when there is no root, because some attempts have
no launch delivery and that is a fact a caller needs to be able to read. The
refusal lives where the contradiction is: `_adopted_launch` in the deployment,
whose retained evidence says a runtime started — and a runtime only starts
after `materialize` completes. Ending with no delivery would report
`not-delivered` for a root that was really made, which is the settlement this
Work exists to stop.

`_launch_operands` gives the arc and the retry ONE spelling of the session,
contract and role. Two would be a delivery the retry could never adopt,
discovered only after a handoff had already failed once.

### [P1] Check-then-open is gone

The root is opened once with `O_NOFOLLOW|O_DIRECTORY`; the document is opened
relative to that descriptor with `O_NOFOLLOW`; and the entry list, both modes,
the file type and the bytes all come from descriptors that are already open.
No path is looked up twice.

### Verification

    PYTHONPATH=src python3 -m unittest tests.manager.test_launch
    -> 33 tests, OK (31 with the reviewer's three additive witnesses).

    ...with test_dogfood_operator, test_input_delivery, test_dependencies,
    test_secrets, test_attempts, test_custody and test_intake
    -> 752 tests, 2 failures, 3 skipped. Whitespace passed.

### The two failures are W43975's, and one of them matters to me

`test_material_kept_by_policy_survives_at_its_custody_locator` and
`test_directory_custody_is_required_before_runtime_destruction` are the
reviewer's newest witnesses for **W43975**'s custody wiring, which sits with
them. I did not act on them under this claim.

The first corroborates the open defect I reported on W43975 last round: the
ordinary `discard_workspace` I added there is removing material a `retained`
ending is supposed to be an account of. That is now two independent witnesses
saying the same thing about that removal, and it should be read as
confirmation rather than as a second problem.
