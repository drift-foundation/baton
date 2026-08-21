# Progress

## 2026-08-21 — implementation complete, awaiting review

**State: awaiting review.** Implemented against `W1395`, revalidated against
the current tree before acting.

### What changed

`v12/test/placement.test.mjs` only. No file outside it was modified; a
post-implementation `find -newermt` over `v12/` confirms
`test/placement.test.mjs` is the sole changed path. `src/placement.mjs` is
untouched, so every runtime placement rule is exactly as reviewed.

The `state` portion of *the shell entry points get their paths from that one
authority* no longer invokes the shipped `poc.json`. It now creates its own
`mkdtempSync` root (`v12poc-entry-unowned-`), which exists and is deliberately
unmarked, writes a rebased configuration pointing `state_root`, `record_base`,
`baton.config` and `runtime.state_dir` at that exact root, and asserts status
2, empty stdout, the `carries no .v12-poc-state-root` diagnostic, that the root
survived, and that no marker was established. Cleanup is in `finally`, so a
failing assertion cannot strand the fixture.

The rebasing is a single helper, `rebasedConfig(root, dir = root)`, shared with
the two adjacent fixture cases rather than a third hand-written config shape.
`dir` exists because the absent-root case needs its root to stay absent, so its
document cannot live there.

### One correction inside the same boundary

Routing the absent-root case through the shared helper had it write its
document into a second `mkdtempSync` directory (`v12poc-absent-cfg-`) that
nothing removed, so every run leaked one directory into `/tmp`. The document
now lands in the parent that case already creates and already removes, so the
one existing `rmSync` covers every path the case makes. Its assertions and its
distinct absent-root coverage are unchanged.

### Verification

- `npm test` from `v12/`: **78/78** with `/tmp/baton-v12-poc` absent —
  the clean-post-reboot result the finding asks for.
- **78/78** again with `/tmp/baton-v12-poc` existing and unmarked, and a third
  time with it existing and carrying a valid marker. The gate no longer depends
  on which way the ambient sample root happens to be.
- No test creates or removes `/tmp/baton-v12-poc`. Every `ROOT` reference in
  the suite is either a string comparison or an `existsSync` read; the path was
  absent before and after each run. The three ambient states above were staged
  and torn down by hand, outside the suite.
- No `v12poc-entry-unowned-` or `v12poc-absent-cfg-` fixture remains after a
  run.
- The two refusals stay independently discriminating, reproduced directly
  against a hand-built fixture root:
  - existing, unmarked → `already exists and carries no .v12-poc-state-root`
    (status 2)
  - marked with `placement.mjs marker` → prints the root (status 0)
  - root removed → `does not exist, so there is nothing this prototype owns to
    remove` (status 2)

### Observation for the reviewer — out of this Work's boundary

The v12 suite still leaks temporary fixtures that predate this change and are
not part of the entry-point case: `scratch()` in `placement.test.mjs` (three
`v12poc-placement-*` directories per run, at the mount-fence and staging cases)
and roughly fifty-five `v12poc-test-*` directories per run from
`unit.test.mjs`. They accumulate without bound on a developer host. I left them
alone rather than widen this patch; recording it here so prioritization stays
with the reviewer.
