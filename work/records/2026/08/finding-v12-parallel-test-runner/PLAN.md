# Plan: run safe v12 tests across available cores

1. [done 2026-08-25] Inventory v12 Python test modules by resource ownership
   and pin the initial parallel-safe and mandatory-serial sets. The 28 pure
   modules, one Docker module and packaging/installed-layout stages are named
   in FINDING.md. Record the 423.54-second, 100%-CPU pure serial baseline in
   `evidence/serial-pure-baseline-2026-08-25.txt`.
2. [done 2026-08-25] Implement the standard-library repository runner under
   `v12/python/tools/`:
   - collect exact unittest ids in disposable child interpreters;
   - fail closed unless every discovered module belongs to exactly one explicit
     parallel/serial registry;
   - partition pure tests by concrete TestCase class, with individual-method
     shards for boundary inventory's two aggregate owner/probe classes;
   - default jobs from `os.process_cpu_count()`, capped by ready shards, and
     accept only a lower whole-number override;
   - run each shard in a fresh process, retain deterministic sorted reporting,
     and return nonzero if any shard fails;
   - on signal/fault terminate and reap every child process group and clean the
     runner's disposable result root.
3. [done 2026-08-25] Add `parallel-test` and `parallel-gate` recipes without replacing
   canonical `gate`. `just parallel-gate 8` is the documented override. Order:
   version, parallel source shards, source serial Docker registry, then the
   existing locked `build`/installed-layout stage. Emit a final phase summary
   that distinguishes parallel source, serial source and serial installed
   results.
4. [done 2026-08-25] Add runner regressions using disposable fake suites: deterministic
   collection/output under inverted completion; registry completeness and
   duplicate/missing-id refusal; default/override bounds; failure propagation;
   no phase overlap; interrupt/internal-fault descendant reaping; result-root
   cleanup; and exact jobs=1/default id/outcome parity. Register the new test
   module atomically so completeness never has a transitional exception.
5. [done 2026-08-25] Verify without weakening the current gate:
   - run jobs=1 and default on the same tree three times each and compare median
     wall time plus `/usr/bin/time -v` user/system/CPU/RSS evidence;
   - require identical collected test ids, failures/skips and deterministic
     final output apart from explicitly normalized durations;
   - run injected failure and interrupt trials, then prove no child processes
     or runner temporary roots remain;
   - run the source Docker module alone and after the parallel phase, prove no
     suite-prefixed containers/images remain, and never overlap two Docker
     runs;
   - run the complete locked installed-layout stage and confirm package origins
     remain in site-packages.
6. [done 2026-08-25] Return the dedicated recipes and evidence for independent review.
   Do not replace canonical `gate` until reviewer sign-off; replacement is a
   separate recorded decision after parity and cleanup are proved.

## Item status at handoff — 2026-08-25 (baton.claude)

Items 1-5 are **done**; item 6 is this handoff. Details and every stated limit
are in `PROGRESS.md` and `evidence/parallel-runner-2026-08-25.md`.

Item 5 is done WITH TWO NAMED GAPS, so it is not read as more than it is:
`just parallel-gate` was never executed as one complete chain (it fail-fasts on
this red tree by design; its three stages were each run individually), and
cross-context Docker exclusion does not exist (the serial registry serializes
within one invocation only).

Item 6's constraint is honoured: canonical `gate` is unchanged and its
replacement is NOT proposed here.

## Revalidated at implementation start — 2026-08-25 (baton.claude)

Item 1's inventory was re-checked against the current tree and is carried
forward with one correction recorded in FINDING.md under "Implementer
revalidation": the mandatory serial source registry holds TWO modules, not one.
`tests.manager.test_oci_engine` landed in `d36ca47` after the inventory was
taken and drives a real engine daemon and the shared image store. Wherever
items 2-6 below say "the source serial Docker registry" or
"the source Docker module", read both of:

    tests.manager.test_worker_container   # builds this repo's image, class fixtures
    tests.manager.test_oci_engine         # real Docker/Podman, shared image store

They run one at a time, in that registry order, never concurrently with each
other and never overlapping the parallel phase. Item 5's Docker verification
covers both. The parallel-safe set of 28 is unchanged.

## Tuner finish — 2026-08-25 (baton.tuner)

Final polish changed comments only: `just --list` now describes
`parallel-test` as the safe all-CPU source-test command and `parallel-gate` as
the complete parallel-source plus locked installed-layout gate. Runner behavior,
the reviewed recipes, and canonical `gate` are unchanged.

Focused verification after that polish:

- `just --list` exposes both complete descriptions and the optional `JOBS`
  argument;
- `PYTHONPATH=src python3 -m unittest tests.tools.test_parallel_runner -v`
  passes all 36 cases;
- `git diff --check` passes.

The signed-off limits remain unchanged: no successful one-chain
`parallel-gate` run is claimed on the currently red tree, and serialization is
within one runner invocation rather than a cross-context Docker lock.
