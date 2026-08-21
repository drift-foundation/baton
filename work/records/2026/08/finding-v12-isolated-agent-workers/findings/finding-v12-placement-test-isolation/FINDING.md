# Finding: make the v12 placement entry-point test own its fixture state

## Observed — 2026-08-21

After a forced machine restart, the self-contained `v12` gate reported 77/78
passing. `test/placement.test.mjs` expected the shell entry point to reject an
existing state root that lacked `.v12-poc-state-root`, but invoked the shipped
sample configuration whose `state_root` is `/tmp/baton-v12-poc`. That path no
longer existed after reboot, so the placement authority correctly returned its
different absent-root refusal:

```text
state_root /tmp/baton-v12-poc does not exist
```

The test therefore depends on ambient host state rather than constructing the
specific missing-marker condition it claims to verify. W126's retained 78/78
evidence was true in its prior environment, but the current gate is not
reproducible from a clean host.

## Proposed correction

The test must create and own a temporary external state root, configure the
entry point to use that exact root, deliberately omit the ownership marker,
and assert the missing-marker refusal. It must clean up only its own temporary
fixture. The separate absent-root test continues to prove the current
absent-root refusal.

No runtime placement rule changes: absent roots remain absent-root refusals,
and existing unowned roots remain missing-marker refusals.

## Acceptance boundary

- The focused case passes whether `/tmp/baton-v12-poc` exists or not before
  the test process starts.
- Removing the fixture marker produces the claimed missing-marker refusal.
- Removing the fixture root produces the distinct absent-root refusal.
- The complete self-contained `v12` gate passes from a clean post-reboot host.
- No test creates, removes, or relies on the sample configuration's live
  `/tmp/baton-v12-poc` location.

## Reviewer revalidation — 2026-08-21

**Observed.** `npm test` from `v12/` completes 78 cases with 77 passing and
one failure. The sole failure is `the shell entry points get their paths from
that one authority` at `test/placement.test.mjs:360`. The `state` invocation
returns status 2 and no stdout, but its stderr correctly says the sample
`/tmp/baton-v12-poc` root does not exist; the test accepts only `carries no
.v12-poc-state-root`.

**Confirmed.** The failing case calls `placement("state", "--config",
CONFIG)` where `CONFIG` is the shipped `v12/poc.json`. It branches on whether
that ambient sample root happens to be owned, but its refusal branch covers
only the existing-unmarked result. The comment claiming both outcomes are
asserted is therefore false on a clean host.

**Confirmed.** The placement authority is behaving as recorded and needs no
change. `assertOwnedStateRoot(..., { forDeletion: true })` deliberately
distinguishes an absent root (`nothing this prototype owns to remove`) from an
existing root without `MARKER_NAME` (`carries no ...`). The preceding focused
tests already construct test-owned fixtures for both branches:

- `the cleanup path refuses an ABSENT root and offers no path to remove`
  creates a private parent and a never-created child;
- `the cleanup entry point refuses an existing root that is not ours` creates
  a private temporary root without a marker, then marks that same root to
  prove the allowed path.

## Implementation-ready test boundary

**Proposed.** Change only the `state` portion of `the shell entry points get
their paths from that one authority`:

1. Create a unique temporary root with `mkdtempSync`; it exists and is owned
   by this test but deliberately has no `.v12-poc-state-root` marker.
2. Write a temporary configuration pointing `state_root`, `record_base`,
   `baton.config`, and `runtime.state_dir` into that exact root. Reusing one
   small root-rebasing helper with the two adjacent fixture cases is preferred
   to a third hand-written configuration shape.
3. Invoke the real CLI entry point with that temporary config and assert
   status 2, empty stdout, the missing-marker diagnostic, continued fixture
   existence, and absence of the marker.
4. Remove only that test-created root in `finally` or `test.after`, so an
   assertion failure cannot leave fixture state behind.

Do not make the regex accept both diagnostics, condition on sample-root
existence, create or remove `/tmp/baton-v12-poc`, or change
`src/placement.mjs`. Those alternatives would hide rather than remove the
ambient dependency. Keep the dedicated absent-root test unchanged so the two
refusals remain independently discriminating.

## Focused verification

- Run the isolated entry-point case with `/tmp/baton-v12-poc` absent.
- Run all of `test/placement.test.mjs` and confirm both distinct diagnostic
  cases still pass.
- Run `npm test` from `v12/`; the expected clean-host result is 78/78.
- Inspect the temporary-root prefix before and after the run to confirm no
  fixture remains, and confirm the sample `/tmp/baton-v12-poc` path was never
  created or removed.
